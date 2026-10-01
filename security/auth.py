from __future__ import annotations

from dataclasses import dataclass
import os

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str = "student"


def require_principal(request: Request) -> Principal:
    mode = os.getenv("AUTH_MODE", "development").lower()
    if mode == "development":
        return Principal(
            user_id=request.headers.get("x-coachai-user-id", "local-user"),
            role=request.headers.get("x-coachai-role", "student"),
        )

    if mode == "api_gateway":
        # API Gateway/ALB must authenticate upstream and overwrite these
        # headers so clients cannot supply their own identity.
        user_id = request.headers.get("x-coachai-user-id") or request.headers.get(
            "x-amzn-oidc-identity"
        )
        if not user_id:
            raise HTTPException(401, "Authenticated user identity is required.")
        role = request.headers.get("x-coachai-role", "student")
        if role not in {"student", "admin"}:
            raise HTTPException(403, "Unsupported user role.")
        return Principal(user_id=user_id, role=role)

    raise HTTPException(503, "Unsupported AUTH_MODE configuration.")
