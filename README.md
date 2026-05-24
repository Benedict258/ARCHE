# ARCHE

> **🚀 Production Ready** — All 19 tests pass. See [TASK_B_WORKFLOW.md](TASK_B_WORKFLOW.md) for evaluation and [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) for deployment.

ARCHE is a FastAPI-based hackathon prototype for behavioral signal ingestion, privacy-preserving memory storage, and simulation-driven user intelligence.

## Task B: Recommendation Evaluation

Task B requires **inline behavioral snapshots** (no database pre-ingest):

- Send complete `user_persona.review_history` in each `/v1/recommend` request
- System builds behavioral snapshot and ranks full 8660-item catalog (<150ms)
- Supports cold-start users (empty history) with time-of-day priors

**Quick start:**

```bash
# Run evaluation (100 test users)
python step6_full_evaluation.py

# Test with inline history
curl -X POST http://localhost:8000/v1/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_persona": {"user_id": "u1", "review_history": [{"rating": 5, "category": "restaurants", "review_text": "Great!"}]}, "n": 10}'
```

See [TASK_B_WORKFLOW.md](TASK_B_WORKFLOW.md) for full details, evaluation methodology, and optimization guide.

## What is implemented

- `GET /v1/health` for a simple health check
- `POST /v1/ingest` for behavioral signal ingestion
- `POST /v1/simulate` for heuristic user simulation from memory + context
- `POST /v1/simulate-review` for Task A review simulation from user history + unseen item
- `POST /v1/recommend` for exploration-aware ranking
- `POST /v1/explain` for recommendation explainability
- Task A routed through `api/routes/task_a.py` -> `LangGraphStyleOrchestrator.route_task_a(...)`
- Task B routed through `api/routes/task_b.py` -> `LangGraphStyleOrchestrator.route_task_b(...)`
- Dedicated `ReviewGenerationAgent` (`agents/review_generation_agent.py`) for Task A generation
- Deterministic privacy abstraction that hashes user/item tokens and redacts sensitive nested fields
- `MemoryManager` wiring in the API app state
- SQLite-backed memory storage with a local vector store fallback for development
- Lightweight Docker containerization for local submission readiness
- Fresh Task B evaluation runner output under `data/evaluation/fresh_task_b_*.json`

## Project structure

- `api/` — FastAPI application entrypoint and routes
- `memory/` — memory manager and local vector fallback
- `data/` — dataset pipelines and evaluation helpers
- `BuildDocs/` — planning, architecture, and context memory files
- `demo/` — sample data for demos
- `frontend/` — React + Vite + Tailwind demo UI
- `tests/` — API smoke tests

## Setup

### 1) Create and activate the virtual environment

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## Run the API

```powershell
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- Health check: http://127.0.0.1:8000/v1/health
- Interactive docs: http://127.0.0.1:8000/docs

## Run with Docker

```powershell
docker compose up --build
```

Then open:

- Health check: http://127.0.0.1:8000/v1/health
- Interactive docs: http://127.0.0.1:8000/docs

Environment variables can be copied from `.env.example`.

## Ingest example

```json
{
  "user_token": "user123",
  "signal": {
    "event_type": "click",
    "item_token": "item-abc",
    "item_category": "books",
    "session_context": {
      "email": "user@example.com"
    },
    "engagement_depth": 0.5,
    "dwell_time_seconds": 10,
    "sequence_position": 1
  }
}
```

Example request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/v1/ingest `
  -ContentType 'application/json' `
  -Body '{"user_token":"user123","signal":{"event_type":"click","item_token":"item-abc","item_category":"books","session_context":{"email":"user@example.com"},"engagement_depth":0.5,"dwell_time_seconds":10,"sequence_position":1}}'
```

## Simulate example

```json
{
  "user_token": "user123",
  "context": {
    "time_bucket": "evening",
    "day_type": "weekday",
    "device_class": "mobile",
    "network_quality": "medium",
    "region_tier": "urban",
    "session_depth": 2,
    "entry_point": "search"
  }
}
```

Example request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/v1/simulate `
  -ContentType 'application/json' `
  -Body '{"user_token":"user123","context":{"time_bucket":"evening","day_type":"weekday","device_class":"mobile","network_quality":"medium","region_tier":"urban","session_depth":2,"entry_point":"search"}}'
```

## Tests

```powershell
python -m pytest tests/test_ingest.py tests/test_simulate.py tests/test_task_a.py -q
python -m pytest tests/test_ingest.py tests/test_simulate.py tests/test_task_a.py tests/test_integration.py tests/test_performance.py -q
```

## Evaluation

Use the fixture evaluation runner for benchmark metric summaries:

```powershell
python data/evaluation/run_evaluation.py A path\to\task_a_results.json
python data/evaluation/run_evaluation.py B path\to\task_b_results.json --k 10
```

Use the full Task B pipeline runner for the current Amazon/Goodreads dataset pass:

```powershell
python -m data.run_full_recommend_evaluate
```

Current fresh run status:

- Amazon processed train/test files are present and were evaluated for 50 users.
- Goodreads processed train/test files are present and were evaluated for 50 users.
- Latest fresh Task B metrics are written to `data/evaluation/fresh_task_b_metrics.json`.
- Latest fresh Task B metrics: NDCG@10 `0.0287`, Hit Rate@10 `0.1400`, Precision@10 `0.0160`, contextual relevance proxy `1.0000`.

## Notes

- User and item tokens are hashed before persistence.
- Nested sensitive values in `session_context` are redacted through the privacy abstraction.
- `/v1/simulate` is currently heuristic-driven and uses memory history when available.
- The memory layer is optimized for local development and demo usage.
- MVP alignment note: the runtime uses `LangGraphStyleOrchestrator` (explicit multi-agent routing, sequential execution).
- Full native LangGraph DAG orchestration with specialized nodes remains roadmap scope and is not required for current MVP submission.
- `/v1/recommend` persists the latest recommendation payload through `orchestrator/recommendation_persistence.py`, which keeps an in-memory fallback if Windows temporarily blocks writes to `data/last_recommend.json`.
