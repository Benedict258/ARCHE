from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _health_request_count(metrics_text: str) -> float:
    for line in metrics_text.splitlines():
        if line.startswith("arche_http_requests_total") and 'path="/v1/health"' in line and 'status="200"' in line:
            return float(line.rsplit(" ", 1)[-1])
    return 0.0


def test_metrics_endpoint_exposes_prometheus_format():
    client.get("/v1/health")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    assert "arche_http_requests_total" in resp.text


def test_metrics_counter_increments_across_requests():
    before = _health_request_count(client.get("/metrics").text)
    client.get("/v1/health")
    after = _health_request_count(client.get("/metrics").text)
    assert after == before + 1


def test_response_carries_request_id_header():
    resp = client.get("/v1/health")
    assert resp.headers.get("x-request-id")
