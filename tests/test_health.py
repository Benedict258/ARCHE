from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_is_pure_liveness_no_dependency_check():
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_ok_when_mongo_reachable():
    resp = client.get("/v1/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["mongo"] is True
    assert "llm_configured" in data
    assert "embeddings_configured" in data
    assert "live_search_configured" in data


def test_readyz_alias_matches_ready():
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json()["mongo"] is True


class _FakeAdmin:
    async def command(self, *args, **kwargs):
        raise RuntimeError("mongo unreachable")


class _FakeClient:
    admin = _FakeAdmin()


def test_ready_returns_503_when_mongo_unreachable(monkeypatch):
    memory_manager = app.state.memory_manager
    monkeypatch.setattr(memory_manager, "client", _FakeClient())

    resp = client.get("/v1/ready")
    assert resp.status_code == 503
    assert resp.json()["mongo"] is False
