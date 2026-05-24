# ARCHE — HackAlign Document

## DSN x BCT LLM Agent Challenge 3.0 — Full Alignment & Build Reference

---

> **Purpose:** This document is the single source of truth for how ARCHE aligns with the official hackathon brief, how we resolved every gap, how we will build Nigerian + global context into the system, and what every team member must do day by day. Read this before writing a single line of code.

---

## Document Metadata

| Field               | Detail                                                                  |
| ------------------- | ----------------------------------------------------------------------- |
| Document            | HackAlign v1.0                                                          |
| Hackathon           | DSN x BCT LLM Agent Challenge 3.0                                       |
| Submission Deadline | May 24, 2026 — midnight, no extensions                                  |
| Grand Finale        | June 10, 2026 — Eko Hotel, Lagos                                        |
| Team Eligibility    | ✅ Confirmed — all members are enrolled students                        |
| Tasks               | Both Task A (User Modeling) AND Task B (Recommendation) — both required |
| Dataset             | Yelp Open Dataset (primary)                                             |
| Deliverables        | 3 required: Containerized App + Solution Paper + GitHub Repo            |

---

## PART 1 — Official Brief Alignment

### 1.1 What The Brief Actually Asks For

The competition has two tasks. Both are required. A team submitting only one is disqualified.

**Task A — User Modeling Agent**

> Build an agent that understands users deeply enough to simulate their reviews — capturing tone, rating behaviour, and contextual nuance.

In plain English:

- Input: A user's history + an item they have never reviewed
- Output: A predicted star rating (1–5) + a written review in that user's voice
- Evaluated on: Review text quality (ROUGE/BERTScore), Rating accuracy (RMSE), Behavioural fidelity (human eval)

**Concrete Example:**

```
Input:
  User: Emeka
  History: [3 past restaurant reviews with ratings and text]
  Unseen Item: Domino's Pizza Lagos

Output:
  Predicted Rating: 3 stars
  Generated Review: "Domino's is aight but nothing special.
  The pizza came hot which I appreciate but for that price
  I could just hit Chicken Republic. Not bad sha,
  would go again if I'm in the area."
```

**Task B — Recommendation Agent**

> Build an agent that delivers personalised recommendations — going beyond collaborative filtering to contextual, conversational retrieval.

In plain English:

- Input: A user's behavioral history / persona
- Output: Top-10 ranked personalized recommendations with reasoning
- Evaluated on: NDCG@10/Hit Rate (30pts), Cold-Start (25pts), Contextual Relevance (20pts), Solution Paper (15pts), Code Reproducibility (10pts)

**Concrete Example:**

```
Input:
  User: Emeka (3 past reviews, evening session, Lagos Mainland)

Output:
  1. The Place Restaurant (0.91) — Nigerian cuisine, value-conscious match
  2. Bukka Hut (0.87) — Authentic local, matches flavor preference
  3. Yellow Chilli (0.84) — Mid-price, strong portion signal
  ... (10 total, each with reasoning)
```

---

### 1.2 How The Two Tasks Connect Through ARCHE

This is our architectural advantage. Other teams build two separate systems. We build one shared brain:

```
SHARED BRAIN: User Simulation Engine
       ↓                    ↓
  Task A Output         Task B Output

"What would Emeka      "What should Emeka
 write about this?"     see next?"
```

The same behavioral simulation that grounds review generation also grounds recommendation ranking. One architecture. Two outputs. One story.

---

### 1.3 Scoring Rubric — Full Breakdown

**Task A — User Modeling (qualitative evaluation)**

| Criterion                             | What Judges Measure                                               |
| ------------------------------------- | ----------------------------------------------------------------- |
| Review Text Quality (ROUGE/BERTScore) | Does generated text match actual review vocabulary and structure? |
| Rating Accuracy (RMSE)                | How close is predicted star rating to actual rating?              |
| Behavioural Fidelity (human eval)     | Does it sound like this specific user?                            |
| Solution Paper                        | Clarity of approach, originality, experimental rigor              |
| Code Reproducibility                  | Can judges run it? Is it clean and documented?                    |

**Task B — Recommendation (100-point rubric)**

| Criterion                            | Points | What Judges Measure                                |
| ------------------------------------ | ------ | -------------------------------------------------- |
| Ranking Quality (NDCG@10 / Hit Rate) | 30     | Are the right items ranked correctly?              |
| Cold-Start & Cross-Domain            | 25     | Does it work with sparse/new user history?         |
| Contextual Relevance (human eval)    | 20     | Do recommendations feel situationally appropriate? |
| Solution Paper                       | 15     | Architecture understanding, experiments, ablation  |
| Code Reproducibility                 | 10     | Clean repo, README, runnable Docker container      |

**Nigerian Bonus:** Additional marks for agents that behave and sound like Nigerians. Explicitly stated in brief. Most teams will miss this.

---

### 1.4 Three Required Deliverables

**Deliverable 1 — Containerized Application (Agent Link)**

- Docker containerized FastAPI application
- Task A endpoint: `POST /simulate-review` — takes user persona + item → returns rating + review
- Task B endpoint: `POST /recommend` — takes user persona → returns ranked recommendations
- Must run with `docker-compose up` — judges will attempt to run it

**Implementation mapping in ARCHE**

- Task A is served by `POST /v1/simulate-review`
- Task B is served by `POST /v1/recommend`
- Explanation traces are served by `POST /v1/explain`
- The frontend demo uses the same backend API, so judges can see the recommendation flow visually while still having direct API access for both tasks
- Task A can be exercised directly through the API endpoint or by wiring a form in the webapp; the backend contract is already aligned either way

