"""Voyage AI embeddings client.

Optional provider, matching the graceful-degradation pattern used throughout
this codebase for LLM providers (`SimulationAgent`) and live search
(`LiveSearchService`): if `VOYAGE_API_KEY` isn't configured, `available()`
returns False and callers skip the semantic-similarity signal entirely
instead of failing.
"""

from __future__ import annotations

import logging
import os
from typing import Literal

import httpx

from agents.call_budget import CallBudget
from api.metrics import embedding_calls_total

_VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"

_embedding_budget = CallBudget(
    max_calls=int(os.getenv("ARCHE_EMBEDDING_BUDGET_PER_MINUTE", "60")),
    window_seconds=60,
)


class EmbeddingService:
    name = "embeddings"

    def __init__(self) -> None:
        self.api_key = os.getenv("VOYAGE_API_KEY")
        self.model = os.getenv("VOYAGE_MODEL", "voyage-3.5-lite")
        self.logger = logging.getLogger("arche.embeddings")

    def available(self) -> bool:
        return bool(self.api_key)

    async def embed(
        self, texts: list[str], input_type: Literal["query", "document"] = "document"
    ) -> list[list[float]] | None:
        """Return one embedding vector per input text, or None on any failure."""
        if not self.available() or not texts:
            return None

        if not _embedding_budget.allow():
            embedding_calls_total.labels(provider="voyage", outcome="budget_exceeded").inc()
            return None

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    _VOYAGE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"input": texts, "model": self.model, "input_type": input_type},
                )
                response.raise_for_status()
                data = response.json()

            embeddings = [item["embedding"] for item in data.get("data", [])]
            if len(embeddings) != len(texts):
                self.logger.warning(
                    "voyage_embedding_count_mismatch requested=%s received=%s", len(texts), len(embeddings)
                )
                embedding_calls_total.labels(provider="voyage", outcome="error").inc()
                return None
            embedding_calls_total.labels(provider="voyage", outcome="success").inc()
            return embeddings
        except Exception as exc:
            self.logger.warning("voyage_embedding_error error=%s", str(exc))
            embedding_calls_total.labels(provider="voyage", outcome="error").inc()
            return None
