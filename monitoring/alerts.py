from dataclasses import dataclass

@dataclass(frozen=True)
class Alert:
    severity: str
    code: str
    message: str
    action: str

def evaluate_alerts(kpis: dict) -> list[Alert]:
    alerts = []
    if kpis.get("verification_failures", 0) > 0:
        alerts.append(Alert("CRITICAL", "GROUNDING_FAILURE", "One or more answers failed grounding verification.", "Disable release and inspect the failed cases."))
    if kpis.get("injection_blocks", 0) >= 3:
        alerts.append(Alert("HIGH", "SECURITY_SPIKE", "Prompt-injection blocks reached the configured spike threshold.", "Review traffic and tighten the gateway/WAF policy."))
    if kpis.get("abstention_rate", 0) > 0.40 and kpis.get("requests", 0) >= 10:
        alerts.append(Alert("MEDIUM", "ABSTENTION_SPIKE", "More than 40% of requests are being rejected or escalated.", "Review retrieval coverage and source freshness."))
    if kpis.get("average_latency_ms", 0) > 3000:
        alerts.append(Alert("HIGH", "LATENCY_SLA", "Average response latency is above 3000 ms.", "Keep the fast path dominant and inspect provider latency."))
    if kpis.get("llm_call_rate", 0) > 0.30 and kpis.get("requests", 0) >= 20:
        alerts.append(Alert("HIGH", "LLM_COST_SPIKE", "Cloud-model usage is above 30% of requests.", "Inspect routing rules, repeated queries and cache hit rate before scaling spend."))
    if kpis.get("budget_blocks", 0) > 0:
        alerts.append(Alert("HIGH", "LLM_BUDGET_BLOCK", "The daily cloud-model budget has been reached.", "Keep the fast path active and review the workload before increasing the budget."))
    if kpis.get("rate_limit_blocks", 0) > 0:
        alerts.append(Alert("MEDIUM", "RATE_LIMITING", "Some requests were blocked by abuse protection.", "Review traffic patterns and distributed gateway limits."))
    return alerts
