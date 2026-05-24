from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from api.live_search import LiveSearchService
from agents.recommendation_scoring import build_simulation_from_history, get_simulation, rank_catalog_against_simulation
from agents.catalog_loader import get_catalog_list
from api.request_repair import repair_payload_from_text
from orchestrator.recommendation_persistence import save_last_recommendation

router = APIRouter()


class SimulateContext(BaseModel):
    """Context applied to Task B recommendations."""

    time_bucket: str | None = None
    day_type: str | None = None
    device_class: str | None = None
    network_quality: str | None = None
    region_tier: str | None = None
    session_depth: int | None = None
    entry_point: str | None = None


class UserPersona(BaseModel):
    """User persona with inline review history for Task B."""

    user_id: str
    review_history: list[dict[str, Any]] = Field(default_factory=list)


class RecommendRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_persona": {
                        "user_id": "ada_test_001",
                        "review_history": [],
                    },
                    "context": {"time_bucket": "evening", "entry_point": "yelp"},
                    "n": 10,
                    "domain_filter": "food",
                    "output_format": "json",
                }
            ]
        }
    )

    user_token: str | None = Field(default=None, description="Optional user token if not using user_persona.")
    user_persona: UserPersona | None = Field(
        default=None,
        description="Preferred judge-friendly nesting for user identity and review history.",
    )
    context: SimulateContext = Field(
        default_factory=SimulateContext,
        description="Context such as time_bucket, device_class, or entry_point.",
    )
    n: int = Field(default=10, description="Number of recommendations to return.")
    domain_filter: str | None = Field(default=None, description="Optional domain filter like food, books, or shopping.")
    enable_live_data: bool = Field(
        default=False,
        description="When true, the app will fetch live candidates from the web via Serper and blend them with the local catalog.",
    )
    live_query: str | None = Field(
        default=None,
        description="Optional explicit live search query. If omitted, the LLM will craft one from the persona and context.",
    )
    live_results_limit: int = Field(
        default=5,
        ge=1,
        le=10,
        description="How many live web results to fetch before blending with the local catalog.",
    )
    raw_input: str | None = Field(
        default=None,
        description="Paste free text or malformed JSON here; the server will repair it into valid JSON.",
    )
    output_format: str = Field(
        default="json",
        description="Choose json for API testing or text for a human-readable response.",
    )


class Recommendation(BaseModel):
    recommendation_id: str
    item_id: str | None = None
    item_name: str
    item_category: str
    confidence: float
    recommendation_type: str
    exploration_factor: str
    explanation: str


class RecommendationSet(BaseModel):
    user_token: str
    simulation_basis: str
    recommendations: list[Recommendation]


class ContextModifiers(BaseModel):
    time_boosts: list[str]
    suppressed_categories: list[str]
    active_context: str


class BehavioralSnapshot(BaseModel):
    current_intent: str
    preference_cluster: str
    top_affinities: list[str]
    rejection_signals: list[str]
    engagement_mode: str
    exploration_readiness: float
    purchase_probability: float


class SimulationResponse(BaseModel):
    user_token: str
    simulated_at: str
    behavioral_snapshot: BehavioralSnapshot
    context_modifiers: ContextModifiers
    cold_start_confidence: float
    simulation_basis: str
    memory_sources: list[str]


class ExplainRequest(BaseModel):
    user_token: str = Field(min_length=1)
    recommendation_id: str = Field(min_length=1)


class ExplainResponse(BaseModel):
    user_token: str
    recommendation_id: str
    simulation: Any
    recommendation: Recommendation
    alternatives_considered: list[Recommendation]
    trace: str


