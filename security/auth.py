from __future__ import annotations

from dataclasses import dataclass
import os

from fastapi import HTTPException, Request

try:
    import jwt
except ImportError:
    jwt = None


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: str = "student"


class OIDCValidator:
    """Validate RS256 bearer tokens against a configured OIDC issuer."""

    def __init__(self, issuer_url: str, audience: list[str], cache_ttl_seconds: int = 900):
        self.issuer_url = issuer_url.rstrip("/")
        self.audience = audience
        self.cache_ttl_seconds = cache_ttl_seconds
        self.jwks_url = os.getenv("OIDC_JWKS_URL", "").strip() or f"{self.issuer_url}/.well-known/jwks.json"
        self._jwks_client = None

    def _client(self):
        if jwt is None:
            raise RuntimeError("PyJWT is required for AUTH_MODE=oidc.")
        if self._jwks_client is None:
            self._jwks_client = jwt.PyJWKClient(
                self.jwks_url,
                cache_jwk_set=True,
                lifespan=self.cache_ttl_seconds,
            )
        return self._jwks_client

    def validate(self, token: str) -> Principal:
        if jwt is None:
            raise HTTPException(503, "OIDC support is not installed.")
        if not self.audience:
            raise HTTPException(503, "OIDC_AUDIENCE is not configured.")
        try:
            signing_key = self._client().get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                audience=self.audience or None,
                issuer=self.issuer_url,
                options={"require": ["sub", "iss", "exp"]},
            )
            role = str(claims.get("custom:role") or claims.get("role") or "student")
            if role not in {"student", "admin"}:
                raise HTTPException(403, "Unsupported user role.")
            return Principal(user_id=str(claims["sub"]), role=role)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(401, f"Invalid OIDC access token: {exc}") from exc


def require_principal(request: Request) -> Principal:
    mode = os.getenv("AUTH_MODE", "development").lower()

    if mode == "development":
        return Principal(
            user_id=request.headers.get("x-coachai-user-id", "local-user"),
            role=request.headers.get("x-coachai-role", "student"),
        )

    if mode == "api_gateway":
        user_id = request.headers.get("x-coachai-user-id") or request.headers.get(
            "x-amzn-oidc-identity"
        )
        if not user_id:
            raise HTTPException(401, "Authenticated user identity is required.")
        role = request.headers.get("x-coachai-role", "student")
        if role not in {"student", "admin"}:
            raise HTTPException(403, "Unsupported user role.")
        return Principal(user_id=user_id, role=role)

    if mode == "oidc":
        authorization = request.headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(401, "Bearer access token is required.")
        issuer = os.getenv("OIDC_ISSUER_URL", "").strip()
        audience = [item.strip() for item in os.getenv("OIDC_AUDIENCE", "").split(",") if item.strip()]
        if not issuer:
            raise HTTPException(503, "OIDC_ISSUER_URL is not configured.")
        token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(401, "Bearer access token is empty.")
        return OIDCValidator(issuer, audience).validate(token)

    raise HTTPException(503, "Unsupported AUTH_MODE configuration.")
