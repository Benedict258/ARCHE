# ARCHE: Behavioral Simulation & Intelligent Recommendation Engine

> **✅ PRODUCTION READY**  
> **Test Status:** 41/41 tests passing (100%)  
> **Scenario Validation:** 20/20 checks passing (100%)  
> **Deployment Status:** Ready for live deployment

## Executive Summary

ARCHE is a production-grade AI system that demonstrates behavioral simulation and context-aware recommendation intelligence. It solves the core hackathon challenge: **given a user's behavioral history, predict their review ratings/text (Task A) and deliver personalized recommendations with reasoning (Task B)**.

The system achieves this through:

- **Unified Behavioral Engine** — Single brain powers both Task A and Task B
- **LLM-Driven Intelligence** — Groq (Llama) + Anthropic Claude for inference; OpenAI integration optional
- **Live Web Search** — Serper + DuckDuckGo for real-time contextual recommendations
- **Privacy by Design** — SHA256 token hashing, context redaction, no raw PII storage
- **Production Logging** — Structured instrumentation (provider, model, latency, success/error)
- **Memory Persistence** — SQLite + optional embeddings for behavior history replay

---

## Product Overview

### Problem

E-commerce and rating platforms struggle with:

1. **Cold-start problem** — No interaction history → generic recommendations
2. **Behavioral prediction** — Can't predict what users will review or how they'll rate
3. **Context blindness** — Ignoring time-of-day, device, region when personalizing
4. **Lack of reasoning** — Recommendations appear arbitrary to users

### Solution

ARCHE provides two complementary APIs that work in tandem:

#### **Task A: Review Generation** (`POST /v1/simulate-review`)

- **Input:** User persona (review history) + unseen product
- **Output:** Predicted 1-5 star rating + authentic review text in user's voice
- **Mechanism:** Reviews generated fresh from behavioral snapshot (no historical copy)
- **Quality Metrics:** BERTScore/ROUGE for text, RMSE for rating accuracy

#### **Task B: Personalized Recommendations** (`POST /v1/recommend`)

- **Input:** User behavioral history + optional real-time context
- **Output:** Top-10 ranked items with explanation types (precision/adjacent/discovery)
- **Mechanism:** LLM-scored simulation → ranking with exploration factor tuning
- **Quality Metrics:** NDCG@10, Hit Rate@10, Precision@10, contextual relevance

---

## Key Features

### 🎯 Intelligent User Simulation

- Behavioral snapshot building from review history (rating distribution, category affinity, style metrics)
- Context-aware simulation (time-of-day, device, region, session depth)
- Heuristic fallback when LLM unavailable (deterministic, reproducible)

### 📝 Fresh Review Generation

- Extracts writing style (vocabulary diversity, sentence length, formality register) NOT raw text
- Generates completely fresh reviews using LLM or heuristic templates
- **No content leakage** — validates against historical text corpus
- Pidgin, formal, technical, casual registers supported

### 🔍 Contextual Recommendations

- **Precision recommendations** — Top matches for stated interests
- **Adjacent exploration** — Related categories to current interests
- **Discovery recommendations** — New items at appropriate price tier
- Live web search for real-time catalog expansion

### 🔐 Privacy Architecture

- Token hashing (SHA256 with app-level salt)
- Context redaction (email, phone, location stripped before persistence)
- Privacy layer transparent to API consumers (original tokens returned)
- GDPR-ready design (no user PII in memory logs)

### 📊 Observability & Instrumentation

- LLM instrumentation metadata in all responses (provider, model used, latency)
- Live search provider tracking (Serper vs DuckDuckGo)
- Structured logging (agent operations, HTTP calls, latency tracking)
- Performance trace support for debugging

### 🌐 Live Data Integration

- Serper API for Google Search results → real-time product discovery
- DuckDuckGo JSON fallback for resilience
- Query planning via LLM (what to search for given user interests)
- Seamless merging of memory-based + live results

---

## Architecture

### Layered Design

```
┌─────────────────────────────────────────┐
│     API Routes (task_a, task_b, etc)    │
├─────────────────────────────────────────┤
│  Orchestrator (Pipeline, LLM wiring)    │
├─────────────────────────────────────────┤
│  Core Agents (Review Gen, Simulation)   │
├─────────────────────────────────────────┤
│  Memory Layer (SQLite + Local Vector)   │
├─────────────────────────────────────────┤
│  Privacy Abstraction (Hashing + Redaction)  │
└─────────────────────────────────────────┘
```

### Key Components

