"""In-memory semantic index over the recommendation catalog.

Builds real embeddings for catalog items (via `EmbeddingService`) once per
process and answers similarity queries with brute-force cosine similarity.
This is intentionally simple: at the catalog sizes this system currently
serves (a small demo fallback list, or a modest `data/yelp_processed` split),
brute-force search over a handful of hundred/thousand vectors is fast and
avoids standing up a dedicated vector database for a feature that has no
real scale requirement yet. If the catalog grows into the tens of thousands
of items, replace this with a real ANN index (e.g. Atlas Vector Search).
"""

from __future__ import annotations

import math
from typing import Any

from agents.embeddings import EmbeddingService


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    length = min(len(a), len(b))
    a, b = a[:length], b[:length]
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if not norm_a or not norm_b:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (norm_a * norm_b)


class CatalogSemanticIndex:
    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self._vectors: dict[str, list[float]] = {}
        self._built_for_keys: frozenset[str] | None = None

    def available(self) -> bool:
        return self.embedding_service.available()

    def has_vectors(self) -> bool:
        return bool(self._vectors)

    async def ensure_built(self, catalog: list[dict[str, Any]]) -> None:
        if not self.available() or not catalog:
            return

        catalog_keys = frozenset(str(item.get("item_id") or item.get("key") or "") for item in catalog)
        if self._built_for_keys == catalog_keys:
            return

        texts = [f"{item.get('item_name') or ''} {item.get('description') or ''}".strip() for item in catalog]
        keys = [str(item.get("item_id") or item.get("key") or "") for item in catalog]

        embeddings = await self.embedding_service.embed(texts, input_type="document")
        if embeddings is None:
            return

        self._vectors = {key: vector for key, vector in zip(keys, embeddings) if key}
        self._built_for_keys = catalog_keys

    def top_k(self, query_vector: list[float], k: int) -> list[tuple[str, float]]:
        if not self._vectors or not query_vector:
            return []
        scored = [(key, _cosine_similarity(query_vector, vector)) for key, vector in self._vectors.items()]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:k]
