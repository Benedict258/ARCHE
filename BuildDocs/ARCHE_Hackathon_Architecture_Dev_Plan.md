# ARCHE — System Architecture & Development Plan

## DSN x BCT LLM Agent Challenge Hackathon 3.0

---

| Field         | Detail                                        |
| ------------- | --------------------------------------------- |
| Document Type | System Architecture & 17-Day Development Plan |
| Version       | v1.0                                          |
| Hackathon     | DSN x BCT LLM Agent Challenge 3.0             |
| Deadline      | May 24, 2026                                  |
| Demo Day      | June 10, 2026 — Eko Hotel, Lagos              |
| Team          | AI Engineer + Backend Dev + Fullstack Dev     |

---

## MVP Freeze Status (May 18, 2026)

This section is the source of truth for what is implemented in this repository right now.

### Implemented Now (In Repo)

- API layer: `GET /v1/health`, `POST /v1/ingest`, `POST /v1/simulate`, `POST /v1/recommend`, `POST /v1/explain` in `api/main.py`
- Privacy abstraction: deterministic hash-and-redact in ingest flow
- Memory layer: SQLite metadata + local vector fallback in `memory/`
- Recommendation engine: 60/25/15 split with deterministic explain flow from persisted recommendation output
- SDK: async Python client in `sdk/client.py`
- Orchestrator: lightweight sequential pipeline in `orchestrator/pipeline.py`
- Frontend demo: React + Vite + Tailwind in `frontend/` with recommend/explain integration

### Deferred to Roadmap (Post-Hackathon)

- Full LangGraph graph orchestration with specialized agent nodes
- Dedicated `agents/` implementations for simulation/retrieval/context/explainability
- PostgreSQL + Redis production memory architecture
- Route modularization + auth/rate-limit middleware split
- Next.js enterprise dashboard and expanded analytics views

### Architecture Note

Sections below describe the target architecture vision. Use this status section for submission and implementation truth.

---

## 1. System Architecture Overview

### Architecture Philosophy

ARCHE's hackathon build follows five non-negotiable architectural principles:

- **Agent-First** — Every intelligent task is performed by a specialized LLM agent, not a monolithic model
- **Simulation-Before-Recommendation** — The pipeline always simulates before it ranks
- **Memory-Backed** — All intelligence is grounded in persistent behavioral memory
- **Explainable-by-Default** — Every output includes a reasoning trace
- **Demo-Ready** — Every component must be demonstrable live on June 10

---

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     DEMO INTERFACE LAYER                          │
│        React Dashboard  |  Chat Interface  |  API Explorer       │
└───────────────────────────────┬──────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│                  LAYER 8: FastAPI + SDK Layer                     │
│   POST /simulate  |  POST /recommend  |  POST /explain           │
│   POST /ingest    |  GET /profile     |  POST /feedback          │
└───────────────────────────────┬──────────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│          LAYER 6: AGENTIC ORCHESTRATOR (LangGraph)               │
│    Parse Request → Route Agent → Sequence Pipeline → Synthesize  │
└───────┬──────────┬──────────────┬──────────────┬─────────────────┘
        │          │              │              │
   ┌────▼───┐ ┌────▼────┐  ┌─────▼────┐  ┌─────▼──────┐
   │CONTEXT │ │RETRIEVAL│  │SIMULATION│  │RECOMMEND   │
   │ AGENT  │ │  AGENT  │  │  AGENT   │  │  AGENT     │
   │(Layer 5│ │(Layer 4)│  │(Layer 1) │  │(Layer 2)   │
   │context)│ │ChromaDB)│  │LLM sim)  │  │explore)    │
   └────────┘ └─────────┘  └──────────┘  └─────┬──────┘
                                                │
                                          ┌─────▼──────┐
                                          │EXPLAINABILI│
                                          │TY AGENT    │
                                          │(Layer 3)   │
                                          └─────┬──────┘
                                                │
                                         API RESPONSE
┌──────────────────────────────────────────────────────────────────┐
│                    LAYER 4: MEMORY LAYER                          │
│  ChromaDB (vectors)  |  PostgreSQL (metadata)  |  Redis (cache)  │
└──────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│                 LAYER 5: DATA COLLECTION LAYER                    │
│         Behavioral signal ingest → Privacy abstraction           │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Full Tech Stack

