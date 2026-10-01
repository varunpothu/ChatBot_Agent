from dataclasses import dataclass

@dataclass(frozen=True)
class Alert:
    severity: str
    code: str
    message: str
    action: str

def evaluate_alerts(snapshot: dict) -> list[Alert]:
    alerts = []
    if snapshot["verification_failures"] > 0:
        alerts.append(Alert("CRITICAL","GROUNDING_FAILURE","A response failed its evidence check.","Pause release and review the model, prompt and evidence."))
    if snapshot["injection_blocks"] >= 3:
        alerts.append(Alert("HIGH","SECURITY_SPIKE","Several unsafe input patterns were blocked.","Review security telemetry and affected sessions."))
    if snapshot["abstention_rate"] > 0.40 and snapshot["requests"] >= 10:
        alerts.append(Alert("MEDIUM","ABSTENTION_SPIKE","More than 40 percent of requests were not answerable.","Check document coverage and retrieval."))
    if snapshot["average_latency_ms"] > 3000:
        alerts.append(Alert("HIGH","LATENCY_SLA","Average response time exceeded 3 seconds.","Inspect retrieval, model and infrastructure latency."))
    return alerts
