from agents.budget import CloudBudget
from agents.cache import TTLCache
from agents.cost_policy import CostPolicy, classify_answer_mode, trim_evidence
from rag.embeddings import HashEmbeddingProvider

def test_simple_question_uses_fast_mode():
    assert classify_answer_mode("What is the course fee?", CostPolicy()) == "fast"

def test_complex_question_uses_deep_mode():
    assert classify_answer_mode("Why is the refund policy different and how does it work?", CostPolicy()) == "deep"

def test_evidence_is_bounded():
    assert sum(map(len, trim_evidence(["a" * 20, "b" * 20], 25))) <= 25

def test_budget_blocks_after_limit():
    budget = CloudBudget(max_llm_calls_per_day=1)
    assert budget.allow() is True
    assert budget.allow() is False

def test_cache_key_is_stable():
    assert TTLCache.key("q", "friendly", "1") == TTLCache.key("q", "friendly", "1")

def test_embeddings_are_stable():
    provider = HashEmbeddingProvider(dimensions=32)
    assert provider.embed(["hello world"]) == provider.embed(["hello world"])
