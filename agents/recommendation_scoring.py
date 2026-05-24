from __future__ import annotations

from typing import Any
import json
import re


DEFAULT_POPULATION_CLUSTERS: dict[str, list[str]] = {
    "value_conscious": ["food", "fast_food", "retail"],
    "quality_first": ["fine_dining", "premium", "electronics"],
    "experience_seeker": ["entertainment", "travel", "unique"],
    "practical": ["convenience", "delivery", "everyday"],
    "social": ["group_dining", "bars", "events"],
}


def detect_register_from_text(text: str) -> str:
    """Detect Nigerian language register from review text."""
    text_lower = text.lower()
    pidgin_markers = [
        "abeg", "na im", "e be like", "no be",
        "wetin", "oga", "wahala",
    ]
    mixed_markers = [
        "sha", "abi", "sef", "jare", "nau",
    ]
    nigerian_markers = [
        "very okay", "too much", "jollof",
        "suya", "pepper soup", "naija",
    ]

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


def _assign_cluster(affinities: list[str]) -> str:
    """Map top affinities to a behavioral cluster."""
    affinity_text = " ".join(str(a) for a in affinities).lower()
    if any(w in affinity_text for w in ["food", "restaurant", "fast_food", "dining"]):
        return "food_enthusiast"
    if any(w in affinity_text for w in ["book", "fiction", "literature", "reading"]):
        return "knowledge_seeker"
    if any(w in affinity_text for w in ["electronic", "tech", "gadget", "software"]):
        return "tech_focused"
    if any(w in affinity_text for w in ["fashion", "clothing", "beauty", "style"]):
        return "style_conscious"
    return "value_conscious"


