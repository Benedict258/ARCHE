# ARCHE — Co-pilot Alignment Prompt
## Read This Entirely Before Writing Any Code

---

> **Context:** You are the AI co-pilot continuing development on ARCHE. This project has been partially built. This document tells you exactly what exists, what must not change, what is missing, and what to build next — in priority order. The companion document `ARCHE_HackAlign.md` contains the full architectural specification, Nigerian context strategy, scoring rubric, and master checklist. Read both before writing anything.

---

## The Competition

| Field | Detail |
|---|---|
| Hackathon | DSN x BCT LLM Agent Challenge 3.0 |
| Submission Deadline | **May 24, 2026 — midnight. No extensions. No exceptions.** |
| Grand Finale | June 10, 2026 — Eko Hotel, Lagos |
| Tasks Required | **BOTH Task A AND Task B — submitting only one = disqualified** |
| Deliverables | 3 required: Containerized App + Solution Paper + GitHub Repo |
| Prize | ₦1,500,000 for 1st place |

---

## What Has Already Been Built — DO NOT TOUCH

The following exists and is working. Do not restructure, rewrite, replace, or refactor any of this unless explicitly instructed. Treat it as locked.

```
Current Repository Structure:
├── README.md
├── main.py                    ← FastAPI backend — WORKING
├── memory_manager.py          ← Memory layer — WORKING
├── local_vector_store.py      ← Vector store — WORKING
├── pipeline.py                ← Orchestration — WORKING
├── client.py                  ← SDK client — WORKING
├── test_integration.py        ← 11 tests PASSING — must stay passing
├── test_performance.py        ← 8 tests PASSING — must stay passing
├── demo_recorder.py
├── demo_script.md
├── mock_data/
│   ├── users.json
│   ├── products.json
│   ├── interactions.json
│   └── deterministic_scenario.json
└── frontend/
    ├── App.tsx                ← React + Vite + Tailwind + GSAP — WORKING
    ├── api.ts
    ├── useAPI.ts
    ├── RecommendationDemo.tsx ← Working demo component
    └── story-scroll.tsx
```

### Working Endpoints (already in main.py)
```
GET  /v1/health       ✅ Working
POST /v1/ingest       ✅ Working
POST /v1/simulate     ✅ Working
POST /v1/recommend    ✅ Working
POST /v1/explain      ✅ Working
```

### Tech Stack That Is Already In Use — Keep It
| Layer | What Exists | Status |
|---|---|---|
| Backend | FastAPI + Pydantic | ✅ Working |
| Memory | SQLite + local vector store | ✅ Working |
| Orchestration | Custom sequential pipeline (pipeline.py) | ✅ Working |
| SDK | Custom async HTTP client (client.py) | ✅ Working |
| Frontend | React + Vite + Tailwind + GSAP | ✅ Working |
| Dataset | Mock data (users.json, products.json, interactions.json) | ✅ In use |
| Tests | 19 tests total, all passing | ✅ Must stay passing |

---

## What Is Missing — The Build Gap

### 🔴 CRITICAL — Submission fails without these

| Missing | Why Critical |
|---|---|
| `POST /v1/simulate-review` | Task A endpoint — required deliverable. Without it we are disqualified for submitting only one task. |
| Yelp dataset integration | Evaluation metrics (RMSE, ROUGE, NDCG@10) require real held-out data. Mock data cannot produce valid scores for the solution paper. |
| Evaluation scripts | Need real RMSE + NDCG@10 numbers for the solution paper. Paper is worth 15 points and judges read it first. |

### 🟡 IMPORTANT — Affects score significantly

| Missing | Why Important |
|---|---|
| Docker (Dockerfile + docker-compose.yml) | Submission must be containerized. Judges will attempt `docker-compose up` on a clean machine. |
| Nigerian context module | Explicit bonus marks in scoring rubric. Most teams will miss this. We should not. |

### 🟢 ENHANCEMENT — Improves demo quality

| Missing | Why Useful |
|---|---|
| Task A frontend view (TaskADemo.tsx) | Judges need to see Task A working visually in the demo on June 10 |
| Evaluation dashboard view (EvaluationView.tsx) | Shows live RMSE + NDCG@10 scores during demo |

---

## The Two Tasks — Full Specification

### How They Connect

