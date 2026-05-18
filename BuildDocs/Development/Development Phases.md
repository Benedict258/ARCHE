# ARCHE — Development Phases (Accelerated 4‑Day Sprint)

Goal: Deliver the hackathon-ready ARCHE hackathon build (Simulation + Recommendation + Explainability + SDK + Demo) in 4 days working round‑the‑clock with multiple engineers. This document compresses the ARCHE_Hackathon_Architecture_Dev_Plan.md and ARCHE_Hackathon_PRD.md into a parallelized, risk‑aware execution plan. Do not change scope without explicit approval from the core team.

Prerequisites (before Day 1)

- Team: at minimum 1 AI Engineer, 1 Backend Dev, 1 Fullstack Dev, 1 DevOps (can be shared). Extra engineers accelerate parallel work.
- Accounts & keys: Claude/LLM API key, hosting account (Railway/Render/Vercel), Postgres credentials, Redis endpoint.
- Repo + branch created: `feature/hackathon-core` (done).
- Mock demo data: `demo/mock_data/users.json`, `products.json`, `interactions.json` (generate Day 1).
- Confirmed Node/Python env and developer tooling installed.

What to ship in 4 days

- Working `POST /v1/simulate`, `POST /v1/recommend`, `POST /v1/explain` endpoints
- Memory layer (ChromaDB dev or fallback file-based vectors) + Postgres metadata + Redis session cache
- Explainability traces attached to every recommendation
- Python SDK with quickstart example
- React demo dashboard with three demo personas and live API integration
- Backup demo recording and submission package

Team Roles & Parallel Workstreams

- AI Engineer (Simulation, Recommendation, Explainability, prompts)
- Backend Dev (FastAPI endpoints, Memory integrations, DB migrations, SDK)
- Fullstack Dev (React dashboard, demo data, UI polish)
- DevOps / SRE (Docker/docker-compose, local dev infra, deployment)
- QA/Support (test harness, smoke tests, demo recording)

Sprint Structure & Checkpoints

- 4 days compressed; work in 12-hour shifts recommended with overlapping handoff windows.
- Checkpoints: Every 6 hours — short sync, record progress in Build-Context-Memory.json
- Demo dry-run at end of Day 4 (final rehearsal + backup recording)

Day 0 — Prep (few hours before Day 1)

- Confirm API keys + env secrets in `.env` and `.env.example`
- Resolve dependency issues (chromadb version) — choose available release or fallback to local simple vector store
- Create branch `feature/hackathon-core` (done)
- Create base `requirements.txt`, initialize repo (done)

Day 1 — Foundation & Memory
Primary objective: get a working API skeleton, memory layer skeleton, and demo data

- Backend
  - Create FastAPI skeleton (`api/main.py`) with `/v1/health` and `/docs`
  - Implement `memory/` package with `memory_manager.py` (interfaces only)
  - Setup docker-compose for Postgres + Redis; if ChromaDB not available, add `memory/local_vector_store.py` fallback
- AI Engineer
  - Draft initial system prompts for Simulation and Explainability agents
  - Prepare mock cohort priors and demo personas
- Fullstack
  - Create React scaffold `dashboard/` and static mock views
- DevOps
  - Ensure environment works and CI checks locally
    Deliverables: health endpoint up, memory interfaces present, demo data generated

Day 2 — Simulation Engine & Ingestion
Primary objective: implement `POST /v1/ingest` and `POST /v1/simulate`

- Backend
  - Implement `POST /v1/ingest` with privacy abstraction (anonymize tokens)
  - Wire ingestion to MemoryManager.update() (session + medium-term)
- AI Engineer
  - Implement `SimulationAgent` prototype using LLM calls; implement cold-start path (cohort priors)
  - Create unit tests for simulation output schema
- Fullstack
  - Wire `SimulationView` to call `/v1/simulate` with demo personas
    Deliverables: ingest working, simulation returns `SimulationOutput` JSON matching schema

