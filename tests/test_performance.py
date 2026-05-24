"""Performance benchmarking tests for ARCHE API endpoints."""

import time
import statistics
from typing import List, Callable, Any, Dict
import pytest
from fastapi.testclient import TestClient
from api.main import app


class PerformanceMetrics:
    """Tracks and reports performance metrics."""
    
    def __init__(self, endpoint_name: str):
        self.endpoint_name = endpoint_name
        self.response_times: List[float] = []
        self.start_time: float | None = None
    
    def start(self):
        self.start_time = time.perf_counter()
    
    def end(self):
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.response_times.append(duration)
            return duration
        return None
    
    def summary(self) -> Dict[str, float]:
        if not self.response_times:
            return {}
        
        return {
            "endpoint": self.endpoint_name,
            "total_requests": len(self.response_times),
            "min_ms": min(self.response_times) * 1000,
            "max_ms": max(self.response_times) * 1000,
            "mean_ms": statistics.mean(self.response_times) * 1000,
            "median_ms": statistics.median(self.response_times) * 1000,
            "stdev_ms": statistics.stdev(self.response_times) * 1000 if len(self.response_times) > 1 else 0,
            "p95_ms": sorted(self.response_times)[int(0.95 * len(self.response_times))] * 1000,
            "p99_ms": sorted(self.response_times)[int(0.99 * len(self.response_times))] * 1000,
        }


@pytest.fixture
def client():
    return TestClient(app)


class TestIngestPerformance:
    """Performance tests for /v1/ingest endpoint."""
    
    def test_ingest_cold_start_latency(self, client):
        """Test first request latency (cold start)."""
        metrics = PerformanceMetrics("POST /v1/ingest (cold start)")
        
        payload = {
            "user_token": "perf_user_1",
            "signal": {
                "event_type": "view",
                "item_token": "item_perf_1",
                "item_category": "test_category",
                "engagement_depth": 0.5,
            },
        }
        
        metrics.start()
        resp = client.post("/v1/ingest", json=payload)
        metrics.end()
        
        assert resp.status_code == 200
        summary = metrics.summary()
        print(f"\n{summary['endpoint']}: {summary['mean_ms']:.2f}ms (cold start)")
        assert summary["mean_ms"] < 100, "Cold start should be < 100ms"
    
    def test_ingest_throughput(self, client):
        """Test throughput: 100 requests to /v1/ingest."""
        metrics = PerformanceMetrics("POST /v1/ingest (throughput)")
        
        for i in range(100):
            payload = {
                "user_token": f"perf_user_{i}",
                "signal": {
                    "event_type": "click",
                    "item_token": f"item_perf_{i}",
                    "item_category": "test",
                    "engagement_depth": 0.7,
                },
            }
            
            metrics.start()
            resp = client.post("/v1/ingest", json=payload)
            metrics.end()
            
            assert resp.status_code == 200
        
        summary = metrics.summary()
        print(f"\n{summary['endpoint']} (100 requests):")
        print(f"  Mean: {summary['mean_ms']:.2f}ms")
        print(f"  Median: {summary['median_ms']:.2f}ms")
        print(f"  P95: {summary['p95_ms']:.2f}ms")
        print(f"  P99: {summary['p99_ms']:.2f}ms")
        
        assert summary["mean_ms"] < 50, "Ingest mean should be < 50ms under load"