```
User History → [EXISTING] Simulation Engine → Behavioral Snapshot
                                                      |
                              ┌───────────────────────┴─────────────────────┐
                              ▼                                              ▼
                      TASK A OUTPUT                               TASK B OUTPUT
                 "What would this user                    "What should this user
                  write about this item?"                  see recommended next?"
                 → predicted_rating (1-5)                 → ranked_recommendations
                 → generated_review (text)                → reasoning traces
                 [POST /v1/simulate-review]               [POST /v1/recommend]
                       MISSING — BUILD THIS               ALREADY BUILT
```

The simulation engine (`/v1/simulate`) already exists. Task A is a new downstream consumer of that simulation output. Build it as an extension — not a replacement.

---

### Task A — User Modeling (MISSING — BUILD FIRST)

**What judges want:**
> Build an agent that understands users deeply enough to simulate their reviews — capturing tone, rating behaviour, and contextual nuance.

**Concrete example:**
```
Input:
  User: Emeka
  History: ["Chicken Republic: jollof rice was fire but slow ⭐⭐⭐⭐",
            "KFC: consistent but overpriced ⭐⭐⭐"]
  Unseen Item: { "name": "Domino's Pizza Lagos", "category": "Fast Food" }

Output:
  predicted_rating: 3
  generated_review: "Domino's is aight but nothing special. Pizza came
                    hot which I appreciate but for that price I could
                    just hit Chicken Republic. Not bad sha."
  tone_confidence: 0.82
  behavioural_basis: "Value-conscious cluster, Western fast food skepticism"
```

**Endpoint to build:**
```
POST /v1/simulate-review

Request:
{
  "user_token": "str",
  "user_history": [
    {
      "item_name": "str",
      "item_category": "str",
      "rating": int,
      "review_text": "str"
    }
  ],
  "item": {
    "name": "str",
    "category": "str",
    "price_tier": "budget | mid | premium | luxury",
    "attributes": {}
  },
  "context": {
    "time_bucket": "morning | afternoon | evening | night",
    "region": "str"
  }
}

Response:
{
  "predicted_rating": int,          // 1-5, always integer
  "generated_review": "str",        // review text in user's voice
  "tone_confidence": float,         // 0.0 to 1.0
  "behavioural_basis": "str"        // plain English explanation of what drove the output
}
```

**Implementation approach:**
1. Call the existing simulation pipeline to get a behavioral snapshot from user history
2. Pass the snapshot + item details to the LLM
3. Generate a review grounded in the behavioral snapshot
4. Detect user's writing style from their history and match it in output
5. If Nigerian language markers detected in history — apply Nigerian calibration (see Nigerian Context section below)

**Evaluated on:**
- RMSE — predicted rating vs actual rating (lower = better)
- ROUGE-1/2/L — generated review text vs actual review text
- Behavioural Fidelity — human eval: does it sound like this specific user?

---

### Task B — Recommendation (ALREADY BUILT — extend only)

**What exists:** `POST /v1/recommend` is working.

**What needs to be added:**
- Yelp dataset as the catalog (alongside existing mock data)
- Cold-start handling verification (users with 1–2 reviews still get output)
- Evaluation script to compute NDCG@10 and Hit Rate@10 on held-out Yelp data

**Evaluated on (100 points):**
```
Ranking Quality (NDCG@10 / Hit Rate)  — 30 points
Cold-Start & Cross-Domain              — 25 points
Contextual Relevance (human eval)      — 20 points
Solution Paper                         — 15 points
Code Reproducibility                   — 10 points
```

---

## Build Priority Order

Work through these in exact order. Do not jump ahead. Confirm tests pass after each item.

---

### PRIORITY 1 — CRITICAL (do these before anything else)

---

#### [P1.1] POST /v1/simulate-review — Task A Endpoint

**File to create:** `api/routes/task_a.py`
**File to modify:** `main.py` (add router import only — minimal change)

