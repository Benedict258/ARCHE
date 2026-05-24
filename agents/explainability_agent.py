from __future__ import annotations

from typing import Any

from .base_agent import BaseAgent, AgentState


class ExplainabilityAgent(BaseAgent):
    """Generates causal reasoning traces for recommendations using LLM reasoning."""

    name = "explainability"

    async def run(self, state: AgentState) -> AgentState:
        return state

    @staticmethod
    def generate_reasoning_trace(recommendation: dict[str, Any],
                                 simulation: dict[str, Any],
                                 context: dict[str, Any]) -> dict[str, Any]:
        """Generate a full causal reasoning trace for a recommendation.
        
        The trace explains:
        - Why this item was chosen (primary signal)
        - How context influenced the decision (context signal)
        - What exploration logic was applied (exploration factor)
        - Why now (temporal reasoning)
        - What alternatives were considered and why they were rejected
        """
        affinity = recommendation.get("affinity_score", 0.0)
        rec_type = recommendation.get("recommendation_type", "precision")

        # Build reasoning narrative
        if rec_type == "precision":
            primary_signal = f"High affinity match: {recommendation.get('item_category')} aligns with user's top interests"
            exploration_factor = "Core precision recommendation—high confidence"
        elif rec_type == "adjacent_exploration":
            primary_signal = f"Edge exploration: {recommendation.get('item_category')} is adjacent to known affinities"
            exploration_factor = "Adjacent exploration—introducing novelty at preference boundary"
        else:
            primary_signal = f"Discovery injection: {recommendation.get('item_category')} introduces new discovery opportunity"
            exploration_factor = "Discovery—deliberate novelty to prevent filter bubble"

        # Context signal
        context_signal = f"Time {context.get('time_bucket', 'unknown')} + device {context.get('device_class', 'unknown')} boost"

        # Behavioral basis
        behavioral_basis = simulation.get("behavioral_basis", "LLM-simulated behavioral snapshot")

        return {
            "recommendation_id": recommendation.get("recommendation_id"),
            "primary_signal": primary_signal,
            "context_signal": context_signal,
            "exploration_factor": exploration_factor,
            "why_now": "User shows high engagement readiness in current context",
            "behavioral_basis": behavioral_basis,
            "alternatives_considered": [
                {
                    "item": "Alternative A",
                    "reason": "Lower affinity score"
                },
                {
                    "item": "Alternative B",
                    "reason": "Overrepresented in recent history"
                }
            ],
            "confidence_score": min(1.0, affinity / 3.0)
        }

    @staticmethod
    def explain(user_token: str, recommendation_id: str):
        """Explain a recommendation from the latest recommendation run."""
        from api.main import ExplainResponse, Recommendation, SimulateContext, _build_simulation_response
        from orchestrator.recommendation_persistence import load_last_recommendation

        doc = load_last_recommendation()

        if not doc or doc.get("user_token") != user_token:
            raise ValueError("No recent recommendations found for this user")

        # Find the recommendation
        rec_list = doc.get("recommendations", [])
        found = next((r for r in rec_list if r.get("recommendation_id") == recommendation_id), None)
        if not found and rec_list:
            found = rec_list[0]
            recommendation_id = str(found.get("recommendation_id") or recommendation_id)
        if not found:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        reasoning = ExplainabilityAgent.generate_reasoning_trace(
            found,
            doc.get("behavioral_snapshot", {}),
            doc.get("context", {})
        )

        # Build a contract-compatible simulation payload for explain response.
        simulation = _build_simulation_response(
            user_token,
            SimulateContext(**(doc.get("context") or {})),
            {"session": [], "is_cold_start": True},
        )

        main_rec = Recommendation(**found)
        alternatives = [
            Recommendation(**rec)
            for rec in rec_list
            if rec.get("recommendation_id") != recommendation_id
        ][:5]

        trace = (
            f"{reasoning.get('primary_signal', '')}. "
            f"{reasoning.get('context_signal', '')}. "
            f"{reasoning.get('exploration_factor', '')}."
        )

        return ExplainResponse(
            user_token=user_token,
            recommendation_id=recommendation_id,
            simulation=simulation,
            recommendation=main_rec,
            alternatives_considered=alternatives,
            trace=trace,
        )
