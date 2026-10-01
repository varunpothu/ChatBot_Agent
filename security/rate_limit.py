from collections import defaultdict, deque
from time import monotonic

class SlidingWindowLimiter:
    """Local safety net.

    For multi-instance production use, enforce the equivalent policy at an
    API Gateway/WAF or distributed rate-limit layer.
    """
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = monotonic()
        q = self._events[key]
        while q and now - q[0] >= self.window_seconds:
            q.popleft()
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True
