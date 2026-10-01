from dataclasses import dataclass
from knowledge.schema import NormalizedChunk
from rag.retrieval import keyword_score
from rag.vector_store import LocalVectorIndex

@dataclass(frozen=True)
class HybridHit:
    chunk:NormalizedChunk
    vector_score:float
    keyword_score:float
    fused_score:float

class HybridSearch:
    def __init__(self,index:LocalVectorIndex,chunks:list[NormalizedChunk]):
        self.index=index
        self.chunks=chunks

    def search(self,query:str,top_k:int=5)->list[HybridHit]:
        vector_hits=self.index.search(query,top_k=20)
        by_id={h.chunk.chunk_id:h for h in vector_hits}
        results=[]
        for chunk in self.chunks:
            v=by_id.get(chunk.chunk_id)
            vs=v.score if v else 0.0
            ks=keyword_score(query,chunk.text)
            fused=0.65*vs+0.35*ks
            results.append(HybridHit(chunk,vs,ks,fused))
        return sorted(results,key=lambda x:x.fused_score,reverse=True)[:top_k]
