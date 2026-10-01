from dataclasses import dataclass
import re
from math import sqrt

from rag.models import DocumentChunk
from rag.guardrails import only_active_student_evidence
from rag.embeddings import HashEmbeddingProvider
from rag.multilingual_embeddings import build_multilingual_provider

STOPWORDS={"the","a","an","is","are","was","were","what","when","where","how","can","do","does","to","of","for","and","or","in","on","my","me","please","tell","about","with"}

@dataclass(frozen=True)
class ScoredChunk:
    chunk:DocumentChunk
    semantic_score:float
    keyword_score:float
    final_score:float

def _normalize_token(token:str)->str:
    token=token.lower().strip()
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    return token

def tokenize(text:str)->set[str]:
    tokens=re.findall(r"[a-zA-Z0-9£$€_.-]+",text.lower())
    return {_normalize_token(t) for t in tokens if t not in STOPWORDS}

def keyword_score(query:str,text:str)->float:
    q=tokenize(query);t=tokenize(text)
    if not q:return 0.0
    overlap=len(q&t)/len(q)
    phrase_bonus=0.15 if query.lower().strip() in text.lower() else 0.0
    return min(1.0,overlap+phrase_bonus)

def _cosine(left:list[float],right:list[float])->float:
    if not left or not right:return 0.0
    n=min(len(left),len(right))
    dot=sum(left[i]*right[i] for i in range(n))
    ln=sqrt(sum(x*x for x in left)) or 1.0
    rn=sqrt(sum(x*x for x in right)) or 1.0
    return max(0.0,dot/(ln*rn))

class HybridRetriever:
    """Hybrid retrieval with optional cross-lingual local embeddings."""
    def __init__(self,chunks:list[DocumentChunk],dimensions:int=96):
        self.chunks=only_active_student_evidence(chunks)
        self.multilingual_provider=build_multilingual_provider()
        if self.multilingual_provider:
            self.embedding_provider=self.multilingual_provider
            self.embeddings=self.embedding_provider.embed_documents([c.text for c in self.chunks])
        else:
            self.embedding_provider=HashEmbeddingProvider(dimensions=dimensions)
            self.embeddings=self.embedding_provider.embed([c.text for c in self.chunks])

    @property
    def supports_cross_language(self)->bool:
        return self.multilingual_provider is not None

    def search(self,query:str,top_k:int=3)->list[ScoredChunk]:
        if not query.strip() or not self.chunks:return []
        if self.multilingual_provider:
            query_vector=self.embedding_provider.embed_query(query)
        else:
            query_vector=self.embedding_provider.embed([query])[0]
        results=[]
        for chunk,vector in zip(self.chunks,self.embeddings):
            ks=keyword_score(query,chunk.text)
            ss=_cosine(query_vector,vector)
            final=0.55*ss+0.45*ks
            results.append(ScoredChunk(chunk,ss,ks,final))
        return sorted(results,key=lambda x:x.final_score,reverse=True)[:top_k]


