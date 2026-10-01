from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    actor: str
    subject_id: str | None
    details: dict
    created_at: str

@dataclass
class HumanReviewItem:
    review_id: str
    reason: str
    message: str
    conversation_id: str | None
    status: str = "OPEN"
    created_at: str = ""
    resolved_by: str | None = None
    resolution: str | None = None

class RuntimeOps:
    def __init__(self):
        self.audit_events: list[AuditEvent] = []
        self.reviews: dict[str, HumanReviewItem] = {}

    def audit(self, event_type: str, actor: str, subject_id: str | None, details: dict) -> AuditEvent:
        event = AuditEvent(
            uuid4().hex,
            event_type,
            actor,
            subject_id,
            details,
            datetime.now(timezone.utc).isoformat(),
        )
        self.audit_events.append(event)
        self.audit_events = self.audit_events[-1000:]
        return event

    def enqueue_review(self, reason: str, message: str, conversation_id: str | None) -> HumanReviewItem:
        item = HumanReviewItem(
            review_id=uuid4().hex,
            reason=reason,
            message=message,
            conversation_id=conversation_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.reviews[item.review_id] = item
        return item

    def list_reviews(self, status: str | None = None) -> list[HumanReviewItem]:
        values = list(self.reviews.values())
        if status:
            values = [x for x in values if x.status == status]
        return sorted(values, key=lambda x: x.created_at, reverse=True)

    def resolve_review(self, review_id: str, reviewer: str, resolution: str) -> HumanReviewItem:
        item = self.reviews[review_id]
        item.status = "RESOLVED"
        item.resolved_by = reviewer
        item.resolution = resolution
        return item

ops = RuntimeOps()
