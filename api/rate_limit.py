"""Per-IP rate limiting.

No user identity exists yet (auth is explicitly deferred), so this is keyed
by remote address — the practical default for an anonymous public API.
In-memory backend, matching the single-instance Docker Compose deployment;
swap for a Redis storage URI here later if this ever runs as multiple
instances.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# The LLM/cost-touching endpoints get the tightest limit.
RATE_LIMIT_EXPENSIVE = os.getenv("ARCHE_RATE_LIMIT_EXPENSIVE", "20/minute")
# DB-only endpoints (ingest/simulate/explain) can be looser.
RATE_LIMIT_STANDARD = os.getenv("ARCHE_RATE_LIMIT_STANDARD", "60/minute")