```python
# api/routes/task_a.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json

router = APIRouter()

class ReviewHistoryItem(BaseModel):
    item_name: str
    item_category: str
    rating: int
    review_text: str

class ItemDetails(BaseModel):
    name: str
    category: str
    price_tier: str = "mid"
    attributes: dict = {}

class SimulateReviewRequest(BaseModel):
    user_token: str
    user_history: list[ReviewHistoryItem]
    item: ItemDetails
    context: dict = {}

class SimulateReviewResponse(BaseModel):
    predicted_rating: int
    generated_review: str
    tone_confidence: float
    behavioural_basis: str

@router.post("/v1/simulate-review", response_model=SimulateReviewResponse)
async def simulate_review(request: SimulateReviewRequest):
    """
    Task A: Given user history + unseen item, simulate what
    the user would write and what rating they would give.
    """
    # Step 1: Build behavioral snapshot from user history
    # (reuse existing simulation logic)
    
    # Step 2: Detect user's language register
    register = detect_register([r.review_text for r in request.user_history])
    
    # Step 3: Get Nigerian calibration if applicable
    nigerian_context = get_nigerian_calibration(register)
    
    # Step 4: Generate review via LLM
    result = await generate_review_from_simulation(
        user_history=request.user_history,
        item=request.item,
        context=request.context,
        register=register,
        nigerian_context=nigerian_context
    )
    
    return SimulateReviewResponse(**result)
```

**LLM prompt for review generation:**
```python
SYSTEM_PROMPT = """You are ARCHE's Review Generation Agent.

Given a user's past reviews and an item they have never reviewed,
generate the review they WOULD write and the rating they WOULD give.

Rules:
1. Match the user's exact writing style from their history
2. Match their vocabulary, sentence length, complaint patterns
3. The rating must be an integer 1-5
4. The review must sound like THIS user, not a generic user
5. Output ONLY valid JSON — no markdown, no extra text

{nigerian_context}

Output format:
{{
  "predicted_rating": <int 1-5>,
  "generated_review": "<review text matching user's style>",
  "tone_confidence": <float 0.0-1.0>,
  "behavioural_basis": "<one sentence: what in their history drove this>"
}}"""

USER_PROMPT = """User's past reviews (learn their style from these):
{user_history}

Item to review (they have never seen this before):
Name: {item_name}
Category: {item_category}
Price tier: {price_tier}

Current context: {context}

Generate the review and rating. Match their voice exactly.
Return ONLY valid JSON."""
```

**After building:** Run `test_integration.py` and `test_performance.py`. All 19 tests must still pass.

---

#### [P1.2] Yelp Dataset Pipeline

**File to create:** `data/yelp_pipeline.py`

Download Yelp Open Dataset from: `https://www.yelp.com/dataset`

```python
# data/yelp_pipeline.py

import pandas as pd
import json
from pathlib import Path

class YelpPipeline:
    """
    Processes Yelp Open Dataset for ARCHE evaluation.
    
    Download the dataset from yelp.com/dataset and place the
    JSON files in data/yelp_raw/ before running this pipeline.
    
    Files needed:
    - yelp_academic_dataset_review.json
    - yelp_academic_dataset_business.json
    """
    
    def __init__(self, raw_dir="data/yelp_raw",
                 processed_dir="data/yelp_processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def load_reviews(self, max_records=500000):
        """Load reviews from Yelp JSON file"""
        records = []
        path = self.raw_dir / "yelp_academic_dataset_review.json"
        with open(path) as f:
            for i, line in enumerate(f):
                if i >= max_records:
                    break
                records.append(json.loads(line))
        return pd.DataFrame(records)
    
    def load_businesses(self):
        """Load business metadata"""
        records = []
        path = self.raw_dir / "yelp_academic_dataset_business.json"
        with open(path) as f:
            for line in f:
                records.append(json.loads(line))
        return pd.DataFrame(records)
    
    def build_user_profiles(self, min_reviews=10):
        """Build user profiles — only users with enough history"""
        reviews = self.load_reviews()
        businesses = self.load_businesses()
        
        # Filter active users
        counts = reviews.groupby('user_id').size()
        active = counts[counts >= min_reviews].index
        reviews = reviews[reviews['user_id'].isin(active)]
        
        # Merge business metadata
        reviews = reviews.merge(
            businesses[['business_id','name','categories','city']],
            on='business_id', how='left'
        )
        
        return reviews
    
    def train_test_split(self, reviews_df, test_ratio=0.2):
        """
        Split: sort by date, last 20% per user = test (held out).
        Agent sees first 80%, must predict last 20%.
        """
        reviews_sorted = reviews_df.sort_values(['user_id','date'])
        train_parts, test_parts = [], []
        
        for user_id, group in reviews_sorted.groupby('user_id'):
            n = len(group)
            split = int(n * (1 - test_ratio))
            train_parts.append(group.iloc[:split])
            test_parts.append(group.iloc[split:])
        
        train = pd.concat(train_parts)
        test = pd.concat(test_parts)
        
        # Save processed splits
        train.to_json(
            self.processed_dir / "train.json",
            orient='records', lines=True
        )
        test.to_json(
            self.processed_dir / "test.json",
            orient='records', lines=True
        )
        
        print(f"Train: {len(train)} reviews | Test: {len(test)} reviews")
        print(f"Users: {reviews_df['user_id'].nunique()}")
        return train, test
    
    def extract_nigerian_users(self, reviews_df):
        """Extract reviews with Nigerian language patterns"""
        markers = [
            "sha", "abi", "sef", "abeg", "na im", "e be like",
            "very okay", "jollof", "suya", "pepper soup", "naija", "9ja"
        ]
        mask = reviews_df['text'].str.lower().apply(
            lambda t: sum(m in str(t) for m in markers) >= 2
            if pd.notna(t) else False
        )
        nigerian = reviews_df[mask].copy()
        nigerian.to_json(
            self.processed_dir / "nigerian_users.json",
            orient='records', lines=True
        )
        print(f"Nigerian-pattern reviews found: {len(nigerian)}")
        return nigerian
    
    def run(self):
        """Run full pipeline"""
        print("Building user profiles...")
        reviews = self.build_user_profiles(min_reviews=10)
        
        print("Splitting train/test...")
        train, test = self.train_test_split(reviews)
        
        print("Extracting Nigerian patterns...")
        self.extract_nigerian_users(reviews)
        
        print("Done. Files saved to data/yelp_processed/")
        return train, test

if __name__ == "__main__":
    pipeline = YelpPipeline()
    pipeline.run()
```

