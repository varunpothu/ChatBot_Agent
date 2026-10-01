from rag.models import DocumentChunk

def only_active_student_evidence(chunks: list[DocumentChunk]) -> list[DocumentChunk]:
    """Filter authorization/state before evidence reaches the LLM."""
    return [
        c for c in chunks
        if c.document.status == "ACTIVE" and c.document.access_level == "student"
    ]
