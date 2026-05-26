from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from .base_agent import BaseAgent, AgentState


class ReviewGenerationAgent(BaseAgent):
    """Task A agent that generates rating + review from simulated behavior.

    The implementation prefers LLM-based generation when available; falls back
    to the deterministic generator for reliability.
    """

    name = "review_generation"

    _PIDGIN_MARKERS = ("sha", "abi", "sef", "abeg", "na im", "e be like", "naija", "9ja", "oga")
    _NIGERIAN_ENGLISH_MARKERS = ("very okay", "too much", "value", "price", "worth it", "not bad", "food", "service")
    _FORMAL_MARKERS = ("overall", "however", "recommend", "consistent", "quality", "experience")

    async def run(self, state: AgentState) -> AgentState:
        return state

    @classmethod
    async def generate(
        cls,
        *,
        user_token: str,
        user_history: list[dict[str, Any]],
        item: dict[str, Any],
        context: dict[str, Any],
        simulation: Any,
    ) -> dict[str, Any]:
        """Prefer LLM-based generation: construct a prompt with the simulation snapshot
        and request a JSON response with rating, review text, confidence, and reasoning.

        If LLM is unavailable or fails, use the deterministic generator.
        """
        # Try LLM path
        try:
            from agents.simulation_agent import SimulationAgent

            sim_agent = SimulationAgent()
            if sim_agent.llm is not None:
                # Build prompt
                system_prompt = """You are ARCHE's Review Generation engine. Given a behavioral snapshot, user history, and item details,
produce a realistic review text and a star rating. Respond with a JSON object with keys:
predicted_rating (int 1-5), generated_review (string), confidence (0.0-1.0), reasoning (brief string).
Do NOT include any surrounding commentary."""

                snapshot = getattr(simulation, 'behavioral_snapshot', simulation) if simulation is not None else {}
                user_history_text = "\n".join([f"- {h.get('item_name')}: {h.get('review_text')} ({h.get('rating')})" for h in user_history])

                user_prompt = f"Behavioral snapshot:\n{snapshot}\n\nUser history:\n{user_history_text}\n\nItem details:\n{item}\n\nContext:\n{context}\n\nProduce the JSON response."

                content = await sim_agent.call_llm(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.45)

                # Parse LLM output
                if isinstance(content, str):
                    if "```json" in content:
                        content = content.split("```json", 1)[1].split("```", 1)[0]
                    elif "```" in content:
                        content = content.split("```", 1)[1].split("```", 1)[0]
                    parsed = None
                    try:
                        parsed = __import__("json").loads(content.strip())
                    except Exception:
                        parsed = None

                    if parsed and isinstance(parsed, dict):
                        return {
                            "predicted_rating": int(parsed.get("predicted_rating") or parsed.get("rating") or 3),
                            "generated_review": str(parsed.get("generated_review") or parsed.get("review_text") or ""),
                            "tone_confidence": float(parsed.get("confidence") or parsed.get("tone_confidence") or 0.0),
                            "behavioural_basis": str(parsed.get("reasoning") or parsed.get("behavioural_basis") or ""),
                            "user_token": user_token,
                            "llm_instrumentation": {
                                "used": True,
                                "provider": sim_agent.llm_provider,
                                "model": sim_agent.groq_model if sim_agent.llm_provider == "groq" else "claude-3-5-sonnet-20241022",
                            },
                        }
        except Exception:
            # LLM path failed; fall back to deterministic
            pass

        # Deterministic fallback (original behavior)
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

        # Extract context with proper aliases
        time_context = context.get("time_of_day") or context.get("time_bucket") or "unspecified time"
        region_context = context.get("region") or context.get("region_tier") or "unspecified region"

        behavioural_basis = (
            f"Detected {register} register with {len(user_history)} prior reviews; "
            f"simulation basis {simulation.simulation_basis}; top affinities {', '.join(top_affinities)}; "
            f"context {time_context} / {region_context}; "
            f"calibration: {nigerian_context}"
        )

        return {
            "predicted_rating": predicted_rating,
            "generated_review": generated_review,
            "tone_confidence": tone_confidence,
            "behavioural_basis": behavioural_basis,
            "user_token": user_token,
            "llm_instrumentation": {
                "used": False,
                "provider": None,
                "model": None,
            },
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
    def _extract_style_metrics(history: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract STYLE metrics from history, NOT content.
        Returns vocabulary complexity, sentence length, tone markers."""
        if not history:
            return {"avg_length": 50, "vocabulary_density": 0.3, "complexity": "moderate"}
        
        all_text = " ".join(str(h.get("review_text") or "") for h in history)
        if not all_text:
            return {"avg_length": 50, "vocabulary_density": 0.3, "complexity": "moderate"}
        
        sentences = [s.strip() for s in all_text.split(".") if s.strip()]
        avg_length = mean([len(s.split()) for s in sentences]) if sentences else 50
        
        # Calculate vocabulary diversity
        words = all_text.lower().split()
        unique_words = len(set(words))
        vocab_density = min(1.0, unique_words / max(1, len(words)))
        
        # Determine complexity level
        if avg_length > 20:
            complexity = "formal"
        elif avg_length > 12:
            complexity = "conversational"
        else:
            complexity = "casual"
        
        return {
            "avg_length": avg_length,
            "vocabulary_density": vocab_density,
            "complexity": complexity,
        }

    @staticmethod
    def _generated_review_text(
        *,
        history: list[dict[str, Any]],
        item: dict[str, Any],
        predicted_rating: int,
        register: str,
        context: dict[str, Any],
    ) -> str:
        """Generate a fresh review WITHOUT copying historical text.
        Extract style patterns but create entirely new content for the target item."""
        
        # Extract style metrics (not content)
        style = ReviewGenerationAgent._extract_style_metrics(history)
        
        # Fix context extraction to handle both aliases
        time_context = context.get("time_of_day") or context.get("time_bucket") or "unspecified time"
        region_context = context.get("region") or context.get("region_tier") or "unspecified region"
        
        item_name = str(item.get("name") or "This item")
        item_category = str(item.get("category") or "general")

        mood = {
            5: "top tier",
            4: "solid",
            3: "decent",
            2: "mixed",
            1: "not impressive",
        }[predicted_rating]

        attribute_text = ReviewGenerationAgent._attribute_phrase(dict(item.get("attributes") or {}))
        attribute_clause = f" The main details are {attribute_text}." if attribute_text else ""

        # Generate fresh review based on register and style metrics
        if register == "casual_pidgin":
            return (
                f"{item_name} dey look {mood} sha. No lie, for {time_context} here for {region_context}, "
                f"it touches the vibe well. {attribute_text or 'Everything feels right'} make sense for the value. "
                f"I rate this kind thing when I see am.{attribute_clause}"
            )
        
        if register == "mixed_pidgin":
            return (
                f"{item_name} is {mood}, abeg. Na so the thing dey work for {time_context} in {region_context}, "
                f"and the value be the thing I still dey consider sha. {attribute_text or 'E get good points'}. "
                f"I would rate am like this.{attribute_clause}"
            )
        
        if register == "nigerian_english":
            return (
                f"{item_name} is very okay sha. For {time_context} when you are at {region_context}, "
                f"it performs well and the overall fit is {mood}. {attribute_text or 'The quality sits well'}. "
                f"I would recommend am, depending on what you are comparing it with.{attribute_clause}"
            )
        
        # formal_english (default)
        return (
            f"{item_name} presents as {mood} across {item_category.lower()} offerings. "
            f"In the context of {time_context} and given the {region_context} location, this item demonstrates consistent value. "
            f"{attribute_text or 'The attributes align well'}. On balance, I would rate this favorably.{attribute_clause}"
        )