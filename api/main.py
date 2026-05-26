import os
import time
import json
import logging
from pathlib import Path
from hashlib import sha256
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Mapping
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

_LOG_LEVEL = os.getenv("ARCHE_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

from memory.memory_manager import MemoryManager
from api.routes.task_a import router as task_a_router
from api.routes.task_b import router as task_b_router
from orchestrator import LangGraphStyleOrchestrator
from data.dataset_loader import UnifiedDatasetLoader
from agents.recommendation_scoring import build_simulation_from_history, get_simulation


@asynccontextmanager
async def _lifespan(_: FastAPI):
    _ensure_core_state()
    yield


app = FastAPI(title="ARCHE API (hackathon)", version="0.1.0", lifespan=_lifespan)

# Configure CORS origins via environment variable for deployment. If not set,
# default to allowing all origins for demo purposes. In production, set
# `ALLOWED_ORIGINS` to a comma-separated list of allowed origins.
allowed = os.getenv("ALLOWED_ORIGINS")
if allowed:
    origins = [o.strip() for o in allowed.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(task_a_router)
app.include_router(task_b_router)


def _route_index() -> dict[str, str]:
    return {
        "root": "/",
        "health": "/v1/health",
        "healthz": "/healthz",
        "datasets_status": "/v1/datasets/status",
        "ingest": "/v1/ingest",
        "simulate": "/v1/simulate",
        "simulate_review": "/v1/simulate-review",
        "recommend": "/v1/recommend",
        "explain": "/v1/explain",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


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
    signal: IngestSignal | None = None
    event_type: str | None = None
    item_token: str | None = None
    item_category: str | None = None
    session_context: Dict[str, Any] = Field(default_factory=dict)
    engagement_depth: float | None = None
    dwell_time_seconds: int | None = None
    sequence_position: int | None = None


class IngestResponse(BaseModel):
    status: str
    privacy_mode: str
    user_token: str
    stored_signal: Dict[str, Any]
    acknowledged_at: int


class SimulateRequest(BaseModel):
    user_token: str = Field(min_length=1)
    review_history: list[dict[str, Any]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)


class SimulateContext(BaseModel):
    time_bucket: str | None = None
    day_type: str | None = None
    device_class: str | None = None
    network_quality: str | None = None
    region_tier: str | None = None
    session_depth: int | None = None
    entry_point: str | None = None


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
    context: Dict[str, Any] = Field(default_factory=dict)
    n: int = 10


class Recommendation(BaseModel):
    recommendation_id: str
    item_id: str | None = None
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


def _ensure_core_state() -> None:
    if not hasattr(app.state, "memory_manager"):
        app.state.memory_manager = MemoryManager()
    if not hasattr(app.state, "privacy"):
        app.state.privacy = PrivacyAbstraction()


def _ensure_app_state() -> None:
    _ensure_core_state()
    if not hasattr(app.state, "dataset_loader"):
        app.state.dataset_loader = UnifiedDatasetLoader()
    if not hasattr(app.state, "agent_graph"):
        app.state.agent_graph = LangGraphStyleOrchestrator(
            memory_manager=app.state.memory_manager,
            privacy=app.state.privacy,
            dataset_loader=app.state.dataset_loader,
        )


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


def _build_simulation_response(user_token: str, context: Dict[str, Any], memory_payload: Dict[str, Any]) -> SimulationResponse:
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
        entry_point = _normalize_value(context.entry_point, "new_user")
        if entry_point in {"amazon", "shopping", "store"}:
            top_affinities = ["shopping", "beauty", "accessories"]
            preference_cluster = "shopping"
        elif entry_point in {"goodreads", "books", "reading"}:
            top_affinities = ["books", "fiction", "literature"]
            preference_cluster = "books"
        elif entry_point in {"yelp", "restaurant", "food"}:
            top_affinities = ["restaurant", "food", "local"]
            preference_cluster = "restaurant"
        else:
            top_affinities = [entry_point, "exploration", "general_interest"]
            preference_cluster = entry_point
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


def _simulation_dict_to_response(user_token: str, context: Dict[str, Any], simulation: Dict[str, Any]) -> SimulationResponse:
    modifiers = simulation.get("context_modifiers") or {}
    return SimulationResponse(
        user_token=user_token,
        simulated_at=datetime.now(timezone.utc),
        behavioral_snapshot=BehavioralSnapshot(
            current_intent=str(simulation.get("current_intent") or "exploratory_browsing"),
            preference_cluster=str(simulation.get("preference_cluster") or "value_conscious"),
            top_affinities=list(simulation.get("top_affinities") or ["general"]),
            rejection_signals=list(simulation.get("rejection_signals") or []),
            engagement_mode=str(simulation.get("engagement_mode") or "scanning"),
            exploration_readiness=float(simulation.get("exploration_readiness") or 0.5),
            purchase_probability=float(simulation.get("purchase_probability") or 0.3),
        ),
        context_modifiers=ContextModifiers(
            time_boosts=list(modifiers.get("time_boosts") or []),
            suppressed_categories=list(modifiers.get("suppressed_categories") or []),
            active_context=str(
                modifiers.get("active_context")
                or f"{_normalize_value(context.get('time_of_day') or context.get('time_bucket'), 'evening')}_session"
            ),
        ),
        cold_start_confidence=float(simulation.get("cold_start_confidence") or 0.4),
        simulation_basis=str(simulation.get("simulation_basis") or ("cold_start_prior" if simulation.get("cold_start_used") else "historical_memory")),
        memory_sources=list(simulation.get("memory_sources") or ([] if simulation.get("cold_start_used") else ["behavioral_history"])),
    )


@app.get("/v1/health")
async def health():
    return {"status": "ok"}


@app.get("/v1/ingest")
async def ingest_help():
    return {
        "method": "POST",
        "endpoint": "/v1/ingest",
        "hint": "Send a JSON body with user_token and signal or event fields.",
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/api/health")
async def api_health():
    return {"status": "ok"}


@app.get("/api/healthz")
async def api_healthz():
    return {"status": "ok"}


@app.get("/api/v1/health")
async def api_v1_health():
    return {"status": "ok"}


@app.get("/api/v1/healthz")
async def api_v1_healthz():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {
        "name": "ARCHE API",
        "status": "ok",
        "routes": _route_index(),
    }


@app.get("/api/")
async def api_root():
    return {
        "name": "ARCHE API",
        "status": "ok",
        "routes": _route_index(),
    }


@app.get("/api/docs")
async def api_docs():
    return {"docs": "/docs", "openapi": "/openapi.json"}


@app.get("/api/openapi.json")
async def api_openapi():
    return app.openapi()


@app.get("/v1/datasets/status")
async def dataset_status():
    _ensure_core_state()
    if not hasattr(app.state, "dataset_loader"):
        app.state.dataset_loader = UnifiedDatasetLoader()
    loader: UnifiedDatasetLoader = app.state.dataset_loader
    catalog = loader.load_catalog(limit_per_source=5)
    return {
        "has_real_datasets": loader.has_real_datasets(),
        "catalog_size": len(catalog),
        "sources": sorted({item.get("source", "unknown") for item in catalog}),
    }


@app.get("/v1/simulate")
async def simulate_help():
    return {
        "method": "POST",
        "endpoint": "/v1/simulate",
        "hint": "Send user_token, review_history, and context as JSON.",
    }


@app.get("/api/v1/datasets/status")
async def api_dataset_status():
    return await dataset_status()


@app.post("/v1/ingest", response_model=IngestResponse)
async def ingest(payload: IngestRequest, request: Request):
    _ensure_core_state()
    privacy: PrivacyAbstraction = request.app.state.privacy
    memory_manager: MemoryManager = request.app.state.memory_manager

    anonymized_user_token = privacy.anonymize_token(payload.user_token, "user")
    if payload.signal is not None:
        signal = payload.signal
    else:
        signal = IngestSignal(
            event_type=payload.event_type or "view",
            item_token=payload.item_token,
            item_category=payload.item_category,
            session_context=payload.session_context,
            engagement_depth=payload.engagement_depth,
            dwell_time_seconds=payload.dwell_time_seconds,
            sequence_position=payload.sequence_position,
        )
    stored_signal = privacy.sanitize_signal(signal)
    memory_manager.update(anonymized_user_token or "", stored_signal)

    return IngestResponse(
        status="accepted",
        privacy_mode="hash-and-redact",
        user_token=anonymized_user_token or "",
        stored_signal=stored_signal,
        acknowledged_at=int(time.time()),
    )


@app.post("/api/v1/ingest", response_model=IngestResponse)
async def api_ingest(payload: IngestRequest, request: Request):
    return await ingest(payload, request)


@app.post("/v1/simulate", response_model=SimulationResponse)
async def simulate(payload: SimulateRequest, request: Request):
    _ensure_app_state()
    privacy: PrivacyAbstraction = request.app.state.privacy
    anonymized_token = privacy.anonymize_token(payload.user_token, "user")
    simulation = get_simulation(
        user_history_inline=payload.review_history,
        user_token=anonymized_token or payload.user_token,
        context=payload.context,
        memory_manager=request.app.state.memory_manager,
    )
    return _simulation_dict_to_response(payload.user_token, payload.context, simulation)


@app.post("/api/v1/simulate", response_model=SimulationResponse)
async def api_simulate(payload: SimulateRequest, request: Request):
    return await simulate(payload, request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
