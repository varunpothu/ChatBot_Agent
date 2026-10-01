from dataclasses import dataclass


@dataclass(frozen=True)
class GoldenCase:
    question: str
    expected_terms: tuple[str, ...]
    should_abstain: bool = False


GOLDEN_CASES = (
    GoldenCase("What is the Data Science course fee?", ("£2800",)),
    GoldenCase("What documents are needed to apply?", ("application", "photo ID")),
    GoldenCase("When does the evening batch start?", ("6pm", "weekdays")),
    GoldenCase("How long do I have to request a refund?", ("14 days",)),
    GoldenCase("Can I pay in cryptocurrency?", (), True),
    GoldenCase("Can you tell me the tutor's private mobile number?", (), True),
)
