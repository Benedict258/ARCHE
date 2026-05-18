from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from fastapi import APIRouter
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


_PIDGIN_MARKERS = ("sha", "abi", "sef", "abeg", "na im", "e be like", "naija", "9ja", "oga")
_NIGERIAN_ENGLISH_MARKERS = ("very okay", "too much", "value", "price", "worth it", "not bad", "food", "service")
_FORMAL_MARKERS = ("overall", "however", "recommend", "consistent", "quality", "experience")


def _normalise_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "time_bucket": context.get("time_bucket"),
        "day_type": context.get("day_type"),
        "region_tier": context.get("region") or context.get("region_tier"),
        "device_class": context.get("device_class"),
    }


def detect_register(history_texts: list[str]) -> str:
    combined = " ".join(text.lower() for text in history_texts if text)
    pidgin_score = sum(marker in combined for marker in _PIDGIN_MARKERS)
    nig_eng_score = sum(marker in combined for marker in _NIGERIAN_ENGLISH_MARKERS)
    formal_score = sum(marker in combined for marker in _FORMAL_MARKERS)

    if pidgin_score >= 2:
        return "casual_pidgin" if pidgin_score >= 4 else "mixed_pidgin"
    if nig_eng_score >= 2 and formal_score < 2:
        return "nigerian_english"
    return "formal_english"


def get_nigerian_calibration(register: str) -> str:
    calibrations = {
        "casual_pidgin": (
            "Use relaxed Nigerian Pidgin-mixed English. Keep it direct, short, and natural. "
            "Reference value, taste, service pace, or vibe when relevant."
        ),
        "mixed_pidgin": (
            "Use a balanced mix of Nigerian English and light pidgin. Keep the review grounded and conversational."
        ),
        "nigerian_english": (
            "Use Nigerian English with familiar markers like 'sha', 'too much', 'very okay', and practical value judgments."
        ),
        "formal_english": (
            "Use clear formal English with a neutral, thoughtful tone."
        ),
    }
    return calibrations.get(register, calibrations["formal_english"])


def _history_weights(history: list[ReviewHistoryItem]) -> list[float]:
    if not history:
        return []
    total = len(history)
    return [0.75 + ((idx + 1) / total) * 0.35 for idx in range(total)]


def _weighted_mean(values: list[float], weights: list[float]) -> float:
    if not values:
        return 3.0
    if len(values) != len(weights) or not weights:
        return mean(values)
    numerator = sum(v * w for v, w in zip(values, weights))
    denominator = sum(weights)
    return numerator / denominator if denominator else mean(values)


def _attribute_phrase(attributes: dict[str, Any]) -> str:
    if not attributes:
        return ""
    fragments: list[str] = []
    for key, value in list(attributes.items())[:3]:
        label = str(key).replace("_", " ")
        if isinstance(value, bool):
            fragments.append(f"{label} is {'present' if value else 'not strong'}")
        else:
            fragments.append(f"{label} is {value}")
    return ", ".join(fragments)


def _style_anchor(history: list[ReviewHistoryItem]) -> str:
    if not history:
        return "The experience feels balanced"
    latest = history[-1].review_text.strip()
    if not latest:
        return "The experience feels balanced"
    first_sentence = latest.split(".")[0].strip()
    return first_sentence[:120] if first_sentence else latest[:120]


def _build_history_memory_payload(user_token: str, history: list[ReviewHistoryItem]) -> dict[str, Any]:
    from datetime import datetime, timezone

    timestamp = int(datetime.now(timezone.utc).timestamp())
    session_rows = []
    for idx, entry in enumerate(history, start=1):
        session_rows.append(
            (
                idx,
                user_token,
                "review",
                entry.item_name,
                entry.item_category,
                {},
                None,
                None,
                idx,
                timestamp - (len(history) - idx),
            )
        )
    return {"session": session_rows, "is_cold_start": len(session_rows) == 0}


def _clamp_rating(value: float) -> int:
    return max(1, min(5, int(round(value))))


