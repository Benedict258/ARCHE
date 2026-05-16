from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_simulate_cold_start_returns_valid_shape():
    resp = client.post(
        "/v1/simulate",
        json={
            "user_token": "new-user",
            "context": {
                "time_bucket": "evening",
                "day_type": "weekday",
                "device_class": "mobile",
                "network_quality": "medium",
                "region_tier": "urban",
                "session_depth": 1,
                "entry_point": "search",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_token"] == "new-user"
    assert data["simulation_basis"] == "cold_start_prior"
    assert "behavioral_snapshot" in data
    assert "context_modifiers" in data
    assert data["behavioral_snapshot"]["current_intent"] in {"exploratory_browsing", "active_purchase", "research", "entertainment"}


def test_simulate_uses_memory_history_after_ingest():
    client.post(
        "/v1/ingest",
        json={
            "user_token": "sim-user",
            "signal": {
                "event_type": "click",
                "item_token": "item-abc",
                "item_category": "books",
                "session_context": {"region": "lagos"},
                "engagement_depth": 0.7,
                "dwell_time_seconds": 12,
                "sequence_position": 1,
            },
        },
    )

    resp = client.post(
        "/v1/simulate",
        json={
            "user_token": "sim-user",
            "context": {
                "time_bucket": "night",
                "day_type": "weekday",
                "device_class": "desktop",
                "network_quality": "high",
                "region_tier": "urban",
                "session_depth": 3,
                "entry_point": "direct",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["simulation_basis"] == "historical_memory:1"
    assert data["cold_start_confidence"] >= 0.8
    assert data["behavioral_snapshot"]["top_affinities"][0] == "books"