class PostgresHybridRetriever:
    """Hybrid retrieval directly from durable PostgreSQL + pgvector.

    Vector candidates are selected in the database; lexical candidates are
    added from PostgreSQL full-text search, then both signals are combined
    with the same deterministic scoring policy as the local retriever.
    """

    def __init__(self, store, embedding_provider=None, candidate_limit: int = 20, query_cache=None):
        from rag.managed_embeddings import build_bedrock_embedding_provider

        self.store = store
        self.embedding_provider = embedding_provider or build_bedrock_embedding_provider()
        self.candidate_limit = max(5, min(candidate_limit, 50))
        self.query_cache = query_cache

    @property
    def supports_cross_language(self) -> bool:
        # Titan V2 is used here with the orchestrator's English translation bridge
        # for cross-language queries. A local multilingual profile can be selected
        # separately when cross-language native retrieval is required.
        return False

    def _query_embedding(self, query: str) -> list[float]:
        if self.query_cache is None:
            return self.embedding_provider.embed_query(query)
        key = self.query_cache.key(
            "embedding",
            self.embedding_provider.model_id,
            str(self.embedding_provider.dimensions),
            query.strip().lower(),
        )
        cached = self.query_cache.get(key)
        if cached is not None:
            return [float(x) for x in cached]
        vector = self.embedding_provider.embed_query(query)
        self.query_cache.set(key, vector)
        return vector

    def search(self, query: str, top_k: int = 3) -> list[ScoredChunk]:
        from rag.models import DocumentMetadata, DocumentStatus

        if not query.strip():
            return []

        query_vector = self._query_embedding(query)
        vector_literal = "[" + ",".join(str(float(x)) for x in query_vector) + "]"

        sql = """
        WITH vector_candidates AS (
            SELECT
                c.chunk_id, c.document_id, c.chunk_index, c.content,
                c.page, c.section, d.name, d.version, d.category,
                d.status, d.effective_from, d.effective_until,
                (1 - (c.embedding <=> CAST(:embedding AS vector))) AS semantic_score
            FROM document_chunks c
            JOIN documents d ON d.document_id = c.document_id
            WHERE d.status = 'ACTIVE'
              AND c.embedding IS NOT NULL
            ORDER BY c.embedding <=> CAST(:embedding AS vector)
            LIMIT :candidate_limit
        ),
        lexical_candidates AS (
            SELECT
                c.chunk_id, c.document_id, c.chunk_index, c.content,
                c.page, c.section, d.name, d.version, d.category,
                d.status, d.effective_from, d.effective_until,
                0.0 AS semantic_score
            FROM document_chunks c
            JOIN documents d ON d.document_id = c.document_id
            WHERE d.status = 'ACTIVE'
              AND to_tsvector('simple', c.content)
                  @@ plainto_tsquery('simple', :query)
            ORDER BY ts_rank_cd(
                to_tsvector('simple', c.content),
                plainto_tsquery('simple', :query)
            ) DESC
            LIMIT :candidate_limit
        ),
        candidates AS (
            SELECT * FROM vector_candidates
            UNION ALL
            SELECT * FROM lexical_candidates
        )
        SELECT
            chunk_id, document_id, content, page, section,
            name, version, category, status, effective_from, effective_until,
            MAX(semantic_score) AS semantic_score
        FROM candidates
        GROUP BY
            chunk_id, document_id, content, page, section,
            name, version, category, status, effective_from, effective_until
        """

        with self.store.engine.connect() as conn:
            rows = conn.execute(
                __import__("sqlalchemy").text(sql),
                {
                    "embedding": vector_literal,
                    "query": query,
                    "candidate_limit": self.candidate_limit,
                },
            ).mappings().all()

        results: list[ScoredChunk] = []
        for row in rows:
            metadata = DocumentMetadata(
                document_id=str(row["document_id"]),
                name=row["name"],
                version=row["version"],
                category=row["category"],
                status=DocumentStatus(row["status"]),
                effective_from=(
                    row["effective_from"].date()
                    if hasattr(row["effective_from"], "date")
                    else row["effective_from"]
                ),
                effective_until=(
                    row["effective_until"].date()
                    if hasattr(row["effective_until"], "date")
                    else row["effective_until"]
                ),
            )
            chunk = DocumentChunk(
                chunk_id=str(row["chunk_id"]),
                document=metadata,
                page=row["page"],
                section=row["section"],
                text=row["content"],
            )
            semantic = max(0.0, min(1.0, float(row["semantic_score"] or 0.0)))
            lexical = keyword_score(query, chunk.text)
            final = 0.55 * semantic + 0.45 * lexical
            results.append(ScoredChunk(chunk, semantic, lexical, final))

        return sorted(results, key=lambda item: item.final_score, reverse=True)[:top_k]
