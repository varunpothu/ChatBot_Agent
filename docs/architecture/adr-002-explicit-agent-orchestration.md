# ADR-002: Explicit agent orchestration

## Decision

Use a controlled workflow with named stages: routing, query rewriting, retrieval, answer generation, verification and escalation.

## Rationale

Explicit boundaries make the workflow observable, testable and easier to debug than unconstrained agent-to-agent delegation.
