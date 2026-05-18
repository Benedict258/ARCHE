import os
import time
import json
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
from typing import Any, Dict, Mapping
from uuid import uuid4

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from memory.memory_manager import MemoryManager
from api.routes.task_a import router as task_a_router

app = FastAPI(title="ARCHE API (hackathon)", version="0.1.0")
app.include_router(task_a_router)


class IngestSignal(BaseModel):
    event_type: str = Field(min_length=1)
    item_token: str | None = None
    item_category: str | None = None
    session_context: Dict[str, Any] = Field(default_factory=dict)
    engagement_depth: float | None = None
    dwell_time_seconds: int | None = None
    sequence_position: int | None = None


class IngestRequest(BaseModel):
    user_token: str = Field(min_length=1)
    signal: IngestSignal


class IngestResponse(BaseModel):
    status: str
    privacy_mode: str
    user_token: str
    stored_signal: Dict[str, Any]
    acknowledged_at: int


class SimulateContext(BaseModel):
    time_bucket: str | None = None
    day_type: str | None = None
    device_class: str | None = None
    network_quality: str | None = None
    region_tier: str | None = None
    session_depth: int | None = None
    entry_point: str | None = None


class SimulateRequest(BaseModel):
    user_token: str = Field(min_length=1)
    context: SimulateContext = Field(default_factory=SimulateContext)


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
    simulated_at: datetime
    behavioral_snapshot: BehavioralSnapshot
    context_modifiers: ContextModifiers
    cold_start_confidence: float
    simulation_basis: str
    memory_sources: list[str]


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


class ExplainRequest(BaseModel):
    user_token: str = Field(min_length=1)
    recommendation_id: str = Field(min_length=1)


class ExplainResponse(BaseModel):
    user_token: str
    recommendation_id: str
    simulation: SimulationResponse
    recommendation: Recommendation
    alternatives_considered: list[Recommendation]
    trace: str


class PrivacyAbstraction:
    """Deterministic privacy layer for demo ingestion.

    It preserves referential stability by hashing tokens while redacting
    sensitive fields inside nested session context payloads.
    """

    sensitive_key_fragments = (
        "token",
        "email",
        "phone",
        "address",
        "name",
        "ip",
        "wallet",
        "password",
        "secret",
        "ssn",
    )

    def __init__(self, salt: str | None = None):
        self.salt = salt or os.getenv("ARCHE_PRIVACY_SALT", "arche-demo-salt")

    def anonymize_token(self, token: str | None, namespace: str) -> str | None:
        if not token:
            return None
        digest = sha256(f"{self.salt}:{namespace}:{token}".encode("utf-8")).hexdigest()
        return f"{namespace}_{digest[:16]}"

    def sanitize_signal(self, signal: IngestSignal) -> Dict[str, Any]:
        payload = signal.model_dump(exclude_none=True)
        payload["item_token"] = self.anonymize_token(payload.get("item_token"), "item")
        payload["session_context"] = self._sanitize_value(payload.get("session_context") or {}, "session_context")
        return payload

    def _sanitize_value(self, value: Any, key_hint: str | None = None) -> Any:
        if isinstance(value, Mapping):
            return {key: self._sanitize_value(inner_value, key) for key, inner_value in value.items()}

        if isinstance(value, list):
            return [self._sanitize_value(item, key_hint) for item in value]

        if isinstance(value, tuple):
            return [self._sanitize_value(item, key_hint) for item in value]

        if key_hint and self._should_redact(key_hint):
            return self.anonymize_token(str(value), key_hint)

        return value

    def _should_redact(self, key: str) -> bool:
        lowered = key.lower()
        return any(fragment in lowered for fragment in self.sensitive_key_fragments)


def _ensure_app_state() -> None:
    if not hasattr(app.state, "memory_manager"):
        app.state.memory_manager = MemoryManager()
    if not hasattr(app.state, "privacy"):
        app.state.privacy = PrivacyAbstraction()