def _predict_rating(history: list[ReviewHistoryItem], item: ItemDetails, simulation) -> int:
    ratings = [float(h.rating) for h in history]
    weights = _history_weights(history)
    base = _weighted_mean(ratings, weights)
    affinities = {aff.lower() for aff in simulation.behavioral_snapshot.top_affinities}
    category = item.category.lower()
    history_categories = Counter(h.item_category.lower() for h in history)
    category_overlap = history_categories.get(category, 0)

    score = float(base)
    if category in affinities:
        score += 0.55
    elif any(category in historical or historical in category for historical in history_categories):
        score += 0.2
    else:
        score -= 0.95

    if category_overlap >= 2:
        score += 0.25
    elif category_overlap == 1:
        score += 0.08

    has_value_signal = any(
        marker in h.review_text.lower()
        for h in history
        for marker in ("value", "worth", "fair", "good", "solid", "okay")
    )
    has_price_signal = any(
        marker in h.review_text.lower()
        for h in history
        for marker in ("price", "overpriced", "expensive", "cost", "budget")
    )
    if item.price_tier in {"budget", "mid"} and has_value_signal:
        score += 0.35
    if item.price_tier in {"premium", "luxury"} and has_price_signal:
        score -= 0.4
    if simulation.behavioral_snapshot.current_intent == "active_purchase":
        score += 0.1

    # Keep the score anchored to the user's average while allowing modest category/value adjustments.
    score = (score * 0.8) + (base * 0.2)

    return _clamp_rating(score)


def _generated_review_text(
    history: list[ReviewHistoryItem],
    item: ItemDetails,
    predicted_rating: int,
    register: str,
    calibration: str,
    context: dict[str, Any],
) -> str:
    last_review = _style_anchor(history)
    time_bucket = context.get("time_bucket") or "unspecified time"
    region = context.get("region") or context.get("region_tier") or "unknown region"
    mood = {
        5: "top tier",
        4: "solid",
        3: "decent",
        2: "mixed",
        1: "not impressive",
    }[predicted_rating]
    attribute_text = _attribute_phrase(item.attributes)
    attribute_clause = f" The main details are {attribute_text}." if attribute_text else ""

    if register == "casual_pidgin":
        return (
            f"{item.name} dey okay sha. Na {mood} vibe be that, but I still dey look at the value side. "
            f"At {time_bucket} for {region}, e no bad like that, and e still get sense because {attribute_text or 'the details fit the price'}."
        )
    if register == "mixed_pidgin":
        return (
            f"{item.name} is {mood}, no lie. E fit work well for {time_bucket} in {region}, but I still want better value. "
            f"From the way I review things, the experience is {last_review.lower() or 'balanced'}{attribute_clause}"
        )
    if register == "nigerian_english":
        return (
            f"{item.name} is very okay sha. It does the job for {time_bucket} in {region}, but the value still matters. "
            f"I would say it is {mood}, especially if you are comparing with similar options. {attribute_clause.strip()}"
        )

    style_anchor = last_review[:120].rstrip(".") if last_review else "The experience feels balanced"
    return (
        f"{style_anchor}. {item.name} feels {mood} overall, and the {item.category.lower()} fit is fair for {time_bucket} in {region}. "
        f"I would say it is decent, but the value still depends on what you are comparing it with.{attribute_clause}"
    )


@router.post("/v1/simulate-review", response_model=SimulateReviewResponse)
async def simulate_review(request: SimulateReviewRequest):
    """
    Task A: Given user history + unseen item, simulate what the user would write and rate.
    """
    from api.main import SimulateContext, _build_simulation_response

    normalized_context = _normalise_context(request.context)
    simulate_context = SimulateContext(**{k: v for k, v in normalized_context.items() if v is not None})
    memory_payload = _build_history_memory_payload(request.user_token, request.user_history)
    simulation = _build_simulation_response(request.user_token, simulate_context, memory_payload)

    history_texts = [entry.review_text for entry in request.user_history]
    register = detect_register(history_texts)
    nigerian_context = get_nigerian_calibration(register)

    predicted_rating = _predict_rating(request.user_history, request.item, simulation)
    generated_review = _generated_review_text(
        request.user_history,
        request.item,
        predicted_rating,
        register,
        nigerian_context,
        request.context,
    )

    tone_confidence = 0.42 + min(0.3, len(request.user_history) * 0.06)
    if register != "formal_english":
        tone_confidence += 0.1
    if simulation.behavioral_snapshot.top_affinities and request.item.category.lower() in {a.lower() for a in simulation.behavioral_snapshot.top_affinities}:
        tone_confidence += 0.1
    if request.item.attributes:
        tone_confidence += 0.05
    tone_confidence = round(min(0.95, tone_confidence), 2)

    behavioural_basis = (
        f"Detected {register} register with {len(request.user_history)} prior reviews; "
        f"simulation basis {simulation.simulation_basis}; top affinities {', '.join(simulation.behavioral_snapshot.top_affinities)}; "
        f"context {normalized_context.get('time_bucket') or 'unspecified time'} / {normalized_context.get('region_tier') or 'unspecified region'}; "
        f"calibration: {nigerian_context}"
    )

    return SimulateReviewResponse(
        predicted_rating=predicted_rating,
        generated_review=generated_review,
        tone_confidence=tone_confidence,
        behavioural_basis=behavioural_basis,
    )