from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from .base_agent import BaseAgent, AgentState
from .retrieval_agent import RetrievalAgent


class RecommendationAgent(BaseAgent):
    """Ranks recommendations using simulation state plus real catalog candidates.

    For higher fidelity the agent will attempt an LLM re-scoring/re-ranking step
    (no token limits) when an LLM provider is configured. If LLM calls fail,
    the deterministic scoring pipeline is used as a fallback.
    """

    name = "recommendation"

    async def run(self, state: AgentState) -> AgentState:
        return state

    @staticmethod
    async def rank_candidates(candidates: list[dict[str, Any]], simulation: Any, context: Any) -> list[dict[str, Any]]:
        """Rank candidate items using the behavioral simulation state.

        Strategy:
        1. Heuristic scoring to form a candidate pool.
        2. If an LLM is available, call the LLM to score/top-rank the pool and provide
           short reasoning for each item. No token limits are applied.
        3. Map LLM scores back to confidences and explanations.
        """
        if not candidates or not hasattr(simulation, 'behavioral_snapshot'):
            return []

        snapshot = simulation.behavioral_snapshot or {}

        # Heuristic pre-score to build candidate pool
        scored = []
        for entry in candidates:
            score = RecommendationAgent._candidate_score(entry, "precision", simulation, context)
            scored.append({**entry, "affinity_score": score, "recommendation_type": "precision"})

        scored.sort(key=lambda x: x["affinity_score"], reverse=True)

        # Keep a manageable pool for LLM re-ranking
        pool = scored[:50] if len(scored) > 50 else scored

        # Default: convert pool into a simple recommendation list (fallback path)
        def assemble_from_pool(pool_list: list[dict[str, Any]]):
            ranked = []
            for i, rec in enumerate(pool_list):
                if "recommendation_id" not in rec:
                    rec["recommendation_id"] = str(uuid4())
                rec_out = {
                    "recommendation_id": rec["recommendation_id"],
                    "item_id": rec.get("key") or rec.get("item_id"),
                    "item_name": rec.get("item_name") or rec.get("item_id") or str(i),
                    "item_category": rec.get("item_category") or "unknown",
                    "confidence": round(0.85 * float(rec.get("affinity_score", 0.0)), 2),
                    "recommendation_type": rec.get("recommendation_type", "precision"),
                    "exploration_factor": "heuristic",
                    "explanation": f"Heuristic score {rec.get('affinity_score'):.3f}",
                    "rank": i + 1,
                }
                ranked.append(rec_out)
            return ranked

        # Attempt LLM re-ranking
        try:
            from agents.simulation_agent import SimulationAgent

            sim_agent = SimulationAgent()
            if sim_agent.llm is not None:
                # Build compact prompt describing snapshot and candidate pool
                brief_items = [
                    {"name": str(e.get("item_name") or e.get("item_id") or ""), "category": str(e.get("item_category") or "unknown")}
                    for e in pool
                ]
                system_prompt = (
                    "You are ARCHE's recommendation rater. Given a behavioral snapshot and a list of candidate items, "
                    "score and justify each candidate's relevance to the user. Return a JSON array of objects with keys: "
                    "item_name, score (0.0-1.0), reasoning (short). Do NOT include extra commentary." 
                )
                user_prompt = f"Behavioral snapshot:\n{snapshot}\n\nCandidates:\n{json.dumps(brief_items, ensure_ascii=False)}\n\nProvide the JSON array."

                content = await sim_agent.call_llm(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.15)

                # Parse LLM output
                parsed = None
                if isinstance(content, str):
                    if "```json" in content:
                        content = content.split("```json", 1)[1].split("```", 1)[0]
                    elif "```" in content:
                        content = content.split("```", 1)[1].split("```", 1)[0]
                    try:
                        parsed = json.loads(content)
                    except Exception:
                        parsed = None

                if parsed and isinstance(parsed, list):
                    # Map scores back to pool entries
                    scored_map = { (e.get("item_name") or ""): e for e in pool }
                    ranked = []
                    max_items = min(len(pool), len(parsed))
                    for idx in range(max_items):
                        p = parsed[idx]
                        name = p.get("item_name") or p.get("name") or ""
                        score = float(p.get("score") or 0.0)
                        reason = p.get("reasoning") or p.get("reason") or ""
                        source_entry = scored_map.get(name)
                        item_id = source_entry.get("key") if source_entry else None
                        item_category = source_entry.get("item_category") if source_entry else "unknown"
                        rec_obj = {
                            "recommendation_id": str(uuid4()),
                            "item_id": item_id,
                            "item_name": name,
                            "item_category": item_category,
                            "confidence": round(min(1.0, max(0.0, score)), 2),
                            "recommendation_type": source_entry.get("recommendation_type") if source_entry else "precision",
                            "exploration_factor": "llm_re_rank",
                            "explanation": reason,
                            "rank": idx + 1,
                        }
                        ranked.append(rec_obj)

                    # Ensure we have exactly n requested positions; append heuristics if short
                    return ranked

        except Exception:
            # LLM re-ranking failed; fall back to heuristics
            pass

        # Fallback deterministic assembly
        fallback = assemble_from_pool(pool)
        # If user requested more than the pool, pad with simple discoveries
        return fallback

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
        """Score a candidate item primarily against simulation signals."""
        category = str(entry.get("item_category") or "unknown").lower()
        price_tier = str(entry.get("price_tier") or "mid").lower()
        snapshot = RecommendationAgent._snapshot_data(simulation)
        affinity_set = {str(aff).lower() for aff in (snapshot.get("top_affinities") or ["general_interest"]) }
        rejection_set = {str(sig).lower() for sig in (snapshot.get("rejection_signals") or [])}
        preferred_price_tier = str(snapshot.get("preferred_price_tier") or "").lower()

        # Simulation context modifiers are modeled on the simulation response contract.
        modifiers = getattr(simulation, "context_modifiers", None)
        time_boosts = getattr(modifiers, "time_boosts", []) if modifiers is not None else []
        boosted_categories = {
            str(boost).split(":", 1)[-1].lower()
            for boost in (time_boosts or [])
            if isinstance(boost, str)
        }

        exploration_readiness = float(snapshot.get("exploration_readiness") or 0.0)
        score = 0.0

        # Signal 1: affinity alignment.
        if category in affinity_set:
            score += 0.40

        # Signal 2: avoid known rejection patterns.
        if category not in rejection_set:
            score += 0.15

        # Signal 3: price alignment when available.
        if preferred_price_tier and price_tier == preferred_price_tier:
            score += 0.20

        # Signal 4: context boost.
        if category in boosted_categories:
            score += 0.15

        # Signal 5: exploration allowance.
        if category not in affinity_set and exploration_readiness > 0.6:
            score += 0.10

        # Keep phase-specific behavior as a light tie-breaker only.
        if priority == "precision" and category in affinity_set:
            score += 0.05
        elif priority == "adjacent_exploration" and category not in rejection_set:
            score += 0.03
        elif priority == "discovery" and category not in affinity_set:
            score += 0.02

        return score

    @staticmethod
    def _build_recommendation(
        *,
        recommendation_type: str,
        simulation,
        context: Any,
        item_id: str | None = None,
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
            item_id=item_id,
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
        from .recommendation_scoring import rank_catalog_against_simulation

        n = max(1, int(n))
        affinities = simulation.behavioral_snapshot.top_affinities or ["general_interest"]
        query_vector = RetrievalAgent.build_query_vector(
            affinities,
            context=dict(context.model_dump()) if hasattr(context, "model_dump") else dict(context or {}),
        )

        context_entry_point = getattr(context, "entry_point", None)
        if context_entry_point is None and isinstance(context, dict):
            context_entry_point = context.get("entry_point")
        should_use_real_catalog = str(context_entry_point or "").lower() in {"amazon", "goodreads", "yelp"}

        candidate_pool: list[dict[str, Any]] = []
        if should_use_real_catalog and dataset_loader is not None:
            candidate_pool = [
                entry
                for entry in dataset_loader.load_catalog(limit_per_source=30000)
                if str(entry.get("source") or "").lower() == str(context_entry_point or "").lower()
            ]
        if not candidate_pool:
            try:
                candidate_pool = [
                    {
                        "key": key,
                        "item_name": meta.get("item_name") or key.split(":", 1)[-1],
                        "item_category": meta.get("item_category") or "unknown",
                        "source": meta.get("source") or key.split(":", 1)[0],
                        "price_tier": meta.get("price_tier") or "mid",
                    }
                    for key, meta in memory_vector_store.query(query_vector, top_k=1000)
                ]
            except Exception:
                candidate_pool = []

        snapshot = cls._snapshot_data(simulation)
        modifiers = getattr(simulation, "context_modifiers", None)
        simulation_payload = {
            "behavioral_snapshot": snapshot,
            "context_modifiers": modifiers.model_dump() if hasattr(modifiers, "model_dump") else (modifiers if isinstance(modifiers, dict) else {}),
            "simulation_basis": getattr(simulation, "simulation_basis", "unknown"),
            "cold_start_confidence": getattr(simulation, "cold_start_confidence", 0.0),
            "recent_categories": snapshot.get("top_affinities", []),
        }

        ranked_candidates = rank_catalog_against_simulation(simulation_payload, candidate_pool, n=n)

        recommendations: list[Any] = []
        for idx, entry in enumerate(ranked_candidates, start=1):
            recommendation_type = str(entry.get("recommendation_type") or "precision")
            item_name = str(entry.get("item_name") or entry.get("item_id") or f"item_{idx}")
            item_category = str(entry.get("item_category") or "unknown")
            item_id = str(entry.get("key") or entry.get("item_id")) if entry.get("key") or entry.get("item_id") else None
            score = float(entry.get("_score") or 0.0)

            if recommendation_type == "precision":
                explanation = (
                    f"Matched to simulated preference cluster '{simulation.behavioral_snapshot.preference_cluster}' "
                    f"with affinity '{item_category}'. Context '{simulation.context_modifiers.active_context}' and basis {simulation.simulation_basis}."
                )
                exploration_factor = "Precision recommendation — within core preference cluster"
                confidence = min(0.95, 0.72 + score)
            elif recommendation_type == "adjacent_exploration":
                explanation = (
                    f"Exploration injection near user's affinities to broaden discovery. Simulation basis: {simulation.simulation_basis} and context {simulation.context_modifiers.active_context}."
                )
                exploration_factor = "Adjacent exploration — similar but broader items"
                confidence = min(0.90, 0.58 + score)
            else:
                explanation = (
                    f"Deliberate discovery pick to maintain diversity. Simulation confidence: {simulation.cold_start_confidence} and context {simulation.context_modifiers.active_context}."
                )
                exploration_factor = "Discovery injection — novel item for serendipity"
                confidence = min(0.75, 0.35 + score)

            recommendations.append(
                cls._build_recommendation(
                    recommendation_type=recommendation_type,
                    simulation=simulation,
                    context=context,
                    item_id=item_id,
                    item_name=item_name,
                    item_category=item_category,
                    confidence=confidence,
                    explanation=explanation,
                    exploration_factor=exploration_factor,
                    rank=idx,
                )
            )

        return RecommendationSet(
            user_token=user_token,
            simulation_basis=simulation.simulation_basis,
            recommendations=recommendations,
        )
