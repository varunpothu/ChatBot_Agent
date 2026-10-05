def test_retention_script_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import scripts.purge_conversations as purge

    try:
        purge.main()
    except RuntimeError as exc:
        assert "DATABASE_URL is required" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when DATABASE_URL is missing")
