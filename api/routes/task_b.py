from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


class SimulateContext(BaseModel):
    time_bucket: str | None = None
    day_type: str | None = None
    device_class: str | None = None
    network_quality: str | None = None
    region_tier: str | None = None
    session_depth: int | None = None
    entry_point: str | None = None


class RecommendRequest(BaseModel):
    user_token: str = Field(min_length=1)
    context: SimulateContext = Field(default_factory=SimulateContext)
    n: int = 10


class Recommendation(BaseModel):
    recommendation_id: str
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


@router.post("/v1/recommend", response_model=RecommendationSet)
async def recommend(payload: RecommendRequest, request: Request):
    from api.main import _ensure_app_state
    from orchestrator import LangGraphStyleOrchestrator

    _ensure_app_state()
    agent_graph: LangGraphStyleOrchestrator = request.app.state.agent_graph
    return await agent_graph.route_task_b(
        action="recommend",
        user_token=payload.user_token,
        context=payload.context,
        n=payload.n,
    )


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
