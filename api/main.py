import os
import time
from hashlib import sha256
from typing import Any, Dict, Mapping

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from memory.memory_manager import MemoryManager

app = FastAPI(title="ARCHE API (hackathon)", version="0.1.0")


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
        payload = signal.dict(exclude_none=True)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
