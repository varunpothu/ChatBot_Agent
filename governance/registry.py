from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from uuid import uuid5, NAMESPACE_URL

from sqlalchemy import text

from storage.postgres import PostgresRuntime


@dataclass(frozen=True)
class ModelRecord:
    model_key: str
    version: str
    provider: str
    model_name: str
    status: str
    configuration: dict
    owner: str | None
    approved_by: str | None
    approved_at: str | None
    evaluation_reference: str | None
    created_at: str


@dataclass(frozen=True)
class PromptRecord:
    prompt_key: str
    version: str
    prompt_hash: str
    template: str
    status: str
    owner: str | None
    approved_by: str | None
    approved_at: str | None
    evaluation_reference: str | None
    created_at: str


def _uuid(value: str) -> str:
    return str(uuid5(NAMESPACE_URL, value))


class GovernanceRegistry:
    """Persistent approval registry for models and prompts."""

    def __init__(self, runtime: PostgresRuntime):
        self.runtime = runtime
        self.engine = runtime.engine

    @staticmethod
    def prompt_hash(template: str) -> str:
        return hashlib.sha256(template.encode("utf-8")).hexdigest()

    def register_model(
        self,
        model_key: str,
        version: str,
        provider: str,
        model_name: str,
        configuration: dict | None = None,
        owner: str | None = None,
        evaluation_reference: str | None = None,
    ) -> ModelRecord:
        created_at = datetime.now(timezone.utc)
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO model_registry "
                    "(model_key, version, provider, model_name, status, configuration, owner, evaluation_reference, created_at) "
                    "VALUES (:model_key, :version, :provider, :model_name, 'PENDING_REVIEW', "
                    "CAST(:configuration AS jsonb), :owner, :evaluation_reference, :created_at) "
                    "ON CONFLICT (model_key, version) DO NOTHING"
                ),
                {
                    "model_key": model_key,
                    "version": version,
                    "provider": provider,
                    "model_name": model_name,
                    "configuration": json.dumps(configuration or {}),
                    "owner": owner,
                    "evaluation_reference": evaluation_reference,
                    "created_at": created_at,
                },
            )
        return self.get_model(model_key, version)

    def register_prompt(
        self,
        prompt_key: str,
        version: str,
        template: str,
        owner: str | None = None,
        evaluation_reference: str | None = None,
    ) -> PromptRecord:
        created_at = datetime.now(timezone.utc)
        digest = self.prompt_hash(template)
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO prompt_registry "
                    "(prompt_key, version, prompt_hash, template, status, owner, evaluation_reference, created_at) "
                    "VALUES (:prompt_key, :version, :prompt_hash, :template, 'PENDING_REVIEW', :owner, :evaluation_reference, :created_at) "
                    "ON CONFLICT (prompt_key, version) DO NOTHING"
                ),
                {
                    "prompt_key": prompt_key,
                    "version": version,
                    "prompt_hash": digest,
                    "template": template,
                    "owner": owner,
                    "evaluation_reference": evaluation_reference,
                    "created_at": created_at,
                },
            )
        return self.get_prompt(prompt_key, version)

    def get_model(self, model_key: str, version: str) -> ModelRecord:
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT model_key, version, provider, model_name, status, configuration, "
                    "owner, approved_by, approved_at, evaluation_reference, created_at "
                    "FROM model_registry WHERE model_key=:model_key AND version=:version"
                ),
                {"model_key": model_key, "version": version},
            ).mappings().first()
        if row is None:
            raise KeyError("Model record not found")
        return ModelRecord(
            row["model_key"], row["version"], row["provider"], row["model_name"],
            row["status"], row["configuration"] or {}, row["owner"], row["approved_by"],
            row["approved_at"].isoformat() if row["approved_at"] else None,
            row["evaluation_reference"],
            row["created_at"].isoformat(),
        )

    def get_prompt(self, prompt_key: str, version: str) -> PromptRecord:
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT prompt_key, version, prompt_hash, template, status, owner, "
                    "approved_by, approved_at, evaluation_reference, created_at "
                    "FROM prompt_registry WHERE prompt_key=:prompt_key AND version=:version"
                ),
                {"prompt_key": prompt_key, "version": version},
            ).mappings().first()
        if row is None:
            raise KeyError("Prompt record not found")
        return PromptRecord(
            row["prompt_key"], row["version"], row["prompt_hash"], row["template"],
            row["status"], row["owner"], row["approved_by"],
            row["approved_at"].isoformat() if row["approved_at"] else None,
            row["evaluation_reference"],
            row["created_at"].isoformat(),
        )

    def list_models(self) -> list[ModelRecord]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT model_key, version FROM model_registry ORDER BY created_at DESC")
            ).all()
        return [self.get_model(str(key), str(version)) for key, version in rows]

    def list_prompts(self) -> list[PromptRecord]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT prompt_key, version FROM prompt_registry ORDER BY created_at DESC")
            ).all()
        return [self.get_prompt(str(key), str(version)) for key, version in rows]

    def approve_prompt(self, prompt_key: str, version: str, reviewer: str, evaluation_reference: str | None = None) -> PromptRecord:
        with self.engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT prompt_hash FROM prompt_registry "
                    "WHERE prompt_key=:prompt_key AND version=:version "
                    "AND status IN ('PENDING_REVIEW','APPROVED') FOR UPDATE"
                ),
                {"prompt_key": prompt_key, "version": version},
            ).mappings().first()
            if row is None:
                raise KeyError("Prompt is not pending review")
            conn.execute(
                text(
                    "UPDATE prompt_registry SET status='APPROVED', approved_by=:reviewer, "
                    "approved_at=now(), evaluation_reference=COALESCE(:evaluation_reference, evaluation_reference) "
                    "WHERE prompt_key=:prompt_key AND version=:version"
                ),
                {"prompt_key": prompt_key, "version": version, "reviewer": reviewer, "evaluation_reference": evaluation_reference},
            )
        return self.get_prompt(prompt_key, version)

    def activate_prompt(self, prompt_key: str, version: str, reviewer: str, evaluation_reference: str | None = None) -> PromptRecord:
        with self.engine.begin() as conn:
            target = conn.execute(
                text(
                    "SELECT status FROM prompt_registry "
                    "WHERE prompt_key=:prompt_key AND version=:version FOR UPDATE"
                ),
                {"prompt_key": prompt_key, "version": version},
            ).mappings().first()
            if target is None or target["status"] not in {"APPROVED", "ACTIVE"}:
                raise ValueError("Prompt must be approved before activation")
            if evaluation_reference is None:
                existing = conn.execute(text("SELECT evaluation_reference FROM prompt_registry WHERE prompt_key=:prompt_key AND version=:version"), {"prompt_key": prompt_key, "version": version}).scalar_one_or_none()
                evaluation_reference = existing
            if not evaluation_reference:
                raise ValueError("Prompt activation requires an evaluation reference")

            conn.execute(
                text(
                    "UPDATE prompt_registry SET status='ARCHIVED' "
                    "WHERE prompt_key=:prompt_key AND status='ACTIVE' AND version<>:version"
                ),
                {"prompt_key": prompt_key, "version": version},
            )
            conn.execute(
                text(
                    "UPDATE prompt_registry SET status='ACTIVE', approved_by=:reviewer, approved_at=COALESCE(approved_at, now()), evaluation_reference=:evaluation_reference "
                    "WHERE prompt_key=:prompt_key AND version=:version"
                ),
                {"prompt_key": prompt_key, "version": version, "reviewer": reviewer, "evaluation_reference": evaluation_reference},
            )
        return self.get_prompt(prompt_key, version)

    def approve_model(self, model_key: str, version: str, reviewer: str, evaluation_reference: str | None = None) -> ModelRecord:
        with self.engine.begin() as conn:
            result = conn.execute(
                text(
                    "UPDATE model_registry SET status='APPROVED', approved_by=:reviewer, approved_at=now(), evaluation_reference=COALESCE(:evaluation_reference, evaluation_reference) "
                    "WHERE model_key=:model_key AND version=:version AND status IN ('PENDING_REVIEW','APPROVED')"
                ),
                {"model_key": model_key, "version": version, "reviewer": reviewer, "evaluation_reference": evaluation_reference},
            )
            if not result.rowcount:
                raise KeyError("Model is not pending review")
        return self.get_model(model_key, version)

    def activate_model(self, model_key: str, version: str, reviewer: str, evaluation_reference: str | None = None) -> ModelRecord:
        with self.engine.begin() as conn:
            target = conn.execute(
                text(
                    "SELECT status FROM model_registry WHERE model_key=:model_key AND version=:version FOR UPDATE"
                ),
                {"model_key": model_key, "version": version},
            ).mappings().first()
            if target is None or target["status"] not in {"APPROVED", "ACTIVE"}:
                raise ValueError("Model must be approved before activation")
            if evaluation_reference is None:
                evaluation_reference = conn.execute(text("SELECT evaluation_reference FROM model_registry WHERE model_key=:model_key AND version=:version"), {"model_key": model_key, "version": version}).scalar_one_or_none()
            if not evaluation_reference:
                raise ValueError("Model activation requires an evaluation reference")

            conn.execute(
                text(
                    "UPDATE model_registry SET status='ARCHIVED' "
                    "WHERE model_key=:model_key AND status='ACTIVE' AND version<>:version"
                ),
                {"model_key": model_key, "version": version},
            )
            conn.execute(
                text(
                    "UPDATE model_registry SET status='ACTIVE', approved_by=:reviewer, approved_at=COALESCE(approved_at, now()), evaluation_reference=:evaluation_reference "
                    "WHERE model_key=:model_key AND version=:version"
                ),
                {"model_key": model_key, "version": version, "reviewer": reviewer, "evaluation_reference": evaluation_reference},
            )
        return self.get_model(model_key, version)

    def active_prompt(self, prompt_key: str) -> PromptRecord | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT prompt_key, version, prompt_hash, template, status, owner, approved_by, approved_at, evaluation_reference, created_at "
                    "FROM prompt_registry WHERE prompt_key=:prompt_key AND status='ACTIVE' "
                    "ORDER BY created_at DESC LIMIT 1"
                ),
                {"prompt_key": prompt_key},
            ).mappings().first()
        return self._prompt_from_row(row) if row else None

    @staticmethod
    def _prompt_from_row(row) -> PromptRecord:
        return PromptRecord(
            row["prompt_key"], row["version"], row["prompt_hash"], row["template"],
            row["status"], row["owner"], row["approved_by"],
            row["approved_at"].isoformat() if row["approved_at"] else None,
            row["evaluation_reference"],
            row["created_at"].isoformat(),
        )

    def active_model(self, model_key: str) -> ModelRecord | None:
        with self.engine.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT model_key, version, provider, model_name, status, configuration, owner, "
                    "approved_by, approved_at, evaluation_reference, created_at FROM model_registry "
                    "WHERE model_key=:model_key AND status='ACTIVE' ORDER BY created_at DESC LIMIT 1"
                ),
                {"model_key": model_key},
            ).mappings().first()
        if row is None:
            return None
        return ModelRecord(
            row["model_key"], row["version"], row["provider"], row["model_name"],
            row["status"], row["configuration"] or {}, row["owner"], row["approved_by"],
            row["approved_at"].isoformat() if row["approved_at"] else None,
            row["evaluation_reference"],
            row["created_at"].isoformat(),
        )
