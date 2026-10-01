from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from agents.orchestrator import CoachAIOrchestrator
from rag.ingestion import extract_pdf_chunks
from rag.models import DocumentMetadata
from rag.retrieval import HybridRetriever
from rag.store import InMemoryKnowledgeStore

app = FastAPI(title="CoachAI API", version="0.2.0")
store = InMemoryKnowledgeStore()
orchestrator = CoachAIOrchestrator()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "coachai-api"}


@app.post("/chat")
async def chat(request: ChatRequest):
    orchestrator.retriever = HybridRetriever(store.all())
    return await orchestrator.run(request.message, request.conversation_id)


@app.post("/documents/index")
async def index_document(path: str):
    # Local development endpoint. Production will accept uploads and store
    # documents in S3 with an approval workflow.
    document = DocumentMetadata(
        document_id=Path(path).stem,
        name=Path(path).name,
        version="v1",
        category="general",
        status="ACTIVE",
    )
    result = extract_pdf_chunks(path, document)
    store.add(result.chunks)
    return {"document_id": document.document_id, "chunks_indexed": len(result.chunks)}
