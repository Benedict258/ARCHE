from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_simulate_review_returns_valid_shape():
    payload = {
        "user_token": "task_a_user",
        "user_history": [
            {
                "item_name": "Chicken Republic Jollof",
                "item_category": "fast_food",
                "rating": 4,
                "review_text": "The rice was solid sha, but the waiting time was a bit much.",
            },
            {
                "item_name": "KFC Burger",
                "item_category": "fast_food",
                "rating": 3,
                "review_text": "It was very okay, nothing too special, but the value was fair.",
            },
        ],
        "item": {
            "name": "Domino's Pizza Lagos",
            "category": "fast_food",
            "price_tier": "mid",
            "attributes": {"delivery": "hot"},
        },
        "context": {
            "time_bucket": "evening",
            "region": "Lagos",
        },
    }

    resp = client.post("/v1/simulate-review", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data["predicted_rating"], int)
    assert 1 <= data["predicted_rating"] <= 5
    assert isinstance(data["generated_review"], str)
    assert data["generated_review"]
    assert 0.0 <= data["tone_confidence"] <= 1.0
    assert isinstance(data["behavioural_basis"], str)
    assert "simulation basis" in data["behavioural_basis"].lower()
