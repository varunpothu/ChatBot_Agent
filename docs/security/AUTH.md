# CoachAI Authentication Boundary

## Development

`AUTH_MODE=development` is for local development only. The app accepts a local principal and operations endpoints continue to use the development admin key.

## Production

`AUTH_MODE=api_gateway` requires an authenticated upstream identity.

Expected headers:

- `X-CoachAI-User-Id`: validated subject identifier.
- `X-CoachAI-Role`: `student` or `admin`.

API Gateway or an authenticated ALB must perform the JWT/OIDC validation before the request reaches the application and must overwrite these headers. The application must not be directly reachable by an untrusted client in this mode.

Student chat uses the authenticated principal. Document upload and operations remain behind the admin control until the final identity deployment is configured.

## Threat model

Retrieved documents are untrusted data, never instructions.

Trusted identity headers are only safe when the ingress layer strips client-supplied copies and injects validated claims.

Rate limits and cloud-call budgets are application safeguards, not replacements for WAF/API Gateway throttling.

## Production deployment step

Configure an API Gateway JWT authorizer or OIDC-compatible identity provider, keep the service behind the trusted ingress, strip incoming identity headers, and map validated claims into the CoachAI identity headers.