---

#### [P1.3] Evaluation Scripts

**File to create:** `data/evaluation/task_a_evaluator.py`

```python
# data/evaluation/task_a_evaluator.py

import numpy as np
from rouge_score import rouge_scorer as rouge_lib

class TaskAEvaluator:
    def __init__(self):
        self.rouge = rouge_lib.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], use_stemmer=True
        )
    
    def rmse(self, predicted: list[int], actual: list[int]) -> float:
        """Root Mean Square Error on star ratings. Lower = better."""
        return float(np.sqrt(np.mean(
            (np.array(predicted) - np.array(actual)) ** 2
        )))
    
    def rouge_scores(self, generated: list[str],
                     reference: list[str]) -> dict:
        """ROUGE scores for review text quality."""
        scores = [
            self.rouge.score(ref, gen)
            for ref, gen in zip(reference, generated)
        ]
        return {
            'rouge1': np.mean([s['rouge1'].fmeasure for s in scores]),
            'rouge2': np.mean([s['rouge2'].fmeasure for s in scores]),
            'rougeL': np.mean([s['rougeL'].fmeasure for s in scores]),
        }
    
    def evaluate(self, results: list[dict]) -> dict:
        """
        results: list of dicts with keys:
          predicted_rating, actual_rating,
          generated_review, actual_review
        """
        return {
            'rmse': self.rmse(
                [r['predicted_rating'] for r in results],
                [r['actual_rating'] for r in results]
            ),
            'rouge': self.rouge_scores(
                [r['generated_review'] for r in results],
                [r['actual_review'] for r in results]
            ),
            'n_samples': len(results)
        }
```

**File to create:** `data/evaluation/task_b_evaluator.py`

```python
# data/evaluation/task_b_evaluator.py

import numpy as np

class TaskBEvaluator:
    def ndcg_at_k(self, recommended: list,
                   relevant: set, k: int = 10) -> float:
        """Normalized Discounted Cumulative Gain @ k."""
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
        """Did any top-k recommendation hit a relevant item?"""
        return float(bool(set(recommended[:k]) & relevant))
    
    def evaluate(self, results: list[dict], k: int = 10) -> dict:
        """
        results: list of dicts with keys:
          recommended (list of item_ids),
          relevant (set of item_ids user actually interacted with)
        """
        ndcg_scores = [
            self.ndcg_at_k(r['recommended'], r['relevant'], k)
            for r in results
        ]
        hit_rates = [
            self.hit_rate_at_k(r['recommended'], r['relevant'], k)
            for r in results
        ]
        return {
            f'ndcg@{k}':     float(np.mean(ndcg_scores)),
            f'hit_rate@{k}': float(np.mean(hit_rates)),
            'n_users':       len(results)
        }
```

