import pytest
from mongomock_motor import AsyncMongoMockClient

from api.main import app, PrivacyAbstraction
from api.rate_limit import limiter
from memory.memory_manager import MemoryManager
from agents.simulation_agent import SimulationAgent
from agents.embeddings import EmbeddingService

app.state.memory_manager = MemoryManager(client=AsyncMongoMockClient())
app.state.privacy = PrivacyAbstraction()

# The test suite exercises real endpoint behavior (throughput/load tests fire
# dozens of sequential requests), not rate-limiting itself — and TestClient
# has no real per-caller address, so every request would share one bucket.
# Rate limiting is verified live instead (see the guardrails plan).
limiter.enabled = False


@pytest.fixture(autouse=True)
def _offline_and_deterministic(monkeypatch):
    """Keep the test suite fast, offline, and deterministic.

    Real LLM/live-search/embedding credentials may be present in the
    environment (for local dev against the real API), but the test suite
    must never depend on network access: it forces every `SimulationAgent`
    onto its heuristic fallback path, disables live web search, and disables
    the Voyage embeddings path regardless of configured keys.
    """
    monkeypatch.setattr(
        SimulationAgent,
        "_init_llm",
        lambda self: (setattr(self, "llm", None), setattr(self, "llm_provider", None)),
    )
    monkeypatch.setenv("ENABLE_FALLBACK_WEBSEARCH", "false")
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    monkeypatch.setattr(EmbeddingService, "available", lambda self: False)
