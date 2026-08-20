from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from types import SimpleNamespace

from agents.context_agent import ContextAgent
from agents.explainability_agent import ExplainabilityAgent
from agents.review_generation_agent import ReviewGenerationAgent
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

    Task B's recommendation flow (catalog assembly, live search, LLM ranking)
    lives in `agents/recommendation_pipeline.py` and is called directly from
    `api/routes/task_b.py` — it is not routed through this orchestrator.
    """

    def __init__(self, memory_manager, privacy, dataset_loader: UnifiedDatasetLoader | None = None):
        self.memory_manager = memory_manager
        self.privacy = privacy
        self.dataset_loader = dataset_loader or UnifiedDatasetLoader()
        self.context_agent = ContextAgent()
        self.simulation_agent = SimulationAgent()
        self.review_generation_agent = ReviewGenerationAgent()
        self.explainability_agent = ExplainabilityAgent()

    async def _retrieve(self, user_token: str) -> dict[str, Any]:
        storage_token = self.privacy.anonymize_token(user_token, "user") or user_token
        return await self.memory_manager.retrieve_all(storage_token)

    async def run_simulation(self, user_token: str, context: Any):
        state = AgentGraphState(user_token=user_token, context=dict(context.model_dump()) if hasattr(context, "model_dump") else dict(context or {}))
        state.memory_payload = await self._retrieve(user_token)
        state.simulation = self.simulation_agent.simulate(user_token, context, state.memory_payload)
        return state.simulation

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
        preserving deterministic output for reliability.
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
        if getattr(self.simulation_agent, "llm", None) is not None:
            llm_snapshot = await self.simulation_agent.simulate_brain_state(
                user_token, state.memory_payload, state.context
            )
            state.simulation = SimpleNamespace(
                user_token=user_token,
                simulated_at=None,
                behavioral_snapshot=SimpleNamespace(
                    current_intent=llm_snapshot.get("current_intent", "exploratory_browsing"),
                    preference_cluster=llm_snapshot.get("preference_cluster", "A"),
                    top_affinities=llm_snapshot.get("top_affinities", []) or [],
                    rejection_signals=llm_snapshot.get("rejection_signals", []) or [],
                    engagement_mode=llm_snapshot.get("engagement_mode", "scanning"),
                    exploration_readiness=float(llm_snapshot.get("exploration_readiness", 0.5)),
                    purchase_probability=float(llm_snapshot.get("purchase_probability", 0.3)),
                ),
                context_modifiers=SimpleNamespace(
                    time_boosts=[normalized_context.time_bucket] if normalized_context.time_bucket else [],
                    suppressed_categories=[],
                    active_context=f"{normalized_context.time_bucket or 'evening'}_session",
                ),
                cold_start_confidence=0.9,
                simulation_basis=str(llm_snapshot.get("behavioral_basis") or "llm_simulation"),
                memory_sources=["behavioral_history", "context_signal"],
            )
        else:
            state.simulation = self.simulation_agent.simulate(user_token, simulation_context, state.memory_payload)

        return await self.review_generation_agent.generate(
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
        recommendation_id: str | None = None,
    ) -> Any:
        """Explicit Task B route: explain pipeline.

        Recommendation ranking itself is handled by
        `agents/recommendation_pipeline.py`, called directly from
        `api/routes/task_b.py`.
        """
        normalized_action = action.strip().lower()
        if normalized_action == "explain":
            if not recommendation_id:
                raise ValueError("recommendation_id is required for explain action")
            return await self.run_explanation(user_token, recommendation_id)
        raise ValueError(f"unsupported Task B action: {action}")

    async def run_explanation(self, user_token: str, recommendation_id: str):
        return self.explainability_agent.explain(user_token, recommendation_id)

    @staticmethod
    def _build_history_memory_payload(*, user_token: str, user_history: list[dict[str, Any]]) -> dict[str, Any]:
        from datetime import datetime, timezone

        timestamp = int(datetime.now(timezone.utc).timestamp())
        session_rows = []
        for idx, entry in enumerate(user_history, start=1):
            session_rows.append(
                {
                    "user_token": user_token,
                    "event_type": "review",
                    "item_token": entry.get("item_name"),
                    "item_category": entry.get("item_category"),
                    "session_context": {},
                    "engagement_depth": None,
                    "dwell_time_seconds": None,
                    "sequence_position": idx,
                    "timestamp": timestamp - (len(user_history) - idx),
                }
            )
        return {"session": session_rows, "is_cold_start": len(session_rows) == 0}