**Deliverable 2 — Solution Paper (4–8 pages)**

- Approach, architecture decisions, experiments, ablation studies
- What could be done with more time
- Judges read this FIRST — it is the primary talent signal
- Originality and clarity rewarded above raw performance
- Write Days 15–17 using actual evaluation numbers from the working system

**Deliverable 3 — GitHub Repository**

- Clean, documented, reproducible codebase
- Clear README with setup instructions
- Well-commented agentic workflow logic
- Modular design — judges reward this explicitly
- Bonus credit for clear README and modular design

---

## PART 2 — Gap Analysis & Resolutions

### GAP 1 — Eligibility ✅ RESOLVED

**Issue:** Competition is student-only (Undergraduate, Postgraduate, PhD)
**Resolution:** All team members confirmed as enrolled students. No action required.

---

### GAP 2 — Two Tasks Required ✅ RESOLVED

**Issue:** Our original plan focused primarily on recommendation (Task B). Brief requires BOTH tasks.

**Resolution:**
Added `ReviewGenerationAgent` as a new core component. It sits downstream of the Simulation Engine and generates star ratings + written reviews for Task A. The simulation engine powers both tasks — architectural change is additive, not structural.

**Endpoint alignment:**

- `POST /v1/simulate-review` accepts user persona + item details and returns the review/rating output expected by Task A
- `POST /v1/recommend` accepts user persona + context and returns ranked recommendations expected by Task B
- `POST /v1/explain` provides the reasoning trace judges expect to see in an agentic system

**New component added to ARCHE:**

```
ReviewGenerationAgent
  Input:  SimulationOutput + unseen item details
  Process: LLM generates rating prediction + review text
           grounded in behavioral snapshot
  Output: { predicted_rating: int, generated_review: str,
            tone_confidence: float, behavioural_basis: str }
```

---

### GAP 3 — Real Datasets Required ✅ RESOLVED

**Issue:** We planned mock data. Brief specifies Yelp, Amazon Reviews, or Goodreads.

**Resolution:** Use Yelp Open Dataset as primary. See Part 3 for full data pipeline.

**Why Yelp:**

- Food/restaurant domain — closest to Nigerian daily life context
- Rich review text — ideal for Task A review simulation
- Strong behavioral signals — repeat visits, ratings, categories
- Judges are Nigerian — food resonates immediately in demo
- Freely available at `yelp.com/dataset`

---

### GAP 4 — Docker Containerization Required ✅ RESOLVED

**Issue:** Submission must be containerized. Docker was dev tooling in our original plan.

**Resolution:** Docker is now a Day 1 priority. Entire application must run with `docker-compose up`. See Part 4 for updated architecture.

---

### GAP 5 — Solution Paper Required ✅ RESOLVED

**Issue:** 4–8 page academic-style solution paper not in original plan.

**Resolution:** Solution paper is now a formal deliverable. Written Days 15–17 using real evaluation numbers. Structure defined in Part 5.

---

### GAP 6 — Nigerian Contextualization ✅ RESOLVED

**Issue:** Bonus marks for Nigerian-calibrated behavior not explicitly planned.

**Resolution:** Approach C adopted — dataset extraction + prompt calibration + few-shot examples. See Part 3 for full Nigerian context strategy.

### GAP 7 — Webapp + API Submission Shape ✅ RESOLVED

**Issue:** The brief allows either a web application or an API endpoint for each task, so the submission must clearly explain how judges use both.

**Resolution:**

- The backend API is the canonical judge-facing contract for both tasks
- The webapp provides the interactive demo for recommendations and explanation traces
- The README and submission package now explain that Task A is available through the API endpoint, while Task B is visible in both API and webapp flows

---

## PART 3 — Nigerian + Global Context Strategy

### 3.1 The Core Architectural Principle

```
Behavioral signals are universal.
Cultural calibration is a layer on top.

ARCHE models behavior first.
Nigerian / global context is injected
at the prompt calibration layer —
not baked into the core architecture.
```

This keeps ARCHE domain-agnostic at the infrastructure level (long-term product vision) while delivering culturally relevant outputs at the surface level (hackathon scoring).

---

### 3.2 Approach — What We Chose and Why

We adopt **Approach C: Dataset-Driven Behavioral Learning + Prompt Calibration + Few-Shot Examples.**

**We do NOT fine-tune any models.** The bonus marks are not worth the compute time and complexity risk within 17 days. Well-crafted prompts grounded in real extracted behavioral data will score the bonus and leave the team time to build the core system properly.

```
Layer 1: Real Nigerian behavioral data extracted from Yelp dataset
         → builds accurate Nigerian behavioral cohort priors

Layer 2: Nigerian few-shot review examples extracted from real data
         → injected into LLM prompts as concrete style anchors

Layer 3: Nigerian cultural context calibration in system prompts
         → time patterns, price sensitivity, language register

Result: Reviews that sound like specific Nigerian users,
        not just "a Nigerian user" in general
```

---

### 3.3 Nigerian Context — What We Model

**Geographic Tiers:**

- Lagos (Island: Lekki, VI, Ikoyi) — premium, quality-focused, global exposure
- Lagos (Mainland: Surulere, Yaba, Ikeja) — value-conscious, practical, tech-aware
- Abuja — government/professional, mid-to-premium, formal register
- Port Harcourt — oil-sector influence, quality expectations
- Pan-Nigerian default — universal Nigerian behavioral signals

**Behavioral Signals We Extract From Data:**

- Rating distributions by category (Nigerians tend to polarize — very high or very low)
- Review length patterns (Nigerian reviews tend to be shorter and more direct)
- Complaint patterns (service speed, portions, value-for-money dominate)
- Praise patterns (taste, atmosphere, staff friendliness)
- Price sensitivity signals (explicit value comparisons common)
- Time patterns (evening surge post-traffic, owambe weekend patterns)

