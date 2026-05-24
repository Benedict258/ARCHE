# ARCHE: Simulation-Driven Agentic User Modeling for Review Generation and Personalized Recommendation

## Abstract

ARCHE is a simulation-driven agentic system for two related hackathon tasks: Task A user modeling (review simulation) and Task B recommendation. The shared backbone is a behavioral simulation layer that converts user history and current context into a compact user-state representation, which is then consumed by downstream generation and ranking modules. In the current MVP, ARCHE runs as a FastAPI application with a custom memory layer, lightweight orchestration, and a React demo frontend. It supports both a review simulation endpoint and an exploration-aware recommendation endpoint. Evaluation is designed around RMSE and ROUGE-style text overlap for Task A, and NDCG@10 / Hit Rate@10 for Task B.

> Metrics below were generated from the reproducible benchmark files in `data/evaluation/` using the built-in runner.

Benchmark fixture results in the current MVP:

- Task A RMSE: 0.5774
- Task A ROUGE-1/2/L: 0.3868 / 0.1520 / 0.2771
- Task B NDCG@10: 0.6131
- Task B Hit Rate@10: 1.0000
- Task B Precision@10: 0.2000

Verification note (May 20, 2026): metrics were re-run using
`python -m data.evaluation.run_evaluation` over
`data/evaluation/task_a_benchmark_results.json` and
`data/evaluation/task_b_benchmark_results.json` and match the values above.

Fresh real-data Task B pass (May 22, 2026):

- Command: `python -m data.run_full_recommend_evaluate`
- Dataset evaluated: Amazon + Goodreads processed splits, 100 users total
- Goodreads status: included (50 users evaluated)
- Fresh NDCG@10: 0.0287
- Fresh Hit Rate@10: 0.1400
- Fresh Precision@10: 0.0160
- Fresh contextual relevance proxy: 1.0000

Interpretation: the API pipeline is reproducible end to end and now produces non-zero fresh retrieval metrics on real data. The benchmark fixtures remain useful for contract validation; the fresh artifacts should be treated as the honest current real-data baseline.

## 1. Introduction

Modern user modeling systems often rely on static preferences or shallow collaborative signals. That breaks down on sparse-history users, culturally specific writing styles, and context-sensitive behavior. ARCHE addresses this by simulating the user before generating a review or ranking a recommendation.

The core contribution is not a larger model, but a shared behavioral simulation layer that produces a richer representation of user intent, preference, and context. This shared representation powers both Task A and Task B.

## 2. Problem Statement

The official brief requires both:

- Task A: simulate what a user would write about an unseen item
- Task B: recommend what the user should see next

Most systems solve one task independently. ARCHE treats them as two outputs of the same simulated user state.

## 3. Architecture

### 3.1 Shared Simulation Backbone

The system first summarizes recent behavioral memory and context into a simulation snapshot. In the current MVP this is implemented in `api/main.py` and reused by both the review simulation route and recommendation route.

### 3.2 Task A: Review Simulation

Task A uses the simulation snapshot plus the user’s past reviews to generate:

- a predicted integer rating from 1 to 5
- a review written in the user’s style
- a tone confidence score
- a plain-English behavioral basis

The MVP implementation uses register detection and lightweight Nigerian calibration to make the generated text more specific and culturally grounded.

### 3.3 Task B: Recommendation

Task B uses the same simulation backbone to produce ranked recommendations. The current MVP preserves the 60/25/15 exploration balance for precision, adjacent exploration, and discovery.

### 3.4 Memory Layer

The current runtime memory stack is lightweight and local:

- SQLite metadata store
- local vector fallback
- persisted recommendation output for explainability

The HackAlign target architecture includes ChromaDB, PostgreSQL, and Redis; that is the roadmap version, not the current MVP runtime.

## 4. Dataset and Evaluation

### 4.1 Datasets

The repo now includes preprocessing pipelines for:

- Yelp Open Dataset
- Amazon reviews
- Goodreads reviews

The live demo runtime uses local memory and the local vector store by default. The current workspace includes both Amazon and Goodreads raw + processed files, and both sources participate in the fresh Task B pass.

### 4.2 Task A Evaluation

Task A is evaluated with:

- RMSE on predicted ratings
- ROUGE-1, ROUGE-2, ROUGE-L style overlap on generated reviews

### 4.3 Task B Evaluation

Task B is evaluated with:

- NDCG@10
- Hit Rate@10
- Precision@10

### 4.4 Evaluation Runner

Use the built-in runner to generate metric summaries:

```powershell
python data/evaluation/run_evaluation.py A path\to\task_a_results.json
python data/evaluation/run_evaluation.py B path\to\task_b_results.json --k 10
```

## 5. Nigerian Contextualization

ARCHE adds a lightweight cultural calibration layer so the generated review can match a user’s writing register more closely. The current MVP detects language markers in review history and calibrates the generated output accordingly.

This matters because the brief explicitly rewards culturally relevant behavior rather than generic Westernized outputs.

## 6. Implementation Status

Current repo state:

- FastAPI backend: working
- Review simulation endpoint: working
- Recommendation endpoint: working
- Memory layer: working locally
- Docker containerization: added
- Evaluation scripts: added
- Frontend demo: working
- Real dataset ingestion: Amazon and Goodreads processed splits are present and both participate in the fresh Task B pass
- Test status: integration and performance suites pass after the persistence and initialization cleanup

## 7. Future Work

Post-hackathon or later-phase work would include:

- full multi-agent orchestration
- stronger memory services
- real dataset ingestion and metric generation
- broader dashboard and analytics views

## 8. Conclusion

ARCHE’s key idea is simple: simulate the user once, then use that simulation for both review generation and recommendation. That shared backbone makes the system easier to explain, easier to demo, and better aligned with the competition’s Task A + Task B structure.
