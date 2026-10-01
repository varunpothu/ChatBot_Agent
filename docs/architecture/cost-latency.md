# Cost and latency architecture

CoachAI uses a **fast path first** design.

## 1. Zero-LLM fast path

Simple fact lookups are answered from the highest-ranked approved evidence using deterministic extraction and formatting. This means a question such as “What is the course fee?” does not require a paid generation call.

## 2. One-call deep path

Only questions that need synthesis, comparison, explanation or multi-part reasoning may use a cloud model. The system sends a maximum of three evidence chunks and a strict context budget. There is no multi-agent LLM loop for ordinary student questions.

## 3. Response cache

A process-local TTL cache stores responses by normalized question, style and knowledge generation. A document update changes the generation and automatically invalidates old answers.

## 4. Evidence compression

Retrieved content is trimmed before generation. The model never receives the entire document when a few sentences are enough.

## 5. Output budget

Generation uses a low maximum output-token ceiling. Answers are intentionally short because the student experience should feel conversational, not like a report.

## 6. Voice cost control

Browser speech input remains the default because it avoids server-side transcription charges. Paid TTS is opt-in. Repeated audio can be cached. The textual answer is generated once; voice is a delivery layer.

## 7. Provider routing

Local extraction handles simple lookups. A small cloud model handles only the deep path. Higher-cost models are reserved for an explicitly configured escalation path.

## 8. AWS production strategy

Amazon Bedrock supports intelligent prompt routing between models for quality/cost optimization. Bedrock prompt caching can reduce repeated input-token costs and latency for supported models; static prompt instructions and reusable context should be placed before dynamic user content.

These controls are deliberately provider-neutral so the application can switch providers without changing the retrieval or governance contracts.
