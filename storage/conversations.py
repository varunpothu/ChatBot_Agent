from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_URL


@dataclass(frozen=True)
class StoredConversationState:
    last_query: str
    last_intent: str


class PostgresConversationMemory:
    """Persistent tiny conversation state; never stores full prompt history for retrieval."""

    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _db_uuid(value: str) -> str:
        from uuid import UUID
        try:
            return str(UUID(value))
        except ValueError:
            return str(uuid5(NAMESPACE_URL, value))

    @staticmethod
    def _looks_like_follow_up(message: str) -> bool:
        normalized = " ".join(message.lower().split())
        starters = (
            "and ", "what about", "how about", "does that", "is that",
            "what if", "then ", "also ", "how much is that", "when is that",
        )
        return any(normalized.startswith(prefix) for prefix in starters) or len(normalized.split()) <= 5

    def resolve(self, conversation_id: str | None, message: str) -> str:
        if not conversation_id or not self._looks_like_follow_up(message):
            return message
        from sqlalchemy import text
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT last_query FROM conversation_state "
                    "WHERE conversation_id=CAST(:conversation_id AS uuid)"
                ),
                {"conversation_id": self._db_uuid(conversation_id)},
            ).scalar_one_or_none()
        return f"{row} {message}" if row else message

    def remember(self, conversation_id: str | None, query: str, intent: str) -> None:
        if not conversation_id:
            return
        from sqlalchemy import text
        db_id = self._db_uuid(conversation_id)
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO conversations(conversation_id, last_intent, updated_at) "
                    "VALUES (CAST(:conversation_id AS uuid), :intent, :updated_at) "
                    "ON CONFLICT (conversation_id) DO UPDATE "
                    "SET last_intent=EXCLUDED.last_intent, updated_at=EXCLUDED.updated_at"
                ),
                {"conversation_id": db_id, "intent": intent, "updated_at": datetime.now(timezone.utc)},
            )
            conn.execute(
                text(
                    "INSERT INTO conversation_state(conversation_id,last_query,last_intent,updated_at) "
                    "VALUES (CAST(:conversation_id AS uuid), :query, :intent, :updated_at) "
                    "ON CONFLICT (conversation_id) DO UPDATE "
                    "SET last_query=EXCLUDED.last_query, last_intent=EXCLUDED.last_intent, updated_at=EXCLUDED.updated_at"
                ),
                {
                    "conversation_id": db_id,
                    "query": query[-1000:],
                    "intent": intent,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

    def record_turn(
        self,
        conversation_id: str,
        user_text: str,
        assistant_text: str,
        grounded: bool,
        citations_count: int,
        latency_ms: float,
        model_id: str | None = None,
    ) -> None:
        from sqlalchemy import text
        turn_id = uuid5(NAMESPACE_URL, f"{conversation_id}:{datetime.now(timezone.utc).timestamp()}:{user_text[:64]}")
        db_conversation_id = self._db_uuid(conversation_id)
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO conversation_turns "
                    "(turn_id, conversation_id, user_text, assistant_text, grounded, citations_count, latency_ms, model_id) "
                    "VALUES (CAST(:turn_id AS uuid), CAST(:conversation_id AS uuid), :user_text, :assistant_text, "
                    ":grounded, :citations_count, :latency_ms, :model_id)"
                ),
                {
                    "turn_id": str(turn_id),
                    "conversation_id": db_conversation_id,
                    "user_text": user_text[:2000],
                    "assistant_text": assistant_text[:4000],
                    "grounded": grounded,
                    "citations_count": citations_count,
                    "latency_ms": latency_ms,
                    "model_id": model_id,
                },
            )