Day 3 — Recommendation & Explainability
Primary objective: implement `POST /v1/recommend` and `POST /v1/explain`

- Backend
  - Implement `RecommendationAgent` with 60/25/15 split logic and diversity penalty
  - Wire ExplainabilityAgent to attach `ReasoningTrace` to each recommendation
  - Add `/v1/recommend` and `/v1/explain` endpoints
- AI Engineer
  - Refine ranking/scoring prompts and ensure reproducible reasoning traces
  - Build tests: RecommendationSet validation, exploration ratio checks
- Fullstack
  - RecommendationView shows 10 recs, badges, and reasoning expansion panel
    Deliverables: Recommendation + Explain endpoints return fully populated JSON with reasoning

Day 4 — Orchestration, SDK, Dashboard, Testing & Demo
Primary objective: integrate orchestrator, produce SDK, finalize UI, and rehearse demo

- Backend
  - Implement lightweight orchestrator (LangGraph or simple sequential pipeline as fallback)
  - Create `sdk/` package with async client quickly consumable in demo
  - Add authentication stub (X-API-Key) and basic rate limit middleware
- AI Engineer
  - Final prompt tuning and add pre-caching for demo personas to avoid LLM latency on stage
- Fullstack
  - Polish UI, implement demo persona toggles, integrate live SDK calls
- QA/DevOps
  - Run performance checks, gather logs, prepare backup demo recording
    Deliverables: Full end-to-end demo flow, SDK quickstart, backup recordings, submission package

Continuous Tasks (every day)

- Logging & Monitoring: ensure explanation/audit logs saved for sample recommendations
- Session Memory Update: after every meaningful change, append a session object to `Build-Context-Memory.json` (see AI_Starter.md)
- Tests: unit tests for memory, simulation, recommendation, explainability
- Demo rehearsal and QA — iterate until stable

Acceptance Criteria (Hackathon judges + internal)

- Cold-start simulation yields plausible personalization for zero-history user
- Recommendation output includes 10 items with 60/25/15 exploration split and diversity score >= 0.5
- Each recommendation includes a `ReasoningTrace` with required fields
- API can be exercised via SDK with one-line quickstart
- Demo can be run in <7 minutes; backup recording available

Risks & Mitigations

- LLM latency / quota: pre-cache demo outputs and implement synchronous fallback JSONs
- ChromaDB or vector store installation issues: provide local fallback vector store (file-based) for dev/demo
- Scope creep: freeze non-essential features after Day 2; focus on L1–L3 (Simulation, Recommendation, Explainability)
- Live demo failure: have pre-recorded video and static JSON responses to serve as fallback

Deliverables & Artifacts to commit

- `api/` FastAPI app with endpoints
- `memory/` memory interfaces and local fallback store
- `agents/` Simulation, Recommendation, Explainability prototypes
- `sdk/` Python client with `quickstart.py`
- `dashboard/` React demo
- `demo/demo_script.md` and pre-recorded backup video
- Updated `Build-Context-Memory.json` session objects after each major milestone

Handover & Communication

- Use short, focused handoffs every 6 hours in shared channel (Slack/Discord)
- Commit frequently and open small PRs to `feature/hackathon-core` for review
- Tag commit messages with `hackathon:` prefix for easy filtering

Appendix: Immediate Checklist (first 6 hours)

- [ ] Update `requirements.txt` to use supported `chromadb` or add `memory/local_vector_store.py` fallback
- [ ] Create `api/main.py` with `/v1/health`
- [ ] Create `memory/memory_manager.py` and `memory/local_vector_store.py`
- [ ] Generate `demo/mock_data/*` and `demo/demo_script.md`
- [ ] Append session object `session_002` to `Build-Context-Memory.json` documenting these actions

---

This `Development Phases.md` is authoritative for the compressed sprint. After each meaningful change, append an entry to `Build-Context-Memory.json` as required by `AI_Starter.md`.
