from pathlib import Path
import shutil
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agents.orchestrator import CoachAIOrchestrator
from knowledge.chunker import semantic_chunks
from knowledge.parsers import parse_document
from rag.models import DocumentChunk, DocumentMetadata, DocumentStatus
from rag.retrieval import HybridRetriever
from rag.store import InMemoryKnowledgeStore

app = FastAPI(title="CoachAI API", version="0.4.0")
store = InMemoryKnowledgeStore()
orchestrator = CoachAIOrchestrator()
UPLOAD_DIR = Path("data/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

@app.get("/")
async def home():
    return FileResponse("web/index.html")

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "coachai-api"}

@app.get("/web/{filename}")
async def web_asset(filename: str):
    return FileResponse(Path("web") / filename)

@app.post("/chat")
async def chat(request: ChatRequest):
    orchestrator.retriever = HybridRetriever(store.all())
    return await orchestrator.run(request.message, request.conversation_id)

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
            document_id=document_id, name=file.filename or destination.name,
            version="v1", category="general", status=DocumentStatus.ACTIVE,
        )
        converted = [
            DocumentChunk(
                chunk_id=f"{document_id}-{i}", document=metadata,
                page=chunk.location.page, section=chunk.location.section,
                text=chunk.text,
            ) for i, chunk in enumerate(chunks)
        ]
        store.add(converted)
        return {
            "document_id": document_id, "filename": file.filename,
            "format": normalized.document_type.value,
            "chunks_indexed": len(converted), "status": metadata.status,
        }
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(422, f"Document extraction failed: {exc}") from exc
