from rag.hybrid import HybridHit

class SimpleReranker:
    """Deterministic baseline. A cross-encoder reranker can replace this class."""
    def rerank(self,query:str,hits:list[HybridHit],top_k:int=5)->list[HybridHit]:
        query_terms=set(query.lower().split())
        scored=[]
        for h in hits:
            terms=set(h.chunk.text.lower().split())
            overlap=len(query_terms & terms)/max(len(query_terms),1)
            scored.append((0.7*h.fused_score+0.3*overlap,h))
        scored.sort(key=lambda x:x[0],reverse=True)
        return [h for _,h in scored[:top_k]]