**Language Register Detection:**

```python
NIGERIAN_REGISTERS = {
    "formal_english": "The service was excellent and the food was well-prepared.",
    "nigerian_english": "The food was very okay, the service too was good sha.",
    "mixed_pidgin": "E be like say the chef sabi work, the suya was mad.",
    "casual_pidgin": "Abeg this place na 5 star, I no go lie, e too do."
}
```

The Simulation Engine detects which register a specific user writes in from their history, then the ReviewGenerationAgent matches that register in generated reviews.

---

### 3.4 Global Context — What We Model

The Yelp dataset is globally sourced. We do not force Nigerian context on non-Nigerian users. Instead:

```
Global behavioral clusters extracted from full dataset:
- Cluster A: Value-conscious users (price-to-quality focus)
- Cluster B: Quality-first users (premium, consistency focus)
- Cluster C: Experience-seekers (ambiance, novelty, discovery)
- Cluster D: Practical users (speed, reliability, convenience)
- Cluster E: Social users (group dining, event-driven choices)
```

These clusters transcend nationality. A Nigerian value-conscious user and a South African value-conscious user share behavioral DNA. Cultural calibration is applied on top of cluster membership — not instead of it.

---

### 3.5 Nigerian Prompt Calibration — Implementation

**System prompt addition for ReviewGenerationAgent:**

```python
NIGERIAN_REVIEW_CALIBRATION = """
NIGERIAN USER CONTEXT:
This user exhibits Nigerian behavioral patterns. Calibrate accordingly:

Language: Match the specific register found in this user's history.
Possible registers:
  - Formal Nigerian English: grammatically standard, Nigerian idioms
  - Nigerian English: "very okay", "too much", "sha", "sef", "abi"
  - Code-switched: English mixed with Yoruba/Igbo/Hausa phrases naturally
  - Pidgin-mixed: "e be like say", "na im be that", "abeg", "oga"

Value signals: Nigerian users frequently reference price-to-value ratio.
If the user shows price sensitivity, reflect this explicitly in the review.

Portion/quantity: Reference to food quantity is culturally significant.
Service pace: Traffic context affects patience with service speed.
Community: Reference to "my people", bringing others, recommending to friends.

CRITICAL: Do not use generic Nigerian stereotypes.
Match THIS USER'S specific tone from their history.
The Nigerian context is background calibration, not foreground performance.
"""
```

**System prompt addition for RecommendationAgent:**

```python
NIGERIAN_RECOMMENDATION_CALIBRATION = """
NIGERIAN BEHAVIORAL CONTEXT:
Apply these Nigerian-specific recommendation signals:

Time patterns:
  - Evening (6pm-10pm): Post-traffic, comfort food, relaxation preference
  - Weekend afternoons: Owambe/social dining, group settings
  - Weekday lunch: Speed and value prioritized, proximity matters

Location sensitivity:
  - Lagos Island users: Premium options appropriate
  - Mainland users: Value + quality balance preferred
  - Consider traffic patterns in proximity recommendations

Price calibration:
  - Apply Nigerian economic context to price tier signals
  - Value-consciousness is the dominant signal for 70%+ of users

Social context:
  - Nigerians frequently dine in groups
  - Recommendations for "a good spot for the boys/girls" are valid contexts
"""
```

---

### 3.6 Few-Shot Examples Strategy

Extract 15–20 real Nigerian-sounding reviews from the Yelp dataset during data preprocessing. Use these as few-shot examples in prompts:

```python
# data/nigerian_fewshot_extractor.py

def extract_nigerian_fewshot_examples(reviews_df, n=20):
    """
    Extract reviews that exhibit Nigerian language patterns.
    Look for: Nigerian English markers, pidgin phrases,
    Nigerian food references, cultural context signals.
    """
    nigerian_markers = [
        "sha", "abi", "sef", "abeg", "na im", "e be like",
        "very okay", "too much", "jollof", "suya", "eba",
        "egusi", "pepper soup", "naija", "9ja"
    ]

    nigerian_reviews = []
    for _, review in reviews_df.iterrows():
        text = review['text'].lower()
        marker_count = sum(1 for m in nigerian_markers if m in text)
        if marker_count >= 2:
            nigerian_reviews.append({
                'text': review['text'],
                'rating': review['stars'],
                'category': review['category'],
                'markers_found': marker_count
            })

    return sorted(nigerian_reviews,
                  key=lambda x: x['markers_found'],
                  reverse=True)[:n]
```

---

## PART 4 — Updated Architecture & Codebase

### 4.1 Full Updated Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    INTERFACE LAYER                            │
│   Web Dashboard  |  FastAPI (Dockerized)  |  API Explorer    │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│              LAYER 8: FastAPI Application                     │
│  POST /simulate-review (Task A)                              │
│  POST /recommend       (Task B)                              │
│  POST /ingest          POST /feedback   GET /health          │
└─────────────────────────┬────────────────────────────────────┘
                          │
