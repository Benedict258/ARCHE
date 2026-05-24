# Task B Solution Paper — Recommendations, Live Web Enrichment & Explainability

## Executive Summary

Task B focuses on producing explainable, high-quality recommendations that blend a local catalog with live web evidence. Judges will evaluate personalization, explainability, live-data blending, and reproducibility. ARCHE implements an exploration-aware recommendation engine that uses a simulation-first approach, optional LLM-guided live web enrichment (Serper adapter), and per-item explanations grounded in evidential snippets.

## Problem Statement

Recommendation systems often fail by being context-blind, opaque, and fragile in cold-start scenarios. Task B needs a system that:

- Produces top-N personalized recommendations.
- Blends local vector-store candidates with live web results (when enabled).
- Returns per-item explanations that reference signals and sources.
- Is controllable via typed API parameters for judge testing.

## Objectives

- Provide `n` personalized recommendations with `explanation` and `source` metadata.
- Support `enable_live_data` toggle and `live_query` override.
- Persist the last recommendation for explainability fallbacks.
- Maintain deterministic behavior with `enable_live_data=false` for repeatable judged runs.

## System Architecture (Task B)

Key components:

- `api/routes/task_b.py`: typed request model exposing `enable_live_data`, `live_query`, `live_results_limit`, and `output_format`.
- `agents/recommendation_agent.py`: core ranking and optional LLM re-ranking logic.
- `api/live_search.py`: `LiveSearchService` — LLM-guided query planning + Serper web search adapter.
- `orchestrator/langgraph_pipeline.py`: coordinates simulation → retrieval → live enrichment → ranking → persist.
- `orchestrator/recommendation_persistence.py`: atomic save/load for last recommendation used by explain endpoint.

Flow:

1. POST to `/v1/recommend` with persona/context and `enable_live_data` flag.
2. Retrieve candidate pool from local vector store and heuristics.
3. If `enable_live_data` is true, call `LiveSearchService.build_query()` (LLM) to create web-query terms, fetch Serper results, transform into candidate objects, and fingerprint them.
4. Merge candidate pools; apply small score boost to live items (configurable).
5. Optionally call LLM to re-score top-K candidates for personalization.
6. Generate per-item `explanation` referencing primary signals and any live evidence snippets.
7. Persist the recommendation and return `n` items in requested `output_format`.

## Live Web Enrichment (Serper Adapter)

Design goals:

- Use LLM to transform user persona/context into high-precision web queries.
- Retrieve compact results (title, snippet, url) from Serper.
- Map web hits to local catalog candidates where possible and include unmatched hits as live candidates.

Operational notes:

- `SERPER_API_KEY` must be present in `.env`; environment is read at startup.
- Circuit-breaker and caching protect the system from live API failures and rate-limits.

## Ranking & Fusion Strategy

- Local candidate scoring: vector similarity + popularity + recency.
- Live candidate scoring: Serper relevance score normalized, plus a small `live_boost` parameter.
- Final score: weighted sum with configurable weights (local_weight, live_weight, exploration_injection).
- Exploration enforcement using 60/25/15 policy: 60% high-confidence, 25% adjacent exploration, 15% discovery injection.

## Explanations

Each returned item includes:

- `explanation`: 1–2 sentence rationale referencing the simulation snapshot (e.g., "Recommended because evening mobile context + inferred affinity for fashion").
- `source`: `local` or `live` and when `live`, the `url` and `snippet` used as evidence.

Explanation generation uses constrained LLM prompts and, where possible, attaches direct evidence snippets (to reduce hallucination and improve judge verification).

## API Contract (Task B)

- Endpoint: `POST /v1/recommend`
- Request fields (selected): `user_persona`, `context`, `n`, `enable_live_data` (bool), `live_query` (optional override), `live_results_limit`, `raw_input`, `output_format` (json|text)
- Response: array of recommendation items { `id`, `title`, `score`, `explanation`, `source`, `live_data` }

Swagger examples are embedded in `api/routes/task_b.py` to make judge testing straightforward.

## Evaluation Plan

- Relevance: human-judged relevance scores comparing `enable_live_data=false` baseline vs `true`.
- Explainability: judges verify explanation faithfulness by sampling items and URLs included.
- Latency: measure median and 95th percentile with and without live enrichment.

Metrics to report: relevance delta (%), explanation faithfulness score, TTFB (ms), live API error rate.

## BCT Alignment

ARCHE is explicitly designed for BCT's enterprise customers (see BuildDocs/ARCHE_Hackathon_PRD.md). Task B emphasizes e-commerce SME scenarios (product recommendation, cross-sell, discovery) and operational features valuable to BCT: deterministic judge-mode, enterprise persistence, and explainability for audit and client trust.

## Risks & Mitigations

- Live API instability: circuit-breaker + cache + fallback to local-only pool.
- Hallucinated explanations: include direct evidence (URL snippets) and validate any claims against the retrieved snippet.
- Privacy: sanitize queries to avoid PII leakage to external web search.

## Future Work

- Add dedicated adapters for Google Places, Yelp Fusion, and Amazon Product API to improve live-data coverage.
- Add LLM re-ranking fine-tuning and supervised evaluation harness.
- Harden production infra (rate-limiter, auth, monitoring dashboards).

---

_(Task B draft prepared and aligned with the DSN x BCT Hack brief; ready for formatting.)_
