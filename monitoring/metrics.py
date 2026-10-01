from dataclasses import dataclass

@dataclass
class Metrics:
    requests: int = 0
    successful_answers: int = 0
    abstentions: int = 0
    human_escalations: int = 0
    verification_failures: int = 0
    injection_blocks: int = 0
    total_latency_ms: float = 0

    def record(self, event: str, latency_ms: float = 0):
        self.requests += 1
        self.total_latency_ms += latency_ms
        if event == "answer": self.successful_answers += 1
        if event == "abstention": self.abstentions += 1
        if event == "human_escalation": self.human_escalations += 1
        if event == "verification_failure": self.verification_failures += 1
        if event == "security_block": self.injection_blocks += 1

    def snapshot(self):
        return {
            "requests": self.requests,
            "successful_answers": self.successful_answers,
            "abstentions": self.abstentions,
            "human_escalations": self.human_escalations,
            "verification_failures": self.verification_failures,
            "injection_blocks": self.injection_blocks,
            "average_latency_ms": round(self.total_latency_ms / self.requests, 2) if self.requests else 0,
            "grounded_answer_rate": round(self.successful_answers / self.requests, 4) if self.requests else 0,
            "abstention_rate": round(self.abstentions / self.requests, 4) if self.requests else 0,
        }

metrics = Metrics()