┌─────────────────────────▼────────────────────────────────────┐
│         LAYER 6: LANGGRAPH ORCHESTRATOR                      │
│  Routes: Task A → Simulation → Review Generation             │
│          Task B → Simulation → Recommendation → Explanation  │
└──────┬──────────┬──────────────┬─────────────┬───────────────┘
       │          │              │             │
  ┌────▼───┐ ┌────▼────┐  ┌─────▼─────┐  ┌───▼──────────┐
  │CONTEXT │ │RETRIEVAL│  │SIMULATION │  │NIGERIAN      │
  │AGENT   │ │AGENT    │  │AGENT      │  │CALIBRATION   │
  │(Layer 5│ │(Layer 4)│  │(Layer 1)  │  │LAYER         │
  └────────┘ └─────────┘  └─────┬─────┘  └───┬──────────┘
                                 │             │
                    ┌────────────┴─────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼─────────┐  ┌────────▼──────────┐
    │TASK A:       │  │TASK B:            │
    │REVIEW        │  │RECOMMENDATION     │
    │GENERATION    │  │AGENT (Layer 2)    │
    │AGENT         │  │                   │
    │              │  │+ EXPLAINABILITY   │
    │Rating + Text │  │  AGENT (Layer 3)  │
    └──────────────┘  └───────────────────┘
┌──────────────────────────────────────────────────────────────┐
│                    LAYER 4: MEMORY                           │
│  ChromaDB (vectors) | PostgreSQL (metadata) | Redis (cache) │
└──────────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────────┐
│             LAYER 5: DATA PIPELINE                           │
│  Yelp Dataset → Privacy Abstraction → Behavioral Signals     │
│  Nigerian Cohort Extraction → Few-Shot Example Mining        │
└──────────────────────────────────────────────────────────────┘
```

---

### 4.2 Updated Repository Structure

```
arche/
├── README.md                      # Setup, run instructions, architecture overview
├── requirements.txt               # All Python dependencies pinned
├── .env.example                   # All required env vars documented
├── Dockerfile                     # Single container — both tasks
├── docker-compose.yml             # Full stack: API + PostgreSQL + Redis + ChromaDB
│
├── api/                           # FastAPI application
│   ├── main.py                    # App entry point, CORS, middleware
│   ├── routes/
│   │   ├── task_a.py              # POST /v1/simulate-review  ← NEW
│   │   ├── task_b.py              # POST /v1/recommend
│   │   ├── ingest.py              # POST /v1/ingest
│   │   ├── feedback.py            # POST /v1/feedback
│   │   └── health.py              # GET  /v1/health
│   └── middleware/
│       ├── auth.py
│       └── rate_limit.py
│
├── agents/
│   ├── orchestrator.py            # LangGraph — routes Task A vs Task B
│   ├── simulation_agent.py        # User Simulation Engine (shared by both tasks)
│   ├── review_generation_agent.py # NEW — Task A: rating + review text generation
│   ├── recommendation_agent.py    # Task B: exploration-aware ranking
│   ├── explainability_agent.py    # Task B: reasoning traces
│   ├── retrieval_agent.py         # Memory access
│   └── context_agent.py           # Time/device/region injection
│
├── nigerian/                      # NEW — Nigerian context module
│   ├── calibration.py             # Nigerian prompt calibration strings
│   ├── register_detector.py       # Detects user's language register from history
│   ├── fewshot_extractor.py       # Extracts Nigerian examples from Yelp data
│   ├── cohort_builder.py          # Builds Nigerian behavioral cohorts
│   └── prompts.py                 # All Nigerian-specific prompt templates
│
├── memory/
│   ├── vector_store.py            # ChromaDB integration
│   ├── relational_store.py        # PostgreSQL integration
│   ├── session_cache.py           # Redis session memory
│   ├── memory_manager.py          # Unified memory interface
│   └── schemas.py
│
├── data/
│   ├── yelp_pipeline.py           # NEW — Yelp dataset download + preprocessing
│   ├── user_profiler.py           # NEW — Build user profiles from Yelp history
│   ├── cohort_clusterer.py        # NEW — K-means/HDBSCAN behavioral clustering
│   ├── train_test_splitter.py     # NEW — 80/20 split for evaluation
│   ├── evaluation/
│   │   ├── task_a_evaluator.py    # NEW — RMSE, ROUGE, BERTScore computation
│   │   └── task_b_evaluator.py    # NEW — NDCG@10, Hit Rate computation
│   ├── privacy.py
│   └── schemas.py
│
├── pipeline/
│   ├── task_a_pipeline.py         # NEW — Full Task A execution pipeline
│   ├── task_b_pipeline.py         # Full Task B execution pipeline
│   ├── cold_start.py              # Cold start handling (25pts on scoring)
│   └── evaluation_runner.py       # NEW — Runs full evaluation, produces metrics
│
├── dashboard/
│   ├── package.json
│   └── src/
│       ├── pages/
│       │   ├── TaskADemo.jsx      # NEW — Review simulation demo view
│       │   ├── TaskBDemo.jsx      # Recommendation demo view
│       │   ├── EvaluationView.jsx # NEW — Shows RMSE, NDCG@10 scores live
│       │   └── BusinessDashboard.jsx
│       └── components/
│           ├── ReviewCard.jsx     # NEW — Shows generated review + predicted rating
│           ├── RecommendationCard.jsx
│           └── ReasoningTrace.jsx
│
├── solution_paper/                # NEW — Solution paper deliverable
│   ├── arche_solution_paper.md    # Draft — written Days 15-17
│   └── figures/                   # Architecture diagrams, results tables
│
├── tests/
│   ├── test_task_a.py             # NEW
│   ├── test_task_b.py
│   ├── test_simulation.py
│   ├── test_nigerian_context.py   # NEW
│   └── test_api.py
│
└── demo/
    ├── mock_data/
    │   ├── yelp_sample.json       # 500-record Yelp sample for quick demo
    │   ├── nigerian_personas.json # 3 Nigerian demo personas
    │   └── demo_items.json        # Items for Task A demo
    └── demo_script.md
```

---

### 4.3 New Components — Key Implementation Details

#### ReviewGenerationAgent (Task A)

```python
# agents/review_generation_agent.py

class ReviewGenerationAgent:
    def __init__(self, llm, nigerian_calibrator):
        self.llm = llm
        self.calibrator = nigerian_calibrator

    async def generate_review(
        self,
        simulation: SimulationOutput,
        item: ItemDetails,
        user_history: list[Review]
    ) -> ReviewOutput:

        # Detect user's language register from history
        register = self.calibrator.detect_register(user_history)

        # Get few-shot examples matching this user's style
        fewshot = self.calibrator.get_fewshot_examples(
            register=register,
            category=item.category,
            n=3
        )

        # Build generation prompt
        prompt = self._build_review_prompt(
            simulation=simulation,
            item=item,
            user_history=user_history,
            register=register,
            fewshot_examples=fewshot
        )

        response = await self.llm.ainvoke(prompt)
        return self._parse_review_output(response)

    def _build_review_prompt(self, simulation, item, history,
                              register, fewshot_examples):
        nigerian_context = self.calibrator.get_calibration_prompt(register)

        return [
            SystemMessage(content=f"""You are ARCHE's Review Generation Agent.
            Your task: Given a user's behavioral simulation and an unseen item,
            generate the review this user WOULD write and the rating they WOULD give.

            {nigerian_context}

            Output ONLY valid JSON:
            {{
                "predicted_rating": <int 1-5>,
                "generated_review": "<review text>",
                "tone_confidence": <float 0-1>,
                "behavioural_basis": "<what in the simulation drove this>"
            }}"""),

            HumanMessage(content=f"""
            USER BEHAVIORAL SIMULATION:
            {simulation.behavioral_snapshot.dict()}

            USER'S PAST REVIEWS (style reference):
            {[r.text for r in history[-5:]]}

            UNSEEN ITEM TO REVIEW:
            Name: {item.name}
            Category: {item.category}
            Price tier: {item.price_tier}
            Attributes: {item.attributes}

            FEW-SHOT STYLE EXAMPLES (similar users, similar items):
            {fewshot_examples}

            Generate the review and rating. Match the user's voice exactly.
            Return ONLY valid JSON.""")
        ]
```

#### Yelp Data Pipeline

```python
# data/yelp_pipeline.py

import pandas as pd
import json
from pathlib import Path

class YelpPipeline:
    """
    Processes Yelp Open Dataset for ARCHE training and evaluation.
    Download from: https://www.yelp.com/dataset
    """

    def __init__(self, data_dir: str = "./data/yelp_raw"):
        self.data_dir = Path(data_dir)

    def load_and_process(self, min_reviews_per_user: int = 10):
        # Load raw Yelp data
        reviews = self._load_reviews()
        businesses = self._load_businesses()

        # Filter: users with enough history for meaningful evaluation
        user_review_counts = reviews.groupby('user_id').size()
        active_users = user_review_counts[
            user_review_counts >= min_reviews_per_user
        ].index
        reviews = reviews[reviews['user_id'].isin(active_users)]

        # Merge with business metadata
        reviews = reviews.merge(businesses[['business_id','name',
                                'categories','city','stars']],
                                on='business_id', how='left')

        return reviews

    def train_test_split(self, reviews_df, test_ratio: float = 0.2):
        """
        For each user: last 20% of reviews = test set (held out)
        First 80% = training history (available to agent)
        """
        reviews_sorted = reviews_df.sort_values(['user_id','date'])
        train, test = [], []

        for user_id, user_reviews in reviews_sorted.groupby('user_id'):
            n = len(user_reviews)
            split_idx = int(n * (1 - test_ratio))
            train.append(user_reviews.iloc[:split_idx])
            test.append(user_reviews.iloc[split_idx:])

        return pd.concat(train), pd.concat(test)

    def extract_nigerian_users(self, reviews_df):
        """Extract reviews exhibiting Nigerian language patterns"""
        nigerian_markers = [
            "sha", "abi", "sef", "abeg", "na im", "e be like",
            "very okay", "jollof", "suya", "pepper soup", "naija"
        ]
        mask = reviews_df['text'].str.lower().apply(
            lambda t: sum(m in t for m in nigerian_markers) >= 2
        )
        return reviews_df[mask]
```

#### Task A Evaluation

```python
# data/evaluation/task_a_evaluator.py

from rouge_score import rouge_scorer
import numpy as np

class TaskAEvaluator:
    def __init__(self):
        self.rouge = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], use_stemmer=True
        )

    def evaluate_rating(self, predicted: list[int],
                         actual: list[int]) -> float:
        """Root Mean Square Error on star ratings"""
        return np.sqrt(np.mean((np.array(predicted) -
                                np.array(actual)) ** 2))

    def evaluate_review_text(self, generated: list[str],
                              reference: list[str]) -> dict:
        """ROUGE scores for review text quality"""
        scores = [self.rouge.score(ref, gen)
                  for ref, gen in zip(reference, generated)]
        return {
            'rouge1': np.mean([s['rouge1'].fmeasure for s in scores]),
            'rouge2': np.mean([s['rouge2'].fmeasure for s in scores]),
            'rougeL': np.mean([s['rougeL'].fmeasure for s in scores]),
        }

    def full_evaluation(self, results: list[dict]) -> dict:
        predicted_ratings = [r['predicted_rating'] for r in results]
        actual_ratings    = [r['actual_rating'] for r in results]
        generated_reviews = [r['generated_review'] for r in results]
        actual_reviews    = [r['actual_review'] for r in results]

        return {
            'rmse':  self.evaluate_rating(predicted_ratings, actual_ratings),
            'rouge': self.evaluate_review_text(generated_reviews, actual_reviews),
            'n_samples': len(results)
        }