| Component        | Technology                     | Why                                         |
| ---------------- | ------------------------------ | ------------------------------------------- |
| LLM              | Claude API (claude-sonnet-4-6) | Best reasoning, tool use, structured output |
| Agent Framework  | LangChain / LangGraph          | Multi-agent orchestration, ReAct support    |
| Vector Store     | ChromaDB                       | Local, fast, zero infra setup for hackathon |
| Backend API      | Python + FastAPI               | Async-native, auto-docs, high performance   |
| Task Queue       | Celery + Redis                 | Background processing, async ingestion      |
| Primary Database | PostgreSQL                     | Structured behavioral metadata storage      |
| Session Cache    | Redis                          | Session memory, hot profile caching         |
| Frontend         | React + Next.js + TailwindCSS  | Demo dashboard                              |
| Hosting          | Railway or Render              | Fast zero-ops deployment                    |
| Python SDK       | arche-sdk (local package)      | Demonstrates infrastructure capability      |
| Environment      | Python 3.11+                   | FastAPI async support                       |
| Package Manager  | pip + requirements.txt         | Simple, standard                            |

---

## 3. Repository Structure

```
arche/
├── README.md
├── requirements.txt
├── .env.example
├── docker-compose.yml
│
├── api/                          # FastAPI application
│   ├── main.py                   # App entry point
│   ├── routes/
│   │   ├── ingest.py             # POST /v1/ingest
│   │   ├── simulate.py           # POST /v1/simulate
│   │   ├── recommend.py          # POST /v1/recommend
│   │   ├── explain.py            # POST /v1/explain
│   │   ├── profile.py            # GET /v1/profile
│   │   ├── feedback.py           # POST /v1/feedback
│   │   └── health.py             # GET /v1/health
│   └── middleware/
│       ├── auth.py               # API key authentication
│       └── rate_limit.py         # Rate limiting
│
├── agents/                       # All LLM agents
│   ├── orchestrator.py           # LangGraph orchestrator
│   ├── simulation_agent.py       # User Simulation Engine
│   ├── recommendation_agent.py   # Exploration-Aware Recommender
│   ├── explainability_agent.py   # Reasoning trace generator
│   ├── retrieval_agent.py        # Memory access and retrieval
│   └── context_agent.py          # Context signal injection
│
├── memory/                       # Memory & Retrieval (Layer 4)
│   ├── vector_store.py           # ChromaDB integration
│   ├── relational_store.py       # PostgreSQL integration
│   ├── session_cache.py          # Redis session memory
│   ├── memory_manager.py         # Unified memory interface
│   └── schemas.py                # Memory data schemas
│
├── pipeline/                     # Core pipeline logic
│   ├── simulation.py             # Simulation Engine pipeline
│   ├── recommendation.py         # Recommendation pipeline
│   ├── explainability.py         # Explainability pipeline
│   └── cold_start.py             # Cold start inference
│
├── data/                         # Data layer (Layer 5)
│   ├── ingest.py                 # Signal ingestion
│   ├── privacy.py                # PII stripping, tokenization
│   ├── schemas.py                # Signal schemas
│   └── mock_catalog.py           # Demo product catalog
│
├── sdk/                          # Python SDK (Layer 8)
│   ├── __init__.py
│   ├── client.py                 # ARCHE SDK client
│   ├── models.py                 # SDK data models
│   └── exceptions.py             # SDK exceptions
│
├── dashboard/                    # React frontend
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── SimulationView.jsx
│   │   │   ├── RecommendationView.jsx
│   │   │   ├── ExplainabilityView.jsx
│   │   │   └── BusinessDashboard.jsx
│   │   └── components/
│   │       ├── ProfileCard.jsx
│   │       ├── RecommendationCard.jsx
│   │       └── ReasoningTrace.jsx
│
├── tests/
│   ├── test_simulation.py
│   ├── test_recommendation.py
│   ├── test_explainability.py
│   └── test_api.py
│
└── demo/
    ├── mock_data/                # Pre-built demo personas and catalog
    │   ├── users.json            # Demo user profiles
    │   ├── products.json         # E-commerce product catalog
    │   └── interactions.json     # Historical interaction data
    └── demo_script.md            # June 10 demo walkthrough
```

---

## 4. Data Schemas

### 4.1 Behavioral Signal Schema

```python
# data/schemas.py

from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class SessionContext(BaseModel):
    time_bucket: Literal["morning", "afternoon", "evening", "night"]
    day_type: Literal["weekday", "weekend", "holiday"]
    device_class: Literal["mobile", "desktop", "tablet"]
    network_quality: Literal["high", "medium", "low"]
    region_tier: Literal["urban", "suburban", "rural"]
    session_depth: int
    entry_point: Literal["direct", "search", "social", "referral", "notification"]

class BehavioralSignal(BaseModel):
    signal_id: str
    tenant_id: str
    user_token: str                    # SHA-256 hashed — never raw identity
    event_type: Literal["view", "click", "purchase", "dwell", "search", "exit", "save"]
    item_token: str                    # Hashed item ID
    item_category: str
    item_price_tier: Literal["budget", "mid", "premium", "luxury"]
    session_context: SessionContext
    engagement_depth: float            # 0.0 to 1.0
    dwell_time_seconds: Optional[int]
    sequence_position: int
    timestamp: datetime
```

