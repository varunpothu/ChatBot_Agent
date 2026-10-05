from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from dataclasses import dataclass
from typing import Iterable

from agents.cache import TTLCache
from agents.cost_policy import CostPolicy
from agents.router import route_query


@dataclass(frozen=True)
class Pricing:
    input_per_1k: float = 0.0
    output_per_1k: float = 0.0
    translation_per_1k_chars: float = 0.0

    @classmethod
    def from_env(cls) -> "Pricing":
        return cls(
            input_per_1k=float(os.getenv("BENCHMARK_INPUT_COST_PER_1K", "0")),
            output_per_1k=float(os.getenv("BENCHMARK_OUTPUT_COST_PER_1K", "0")),
            translation_per_1k_chars=float(
                os.getenv("BENCHMARK_TRANSLATION_COST_PER_1K_CHARS", "0")
            ),
        )


CASES = (
    ("fast_fact", "What is the course fee?", "en-GB", 0),
    ("fast_fact", "What documents do I need to apply?", "en-GB", 0),
    ("fast_fact", "When does the evening batch start?", "en-GB", 0),
    ("deep_explanation", "Can you explain the difference between the weekday and evening options and recommend one?", "en-GB", 1),
    ("follow_up", "Is that fee refundable?", "en-GB", 1),
    ("multilingual", "कोर्स की फीस कितनी है?", "hi-IN", 1),
    ("human_review", "I want to speak to a human manager.", "en-GB", 0),
)


def estimate_tokens(text: str) -> int:
    """Conservative, provider-neutral estimate for English and multilingual text."""
    if not text:
        return 0
    # Roughly 4 characters/token is useful for planning, not billing.
    return max(1, (len(text) + 3) // 4)


def estimate_output_tokens(mode: str, policy: CostPolicy) -> int:
    if mode == "fast":
        return min(48, policy.max_output_tokens)
    return min(policy.max_output_tokens, 120)


def percentile(values: Iterable[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def run(iterations: int = 20, pricing: Pricing | None = None) -> dict:
    if iterations < 1:
        raise ValueError("iterations must be >= 1")

    policy = CostPolicy.from_env()
    pricing = pricing or Pricing.from_env()
    cache = TTLCache(ttl_seconds=300, max_items=256)

    rows: list[dict] = []
    for iteration in range(iterations):
        for name, question, language, expected_llm in CASES:
            started = time.perf_counter()
            decision = route_query(question, policy)
            key = cache.key("benchmark-v1", language, question.lower().strip())
            cached = cache.get(key) is not None

            # Human-review requests are deliberately not sent to the LLM.
            llm_calls = 0 if decision.requires_human_review else (
                0 if cached else int(decision.answer_mode == "deep" or expected_llm)
            )
            input_tokens = 0
            output_tokens = 0
            if llm_calls:
                input_tokens = estimate_tokens(question) + estimate_tokens(
                    "approved evidence"
                )
                output_tokens = estimate_output_tokens(decision.answer_mode, policy)

            if not cached and not decision.requires_human_review:
                cache.set(key, True)

            elapsed_ms = (time.perf_counter() - started) * 1000
            translation_chars = len(question) if language != "en-GB" and llm_calls else 0
            estimated_cost = (
                input_tokens / 1000 * pricing.input_per_1k
                + output_tokens / 1000 * pricing.output_per_1k
                + translation_chars / 1000 * pricing.translation_per_1k_chars
            )
            rows.append(
                {
                    "case": name,
                    "language": language,
                    "route": decision.answer_mode,
                    "human_review": decision.requires_human_review,
                    "cache_hit": cached,
                    "llm_calls": llm_calls,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "translation_characters": translation_chars,
                    "estimated_cost": estimated_cost,
                    "latency_ms": elapsed_ms,
                }
            )

    requests = len(rows)
    total_calls = sum(row["llm_calls"] for row in rows)
    total_input = sum(row["input_tokens"] for row in rows)
    total_output = sum(row["output_tokens"] for row in rows)
    total_translation = sum(row["translation_characters"] for row in rows)
    total_cost = sum(row["estimated_cost"] for row in rows)
    cache_hits = sum(row["cache_hit"] for row in rows)
    latencies = [row["latency_ms"] for row in rows]

    return {
        "iterations": iterations,
        "requests": requests,
        "pricing": pricing.__dict__,
        "summary": {
            "llm_calls": total_calls,
            "llm_call_rate": round(total_calls / requests, 4),
            "cache_hits": cache_hits,
            "cache_hit_rate": round(cache_hits / requests, 4),
            "estimated_input_tokens": total_input,
            "estimated_output_tokens": total_output,
            "translation_characters": total_translation,
            "estimated_total_cost": round(total_cost, 8),
            "estimated_cost_per_request": round(total_cost / requests, 8),
            "estimated_cost_per_1000_requests": round(total_cost / requests * 1000, 6),
            "latency_ms": {
                "p50": round(percentile(latencies, 0.50), 3),
                "p95": round(percentile(latencies, 0.95), 3),
                "max": round(max(latencies), 3),
            },
        },
        "cases": rows,
        "notes": [
            "Token counts are planning estimates, not provider billing records.",
            "Cost is zero unless benchmark pricing environment variables are supplied.",
            "Latency measures local routing/cache overhead only; it is not AWS end-to-end latency.",
            "Run a live AWS benchmark separately before using production latency or cost claims.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic CoachAI cost/latency benchmark.")
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()
    print(json.dumps(run(args.iterations), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