```

#### Task B Evaluation

```python
# data/evaluation/task_b_evaluator.py

import numpy as np

class TaskBEvaluator:
    def ndcg_at_k(self, recommended: list, relevant: set,
                   k: int = 10) -> float:
        """Normalized Discounted Cumulative Gain @ k"""
        dcg = sum(
            1 / np.log2(i + 2)
            for i, item in enumerate(recommended[:k])
            if item in relevant
        )
        ideal_dcg = sum(
            1 / np.log2(i + 2)
            for i in range(min(len(relevant), k))
        )
        return dcg / ideal_dcg if ideal_dcg > 0 else 0.0

    def hit_rate_at_k(self, recommended: list,
                       relevant: set, k: int = 10) -> float:
        """Did any of the top-k recommendations hit a relevant item?"""
        return float(bool(set(recommended[:k]) & relevant))

    def full_evaluation(self, results: list[dict], k: int = 10) -> dict:
        ndcg_scores = []
        hit_rates   = []

        for r in results:
            ndcg_scores.append(
                self.ndcg_at_k(r['recommended'], r['relevant'], k)
            )
            hit_rates.append(
                self.hit_rate_at_k(r['recommended'], r['relevant'], k)
            )

        return {
            f'ndcg@{k}':     np.mean(ndcg_scores),
            f'hit_rate@{k}': np.mean(hit_rates),
            'n_users':       len(results)
        }
