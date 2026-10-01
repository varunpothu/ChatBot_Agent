import pytest

from agents.orchestrator import CoachAIOrchestrator

@pytest.mark.asyncio
async def test_unknown_question_abstains_without_evidence():
    result = await CoachAIOrchestrator().run("Tell me the secret scholarship rule.")
    assert result["abstained"] is True
    assert result["next_action"] == "human_review"