### 4.2 Behavioral Simulation Output Schema

```python
class ContextModifiers(BaseModel):
    time_boosts: list[str]
    suppressed_categories: list[str]
    active_context: str

class BehavioralSnapshot(BaseModel):
    current_intent: Literal["exploratory_browsing", "active_purchase", "research", "entertainment"]
    preference_cluster: str
    top_affinities: list[str]
    rejection_signals: list[str]
    engagement_mode: Literal["high_depth", "scanning", "quick_check"]
    exploration_readiness: float       # 0.0 to 1.0
    purchase_probability: float        # 0.0 to 1.0

class SimulationOutput(BaseModel):
    user_token: str
    simulated_at: datetime
    behavioral_snapshot: BehavioralSnapshot
    context_modifiers: ContextModifiers
    cold_start_confidence: float
    simulation_basis: str
    memory_sources: list[str]
```

### 4.3 Recommendation Output Schema

```python
class ReasoningTrace(BaseModel):
    primary_signal: str
    context_signal: str
    exploration_factor: str
    simulation_basis: str
    why_now: str
    behavioral_state: str

class Recommendation(BaseModel):
    recommendation_id: str
    item_token: str
    item_name: str
    item_category: str
    confidence: float
    rank: int
    recommendation_type: Literal["precision", "adjacent_exploration", "discovery"]
    reasoning: ReasoningTrace
    alternatives_considered: list[str]

class RecommendationSet(BaseModel):
    user_token: str
    generated_at: datetime
    recommendations: list[Recommendation]
    diversity_score: float
    exploration_ratio: float
    cold_start_used: bool
```

---

## 5. Core Pipeline Implementation

### 5.1 Simulation Engine Pipeline

```python
# agents/simulation_agent.py

from langchain_anthropic import ChatAnthropic
from langchain.schema import SystemMessage, HumanMessage

class SimulationAgent:
    def __init__(self, memory_manager, context_agent):
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514")
        self.memory = memory_manager
        self.context = context_agent

    async def simulate(self, user_token: str, context: dict) -> SimulationOutput:
        # Step 1 — Retrieve behavioral memory
        user_memory = await self.memory.retrieve_all(user_token)
        cohort_data = await self.memory.get_cohort(user_token)

        # Step 2 — Inject context signals
        context_signals = self.context.process(context)

        # Step 3 — Handle cold start
        if user_memory.is_cold_start:
            return await self._cold_start_simulate(context_signals, cohort_data)

        # Step 4 — Generate behavioral simulation
        simulation_prompt = self._build_simulation_prompt(
            user_memory, context_signals, cohort_data
        )
        response = await self.llm.ainvoke(simulation_prompt)
        return self._parse_simulation(response)

    async def _cold_start_simulate(self, context, cohort_data):
        # Use population priors + context signals to bootstrap simulation
        prompt = self._build_cold_start_prompt(context, cohort_data)
        response = await self.llm.ainvoke(prompt)
        return self._parse_simulation(response, cold_start=True)

    def _build_simulation_prompt(self, memory, context, cohort):
        return [
            SystemMessage(content="""You are ARCHE's User Simulation Engine.
            Generate a behavioral snapshot for this user given their history and current context.
            Output must be valid JSON matching the BehavioralSnapshot schema.
            Be specific, predictive, and context-aware."""),
            HumanMessage(content=f"""
            User behavioral memory: {memory.to_dict()}
            Current context: {context}
            Population cohort data: {cohort}

            Generate a forward-looking behavioral simulation snapshot.
            Return ONLY valid JSON.""")
        ]
```

### 5.2 Recommendation Engine Pipeline

