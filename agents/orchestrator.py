from copy import deepcopy
from dataclasses import dataclass, field
import re
from typing import Any

from agents.budget import CloudBudget
from agents.cache import TTLCache
from agents.conversation import memory
from agents.cost_policy import CostPolicy, trim_evidence
from agents.model import AnswerModel, ExtractiveAnswerModel
from agents.response import humanize_deep_answer, humanize_factual_answer
from agents.router import route_query
from agents.verification import verify_claims
from language.messages import message as localized_message
from language.registry import detect_script_language, get_language
from rag.citations import Citation
from rag.retrieval import HybridRetriever
from security.input_guard import looks_like_prompt_injection
from translation.service import TranslationService

@dataclass
class CoachAIOrchestrator:
    retriever:HybridRetriever|None=None
    answer_model:AnswerModel|None=None
    translator:TranslationService|None=None
    policy:CostPolicy=field(default_factory=CostPolicy.from_env)
    cloud_budget:CloudBudget=field(default_factory=lambda:CloudBudget())
    cache:Any|None=None
    translation_cache:Any|None=None
    knowledge_generation:int=0
    source_language:str="en"

    def __post_init__(self):
        if self.cache is None:
            self.cache=TTLCache(ttl_seconds=self.policy.cache_ttl_seconds)
        if self.translation_cache is None:
            self.translation_cache=TTLCache(ttl_seconds=max(self.policy.cache_ttl_seconds,600))

    @staticmethod
    def _adaptive_results(results):
        if len(results)<=1:return results
        top,second=results[0].final_score,results[1].final_score
        if top>=0.72 and top-second>=0.12:return results[:1]
        if top>=0.48 and top-second>=0.10:return results[:2]
        return results[:3]

    async def _translate(self,text,source,target):
        if source==target:return text
        if not self.translator or not self.translator.enabled:
            raise RuntimeError("Multilingual translation is not configured.")
        key=self.translation_cache.key(source,target,text)
        cached=self.translation_cache.get(key)
        if cached is not None:return cached
        value=await self.translator.translate(text,source,target)
        self.translation_cache.set(key,value)
        return value

    async def run(self,message,conversation_id=None,style="friendly",voice_id="Brian",language="auto"):
        message=" ".join(message.split())[:self.policy.max_input_chars]
        resolved_message=memory.resolve(conversation_id,message)
        target_code=detect_script_language(message) if language=="auto" else language
        target=get_language(target_code)
        voice_meta={"voice_id":voice_id,"style":style,"language":target.code,"language_name":target.name}

        if looks_like_prompt_injection(message):
            result={"conversation_id":conversation_id,"answer":localized_message("security",target.code),"intent":"security","abstained":True,"security_blocked":True,"next_action":"human_review","voice":voice_meta,"language":target.code}
            memory.remember(conversation_id,message,"security");return result

        route=route_query(resolved_message,self.policy)
        if route.requires_human_review:
            result={"conversation_id":conversation_id,"answer":localized_message("human",target.code),"intent":route.intent,"abstained":False,"next_action":"human_review","voice":voice_meta,"language":target.code}
            memory.remember(conversation_id,resolved_message,route.intent);return result
        if self.retriever is None:
            return self._abstain(conversation_id,route.intent,"Knowledge base is not configured.",voice_meta)

        retrieval_query=resolved_message
        translated_query=False
        native_multilingual=self.retriever.supports_cross_language
        if target.translate_code!="en" and not native_multilingual:
            try:
                retrieval_query=await self._translate(resolved_message,self.source_language,target.translate_code)
                translated_query=True
            except Exception:
                return self._abstain(conversation_id,route.intent,"Language bridge is unavailable for this request.",voice_meta)

        cache_key=self.cache.key(retrieval_query.lower(),style,target.code,str(self.knowledge_generation))
        cached=self.cache.get(cache_key)
        if cached is not None:
            cached=deepcopy(cached);cached["conversation_id"]=conversation_id;cached["voice"]=voice_meta
            cached["performance"]["cache_hit"]=True;memory.remember(conversation_id,retrieval_query,route.intent);return cached

        results=self.retriever.search(retrieval_query,top_k=self.policy.retrieval_top_k)
        if not results or results[0].final_score<self.policy.low_score_threshold:
            result=self._abstain(conversation_id,route.intent,"No sufficiently strong approved evidence was found.",voice_meta)
            memory.remember(conversation_id,retrieval_query,route.intent);return result

        results=self._adaptive_results(results)
        evidence=trim_evidence([r.chunk.text for r in results],self.policy.max_evidence_chars)
        budget_blocked=False
        use_llm=route.answer_mode=="deep" and self.answer_model is not None and self.policy.llm_enabled
        if use_llm and not self.cloud_budget.allow():use_llm=False;budget_blocked=True

        model=self.answer_model if use_llm else ExtractiveAnswerModel()
        try:
            draft=await model.generate(retrieval_query,evidence,style,"English")
        except Exception as exc:
            draft=await ExtractiveAnswerModel().generate(retrieval_query,evidence,style,"English")
            use_llm=False;cloud_error=str(exc)[:160]
        else:cloud_error=None

        if draft.strip().upper()=="ABSTAIN":
            return self._abstain(conversation_id,route.intent,"The model could not produce an evidence-grounded answer.",voice_meta)

        source_answer=humanize_deep_answer(draft,style) if use_llm else humanize_factual_answer(draft,style,retrieval_query)
        verification=verify_claims(source_answer,evidence)
        if not verification.grounded:
            return self._abstain(conversation_id,route.intent,"Answer failed grounding verification.",voice_meta)

        answer=source_answer
        translated_answer=False
        if target.translate_code!="en":
            try:
                answer=await self._translate(source_answer,"en",target.translate_code)
                translated_answer=True
            except Exception:
                return self._abstain(conversation_id,route.intent,"The verified answer could not be translated safely.",voice_meta)

        result={
            "conversation_id":conversation_id,
            "answer":re.sub(r"\s*\[S\d+\]","",answer).strip(),
            "intent":route.intent,
            "citations":[Citation.from_result(r).__dict__ for r in results],
            "verification":verification.__dict__,
            "abstained":False,
            "next_action":"answer",
            "voice":voice_meta,
            "language":target.code,
            "performance":{
                "path":"deep_llm" if use_llm else "fast_extract","cache_hit":False,"llm_called":use_llm,
                "native_multilingual_retrieval":native_multilingual,
                "translation_used":translated_query or translated_answer,
                "query_translated":translated_query,"answer_translated":translated_answer,
                "budget_blocked":budget_blocked,"cloud_fallback":cloud_error is not None,"cloud_error":cloud_error,
                "evidence_chunks":len(evidence),"input_chars":len(resolved_message),"evidence_chars":sum(len(x) for x in evidence),
                "max_output_tokens":self.policy.max_output_tokens,
            },
        }
        self.cache.set(cache_key,result);memory.remember(conversation_id,retrieval_query,route.intent);return result

    @staticmethod
    def _abstain(conversation_id,intent,reason,voice_meta):
        return {"conversation_id":conversation_id,"answer":localized_message("abstain",voice_meta.get("language","en-GB")),"intent":intent,"abstained":True,"reason":reason,"next_action":"human_review","voice":voice_meta,"language":voice_meta.get("language")}
