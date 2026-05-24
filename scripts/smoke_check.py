from fastapi.testclient import TestClient
from api.main import app
client=TestClient(app)
print('health ->', client.get('/v1/health').json())
# small simulate-review payload
payload = {
  "user_token": "emeka_001",
  "user_history": [
    {"item_name": "Chicken Republic Lekki", "item_category": "Fast Food", "rating": 4, "review_text": "Jollof rice was fire but service was slow sha"},
    {"item_name": "KFC Marina", "item_category": "Fast Food", "rating": 3, "review_text": "Consistent but overpriced for what you get"}
  ],
  "item": {"name": "Domino's Pizza Lagos", "category": "Fast Food", "price_tier": "mid", "attributes": {"cuisine": "Western", "delivery": True}},
  "context": {"time_bucket": "evening", "region": "Lagos Mainland"}
}
resp = client.post('/v1/simulate-review', json=payload)
print('simulate-review ->', resp.status_code)
print(resp.json())
# recommend
rec_payload = {"user_token": "emeka_001", "context": {"time_bucket":"evening","entry_point":"yelp","region_tier":"lagos_mainland"}, "n": 5}
rec = client.post('/v1/recommend', json=rec_payload)
print('recommend ->', rec.status_code)
print(rec.json())
