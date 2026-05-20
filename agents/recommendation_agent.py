from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .base_agent import BaseAgent, AgentState
from .retrieval_agent import RetrievalAgent


class RecommendationAgent(BaseAgent):
    """Ranks recommendations using simulation state plus real catalog candidates."""

    name = "recommendation"

    async def run(self, state: AgentState) -> AgentState:
        return state

    @staticmethod
    def rank_candidates(candidates: list[dict[str, Any]], simulation: Any, context: Any) -> list[dict[str, Any]]:
        """Rank candidate items using the behavioral simulation state.
        
        Applies a 60/25/15 exploration split:
        - 60% precision recommendations (high affinity)
        - 25% adjacent exploration (edge of preference space)
        - 15% discovery injection (deliberate novelty)
        """
        if not candidates or not hasattr(simulation, 'behavioral_snapshot'):
            return []
        
        snapshot = simulation.behavioral_snapshot or {}
        
        # Score candidates
        scored = []
        for entry in candidates:
            score = RecommendationAgent._candidate_score(
                entry, "precision", simulation, context
            )
            scored.append({
                **entry,
                "affinity_score": score,
                "recommendation_type": "precision"
            })
        
        # Sort by affinity
        scored.sort(key=lambda x: x["affinity_score"], reverse=True)
        
        # Apply 60/25/15 split
        n = len(scored)
        n_precision = max(1, int(n * 0.60))
        n_adjacent = max(0, int(n * 0.25))
        n_discovery = max(0, n - n_precision - n_adjacent)
        
        precision_set = scored[:n_precision]
        adjacent_set = scored[n_precision:n_precision + n_adjacent]
        discovery_set = scored[n_precision + n_adjacent:n_precision + n_adjacent + n_discovery]
        
        # Mark types
        for rec in precision_set:
            rec["recommendation_type"] = "precision"
        for rec in adjacent_set:
            rec["recommendation_type"] = "adjacent_exploration"
        for rec in discovery_set:
            rec["recommendation_type"] = "discovery"
        
        # Combine
        ranked = precision_set + adjacent_set + discovery_set
        
        # Add IDs
        for i, rec in enumerate(ranked):
            if "recommendation_id" not in rec:
                rec["recommendation_id"] = str(uuid4())
            rec["rank"] = i + 1
        
        return ranked

    @staticmethod
    def calculate_exploration_ratio(recommendations: list[dict[str, Any]]) -> float:
        """Calculate the diversity/exploration ratio in the recommendation set."""
        if not recommendations:
            return 0.0
        
        exploration_count = len([r for r in recommendations if r.get("recommendation_type") in ["adjacent_exploration", "discovery"]])
        return exploration_count / len(recommendations)

    @staticmethod
    def _snapshot_data(simulation: Any) -> dict[str, Any]:
        snapshot = getattr(simulation, "behavioral_snapshot", {})
        if hasattr(snapshot, "model_dump"):
            return snapshot.model_dump()
        if isinstance(snapshot, dict):
            return snapshot
        return {}

    @staticmethod
    def _candidate_score(entry: dict[str, Any], priority: str, simulation, context: Any) -> float:
        """Score a candidate item based on behavioral alignment and context."""
        category = (entry.get("item_category") or "unknown").lower()
        item_name = (entry.get("item_name") or "").lower()
        snapshot = RecommendationAgent._snapshot_data(simulation)
        affinity_set = {aff.lower() for aff in (snapshot.get("top_affinities") or ["general_interest"]) }

        context_entry_point = getattr(context, "entry_point", None)
        context_device_class = getattr(context, "device_class", None)
        if context_entry_point is None and isinstance(context, dict):
            context_entry_point = context.get("entry_point")
        if context_device_class is None and isinstance(context, dict):
            context_device_class = context.get("device_class")

        score = 0.0
        if priority == "precision":
            if category in affinity_set:
                score += 3.0
            if snapshot.get("current_intent") == "active_purchase":
                score += 0.4
        elif priority == "adjacent_exploration":
            if category.startswith("adjacent_to_"):
                score += 2.0
            score += 0.2 * float(snapshot.get("exploration_readiness", 0.5))
        else:
            if category == "discovery":
                score += 2.5
            elif category not in affinity_set:
                score += 1.0
            score += 0.2 * simulation.cold_start_confidence

        if context_entry_point == "search" and priority == "precision":
            score += 0.15
        if context_device_class == "mobile" and category in {"fashion", "food", "social"}:
            score += 0.1
        if category and category in item_name:
            score += 0.05
        return score

    @staticmethod
    def _build_recommendation(
        *,
        recommendation_type: str,
        simulation,
        context: Any,
        item_name: str,
        item_category: str,
        confidence: float,
        explanation: str,
        exploration_factor: str,
        rank: int,
    ):
        from api.main import Recommendation

        return Recommendation(
            recommendation_id=str(uuid4()),
            item_name=item_name,
            item_category=item_category,
            confidence=round(confidence, 2),
            recommendation_type=recommendation_type,
            exploration_factor=exploration_factor,
            explanation=explanation,
        )

    @classmethod
    def rank_candidates(
        cls,
        *,
        user_token: str,
        simulation,
        context: Any,
        n: int,
        memory_vector_store,
        dataset_loader=None,
    ):
        from api.main import RecommendationSet

        n = max(1, n)
        precision_share = 0.68 if simulation.simulation_basis.startswith("historical_memory:") else 0.58
        if simulation.behavioral_snapshot.current_intent == "active_purchase":
            precision_share += 0.05
        if simulation.behavioral_snapshot.exploration_readiness < 0.5:
            precision_share += 0.05
        precision_share = min(0.82, precision_share)

        adjacent_share = 0.22
        if simulation.behavioral_snapshot.exploration_readiness >= 0.7:
            adjacent_share += 0.04
        adjacent_share = min(0.3, adjacent_share)

        n_precision = max(1, int(round(n * precision_share)))
        n_adjacent = max(0, int(round(n * adjacent_share)))
        if n_precision + n_adjacent > n:
            n_adjacent = max(0, n - n_precision)
        n_discovery = max(0, n - n_precision - n_adjacent)
        if n > 4 and n_discovery > 1 and simulation.behavioral_snapshot.exploration_readiness < 0.6:
            n_discovery = 1
            n_adjacent = max(0, n - n_precision - n_discovery)

        affinities = simulation.behavioral_snapshot.top_affinities or ["general_interest"]
        affinity_set = {aff.lower() for aff in affinities}
        query_vector = RetrievalAgent.build_query_vector(affinities, context=dict(context.model_dump()) if hasattr(context, "model_dump") else dict(context or {}))

        if dataset_loader is not None:
            candidate_pool = dataset_loader.load_catalog(limit_per_source=200)
        else:
            candidate_pool = []

        if not candidate_pool:
            try:
                candidate_pool = [
                    {"key": key, "item_name": meta.get("item_name") or key.split(":", 1)[-1], "item_category": meta.get("item_category") or "unknown"}
                    for key, meta in memory_vector_store.query(query_vector, top_k=50)
                ]
            except Exception:
                candidate_pool = []

        seen_keys: set[str] = set()
        precision_items: list[dict[str, Any]] = []
        adjacent_items: list[dict[str, Any]] = []
        other_items: list[dict[str, Any]] = []

        for entry in candidate_pool:
            key = str(entry.get("key") or entry.get("item_id") or entry.get("item_name") or uuid4())
            if key in seen_keys:
                continue
            seen_keys.add(key)
            category = str(entry.get("item_category") or "unknown")
            if category.lower() in affinity_set:
                precision_items.append(entry)
            elif category.lower().startswith("adjacent_to_"):
                adjacent_items.append(entry)
            else:
                other_items.append(entry)

        precision_items.sort(key=lambda entry: (-cls._candidate_score(entry, "precision", simulation, context), str(entry.get("item_name") or "")))
        adjacent_items.sort(key=lambda entry: (-cls._candidate_score(entry, "adjacent_exploration", simulation, context), str(entry.get("item_name") or "")))
        other_items.sort(key=lambda entry: (-cls._candidate_score(entry, "discovery", simulation, context), str(entry.get("item_name") or "")))

        recommendations: list[Any] = []
        for i in range(n_precision):
            if i < len(precision_items):
                entry = precision_items[i]
            else:
                entry = {"item_name": affinities[i % len(affinities)], "item_category": affinities[i % len(affinities)]}
            item_name = str(entry.get("item_name") or f"{affinities[i % len(affinities)]}_recommendation_{i+1}")
            item_category = str(entry.get("item_category") or affinities[i % len(affinities)])
            recommendations.append(
                cls._build_recommendation(
                    recommendation_type="precision",
                    simulation=simulation,
                    context=context,
                    item_name=item_name,
                    item_category=item_category,
                    confidence=0.88 - (i * 0.015),
                    explanation=(
                        f"Matched to simulated preference cluster '{simulation.behavioral_snapshot.preference_cluster}' "
                        f"with affinity '{item_category}'. Context '{simulation.context_modifiers.active_context}' and basis {simulation.simulation_basis}."
                    ),
                    exploration_factor="Precision recommendation — within core preference cluster",
                    rank=i + 1,
                )
            )

        for i in range(n_adjacent):
            if i < len(adjacent_items):
                entry = adjacent_items[i]
            elif i < len(other_items):
                entry = other_items[i]
            else:
                entry = {"item_name": f"adjacent_to_{affinities[i % len(affinities)]}", "item_category": f"adjacent_to_{affinities[i % len(affinities)]}"}

            item_name = str(entry.get("item_name") or f"adjacent_to_{affinities[i % len(affinities)]}_recommendation_{i+1}")
            item_category = str(entry.get("item_category") or f"adjacent_to_{affinities[i % len(affinities)]}")
            recommendations.append(
                cls._build_recommendation(
                    recommendation_type="adjacent_exploration",
                    simulation=simulation,
                    context=context,
                    item_name=item_name,
                    item_category=item_category,
                    confidence=0.68 - (i * 0.012),
                    explanation=(
                        f"Exploration injection near user's affinities to broaden discovery. Simulation basis: {simulation.simulation_basis} and context {simulation.context_modifiers.active_context}."
                    ),
                    exploration_factor="Adjacent exploration — similar but broader items",
                    rank=n_precision + i + 1,
                )
            )

        for i in range(n_discovery):
            if i < len(other_items):
                entry = other_items[i]
                item_name = str(entry.get("item_name") or f"novel_discovery_{i+1}")
                item_category = str(entry.get("item_category") or "discovery")
            else:
                item_name = f"novel_discovery_{i+1}"
                item_category = "discovery"
            recommendations.append(
                cls._build_recommendation(
                    recommendation_type="discovery",
                    simulation=simulation,
                    context=context,
                    item_name=item_name,
                    item_category=item_category,
                    confidence=0.4 - (i * 0.01),
                    explanation=(
                        f"Deliberate discovery pick to maintain diversity. Simulation confidence: {simulation.cold_start_confidence} and context {simulation.context_modifiers.active_context}."
                    ),
                    exploration_factor="Discovery injection — novel item for serendipity",
                    rank=n_precision + n_adjacent + i + 1,
                )
            )

        return RecommendationSet(
            user_token=user_token,
            simulation_basis=simulation.simulation_basis,
            recommendations=recommendations,
        )
