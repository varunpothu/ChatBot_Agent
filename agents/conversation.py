from dataclasses import dataclass, field
import re

@dataclass
class ConversationState:
    last_query: str = ""
    last_intent: str = "general_information"

@dataclass
class ConversationMemory:
    """Very small structured memory.

    We keep only the previous question and intent, not the full transcript.
    This enables natural follow-ups without replaying chat history into an LLM.
    """
    states: dict[str, ConversationState] = field(default_factory=dict)

    def resolve(self, conversation_id: str | None, message: str) -> str:
        if not conversation_id:
            return message
        state = self.states.get(conversation_id)
        if not state or not self._looks_like_follow_up(message):
            return message
        return f"{state.last_query} {message}"

    def remember(self, conversation_id: str | None, query: str, intent: str) -> None:
        if not conversation_id:
            return
        self.states[conversation_id] = ConversationState(
            last_query=query[-1000:],
            last_intent=intent,
        )

    def delete(self, conversation_id: str) -> bool:
        return self.states.pop(conversation_id, None) is not None

    def purge_expired(self, retention_days: int) -> int:
        # Process-local memory has no durable age metadata; nothing persists across restarts.
        return 0

    @staticmethod
    def _looks_like_follow_up(message: str) -> bool:
        text = re.sub(r"\s+", " ", message.lower()).strip()
        starters = (
            "and ", "what about", "how about", "does that", "is that",
            "what if", "then ", "also ", "how much is that", "when is that"
        )
        return any(text.startswith(x) for x in starters) or len(text.split()) <= 5

memory = ConversationMemory()