```

---

### 4.4 Docker Setup — Submission Ready

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml — SUBMISSION READY
version: "3.8"

services:
  arche-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgresql://arche:arche@postgres:5432/arche
      - REDIS_URL=redis://redis:6379
      - CHROMADB_HOST=chromadb
    depends_on:
      - postgres
      - redis
      - chromadb
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=arche
      - POSTGRES_USER=arche
      - POSTGRES_PASSWORD=arche
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - chroma_data:/chroma/chroma
    restart: unless-stopped

volumes:
  postgres_data:
  chroma_data:
```

---

### 4.5 Updated API Endpoints

```
Task A — User Modeling:
POST /v1/simulate-review
  Body: {
    "user_token": "hashed_id",
    "user_history": [...],        ← user's past reviews
    "item": {                     ← unseen item to review
      "name": "Domino's Pizza Lagos",
      "category": "Fast Food",
      "price_tier": "mid",
      "attributes": {...}
    },
    "context": {
      "time_bucket": "evening",
      "region": "Lagos Mainland"
    }
  }
  Response: {
    "predicted_rating": 3,
    "generated_review": "Domino's is aight but...",
    "tone_confidence": 0.84,
    "behavioural_basis": "Value-conscious cluster, Western food skepticism signal"
  }

Task B — Recommendation:
POST /v1/recommend
  Body: {
    "user_token": "hashed_id",
    "user_history": [...],
    "n": 10,
    "context": { "time_bucket": "evening", "device": "mobile" }
  }
  Response: {
    "recommendations": [...],
    "diversity_score": 0.73,
    "exploration_ratio": 0.40,
    "cold_start_used": false
  }
```

---

## PART 5 — Solution Paper Structure

Write this Days 15–17 using real evaluation numbers.

```
Title: ARCHE: Simulation-Driven Agentic User Modeling
       for Review Generation and Personalized Recommendation

Abstract (0.5 pages)
  What ARCHE does. Key results (RMSE X, NDCG@10 Y).
  One-line contribution: simulation-driven architecture.

1. Introduction (0.5 pages)
   Problem: static user modeling fails.
   Our approach: simulate before generating/recommending.

2. Related Work (0.5 pages)
   Collaborative filtering limitations.
   LLM-based recommendation prior work.
   Why simulation is novel.

3. Architecture (2 pages)
   3.1 User Simulation Engine
   3.2 ReviewGenerationAgent (Task A)
   3.3 RecommendationAgent (Task B)
   3.4 Multi-Agent Orchestration
   3.5 Memory Architecture
   3.6 Nigerian Contextualization Layer

4. Experiments & Results (1.5 pages)
   Dataset: Yelp Open Dataset (X users, Y reviews)
   Task A results: RMSE, ROUGE-1/2/L, BERTScore
   Task B results: NDCG@10, Hit Rate@10, Cold-Start performance
   Ablation: With simulation vs without simulation engine
   Nigerian bonus: qualitative examples

5. Nigerian Contextualization (0.5 pages)
   Register detection approach
   Calibration methodology
   Example: same user, with/without Nigerian calibration

6. Future Work (0.5 pages)
   Full 16-layer ARCHE vision
   Production deployment for BCT clients
   Fine-tuning for deeper cultural calibration

7. Conclusion (0.25 pages)
```

---

## PART 6 — Updated 17-Day Build Plan

### Revised Day-by-Day Schedule

