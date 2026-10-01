from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_URL

from sqlalchemy import text


def _db_uuid(value: str) -> str:
    try:
        from uuid import UUID
        return str(UUID(value))
    except ValueError:
        return str(uuid5(NAMESPACE_URL, value))


class PostgresConversationMemory:
    """Persist only the minimal state needed for natural follow-up questions."""

    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _looks_like_follow_up(message: str) -> bool:
        text_value = re.sub(r"\s+", " ", message.lower()).strip()
        starters = (
            "and ", "what about", "how about", "does that", "is that",
            "what if", "then ", "also ", "how much is that", "when is that",
        )
        return any(text_value.startswith(x) for x in starters) or len(text_value.split()) <= 5

    def resolve(self, conversation_id: str | None, message: str) -> str:
        if not conversation_id or not self._looks_like_follow_up(message):
            return message
        with self.engine.connect() as conn:
            previous = conn.execute(
                text(
                    "SELECT last_query FROM conversation_state "
                    "WHERE conversation_id=CAST(:conversation_id AS uuid)"
                ),
                {"conversation_id": _db_uuid(conversation_id)},
            ).scalar_one_or_none()
        return f"{previous} {message}" if previous else message

    def remember(self, conversation_id: str | None, query: str, intent: str) -> None:
        if not conversation_id:
            return
        db_id = _db_uuid(conversation_id)
        now = datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO conversations (conversation_id, last_intent, updated_at) "
                    "VALUES (CAST(:conversation_id AS uuid), :intent, :updated_at) "
                    "ON CONFLICT (conversation_id) DO UPDATE "
                    "SET last_intent=:intent, updated_at=:updated_at"
                ),
                {"conversation_id": db_id, "intent": intent, "updated_at": now},
            )
            conn.execute(
                text(
                    "INSERT INTO conversation_state "
                    "(conversation_id, last_query, last_intent, updated_at) "
                    "VALUES (CAST(:conversation_id AS uuid), :last_query, :intent, :updated_at) "
                    "ON CONFLICT (conversation_id) DO UPDATE "
                    "SET last_query=:last_query, last_intent=:intent, updated_at=:updated_at"
                ),
                {
                    "conversation_id": db_id,
                    "last_query": query[-1000:],
                    "intent": intent,
                    "updated_at": now,
                },
            )