**File to create:** `data/evaluation/run_evaluation.py`

```python
# data/evaluation/run_evaluation.py
# Run this after Yelp pipeline to get evaluation numbers for solution paper

from task_a_evaluator import TaskAEvaluator
from task_b_evaluator import TaskBEvaluator
import json, asyncio

async def run_full_evaluation():
    """
    Runs full evaluation on held-out Yelp test set.
    Prints results table for solution paper.
    """
    print("\n" + "="*50)
    print("ARCHE — Full Evaluation Run")
    print("="*50)
    
    # Load test set
    with open("data/yelp_processed/test.json") as f:
        test_data = [json.loads(l) for l in f]
    
    print(f"\nTest set size: {len(test_data)} reviews")
    print("Running Task A evaluation (RMSE + ROUGE)...")
    
    # Task A evaluation
    # (call /v1/simulate-review for each test record,
    #  compare to held-out actual rating + review text)
    task_a_results = []
    # ... populate by calling the API ...
    
    evaluator_a = TaskAEvaluator()
    task_a_scores = evaluator_a.evaluate(task_a_results)
    
    print("\nTask A Results:")
    print(f"  RMSE (rating accuracy):  {task_a_scores['rmse']:.4f}")
    print(f"  ROUGE-1 (review text):   {task_a_scores['rouge']['rouge1']:.4f}")
    print(f"  ROUGE-2 (review text):   {task_a_scores['rouge']['rouge2']:.4f}")
    print(f"  ROUGE-L (review text):   {task_a_scores['rouge']['rougeL']:.4f}")
    
    print("\nRunning Task B evaluation (NDCG@10 + Hit Rate)...")
    
    # Task B evaluation
    # (call /v1/recommend for each user,
    #  compare to held-out actual items)
    task_b_results = []
    # ... populate by calling the API ...
    
    evaluator_b = TaskBEvaluator()
    task_b_scores = evaluator_b.evaluate(task_b_results, k=10)
    
    print("\nTask B Results:")
    print(f"  NDCG@10:                 {task_b_scores['ndcg@10']:.4f}")
    print(f"  Hit Rate@10:             {task_b_scores['hit_rate@10']:.4f}")
    print(f"  Users evaluated:         {task_b_scores['n_users']}")
    
    print("\n" + "="*50)
    print("SAVE THESE NUMBERS FOR THE SOLUTION PAPER")
    print("="*50)
    
    return task_a_scores, task_b_scores

if __name__ == "__main__":
    asyncio.run(run_full_evaluation())
```

---

### PRIORITY 2 — IMPORTANT

---

#### [P2.1] Docker Setup

**File to create:** `Dockerfile` (in project root)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ curl sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create data directories
RUN mkdir -p data/yelp_raw data/yelp_processed

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
    --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File to create:** `docker-compose.yml` (in project root)

```yaml
version: '3.8'

services:
  arche-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./data:/app/data
      - ./mock_data:/app/mock_data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  arche_data:
```

**Critical requirements for Docker:**
- Must use SQLite (not PostgreSQL) — keeps container self-contained
- Must use local vector store (not ChromaDB) — keeps container self-contained
- `docker-compose up` must start the API with zero external dependencies
- A judge with no prior setup must be able to run it with one command
- The `.env` file must only require `ANTHROPIC_API_KEY`

**File to create:** `.env.example`
```
ANTHROPIC_API_KEY=your_claude_api_key_here
ENVIRONMENT=development
```

---

#### [P2.2] Nigerian Context Module

**File to create:** `nigerian/register_detector.py`

```python
# nigerian/register_detector.py

NIGERIAN_MARKERS = {
    "casual_pidgin": [
        "abeg", "na im", "e be like", "no be", "wetin",
        "oga", "e don", "na so", "dem say", "wahala"
    ],
    "mixed_pidgin": [
        "sha", "abi", "sef", "jare", "nau", "ehen",
        "na wa", "e be like say"
    ],
    "nigerian_english": [
        "very okay", "too much", "not too bad",
        "jollof", "suya", "pepper soup", "eba", "egusi",
        "naija", "9ja", "lagos", "abuja"
    ]
}

def detect_register(review_texts: list[str]) -> str:
    """
    Detect user's language register from their review history.
    Returns: "casual_pidgin" | "mixed_pidgin" | 
             "nigerian_english" | "formal_english"
    """
    combined = " ".join(review_texts).lower()
    
    scores = {
        register: sum(
            1 for marker in markers if marker in combined
        )
        for register, markers in NIGERIAN_MARKERS.items()
    }
    
    max_score = max(scores.values())
    
    if max_score == 0:
        return "formal_english"
    
    return max(scores, key=scores.get)

def is_nigerian_user(review_texts: list[str]) -> bool:
    """Quick check — does this user exhibit Nigerian patterns?"""
    return detect_register(review_texts) != "formal_english"
```

