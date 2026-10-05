# Cost-control and abuse-resistance design

CoachAI follows a cost-firewall model.

## Request path

1. Normalize and cap input.
2. Detect prompt injection.
3. Authenticate the caller and apply a per-client, per-capability request limit.
4. Retrieve only approved evidence.
5. Use the zero-LLM fast path for simple factual questions.
6. For a deep question, check the cloud-call budget.
7. Send only the minimum evidence required.
8. Cap output tokens.
9. Verify the result.
10. Cache the verified response.

## Cost breakers

MAX_OUTPUT_TOKENS, MAX_EVIDENCE_CHARS, TOP_K_FINAL, DEEP_WORD_LIMIT, RESPONSE_CACHE_TTL_SECONDS and the daily cloud-call budget are independent brakes. A single control failure should not turn into uncontrolled spend.

## Multi-instance production

The development implementation uses process-local memory. In production, move distributed state to the appropriate platform layer:

- rate limiting: API Gateway/WAF or Redis-compatible shared state
- response cache: ElastiCache/Redis
- voice spend: authenticated STT/TTS endpoints, small payload caps and cache hits before provider calls
- cloud budget: DynamoDB or a cost-control service
- audit and conversations: PostgreSQL
- metrics and alerts: CloudWatch

The application interfaces stay small so these replacements do not change the student conversation contract.
