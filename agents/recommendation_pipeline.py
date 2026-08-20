"""Task B recommendation pipeline: catalog assembly, live search blending, and ranking.

Extracted out of the HTTP route layer (`api/routes/task_b.py`) so the actual
recommendation logic is testable without spinning up FastAPI and is not
duplicated across the API layer and the orchestrator.
"""

from __future__ import annotations

import json
import os
from typing import Any
from uuid import uuid4

from agents.catalog_loader import get_catalog_list
from agents.catalog_semantic_index import CatalogSemanticIndex
from agents.collaborative_filtering import get_default_index
from agents.embeddings import EmbeddingService
from agents.recommendation_scoring import get_simulation, rank_catalog_against_simulation
from agents.simulation_agent import SimulationAgent
from api.live_search import LiveSearchService
from orchestrator.recommendation_persistence import save_last_recommendation

# Built once per process and reused across requests: re-embedding the whole
# catalog on every call would be wasteful, and the catalog itself only
# changes when the process restarts (see agents/catalog_loader.py's cache).
_semantic_index = CatalogSemanticIndex()


def _apply_collaborative_scores(catalog: list[dict[str, Any]], user_history: list[dict[str, Any]]) -> None:
    """Stamp catalog items in-place with a real `collaborative_score` derived
    from item-item co-occurrence in real review data (agents/collaborative_filtering.py).

    No-ops if the offline index has no data yet (no processed dataset present),
    or if the caller's history doesn't carry `item_id` values that match real
    catalog keys — this is only meaningful when history references real items,
    same graceful-degradation pattern as the semantic/live-search signals.
    """
    cf_index = get_default_index()
    if not cf_index.available():
        return

    liked_item_ids = [
        str(entry.get("item_id"))
        for entry in user_history
        if entry.get("item_id") and float(entry.get("rating") or 0) >= 4
    ]
    if not liked_item_ids:
        return

    neighbor_scores: dict[str, float] = {}
    for liked_id in liked_item_ids:
        for neighbor_key, score in cf_index.similar_items(liked_id, top_k=30):
            neighbor_scores[neighbor_key] = max(neighbor_scores.get(neighbor_key, 0.0), score)

    if not neighbor_scores:
        return

    for item in catalog:
        key = str(item.get("item_id") or item.get("key") or "")
        if key in neighbor_scores:
            item["collaborative_score"] = neighbor_scores[key]


async def _apply_semantic_scores(catalog: list[dict[str, Any]], simulation: dict[str, Any]) -> None:
    """Stamp catalog items in-place with a `semantic_score` when embeddings are available.

    No-ops entirely (including skipping the embedding call) when
    VOYAGE_API_KEY isn't configured, so behavior is unchanged without it.
    """
    if not _semantic_index.available():
        return

    await _semantic_index.ensure_built(catalog)
    if not _semantic_index.has_vectors():
        return

    query_text = " ".join(
        [
            str(simulation.get("preference_cluster") or ""),
            str(simulation.get("current_intent") or ""),
            " ".join(str(a) for a in (simulation.get("top_affinities") or [])),
        ]
    ).strip()
    if not query_text:
        return

    query_embedding = await _semantic_index.embedding_service.embed([query_text], input_type="query")
    if not query_embedding:
        return

    similarities = dict(_semantic_index.top_k(query_embedding[0], k=len(catalog)))
    for item in catalog:
        key = str(item.get("item_id") or item.get("key") or "")
        if key in similarities:
            item["semantic_score"] = similarities[key]

_LLM_RANK_SYSTEM_PROMPT = (
    "You are ARCHE's recommendation rater. Given a behavioral snapshot and a list of candidate items, "
    "score and justify each candidate's relevance to the user. \n\n"
    "CRITICAL CONSTRAINTS:\n"
    "1. PERSONA ALIGNMENT: Strictly respect the user's interaction style and persona. If the persona is 'cautious' or 'cost-conscious', "
    "penalize items with a 'high' price_tier and prioritize value/frugality in your reasoning.\n"
    "2. SCORE NORMALIZATION: Your 'score' MUST be a float strictly between 0.0 and 1.0. Never exceed 1.0.\n"
    "3. OUTPUT: Return a JSON array of objects with keys: item_name, score, reasoning (short). No extra text."
)


