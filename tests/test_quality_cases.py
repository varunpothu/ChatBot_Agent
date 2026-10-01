from tests.quality_cases import GOLDEN_CASES


def test_golden_suite_contains_supported_and_abstention_cases():
    assert len(GOLDEN_CASES) >= 6
    assert any(case.should_abstain for case in GOLDEN_CASES)
    assert any(not case.should_abstain for case in GOLDEN_CASES)
