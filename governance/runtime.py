from __future__ import annotations

import os

from governance.registry import GovernanceRegistry


class GovernedPromptProvider:
    """Resolve only ACTIVE, approved prompt templates for runtime use."""

    def __init__(self, registry: GovernanceRegistry, required: bool = False):
        self.registry = registry
        self.required = required

    def system_prompt(self, style: str, target_language: str) -> str | None:
        record = self.registry.active_prompt(f"answer.{style}")
        if record is None:
            if self.required:
                raise RuntimeError(f"No active approved prompt for answer.{style}")
            return None

        template = record.template.replace("{TARGET_LANGUAGE}", target_language)
        return template


def prompt_governance_required() -> bool:
    return os.getenv("PROMPT_GOVERNANCE_REQUIRED", "false").lower() == "true"
