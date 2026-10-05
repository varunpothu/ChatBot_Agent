from pathlib import Path


def test_production_terraform_requires_https_certificate():
    variables = Path("infra/terraform/variables.tf").read_text(encoding="utf-8")
    alb = Path("infra/terraform/alb.tf").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/deploy.yml").read_text(encoding="utf-8")

    assert 'variable "enforce_https"' in variables
    assert 'condition     = !var.enforce_https || trimspace(var.certificate_arn) != ""' in alb
    assert 'TF_VAR_enforce_https: "true"' in workflow


def test_storage_is_private_and_versioned():
    storage = Path("infra/terraform/storage.tf").read_text(encoding="utf-8")
    assert 'block_public_acls       = true' in storage
    assert 'block_public_policy     = true' in storage
    assert 'status = "Enabled"' in storage
    assert 'scan_on_push = true' in storage