def _normalize_value(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _extract_signal_rows(memory_payload: Dict[str, Any]) -> list[Any]:
    session_rows = memory_payload.get("session") or []
    return [row for row in session_rows if isinstance(row, (list, tuple)) and len(row) >= 10]

def _row_category(row: Any) -> str | None:
    if isinstance(row, (list, tuple)) and len(row) >= 5:
        category = row[4]
        if isinstance(category, str) and category.strip():
            return category.strip()
    return None

def _row_event(row: Any) -> str | None:
    if isinstance(row, (list, tuple)) and len(row) >= 3:
        event = row[2]
        if isinstance(event, str) and event.strip():
            return event.strip()
    return None

def _weight_for_recency(index: int) -> float:
    # Newer rows are returned first from storage.
    return 1.0 / (1.0 + (index * 0.35))


def _build_simulation_response(user_token: str, context: SimulateContext, memory_payload: Dict[str, Any]) -> SimulationResponse:
    rows = _extract_signal_rows(memory_payload)
    categories: list[str] = []
    events: list[str] = []
    item_tokens: list[str] = []
    weighted_category_counts: Dict[str, float] = {}
    weighted_event_counts: Dict[str, float] = {}
    for index, row in enumerate(rows):
        event_type = _row_event(row)
        item_token = row[3]
        item_category = _row_category(row)
        weight = _weight_for_recency(index)
        if event_type:
            events.append(str(event_type))
            weighted_event_counts[event_type] = weighted_event_counts.get(event_type, 0.0) + weight
        if item_category:
            categories.append(str(item_category))
            weighted_category_counts[item_category] = weighted_category_counts.get(item_category, 0.0) + weight
        if item_token:
            item_tokens.append(str(item_token))

    category_counts: Dict[str, float] = weighted_category_counts or {}

    top_affinities = [category for category, _ in sorted(category_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:3]]
    if not top_affinities:
        top_affinities = ["general_interest"]

    current_intent = "exploratory_browsing"
    if any(event in {"purchase", "save"} for event in weighted_event_counts):
        current_intent = "active_purchase"
    elif len(events) >= 3 or (rows and sum(weighted_event_counts.values()) >= 2.0):
        current_intent = "research"

    engagement_mode = "scanning"
    if (context.session_depth or 0) >= 5 or any(event == "dwell" for event in weighted_event_counts):
        engagement_mode = "high_depth"
    elif any(event == "click" for event in weighted_event_counts):
        engagement_mode = "quick_check"

    active_context = ", ".join(
        [
            _normalize_value(context.time_bucket, "time-unknown"),
            _normalize_value(context.device_class, "device-unknown"),
            _normalize_value(context.entry_point, "entry-unknown"),
        ]
    )

    time_boosts = [context.time_bucket] if context.time_bucket else []
    if context.device_class:
        time_boosts.append(f"device:{context.device_class}")

    suppressed_categories = []
    if context.network_quality == "low":
        suppressed_categories.append("heavy_media")
    if context.entry_point == "notification":
        suppressed_categories.append("deep_research")

    if rows:
        purchase_events = sum(weighted_event_counts.get(event, 0.0) for event in ("purchase", "save"))
        affinity_strength = sum(category_counts.get(category, 0.0) for category in top_affinities)
        purchase_probability = min(0.95, 0.32 + (0.12 * purchase_events) + (0.06 * len(top_affinities)) + (0.03 * affinity_strength))
        exploration_readiness = min(0.95, 0.38 + (0.1 if context.entry_point in {"search", "social"} else 0.0) + (0.04 * len(top_affinities)) + (0.02 * affinity_strength))
        cold_start_confidence = 0.82
        simulation_basis = f"historical_memory:{len(rows)}"
        memory_sources = ["behavioral_history", "context_signal"]
        preference_cluster = top_affinities[0]
        rejection_signals = [f"low_fit:{category}" for category in suppressed_categories]
    else:
        purchase_probability = 0.25
        exploration_readiness = 0.7
        cold_start_confidence = 0.4
        simulation_basis = "cold_start_prior"
        memory_sources = ["context_signal", "cohort_prior"]
        preference_cluster = _normalize_value(context.entry_point, "new_user")
        rejection_signals = ["no_recent_history"]

    return SimulationResponse(
        user_token=user_token,
        simulated_at=datetime.now(timezone.utc),
        behavioral_snapshot=BehavioralSnapshot(
            current_intent=current_intent,
            preference_cluster=preference_cluster,
            top_affinities=top_affinities,
            rejection_signals=rejection_signals,
            engagement_mode=engagement_mode,
            exploration_readiness=round(exploration_readiness, 2),
            purchase_probability=round(purchase_probability, 2),
        ),
        context_modifiers=ContextModifiers(
            time_boosts=[boost for boost in time_boosts if boost],
            suppressed_categories=suppressed_categories,
            active_context=active_context,
        ),
        cold_start_confidence=round(cold_start_confidence, 2),
        simulation_basis=simulation_basis,
        memory_sources=memory_sources,
    )


@app.on_event("startup")
async def startup_event() -> None:
    _ensure_app_state()


@app.get("/v1/health")
async def health():
    return {"status": "ok"}


@app.post("/v1/ingest", response_model=IngestResponse)
async def ingest(payload: IngestRequest, request: Request):
    _ensure_app_state()
    privacy: PrivacyAbstraction = request.app.state.privacy
    memory_manager: MemoryManager = request.app.state.memory_manager

    anonymized_user_token = privacy.anonymize_token(payload.user_token, "user")
    stored_signal = privacy.sanitize_signal(payload.signal)
    memory_manager.update(anonymized_user_token or "", stored_signal)

    return IngestResponse(
        status="accepted",
        privacy_mode="hash-and-redact",
        user_token=anonymized_user_token or "",
        stored_signal=stored_signal,
        acknowledged_at=int(time.time()),
    )


@app.post("/v1/simulate", response_model=SimulationResponse)
async def simulate(payload: SimulateRequest, request: Request):
    _ensure_app_state()
    privacy: PrivacyAbstraction = request.app.state.privacy
    memory_manager: MemoryManager = request.app.state.memory_manager
    storage_token = privacy.anonymize_token(payload.user_token, "user") or payload.user_token
    memory_payload = memory_manager.retrieve_all(storage_token)
    return _build_simulation_response(payload.user_token, payload.context, memory_payload)


@app.post("/v1/recommend", response_model=RecommendationSet)
async def recommend(payload: RecommendRequest, request: Request):
    """Generate a balanced recommendation set using the simulation output.

    Pipeline: retrieve memory -> simulate -> generate precision/adjacent/discovery mixes.
    """
    _ensure_app_state()
    privacy: PrivacyAbstraction = request.app.state.privacy
    memory_manager: MemoryManager = request.app.state.memory_manager

    storage_token = privacy.anonymize_token(payload.user_token, "user") or payload.user_token
    memory_payload = memory_manager.retrieve_all(storage_token)
    simulation = _build_simulation_response(payload.user_token, payload.context, memory_payload)

    n = max(1, payload.n)
    precision_share = 0.68 if simulation.simulation_basis.startswith("historical_memory:") else 0.58
    if simulation.behavioral_snapshot.current_intent == "active_purchase":
        precision_share += 0.05
    if simulation.behavioral_snapshot.exploration_readiness < 0.5:
        precision_share += 0.05
    precision_share = min(0.82, precision_share)

    adjacent_share = 0.22
    if simulation.behavioral_snapshot.exploration_readiness >= 0.7:
        adjacent_share += 0.04
    adjacent_share = min(0.3, adjacent_share)

    n_precision = max(1, int(round(n * precision_share)))
    n_adjacent = max(0, int(round(n * adjacent_share)))
    if n_precision + n_adjacent > n:
        n_adjacent = max(0, n - n_precision)
    n_discovery = max(0, n - n_precision - n_adjacent)
    if n > 4 and n_discovery > 1 and simulation.behavioral_snapshot.exploration_readiness < 0.6:
        n_discovery = 1
        n_adjacent = max(0, n - n_precision - n_discovery)

    affinities = simulation.behavioral_snapshot.top_affinities or ["general_interest"]
    affinity_set = {aff.lower() for aff in affinities}

    def _candidate_score(entry: dict[str, str], priority: str) -> float:
        category = (entry.get("item_category") or "unknown").lower()
        item_name = (entry.get("item_name") or "").lower()
        score = 0.0
        if priority == "precision":
            if category in affinity_set:
                score += 3.0
            elif any(category == f"adjacent_to_{a}" for a in affinity_set):
                score += 1.5
            if simulation.behavioral_snapshot.current_intent == "active_purchase":
                score += 0.4
        elif priority == "adjacent_exploration":
            if category.startswith("adjacent_to_"):
                score += 2.0
            if any(a in category for a in affinity_set):
                score += 0.8
            score += 0.2 * simulation.behavioral_snapshot.exploration_readiness
        else:
            if category == "discovery":
                score += 2.5
            elif category not in affinity_set:
                score += 1.0
            score += 0.2 * simulation.cold_start_confidence
        if payload.context.entry_point == "search" and priority == "precision":
            score += 0.15
        if payload.context.device_class == "mobile" and category in {"fashion", "food", "social"}:
            score += 0.1
        if category in item_name:
            score += 0.05
        return score

    try:
        candidates = memory_manager.vector_store.query([0.0], top_k=50)
    except Exception:
        candidates = []

    seen_keys: set[str] = set()
    precision_items: list[dict[str, str]] = []
    adjacent_items: list[dict[str, str]] = []
    other_items: list[dict[str, str]] = []

    for key, meta in candidates:
        if key in seen_keys:
            continue
        seen_keys.add(key)
        cat = meta.get("item_category") if isinstance(meta, dict) else None
        item_name = key.split(":", 1)[-1] or f"item_{len(seen_keys)}"
        entry = {"key": key, "item_name": item_name, "item_category": cat or "unknown"}
        if isinstance(cat, str) and cat.lower() in affinity_set:
            precision_items.append(entry)
        elif isinstance(cat, str) and cat.lower().startswith("adjacent_to_"):
            adjacent_items.append(entry)
        else:
            other_items.append(entry)

    precision_items.sort(key=lambda entry: (-_candidate_score(entry, "precision"), entry["item_name"]))
    adjacent_items.sort(key=lambda entry: (-_candidate_score(entry, "adjacent_exploration"), entry["item_name"]))
    other_items.sort(key=lambda entry: (-_candidate_score(entry, "discovery"), entry["item_name"]))

    recommendations: list[Recommendation] = []

    for i in range(n_precision):
        if i < len(precision_items):
            it = precision_items[i]
            base_name = (it["item_category"] or affinities[i % len(affinities)]).replace("adjacent_to_", "")
            rec = Recommendation(
                recommendation_id=str(uuid4()),
                item_name=f"{base_name}_recommendation_{i+1}",
                item_category=it["item_category"],
                confidence=round(0.88 - (i * 0.015), 2),
                recommendation_type="precision",
                exploration_factor="Precision recommendation — within core preference cluster",
                explanation=(
                    f"Matched to simulated preference cluster '{simulation.behavioral_snapshot.preference_cluster}' "
                    f"with affinity '{it['item_category']}'. Context '{simulation.context_modifiers.active_context}' and basis {simulation.simulation_basis}."
                ),
            )
        else:
            affinity = affinities[i % len(affinities)]
            rec = Recommendation(
                recommendation_id=str(uuid4()),
                item_name=f"{affinity}_recommendation_{i+1}",
                item_category=affinity,
                confidence=round(0.88 - (i * 0.015), 2),
                recommendation_type="precision",
                exploration_factor="Precision recommendation — within core preference cluster",
                explanation=(
                    f"Matched to simulated preference cluster '{simulation.behavioral_snapshot.preference_cluster}' "
                    f"with affinity '{affinity}'. Context '{simulation.context_modifiers.active_context}' and basis {simulation.simulation_basis}."
                ),
            )
        recommendations.append(rec)

    for i in range(n_adjacent):
        if i < len(adjacent_items):
            it = adjacent_items[i]
            base_name = (it["item_category"] or affinities[i % len(affinities)]).replace("adjacent_to_", "")
            adjacent_name = f"adjacent_to_{base_name}_recommendation_{i+1}"
            rec = Recommendation(
                recommendation_id=str(uuid4()),
                item_name=adjacent_name,
                item_category=it["item_category"],
                confidence=round(0.68 - (i * 0.012), 2),
                recommendation_type="adjacent_exploration",
                exploration_factor="Adjacent exploration — similar but broader items",
                explanation=(
                    f"Exploration injection near user's affinities to broaden discovery. Simulation basis: {simulation.simulation_basis} and context {simulation.context_modifiers.active_context}."
                ),
            )
        elif i < len(other_items):
            it = other_items[i]
            rec = Recommendation(
                recommendation_id=str(uuid4()),
                item_name=it["item_name"],
                item_category=it["item_category"],
                confidence=round(0.64 - (i * 0.012), 2),
                recommendation_type="adjacent_exploration",
                exploration_factor="Adjacent exploration — similar but broader items",
                explanation=(
                    f"Exploration injection near user's affinities to broaden discovery. Simulation basis: {simulation.simulation_basis} and context {simulation.context_modifiers.active_context}."
                ),
            )
        else:
            base = affinities[i % len(affinities)]
            adj_cat = f"adjacent_to_{base}"
            rec = Recommendation(
                recommendation_id=str(uuid4()),
                item_name=f"{adj_cat}_rec_{i+1}",
                item_category=adj_cat,
                confidence=round(0.64 - (i * 0.012), 2),
                recommendation_type="adjacent_exploration",
                exploration_factor="Adjacent exploration — similar but broader items",
                explanation=(
                    f"Exploration injection near '{base}' to broaden discovery. Simulation basis: {simulation.simulation_basis} and context {simulation.context_modifiers.active_context}."
                ),
            )
        recommendations.append(rec)

    for i in range(n_discovery):
        if i < len(other_items):
            it = other_items[i]
            rec = Recommendation(
                recommendation_id=str(uuid4()),
                item_name=it["item_name"],
                item_category=it["item_category"],
                confidence=round(0.4 - (i * 0.01), 2),
                recommendation_type="discovery",
                exploration_factor="Discovery injection — novel item for serendipity",
                explanation=(
                    f"Deliberate discovery pick to maintain diversity. Simulation confidence: {simulation.cold_start_confidence} and context {simulation.context_modifiers.active_context}."
                ),
            )
        else:
            rec = Recommendation(
                recommendation_id=str(uuid4()),
                item_name=f"novel_discovery_{i+1}",
                item_category="discovery",
                confidence=round(0.4 - (i * 0.01), 2),
                recommendation_type="discovery",
                exploration_factor="Discovery injection — novel item for serendipity",
                explanation=(
                    f"Deliberate discovery pick to maintain diversity. Simulation confidence: {simulation.cold_start_confidence} and context {simulation.context_modifiers.active_context}."
                ),
            )
        recommendations.append(rec)

    try:
        out_path = Path("data/last_recommend.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out = {
            "user_token": payload.user_token,
            "simulation_basis": simulation.simulation_basis,
            "recommendations": [r.model_dump() for r in recommendations],
            "simulated_at": simulation.simulated_at.isoformat(),
        }
        out_path.write_text(json.dumps(out, ensure_ascii=False, default=str), encoding="utf-8")
    except Exception:
        pass

    return RecommendationSet(
        user_token=payload.user_token,
        simulation_basis=simulation.simulation_basis,
        recommendations=recommendations,
    )


@app.post("/v1/explain", response_model=ExplainResponse)
async def explain(payload: ExplainRequest, request: Request):
    from fastapi import HTTPException
    
    _ensure_app_state()
    privacy: PrivacyAbstraction = request.app.state.privacy
    storage_token = privacy.anonymize_token(payload.user_token, "user") or payload.user_token

    # load last persisted recommendations
    try:
        raw = Path("data/last_recommend.json").read_text(encoding="utf-8")
        doc = json.loads(raw)
    except Exception:
        doc = None

    if not doc or doc.get("user_token") != payload.user_token:
        # fallback: return minimal trace
        raise HTTPException(status_code=404, detail="No recent recommendations found for this user")

    recs = doc.get("recommendations") or []
    found = None
    for r in recs:
        if r.get("recommendation_id") == payload.recommendation_id:
            found = r
            break

    if not found:
        raise HTTPException(status_code=404, detail="Recommendation not found in last run")

    # Build a simple causal trace
    simulation = _build_simulation_response(payload.user_token, SimulateContext(**{}), {"session": [], "is_cold_start": True})
    alt_recs = [Recommendation(**r) for r in recs if r.get("recommendation_id") != payload.recommendation_id][:5]
    main_rec = Recommendation(**found)
    trace = (
        f"Recommendation {main_rec.recommendation_id} chosen because: {main_rec.explanation} "
        f"Alternatives considered: {[a.recommendation_id for a in alt_recs]}."
    )

    return ExplainResponse(
        user_token=payload.user_token,
        recommendation_id=payload.recommendation_id,
        simulation=simulation,
        recommendation=main_rec,
        alternatives_considered=alt_recs,
        trace=trace,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