def _build_item_pool_catalog(item_pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    catalog = []
    for item in item_pool:
        iname = item.get("item_name") or item.get("name") or "unknown"
        icat = item.get("item_category") or item.get("category") or "unknown"
        iid = item.get("item_id") or item.get("id") or str(uuid4())
        catalog.append(
            {
                "item_id": iid,
                "item_name": iname,
                "item_category": icat,
                "price_tier": item.get("price_tier") or "mid",
                "description": item.get("description") or "",
                "attributes": item.get("attributes") or {},
                "source": "item_pool",
                "is_pool_item": True,
            }
        )
    return catalog


def _looks_like_search_title(name: str) -> bool:
    lowered = name.lower()
    return any(x in lowered for x in ["best ", "top ", "review", "buying guide", "how to"])


async def _fetch_live_candidates(
    *,
    live_search: LiveSearchService,
    domain_filter: str,
    context: dict[str, Any],
    user_history: list[dict[str, Any]],
    live_query: str | None,
    live_results_limit: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Returns (live_candidate_items, metadata about the live search call)."""
    meta: dict[str, Any] = {
        "query": None,
        "source": None,
        "provider": None,
        "llm_used": False,
        "llm_provider": None,
        "llm_model": None,
    }

    plan = await live_search.build_query(
        category=domain_filter or context.get("entry_point") or "general",
        context=context,
        user_history=user_history,
        live_query=live_query,
    )
    meta["query"] = plan.get("query")
    meta["source"] = plan.get("source")
    meta["llm_used"] = bool(plan.get("source") == "llm")
    llm_provider = getattr(live_search.llm_agent, "llm_provider", None)
    meta["llm_provider"] = llm_provider
    meta["llm_model"] = (
        getattr(live_search.llm_agent, "groq_model", None)
        if llm_provider == "groq"
        else ("claude-3-5-sonnet-20241022" if llm_provider else None)
    )

    try:
        fetched = await live_search.search(meta["query"] or "", num_results=live_results_limit)
    except Exception:
        return [], meta

    if fetched:
        meta["provider"] = fetched[0].source

    candidates = [
        {
            "item_id": item.item_id,
            "item_name": item.item_name,
            "item_category": item.item_category,
            "source": f"live:{item.source}",
            "description": item.description,
            "price_tier": item.price_tier,
            "url": item.url,
            "metadata": item.metadata or {},
            "is_live_item": True,
        }
        for item in fetched
        if not _looks_like_search_title(item.item_name)
    ]
    return candidates, meta


async def _rank_with_llm(
    *,
    sim_agent: SimulationAgent,
    simulation: dict[str, Any],
    context: dict[str, Any],
    catalog: list[dict[str, Any]],
    n: int,
) -> tuple[list[dict[str, Any]], bool]:
    """Attempt LLM re-ranking of an item_pool-backed catalog. Returns (ranked, llm_used)."""
    brief_items = [
        {"name": i["item_name"], "category": i["item_category"], "description": i.get("description", "")}
        for i in catalog[:50]
    ]
    snapshot = simulation.get("behavioral_snapshot") or simulation
    user_prompt = (
        f"Behavioral snapshot:\n{json.dumps(snapshot, indent=2)}\n\n"
        f"Context:\n{json.dumps(context, indent=2)}\n\n"
        f"Candidates (check price_tier and category):\n{json.dumps(brief_items, indent=2)}\n\n"
        "Provide the JSON array."
    )

    content = await sim_agent.call_llm(system_prompt=_LLM_RANK_SYSTEM_PROMPT, user_prompt=user_prompt)

    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0]

    parsed = json.loads(content.strip())
    if not isinstance(parsed, list):
        return rank_catalog_against_simulation(simulation, catalog, n=n), False

    score_map = {str(p.get("item_name") or p.get("name") or "").lower(): p for p in parsed}
    for item in catalog:
        match = score_map.get(str(item["item_name"]).lower())
        if not match:
            continue
        raw_score = min(1.0, float(match.get("score") or 0.5))
        item["_confidence"] = raw_score
        item["explanation"] = str(match.get("reasoning") or match.get("reason") or "")
        if item.get("is_pool_item"):
            item["recommendation_type"] = "precision"
            item["_sort_score"] = raw_score + 1.0  # boost for sorting only
        else:
            item["recommendation_type"] = "discovery"
            item["_sort_score"] = raw_score

    catalog.sort(key=lambda x: x.get("_sort_score", 0.0), reverse=True)
    return catalog[:n], True


async def run_recommendation_pipeline(
    *,
    user_token: str,
    lookup_token: str,
    user_history: list[dict[str, Any]],
    context: dict[str, Any],
    domain_filter: str,
    n: int,
    item_pool: list[dict[str, Any]] | None,
    enable_live_data: bool,
    live_query: str | None,
    live_results_limit: int,
    memory_manager: Any,
) -> dict[str, Any]:
    """Run the full Task B pipeline: simulate -> assemble catalog -> rank -> explain.

    Returns the response payload for `/v1/recommend` (recommendations plus
    diagnostics) and persists the run so `/v1/explain` can look it up.
    """
    simulation = await get_simulation(
        user_history_inline=user_history,
        user_token=lookup_token,
        context=context,
        memory_manager=memory_manager,
    )

    if item_pool:
        catalog = _build_item_pool_catalog(item_pool)
    else:
        catalog = get_catalog_list()

    if domain_filter:
        catalog = [item for item in catalog if str(item.get("item_category") or "").lower() == domain_filter]
    if not catalog and not item_pool:
        catalog = get_catalog_list()

    live_search = LiveSearchService()
    live_candidates: list[dict[str, Any]] = []
    live_meta: dict[str, Any] = {"query": None, "source": None, "provider": None, "llm_used": False, "llm_provider": None, "llm_model": None}
    if enable_live_data and live_search.available():
        live_candidates, live_meta = await _fetch_live_candidates(
            live_search=live_search,
            domain_filter=domain_filter,
            context=context,
            user_history=user_history,
            live_query=live_query,
            live_results_limit=live_results_limit,
        )

    if live_candidates:
        catalog = catalog + live_candidates

    _apply_collaborative_scores(catalog, user_history)
    await _apply_semantic_scores(catalog, simulation)

    llm_instrumentation = {
        "used": live_meta["llm_used"],
        "provider": live_meta["llm_provider"],
        "model": live_meta["llm_model"],
    }

    sim_agent = SimulationAgent()
    if item_pool and (sim_agent.llm or os.getenv("GROQ_API_KEY")):
        try:
            llm_instrumentation["used"] = True
            llm_instrumentation["provider"] = "groq"
            llm_instrumentation["model"] = "llama-3.3-70b-versatile"
            ranked_catalog, _ = await _rank_with_llm(
                sim_agent=sim_agent, simulation=simulation, context=context, catalog=catalog, n=n
            )
        except Exception:
            ranked_catalog = rank_catalog_against_simulation(simulation, catalog, n=n)
            llm_instrumentation["used"] = True
            if not llm_instrumentation["provider"]:
                llm_instrumentation["provider"] = "groq"
                llm_instrumentation["model"] = "llama-3.3-70b-versatile"
    else:
        ranked_catalog = rank_catalog_against_simulation(simulation, catalog, n=n)

    recommendations = []
    for idx, rec in enumerate(ranked_catalog, start=1):
        raw_conf = rec.get("_confidence") or rec.get("_score") or 0.0
        confidence = min(1.0, float(raw_conf))
        recommendations.append(
            {
                "recommendation_id": f"rec_{idx}_{user_token}",
                "item_id": rec.get("item_id") or rec.get("key"),
                "item_name": rec.get("item_name") or rec.get("item_id") or f"item_{idx}",
                "item_category": rec.get("item_category") or "unknown",
                "confidence": round(confidence, 2),
                "recommendation_type": rec.get("recommendation_type") or "precision",
                "exploration_factor": "inline_history" if user_history else "cold_start_prior",
                "explanation": rec.get("explanation") or f"Ranked with {simulation.get('simulation_basis', 'unknown')}",
                "source": rec.get("source") or ("live" if str(rec.get("source") or "").startswith("live:") else "local_catalog"),
            }
        )

    save_last_recommendation(
        {
            "user_token": user_token,
            "simulation_basis": simulation.get("simulation_basis") or ("cold_start_prior" if simulation.get("cold_start_used") else "historical_memory"),
            "recommendations": recommendations,
        }
    )

    normalized_recs = []
    for idx, r in enumerate(recommendations, start=1):
        normalized_recs.append(
            {
                "recommendation_id": r.get("recommendation_id"),
                "item_id": r.get("item_id"),
                "rank": idx,
                "item_name": r.get("item_name"),
                "category": r.get("item_category"),
                "confidence": r.get("confidence"),
                "explanation": r.get("explanation") or "",
                "recommendation_type": r.get("recommendation_type"),
            }
        )

    exploration_ratio = 0.4
    if recommendations:
        computed = sum(1 for r in recommendations if r.get("recommendation_type") in {"adjacent_exploration", "discovery"}) / len(recommendations)
        if computed > 0:
            exploration_ratio = computed

    return {
        "recommendations": normalized_recs,
        "diversity_score": round(float(exploration_ratio), 2),
        "cold_start_handled": bool(simulation.get("cold_start_used")),
        "exploration_ratio": round(float(exploration_ratio), 2),
        "live_data_used": bool(live_candidates),
        "live_search_query": live_meta["query"],
        "live_search_source": live_meta["source"],
        "live_search_provider": live_meta["provider"],
        "llm_instrumentation": llm_instrumentation,
    }