```python
# agents/recommendation_agent.py

class RecommendationAgent:
    def __init__(self, llm, catalog, memory_manager):
        self.llm = llm
        self.catalog = catalog
        self.memory = memory_manager

    async def recommend(
        self,
        simulation: SimulationOutput,
        context: dict,
        n: int = 10
    ) -> RecommendationSet:

        # Apply 60/25/15 exploration split
        n_precision = int(n * 0.60)    # 6 precision recommendations
        n_adjacent  = int(n * 0.25)    # 3 adjacent exploration
        n_discovery = n - n_precision - n_adjacent  # 1 discovery injection

        # Score catalog items against simulation snapshot
        precision_items = await self._score_precision(
            simulation.behavioral_snapshot, n_precision
        )
        adjacent_items = await self._score_adjacent(
            simulation.behavioral_snapshot, n_adjacent
        )
        discovery_items = await self._inject_discovery(
            simulation.behavioral_snapshot, n_discovery
        )

        # Combine and apply diversity penalty
        all_items = precision_items + adjacent_items + discovery_items
        diversified = self._apply_diversity_penalty(all_items)

        # Apply context modifiers
        contextualized = self._apply_context(diversified, simulation.context_modifiers)

        return RecommendationSet(
            user_token=simulation.user_token,
            recommendations=contextualized,
            diversity_score=self._calculate_diversity(contextualized),
            exploration_ratio=(n_adjacent + n_discovery) / n,
            cold_start_used=simulation.cold_start_confidence > 0.5
        )

    def _apply_diversity_penalty(self, items):
        # Mathematical penalty for over-clustering of similar categories
        seen_categories = {}
        penalized = []
        for item in items:
            category_count = seen_categories.get(item.category, 0)
            penalty = 0.1 * category_count  # 10% penalty per repeat category
            item.confidence = item.confidence * (1 - penalty)
            seen_categories[item.category] = category_count + 1
            penalized.append(item)
        return sorted(penalized, key=lambda x: x.confidence, reverse=True)
```

### 5.3 Explainability Pipeline

```python
# agents/explainability_agent.py

class ExplainabilityAgent:
    def __init__(self, llm):
        self.llm = llm

    async def explain(
        self,
        recommendation: Recommendation,
        simulation: SimulationOutput,
        context: dict
    ) -> Recommendation:

        explanation_prompt = [
            SystemMessage(content="""You are ARCHE's Explainability Agent.
            Generate a complete, honest, causal reasoning trace for this recommendation.
            Do not rationalize post-hoc. Derive the explanation from the simulation data.
            Output ONLY valid JSON matching the ReasoningTrace schema."""),
            HumanMessage(content=f"""
            Recommendation: {recommendation.item_name} ({recommendation.item_category})
            Confidence: {recommendation.confidence}
            Recommendation type: {recommendation.recommendation_type}

            Behavioral simulation: {simulation.behavioral_snapshot.dict()}
            Context: {context}
            Memory sources: {simulation.memory_sources}

            Generate the reasoning trace. Be specific, honest, and complete.
            Include: primary_signal, context_signal, exploration_factor,
            simulation_basis, why_now, behavioral_state.""")
        ]

        response = await self.llm.ainvoke(explanation_prompt)
        reasoning = self._parse_reasoning(response)
        recommendation.reasoning = reasoning
        return recommendation
```

### 5.4 LangGraph Orchestrator

```python
# agents/orchestrator.py

from langgraph.graph import StateGraph, END
from typing import TypedDict

class ARCHEState(TypedDict):
    user_token: str
    context: dict
    user_memory: dict
    simulation: dict
    recommendations: list
    explained_recommendations: list
    error: str

def build_arche_graph():
    graph = StateGraph(ARCHEState)

    # Add all agent nodes
    graph.add_node("retrieve_memory",    retrieve_memory_node)
    graph.add_node("inject_context",     inject_context_node)
    graph.add_node("simulate_user",      simulate_user_node)
    graph.add_node("generate_recs",      generate_recommendations_node)
    graph.add_node("explain_recs",       explain_recommendations_node)
    graph.add_node("security_check",     security_check_node)

    # Define pipeline flow
    graph.set_entry_point("retrieve_memory")
    graph.add_edge("retrieve_memory",  "inject_context")
    graph.add_edge("inject_context",   "simulate_user")
    graph.add_edge("simulate_user",    "generate_recs")
    graph.add_edge("generate_recs",    "explain_recs")
    graph.add_edge("explain_recs",     "security_check")
    graph.add_edge("security_check",   END)

    return graph.compile()

arche_pipeline = build_arche_graph()
```

---

## 6. API Specification

### Full Endpoint Reference

```
Base URL: http://localhost:8000/v1  (dev)
         https://arche-api.railway.app/v1  (deployed)

Authentication: X-API-Key: your_api_key (header)
```

#### POST /v1/ingest

```json
// Request
{
  "user_token": "sha256_hashed_id",
  "event_type": "view",
  "item_category": "fashion",
  "item_price_tier": "mid",
  "session_context": {
    "time_bucket": "evening",
    "device_class": "mobile",
    "region_tier": "urban",
    "session_depth": 2,
    "day_type": "weekday",
    "network_quality": "high",
    "entry_point": "social"
  },
  "engagement_depth": 0.65,
  "dwell_time_seconds": 38
}

// Response
{
  "signal_id": "uuid",
  "accepted": true,
  "queued_at": "2026-05-11T19:34:22Z"
}
```

#### POST /v1/simulate

