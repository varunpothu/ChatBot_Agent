from governance.runtime import GovernedPromptProvider


class FakeRegistry:
    def __init__(self, record=None):
        self.record = record

    def active_prompt(self, _key):
        return self.record


class Record:
    template = "Answer in {TARGET_LANGUAGE}. Be concise."


def test_governed_prompt_provider_renders_target_language():
    provider = GovernedPromptProvider(FakeRegistry(Record()), required=True)
    assert provider.system_prompt("friendly", "Hindi") == "Answer in Hindi. Be concise."


def test_required_governed_prompt_fails_closed():
    provider = GovernedPromptProvider(FakeRegistry(), required=True)
    try:
        provider.system_prompt("friendly", "English")
    except RuntimeError as exc:
        assert "active approved prompt" in str(exc)
    else:
        raise AssertionError("Expected missing governed prompt to fail closed")
