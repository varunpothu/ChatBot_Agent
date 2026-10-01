install:
	python -m pip install -e .

run-api:
	uvicorn apps.api.main:app --reload

test:
	pytest -q
