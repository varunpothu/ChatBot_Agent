# ADR-001: Grounded answering over free-form generation

## Decision

Answers must be generated from retrieved, authorized, active evidence. Unsupported or conflicting evidence should cause the system to abstain or escalate.

## Why

Operational coaching-centre information such as fees, schedules and policies can change. The assistant should be traceable to an approved source rather than rely on unsupported model memory.

## Consequence

Retrieval quality, source metadata, citation tracking and verification are first-class system components.
