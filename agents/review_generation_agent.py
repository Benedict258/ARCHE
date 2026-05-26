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

    _PIDGIN_MARKERS = ("sha", "abi", "sef", "abeg", "na im", "e be like", "naija", "9ja", "oga", "no cap", "fr", "omo", "nah", "mad", "clean", "slaps", "vibe", "it is giving", "unhinged", "chief", "guy", "joor", "ahn", "shey")
    _NIGERIAN_ENGLISH_MARKERS = ("very okay", "too much", "value", "price", "worth it", "not bad", "food", "service", "practical", "quality", "experience", "decent")
    _FORMAL_MARKERS = ("overall", "however", "recommend", "consistent", "research", "thoroughly", "professional")

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
        """Prefer LLM-based generation with refined prompt. Falls back to natural heuristic."""
        # Try LLM path
        try:
            from agents.simulation_agent import SimulationAgent
            import logging
            logger = logging.getLogger("arche.llm")

            sim_agent = SimulationAgent()
            if sim_agent.llm is not None and sim_agent.llm_provider:
                # Extract calibration from register detection
                history_texts = [str(entry.get("review_text") or "") for entry in user_history]
                register = cls.detect_register(history_texts)
                calibration = cls.get_nigerian_calibration(register)
                
                # Extract style metrics but NOT content
                style = cls._extract_style_metrics(user_history)
                history_snippets = "\n".join([f"- {h.get('review_text', '')[:60]}..." for h in user_history[:3]])
                
                # Build the refined prompt following user specifications
                system_prompt = f"""You are simulating a specific user persona to generate a highly realistic review for a new item.

USER REGISTER & STYLE CALIBRATION:
{calibration}

STYLE CHARACTERISTICS (Analyze only. DO NOT copy sentences):
- Average sentence length: {style.get('avg_length', 15):.0f} words
- Vocabulary diversity: {style.get('vocabulary_density', 0.5):.0f}
- Tone: {style.get('complexity', 'conversational')}

CRITICAL EXECUTION RULES:
1. Write a completely organic, fresh review in the persona's authentic voice.
2. DO NOT output raw attribute strings or "key is value" patterns. Translate attributes naturally.
3. Weave contextual variables (time, region) into the experience naturally.
4. Do NOT use robotic meta-phrases unless the persona uses them natively.
Respond ONLY with the review text itself, no JSON, no commentary."""

                time_context = context.get("time_of_day") or context.get("time_bucket") or "daytime"
                region_context = context.get("region") or context.get("region_tier") or "your area"
                
                user_prompt = f"""Generate a review for:
- Item: {item.get('name', 'this item')}
- Category: {item.get('category', 'general')}
- Key attributes: {ReviewGenerationAgent._humanize_attributes(dict(item.get('attributes') or {}))}
- Context: {time_context} in {region_context}

Historical style references:
{history_snippets}

Now write the review:"""

                try:
                    logger.info(f"review_generation llm_call_start provider={sim_agent.llm_provider} model={sim_agent.groq_model if sim_agent.llm_provider == 'groq' else 'claude-3-5-sonnet-20241022'}")
                    content = await sim_agent.call_llm(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.6)
                    logger.info(f"review_generation llm_call_success provider={sim_agent.llm_provider}")
                    
                    # Clean up the response
                    review_text = str(content).strip()
                    if review_text.startswith(('"', "'")):
                        review_text = review_text.strip('"\'')
                    
                    # Predict rating based on history
                    predicted_rating = cls._predict_rating(user_history, item, simulation)
                    tone_confidence = 0.78
                    
                    return {
                        "predicted_rating": predicted_rating,
                        "generated_review": review_text,
                        "tone_confidence": tone_confidence,
                        "behavioural_basis": f"LLM-generated {register} review for {item.get('name', 'item')}",
                        "user_token": user_token,
                        "llm_instrumentation": {
                            "used": True,
                            "provider": sim_agent.llm_provider,
                            "model": sim_agent.groq_model if sim_agent.llm_provider == "groq" else "claude-3-5-sonnet-20241022",
                        },
                    }
                except Exception as llm_error:
                    logger.debug(f"LLM generation failed, using fallback: {str(llm_error)[:60]}")
        except Exception as e:
            import logging
            logging.getLogger("arche.llm").debug(f"LLM init failed: {e}")

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
    def _humanize_attributes(attributes: dict[str, Any]) -> str:
        """Convert raw attributes into natural language hints for LLM context.
        DO NOT include these directly in review - they're just for LLM awareness."""
        if not attributes:
            return "no special attributes"
        hints: list[str] = []
        for key, value in list(attributes.items())[:3]:
            label = str(key).replace("_", " ").title()
            if isinstance(value, bool):
                if value:
                    hints.append(f"{label} available")
            else:
                hints.append(f"{label}: {value}")
        return "; ".join(hints) if hints else "standard"

    @staticmethod
    def _attribute_phrase(attributes: dict[str, Any]) -> str:
        """Deprecated: Fall-back for old code. Use _humanize_attributes instead."""
        if not attributes:
            return ""
        return ReviewGenerationAgent._humanize_attributes(attributes)

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
        """Generate a NATURAL fallback review without copying history or dumping raw attributes.
        This fires when LLM is unavailable - prioritize authenticity over perfection."""
        
        # Context extraction with aliases
        time_context = context.get("time_of_day") or context.get("time_bucket") or "daytime"
        region_context = context.get("region") or context.get("region_tier") or "here"
        
        item_name = str(item.get("name") or "This item")

        # Sentiment descriptors - never leak raw attributes
        positive_sentiment = {
            5: "absolutely fantastic",
            4: "really solid",
            3: "pretty good",
            2: "decent enough",
            1: "disappointing",
        }[predicted_rating]
        
        recommendation = {
            5: "definitely buying again",
            4: "a great choice",
            3: "worth trying",
            2: "an okay option",
            1: "not for me",
        }[predicted_rating]

        # Generate natural reviews per register - NO attribute dumping, NO robotic templates
        if register == "casual_pidgin":
            return (
                f"Yo, {item_name}? No cap, it's {positive_sentiment}. "
                f"For {time_context} here in {region_context}, the thing just slaps different. "
                f"No complaints at all. Would I grab another? Straight up yes, {recommendation}."
            )
        
        if register == "mixed_pidgin":
            return (
                f"{item_name} sha, e no disappoint. {time_context} when you're at {region_context}, "
                f"this one stands out for real. Abeg, the functionality is on point. "
                f"If I need another, without thinking twice, {recommendation}."
            )
        
        if register == "nigerian_english":
            return (
                f"{item_name}? Very okay sha. For {time_context} in {region_context}, "
                f"it's {positive_sentiment}. The practical benefits are clear when you use it. "
                f"Value for money? Absolutely. Bottom line: {recommendation}."
            )
        
        # formal_english - clean, professional, no jargon
        return (
            f"After using {item_name}, I found it to be {positive_sentiment}. "
            f"In {time_context} conditions in {region_context}, the functionality held up well. "
            f"The overall experience met my expectations. "
            f"In summary, this is {recommendation}."
        )