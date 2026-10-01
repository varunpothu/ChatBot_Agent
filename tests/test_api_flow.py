import pytest

from agents.model import ExtractiveAnswerModel
from agents.orchestrator import CoachAIOrchestrator
from rag.models import DocumentChunk, DocumentMetadata
from rag.retrieval import HybridRetriever

@pytest.mark.asyncio
async def test_grounded_response_contains_citation():
    doc = DocumentMetadata("fees", "Fees.pdf", "v1", "fees", "ACTIVE")
    chunk = DocumentChunk("fees-p1-0", doc, 1, "Fees", "The Data Science course fee is £2800.")
    orchestrator = CoachAIOrchestrator(
        retriever=HybridRetriever([chunk]),
        answer_model=ExtractiveAnswerModel(),
    )
    result = await orchestrator.run("What is the Data Science course fee?")
    assert result["abstained"] is False
    assert result["citations"][0]["page"] == 1
    assert result["verification"]["grounded"] is True
