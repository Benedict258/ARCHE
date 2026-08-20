from typing import Any, Dict, List
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from api.rate_limit import limiter, RATE_LIMIT_EXPENSIVE, RATE_LIMIT_STANDARD
from api.request_repair import repair_payload_from_text
from agents.recommendation_pipeline import run_recommendation_pipeline

router = APIRouter()


class ItemDetailsModel(BaseModel):
    """Member item of an evaluation pool."""
    item_id: str | None = Field(default=None, alias="id")
    name: str | None = None
    item_name: str | None = None
    category: str | None = None
    item_category: str | None = None
    price_tier: str | None = "mid"
    description: str | None = ""
    attributes: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


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
    review_history: list[dict[str, Any]] = Field(default_factory=list, max_length=200)


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
    user_history: list[dict[str, Any]] = Field(default_factory=list, max_length=200, description="Alias for inline review history - accepted at top-level for convenience.")
    user_persona: UserPersona | None = Field(
        default=None,
        description="Preferred nesting for user identity and review history.",
    )
    context: SimulateContext = Field(
        default_factory=SimulateContext,
        description="Context such as time_bucket, device_class, or entry_point.",
    )
    item_pool: List[ItemDetailsModel] | None = Field(
        default=None,
        max_length=200,
        description="Pool of items to rank for recommendation. If provided, the local catalog is ignored.",
    )
    n: int = Field(default=10, ge=1, le=50, description="Number of recommendations to return.")
    domain_filter: str | None = Field(default=None, description="Optional domain filter like food, books, or shopping.")
    enable_live_data: bool = Field(
        default=False,
        description="When true, the app fetches live candidates from the web via Serper/DuckDuckGo and blends them with the local catalog.",
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
        max_length=4000,
        description="Paste free text or malformed JSON here; the server will repair it into valid JSON.",
    )
    output_format: str = Field(
        default="json",
        description="Choose json for API testing or text for a human-readable response.",
    )


class RecommendationOut(BaseModel):
    recommendation_id: str
    item_id: str | None = None
    rank: int
    item_name: str
    category: str
    confidence: float
    explanation: str
    recommendation_type: str


class RecommendResponse(BaseModel):
    recommendations: list[RecommendationOut]
    diversity_score: float
    cold_start_handled: bool
    exploration_ratio: float
    live_data_used: bool
    live_search_query: str | None = None
    live_search_source: str | None = None
    live_search_provider: str | None = None
    llm_instrumentation: Dict[str, Any]


class ExplainRequest(BaseModel):
    user_token: str = Field(min_length=1)
    recommendation_id: str = Field(min_length=1)


@router.post("/v1/recommend", response_model=RecommendResponse)
@router.post("/api/v1/recommend", response_model=RecommendResponse)
@limiter.limit(RATE_LIMIT_EXPENSIVE)
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

    if payload.raw_input and not payload.user_persona and not payload.user_token and not payload.item_pool:
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
    user_history = persona.review_history if persona else payload.user_history
    context = payload.context.model_dump() if hasattr(payload.context, "model_dump") else dict(payload.context or {})
    domain_filter = (payload.domain_filter or context.get("entry_point") or context.get("domain") or "").strip().lower()
    lookup_token = privacy.anonymize_token(user_token, "user") or user_token

    item_pool = [item.model_dump() for item in payload.item_pool] if payload.item_pool else None

    out = await run_recommendation_pipeline(
        user_token=user_token,
        lookup_token=lookup_token,
        user_history=user_history,
        context=context,
        domain_filter=domain_filter,
        n=payload.n,
        item_pool=item_pool,
        enable_live_data=payload.enable_live_data,
        live_query=payload.live_query,
        live_results_limit=payload.live_results_limit,
        memory_manager=request.app.state.memory_manager,
    )

    if payload.output_format.strip().lower() == "text":
        lines = [
            f"User: {user_token}",
            f"Cold start handled: {out['cold_start_handled']}",
            f"Diversity score: {out['diversity_score']}",
            "Recommendations:",
        ]
        for rec in out["recommendations"][:10]:
            lines.append(f"- {rec['rank']}. {rec['item_name']} ({rec['category']}) | {rec['explanation']}")
        return PlainTextResponse("\n".join(lines))

    return out


@router.get("/v1/recommend")
@router.get("/api/v1/recommend")
async def recommend_help():
    return {
        "method": "POST",
        "endpoint": "/v1/recommend",
        "hint": "Send JSON with user_token, context, n, domain_filter, enable_live_data, output_format.",
    }


@router.post("/v1/explain")
@router.post("/api/v1/explain")
@limiter.limit(RATE_LIMIT_STANDARD)
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


@router.get("/v1/explain")
@router.get("/api/v1/explain")
async def explain_help():
    return {
        "method": "POST",
        "endpoint": "/v1/explain",
        "hint": "Send JSON with user_token and recommendation_id.",
    }
