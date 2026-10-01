def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires external services such as PostgreSQL/Redis")
