from pathlib import Path
import hashlib
import os
import shutil
import time
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from agents.bedrock_model import BedrockAnswerModel
from agents.cache import TTLCache
from agents.groq_model import GroqAnswerModel
from agents.orchestrator import CoachAIOrchestrator
from knowledge.chunker import semantic_chunks
from knowledge.document_registry import ManagedDocument, documents
from knowledge.parsers import parse_document
from rag.models import DocumentChunk, DocumentMetadata, DocumentStatus
from rag.retrieval import HybridRetriever
from rag.store import InMemoryKnowledgeStore
from monitoring.metrics import metrics
from monitoring.alerts import evaluate_alerts
from ops.runtime import ops
from voice.providers import VOICES, AmazonPollyProvider

app = FastAPI(title="CoachAI API", version="1.1.0")
store = InMemoryKnowledgeStore()
retriever: HybridRetriever | None = None
retriever_generation = -1

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
tts_cache = TTLCache(ttl_seconds=int(os.getenv("TTS_CACHE_TTL_SECONDS", "3600")), max_items=256)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1400)
    conversation_id: str | None = None
    voice_id: str = "Brian"
    conversation_style: str = "friendly"

class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=3000)
    voice_id: str = "Brian"

class ReviewResolution(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)
    resolution: str = Field(min_length=1, max_length=1000)

def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected:
        raise HTTPException(503, "Admin API is not configured.")
    if x_admin_key != expected:
        raise HTTPException(401, "Invalid admin credentials.")

@app.get("/")
async def home(): return FileResponse("web/index.html")

@app.get("/dashboard")
async def dashboard(): return FileResponse("web/dashboard.html")

@app.get("/config")
async def config():
    return {"tts_mode": os.getenv("TTS_MODE", "browser"), "llm_provider": os.getenv("LLM_PROVIDER", "auto"), "fast_path_default": True, "governed_ingestion": True}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "coachai-api", "generation": store.generation, "retriever_ready": retriever is not None and retriever_generation == store.generation, "open_reviews": len(ops.list_reviews("OPEN"))}

@app.get("/kpis", dependencies=[Depends(require_admin)])
async def kpis():
    snapshot = metrics.snapshot()
    return {
        "kpis": snapshot,
        "alerts": [a.__dict__ for a in evaluate_alerts(snapshot)],
        "documents": {
            "total": len(documents.documents),
            "pending_review": sum(d.status == "PENDING_REVIEW" for d in documents.documents.values()),
            "active": sum(d.status == "ACTIVE" for d in documents.documents.values()),
        },
        "human_review_queue": {"open": len(ops.list_reviews("OPEN"))},
    }

@app.get("/voices")
async def voices(): return [v.__dict__ for v in VOICES]

@app.get("/documents", dependencies=[Depends(require_admin)])
async def list_documents(): return [d.__dict__ for d in documents.list()]

@app.post("/admin/documents/{document_id}/approve", dependencies=[Depends(require_admin)])
async def approve_document(document_id: str, reviewer: str = "admin"):
    try:
        archived = documents.activate(document_id, reviewer)
        store.set_document_status(document_id, DocumentStatus.ACTIVE)
        for archived_id in archived:
            store.set_document_status(archived_id, DocumentStatus.ARCHIVED)
        event = ops.audit("DOCUMENT_ACTIVATED", reviewer, document_id, {"archived_versions": archived})
        return {"status": "ACTIVE", "document_id": document_id, "archived_versions": archived, "audit_event_id": event.event_id}
    except KeyError:
        raise HTTPException(404, "Document not found") from None
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.post("/admin/documents/{document_id}/reject", dependencies=[Depends(require_admin)])
async def reject_document(document_id: str, reviewer: str = "admin"):
    try:
        documents.reject(document_id, reviewer)
        store.set_document_status(document_id, DocumentStatus.REJECTED)
        event = ops.audit("DOCUMENT_REJECTED", reviewer, document_id, {})
        return {"status": "REJECTED", "document_id": document_id, "audit_event_id": event.event_id}
    except KeyError:
        raise HTTPException(404, "Document not found") from None
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.get("/reviews", dependencies=[Depends(require_admin)])
async def list_reviews(status: str | None = None): return [r.__dict__ for r in ops.list_reviews(status)]

@app.post("/reviews/{review_id}/resolve", dependencies=[Depends(require_admin)])
async def resolve_review(review_id: str, request: ReviewResolution):
    try:
        item = ops.resolve_review(review_id, request.reviewer, request.resolution)
        ops.audit("HUMAN_REVIEW_RESOLVED", request.reviewer, review_id, {"resolution": request.resolution})
        return item.__dict__
    except KeyError:
        raise HTTPException(404, "Review not found") from None

