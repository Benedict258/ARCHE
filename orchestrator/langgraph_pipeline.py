from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agents.context_agent import ContextAgent
from agents.explainability_agent import ExplainabilityAgent
from agents.recommendation_agent import RecommendationAgent
from agents.review_generation_agent import ReviewGenerationAgent
from agents.retrieval_agent import RetrievalAgent
from agents.simulation_agent import SimulationAgent
from data.dataset_loader import UnifiedDatasetLoader


@dataclass
class AgentGraphState:
    user_token: str
    context: dict[str, Any] = field(default_factory=dict)
    memory_payload: dict[str, Any] = field(default_factory=dict)
    simulation: Any | None = None
    recommendation_set: Any | None = None
    explanation: Any | None = None
    errors: list[str] = field(default_factory=list)


class LangGraphStyleOrchestrator:
    """LangGraph-style multi-agent orchestrator without external graph dependency.

    The class preserves the MVP output contracts while routing through explicit
    agent nodes, which makes the system behave like a real multi-agent graph.
    """

    def __init__(self, memory_manager, privacy, dataset_loader: UnifiedDatasetLoader | None = None):
        self.memory_manager = memory_manager
        self.privacy = privacy
        self.dataset_loader = dataset_loader or UnifiedDatasetLoader()
        self.context_agent = ContextAgent()
        self.retrieval_agent = RetrievalAgent()
        self.simulation_agent = SimulationAgent()
        self.recommendation_agent = RecommendationAgent()
        self.review_generation_agent = ReviewGenerationAgent()
        self.explainability_agent = ExplainabilityAgent()
        self._seed_real_datasets()

    def _seed_real_datasets(self) -> None:
        if not getattr(self.dataset_loader, "has_real_datasets", lambda: False)():
            return
        try:
            self.dataset_loader.seed_vector_store(self.memory_manager.vector_store, limit_per_source=100)
        except Exception:
            # Real datasets are optional and should never break the demo path.
            pass

    def _retrieve(self, user_token: str) -> dict[str, Any]:
        storage_token = self.privacy.anonymize_token(user_token, "user") or user_token
        return self.memory_manager.retrieve_all(storage_token)

    async def run_simulation(self, user_token: str, context: Any):
        state = AgentGraphState(user_token=user_token, context=dict(context.model_dump()) if hasattr(context, "model_dump") else dict(context or {}))
        state.memory_payload = self._retrieve(user_token)
        state.simulation = self.simulation_agent.simulate(user_token, context, state.memory_payload)
        return state.simulation

    async def run_recommendation(self, user_token: str, context: Any, n: int = 10):
        state = AgentGraphState(user_token=user_token, context=dict(context.model_dump()) if hasattr(context, "model_dump") else dict(context or {}))
        state.memory_payload = self._retrieve(user_token)
        normalized_context = self.context_agent.normalize(state.context)
        simulation_context_cls = self._simulation_context_class()
        simulation_context = simulation_context_cls(
            time_bucket=normalized_context.time_bucket,
            day_type=normalized_context.day_type,
            device_class=normalized_context.device_class,
            network_quality=normalized_context.network_quality,
            region_tier=normalized_context.region_tier,
            session_depth=normalized_context.session_depth,
            entry_point=normalized_context.entry_point,
        )
        state.simulation = self.simulation_agent.simulate(user_token, simulation_context, state.memory_payload)
        state.recommendation_set = self.recommendation_agent.rank_candidates(
            user_token=user_token,
            simulation=state.simulation,
            context=simulation_context,
            n=n,
            memory_vector_store=self.memory_manager.vector_store,
            dataset_loader=self.dataset_loader,
        )
        self._persist_last_recommendation(user_token, state.simulation, state.recommendation_set)
        return state.recommendation_set

    async def run_simulate_review(
        self,
        *,
        user_token: str,
        user_history: list[dict[str, Any]],
        item: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Task A flow: context -> simulation -> review generation.

        This keeps Task A on the same orchestrated agent path as Task B while
        preserving deterministic output for hackathon MVP reliability.
        """
        state = AgentGraphState(user_token=user_token, context=dict(context or {}))

        normalized_context = self.context_agent.normalize(state.context)
        simulation_context = type(
            "TaskASimulateContext",
            (),
            {
                "time_bucket": normalized_context.time_bucket,
                "day_type": normalized_context.day_type,
                "device_class": normalized_context.device_class,
                "network_quality": normalized_context.network_quality,
                "region_tier": normalized_context.region_tier,
                "session_depth": normalized_context.session_depth,
                "entry_point": normalized_context.entry_point,
            },
        )()

        # For Task A, simulation should be grounded in provided user history.
        state.memory_payload = self._build_history_memory_payload(user_token=user_token, user_history=user_history)
        state.simulation = self.simulation_agent.simulate(user_token, simulation_context, state.memory_payload)

        return self.review_generation_agent.generate(
            user_token=user_token,
            user_history=user_history,
            item=item,
            context=state.context,
            simulation=state.simulation,
        )

    async def route_task_a(
        self,
        *,
        user_token: str,
        user_history: list[dict[str, Any]],
        item: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Explicit Task A route: simulate-review pipeline."""
        return await self.run_simulate_review(
            user_token=user_token,
            user_history=user_history,
            item=item,
            context=context,
        )

    async def route_task_b(
        self,
        *,
        action: str,
        user_token: str,
        context: Any | None = None,
        n: int = 10,
        recommendation_id: str | None = None,
    ) -> Any:
        """Explicit Task B route: recommend/explain pipeline."""
        normalized_action = action.strip().lower()
        if normalized_action == "recommend":
            return await self.run_recommendation(user_token, context or {}, n=n)
        if normalized_action == "explain":
            if not recommendation_id:
                raise ValueError("recommendation_id is required for explain action")
            return await self.run_explanation(user_token, recommendation_id)
        raise ValueError(f"unsupported Task B action: {action}")

    async def run_explanation(self, user_token: str, recommendation_id: str):
        return self.explainability_agent.explain(user_token, recommendation_id)

    def _persist_last_recommendation(self, user_token: str, simulation, recommendation_set) -> None:
        import json
        from pathlib import Path

        out_path = Path("data/last_recommend.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out = {
            "user_token": user_token,
            "simulation_basis": simulation.simulation_basis,
            "recommendations": [r.model_dump() for r in recommendation_set.recommendations],
            "simulated_at": simulation.simulated_at.isoformat(),
            "behavioral_snapshot": simulation.behavioral_snapshot.model_dump(),
            "context": {
                "time_bucket": simulation.context_modifiers.time_boosts[0] if simulation.context_modifiers.time_boosts else None,
                "device_class": next(
                    (boost.split(":", 1)[1] for boost in simulation.context_modifiers.time_boosts if boost.startswith("device:")),
                    None,
                ),
            },
        }
        out_path.write_text(json.dumps(out, ensure_ascii=False, default=str), encoding="utf-8")

    @staticmethod
    def _simulation_context_class():
        from api.main import SimulateContext

        return SimulateContext

    @staticmethod
    def _build_history_memory_payload(*, user_token: str, user_history: list[dict[str, Any]]) -> dict[str, Any]:
        from datetime import datetime, timezone

        timestamp = int(datetime.now(timezone.utc).timestamp())
        session_rows = []
        for idx, entry in enumerate(user_history, start=1):
            session_rows.append(
                (
                    idx,
                    user_token,
                    "review",
                    entry.get("item_name"),
                    entry.get("item_category"),
                    {},
                    None,
                    None,
                    idx,
                    timestamp - (len(user_history) - idx),
                )
            )
        return {"session": session_rows, "is_cold_start": len(session_rows) == 0}
