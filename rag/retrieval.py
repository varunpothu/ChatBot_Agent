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

def tokenize(text:str)->set[str]:
    tokens=set(re.findall(r"[a-zA-Z0-9£$€_.-]+",text.lower()))
    return {t for t in tokens if t not in STOPWORDS}

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
