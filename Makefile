install:
	python -m pip install -e .

run-api:
	uvicorn apps.api.main:app --reload

test:
	pytest -q -m "not integration"

integration:
	pytest -m integration -q

quality:
	python -m evaluation.ci_gate

benchmark:
	python -m evaluation.benchmark

compile:
	python -m compileall agents ai_controls apps dashboard evaluation governance infra knowledge language monitoring ops rag security storage translation voice workers

terraform-fmt:
	terraform fmt -recursive infra/terraform

terraform-validate:
	cd infra/terraform && terraform init -backend=false && terraform validate

db-init:
	coachai-db-init

governance-seed:
	coachai-seed-governance

worker:
	coachai-ingestion-worker
