from fastapi.testclient import TestClient
from api.main import app


def test_ingest_accepts_and_anonymizes():
    client = TestClient(app)
    payload = {
        "user_token": "user123",
        "signal": {
            "event_type": "click",
            "item_token": "item-abc",
            "item_category": "books",
            "session_context": {"email": "user@example.com"},
            "engagement_depth": 0.5,
            "dwell_time_seconds": 10,
            "sequence_position": 1,
        },
    }

    resp = client.post("/v1/ingest", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "accepted"
    assert data["privacy_mode"] == "hash-and-redact"
    assert data["user_token"].startswith("user_")
    assert "item_token" in data["stored_signal"]
    assert data["acknowledged_at"] > 0
