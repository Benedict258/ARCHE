from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter()


class ReviewHistoryItem(BaseModel):
    item_name: str
    item_category: str
    rating: int
    review_text: str


class ItemDetails(BaseModel):
    name: str
    category: str
    price_tier: str = "mid"
    attributes: dict[str, Any] = Field(default_factory=dict)


class SimulateReviewRequest(BaseModel):
    user_token: str
    user_history: list[ReviewHistoryItem]
    item: ItemDetails
    context: dict[str, Any] = Field(default_factory=dict)


class SimulateReviewResponse(BaseModel):
    predicted_rating: int
    generated_review: str
    tone_confidence: float
    behavioural_basis: str


def _normalise_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "time_bucket": context.get("time_bucket"),
        "day_type": context.get("day_type"),
        "region_tier": context.get("region") or context.get("region_tier"),
        "device_class": context.get("device_class"),
    }


@router.post("/v1/simulate-review", response_model=SimulateReviewResponse)
async def simulate_review(request: SimulateReviewRequest, http_request: Request):
    """Task A: route request through orchestrator -> simulation agent -> review generation agent."""
    from api.main import _ensure_app_state
    from orchestrator import LangGraphStyleOrchestrator

    _ensure_app_state()
    agent_graph: LangGraphStyleOrchestrator = http_request.app.state.agent_graph
    result = await agent_graph.route_task_a(
        user_token=request.user_token,
        user_history=[entry.model_dump() for entry in request.user_history],
        item=request.item.model_dump(),
        context=_normalise_context(request.context),
    )

    return SimulateReviewResponse(**result)
