from dataclasses import dataclass
from agents.cost_policy import classify_answer_mode, CostPolicy

@dataclass(frozen=True)
class RouteDecision:
    intent: str
    requires_retrieval: bool = True
    requires_human_review: bool = False
    answer_mode: str = "fast"

def route_query(message: str, policy: CostPolicy | None = None) -> RouteDecision:
    policy = policy or CostPolicy.from_env()
    text = message.lower()
    if any(x in text for x in ("complaint", "manager", "speak to someone", "human", "complain")):
        return RouteDecision("human_support", requires_retrieval=False, requires_human_review=True, answer_mode="fast")
    if any(x in text for x in ("fee", "price", "cost", "tuition")):
        return RouteDecision("fees", answer_mode=classify_answer_mode(message, policy))
    if any(x in text for x in ("batch", "schedule", "timing", "start date")):
        return RouteDecision("batch_schedule", answer_mode=classify_answer_mode(message, policy))
    if any(x in text for x in ("admission", "enrol", "enroll", "apply")):
        return RouteDecision("admissions", answer_mode=classify_answer_mode(message, policy))
    if any(x in text for x in ("refund", "cancel", "cancellation")):
        return RouteDecision("refund_policy", answer_mode=classify_answer_mode(message, policy))
    return RouteDecision("general_information", answer_mode=classify_answer_mode(message, policy))