| Day | Focus                                        | Owner        | Key Output                                     |
| --- | -------------------------------------------- | ------------ | ---------------------------------------------- |
| 1   | Repo setup + Docker + Yelp download          | All          | docker-compose up works. Yelp data downloaded. |
| 2   | Yelp data pipeline + train/test split        | Backend + AI | Clean user profiles ready for training         |
| 3   | Nigerian cohort extraction + few-shot mining | AI Engineer  | Nigerian behavioral clusters built             |
| 4   | Memory Layer (ChromaDB + PostgreSQL + Redis) | AI + Backend | All memory layers reading/writing              |
| 5   | User Simulation Engine — core build          | AI Engineer  | SimulationAgent returns coherent snapshot      |
| 6   | Cold Start system + population priors        | AI Engineer  | New user gets meaningful simulation            |
| 7   | ReviewGenerationAgent — Task A               | AI Engineer  | Star rating + review text generated            |
| 8   | Task A evaluation (RMSE + ROUGE)             | AI Engineer  | Evaluation numbers in hand                     |
| 9   | RecommendationAgent — Task B                 | AI Engineer  | 10 ranked recommendations returned             |
| 10  | LangGraph Orchestrator + all agents wired    | AI + Backend | Full pipeline executes end-to-end              |
| 11  | Task B evaluation (NDCG@10 + Hit Rate)       | AI Engineer  | Evaluation numbers in hand                     |
| 12  | FastAPI endpoints + Docker polish            | Backend      | Both task endpoints working in container       |
| 13  | Dashboard — TaskADemo + TaskBDemo + EvalView | Fullstack    | All views live and connected                   |
| 14  | Nigerian calibration tuning + demo prep      | All          | Nigerian demos compelling and accurate         |
| 15  | Solution paper draft + ablation study        | All          | Paper draft complete with real numbers         |
| 16  | Polish, bug fixes, submission package        | All          | Submitted before midnight May 24               |
| 17  | June 10 prep — dry run + Q&A practice        | All          | Ready for Grand Finale                         |

---

## PART 7 — MASTER BUILD CHECKLIST

Use this every day. Check off as you complete each item.

---

### 🔧 SETUP (Day 1)

- [ ] GitHub repository created with agreed branching strategy
- [ ] `.env.example` created with all required environment variables documented
- [ ] `docker-compose.yml` written — all services defined
- [ ] `docker-compose up` runs without errors
- [ ] FastAPI skeleton — `GET /v1/health` returns 200
- [ ] Claude API key configured and tested
- [ ] LangChain + LangGraph installed — hello-world agent running
- [ ] Yelp dataset downloaded and stored in `data/yelp_raw/`
- [ ] PostgreSQL schema designed and migration written
- [ ] Team aligned: all read this HackAlign document

---

### 📦 DATA PIPELINE (Days 1–3)

- [ ] `yelp_pipeline.py` — loads and cleans Yelp data
- [ ] User profiles built — each user has structured history
- [ ] Train/test split complete — 80% history / 20% held out
- [ ] Minimum 10 reviews per user filter applied
- [ ] Business metadata merged with reviews
- [ ] `cohort_clusterer.py` — behavioral clusters created (5 global clusters)
- [ ] Nigerian users extracted — `extract_nigerian_users()` working
- [ ] Few-shot Nigerian examples mined — 15–20 examples saved
- [ ] Language register detector working — classifies user writing style
- [ ] Sample data confirmed: can retrieve user history + unseen items cleanly

---

### 🧠 MEMORY LAYER (Day 4)

- [ ] ChromaDB collection created — `behavioral_embeddings`
- [ ] PostgreSQL tables created: `users`, `signals`, `sessions`, `cohorts`, `reviews`
- [ ] Redis session cache working — get/set/delete
- [ ] `MemoryManager.retrieve_all()` working across all 4 memory layers
- [ ] `MemoryManager.update()` writing signals to all layers
- [ ] Population cohort priors stored in ChromaDB
- [ ] Unit tests for memory layer passing

---

### 🎭 USER SIMULATION ENGINE (Days 5–6)

- [ ] `SimulationAgent` class complete
- [ ] System prompt for simulation written and tested
- [ ] `_build_simulation_prompt()` — memory + context → coherent LLM prompt
- [ ] Simulation output parser — LLM JSON → `SimulationOutput` schema
- [ ] Cold start: new user gets simulation with confidence > 0.65
- [ ] Register detection integrated into simulation
- [ ] Nigerian calibration prompt injected when Nigerian signals detected
- [ ] Simulation tested on 5 different user profiles — outputs coherent
- [ ] `POST /v1/simulate` endpoint wired and working

---

### ✍️ TASK A — REVIEW GENERATION (Day 7–8)

- [ ] `ReviewGenerationAgent` class complete
- [ ] `_build_review_prompt()` — simulation + item + fewshot → LLM prompt
- [ ] Review output parser — LLM JSON → `ReviewOutput` schema
- [ ] Predicted rating in correct 1–5 range
- [ ] Generated review text captures user's vocabulary patterns
- [ ] Nigerian register correctly applied when applicable
- [ ] `POST /v1/simulate-review` endpoint working
- [ ] `TaskAEvaluator` complete — RMSE, ROUGE-1/2/L computing correctly
- [ ] Evaluation run on 100 test users — RMSE and ROUGE numbers recorded
- [ ] Ablation: compare simulation-grounded vs direct generation (for paper)

---

### 🎯 TASK B — RECOMMENDATION (Days 9–11)

- [ ] `RecommendationAgent` class complete
- [ ] 60/25/15 exploration split implemented
- [ ] Diversity penalty algorithm working
- [ ] Context modifiers applied to ranking
- [ ] Nigerian recommendation calibration injected when applicable
- [ ] `POST /v1/recommend` endpoint working
- [ ] `ExplainabilityAgent` generating reasoning traces
- [ ] Cold start: sparse user (1–2 reviews) still gets ranked output
- [ ] Cross-domain: user from restaurants getting book/product recs if applicable
- [ ] `TaskBEvaluator` complete — NDCG@10 and Hit Rate computing correctly
- [ ] Evaluation run on 100 test users — NDCG@10 and Hit Rate recorded
- [ ] Ablation: simulation-grounded vs direct ranking (for paper)

---

### 🤖 ORCHESTRATOR + INTEGRATION (Day 10)