class TestSimulatePerformance:
    """Performance tests for /v1/simulate endpoint."""
    
    def test_simulate_cold_start_latency(self, client):
        """Test first request latency (cold start)."""
        # Pre-create some memory
        ingest_payload = {
            "user_token": "sim_user_1",
            "signal": {
                "event_type": "view",
                "item_token": "item_sim_1",
                "item_category": "test",
                "engagement_depth": 0.5,
            },
        }
        client.post("/v1/ingest", json=ingest_payload)
        
        metrics = PerformanceMetrics("POST /v1/simulate (cold start)")
        
        sim_payload = {
            "user_token": "sim_user_1",
            "context": {"time_bucket": "evening", "device_class": "mobile"},
        }
        
        metrics.start()
        resp = client.post("/v1/simulate", json=sim_payload)
        metrics.end()
        
        assert resp.status_code == 200
        summary = metrics.summary()
        print(f"\n{summary['endpoint']}: {summary['mean_ms']:.2f}ms (cold start)")
        assert summary["mean_ms"] < 200, "Simulate cold start should be < 200ms"
    
    def test_simulate_throughput(self, client):
        """Test throughput: 50 simulation requests."""
        # Pre-populate memory
        for i in range(20):
            payload = {
                "user_token": f"sim_user_{i}",
                "signal": {
                    "event_type": "view",
                    "item_token": f"item_sim_{i}",
                    "item_category": "test",
                    "engagement_depth": 0.6,
                },
            }
            client.post("/v1/ingest", json=payload)
        
        metrics = PerformanceMetrics("POST /v1/simulate (throughput)")
        
        for i in range(50):
            payload = {
                "user_token": f"sim_user_{i % 20}",
                "context": {"time_bucket": "evening", "device_class": "mobile"},
            }
            
            metrics.start()
            resp = client.post("/v1/simulate", json=payload)
            metrics.end()
            
            assert resp.status_code == 200
        
        summary = metrics.summary()
        print(f"\n{summary['endpoint']} (50 requests):")
        print(f"  Mean: {summary['mean_ms']:.2f}ms")
        print(f"  Median: {summary['median_ms']:.2f}ms")
        print(f"  P95: {summary['p95_ms']:.2f}ms")
        print(f"  P99: {summary['p99_ms']:.2f}ms")
        
        assert summary["mean_ms"] < 150, "Simulate mean should be < 150ms"


class TestRecommendPerformance:
    """Performance tests for /v1/recommend endpoint."""
    
    def test_recommend_cold_start_latency(self, client):
        """Test first request latency (cold start)."""
        # Pre-create memory
        ingest_payload = {
            "user_token": "rec_user_1",
            "signal": {
                "event_type": "view",
                "item_token": "item_rec_1",
                "item_category": "tech",
                "engagement_depth": 0.8,
            },
        }
        client.post("/v1/ingest", json=ingest_payload)
        
        metrics = PerformanceMetrics("POST /v1/recommend (cold start)")
        
        rec_payload = {
            "user_token": "rec_user_1",
            "context": {"time_bucket": "evening", "device_class": "mobile"},
            "n": 6,
        }
        
        metrics.start()
        resp = client.post("/v1/recommend", json=rec_payload)
        metrics.end()
        
        assert resp.status_code == 200
        summary = metrics.summary()
        print(f"\n{summary['endpoint']}: {summary['mean_ms']:.2f}ms (cold start)")
        assert summary["mean_ms"] < 250, "Recommend cold start should be < 250ms"
    
    def test_recommend_throughput(self, client):
        """Test throughput: 30 recommendation requests."""
        # Pre-populate memory
        for i in range(15):
            payload = {
                "user_token": f"rec_user_{i}",
                "signal": {
                    "event_type": "view",
                    "item_token": f"item_rec_{i}",
                    "item_category": "tech",
                    "engagement_depth": 0.7,
                },
            }
            client.post("/v1/ingest", json=payload)
        
        metrics = PerformanceMetrics("POST /v1/recommend (throughput)")
        
        for i in range(30):
            payload = {
                "user_token": f"rec_user_{i % 15}",
                "context": {"time_bucket": "evening", "device_class": "mobile"},
                "n": 6,
            }
            
            metrics.start()
            resp = client.post("/v1/recommend", json=payload)
            metrics.end()
            
            assert resp.status_code == 200
        
        summary = metrics.summary()
        print(f"\n{summary['endpoint']} (30 requests):")
        print(f"  Mean: {summary['mean_ms']:.2f}ms")
        print(f"  Median: {summary['median_ms']:.2f}ms")
        print(f"  P95: {summary['p95_ms']:.2f}ms")
        print(f"  P99: {summary['p99_ms']:.2f}ms")
        
        assert summary["mean_ms"] < 200, "Recommend mean should be < 200ms"