```json
// Request
{
  "user_token": "sha256_hashed_id",
  "context": {
    "time_bucket": "evening",
    "device_class": "mobile",
    "region_tier": "urban"
  }
}

// Response
{
  "user_token": "sha256_hashed_id",
  "behavioral_snapshot": {
    "current_intent": "exploratory_browsing",
    "preference_cluster": "7B",
    "top_affinities": ["fashion", "home_goods"],
    "rejection_signals": ["luxury", "gaming"],
    "exploration_readiness": 0.72,
    "purchase_probability": 0.41
  },
  "cold_start_confidence": 0.88,
  "simulation_basis": "cohort_7B + evening_mobile_context"
}
```

#### POST /v1/recommend

```json
// Request
{
  "user_token": "sha256_hashed_id",
  "n": 10,
  "context": {
    "time_bucket": "evening",
    "device_class": "mobile",
    "region_tier": "urban"
  }
}

// Response
{
  "user_token": "sha256_hashed_id",
  "diversity_score": 0.73,
  "exploration_ratio": 0.40,
  "cold_start_used": false,
  "recommendations": [
    {
      "recommendation_id": "uuid",
      "item_name": "Ankara Print Tote Bag",
      "item_category": "fashion",
      "confidence": 0.87,
      "rank": 1,
      "recommendation_type": "precision",
      "reasoning": {
        "primary_signal": "Cluster 7B: fashion + home goods affinity across 3 sessions",
        "context_signal": "Evening mobile boosts fashion category by 34%",
        "exploration_factor": "Precision recommendation — within core preference cluster",
        "simulation_basis": "Short-term memory + cohort 7B priors",
        "why_now": "Trending +38% in cohort this week",
        "behavioral_state": "High engagement mode — deep browse session"
      },
      "alternatives_considered": [
        "Item B: rejected — too similar to last viewed",
        "Item C: rejected — luxury tier mismatch with budget signal"
      ]
    }
  ]
}
```

---

## 7. Memory Architecture Implementation

```python
# memory/memory_manager.py

import chromadb
import redis
from sqlalchemy import create_engine

class MemoryManager:
    def __init__(self):
        # Vector store — behavioral embeddings
        self.vector_client = chromadb.Client()
        self.behavioral_collection = self.vector_client.get_or_create_collection(
            name="behavioral_embeddings"
        )

        # Session cache — short-term memory
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

        # Relational — structured metadata
        self.db = create_engine("postgresql://user:pass@localhost/arche")

    async def retrieve_all(self, user_token: str) -> UserMemory:
        session   = await self._get_session_memory(user_token)
        medium    = await self._get_medium_term(user_token)
        long_term = await self._get_long_term_vectors(user_token)
        cohort    = await self._get_cohort_priors(user_token)

        is_cold_start = (session is None and medium is None and long_term is None)

        return UserMemory(
            session_memory=session,
            medium_term=medium,
            long_term_vectors=long_term,
            cohort_priors=cohort,
            is_cold_start=is_cold_start
        )

    async def _get_long_term_vectors(self, user_token: str):
        results = self.behavioral_collection.query(
            query_texts=[user_token],
            n_results=20
        )
        return results

    async def update(self, user_token: str, signal: BehavioralSignal):
        # Update all memory layers after new signal
        await self._update_session(user_token, signal)
        await self._update_medium_term(user_token, signal)
        await self._update_vector_embedding(user_token, signal)
        await self._check_cohort_membership(user_token)
```

---

## 8. Privacy Implementation

```python
# data/privacy.py

import hashlib
import re

class PrivacyLayer:

    PII_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{10,11}\b',                                            # Phone
        r'\b[A-Z]{2}\d{6,9}\b',                                     # ID numbers
    ]

    def anonymize_user_token(self, raw_identifier: str) -> str:
        """Convert any user identifier to anonymous token — non-reversible"""
        return hashlib.sha256(raw_identifier.encode()).hexdigest()

    def strip_pii(self, text: str) -> str:
        """Remove any accidentally included PII from signal text fields"""
        for pattern in self.PII_PATTERNS:
            text = re.sub(pattern, '[REDACTED]', text)
        return text

    def abstract_signal(self, raw_signal: dict) -> BehavioralSignal:
        """
        Convert raw interaction data to privacy-safe behavioral signal.

        Input:  { "user_id": "ada.okonkwo@email.com", "product": "Red Ankara Bag", ... }
        Output: { "user_token": "sha256hash...", "item_token": "sha256hash...",
                  "item_category": "fashion", "engagement_depth": 0.7, ... }
        """
        return BehavioralSignal(
            user_token=self.anonymize_user_token(raw_signal["user_id"]),
            item_token=self.anonymize_user_token(raw_signal["product_id"]),
            item_category=raw_signal["category"],   # Category only — not specific product
            # ... map remaining fields
        )
```

---

