from typing import List, Dict, Any


def build_simulation_from_history(
    review_history: List[Dict[str, Any]],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    if not review_history or len(review_history) == 0:
        return build_cold_start_simulation(context)

    high_rated = [r for r in review_history if int(r.get("rating", 3)) >= 4]
    low_rated = [r for r in review_history if int(r.get("rating", 3)) <= 2]

    top_affinities = list(dict.fromkeys([
        r.get("category", r.get("item_category", "general"))
        for r in high_rated
    ]))[:5]

    rejection_signals = list(dict.fromkeys([
        r.get("category", r.get("item_category", "general"))
        for r in low_rated
    ]))[:3]

    price_tiers = [r.get("price_tier", "mid") for r in high_rated]
    preferred_price = (max(set(price_tiers), key=price_tiers.count) if price_tiers else "mid")

    avg_rating = sum(int(r.get("rating", 3)) for r in review_history) / len(review_history) if review_history else 3.0

    all_review_text = " ".join([str(r.get("review_text", "")) for r in review_history])
    register = detect_register_from_text(all_review_text)

    recent = review_history[-3:] if len(review_history) >= 3 else review_history
    recent_categories = [r.get("category", r.get("item_category", "")) for r in recent]

    unique_cats = len(set(r.get("category", "") for r in review_history))
    exploration_readiness = min(0.9, 0.3 + (unique_cats * 0.1))

    time_bucket = context.get("time_of_day", context.get("time_bucket", "evening"))
    intent_map = {"morning": "practical", "afternoon": "exploratory_browsing", "evening": "active_purchase", "night": "entertainment"}
    current_intent = intent_map.get(time_bucket, "exploratory_browsing")

    time_boosts = {"morning": ["breakfast", "coffee", "bakery", "practical"], "afternoon": ["lunch", "cafe", "retail", "books"], "evening": ["dinner", "food", "entertainment", "social"], "night": ["entertainment", "bar", "late_night", "delivery"]}
    context_boosts = time_boosts.get(time_bucket, [])

    snapshot = {
        "current_intent": current_intent,
        "preference_cluster": _assign_cluster(top_affinities),
        "top_affinities": top_affinities if top_affinities else ["general"],
        "rejection_signals": rejection_signals,
        "preferred_price_tier": preferred_price,
        "exploration_readiness": round(exploration_readiness, 2),
        "purchase_probability": round(min(0.9, avg_rating / 5.0), 2),
        "engagement_mode": "high_depth" if avg_rating >= 4.0 else "scanning",
        "writing_register": register,
        "recent_categories": recent_categories,
        "history_depth": len(review_history),
        "context_modifiers": {"time_boosts": context_boosts, "suppressed_categories": rejection_signals, "active_context": f"{time_bucket}_session"},
        "cold_start_used": False,
        "cold_start_confidence": 1.0,
    }

    return snapshot


def _assign_cluster(affinities: List[str]) -> str:
    affinity_text = " ".join(affinities).lower()
    if any(w in affinity_text for w in ["food", "restaurant", "fast_food", "dining"]):
        return "food_enthusiast"
    if any(w in affinity_text for w in ["book", "fiction", "literature", "reading"]):
        return "knowledge_seeker"
    if any(w in affinity_text for w in ["electronic", "tech", "gadget", "software"]):
        return "tech_focused"
    if any(w in affinity_text for w in ["fashion", "clothing", "beauty", "style"]):
        return "style_conscious"
    return "value_conscious"


def build_cold_start_simulation(context: Dict[str, Any]) -> Dict[str, Any]:
    time_bucket = context.get("time_of_day", context.get("time_bucket", "evening"))
    time_boosts = {"morning": ["breakfast", "coffee", "practical"], "afternoon": ["lunch", "cafe", "general"], "evening": ["dinner", "food", "entertainment"], "night": ["entertainment", "delivery", "social"]}
    return {"current_intent": "exploratory_browsing", "preference_cluster": "value_conscious", "top_affinities": time_boosts.get(time_bucket, ["food", "general"]), "rejection_signals": [], "preferred_price_tier": "mid", "exploration_readiness": 0.75, "purchase_probability": 0.30, "engagement_mode": "scanning", "writing_register": "formal_english", "recent_categories": [], "history_depth": 0, "context_modifiers": {"time_boosts": time_boosts.get(time_bucket, []), "suppressed_categories": [], "active_context": f"{time_bucket}_cold_start"}, "cold_start_used": True, "cold_start_confidence": 0.40}


def detect_register_from_text(text: str) -> str:
    text_lower = text.lower()
    pidgin_markers = ["abeg", "na im", "e be like", "no be", "wetin", "oga", "wahala"]
    mixed_markers = ["sha", "abi", "sef", "jare", "nau"]
    nigerian_markers = ["very okay", "too much", "jollof", "suya", "pepper soup", "naija"]

    pidgin_count = sum(1 for m in pidgin_markers if m in text_lower)
    mixed_count = sum(1 for m in mixed_markers if m in text_lower)
    nigerian_count = sum(1 for m in nigerian_markers if m in text_lower)

    if pidgin_count >= 2:
        return "casual_pidgin"
    if mixed_count >= 2:
        return "mixed_pidgin"
    if nigerian_count >= 1:
        return "nigerian_english"
    return "formal_english"


def get_simulation(user_history_inline: List[Dict[str, Any]], user_token: str, context: Dict[str, Any]) -> Dict[str, Any]:
    if user_history_inline and len(user_history_inline) > 0:
        return build_simulation_from_history(user_history_inline, context)
    return build_cold_start_simulation(context)
