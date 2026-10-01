from knowledge.schema import NormalizedChunk, SourceLocation
from knowledge.document_types import DocumentType
from rag.embeddings import HashEmbeddingProvider
from rag.vector_store import LocalVectorIndex
from rag.hybrid import HybridSearch

def test_hybrid_search_returns_exact_term():
    chunks=[
        NormalizedChunk("1","d1","The Data Science course costs £2800.",SourceLocation(page=1),metadata={"document_type":DocumentType.TXT.value}),
        NormalizedChunk("2","d2","The engineering course includes laboratory sessions.",SourceLocation(page=1),metadata={"document_type":DocumentType.TXT.value}),
    ]
    index=LocalVectorIndex(HashEmbeddingProvider())
    index.add(chunks)
    hits=HybridSearch(index,chunks).search("Data Science course fee",top_k=1)
    assert hits[0].chunk.chunk_id=="1"
