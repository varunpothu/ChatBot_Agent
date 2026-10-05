#!/usr/bin/env python3
"""Read-only deployment smoke checks for a deployed CoachAI API."""
from __future__ import annotations
import json, os, sys, time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

def request(base: str, path: str, token: str | None = None, method: str = "GET", body: dict | None = None):
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(base.rstrip("/") + path, data=data, headers=headers, method=method)
    with urlopen(req, timeout=20) as response:
        raw = response.read().decode()
        return response.status, json.loads(raw) if raw else {}

def main() -> int:
    base = os.getenv("COACHAI_BASE_URL", "").strip()
    token = os.getenv("COACHAI_BEARER_TOKEN", "").strip() or None
    if not base:
        print("COACHAI_BASE_URL is required", file=sys.stderr)
        return 2
    checks = [
        ("/health", lambda data: data.get("status") == "ok"),
        ("/config", lambda data: data.get("runtime_backend") in {"postgres", "memory"}),
        ("/languages", lambda data: isinstance(data, list) and len(data) >= 2),
    ]
    failures = 0
    for path, predicate in checks:
        try:
            status, data = request(base, path, token)
            ok = status == 200 and predicate(data)
            print(f"{path}: {'PASS' if ok else 'FAIL'} ({status})")
            failures += not ok
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            print(f"{path}: FAIL ({exc})")
            failures += 1
    if token:
        conversation_id = None
        try:
            started = time.perf_counter()
            status, data = request(base, "/chat", token, method="POST", body={"message":"What are the course fees?","language":"en-GB","conversation_style":"concise"})
            latency_ms = (time.perf_counter() - started) * 1000
            conversation_id = data.get("conversation_id")
            ok = status == 200 and bool(data.get("answer")) and bool(conversation_id)
            print(f"/chat: {'PASS' if ok else 'FAIL'} ({status}, {latency_ms:.1f} ms)")
            failures += not ok
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            print(f"/chat: FAIL ({exc})")
            failures += 1
        if conversation_id:
            try:
                status, data = request(base, "/conversations/" + conversation_id, token, method="DELETE")
                ok = status == 200 and data.get("deleted") is True
                print(f"conversation cleanup: {'PASS' if ok else 'FAIL'} ({status})")
                failures += not ok
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                print(f"conversation cleanup: FAIL ({exc})")
                failures += 1
    else:
        print("Authenticated /chat smoke skipped: set COACHAI_BEARER_TOKEN to enable it.")
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())