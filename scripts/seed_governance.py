from __future__ import annotations

import os

from agents.answer_prompt import build_system_prompt
from governance.registry import GovernanceRegistry
from storage.postgres import PostgresRuntime


def main() -> None:
    runtime = PostgresRuntime(os.getenv("DATABASE_URL", ""), auto_init_schema=False)
    registry = GovernanceRegistry(runtime)

    for style in ("friendly", "professional", "concise"):
        template = build_system_prompt(style, "{TARGET_LANGUAGE}")
        registry.register_prompt(
            f"answer.{style}",
            os.getenv("PROMPT_VERSION", "v1"),
            template,
            owner=os.getenv("GOVERNANCE_OWNER", "coachai-platform"),
        )

    model_id = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
    registry.register_model(
        "bedrock-answer",
        os.getenv("MODEL_VERSION", "v1"),
        "bedrock",
        model_id,
        configuration={
            "max_output_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "180")),
            "temperature": 0,
        },
        owner=os.getenv("GOVERNANCE_OWNER", "coachai-platform"),
    )

    print("Governance records registered as PENDING_REVIEW.")
    print("Review, evaluate, approve and activate each prompt/model before enabling *_GOVERNANCE_REQUIRED=true.")


if __name__ == "__main__":
    main()
