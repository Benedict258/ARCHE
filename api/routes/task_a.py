from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from api.request_repair import repair_payload_from_text

router = APIRouter()


class ReviewHistoryItem(BaseModel):
    """Single prior review used to simulate the user's taste profile."""

    model_config = ConfigDict(populate_by_name=True)
    
    item_name: str
    item_category: str = Field(alias='category')
    rating: float
    review_text: str


class ItemDetails(BaseModel):
    """Item being reviewed in Task A."""

    name: str
    category: str
    price_tier: str = "mid"
    attributes: dict[str, Any] = Field(default_factory=dict)


class UserPersona(BaseModel):
    user_id: str | None = None
    user_token: str | None = None
    review_history: list[ReviewHistoryItem] = Field(default_factory=list)


class SimulateReviewRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_persona": {
                        "user_id": "chidi_001",
                        "review_history": [
                            {
                                "item_name": "Chicken Republic Lekki",
                                "item_category": "fast_food",
                                "rating": 4,
                                "review_text": "Sha, the jollof was okay and service was decent.",
                            }
                        ],
                    },
                    "item_details": {
                        "name": "Dominos Pizza Lagos",
                        "category": "fast_food",
                        "price_tier": "mid",
                        "attributes": {"delivery": True},
                    },
                    "context": {"time_of_day": "evening", "region": "Lagos"},
                    "output_format": "json",
                }
            ]
        }
    )

    user_token: str | None = Field(default=None, description="Optional user token if not using user_persona.")
    user_history: list[ReviewHistoryItem] = Field(
        default_factory=list,
        description="Paste prior reviews here, or use user_persona.review_history.",
    )
    item: ItemDetails | None = Field(default=None, description="Item to simulate a review for.")
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Context such as time_of_day, region, or occasion.",
    )
    user_persona: UserPersona | None = Field(
        default=None,
        description="Preferred judge-friendly nesting for user identity and review history.",
    )
    item_details: ItemDetails | None = Field(
        default=None,
        description="Alternate item field accepted by the handler.",
    )
    raw_input: str | None = Field(
        default=None,
        description="Paste free text or malformed JSON here; the server will repair it into valid JSON.",
    )
    output_format: str = Field(
        default="json",
        description="Choose json for API testing or text for a human-readable response.",
    )


class SimulateReviewResponse(BaseModel):
    predicted_rating: float
    generated_review: str
    tone_confidence: float
    behavioural_basis: str


def _normalise_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "time_bucket": context.get("time_of_day") or context.get("time_bucket"),
        "day_type": context.get("day_type"),
        "region_tier": context.get("region") or context.get("region_tier"),
        "device_class": context.get("device_class"),
    }


@router.post("/v1/simulate-review")
@router.post("/api/v1/simulate-review")
async def simulate_review(payload: SimulateReviewRequest, http_request: Request):
    """Task A: route request through orchestrator -> simulation agent -> review generation agent.

    Returns a submission-friendly JSON contract that includes both the existing
    internal fields and the HackAlign-friendly aliases `confidence` and `reasoning`.

    Swagger tips:
    - Use `user_persona.review_history` for normal testing.
    - Use `raw_input` if you want the server to repair free text or malformed JSON.
    - Set `output_format` to `text` for a human-readable response.
    """
    from api.main import _ensure_app_state
    from orchestrator import LangGraphStyleOrchestrator

    _ensure_app_state()
    agent_graph: LangGraphStyleOrchestrator = http_request.app.state.agent_graph

    # Accept either the strict shape or the HackAlign judge shape that nests a user_persona object.

    if payload.raw_input and not payload.user_persona and not payload.user_history and not payload.item and not payload.item_details and not payload.user_token:
        repaired = await repair_payload_from_text(
            payload.raw_input,
            schema_name="Task A /v1/simulate-review",
            schema_description="Expected keys: user_token or user_persona, user_history, item or item_details, context, output_format.",
            example_payload={
                "user_persona": {"user_id": "chidi_001", "review_history": []},
                "item_details": {"name": "Dominos Pizza Lagos", "category": "fast_food", "price_tier": "mid", "attributes": {}},
                "context": {"time_of_day": "evening", "region": "Lagos"},
                "output_format": "json",
            },
        )
        try:
            payload = SimulateReviewRequest.model_validate(repaired)
        except Exception:
            payload = SimulateReviewRequest.model_validate({**repaired, "output_format": payload.output_format})

    persona = payload.user_persona
    if persona is not None:
        user_token = persona.user_id or persona.user_token or payload.user_token or "anonymous"
        user_history = [entry.model_dump() for entry in persona.review_history]
        item_model = payload.item_details or payload.item
        item = item_model.model_dump() if item_model is not None else {}
        if "item_category" not in item and "category" in item:
            item = dict(item)
            item["item_category"] = item.get("category")
        context = _normalise_context(payload.context)
    else:
        user_token = payload.user_token or "anonymous"
        user_history = [entry.model_dump() for entry in payload.user_history]
        item = payload.item.model_dump() if payload.item is not None else {}
        context = _normalise_context(payload.context)

    result = await agent_graph.route_task_a(
        user_token=user_token,
        user_history=user_history,
        item=item,
        context=context,
    )

    # Provide HackAlign-compatible aliases while preserving original fields.
    tone_confidence = result.get("tone_confidence") if result.get("tone_confidence") is not None else result.get("confidence", 0.0)
    behavioural_basis = result.get("behavioural_basis") or result.get("reasoning", "")
    out = {
        "predicted_rating": result.get("predicted_rating"),
        "generated_review": result.get("generated_review"),
        "tone_confidence": tone_confidence,
        "behavioural_basis": behavioural_basis,
        "llm_instrumentation": result.get("llm_instrumentation") or {"used": False, "provider": None, "model": None},
        # aliases preserved for HackAlign compatibility
        "confidence": tone_confidence,
        "reasoning": behavioural_basis,
        "_internal": result,
    }
    if payload.output_format.strip().lower() == "text":
        pred = out.get('predicted_rating')
        try:
            pred_str = f"{float(pred):.1f}"
        except Exception:
            pred_str = str(pred)
        return PlainTextResponse(
            f"Predicted rating: {pred_str}\n"
            f"Review: {out['generated_review']}\n"
            f"Confidence: {out['tone_confidence']}\n"
            f"Reasoning: {out['behavioural_basis']}"
        )
    return out


@router.get("/v1/simulate-review")
@router.get("/api/v1/simulate-review")
async def simulate_review_help():
    return {
        "method": "POST",
        "endpoint": "/v1/simulate-review",
        "hint": "Send JSON with user_token or user_persona, user_history, item or item_details, context, output_format.",
    }