**File to create:** `nigerian/calibration.py`

```python
# nigerian/calibration.py

REGISTER_PROMPTS = {
    "casual_pidgin": """
NIGERIAN USER — CASUAL PIDGIN REGISTER:
This user writes in Nigerian Pidgin English.
Use pidgin phrases naturally: "abeg", "na im be that", "e be like say",
"no be small thing", "dem say". Mix with English fluidly.
Short sentences. Direct. Expressive emotion.
""",
    "mixed_pidgin": """
NIGERIAN USER — MIXED LANGUAGE REGISTER:
This user mixes Nigerian English with occasional pidgin.
Use: "sha", "abi", "sef", "jare". Write mostly in English
but pepper Nigerian expressions naturally throughout.
""",
    "nigerian_english": """
NIGERIAN USER — NIGERIAN ENGLISH REGISTER:
This user writes in Nigerian English.
Use Nigerian English idioms: "very okay", "not too bad", 
"the food was much". Reference Nigerian context naturally.
Standard English structure with Nigerian flavor.
""",
    "formal_english": ""  # No special calibration needed
}

NIGERIAN_BEHAVIORAL_CONTEXT = """
NIGERIAN BEHAVIORAL SIGNALS TO APPLY:
- Value consciousness: Nigerians frequently compare price-to-value
- Portion sensitivity: quantity of food is culturally significant  
- Service pace: traffic context affects patience expectations
- Community reference: mentioning bringing others is common
- Direct criticism: Nigerian reviews tend to be direct and honest

CRITICAL: Match THIS USER'S specific tone from their history.
Nigerian context is background calibration — not foreground performance.
Do not exaggerate or stereotype. Be authentic to this user.
"""

def get_calibration_prompt(register: str) -> str:
    """Get the Nigerian calibration prompt for a detected register."""
    base = REGISTER_PROMPTS.get(register, "")
    if register == "formal_english":
        return ""
    return base + NIGERIAN_BEHAVIORAL_CONTEXT

def get_fewshot_examples(register: str, category: str) -> str:
    """
    Returns few-shot examples for the detected register.
    Populated from nigerian_users.json extracted by Yelp pipeline.
    """
    # Load from extracted Nigerian examples
    # (populated after Yelp pipeline runs)
    try:
        import json
        with open("data/yelp_processed/nigerian_users.json") as f:
            examples = [json.loads(l) for l in f
                       if json.loads(l).get('stars')]
        # Return 2-3 examples matching category
        filtered = [e for e in examples
                   if category.lower() in
                   str(e.get('categories','')).lower()][:3]
        if not filtered:
            filtered = examples[:3]
        return "\n".join([
            f"Example review ({e.get('stars')} stars): {e.get('text','')[:200]}"
            for e in filtered
        ])
    except FileNotFoundError:
        return ""  # Graceful fallback if Yelp data not yet downloaded
```

---

### PRIORITY 3 — ENHANCEMENT

---

#### [P3.1] Task A Frontend View

**File to create:** `frontend/TaskADemo.tsx`

Build a component that:
- Lets user select a demo persona from nigerian_personas (Ada, Chidi, Ngozi)
- Lets user select an unseen item from the catalog
- Calls `POST /v1/simulate-review`
- Shows: predicted star rating (1–5 stars visually), generated review text, behavioural_basis
- Style consistent with existing `RecommendationDemo.tsx`
- Add it to `App.tsx` navigation

---

#### [P3.2] Evaluation Dashboard View

**File to create:** `frontend/EvaluationView.tsx`

Build a component that:
- Shows live evaluation metrics: RMSE, NDCG@10, Hit Rate
- Fetches from `GET /v1/evaluation-results` (new lightweight endpoint)
- Shows which dataset was used (Yelp / mock)
- Style consistent with existing components

