from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from agents.answer_prompt import build_system_prompt
from agents.cache import TTLCache
from agents.cost_policy import CostPolicy, trim_evidence
from agents.model import AnswerModel, ExtractiveAnswerModel
from agents.response import humanize_deep_answer, humanize_factual_answer
from agents.router import route_query
from agents.verification import verify_claims
from rag.citations import Citation
from rag.retrieval import HybridRetriever
from security.input_guard import looks_like_prompt_injection

@dataclass
class CoachAIOrchestrator:
    retriever: HybridRetriever | None = None
    answer_model: AnswerModel | None = None
    policy: CostPolicy = field(default_factory=CostPolicy.from_env)
    cache: TTLCache = field(init=False)
    knowledge_generation: int = 0

    def __post_init__(self) -> None:
        self.cache = TTLCache(ttl_seconds=self.policy.cache_ttl_seconds)

    async def run(
        self,
        message: str,
        conversation_id: str | None = None,
        style: str = "friendly",
        voice_id: str = "Brian",
    ) -> dict[str, Any]:
        message = " ".join(message.split())[: self.policy.max_input_chars]
        if looks_like_prompt_injection(message):
            return {
                "conversation_id": conversation_id,
                "answer": "I can help with coaching-centre information, but I can't follow requests to reveal or change my internal instructions.",
                "intent": "security",
                "abstained": True,
                "security_blocked": True,
                "next_action": "human_review",
                "voice": {"voice_id": voice_id, "style": style},
            }

        route = route_query(message, self.policy)
        if route.requires_human_review:
            return {
                "conversation_id": conversation_id,
                "answer": "I can help, but this needs a member of the coaching-centre team. I’ll keep this as a human-review case.",
                "intent": route.intent,
                "abstained": False,
                "next_action": "human_review",
                "voice": {"voice_id": voice_id, "style": style},
            }

        if not route.requires_retrieval:
            return self._abstain(conversation_id, route.intent, "This request requires a human.")
        if self.retriever is None:
            return self._abstain(conversation_id, route.intent, "Knowledge base is not configured.")

        cache_key = self.cache.key(message.lower(), style, str(self.knowledge_generation))
        cached = self.cache.get(cache_key)
        if cached is not None:
            cached = deepcopy(cached)
            cached["conversation_id"] = conversation_id
            cached["voice"] = {"voice_id": voice_id, "style": style}
            cached["performance"]["cache_hit"] = True
            return cached

        results = self.retriever.search(message, top_k=self.policy.retrieval_top_k)
        if not results or results[0].final_score < self.policy.low_score_threshold:
            return self._abstain(conversation_id, route.intent, "No sufficiently strong approved evidence was found.")

        evidence = trim_evidence([r.chunk.text for r in results], self.policy.max_evidence_chars)
        use_llm = route.answer_mode == "deep" and self.answer_model is not None and self.policy.llm_enabled
        model = self.answer_model if use_llm else ExtractiveAnswerModel()

        draft = await model.generate(message, evidence, style)
        if draft.strip().upper() == "ABSTAIN":
            return self._abstain(conversation_id, route.intent, "The model could not produce an evidence-grounded answer.")

        answer = (
            humanize_deep_answer(draft, style)
            if use_llm
            else humanize_factual_answer(draft, style)
        )
        verification = verify_claims(answer, evidence)
        if not verification.grounded:
            return self._abstain(conversation_id, route.intent, "Answer failed grounding verification.")

        result = {
            "conversation_id": conversation_id,
            "answer": answer,
            "intent": route.intent,
            "citations": [Citation.from_result(r).__dict__ for r in results],
            "verification": verification.__dict__,
            "abstained": False,
            "next_action": "answer",
            "voice": {"voice_id": voice_id, "style": style},
            "performance": {
                "path": "deep_llm" if use_llm else "fast_extract",
                "cache_hit": False,
                "llm_called": use_llm,
                "evidence_chunks": len(evidence),
                "input_chars": len(message),
                "evidence_chars": sum(len(x) for x in evidence),
                "max_output_tokens": self.policy.max_output_tokens,
            },
        }
        self.cache.set(cache_key, result)
        return result

    @staticmethod
    def _abstain(conversation_id: str | None, intent: str, reason: str) -> dict[str, Any]:
        return {
            "conversation_id": conversation_id,
            "answer": "I couldn't verify that in the approved coaching-centre documents, so I don't want to guess. A team member can help with this.",
            "intent": intent,
            "abstained": True,
            "reason": reason,
            "next_action": "human_review",
        }
