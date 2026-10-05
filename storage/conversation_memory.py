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
        return any(text_value.startswith(x) for x in starters)

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

    def ensure_owner(self, conversation_id: str, user_id: str) -> None:
        db_id = _db_uuid(conversation_id)
        with self.engine.begin() as conn:
            existing = conn.execute(
                text(
                    "SELECT user_id FROM conversations "
                    "WHERE conversation_id=CAST(:conversation_id AS uuid) "
                    "FOR UPDATE"
                ),
                {"conversation_id": db_id},
            ).scalar_one_or_none()
            if existing is None:
                conn.execute(
                    text(
                        "INSERT INTO conversations (conversation_id, user_id) "
                        "VALUES (CAST(:conversation_id AS uuid), :user_id)"
                    ),
                    {"conversation_id": db_id, "user_id": user_id},
                )
            elif existing != user_id:
                raise PermissionError("Conversation belongs to another user.")

    def delete(self, conversation_id: str, user_id: str, is_admin: bool = False) -> int:
        db_id = _db_uuid(conversation_id)
        with self.engine.begin() as conn:
            owner_clause = "" if is_admin else " AND user_id = :user_id"
            params = {"conversation_id": db_id}
            if not is_admin:
                params["user_id"] = user_id

            existing = conn.execute(
                text(
                    "SELECT 1 FROM conversations "
                    "WHERE conversation_id=CAST(:conversation_id AS uuid)"
                    + owner_clause
                ),
                params,
            ).scalar_one_or_none()
            if existing is None:
                return 0

            for table in ("human_review_queue", "conversation_turns", "conversation_state"):
                conn.execute(
                    text(
                        f"DELETE FROM {table} "
                        "WHERE conversation_id=CAST(:conversation_id AS uuid)"
                    ),
                    {"conversation_id": db_id},
                )
            conn.execute(
                text(
                    "DELETE FROM conversations "
                    "WHERE conversation_id=CAST(:conversation_id AS uuid)"
                    + owner_clause
                ),
                params,
            )
            return 1

    def purge_expired(self, retention_days: int) -> int:
        retention_days = max(1, min(int(retention_days), 3650))
        with self.engine.begin() as conn:
            expired = conn.execute(
                text(
                    "SELECT conversation_id FROM conversations "
                    "WHERE updated_at < now() - (:retention_days * INTERVAL '1 day')"
                ),
                {"retention_days": retention_days},
            ).scalars().all()
            for conversation_id in expired:
                cid = str(conversation_id)
                for table in ("human_review_queue", "conversation_turns", "conversation_state"):
                    conn.execute(
                        text(
                            f"DELETE FROM {table} "
                            "WHERE conversation_id=CAST(:conversation_id AS uuid)"
                        ),
                        {"conversation_id": cid},
                    )
                conn.execute(
                    text(
                        "DELETE FROM conversations "
                        "WHERE conversation_id=CAST(:conversation_id AS uuid)"
                    ),
                    {"conversation_id": cid},
                )
            return len(expired)

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
        turn_id = uuid5(
            NAMESPACE_URL,
            f"{conversation_id}:{datetime.now(timezone.utc).timestamp()}:{user_text[:64]}",
        )
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO conversation_turns "
                    "(turn_id, conversation_id, user_text, assistant_text, grounded, "
                    "citations_count, latency_ms, model_id) "
                    "VALUES (CAST(:turn_id AS uuid), CAST(:conversation_id AS uuid), "
                    ":user_text, :assistant_text, :grounded, :citations_count, "
                    ":latency_ms, :model_id)"
                ),
                {
                    "turn_id": str(turn_id),
                    "conversation_id": _db_uuid(conversation_id),
                    "user_text": user_text[:2000],
                    "assistant_text": assistant_text[:4000],
                    "grounded": grounded,
                    "citations_count": citations_count,
                    "latency_ms": latency_ms,
                    "model_id": model_id,
                },
            )