**Endpoint to add to main.py:**
```python
@app.get("/v1/evaluation-results")
async def get_evaluation_results():
    """Returns latest evaluation metrics for dashboard display."""
    # Load from saved evaluation output file
    try:
        with open("data/evaluation_results.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "message": "Run data/evaluation/run_evaluation.py first",
            "task_a": None, "task_b": None
        }
```

---

## Architecture Rules — Non-Negotiable

```
1. DO NOT replace pipeline.py with LangGraph.
   Custom pipeline is working and tested. LangGraph is
   post-submission roadmap only.

2. DO NOT replace SQLite with PostgreSQL.
   SQLite keeps Docker self-contained. Required for submission.

3. DO NOT replace local_vector_store.py with ChromaDB.
   Local vector store keeps Docker self-contained.

4. ALL 19 existing tests must pass after every change.
   Run both test files before marking any task complete.

5. ADD new files rather than modifying existing ones wherever
   possible. When main.py must be modified, make the smallest
   possible targeted change only.

6. ALL new endpoints follow existing patterns in main.py.
   Same Pydantic validation style. Same error responses.
   Same response format conventions.

7. DO NOT change the frontend framework.
   React + Vite + Tailwind + GSAP stays exactly as-is.
   New components follow existing component patterns.

8. Docker must be self-contained.
   The only external dependency is ANTHROPIC_API_KEY.
   Everything else runs inside the container.

9. Mock data stays.
   Yelp data is additive — it supplements, not replaces.
   The demo still works with mock data if Yelp is unavailable.
```

---

## Three Required Deliverables — Submission Checklist

```
DELIVERABLE 01 — Containerized App
[ ] Dockerfile exists and builds without errors
[ ] docker-compose.yml exists
[ ] docker-compose up starts API on port 8000
[ ] GET  /v1/health returns 200 inside container
[ ] POST /v1/simulate-review works inside container   ← Task A
[ ] POST /v1/recommend works inside container         ← Task B
[ ] Works on a clean machine with only ANTHROPIC_API_KEY in .env

DELIVERABLE 02 — Solution Paper (4-8 pages PDF)
[ ] Abstract with real RMSE and NDCG@10 numbers
[ ] Architecture section with simulation engine explanation
[ ] Results table: RMSE, ROUGE-1/2/L, NDCG@10, Hit Rate@10
[ ] Ablation study: simulation-grounded vs direct generation
[ ] Nigerian contextualization section with examples
[ ] Future work referencing full ARCHE vision
[ ] 4-8 pages — not over or under
[ ] Submitted as PDF

DELIVERABLE 03 — GitHub Repository
[ ] Repository is public
[ ] README has docker-compose up instructions (one command)
[ ] All agent/pipeline logic is well-commented
[ ] requirements.txt is complete and pinned
[ ] .env.example documents all required variables
[ ] No API keys committed
[ ] Modular structure — each component is independently readable
```

---

## Current Status at a Glance

```
✅ Task B /v1/recommend           — working
✅ /v1/simulate                   — working (shared brain for both tasks)
✅ /v1/ingest, /v1/explain        — working
✅ Memory layer (SQLite + vectors) — working
✅ Frontend (React + Vite)         — working
✅ 19 passing tests                — must stay passing
✅ Custom pipeline orchestration   — working

🔴 POST /v1/simulate-review       — MISSING (Task A — build first)
🔴 Yelp dataset integration        — MISSING (needed for evaluation)
🔴 Evaluation scripts              — MISSING (needed for solution paper)
🟡 Docker setup                    — MISSING (required for submission)
🟡 Nigerian context module         — MISSING (bonus marks)
🟢 TaskADemo.tsx                   — MISSING (demo quality)
🟢 EvaluationView.tsx              — MISSING (demo quality)
```

---

## Where To Start

**Right now, build this:**

`POST /v1/simulate-review` in `api/routes/task_a.py`

Then add it to `main.py` with a single import line.

Then run all tests. Then move to P1.2 (Yelp pipeline).

Do not proceed to Priority 2 until Priority 1 is complete and all 19 tests pass.

---

## Questions?

If anything in this brief is unclear, ask before building.
It is faster to clarify than to rebuild.

The full architectural specification, Nigerian context strategy,
and master build checklist are in `ARCHE_HackAlign.md`.
Read it alongside this document.

---

*ARCHE Co-pilot Alignment Prompt v1.0 — May 2026*
*Give this file + ARCHE_HackAlign.md to co-pilot together.*