@router.post("/v1/recommend")
async def recommend(payload: RecommendRequest, request: Request):
    """Task B: return personalized recommendations.

    Swagger tips:
    - Use `user_persona.review_history` for normal testing.
    - Use `raw_input` if you want the server to repair free text or malformed JSON.
    - Set `output_format` to `text` for a human-readable response.
    - Leave `domain_filter` blank unless you want to force a category.
    """
    from api.main import _ensure_app_state

    _ensure_app_state()
    privacy = request.app.state.privacy
    live_search = LiveSearchService()

    if payload.raw_input and not payload.user_persona and not payload.user_token:
        repaired = await repair_payload_from_text(
            payload.raw_input,
            schema_name="Task B /v1/recommend",
            schema_description="Expected keys: user_token or user_persona, context, n, domain_filter, output_format.",
            example_payload={
                "user_persona": {"user_id": "ada_test_001", "review_history": []},
                "context": {"time_bucket": "evening", "entry_point": "yelp"},
                "n": 10,
                "domain_filter": "food",
                "output_format": "json",
            },
        )
        try:
            payload = RecommendRequest.model_validate(repaired)
        except Exception:
            payload = RecommendRequest.model_validate({**repaired, "output_format": payload.output_format})

    persona = payload.user_persona
    user_token = (persona.user_id if persona else payload.user_token) or "anonymous"
    user_history = persona.review_history if persona else []
    context = payload.context.model_dump() if hasattr(payload.context, "model_dump") else dict(payload.context or {})
    domain_filter = (payload.domain_filter or context.get("entry_point") or context.get("domain") or "").strip().lower()
    n = payload.n
    lookup_token = privacy.anonymize_token(user_token, "user") or user_token

    memory_manager = request.app.state.memory_manager
    simulation = get_simulation(
        user_history_inline=user_history,
        user_token=lookup_token,
        context=context,
        memory_manager=memory_manager,
    )

    # Use full catalog from processed yelp data for recommendations.
    catalog = get_catalog_list()
    if domain_filter:
        catalog = [item for item in catalog if str(item.get("item_category") or "").lower() == domain_filter]
    if not catalog:
        catalog = get_catalog_list()

    live_candidates: list[dict[str, Any]] = []
    live_search_query = None
    live_search_source = None
    if payload.enable_live_data and live_search.available():
        plan = await live_search.build_query(
            category=domain_filter or context.get("entry_point") or "general",
            context=context,
            user_history=user_history,
            live_query=payload.live_query,
        )
        live_search_query = plan.get("query")
        live_search_source = plan.get("source")
        try:
            fetched = await live_search.search(live_search_query or "", num_results=payload.live_results_limit)
            live_candidates = [
                {
                    "item_id": item.item_id,
                    "item_name": item.item_name,
                    "item_category": item.item_category,
                    "source": f"live:{item.source}",
                    "collaborative_score": 1.0,
                    "description": item.description,
                    "price_tier": item.price_tier,
                    "url": item.url,
                    "metadata": item.metadata or {},
                }
                for item in fetched
            ]
        except Exception:
            live_candidates = []

    if live_candidates:
        catalog = live_search.merge_with_local_catalog(live_candidates, catalog, limit=max(payload.n, payload.live_results_limit, 10))


    ranked_catalog = rank_catalog_against_simulation(simulation, catalog, n=n)

    recommendations = []
    for idx, rec in enumerate(ranked_catalog, start=1):
        recommendations.append(
            {
                "recommendation_id": f"rec_{idx}_{user_token}",
                "item_id": rec.get("item_id") or rec.get("key"),
                "item_name": rec.get("item_name") or rec.get("item_id") or f"item_{idx}",
                "item_category": rec.get("item_category") or "unknown",
                "confidence": round(float(rec.get("_score") or 0.0), 2),
                "recommendation_type": rec.get("recommendation_type") or "precision",
                "exploration_factor": "inline_history" if user_history else "cold_start_prior",
                "explanation": rec.get("explanation") or f"Ranked with {simulation.get('simulation_basis', 'unknown')}",
                "source": rec.get("source") or ("live" if str(rec.get("source") or "").startswith("live:") else "local_catalog"),
            }
        )

    recs = {
        "user_token": user_token,
        "simulation_basis": simulation.get("simulation_basis") or ("cold_start_prior" if simulation.get("cold_start_used") else "historical_memory"),
        "recommendations": recommendations,
    }

    save_last_recommendation(recs)

    # Ensure each recommendation has a rank and reasoning alias.
    normalized_recs = []
    for idx, r in enumerate(recommendations, start=1):
        rec_out = {
            "recommendation_id": r.get("recommendation_id"),
            "item_id": r.get("item_id"),
            "rank": idx,
            "item_name": r.get("item_name"),
            "category": r.get("item_category"),
            "confidence": r.get("confidence"),
            "reasoning": r.get("explanation") or "",
            "explanation": r.get("explanation") or "",
            "recommendation_type": r.get("recommendation_type"),
        }
        normalized_recs.append(rec_out)

    # Compute exploration/diversity proxy
    try:
        exploration_ratio = sum(1 for r in recommendations if (r.get("recommendation_type") in {"adjacent_exploration", "discovery"})) / max(1, len(recommendations))
    except Exception:
        exploration_ratio = 0.0

    out = {
        "recommendations": normalized_recs,
        "diversity_score": round(float(exploration_ratio), 2),
        "cold_start_handled": bool(simulation.get("cold_start_used")),
        "exploration_ratio": round(float(exploration_ratio), 2),
        "live_data_used": bool(live_candidates),
        "live_search_query": live_search_query,
        "live_search_source": live_search_source,
        "_internal": recs,
    }

    if payload.output_format.strip().lower() == "text":
        lines = [
            f"User: {user_token}",
            f"Cold start handled: {out['cold_start_handled']}",
            f"Diversity score: {out['diversity_score']}",
            "Recommendations:",
        ]
        for rec in normalized_recs[:10]:
            lines.append(f"- {rec['rank']}. {rec['item_name']} ({rec['category']}) | {rec['reasoning']}")
        return PlainTextResponse("\n".join(lines))

    return out


@router.post("/v1/explain", response_model=ExplainResponse)
async def explain(payload: ExplainRequest, request: Request):
    from api.main import _ensure_app_state
    from orchestrator import LangGraphStyleOrchestrator

    _ensure_app_state()
    try:
        agent_graph: LangGraphStyleOrchestrator = request.app.state.agent_graph
        return await agent_graph.route_task_b(
            action="explain",
            user_token=payload.user_token,
            recommendation_id=payload.recommendation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