## 9. Dashboard — Key UI Components

### SimulationView.jsx

Shows the behavioral simulation running live:

- User profile card (behavioral cluster, top affinities, intent)
- Simulation progress indicator
- Context signals being injected (time, device, region)
- Cold start confidence score
- Memory sources being retrieved

### RecommendationView.jsx

Shows the recommendation output:

- 10 recommendation cards with item name, confidence, type badge (precision/exploration/discovery)
- Exploration ratio indicator (60/25/15 split visualization)
- Diversity score gauge
- Each card expandable to show full reasoning trace

### ExplainabilityView.jsx

Full reasoning trace panel:

- Primary signal explanation
- Context signal
- Exploration factor
- Why now
- Alternatives considered with rejection reasons

### BusinessDashboard.jsx

SME owner view:

- Customer behavioral segments map
- Recommendation acceptance rate over time
- Top recommended categories by segment
- Cold start resolution rate

---

## 10. 17-Day Development Plan

### Day-by-Day Schedule

---

#### DAY 1 — Setup & Foundation

**All team**

- [ ] GitHub repo created, branching strategy agreed
- [ ] `.env.example` created with all required keys
- [ ] `docker-compose.yml` — PostgreSQL, Redis, ChromaDB
- [ ] Database schema designed and migrations written
- [ ] FastAPI skeleton with health endpoint live
- [ ] Claude API key tested and working
- [ ] LangChain / LangGraph installed and hello-world agent running
- [ ] Team sync: architecture walkthrough, everyone aligned

**End of day target:** `GET /v1/health` returns 200. All services running.

---

#### DAY 2 — Memory Layer

**AI Engineer + Backend Dev**

- [ ] ChromaDB collection setup — `behavioral_embeddings`
- [ ] PostgreSQL tables: `users`, `signals`, `sessions`, `cohorts`
- [ ] Redis session cache connection and basic get/set
- [ ] `MemoryManager` class — `retrieve_all()`, `update()` methods
- [ ] All 4 memory layers reading and writing correctly
- [ ] Unit tests for memory layer

**End of day target:** Can store and retrieve behavioral signals from all memory layers.

---

#### DAY 3 — Data Collection & Privacy Layer

**Backend Dev**

- [ ] `BehavioralSignal` Pydantic schema
- [ ] `PrivacyLayer` class — `anonymize_user_token()`, `strip_pii()`, `abstract_signal()`
- [ ] `POST /v1/ingest` endpoint working
- [ ] Signal validation and error handling
- [ ] Mock data generator — create 3 demo user profiles + 50-item product catalog
- [ ] `demo/mock_data/` populated with realistic e-commerce data

**End of day target:** `POST /v1/ingest` accepts signals and stores them correctly.

---

#### DAYS 4–5 — User Simulation Engine (Core Build)

**AI Engineer**

Day 4:

- [ ] `SimulationAgent` class skeleton
- [ ] System prompt engineering for behavioral simulation
- [ ] `_build_simulation_prompt()` — takes memory + context → generates LLM prompt
- [ ] Simulation output parser — LLM response → `SimulationOutput` schema
- [ ] Test simulation with mock user data

Day 5:

- [ ] Simulation quality testing — outputs are coherent and useful
- [ ] Prompt refinement — better behavioral snapshots
- [ ] Edge case handling — partial memory, old memory
- [ ] `POST /v1/simulate` endpoint wired to Simulation Agent

**End of day target:** `POST /v1/simulate` returns a coherent `SimulationOutput` for a returning user.

---

#### DAY 6 — Cold Start System

**AI Engineer**

- [ ] `_cold_start_simulate()` method in Simulation Agent
- [ ] Population cohort priors — build 5 behavioral clusters from mock data
- [ ] Context-only inference — device + time + region → cluster mapping
- [ ] `cold_start_confidence` score calculation
- [ ] Test: new user with zero history still gets meaningful simulation

**End of day target:** New user simulation produces coherent behavioral snapshot with confidence > 0.7.

---

#### DAYS 7 — Recommendation Engine

**AI Engineer**

- [ ] `RecommendationAgent` class
- [ ] Catalog scoring against simulation snapshot
- [ ] 60/25/15 split implementation — precision/adjacent/discovery
- [ ] Diversity penalty algorithm
- [ ] Context modifiers applied to final ranking
- [ ] `POST /v1/recommend` endpoint wired

**End of day target:** Full recommendation set returned with correct exploration split.

---

#### DAY 8 — Explainability System

**AI Engineer**

- [ ] `ExplainabilityAgent` class
- [ ] Explanation prompt engineering — causal, specific, honest
- [ ] `ReasoningTrace` output parser
- [ ] Alternatives considered generation
- [ ] `POST /v1/explain` endpoint wired
- [ ] Quality check — explanations are genuinely informative, not generic

