from evaluation.cost_latency import Pricing, estimate_tokens, percentile, run


def test_token_estimate_is_positive_and_deterministic():
    assert estimate_tokens("hello") == 2
    assert estimate_tokens("कोर्स की फीस कितनी है?") > 0
    assert estimate_tokens("") == 0


def test_percentile_handles_empty_and_interpolation():
    assert percentile([], 0.95) == 0.0
    assert percentile([10], 0.95) == 10
    assert percentile([10, 20, 30, 40], 0.50) == 25


def test_benchmark_avoids_llm_for_human_review():
    result = run(iterations=1, pricing=Pricing(1.0, 2.0, 0.5))
    human = next(row for row in result["cases"] if row["case"] == "human_review")
    assert human["human_review"] is True
    assert human["llm_calls"] == 0


def test_benchmark_reports_cache_and_cost_metrics():
    result = run(iterations=2, pricing=Pricing(1.0, 2.0, 0.5))
    summary = result["summary"]
    assert result["requests"] > 0
    assert 0 < summary["cache_hit_rate"] < 1
    assert summary["llm_calls"] >= 1
    assert summary["estimated_input_tokens"] > 0
    assert summary["estimated_output_tokens"] > 0
    assert summary["estimated_total_cost"] > 0
    assert summary["estimated_cost_per_1000_requests"] > 0
    assert summary["latency_ms"]["p95"] >= summary["latency_ms"]["p50"]