class TestExplainPerformance:
    """Performance tests for /v1/explain endpoint."""
    
    def test_explain_latency(self, client):
        """Test explanation latency."""
        # Get a recommendation first
        ingest_payload = {
            "user_token": "exp_user_1",
            "signal": {
                "event_type": "view",
                "item_token": "item_exp_1",
                "item_category": "books",
                "engagement_depth": 0.6,
            },
        }
        client.post("/v1/ingest", json=ingest_payload)
        
        rec_payload = {
            "user_token": "exp_user_1",
            "context": {"time_bucket": "evening"},
            "n": 1,
        }
        rec_resp = client.post("/v1/recommend", json=rec_payload)
        assert rec_resp.status_code == 200
        
        rec_data = rec_resp.json()
        rec_id = rec_data["recommendations"][0]["recommendation_id"]
        
        metrics = PerformanceMetrics("POST /v1/explain")
        
        explain_payload = {"recommendation_id": rec_id, "user_token": "exp_user_1"}
        
        metrics.start()
        resp = client.post("/v1/explain", json=explain_payload)
        metrics.end()
        
        assert resp.status_code == 200
        summary = metrics.summary()
        print(f"\n{summary['endpoint']}: {summary['mean_ms']:.2f}ms")
        assert summary["mean_ms"] < 200, "Explain should be < 200ms (includes catalog ranking)"


class TestEndToEndPerformance:
    """End-to-end pipeline performance test."""
    
    def test_full_pipeline_latency(self, client):
        """Test full ingest → simulate → recommend → explain pipeline."""
        print("\n=== Full Pipeline Performance Test ===")
        
        user_token = "e2e_user_1"
        
        # 1. Ingest
        ingest_time = time.perf_counter()
        ingest_payload = {
            "user_token": user_token,
            "signal": {
                "event_type": "view",
                "item_token": "item_e2e_1",
                "item_category": "tech",
                "engagement_depth": 0.8,
                "dwell_time_seconds": 30,
            },
        }
        resp = client.post("/v1/ingest", json=ingest_payload)
        ingest_duration = (time.perf_counter() - ingest_time) * 1000
        assert resp.status_code == 200
        print(f"  Ingest: {ingest_duration:.2f}ms")
        
        # 2. Simulate
        sim_time = time.perf_counter()
        sim_payload = {
            "user_token": user_token,
            "context": {"time_bucket": "evening", "device_class": "mobile"},
        }
        resp = client.post("/v1/simulate", json=sim_payload)
        sim_duration = (time.perf_counter() - sim_time) * 1000
        assert resp.status_code == 200
        print(f"  Simulate: {sim_duration:.2f}ms")
        
        # 3. Recommend
        rec_time = time.perf_counter()
        rec_payload = {
            "user_token": user_token,
            "context": {"time_bucket": "evening", "device_class": "mobile"},
            "n": 6,
        }
        resp = client.post("/v1/recommend", json=rec_payload)
        rec_duration = (time.perf_counter() - rec_time) * 1000
        assert resp.status_code == 200
        rec_data = resp.json()
        rec_id = rec_data["recommendations"][0]["recommendation_id"]
        print(f"  Recommend: {rec_duration:.2f}ms")
        
        # 4. Explain
        exp_time = time.perf_counter()
        exp_payload = {"recommendation_id": rec_id, "user_token": user_token}
        resp = client.post("/v1/explain", json=exp_payload)
        exp_duration = (time.perf_counter() - exp_time) * 1000
        assert resp.status_code == 200
        print(f"  Explain: {exp_duration:.2f}ms")
        
        # Total
        total = ingest_duration + sim_duration + rec_duration + exp_duration
        print(f"  Total Pipeline: {total:.2f}ms")
        
        assert total < 1000, "Full pipeline should complete in < 1 second"