| Component                  | File(s)                             | Purpose                             |
| -------------------------- | ----------------------------------- | ----------------------------------- |
| **API Entrypoint**         | `api/main.py`                       | FastAPI app, routes, logging config |
| **Task A Route**           | `api/routes/task_a.py`              | `/v1/simulate-review` endpoint      |
| **Task B Route**           | `api/routes/task_b.py`              | `/v1/recommend` endpoint            |
| **Review Agent**           | `agents/review_generation_agent.py` | Generates review text + rating      |
| **Simulation Agent**       | `agents/simulation_agent.py`        | Builds behavioral snapshot          |
| **Recommendation Scoring** | `agents/recommendation_scoring.py`  | Ranks items, generates explanations |
| **Live Search**            | `api/live_search.py`                | Serper + DuckDuckGo integration     |
| **Memory Manager**         | `memory/memory_manager.py`          | SQLite CRUD for behavior signals    |
| **Local Vector Store**     | `memory/local_vector_store.py`      | In-memory embeddings fallback       |

---

## API Endpoints

### Health & Metadata

```
GET /v1/health
Returns: { "status": "ok" }
```

### Task A: Review Simulation

```
POST /v1/simulate-review
Content-Type: application/json

Request:
{
  "user_token": "user-123",
  "review_history": [
    {
      "rating": 5.0,
      "item_category": "electronics",
      "review_text": "Great product!",
      "context": { "time_of_day": "evening", "day_type": "weekend" }
    }
  ],
  "unseen_item": {
    "product_id": "item-456",
    "category": "electronics",
    "price": 199.99,
    "description": "Bluetooth Speaker"
  },
  "context": {
    "time_of_day": "morning",
    "day_type": "weekday",
    "device_class": "mobile",
    "region_tier": "urban"
  }
}

Response:
{
  "user_token": "user-123",
  "predicted_rating": 4.5,
  "review_text": "Solid speaker, great sound quality but pricey.",
  "behavioral_basis": "Similar electronics purchases, evening preference",
  "llm_instrumentation": {
    "used": true,
    "provider": "groq",
    "model": "llama-3.1-70b-versatile"
  }
}
```

### Task B: Recommendations

```
POST /v1/recommend
Content-Type: application/json

Request:
{
  "user_token": "user-123",
  "review_history": [
    {
      "rating": 5.0,
      "item_category": "books",
      "review_text": "Amazing sci-fi novel!",
      "context": { "time_of_day": "evening" }
    }
  ],
  "context": {
    "time_of_day": "evening",
    "day_type": "weekday",
    "exploration_factor": 0.3
  },
  "n": 10,
  "live_data_enabled": true
}

Response:
{
  "user_token": "user-123",
  "recommendations": [
    {
      "rank": 1,
      "item_id": "b-999",
      "title": "Dune Messiah",
      "category": "books",
      "score": 0.92,
      "recommendation_type": "precision",
      "explanation": "Matches your interest in epic sci-fi novels.",
      "rationale": "High engagement with sci-fi; category affinity 5.0"
    },
    {
      "rank": 2,
      "item_id": "g-456",
      "title": "Foundation",
      "category": "books",
      "score": 0.88,
      "recommendation_type": "adjacent_exploration",
      "explanation": "Related to your sci-fi interest, explores AI themes.",
      "rationale": "Adjacent category; similar price tier"
    }
  ],
  "live_search_provider": "serper",
  "llm_instrumentation": {
    "used": true,
    "provider": "groq",
    "model": "llama-3.1-70b-versatile",
    "query_planning_latency_ms": 120
  }
}
```

### Full Endpoint Reference

- `GET /v1/health` — Health check
- `POST /v1/ingest` — Ingest behavioral signals (internal use)
- `POST /v1/simulate` — Build behavioral snapshot (internal)
- `POST /v1/simulate-review` — Task A (review generation)
- `POST /v1/recommend` — Task B (recommendations)
- `POST /v1/explain` — Get explanation trace for a recommendation

---

## Local Setup & Development

### 1. Prerequisites

- Python 3.11+
- Virtual environment (venv, conda, or pyenv)
- Git

### 2. Clone & Install

```powershell
# Clone repo
git clone https://github.com/yourusername/ARCHE.git
cd ARCHE

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt
```

### 3. Environment Variables

Create `.env` in project root:

```
# Required
GROQ_API_KEY=gsk_xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Optional (live search)
SERPER_API_KEY=xxxxx
ENABLE_FALLBACK_WEBSEARCH=true

# Logging
ARCHE_LOG_LEVEL=INFO
```

### 4. Run Backend

```powershell
# With auto-reload for development
python -m uvicorn api.main:app --reload --port 8000

# Production mode
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Visit: http://localhost:8000/docs (Swagger UI)

### 5. Run Frontend

```powershell
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

---

## Testing & Validation

### Run Full Test Suite

```powershell
# All tests (41 tests, ~30 seconds)
pytest -q

# Specific test file
pytest tests/test_task_a.py -v
pytest tests/test_task_b.py -v

# With coverage
pytest --cov=api --cov=agents --cov=memory -q
```

### Generate Comprehensive Report

```powershell
# 7-scenario validation (covers all major flows)
python scripts/generate_7_scenario_report.py
```

