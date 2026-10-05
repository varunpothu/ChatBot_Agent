from pathlib import Path

def test_aws_smoke_script_has_safe_authenticated_flow():
    script = Path("scripts/aws_smoke_test.py").read_text(encoding="utf-8")
    assert "COACHAI_BASE_URL" in script
    assert "COACHAI_BEARER_TOKEN" in script
    assert '"/health"' in script
    assert '"/config"' in script
    assert '"/languages"' in script
    assert '"/chat"' in script
    assert 'method="DELETE"' in script