def build_cold_start_simulation(context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Only called when review history is empty."""
    context = context or {}
    time_bucket = str(context.get("time_of_day") or context.get("time_bucket") or "evening").lower()
    region = str(context.get("region") or context.get("location_tier") or context.get("region_tier") or "urban").lower()
    occasion = str(context.get("occasion") or "general").lower()

    time_boosts = {
        "morning": ["breakfast", "coffee", "practical"],
        "afternoon": ["lunch", "cafe", "general"],
        "evening": ["dinner", "food", "entertainment"],
        "night": ["entertainment", "delivery", "social"],
    }

    return {
        "current_intent": "exploratory_browsing",
        "preference_cluster": "value_conscious",
        "top_affinities": time_boosts.get(time_bucket, ["food", "general"]),
        "rejection_signals": [],
        "preferred_price_tier": "mid",
        "exploration_readiness": 0.75,
        "purchase_probability": 0.30,
        "engagement_mode": "scanning",
        "writing_register": "formal_english",
        "recent_categories": [],
        "history_depth": 0,
        "recent_item_terms": [],
        "context_modifiers": {
            "time_boosts": time_boosts.get(time_bucket, []),
            "suppressed_categories": [],
            "active_context": f"{time_bucket}_cold_start",
        },
        "cold_start_used": True,
        "cold_start_confidence": 0.40,
        "simulation_basis": "cold_start_prior",
        "memory_sources": ["context_signal", "cohort_prior"],
        "region": region,
        "occasion": occasion,
    }


def build_simulation_from_history(review_history: list[dict[str, Any]], context: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Build behavioral snapshot from inline review history.
    This is the PRIMARY simulation path.
    Called directly from /v1/simulate and /v1/recommend.
    Does NOT require prior /v1/ingest call.
    Does NOT touch the database for history lookup.
    History arrives inline in the request.
    """

    context = context or {}

    # ── COLD START ────────────────────────────────────────
    if not review_history or len(review_history) == 0:
        return build_cold_start_simulation(context)

    # ── EXTRACT BEHAVIORAL SIGNALS FROM HISTORY ───────────

    # 1. Category affinities — what categories user rated 4+
    high_rated = [r for r in review_history if int(r.get("rating", 3)) >= 4]
    low_rated = [r for r in review_history if int(r.get("rating", 3)) <= 2]

    top_affinities = list(dict.fromkeys([
        str(r.get("category", r.get("item_category", "general")))
        for r in high_rated
        if str(r.get("category", r.get("item_category", "general"))).strip()
    ]))[:5]

    rejection_signals = list(dict.fromkeys([
        str(r.get("category", r.get("item_category", "general")))
        for r in low_rated
        if str(r.get("category", r.get("item_category", "general"))).strip()
    ]))[:3]

    # 2. Price tier preference — most common tier in high-rated
    price_tiers = [str(r.get("price_tier", "mid")) for r in high_rated]
    preferred_price = max(set(price_tiers), key=price_tiers.count) if price_tiers else "mid"

    # 3. Average rating — tells us how critical this user is
    avg_rating = sum(int(r.get("rating", 3)) for r in review_history) / len(review_history)

    # 4. Writing register detection
    all_review_text = " ".join([str(r.get("review_text", "")) for r in review_history])
    register = detect_register_from_text(all_review_text)

    # 5. Recent categories (last 3 reviews)
    recent = review_history[-3:] if len(review_history) >= 3 else review_history
    recent_categories = [str(r.get("category", r.get("item_category", ""))) for r in recent if str(r.get("category", r.get("item_category", ""))).strip()]

    # 6. Exploration readiness
    # Users with many reviews and varied categories = open to discovery
    unique_cats = len(set(str(r.get("category", r.get("item_category", ""))) for r in review_history if str(r.get("category", r.get("item_category", ""))).strip()))
    exploration_readiness = min(0.9, 0.3 + (unique_cats * 0.1))

    # 7. Intent detection from context
    time_bucket = str(context.get("time_of_day") or context.get("time_bucket") or "evening").lower()
    intent_map = {
        "morning": "practical",
        "afternoon": "exploratory_browsing",
        "evening": "active_purchase",
        "night": "entertainment",
    }
    current_intent = intent_map.get(time_bucket, "exploratory_browsing")

    # 8. Context time boosts
    time_boosts = {
        "morning": ["breakfast", "coffee", "bakery", "practical"],
        "afternoon": ["lunch", "cafe", "retail", "books"],
        "evening": ["dinner", "food", "entertainment", "social"],
        "night": ["entertainment", "bar", "late_night", "delivery"],
    }
    context_boosts = time_boosts.get(time_bucket, [])

    recent_item_terms: list[str] = []
    for row in review_history:
        recent_item_terms.extend(
            token for token in re.split(r"[^a-z0-9]+", str(row.get("review_text", "")).lower()) if len(token) >= 3
        )
    recent_item_terms = list(dict.fromkeys(recent_item_terms))

    # ── BUILD SNAPSHOT ────────────────────────────────────
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
        "recent_item_terms": recent_item_terms,
        "context_modifiers": {
            "time_boosts": context_boosts,
            "suppressed_categories": rejection_signals,
            "active_context": f"{time_bucket}_session",
        },
        "cold_start_used": False,
        "cold_start_confidence": 1.0,
        "simulation_basis": f"historical_memory:{len(review_history)}",
        "memory_sources": ["behavioral_history", "context_signal"],
    }

    return snapshot


