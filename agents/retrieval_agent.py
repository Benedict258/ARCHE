from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from .base_agent import BaseAgent, AgentState


@dataclass
class RetrievalBundle:
    memory_payload: dict[str, Any]
    candidate_pool: list[dict[str, Any]]
    query_vector: list[float]


class RetrievalAgent(BaseAgent):
    """Retrieves behavioral memory and candidate items for downstream agents."""

    name = "retrieval"

    @staticmethod
    def text_to_vector(text: str, dim: int = 16) -> list[float]:
        digest = sha256(text.encode("utf-8")).digest()
        vector: list[float] = []
        for idx in range(dim):
            vector.append(round(digest[idx % len(digest)] / 255.0, 4))
        return vector

    @classmethod
    def build_query_vector(cls, affinities: list[str], context: dict[str, Any] | None = None) -> list[float]:
        seed = " | ".join([*(affinities or ["general_interest"]), str(context or {})])
        return cls.text_to_vector(seed)

    async def run(self, state: AgentState) -> AgentState:
        return state
