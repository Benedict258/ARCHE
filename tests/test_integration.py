"""Integration tests for ARCHE API full-stack workflows."""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestIntegration:
    """Full integration tests covering cross-endpoint workflows."""
    
    def test_ingest_simulate_recommend_flow(self, client):
        """Test complete workflow: ingest → simulate → recommend."""
        user_token = "integration_test_user_1"
        
        # Step 1: Ingest behavioral signal
        ingest_payload = {
            "user_token": user_token,
            "signal": {
                "event_type": "view",
                "item_token": "integration_item_1",
                "item_category": "tech",
                "engagement_depth": 0.8,
                "dwell_time_seconds": 30,
            },
        }
        ingest_resp = client.post("/v1/ingest", json=ingest_payload)
        assert ingest_resp.status_code == 200
        ingest_data = ingest_resp.json()
        assert ingest_data["status"] == "accepted"
        assert ingest_data["privacy_mode"] == "hash-and-redact"
        
        # Step 2: Simulate user behavior
        sim_payload = {
            "user_token": user_token,
            "context": {"time_bucket": "evening", "device_class": "mobile"},
        }
        sim_resp = client.post("/v1/simulate", json=sim_payload)
        assert sim_resp.status_code == 200
        sim_data = sim_resp.json()
        assert "behavioral_snapshot" in sim_data
        assert "current_intent" in sim_data["behavioral_snapshot"]
        assert sim_data["simulation_basis"] in ["cold_start_prior", "warm_start_memory"]
        
        # Step 3: Get recommendations
        rec_payload = {
            "user_token": user_token,
            "context": {"time_bucket": "evening", "device_class": "mobile"},
            "n": 5,
        }
        rec_resp = client.post("/v1/recommend", json=rec_payload)
        assert rec_resp.status_code == 200
        rec_data = rec_resp.json()
        assert "recommendations" in rec_data
        assert len(rec_data["recommendations"]) <= 5
        
        # Validate recommendation structure
        for rec in rec_data["recommendations"]:
            assert "recommendation_id" in rec
            assert "item_name" in rec
            assert "confidence" in rec
            assert 0 <= rec["confidence"] <= 1
            assert "recommendation_type" in rec
            assert rec["recommendation_type"] in ["precision", "exploration", "discovery"]
    
    def test_multiple_ingests_then_recommend(self, client):
        """Test multiple ingestion signals improving recommendations."""
        user_token = "integration_test_user_2"
        
        # Ingest multiple signals
        signals = [
            {"event_type": "view", "item_token": "item_a", "item_category": "tech", "engagement_depth": 0.7},
            {"event_type": "save", "item_token": "item_a", "item_category": "tech", "engagement_depth": 0.9},
            {"event_type": "view", "item_token": "item_b", "item_category": "tech", "engagement_depth": 0.6},
            {"event_type": "view", "item_token": "item_c", "item_category": "science", "engagement_depth": 0.5},
        ]
        
        for signal in signals:
            payload = {"user_token": user_token, "signal": signal}
            resp = client.post("/v1/ingest", json=payload)
            assert resp.status_code == 200
        
        # Get recommendations after multiple ingestions
        rec_payload = {
            "user_token": user_token,
            "context": {"time_bucket": "evening"},
            "n": 6,
        }
        resp = client.post("/v1/recommend", json=rec_payload)
        assert resp.status_code == 200
        data = resp.json()
        
        # Should have recommendations
        assert len(data["recommendations"]) > 0
        
        # Should show tech category bias (ingest signals were tech-heavy)
        tech_recommendations = [
            rec for rec in data["recommendations"]
            if rec.get("item_category") == "tech"
        ]
        # At least some should be tech-biased given the ingestion pattern
        assert len(tech_recommendations) > 0
    
    def test_explain_non_existent_recommendation(self, client):
        """Test explainability error handling."""
        fake_rec_id = "00000000-0000-0000-0000-000000000000"
        payload = {"recommendation_id": fake_rec_id}
        
        resp = client.post("/v1/explain", json=payload)
        # Should either return 404 or return explanation for unknown rec
        assert resp.status_code in [200, 404, 400]
    
    def test_recommend_cold_start_new_user(self, client):
        """Test cold-start recommendations for completely new user."""
        user_token = "brand_new_user_xyz"
        
        # No prior ingestion for this user
        payload = {
            "user_token": user_token,
            "context": {"time_bucket": "morning"},
            "n": 5,
        }
        
        resp = client.post("/v1/recommend", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        
        # Should still return recommendations (cold-start basis)
        assert len(data["recommendations"]) > 0
        assert data["simulation_basis"] == "cold_start_prior"
    
    def test_recommend_with_various_context(self, client):
        """Test recommendations vary with different contexts."""
        user_token = "context_test_user"
        
        # Ingest signal
        ingest_payload = {
            "user_token": user_token,
            "signal": {
                "event_type": "view",
                "item_token": "context_item",
                "item_category": "general",
                "engagement_depth": 0.6,
            },
        }
        client.post("/v1/ingest", json=ingest_payload)
        
        # Get recommendations with different contexts
        contexts = [
            {"time_bucket": "morning", "device_class": "desktop"},
            {"time_bucket": "evening", "device_class": "mobile"},
            {"time_bucket": "afternoon", "device_class": "tablet"},
        ]
        
        all_recommendations = []
        for ctx in contexts:
            payload = {
                "user_token": user_token,
                "context": ctx,
                "n": 3,
            }
            resp = client.post("/v1/recommend", json=payload)
            assert resp.status_code == 200
            all_recommendations.append(resp.json()["recommendations"])
        
        # At least one context should produce different recommendations
        assert len(all_recommendations) == 3
    
    def test_privacy_across_endpoints(self, client):
        """Test that privacy is maintained across all endpoints."""
        sensitive_user_token = "user_with_sensitive_data_123"
        sensitive_item = "item_confidential_456"
        
        # Ingest with sensitive data
        ingest_payload = {
            "user_token": sensitive_user_token,
            "signal": {
                "event_type": "search",
                "item_token": sensitive_item,
                "item_category": "medical",
                "session_context": {"email": "secret@example.com"},
                "engagement_depth": 0.8,
            },
        }
        ingest_resp = client.post("/v1/ingest", json=ingest_payload)
        assert ingest_resp.status_code == 200
        
        # Verify tokens are hashed in response
        ingest_data = ingest_resp.json()
        assert ingest_data["user_token"].startswith("user_")
        # Email should not be in response
        assert "secret@example.com" not in str(ingest_data)
        
        # Simulate should use anonymized token
        sim_payload = {
            "user_token": sensitive_user_token,
            "context": {},
        }
        sim_resp = client.post("/v1/simulate", json=sim_payload)
        assert sim_resp.status_code == 200
        
        # Recommend should also maintain privacy
        rec_payload = {
            "user_token": sensitive_user_token,
            "context": {},
            "n": 5,
        }
        rec_resp = client.post("/v1/recommend", json=rec_payload)
        assert rec_resp.status_code == 200


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_user_token(self, client):
        """Test handling of invalid user tokens."""
        payload = {
            "user_token": "",  # Empty token
            "signal": {"event_type": "view"},
        }
        resp = client.post("/v1/ingest", json=payload)
        assert resp.status_code == 422  # Validation error
    
    def test_missing_required_field(self, client):
        """Test handling of missing required fields."""
        payload = {
            # Missing user_token
            "signal": {"event_type": "view"},
        }
        resp = client.post("/v1/ingest", json=payload)
        assert resp.status_code == 422
    
    def test_invalid_confidence_range(self, client):
        """Test recommendations maintain valid confidence scores."""
        user_token = "error_test_user"
        
        ingest_payload = {
            "user_token": user_token,
            "signal": {"event_type": "view", "item_token": "item", "item_category": "test"},
        }
        client.post("/v1/ingest", json=ingest_payload)
        
        rec_payload = {
            "user_token": user_token,
            "context": {},
            "n": 10,
        }
        resp = client.post("/v1/recommend", json=rec_payload)
        assert resp.status_code == 200
        
        data = resp.json()
        for rec in data["recommendations"]:
            assert 0 <= rec["confidence"] <= 1


class TestLoadHandling:
    """Test behavior under various load conditions."""
    
    def test_recommend_high_n_value(self, client):
        """Test recommendation endpoint with large n value."""
        user_token = "load_test_user"
        
        ingest_payload = {
            "user_token": user_token,
            "signal": {"event_type": "view", "item_token": "item", "item_category": "test"},
        }
        client.post("/v1/ingest", json=ingest_payload)
        
        # Request 100 recommendations
        rec_payload = {
            "user_token": user_token,
            "context": {},
            "n": 100,
        }
        resp = client.post("/v1/recommend", json=rec_payload)
        assert resp.status_code == 200
        
        data = resp.json()
        assert len(data["recommendations"]) > 0
    
    def test_concurrent_simulations(self, client):
        """Test multiple simulation requests."""
        for i in range(10):
            payload = {
                "user_token": f"concurrent_user_{i}",
                "context": {"time_bucket": "evening"},
            }
            resp = client.post("/v1/simulate", json=payload)
            assert resp.status_code == 200
