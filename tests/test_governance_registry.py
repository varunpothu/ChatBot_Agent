from governance.registry import GovernanceRegistry


def test_prompt_hash_is_deterministic():
    value = GovernanceRegistry.prompt_hash("CoachAI prompt")
    assert value == GovernanceRegistry.prompt_hash("CoachAI prompt")
    assert len(value) == 64
