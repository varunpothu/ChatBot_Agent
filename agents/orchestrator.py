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
from rag.citations import Citation
from rag.retrieval import HybridRetriever
from security.input_guard import looks_like_prompt_injection

@dataclass
class CoachAIOrchestrator:
    retriever: HybridRetriever | None = None
    answer_model: AnswerModel | None = None
    policy: CostPolicy = field(default_factory=CostPolicy.from_env)
    cloud_budget: CloudBudget = field(default_factory=lambda: CloudBudget())
    cache: TTLCache = field(init=False)
    knowledge_generation: int = 0

    def __post_init__(self) -> None:
        self.cache = TTLCache(ttl_seconds=self.policy.cache_ttl_seconds)

    @staticmethod
    def _adaptive_results(results):
        if len(results) <= 1:
            return results
        top = results[0].final_score
        second = results[1].final_score
        if top >= 0.72 and (top - second) >= 0.12:
            return results[:1]
        if top >= 0.48 and (top - second) >= 0.10:
            return results[:2]
        return results[:3]

    async def run(self, message: str, conversation_id: str | None = None, style: str = "friendly", voice_id: str = "Brian") -> dict[str, Any]:
        message = " ".join(message.split())[: self.policy.max_input_chars]
        resolved_message = memory.resolve(conversation_id, message)

        if looks_like_prompt_injection(message):
            result = {
                "conversation_id": conversation_id,
                "answer": "I can help with coaching-centre information, but I can't follow requests to reveal or change my internal instructions.",
                "intent": "security",
                "abstained": True,
                "security_blocked": True,
                "next_action": "human_review",
                "voice": {"voice_id": voice_id, "style": style},
            }
            memory.remember(conversation_id, message, "security")
            return result

        route = route_query(resolved_message, self.policy)
        if route.requires_human_review:
            result = {
                "conversation_id": conversation_id,
                "answer": "I can help, but this needs a member of the coaching-centre team. I’ll keep this as a human-review case.",
                "intent": route.intent,
                "abstained": False,
                "next_action": "human_review",
                "voice": {"voice_id": voice_id, "style": style},
            }
            memory.remember(conversation_id, resolved_message, route.intent)
            return result

        if self.retriever is None:
            return self._abstain(conversation_id, route.intent, "Knowledge base is not configured.", voice_id, style)

        cache_key = self.cache.key(resolved_message.lower(), style, str(self.knowledge_generation))
        cached = self.cache.get(cache_key)
        if cached is not None:
            cached = deepcopy(cached)
            cached["conversation_id"] = conversation_id
            cached["voice"] = {"voice_id": voice_id, "style": style}
            cached["performance"]["cache_hit"] = True
            memory.remember(conversation_id, resolved_message, route.intent)
            return cached

        results = self.retriever.search(resolved_message, top_k=self.policy.retrieval_top_k)
        if not results or results[0].final_score < self.policy.low_score_threshold:
            result = self._abstain(conversation_id, route.intent, "No sufficiently strong approved evidence was found.", voice_id, style)
            memory.remember(conversation_id, resolved_message, route.intent)
            return result

        results = self._adaptive_results(results)
        evidence = trim_evidence([r.chunk.text for r in results], self.policy.max_evidence_chars)

        budget_blocked = False
        use_llm = route.answer_mode == "deep" and self.answer_model is not None and self.policy.llm_enabled
        if use_llm and not self.cloud_budget.allow():
            use_llm = False
            budget_blocked = True

        model = self.answer_model if use_llm else ExtractiveAnswerModel()
        try:
            draft = await model.generate(resolved_message, evidence, style)
        except Exception as exc:
            draft = await ExtractiveAnswerModel().generate(resolved_message, evidence, style)
            use_llm = False
            cloud_error = str(exc)[:160]
        else:
            cloud_error = None

        if draft.strip().upper() == "ABSTAIN":
            result = self._abstain(conversation_id, route.intent, "The model could not produce an evidence-grounded answer.", voice_id, style)
            memory.remember(conversation_id, resolved_message, route.intent)
            return result

        answer = humanize_deep_answer(draft, style) if use_llm else humanize_factual_answer(draft, style, resolved_message)
        verification = verify_claims(answer, evidence)
        if not verification.grounded:
            result = self._abstain(conversation_id, route.intent, "Answer failed grounding verification.", voice_id, style)
            memory.remember(conversation_id, resolved_message, route.intent)
            return result

        display_answer = re.sub(r"\\s*\\[S\\d+\\]", "", answer).strip()
        result = {
            "conversation_id": conversation_id,
            "answer": display_answer,
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
                "budget_blocked": budget_blocked,
                "cloud_fallback": cloud_error is not None,
                "cloud_error": cloud_error,
                "evidence_chunks": len(evidence),
                "input_chars": len(resolved_message),
                "evidence_chars": sum(len(x) for x in evidence),
                "max_output_tokens": self.policy.max_output_tokens,
            },
        }
        self.cache.set(cache_key, result)
        memory.remember(conversation_id, resolved_message, route.intent)
        return result

    @staticmethod
    def _abstain(conversation_id: str | None, intent: str, reason: str, voice_id: str = "Brian", style: str = "friendly") -> dict[str, Any]:
        return {
            "conversation_id": conversation_id,
            "answer": "I couldn't verify that in the approved coaching-centre documents, so I don't want to guess. A team member can help with this.",
            "intent": intent,
            "abstained": True,
            "reason": reason,
            "next_action": "human_review",
            "voice": {"voice_id": voice_id, "style": style},
        }