- [ ] `ARCHEState` TypedDict defined
- [ ] LangGraph graph built — all agent nodes added
- [ ] Task A pipeline: retrieve → context → simulate → generate_review → security
- [ ] Task B pipeline: retrieve → context → simulate → recommend → explain → security
- [ ] Orchestrator correctly routes Task A vs Task B requests
- [ ] Error handling — graceful fallback if any agent fails
- [ ] Full pipeline tested end-to-end for both tasks with real Yelp data

---

### 🐳 DOCKER + API (Day 12)

- [ ] `Dockerfile` builds without errors
- [ ] `docker-compose up` starts all services cleanly
- [ ] Both task endpoints working inside Docker container
- [ ] Environment variables passed correctly via `.env`
- [ ] Health check endpoint returns healthy from inside container
- [ ] `docker-compose down && docker-compose up` — clean restart works
- [ ] API auto-docs at `/docs` showing both task endpoints
- [ ] README has exact `docker-compose up` instructions for judges

---

### 🖥️ DASHBOARD (Day 13)

- [ ] React + Next.js + Tailwind project setup
- [ ] `TaskADemo` — user history input + item input → shows generated review + rating
- [ ] `TaskBDemo` — user persona input → shows 10 recommendations with reasoning
- [ ] `EvaluationView` — shows RMSE, NDCG@10, Hit Rate scores live
- [ ] `BusinessDashboard` — SME analytics view
- [ ] All views connected to live Docker API
- [ ] Nigerian demo persona loaded — shows culturally calibrated output
- [ ] Deployed to Vercel at public URL

---

### 🇳🇬 NIGERIAN CONTEXT (Day 14)

- [ ] Register detector tested on 10 Nigerian user profiles — correct classification
- [ ] Generated reviews from Nigerian users include appropriate language markers
- [ ] Recommendation output for Nigerian users shows culturally relevant signals
- [ ] Demo: side-by-side — same user with/without Nigerian calibration (for paper)
- [ ] 3 Nigerian demo personas prepared: Lagos Island, Lagos Mainland, Abuja
- [ ] Nigerian few-shot examples visibly improve review quality

---

### 📄 SOLUTION PAPER (Days 15–16)

- [ ] Abstract written — includes actual RMSE and NDCG@10 numbers
- [ ] Introduction written — problem clearly stated
- [ ] Architecture section complete — all diagrams included
- [ ] Experiments section — results table with real numbers
- [ ] Ablation study written — simulation vs no simulation comparison
- [ ] Nigerian contextualization section — qualitative examples included
- [ ] Future work section — references full ARCHE 16-layer vision
- [ ] Paper is 4–8 pages — not over or under
- [ ] Paper reviewed by all team members
- [ ] PDF exported and ready for submission

---

### 📁 GITHUB REPOSITORY (Day 16)

- [ ] Repository is public (or accessible to judges)
- [ ] README includes: what ARCHE does, how to run it, architecture overview
- [ ] `docker-compose up` instructions in README — one command setup
- [ ] All agent files have clear docstrings
- [ ] Agentic workflow logic is well-commented
- [ ] requirements.txt is pinned and complete
- [ ] `.env.example` documents all required variables
- [ ] No API keys committed to repository
- [ ] At least one example input/output in README
- [ ] Modular structure — each agent is independently readable

---

### 🚀 SUBMISSION (Day 16 — Before Midnight)

- [ ] Containerized app submitted — Docker link or deployed URL
- [ ] Solution paper submitted — PDF, 4–8 pages
- [ ] GitHub repository submitted — clean, public, runnable
- [ ] All three submitted via official submission form before midnight May 24
- [ ] Confirmation email received from organizers
- [ ] Backup copies of all deliverables stored locally

---

### 🎤 JUNE 10 PREPARATION (Day 17)

- [ ] Full demo dry run — both Task A and Task B shown, timed at 7 minutes
- [ ] 10 anticipated judge questions written out with answers
- [ ] Architecture diagram printed and ready
- [ ] Backup demo recording made (full screen record)
- [ ] All team members know their speaking roles
- [ ] Evaluation numbers memorized — RMSE X, NDCG@10 Y, Hit Rate Z
- [ ] Travel/logistics to Eko Hotel confirmed

---

## PART 8 — Competitive Edge Summary

| Scoring Criterion                     | Other Teams                       | ARCHE                                                             |
| ------------------------------------- | --------------------------------- | ----------------------------------------------------------------- |
| Review Text Quality (ROUGE/BERTScore) | History replay → generic output   | Simulation-grounded voice capture → user-specific output          |
| Rating Accuracy (RMSE)                | Average past ratings              | Behavioral snapshot → contextual prediction                       |
| Behavioural Fidelity (human eval)     | Sounds like "a user"              | Sounds like THIS user — register, tone, vocabulary                |
| NDCG@10 / Hit Rate (30pts)            | Pure relevance scoring            | Exploration-aware diversity ranking                               |
| Cold-Start (25pts)                    | Fails or returns popular items    | Population cohort memory → inference from priors                  |
| Contextual Relevance (20pts)          | Context ignored                   | Time/device/region as primary inputs                              |
| Solution Paper (15pts)                | "We used GPT to generate reviews" | Novel simulation architecture — genuine intellectual contribution |
| Code Reproducibility (10pts)          | Jupyter notebook                  | Modular, documented, Dockerized, clean README                     |
| Nigerian Bonus                        | One slang word added              | Culturally calibrated behavioral simulation grounded in real data |

**ARCHE does not win on one criterion. It wins on every row simultaneously.**

---

_HackAlign v1.0 — ARCHE — DSN x BCT LLM Agent Challenge 3.0 — Confidential_
_Read this document before writing a single line of code._
