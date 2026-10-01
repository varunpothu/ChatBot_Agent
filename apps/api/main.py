from pathlib import Path
import os
import shutil
import time
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from agents.bedrock_model import BedrockAnswerModel
from agents.groq_model import GroqAnswerModel
from agents.orchestrator import CoachAIOrchestrator
from knowledge.chunker import semantic_chunks
from knowledge.parsers import parse_document
from rag.models import DocumentChunk, DocumentMetadata, DocumentStatus
from rag.retrieval import HybridRetriever
from rag.store import InMemoryKnowledgeStore
from monitoring.metrics import metrics
from monitoring.alerts import evaluate_alerts
from voice.providers import VOICES, AmazonPollyProvider

app = FastAPI(title="CoachAI API", version="0.8.0")
store = InMemoryKnowledgeStore()

def build_cloud_model():
    provider = os.getenv("LLM_PROVIDER", "auto").lower()
    if provider == "local":
        return None
    if provider == "bedrock":
        try:
            return BedrockAnswerModel()
        except Exception:
            return None
    if provider == "groq":
        try:
            return GroqAnswerModel()
        except Exception:
            return None
    if os.getenv("GROQ_API_KEY") and os.getenv("GROQ_MODEL"):
        try:
            return GroqAnswerModel()
        except Exception:
            pass
    if os.getenv("BEDROCK_MODEL_ID"):
        try:
            return BedrockAnswerModel()
        except Exception:
            pass
    return None

orchestrator = CoachAIOrchestrator(answer_model=build_cloud_model())
UPLOAD_DIR = Path(os.getenv("DOCUMENT_STORAGE_PATH", "data/documents"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
tts_cache: dict[str, bytes] = {}

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1400)
    conversation_id: str | None = None
    voice_id: str = "Brian"
    conversation_style: str = "friendly"

class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000)
    voice_id: str = "Brian"

@app.get("/")
async def home(): return FileResponse("web/index.html")

@app.get("/dashboard")
async def dashboard(): return FileResponse("web/dashboard.html")

@app.get("/health")
async def health(): return {"status": "ok", "service": "coachai-api", "generation": store.generation}

@app.get("/kpis")
async def kpis():
    snapshot = metrics.snapshot()
    return {"kpis": snapshot, "alerts": [a.__dict__ for a in evaluate_alerts(snapshot)]}

@app.get("/voices")
async def voices(): return [v.__dict__ for v in VOICES]

@app.post("/chat")
async def chat(request: ChatRequest):
    started = time.perf_counter()
    allowed = {v.voice_id for v in VOICES}
    if request.voice_id not in allowed:
        raise HTTPException(400, "Unknown voice")
    if request.conversation_style not in {"friendly", "professional", "concise"}:
        raise HTTPException(400, "Unsupported conversation style")

    orchestrator.retriever = HybridRetriever(store.all())
    orchestrator.knowledge_generation = store.generation
    result = await orchestrator.run(
        request.message,
        request.conversation_id,
        request.conversation_style,
        request.voice_id,
    )
    elapsed = (time.perf_counter() - started) * 1000

    if result.get("performance", {}).get("cache_hit"):
        metrics.record("cache_hit", elapsed)
    elif result.get("performance", {}).get("llm_called"):
        metrics.record("llm_call", elapsed, input_tokens=len(request.message)//4, output_tokens=len(result.get("answer", ""))//4)
    else:
        metrics.record("fast_path", elapsed)

    if result.get("abstained"):
        metrics.record("abstention", elapsed)
    else:
        metrics.record("answer", elapsed)
    if result.get("security_blocked"):
        metrics.record("security_block", elapsed)
    if result.get("next_action") == "human_review":
        metrics.record("human_escalation", elapsed)
    return result

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    allowed = {".pdf",".docx",".pptx",".xlsx",".xls",".csv",".txt",".md",".html",".htm",".json"}
    if suffix not in allowed:
        raise HTTPException(415, f"Unsupported file type: {suffix or 'unknown'}")
    document_id = uuid4().hex
    destination = UPLOAD_DIR / f"{document_id}{suffix}"
    with destination.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    try:
        normalized = parse_document(destination)
        chunks = semantic_chunks(normalized)
        metadata = DocumentMetadata(
            document_id=document_id,
            name=file.filename or destination.name,
            version="v1",
            category="general",
            status=DocumentStatus.ACTIVE,
        )
        converted = [
            DocumentChunk(
                chunk_id=f"{document_id}-{i}",
                document=metadata,
                page=chunk.location.page,
                section=chunk.location.section,
                text=chunk.text,
            )
            for i, chunk in enumerate(chunks)
        ]
        store.add(converted)
        return {
            "document_id": document_id,
            "filename": file.filename,
            "format": normalized.document_type.value,
            "chunks_indexed": len(converted),
            "status": metadata.status,
            "generation": store.generation,
        }
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(422, f"Document extraction failed: {exc}") from exc

@app.post("/tts")
async def tts(request: TTSRequest):
    allowed = {v.voice_id for v in VOICES}
    if request.voice_id not in allowed:
        raise HTTPException(400, "Unknown voice")
    cache_key = AmazonPollyProvider.cache_key(request.text, request.voice_id, os.getenv("POLLY_ENGINE", "neural"))
    cached = tts_cache.get(cache_key)
    if cached is not None:
        return Response(content=cached, media_type="audio/mpeg", headers={"X-TTS-Cache": "HIT"})
    try:
        audio = AmazonPollyProvider().synthesize(request.text, request.voice_id)
    except Exception as exc:
        raise HTTPException(503, f"Voice service unavailable: {exc}") from exc
    tts_cache[cache_key] = audio
    metrics.record("tts", tts_characters=len(request.text))
    return Response(content=audio, media_type="audio/mpeg", headers={"X-TTS-Cache": "MISS"})