@app.get("/audit", dependencies=[Depends(require_admin)])
async def audit(): return [e.__dict__ for e in reversed(ops.audit_events[-200:])]

def get_retriever() -> HybridRetriever:
    global retriever, retriever_generation
    if retriever is None or retriever_generation != store.generation:
        retriever = HybridRetriever(store.all())
        retriever_generation = store.generation
    return retriever

@app.post("/chat")
async def chat(request: ChatRequest):
    started = time.perf_counter()
    if request.voice_id not in {v.voice_id for v in VOICES}:
        raise HTTPException(400, "Unknown voice")
    if request.conversation_style not in {"friendly", "professional", "concise"}:
        raise HTTPException(400, "Unsupported conversation style")

    conversation_id = request.conversation_id or uuid4().hex
    orchestrator.retriever = get_retriever()
    orchestrator.knowledge_generation = store.generation
    result = await orchestrator.run(request.message, conversation_id, request.conversation_style, request.voice_id)
    elapsed = (time.perf_counter() - started) * 1000

    if result.get("performance", {}).get("cache_hit"): metrics.record("cache_hit", elapsed)
    elif result.get("performance", {}).get("llm_called"): metrics.record("llm_call", elapsed, input_tokens=len(request.message)//4, output_tokens=len(result.get("answer",""))//4)
    else: metrics.record("fast_path", elapsed)

    metrics.record("abstention" if result.get("abstained") else "answer", elapsed)
    if result.get("security_blocked"): metrics.record("security_block", elapsed)
    review_id = None
    if result.get("next_action") == "human_review":
        item = ops.enqueue_review(result.get("reason", result.get("intent", "human_review")), request.message, conversation_id)
        review_id = item.review_id
        metrics.record("human_escalation", elapsed)
        ops.audit("HUMAN_REVIEW_CREATED", "system", review_id, {"intent": result.get("intent")})
    result["conversation_id"] = conversation_id
    if review_id: result["review_id"] = review_id
    return result

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    allowed = {".pdf",".docx",".pptx",".xlsx",".xls",".csv",".txt",".md",".html",".htm",".json"}
    if suffix not in allowed: raise HTTPException(415, f"Unsupported file type: {suffix or 'unknown'}")
    original_name = file.filename or f"document{suffix}"
    content_hash = hashlib.sha256()
    document_id = uuid4().hex
    destination = UPLOAD_DIR / f"{document_id}{suffix}"
    with destination.open("wb") as output:
        while chunk := file.file.read(1024 * 1024):
            content_hash.update(chunk)
            output.write(chunk)
    digest = content_hash.hexdigest()
    if any(d.content_hash == digest for d in documents.documents.values()):
        destination.unlink(missing_ok=True)
        raise HTTPException(409, "This document content already exists.")
    version = documents.next_version(original_name)
    try:
        normalized = parse_document(destination)
        chunks = semantic_chunks(normalized)
        metadata = DocumentMetadata(document_id, original_name, version, "general", DocumentStatus.PENDING_REVIEW)
        converted = [DocumentChunk(f"{document_id}-{i}", metadata, chunk.location.page, chunk.location.section, chunk.text) for i, chunk in enumerate(chunks)]
        store.add(converted)
        documents.add(ManagedDocument(document_id, original_name, version, digest, "general", "PENDING_REVIEW", datetime.now(timezone.utc)))
        event = ops.audit("DOCUMENT_UPLOADED", "system", document_id, {"filename": original_name, "version": version, "content_hash": digest, "chunks": len(converted)})
        return {"document_id": document_id, "filename": original_name, "format": normalized.document_type.value, "version": version, "chunks_indexed": len(converted), "status": "PENDING_REVIEW", "message": "Document processed. An admin must approve it before students can use it.", "audit_event_id": event.event_id}
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(422, f"Document extraction failed: {exc}") from exc

@app.post("/tts")
async def tts(request: TTSRequest):
    if request.voice_id not in {v.voice_id for v in VOICES}: raise HTTPException(400, "Unknown voice")
    engine = os.getenv("POLLY_ENGINE", "neural")
    cache_key = AmazonPollyProvider.cache_key(request.text, request.voice_id, engine)
    cached = tts_cache.get(cache_key)
    if cached is not None: return Response(content=cached, media_type="audio/mpeg", headers={"X-TTS-Cache": "HIT"})
    try: audio = AmazonPollyProvider().synthesize(request.text, request.voice_id)
    except Exception as exc: raise HTTPException(503, f"Voice service unavailable: {exc}") from exc
    tts_cache.set(cache_key, audio)
    metrics.record("tts", tts_characters=len(request.text))
    return Response(content=audio, media_type="audio/mpeg", headers={"X-TTS-Cache": "MISS"})
