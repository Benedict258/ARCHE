# ARCHE Submission Package

This folder contains the final submission bundle for the current agentic ARCHE state.

## Included

- `arche_solution_paper.md` - final solution paper with evaluation metrics filled in
- `evaluation_metrics.json` - reproducible benchmark results used in the paper
- `validation_summary.md` - latest API and integration verification run
- `package_manifest.json` - machine-readable bundle index for the SDK and webapp deliverables

## Main Submission Details

The primary judge-facing submission points are already implemented and ready:

- `POST /v1/simulate-review` — Task A user modeling endpoint
- `POST /v1/recommend` — Task B recommendation endpoint
- `POST /v1/explain` — explanation endpoint for recommendation traces
- Webapp in `frontend/` — interactive UI that calls the API endpoints above

### How the endpoints are used

#### Task A: `POST /v1/simulate-review`

- Input: user persona + product details, represented in the API as `user_persona` or `user_token` + `user_history` + `item`, optional `context`
- Output: `predicted_rating`, `generated_review`, `confidence`, `reasoning`
- Purpose: simulate how the user would review an unseen item

#### Task B: `POST /v1/recommend`

- Input: user persona, represented in the API as `user_persona` or `user_token`, optional `context`, optional `n`
- Output: ranked recommendations with `rank`, `item_name`, `category`, `confidence`, `reasoning`, `recommendation_type`
- Purpose: deliver personalized, explainable recommendations

#### `POST /v1/explain`

- Input: `user_token`, `recommendation_id`
- Output: full explanation trace, simulation snapshot, and alternatives considered
- Purpose: show why a recommendation was chosen

### How the webapp uses the endpoints

The webapp is a judge/demo-facing UI that sits on top of the same API:

- The landing page introduces ARCHE and routes users into the demo
- The demo page collects a user token and requests recommendations from `POST /v1/recommend`
- Each recommendation card can call `POST /v1/explain` to reveal the reasoning trace
- The frontend API layer in `frontend/src/services/api.ts` centralizes the endpoint calls

This means judges can evaluate the system in two ways:

1. **Direct API submission** through the endpoints
2. **Interactive webapp** for a visual walk-through of the same outputs

### Practical judge flow

- For **Task A**, judges can call `POST /v1/simulate-review` directly with a user persona and item details, or use the same backend contract through a web form if desired.
- For **Task B**, judges can call `POST /v1/recommend` directly, then click into `POST /v1/explain` to inspect the reasoning trace.
- The frontend currently showcases the recommendation and explanation flow, while the API covers the full submission surface for both tasks.

## SDK Deliverable

The Python SDK is provided in `sdk/client.py` and is ready for judge or teammate use.

### What it exposes

- `ArcheClient.health()` - API health check
- `ArcheClient.ingest()` - privacy-preserving signal ingestion
- `ArcheClient.simulate()` - user behavior simulation
- `ArcheClient.recommend()` - ranked recommendations with reasoning
- `ArcheClient.explain()` - causal explanation trace for a recommendation

### SDK usage example

See `examples/usage_example.py` for a full async walkthrough of the SDK and pipeline client.

## Webapp Deliverable

The webapp lives in `frontend/` and is built with Vite + React + Tailwind.

### Included app assets

- `frontend/src/` - UI source code
- `frontend/dist/` - production build output
- `frontend/package.json` - frontend scripts and dependencies
- `frontend/README.md` - frontend run/build notes

### Webapp build commands

```powershell
cd frontend
npm install
npm run build
```

### Webapp run commands

```powershell
cd frontend
npm run dev
```

The app expects the backend to be available at the API base URL configured in `frontend/.env.local`.

## Bundle Contents

The final bundle is organized to help judges reproduce the project quickly:

1. **Backend** - FastAPI app in `api/`
2. **SDK** - async Python client in `sdk/client.py`
3. **Webapp** - production-ready frontend in `frontend/`
4. **Docs** - solution paper, evaluation metrics, and validation notes

## Reproducibility

Run the evaluator against the benchmark files in `data/evaluation/`:

- Task A: `python data/evaluation/run_evaluation.py A data/evaluation/task_a_benchmark_results.json`
- Task B: `python data/evaluation/run_evaluation.py B data/evaluation/task_b_benchmark_results.json --k 10`

Run API validation tests:

- `python -m pytest tests/test_integration.py -q`
- `python -m pytest tests/test_cold_start.py -q`
- `python -m pytest tests/test_performance.py -q`

## Reproduction

Run the evaluator against the benchmark files in `data/evaluation/`:

- Task A: `python data/evaluation/run_evaluation.py A data/evaluation/task_a_benchmark_results.json`
- Task B: `python data/evaluation/run_evaluation.py B data/evaluation/task_b_benchmark_results.json --k 10`

Run API validation tests:

- `python -m pytest tests/test_integration.py -q`
- `python -m pytest tests/test_cold_start.py -q`
- `python -m pytest tests/test_performance.py -q`

## Notes

- The benchmark files were generated from live API endpoints in this repository.
- The API now routes through the LangGraph-style multi-agent orchestrator (`orchestrator/langgraph_pipeline.py`) and real dataset loader (`data/dataset_loader.py`) when data is present.
- The paper metrics are rounded to 4 decimal places for presentation.
- The SDK and webapp are included to make the final submission reproducible from both code and UI entry points.
