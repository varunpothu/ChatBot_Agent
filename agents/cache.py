import hashlib
import time
from dataclasses import dataclass
from typing import Any

@dataclass
class _Entry:
    value: Any
    expires_at: float

class TTLCache:
    """Tiny process-local cache for ultra-fast repeated requests.

    The key should include a knowledge-store generation/version so a document
    change automatically makes old answers unreachable.
    """
    def __init__(self, ttl_seconds: int = 300, max_items: int = 512):
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._items: dict[str, _Entry] = {}

    @staticmethod
    def key(*parts: str) -> str:
        raw = "\x1f".join(parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Any | None:
        entry = self._items.get(key)
        if entry is None:
            return None
        if entry.expires_at <= time.monotonic():
            self._items.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any) -> None:
        if len(self._items) >= self.max_items:
            oldest = min(self._items, key=lambda k: self._items[k].expires_at)
            self._items.pop(oldest, None)
        self._items[key] = _Entry(value=value, expires_at=time.monotonic() + self.ttl_seconds)