**End of day target:** Every recommendation has a complete, honest, specific reasoning trace.

---

#### DAY 9 — LangGraph Orchestrator

**AI Engineer + Backend Dev**

- [ ] `ARCHEState` TypedDict defined
- [ ] All agent nodes wired into LangGraph graph
- [ ] Pipeline flow: retrieve → context → simulate → recommend → explain → security
- [ ] Error handling and fallback paths
- [ ] Orchestrator tested end-to-end

**End of day target:** Single `arche_pipeline.invoke()` call executes full pipeline correctly.

---

#### DAY 10 — Multi-Agent Integration & Context Agent

**AI Engineer + Backend Dev**

- [ ] `ContextAgent` class — time/device/region signal processing
- [ ] Context modifiers calculated and injected into simulation
- [ ] Time-of-day demo: same user → morning recommendations vs evening recommendations visible
- [ ] All agents communicating through orchestrator correctly
- [ ] Agent error isolation — one agent failure doesn't crash pipeline

**End of day target:** Time-of-day context visibly changes recommendations for same user.

---

#### DAY 11 — FastAPI Endpoints Polish

**Backend Dev**

- [ ] All endpoints complete: /ingest, /simulate, /recommend, /explain, /profile, /feedback, /health
- [ ] Request validation on all endpoints
- [ ] Error responses — proper HTTP codes and messages
- [ ] API authentication — X-API-Key header validation
- [ ] Auto-generated API docs at `/docs` working
- [ ] Load test: endpoints handle concurrent requests without errors

**End of day target:** All 7 endpoints working correctly with proper validation and auth.

---

#### DAY 12 — Python SDK

**Backend Dev**

- [ ] `sdk/client.py` — `ARCHE` class with all methods
- [ ] `sdk/models.py` — SDK data models matching API schemas
- [ ] Methods: `ingest()`, `simulate()`, `recommend()`, `explain()`, `feedback()`
- [ ] Async support throughout
- [ ] SDK quickstart example working
- [ ] SDK documented with docstrings

**End of day target:** SDK quickstart example runs and returns recommendations.

---

#### DAY 13 — Dashboard Frontend

**Fullstack Dev**

- [ ] React + Next.js project setup with Tailwind
- [ ] `SimulationView` — behavioral snapshot visualization
- [ ] `RecommendationView` — 10 recommendation cards with confidence and type badges
- [ ] `ExplainabilityView` — full reasoning trace panel
- [ ] `BusinessDashboard` — SME owner analytics view
- [ ] API integration — all views connected to live FastAPI backend
- [ ] Deployed to Vercel

**End of day target:** Full demo dashboard accessible at public URL.

---

#### DAY 14 — Demo Preparation & Polish

**All team**

- [ ] 3 demo personas prepared with realistic data:
  - Ada: new user (cold start demo)
  - Chidi: returning user (3 sessions)
  - Ngozi: power user (10+ sessions, preference drift)
- [ ] E-commerce product catalog polished — real Nigerian product names and categories
- [ ] SME business catalog prepared
- [ ] Context demo: morning vs evening recommendations visually compelling
- [ ] All UI components polished — no broken layouts, professional appearance
- [ ] Demo flow rehearsed once

**End of day target:** Full demo flow completed without errors in < 7 minutes.

---

#### DAY 15 — End-to-End Integration Testing

**All team**

- [ ] Full pipeline tested with all 3 demo personas
- [ ] Cold start → returning user transition tested
- [ ] Explainability quality reviewed — all traces genuinely informative
- [ ] Diversity scores verified — exploration ratio visible in output
- [ ] SDK demo working live
- [ ] Edge cases handled: empty catalog, API errors, slow LLM response
- [ ] Performance: full pipeline < 3 seconds end-to-end

**End of day target:** Full demo runs without errors. All edge cases handled.

---

#### DAY 16 — Bug Fixes, Polish & Submission Package

**All team**

- [ ] All bugs identified in Day 15 fixed
- [ ] UI final polish pass
- [ ] Submission document prepared (README, project description, demo link)
- [ ] Backup demo recording made (screen record full demo flow)
- [ ] Demo rehearsal #2 — all team members can explain their layers
- [ ] Submission package uploaded before deadline

**End of day target:** Submission complete. Everything working. Backup ready.

---

#### DAY 17 — Dry Run & June 10 Preparation

**All team**

- [ ] Full demo dry run — timed at 7 minutes
- [ ] Q&A preparation — anticipated judge questions and answers
- [ ] Architecture diagram ready for technical questions
- [ ] Backup demo (recording) ready in case of live failure
- [ ] All team members briefed on their speaking roles for June 10
- [ ] Travel / logistics for Eko Hotel confirmed

