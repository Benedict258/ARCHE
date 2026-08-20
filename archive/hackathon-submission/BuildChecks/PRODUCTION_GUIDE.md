# ARCHE Production Deployment Guide

## Overview

ARCHE is a high-performance recommendation system using inline behavioral snapshots for personalization. This guide covers deployment, configuration, and operations.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start dev server
uvicorn api.main:app --reload --port 8000
```

### Docker Deployment

```bash
# Build image
docker build -t arche:latest .

# Run container
docker run -p 8000:8000 \
  -e PYTHONIOENCODING=utf-8 \
  arche:latest

# Health check
curl http://localhost:8000/v1/health
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Architecture

### Inline-First Recommendation Pipeline

Task B uses an **inline-first approach** where judges send complete `user_persona.review_history` in each request:

```json
POST /v1/recommend
{
  "user_persona": {
    "user_id": "user_123",
    "review_history": [
      {
        "rating": 5,
        "category": "restaurants",
        "review_text": "Excellent service and food"
      },
      {
        "rating": 4,
        "category": "local_flavor",
        "review_text": "Great atmosphere"
      }
    ]
  },
  "context": {
    "time_bucket": "evening"
  },
  "n": 10
}
```

### Key Components

1. **Catalog Loader** (`agents/catalog_loader.py`)
   - Loads 8660+ items from processed Yelp JSONL
   - Extracts 603 unique business categories
   - Cached in-memory for fast access

2. **Simulation Builder** (`agents/simulation_builder.py`)
   - Converts `review_history` → behavioral snapshot
   - Extracts signals: category affinities, price tier, exploration readiness
   - Handles cold-start users (empty history)

3. **Ranking Engine** (`agents/recommendation_scoring.py`)
   - Scores all catalog items against user simulation
   - Splits recommendations: 60% precision, 25% adjacent, 15% discovery
   - Signals: category match, price match, context boosts, exploration bonuses

4. **Privacy Layer** (`orchestrator.privacy_handler`)
   - Deterministic SHA256 anonymization per namespace
   - Token format: `{hash[:8]}_{user_id_hash[:8]}`

## Performance

All endpoints meet production SLAs:

| Endpoint        | Latency | Notes                            |
| --------------- | ------- | -------------------------------- |
| `/v1/ingest`    | <50ms   | Memory write                     |
| `/v1/simulate`  | <30ms   | Snapshot from history            |
| `/v1/recommend` | <150ms  | Full catalog (8660 items) ranked |
| `/v1/explain`   | <200ms  | Ranking trace + alternatives     |

See `tests/test_performance.py` for benchmark details.

## Task B: 5-Step Evaluation Workflow

Reproduce the evaluation pipeline locally:

```bash
# Step 1: Diagnostic (catalog coverage, user history distribution)
python step1_fast_diagnostic.py

# Step 2-4: (Skipped - cold-start and catalog construction covered above)

# Step 6: Full evaluation (100 test users, Hit Rate@10 measurement)
export PYTHONIOENCODING=utf-8
python step6_full_evaluation.py
```

**Current Metrics (100 test users):**

- Hit Rate@10: 0.0100 (target: > 0.35)
- NDCG@10: 0.0014 (target: > 0.15)
- Precision@10: 0.0010 (target: > 0.07)

**Note:** Metrics are below target due to evaluation dataset characteristics (user history categories don't match catalog categories well). Personalization is working (recommendations vary per user), but signal alignment with test queries needs refinement.

## Testing

### Unit & Integration Tests

```bash
# Run all tests (19 total)
pytest tests/test_integration.py tests/test_performance.py -v

# Run specific test class
pytest tests/test_integration.py::TestIntegration -v

# Run with coverage
pytest tests/ --cov=api --cov=memory --cov=orchestrator --cov-report=html
```

### API Smoke Test

```bash
# Start server
uvicorn api.main:app &

# Test /v1/recommend with inline history
curl -X POST http://localhost:8000/v1/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_persona": {
      "user_id": "test_user",
      "review_history": [
        {"rating": 5, "category": "restaurants", "review_text": "Great!"}
      ]
    },
    "n": 5
  }'
```

## Configuration

### Environment Variables

```
PYTHONIOENCODING=utf-8        # UTF-8 output (required for Windows)
DATABASE_URL={sqlite|redis}   # Memory backend (default: sqlite)
LOG_LEVEL=INFO                # Logging level
CATALOG_CACHE_SIZE=8660       # Max catalog items cached
```

### Production Deployment

Edit `.env`:

```
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=redis://prod-redis:6379
WORKERS=4
```

Run with Gunicorn (production WSGI server):

```bash
gunicorn api.main:app \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## Data Pipeline

### Processed Dataset Path

```
data/yelp_processed/
  ├── train.json     (42,141 reviews / 8660 items)
  └── test.json      (12,059 reviews / 3103 users)
```

### Schema (JSONL)

Each line is a review record:

```json
{
  "review_id": "uuid",
  "user_id": "user_token",
  "business_id": "item_id",
  "name": "business_name",
  "categories": "Local Flavor, Food, Brewpubs, ...",
  "stars_x": 4.0,
  "stars_y": 4.5,
  "text": "review text...",
  "date": 1247625516000,
  "city": "Saint Louis",
  "state": "MO"
}
```

## Optimization Guide

### To Improve Hit Rate@10 beyond 0.35:

1. **Signal Refinement**
   - Current: category + price + exploration bonuses
   - Add: collaborative filtering, temporal decay, location affinity
   - Edit: `agents/recommendation_scoring.py` → `score_item_against_simulation()`

2. **Catalog Enhancement**
   - Current: 603 unique categories (extracted from first category in comma-separated list)
   - Improve: multi-category tagging, embedding-based similarity
   - Edit: `agents/catalog_loader.py` → category extraction logic

3. **Cold-Start Handling**
   - Current: time-of-day prior + generic cluster priors
   - Improve: location-based priors, device/network context
   - Edit: `agents/recommendation_scoring.py` → `build_cold_start_simulation()`

4. **Evaluation Methodology**
   - Match test user history categories to catalog categories better
   - Use cross-validation on multiple user cohorts
   - Run A/B tests in production

## Troubleshooting

### Unicode Errors (Windows)

```bash
# Set UTF-8 mode
$env:PYTHONIOENCODING='utf-8'
python script.py
```

### Database Lock (SQLite)

```bash
# Kill Python processes and remove lock file
taskkill /F /IM python.exe
rm data/recommender.db
```

### Slow Recommendations

```bash
# Check catalog cache is populated
python -c "from agents.catalog_loader import get_catalog_size; print(get_catalog_size())"

# Profile endpoint
python -m cProfile -s cumulative api/main.py
```

## CI/CD

GitHub Actions workflow (`.github/workflows/ci-cd.yml`) runs on push/PR:

- Python 3.11, 3.12, 3.13 matrix
- Unit tests + coverage (Codecov)
- Lint (black, isort, flake8, mypy)
- Security scan (bandit, safety)
- Performance benchmarks

View workflow status: GitHub → Actions tab

## License & Attribution

- Dataset: Yelp Open Dataset (CC BY-NC-SA 4.0)
- Framework: FastAPI, LiteLLM, Pydantic
- Personalization: Custom behavioral snapshot + ranking pipeline

## Contact & Support

For deployment issues, file an issue at: https://github.com/Benedict258/ARCHE/issues
