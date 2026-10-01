from dataclasses import dataclass
from typing import Any

from agents.model import AnswerModel, ExtractiveAnswerModel
from agents.router import route_query
from agents.verification import verify_claims
from rag.citations import Citation
from rag.retrieval import HybridRetriever


@dataclass
class CoachAIOrchestrator:
    retriever: HybridRetriever | None = None
    answer_model: AnswerModel | None = None

    async def run(self, message: str, conversation_id: str | None = None) -> dict[str, Any]:
        route = route_query(message)

        if route.requires_human_review:
            return {
                "conversation_id": conversation_id,
                "answer": "I'll route this to a member of the coaching-centre team.",
                "intent": route.intent,
                "abstained": False,
                "next_action": "human_review",
            }

        if self.retriever is None:
            return self._abstain(conversation_id, route.intent, "Knowledge base is not configured.")

        results = self.retriever.search(message, top_k=5)
        if not results or results[0].final_score <= 0:
            return self._abstain(conversation_id, route.intent, "No matching approved evidence was found.")

        evidence = [r.chunk.text for r in results]
        model = self.answer_model or ExtractiveAnswerModel()
        draft = await model.generate(message, evidence)

        verification = verify_claims(draft, evidence)
        if not verification.grounded:
            return self._abstain(conversation_id, route.intent, "Draft answer failed grounding verification.")

        citations = [Citation.from_result(r).__dict__ for r in results]
        return {
            "conversation_id": conversation_id,
            "answer": draft,
            "intent": route.intent,
            "citations": citations,
            "verification": verification.__dict__,
            "abstained": False,
        }

    @staticmethod
    def _abstain(conversation_id: str | None, intent: str, reason: str) -> dict[str, Any]:
        return {
            "conversation_id": conversation_id,
            "answer": "I couldn't verify that information in the approved coaching-centre documents, so I don't want to guess.",
            "intent": intent,
            "abstained": True,
            "reason": reason,
            "next_action": "human_review",
        }
