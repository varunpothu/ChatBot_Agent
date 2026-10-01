from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class ModelVersion:
    model_id: str
    provider: str
    version: str
    prompt_version: str
    status: str
    owner: str
    registered_at: datetime

MODEL_REGISTRY: list[ModelVersion] = []

def register_model(model_id: str, provider: str, version: str, prompt_version: str, owner: str) -> ModelVersion:
    model = ModelVersion(model_id, provider, version, prompt_version, "REGISTERED", owner, datetime.now(timezone.utc))
    MODEL_REGISTRY.append(model)
    return model

def list_models() -> list[dict]:
    return [m.__dict__ for m in MODEL_REGISTRY]
