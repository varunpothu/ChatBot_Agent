from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class CloudBudget:
    max_llm_calls_per_day: int = 1000
    day: str = ""
    calls: int = 0

    def allow(self) -> bool:
        today = datetime.now(timezone.utc).date().isoformat()
        if today != self.day:
            self.day = today
            self.calls = 0
        if self.calls >= self.max_llm_calls_per_day:
            return False
        self.calls += 1
        return True
