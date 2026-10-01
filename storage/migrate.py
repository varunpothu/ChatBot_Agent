from __future__ import annotations

import os

from storage.postgres import PostgresRuntime


def main() -> None:
    runtime = PostgresRuntime(
        os.getenv("DATABASE_URL", ""),
        auto_init_schema=True,
    )
    runtime.engine.dispose()
    print("CoachAI database schema initialized.")


if __name__ == "__main__":
    main()
