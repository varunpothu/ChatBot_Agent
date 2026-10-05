import os
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text

from storage.conversation_memory import PostgresConversationMemory
from storage.postgres import PostgresRuntime


@pytest.mark.integration
def test_postgres_conversation_isolation_and_delete():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    runtime = PostgresRuntime(database_url, auto_init_schema=True)
    memory = PostgresConversationMemory(runtime.engine)

    owner = f"test-owner-{uuid4().hex}"
    other_owner = f"test-other-{uuid4().hex}"
    conversation_id = str(uuid4())

    memory.ensure_owner(conversation_id, owner)
    memory.record_turn(
        conversation_id=conversation_id,
        user_text="What is the fee?",
        assistant_text="The fee is listed in the approved course information.",
        grounded=True,
        citations_count=1,
        latency_ms=12.5,
    )

    with runtime.engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO human_review_queue "
                "(review_id, conversation_id, reason, message) "
                "VALUES (CAST(:review_id AS uuid), CAST(:conversation_id AS uuid), "
                ":reason, :message)"
            ),
            {
                "review_id": str(uuid4()),
                "conversation_id": conversation_id,
                "reason": "test",
                "message": "test review",
            },
        )

    with pytest.raises(PermissionError):
        memory.ensure_owner(conversation_id, other_owner)

    assert memory.delete(conversation_id, other_owner) == 0
    assert memory.delete(conversation_id, owner) == 1

    with runtime.engine.connect() as conn:
        counts = conn.execute(
            text(
                "SELECT "
                "(SELECT COUNT(*) FROM conversations WHERE conversation_id=CAST(:id AS uuid)) AS conversations, "
                "(SELECT COUNT(*) FROM conversation_state WHERE conversation_id=CAST(:id AS uuid)) AS state, "
                "(SELECT COUNT(*) FROM conversation_turns WHERE conversation_id=CAST(:id AS uuid)) AS turns, "
                "(SELECT COUNT(*) FROM human_review_queue WHERE conversation_id=CAST(:id AS uuid)) AS reviews"
            ),
            {"id": conversation_id},
        ).mappings().one()

    assert counts["conversations"] == 0
    assert counts["state"] == 0
    assert counts["turns"] == 0
    assert counts["reviews"] == 0


@pytest.mark.integration
def test_postgres_retention_removes_expired_conversation_only():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests")

    runtime = PostgresRuntime(database_url, auto_init_schema=True)
    memory = PostgresConversationMemory(runtime.engine)

    expired_id = str(uuid4())
    active_id = str(uuid4())
    owner = f"retention-test-{uuid4().hex}"

    memory.ensure_owner(expired_id, owner)
    memory.ensure_owner(active_id, owner)

    with runtime.engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE conversations "
                "SET updated_at = now() - (:days * INTERVAL '1 day') "
                "WHERE conversation_id IN "
                "(CAST(:expired AS uuid), CAST(:active AS uuid))"
            ),
            {"days": 31, "expired": expired_id, "active": active_id},
        )

    assert memory.purge_expired(30) >= 1

    with runtime.engine.connect() as conn:
        remaining = conn.execute(
            text(
                "SELECT conversation_id FROM conversations "
                "WHERE conversation_id IN "
                "(CAST(:expired AS uuid), CAST(:active AS uuid))"
            ),
            {"expired": expired_id, "active": active_id},
        ).scalars().all()

    assert str(active_id) in {str(item) for item in remaining}
    assert str(expired_id) not in {str(item) for item in remaining}

    memory.delete(active_id, owner)
