from monitoring.metrics import metrics
from monitoring.alerts import evaluate_alerts

def dashboard_snapshot():
    snapshot = metrics.snapshot()
    return {
        "kpis": snapshot,
        "alerts": [a.__dict__ for a in evaluate_alerts(snapshot)],
    }
