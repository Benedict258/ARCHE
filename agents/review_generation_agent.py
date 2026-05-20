from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from .base_agent import BaseAgent, AgentState


class ReviewGenerationAgent(BaseAgent):
    """Task A agent that generates rating + review from simulated behavior.

    The implementation is deterministic for MVP reliability while preserving
    the agent boundary required by HackAlign.
    """

    name = "review_generation"

    _PIDGIN_MARKERS = ("sha", "abi", "sef", "abeg", "na im", "e be like", "naija", "9ja", "oga")
    _NIGERIAN_ENGLISH_MARKERS = ("very okay", "too much", "value", "price", "worth it", "not bad", "food", "service")
    _FORMAL_MARKERS = ("overall", "however", "recommend", "consistent", "quality", "experience")

    async def run(self, state: AgentState) -> AgentState:
        return state

    @classmethod
    def generate(
        cls,
        *,
        user_token: str,
        user_history: list[dict[str, Any]],
        item: dict[str, Any],
        context: dict[str, Any],
        simulation: Any,
    ) -> dict[str, Any]:
        history_texts = [str(entry.get("review_text") or "") for entry in user_history]
        register = cls.detect_register(history_texts)
        nigerian_context = cls.get_nigerian_calibration(register)

        predicted_rating = cls._predict_rating(user_history, item, simulation)
        generated_review = cls._generated_review_text(
            history=user_history,
            item=item,
            predicted_rating=predicted_rating,
            register=register,
            context=context,
        )

        tone_confidence = 0.42 + min(0.3, len(user_history) * 0.06)
        if register != "formal_english":
            tone_confidence += 0.1
        top_affinities = [str(v) for v in (simulation.behavioral_snapshot.top_affinities or [])]
        if str(item.get("category") or "").lower() in {a.lower() for a in top_affinities}:
            tone_confidence += 0.1
        if item.get("attributes"):
            tone_confidence += 0.05
        tone_confidence = round(min(0.95, tone_confidence), 2)

        behavioural_basis = (
            f"Detected {register} register with {len(user_history)} prior reviews; "
            f"simulation basis {simulation.simulation_basis}; top affinities {', '.join(top_affinities)}; "
            f"context {context.get('time_bucket') or 'unspecified time'} / {context.get('region_tier') or context.get('region') or 'unspecified region'}; "
            f"calibration: {nigerian_context}"
        )

        return {
            "predicted_rating": predicted_rating,
            "generated_review": generated_review,
            "tone_confidence": tone_confidence,
            "behavioural_basis": behavioural_basis,
            "user_token": user_token,
        }

    @classmethod
    def detect_register(cls, history_texts: list[str]) -> str:
        combined = " ".join(text.lower() for text in history_texts if text)
        pidgin_score = sum(marker in combined for marker in cls._PIDGIN_MARKERS)
        nig_eng_score = sum(marker in combined for marker in cls._NIGERIAN_ENGLISH_MARKERS)
        formal_score = sum(marker in combined for marker in cls._FORMAL_MARKERS)

        if pidgin_score >= 2:
            return "casual_pidgin" if pidgin_score >= 4 else "mixed_pidgin"
        if nig_eng_score >= 2 and formal_score < 2:
            return "nigerian_english"
        return "formal_english"

    @staticmethod
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
            "formal_english": "Use clear formal English with a neutral, thoughtful tone.",
        }
        return calibrations.get(register, calibrations["formal_english"])

    @staticmethod
    def _history_weights(history: list[dict[str, Any]]) -> list[float]:
        if not history:
            return []
        total = len(history)
        return [0.75 + ((idx + 1) / total) * 0.35 for idx in range(total)]

    @staticmethod
    def _weighted_mean(values: list[float], weights: list[float]) -> float:
        if not values:
            return 3.0
        if len(values) != len(weights) or not weights:
            return mean(values)
        numerator = sum(v * w for v, w in zip(values, weights))
        denominator = sum(weights)
        return numerator / denominator if denominator else mean(values)

    @staticmethod
    def _clamp_rating(value: float) -> int:
        return max(1, min(5, int(round(value))))

    @staticmethod
    def _predict_rating(history: list[dict[str, Any]], item: dict[str, Any], simulation: Any) -> int:
        ratings = [float(h.get("rating") or 3.0) for h in history]
        weights = ReviewGenerationAgent._history_weights(history)
        base = ReviewGenerationAgent._weighted_mean(ratings, weights)

        affinities = {str(aff).lower() for aff in simulation.behavioral_snapshot.top_affinities}
        category = str(item.get("category") or "").lower()
        history_categories = Counter(str(h.get("item_category") or "").lower() for h in history)
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
            marker in str(h.get("review_text") or "").lower()
            for h in history
            for marker in ("value", "worth", "fair", "good", "solid", "okay")
        )
        has_price_signal = any(
            marker in str(h.get("review_text") or "").lower()
            for h in history
            for marker in ("price", "overpriced", "expensive", "cost", "budget")
        )
        item_price_tier = str(item.get("price_tier") or "mid")
        if item_price_tier in {"budget", "mid"} and has_value_signal:
            score += 0.35
        if item_price_tier in {"premium", "luxury"} and has_price_signal:
            score -= 0.4
        if simulation.behavioral_snapshot.current_intent == "active_purchase":
            score += 0.1

        score = (score * 0.8) + (base * 0.2)
        return ReviewGenerationAgent._clamp_rating(score)

    @staticmethod
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

    @staticmethod
    def _style_anchor(history: list[dict[str, Any]]) -> str:
        if not history:
            return "The experience feels balanced"
        latest = str(history[-1].get("review_text") or "").strip()
        if not latest:
            return "The experience feels balanced"
        first_sentence = latest.split(".")[0].strip()
        return first_sentence[:120] if first_sentence else latest[:120]

    @staticmethod
    def _generated_review_text(
        *,
        history: list[dict[str, Any]],
        item: dict[str, Any],
        predicted_rating: int,
        register: str,
        context: dict[str, Any],
    ) -> str:
        last_review = ReviewGenerationAgent._style_anchor(history)
        item_name = str(item.get("name") or "This item")
        item_category = str(item.get("category") or "general")
        time_bucket = str(context.get("time_bucket") or "unspecified time")
        region = str(context.get("region") or context.get("region_tier") or "unknown region")

        mood = {
            5: "top tier",
            4: "solid",
            3: "decent",
            2: "mixed",
            1: "not impressive",
        }[predicted_rating]

        attribute_text = ReviewGenerationAgent._attribute_phrase(dict(item.get("attributes") or {}))
        attribute_clause = f" The main details are {attribute_text}." if attribute_text else ""

        if register == "casual_pidgin":
            return (
                f"{item_name} dey okay sha. Na {mood} vibe be that, but I still dey look at the value side. "
                f"At {time_bucket} for {region}, e no bad like that, and e still get sense because {attribute_text or 'the details fit the price'}."
            )
        if register == "mixed_pidgin":
            return (
                f"{item_name} is {mood}, no lie. E fit work well for {time_bucket} in {region}, but I still want better value. "
                f"From the way I review things, the experience is {last_review.lower() or 'balanced'}{attribute_clause}"
            )
        if register == "nigerian_english":
            return (
                f"{item_name} is very okay sha. It does the job for {time_bucket} in {region}, but the value still matters. "
                f"I would say it is {mood}, especially if you are comparing with similar options. {attribute_clause.strip()}"
            )

        style_anchor = last_review[:120].rstrip(".") if last_review else "The experience feels balanced"
        return (
            f"{style_anchor}. {item_name} feels {mood} overall, and the {item_category.lower()} fit is fair for {time_bucket} in {region}. "
            f"I would say it is decent, but the value still depends on what you are comparing it with.{attribute_clause}"
        )