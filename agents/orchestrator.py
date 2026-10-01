from dataclasses import dataclass
from typing import Any

@dataclass
class RetrievalEvidence:
    source: str
    page: int | None
    text: str
    score: float

class CoachAIOrchestrator:
    """Controlled workflow skeleton; real adapters are added in later milestones."""

    async def run(self, message: str, conversation_id: str | None = None) -> dict[str, Any]:
        intent = self.route(message)
        rewritten = self.rewrite(message)
        evidence = self.retrieve(rewritten, intent)

        if not evidence:
            return self.abstain(reason="No approved evidence was found.")

        answer = self.generate_answer(message, evidence)
        verification = self.verify(answer, evidence)

        if not verification["grounded"]:
            return self.abstain(reason="The draft answer could not be fully grounded.")

        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "intent": intent,
            "citations": [{"source": e.source, "page": e.page, "score": e.score} for e in evidence],
            "verification": verification,
        }

    def route(self, message: str) -> str:
        lowered = message.lower()
        if any(w in lowered for w in ("fee", "price", "cost", "tuition")):
            return "fees"
        if any(w in lowered for w in ("batch", "schedule", "timing", "start")):
            return "batch_schedule"
        if any(w in lowered for w in ("admission", "enrol", "enroll", "apply")):
            return "admissions"
        return "general_information"

    def rewrite(self, message: str) -> str:
        return message.strip()

    def retrieve(self, query: str, intent: str) -> list[RetrievalEvidence]:
        # Phase 2 replaces this with approved-document hybrid retrieval.
        return []

    def generate_answer(self, message: str, evidence: list[RetrievalEvidence]) -> str:
        return ""

    def verify(self, answer: str, evidence: list[RetrievalEvidence]) -> dict[str, Any]:
        return {"grounded": bool(answer and evidence), "score": 1.0 if answer and evidence else 0.0}

    def abstain(self, reason: str) -> dict[str, Any]:
        return {
            "answer": "I couldn't verify that information in the approved coaching-centre documents, so I don't want to guess.",
            "abstained": True,
            "reason": reason,
            "next_action": "human_review",
        }
