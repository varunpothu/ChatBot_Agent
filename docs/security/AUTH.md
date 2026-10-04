# CoachAI Authentication Boundary

## Development

`AUTH_MODE=development` is for local development only. The app accepts a local principal and operations endpoints use the development admin key.

## Production OIDC

`AUTH_MODE=oidc` validates a bearer JWT against the configured OIDC issuer and accepted audience values.

Required settings:

`OIDC_ISSUER_URL`
`OIDC_AUDIENCE`

The application validates issuer, audience, expiry, subject and RS256 signature. Signing keys are resolved from the issuer JWKS endpoint and cached briefly.

## API Gateway header mode

`AUTH_MODE=api_gateway` is supported when a trusted upstream gateway validates identity and injects the expected identity headers.

Expected headers:

- `X-CoachAI-User-Id`
- `X-CoachAI-Role`

Only use this mode when untrusted clients cannot bypass the trusted ingress and spoof those headers.

## Operations

Document ingestion, governance endpoints, KPI data and audit access remain protected by the admin control. Replace the development admin-key mechanism with the final production identity/role mapping before broad public operations access.

In OIDC or API-Gateway mode, admin operations require the validated principal to have the `admin` role. A shared production admin API key is not required.