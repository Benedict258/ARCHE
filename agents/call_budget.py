"""In-memory fixed-window call budgets for outbound LLM/embedding/search calls.

This is a cost circuit breaker, not a rate limiter for callers: rate limiting
(api/rate_limit.py) protects the API from abusive request volume; this
protects the service's own spend on Groq/Anthropic/Voyage/Serper regardless
of how the request volume is distributed. Deliberately process-local/in-memory
— matches the single-instance Docker Compose deployment, no new
infrastructure (Redis) for something that doesn't need cross-instance
coordination yet.
"""

from __future__ import annotations

import threading
import time


class CallBudget:
    def __init__(self, max_calls: int, window_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._window_start = time.monotonic()
        self._count = 0

    def allow(self) -> bool:
        """Returns True and consumes one unit of budget, or False if the
        current window's budget is exhausted."""
        with self._lock:
            now = time.monotonic()
            if now - self._window_start >= self.window_seconds:
                self._window_start = now
                self._count = 0
            if self._count >= self.max_calls:
                return False
            self._count += 1
            return True