def _history_from_memory_payload(memory_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not memory_payload:
        return []

    history: list[dict[str, Any]] = []
    for row in memory_payload.get("session") or []:
        if not isinstance(row, (list, tuple)) or len(row) < 9:
            continue
        session_context = row[5]
        if isinstance(session_context, str):
            try:
                session_context = json.loads(session_context)
            except Exception:
                session_context = {}
        history.append(
            {
                "event_type": row[2],
                "item_token": row[3],
                "category": row[4],
                "session_context": session_context if isinstance(session_context, dict) else {},
                "engagement_depth": row[6],
                "dwell_time_seconds": row[7],
                "sequence_position": row[8],
            }
        )
    return history


def get_simulation(
    *,
    user_history_inline: list[dict[str, Any]] | None,
    user_token: str,
    context: dict[str, Any] | None,
    memory_manager: Any | None = None,
) -> dict[str, Any]:
    """
    Priority order for simulation:
    1. Use inline history if provided (judges send this)
    2. Fall back to database history if no inline history
    3. Cold start if neither exists
    """
    if user_history_inline and len(user_history_inline) > 0:
        return build_simulation_from_history(user_history_inline, context)

    if memory_manager is not None:
        try:
            memory_payload = memory_manager.retrieve_all(user_token)
        except Exception:
            memory_payload = {}
        db_history = _history_from_memory_payload(memory_payload)
        if db_history:
            return build_simulation_from_history(db_history, context)

    return build_cold_start_simulation(context)


def handle_cold_start_simulation(
    user_history: list[dict[str, Any]],
    context: dict[str, Any],
    population_clusters: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Build a simulation-style snapshot for users with fewer than 3 reviews.

    This uses context plus weak behavioral priors instead of generic popularity.
    The returned payload is compatible with the recommendation ranker helpers.
    """
    clusters = population_clusters or DEFAULT_POPULATION_CLUSTERS

    time_bucket = str(context.get("time_of_day") or context.get("time_bucket") or "evening").lower()
    region = str(context.get("region") or context.get("location_tier") or context.get("region_tier") or "urban").lower()
    occasion = str(context.get("occasion") or "general").lower()

    known_cats = list(
        dict.fromkeys(
            str(r.get("category") or r.get("item_category") or "").strip().lower()
            for r in user_history
            if float(r.get("rating") or 3) >= 4 and str(r.get("category") or r.get("item_category") or "").strip()
        )
    )

    if known_cats:
        cluster_name = "value_conscious"
        for name, cats in clusters.items():
            if any(any(kw in cat for kw in cats) for cat in known_cats):
                cluster_name = name
                break
    else:
        time_clusters = {
            "morning": "practical",
            "afternoon": "value_conscious",
            "evening": "social",
            "night": "experience_seeker",
        }
        cluster_name = time_clusters.get(time_bucket, "value_conscious")

    cluster_affinities = clusters.get(cluster_name, ["food", "retail"])

    return {
        "current_intent": "exploratory_browsing",
        "preference_cluster": cluster_name,
        "top_affinities": cluster_affinities + known_cats,
        "rejection_signals": [],
        "exploration_readiness": 0.70,
        "preferred_price_tier": "mid",
        "context_modifiers": {
            "time_boosts": [cluster_affinities[0], cluster_affinities[1] if len(cluster_affinities) > 1 else cluster_affinities[0]],
            "active_context": f"{time_bucket}, {region}, {occasion}",
        },
        "cold_start_used": True,
        "cold_start_confidence": min(0.95, 0.45 + (len(user_history) * 0.10)),
        "recent_categories": known_cats,
        "behavioral_snapshot": {
            "current_intent": "exploratory_browsing",
            "preference_cluster": cluster_name,
            "top_affinities": cluster_affinities + known_cats,
            "rejection_signals": [],
            "engagement_mode": "scanning",
            "exploration_readiness": 0.70,
            "purchase_probability": 0.25,
        },
        "simulation_basis": "cold_start_prior",
    }


def _extract_snapshot(simulation: dict[str, Any] | Any) -> dict[str, Any]:
    if simulation is None:
        return {}
    if isinstance(simulation, dict):
        snapshot = simulation.get("behavioral_snapshot")
        if isinstance(snapshot, dict):
            return snapshot
        return simulation
    snapshot = getattr(simulation, "behavioral_snapshot", None)
    if hasattr(snapshot, "model_dump"):
        return snapshot.model_dump()
    if isinstance(snapshot, dict):
        return snapshot
    return {}


def _extract_modifiers(simulation: dict[str, Any] | Any) -> dict[str, Any]:
    if simulation is None:
        return {}
    if isinstance(simulation, dict):
        modifiers = simulation.get("context_modifiers")
        return modifiers if isinstance(modifiers, dict) else {}
    modifiers = getattr(simulation, "context_modifiers", None)
    if hasattr(modifiers, "model_dump"):
        return modifiers.model_dump()
    if isinstance(modifiers, dict):
        return modifiers
    return {}


def _tokenize_text(value: Any) -> set[str]:
    text = str(value or "").lower()
    tokens = {token for token in re.split(r"[^a-z0-9]+", text) if len(token) >= 3}
    return tokens


def score_item_against_simulation(item: dict[str, Any], simulation: dict[str, Any]) -> float:
    score = 0.0
    snapshot = _extract_snapshot(simulation)
    modifiers = _extract_modifiers(simulation)

    top_affinities = snapshot.get("top_affinities", []) or []
    rejection_signals = snapshot.get("rejection_signals", []) or []
    exploration_ready = float(snapshot.get("exploration_readiness", 0.3) or 0.3)
    price_signal = str(snapshot.get("preferred_price_tier", "mid") or "mid").lower()
    context_boosts = modifiers.get("time_boosts", []) or []
    recent_item_terms = set()
    for value in simulation.get("recent_item_terms", []) or []:
        if isinstance(value, str):
            token = value.lower().strip()
            if token:
                recent_item_terms.add(token)
        else:
            recent_item_terms.update(_tokenize_text(value))

    item_cat = str(item.get("item_category", "") or "").lower()
    item_price = str(item.get("price_tier", "mid") or "mid").lower()
    item_terms = _tokenize_text(item.get("item_name")) | _tokenize_text(item.get("description"))

    # Category affinity — strongest signal
    for affinity in top_affinities:
        affinity_text = str(affinity).lower()
        if affinity_text in item_cat or item_cat in affinity_text:
            score += 0.40
            break

    # Rejection signal penalty
    for rejection in rejection_signals:
        if str(rejection).lower() in item_cat:
            score -= 0.30
            break

    # Price tier match
    if item_price == price_signal:
        score += 0.15

    # Context time boost
    for boost_cat in context_boosts:
        boost_text = str(boost_cat).lower()
        if boost_text in item_cat:
            score += 0.15
            break

    # Exploration bonus for novel items
    is_in_affinities = any(str(a).lower() in item_cat or item_cat in str(a).lower() for a in top_affinities)
    if not is_in_affinities and exploration_ready > 0.5:
        score += 0.10

    # Recency signal from history
    recent_cats = [str(c).lower() for c in (simulation.get("recent_categories", []) or [])]
    if item_cat in recent_cats:
        score += 0.10

    # Exact or near-exact text overlap with recent user history
    if recent_item_terms and item_terms:
        overlap = len(recent_item_terms & item_terms)
        if overlap:
            score += min(0.20, 0.05 * overlap)

    # Collaborative prior propagated from the evaluation pipeline or ranker
    collab_score = item.get("collaborative_score")
    try:
        if collab_score is not None:
            score += min(0.20, max(0.0, float(collab_score)) * 0.20)
    except (TypeError, ValueError):
        pass

    return max(0.0, score)


def rank_catalog_against_simulation(simulation: dict[str, Any], catalog: list[dict[str, Any]], n: int = 10) -> list[dict[str, Any]]:
    # Score every item
    scored: list[dict[str, Any]] = []
    for item in catalog:
        item_copy = item.copy()
        item_copy["_score"] = score_item_against_simulation(item, simulation)
        scored.append(item_copy)

    # Sort by score descending
    scored.sort(key=lambda x: x.get("_score", 0.0), reverse=True)

    # Apply 60/25/15 exploration split
    n = max(1, int(n))
    n_precision = int(n * 0.60)
    n_adjacent = int(n * 0.25)
    n_discovery = n - n_precision - n_adjacent

    snapshot = _extract_snapshot(simulation)
    top_affinities = snapshot.get("top_affinities", []) or []
    rejection_signals = snapshot.get("rejection_signals", []) or []

    precision_items = [
        i for i in scored
        if any(str(a).lower() in str(i.get("item_category", "")).lower() for a in top_affinities)
    ][:n_precision]

    adjacent_items = [
        i for i in scored
        if i not in precision_items
        and not any(str(r).lower() in str(i.get("item_category", "")).lower() for r in rejection_signals)
    ][:n_adjacent]

    discovery_items = [
        i for i in scored
        if i not in precision_items
        and i not in adjacent_items
    ][:n_discovery]

    final = precision_items + adjacent_items + discovery_items

    # Fill to n if any bucket was short
    used = {id(i) for i in final}
    remainder = [i for i in scored if id(i) not in used]
    while len(final) < n and remainder:
        final.append(remainder.pop(0))

    # Tag recommendation type
    for i, item in enumerate(final):
        if i < n_precision:
            item["recommendation_type"] = "precision"
        elif i < n_precision + n_adjacent:
            item["recommendation_type"] = "adjacent_exploration"
        else:
            item["recommendation_type"] = "discovery"

    return final[:n]
