from dataclasses import dataclass


@dataclass(frozen=True)
class RouteDecision:
    intent: str
    requires_retrieval: bool = True
    requires_human_review: bool = False


def route_query(message: str) -> RouteDecision:
    text = message.lower()
    if any(x in text for x in ("complaint", "manager", "speak to someone", "human")):
        return RouteDecision("human_support", requires_retrieval=False, requires_human_review=True)
    if any(x in text for x in ("fee", "price", "cost", "tuition")):
        return RouteDecision("fees")
    if any(x in text for x in ("batch", "schedule", "timing", "start date")):
        return RouteDecision("batch_schedule")
    if any(x in text for x in ("admission", "enrol", "enroll", "apply")):
        return RouteDecision("admissions")
    if any(x in text for x in ("refund", "cancel", "cancellation")):
        return RouteDecision("refund_policy")
    return RouteDecision("general_information")
