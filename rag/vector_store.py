from dataclasses import dataclass
import math

from rag.embeddings import EmbeddingProvider
from knowledge.schema import NormalizedChunk

@dataclass(frozen=True)
class VectorHit:
    chunk:NormalizedChunk
    score:float

class LocalVectorIndex:
    """In-process vector index for development; replace storage with pgvector in AWS."""
    def __init__(self,provider:EmbeddingProvider):
        self.provider=provider
        self.items:list[tuple[NormalizedChunk,list[float]]]=[]

    def add(self,chunks:list[NormalizedChunk])->None:
        vectors=self.provider.embed([c.text for c in chunks])
        self.items.extend(zip(chunks,vectors))

    def search(self,query:str,top_k:int=10)->list[VectorHit]:
        q=self.provider.embed([query])[0]
        hits=[]
        for chunk,v in self.items:
            score=sum(a*b for a,b in zip(q,v))
            hits.append(VectorHit(chunk,score))
        return sorted(hits,key=lambda x:x.score,reverse=True)[:top_k]