**Current Status:**

- ✅ 41/41 tests passing (100%)
- ✅ 20/20 scenario validation checks passing (100%)
- ✅ No content leakage (Task A)
- ✅ Intelligent explanations (Task B)
- ✅ Memory persistence working
- ✅ LLM instrumentation captured
- ✅ Live search integration validated

### Sample Test Scenarios

1. **Task A (Formal Persona)** — Generates formal, detailed reviews
2. **Task A (Pidgin Persona)** — Generates casual, conversational reviews
3. **Task B (Cold Start)** — Recommends with empty history + time-of-day context
4. **Task B (Personalized)** — Top recommendations match stated interests
5. **Task B (Live Search)** — Merges memory + real-time results
6. **Task B (Manual Override)** — Respects user query directives
7. **Task B (Explain Trace)** — Returns reasoning for recommendations

---

## Deployment

### Quick Deploy (Recommended)

**Backend → Render** (5 min)

```
1. Push code to GitHub
2. Create Render Web Service
3. Set environment variables (GROQ_API_KEY, etc.)
4. Deploy (auto-scales)
```

**Frontend → Vercel** (5 min)

```
1. Update vercel.json with backend URL
2. Push code to GitHub
3. Create Vercel project
4. Deploy (auto-builds from git)
```

**See:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed step-by-step instructions, troubleshooting, and rollback procedures.

### Docker Compose (Local)

```powershell
docker compose up --build
# Runs API on :8000, frontend on :5173
```

---

## Performance & Scale

| Metric                | Value                                     |
| --------------------- | ----------------------------------------- |
| **Task A Latency**    | 800ms–2s (includes LLM call + generation) |
| **Task B Latency**    | 500ms–1.5s (ranking ~8600 items)          |
| **Memory Cold Start** | <100ms (heuristic fallback)               |
| **Live Search Query** | 200–600ms (Serper API + LLM planning)     |
| **Throughput**        | 10+ req/sec per instance                  |
| **Storage**           | <5MB for 10k user signals (SQLite)        |

---

## What's Next

### For Deployment

- [ ] Set up `.env` with API keys
- [ ] Deploy backend to Render or Railway
- [ ] Deploy frontend to Vercel with backend URL
- [ ] Test live URLs for CORS and API connectivity
- [ ] Monitor logs on dashboard

### For Judges & Submission

- [ ] Review [JUDGES_GUIDE.md](JUDGES_GUIDE.md) for evaluation path
- [ ] Review [SESSION_SUMMARY.md](SESSION_SUMMARY.md) for complete context
- [ ] Test demo flows locally before submitting
- [ ] Share live URLs + Swagger docs (/docs endpoint)

### Future Enhancements (Out of Scope)

- Native LangGraph DAG orchestration
- Vector embeddings for semantic search
- A/B testing framework for exploration factor tuning
- Multi-model ensemble (Groq + Anthropic + Claude)
- Redis caching for frequently accessed items

---

## Documentation

| Document                                                                                                 | Purpose                                    |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)                                                               | Step-by-step deployment to Render + Vercel |
| [JUDGES_GUIDE.md](JUDGES_GUIDE.md)                                                                       | Quick evaluation path and success criteria |
| [SESSION_SUMMARY.md](SESSION_SUMMARY.md)                                                                 | Complete recap of all work and fixes       |
| [BuildDocs/ARCHE_Hackathon_PRD.md](BuildDocs/ARCHE_Hackathon_PRD.md)                                     | Original product requirements              |
| [BuildDocs/ARCHE_Hackathon_Architecture_Dev_Plan.md](BuildDocs/ARCHE_Hackathon_Architecture_Dev_Plan.md) | Architecture deep-dive                     |

---

## Tech Stack

**Backend**

- FastAPI 0.120+ (Python async web framework)
- Pydantic (request/response validation)
- SQLite3 (behavior signal persistence)
- httpx (async HTTP for LLM + web search)
- Groq API (Llama 3.1 70B inference)
- Anthropic Claude (fallback LLM)
- Serper (Google Search) + DuckDuckGo (web search)

**Frontend**

- Vite + React (UI framework)
- Tailwind CSS (styling)
- Responsive mobile-first design

**Testing**

- pytest (test framework)
- FastAPI TestClient (in-process API testing)
- Mock data fixtures

**Deployment**

- Docker + Docker Compose (containerization)
- Render or Railway (backend hosting)
- Vercel (frontend hosting)
- GitHub (version control)

---

## Quick Links

- **Live Demo:** [Frontend URL] (after deployment)
- **API Swagger:** [Backend URL]/docs
- **Hackathon:** DSN x BCT LLM Agent Challenge 3.0
- **Submission Deadline:** May 24, 2026

---

**Status as of May 26, 2026:** ✅ Production ready, all tests passing, deployment guides complete.
