from __future__ import annotations

import os

from storage.conversation_memory import PostgresConversationMemory
from storage.postgres import PostgresRuntime


def main() -> None:
    retention_days = int(os.getenv("CONVERSATION_RETENTION_DAYS", "30"))
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for conversation retention cleanup.")
    runtime = PostgresRuntime(database_url, auto_init_schema=False)
    memory = PostgresConversationMemory(runtime.engine)
    deleted = memory.purge_expired(retention_days)
    print(
        f"Conversation retention cleanup complete: deleted={deleted}, "
        f"retention_days={retention_days}"
    )


if __name__ == "__main__":
    main()
