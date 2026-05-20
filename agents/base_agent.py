from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol


class AgentState(Protocol):
    """Protocol for graph state objects passed between agents."""

    errors: list[str]


class BaseAgent(ABC):
    """Common interface for graph nodes used by the agentic orchestrator."""

    name: str = "agent"

    @abstractmethod
    async def run(self, state: AgentState) -> AgentState:
        """Execute a single graph node and return the updated state."""


class AgentResult(dict[str, Any]):
    """Thin convenience container for agent outputs."""