**End of day target:** Team confident, demo polished, ready for June 10.

---

## 11. Performance Targets

| Metric                         | Target                                |
| ------------------------------ | ------------------------------------- |
| Full pipeline latency (p50)    | < 2 seconds                           |
| Full pipeline latency (p99)    | < 4 seconds                           |
| API endpoint latency           | < 500ms for cached profiles           |
| Cold start simulation          | < 3 seconds                           |
| Recommendation diversity score | > 0.5                                 |
| Explainability completeness    | 100% — every recommendation explained |
| Exploration ratio              | 35–40% of recommendations             |

---

## 12. Risk Register & Mitigations

| Risk                               | Probability | Impact | Mitigation                                                                         |
| ---------------------------------- | ----------- | ------ | ---------------------------------------------------------------------------------- |
| LLM API slow during live demo      | Medium      | High   | Pre-cache simulation outputs for all 3 demo personas                               |
| Scope too ambitious — not finished | Medium      | High   | Core 3 layers are non-negotiable. Everything else is enhancement. Ship core first. |
| LangGraph complexity delays build  | Medium      | Medium | Day 9 has buffer. If needed, replace LangGraph with simple sequential pipeline.    |
| Demo breaks live on stage          | Low         | High   | Full backup screen recording ready. Practice failover narrative.                   |
| ChromaDB slow on Railway           | Low         | Medium | Pre-warm embeddings before demo. Use Redis cache as first check.                   |
| Dashboard not polished enough      | Medium      | Medium | Fullstack Dev focuses 100% on dashboard Days 13–16.                                |

---

## 13. Team Responsibilities

| Team Member   | Primary Layers                                                                                 | Secondary                      |
| ------------- | ---------------------------------------------------------------------------------------------- | ------------------------------ |
| AI Engineer   | L1 (Simulation), L2 (Recommendation), L3 (Explainability), L6 (Orchestrator), L7 (Multi-Agent) | Code review on L4, L5          |
| Backend Dev   | L4 (Memory), L5 (Privacy), L8 (SDK + API), Database, Deployment                                | Support L6 orchestrator wiring |
| Fullstack Dev | Demo Dashboard, API integration, UI/UX, demo data preparation                                  | Support L8 SDK documentation   |

---

## 14. June 10 Demo Script

### Opening (30 seconds)

_"Modern recommendation systems are broken. They're static, context-blind, and operate as black boxes. ARCHE is the infrastructure that fixes this — through behavioral simulation, exploration-aware ranking, and complete explainability. Let us show you."_

### Act 1 — Cold Start (90 seconds)

- Open dashboard — New user: Ada. Zero history.
- "Ada just arrived. No purchase history. Most systems show generic popular items."
- "ARCHE's Simulation Engine activates — inferring from her device, time, location."
- Show simulation running — behavioral snapshot appears
- "She's mapped to behavioral cluster 7B. Evening mobile session boosts fashion."
- Show 10 personalized recommendations appear
- "First session. Zero history. Genuinely personalized."

### Act 2 — Returning User + Context (90 seconds)

- Switch to Chidi — returning user, 3 sessions
- Show his behavioral profile — cluster, affinities, evolution
- "Watch what happens when we change the context — it's now morning."
- Toggle time context → recommendations change visibly
- "Same user. Different time. Different intent. Different recommendations."
- Show exploration split: 6 precision, 3 adjacent, 1 discovery

### Act 3 — Explainability (60 seconds)

- Click on recommendation #1
- Full reasoning trace expands
- "Why did ARCHE recommend this? Primary signal: Cluster 7B fashion affinity. Context: Evening mobile boosts fashion 34%. Exploration: Item is 23% outside core cluster — discovery injection. Why now: Trending 38% in cohort this week."
- "Every recommendation. Fully explained. Always."

### Act 4 — Business Dashboard (60 seconds)

- Switch to SME owner view
- Show customer segments, recommendation acceptance rate, diversity scores
- "This is what the business sees. Customer intelligence. Not a black box."

### Act 5 — Infrastructure Proof (60 seconds)

- Open API explorer — live call to `/v1/recommend`
- Show JSON response with recommendations + reasoning
- "This is infrastructure. Any African enterprise plugs in with one API key."
- Show SDK quickstart — 5 lines of Python

### Close (30 seconds)

_"ARCHE is not a recommendation chatbot. It is the intelligence layer that simulates who your customers are, recommends what they actually need, and tells you exactly why — built as infrastructure for African enterprises. BCT can deploy this for their clients tomorrow."_

---

_ARCHE System Architecture & Development Plan v1.0 — DSN x BCT LLM Agent Challenge 3.0 — Confidential_
