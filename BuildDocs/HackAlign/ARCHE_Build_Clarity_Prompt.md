# ARCHE — Build Clarity & Implementation Prompt
## What The System Must Actually Do — Full Technical Specification

---

> **How to use this file:** Read this alongside the full brief explanation
> document. This file tells you EXACTLY what to build, how each piece
> connects, and what judges will test. No guessing. No ambiguity.

---

## The One-Sentence Summary

ARCHE is a containerized LLM agent system that:
- Takes a user persona as input
- Runs a behavioral simulation of that user
- Either generates a review + rating (Task A) OR ranked recommendations (Task B)
- Explains its reasoning on every output
- Runs with `docker-compose up` on a clean machine

---

## How The LLM Agent Actually Works In This System

This is not a chatbot. This is not a simple LLM call.
The LLM agent is the **reasoning engine** that orchestrates
the entire pipeline. It does NOT answer directly — it thinks,
retrieves, simulates, then acts.

### The Agent Loop — Every Request Goes Through This

```
REQUEST ARRIVES
      │
      ▼
STEP 1: AGENT THINKS
  "What do I know about this user?
   What context am I operating in?
   What task am I performing — review or recommend?"
      │
      ▼
STEP 2: AGENT RETRIEVES (Tool Call → memory_manager)
  → Fetches user's behavioral history
  → Fetches population cohort priors (for cold start)
  → Fetches any relevant contextual signals
      │
      ▼
STEP 3: AGENT SIMULATES (Tool Call → simulation engine)
  → Builds behavioral snapshot:
    { current_intent, preference_cluster,
      top_affinities, rejection_signals,
      exploration_readiness, writing_register }
  → For new users: infers from context + population priors
      │
      ▼
STEP 4: AGENT REASONS
  "This user is value-conscious. Evening context active.
   Nigerian English register detected. Western food
   skepticism signal present. Exploration readiness: low."
      │
      ▼
STEP 5: AGENT ACTS
  → Task A: generates review + rating from simulation
  → Task B: ranks recommendations from simulation
      │
      ▼
STEP 6: AGENT EXPLAINS
  → Generates reasoning trace: why this output,
    what drove it, what was considered and rejected
      │
      ▼
STRUCTURED OUTPUT RETURNED
```

### How To Implement The Agent Loop In Existing pipeline.py

Do NOT replace pipeline.py. Extend it.

The agent loop maps to pipeline.py like this:

```python
# pipeline.py — existing sequential pipeline
# The LLM is called at Steps 1, 4, and 6
# Steps 2, 3, 5 are tool calls to existing modules

async def run_agent_pipeline(request, task: str):
    
    # STEP 2: Retrieve
    memory = await memory_manager.retrieve(request.user_token)
    context = extract_context_signals(request.context)
    
    # STEP 3: Simulate  
    simulation = await simulate_user(
        history=memory,
        context=context,
        cold_start=(memory is None or len(memory) < 3)
    )
    
    # STEP 1 + 4 + 6: LLM reasons, acts, explains
    if task == "review":
        result = await llm_generate_review(simulation, request.item)
    elif task == "recommend":
        result = await llm_rank_recommendations(simulation, request.context)
    
    return result
```

The LLM receives the simulation output as context.
It does NOT receive raw user history directly.
The simulation is the intermediary — that is the innovation.

---

## Task A — Exact Implementation Specification

### What judges will call

```
POST /v1/simulate-review
```

### Exact request format judges will send

```json
{
  "user_persona": {
    "user_id": "any_string",
    "review_history": [
      {
        "item_name": "string — name of item user reviewed",
        "category": "string — food, electronics, books, etc",
        "rating": 4,
        "review_text": "string — what the user actually wrote"
      }
    ]
  },
  "item_details": {
    "name": "string — item to review (user has NOT seen this)",
    "category": "string",
    "price_tier": "budget | mid | premium | luxury",
    "attributes": {}
  },
  "context": {
    "time_of_day": "morning | afternoon | evening | night",
    "region": "string — optional location context"
  }
}
```

### Exact response format judges expect

```json
{
  "predicted_rating": 3,
  "generated_review": "Full review text in the user's voice",
  "confidence": 0.82,
  "reasoning": "Plain English explanation of what drove this output",
  "behavioral_basis": {
    "register_detected": "nigerian_english | formal_english | mixed_pidgin | casual_pidgin",
    "dominant_signal": "value_conscious | quality_first | experience_seeker",
    "context_applied": "evening session boosted comfort food affinity",
    "cold_start_used": false
  }
}
```

### The LLM prompt that generates Task A output

The agent receives the simulation snapshot and generates the review.
It does NOT receive raw history — only the behavioral snapshot.

```python
TASK_A_SYSTEM_PROMPT = """
You are ARCHE's Review Generation Agent.

You have been given:
1. A behavioral simulation of a specific user
2. Details of an item they have never reviewed
3. Their detected writing register and cultural context

Your job: Generate the review this user WOULD write
and the rating they WOULD give — based entirely on
the behavioral simulation provided.

RULES:
- Match the user's exact writing register from the simulation
- Match their complaint patterns and praise patterns
- The rating must be an integer 1-5
- The review must sound like THIS specific person
- Never be generic — every output must be personalized
- If Nigerian register detected: apply Nigerian voice calibration
- Output ONLY valid JSON, no markdown, no preamble

OUTPUT FORMAT:
{
  "predicted_rating": <int 1-5>,
  "generated_review": "<review text>",
  "confidence": <float 0-1>,
  "reasoning": "<one sentence: what drove this output>",
  "behavioral_basis": {
    "register_detected": "<register>",
    "dominant_signal": "<signal>",
    "context_applied": "<context effect>",
    "cold_start_used": <bool>
  }
}
"""

TASK_A_USER_PROMPT = """
BEHAVIORAL SIMULATION OF USER:
{simulation_snapshot}

WRITING REGISTER DETECTED: {register}
NIGERIAN CONTEXT: {nigerian_context}

ITEM TO REVIEW (user has never seen this):
Name: {item_name}
Category: {item_category}
Price tier: {price_tier}
Attributes: {attributes}

CURRENT CONTEXT:
{context}

FEW-SHOT STYLE EXAMPLES FROM SIMILAR USERS:
{fewshot_examples}

Generate the review and rating.
Match this specific user's voice exactly.
Return ONLY valid JSON.
"""
```

---

## Task B — Exact Implementation Specification

### What judges will call

```
POST /v1/recommend
```

### Exact request format judges will send

```json
{
  "user_persona": {
    "user_id": "any_string",
    "review_history": [
      {
        "item_name": "string",
        "category": "string",
        "rating": 4,
        "review_text": "string"
      }
    ]
  },
  "context": {
    "time_of_day": "evening",
    "occasion": "dinner with friends",
    "location_tier": "Lagos Mainland",
    "mood": "optional string"
  },
  "n": 10,
  "domain_filter": "optional — food | books | electronics | any"
}
```

### Exact response format judges expect

```json
{
  "recommendations": [
    {
      "rank": 1,
      "item_id": "string",
      "item_name": "string",
      "category": "string",
      "confidence": 0.91,
      "recommendation_type": "precision | adjacent_exploration | discovery",
      "reasoning": "Why this item for this user right now"
    }
  ],
  "diversity_score": 0.73,
  "exploration_ratio": 0.35,
  "cold_start_used": false,
  "cross_domain_applied": false,
  "simulation_summary": "Brief description of user behavioral snapshot used"
}
```

### The 60/25/15 Split — Must Be Implemented

Every recommendation set must follow this structure:

```python
def build_recommendation_set(simulation, catalog, n=10):
    n_precision  = int(n * 0.60)   # items that strongly match simulation
    n_adjacent   = int(n * 0.25)   # items at edge of preference space
    n_discovery  = n - n_precision - n_adjacent  # deliberate novelty

    precision  = rank_by_affinity(simulation, catalog, n_precision)
    adjacent   = rank_by_adjacency(simulation, catalog, n_adjacent)
    discovery  = inject_discovery(simulation, catalog, n_discovery)

    all_items = precision + adjacent + discovery
    return apply_diversity_penalty(all_items)
```

### Cold Start — Must Be Handled Explicitly

When user has fewer than 3 reviews:

```python
def handle_cold_start(user_history, context):
    if len(user_history) < 3:
        # Do NOT return error
        # Do NOT return generic popular items
        # DO infer from context + population priors
        
        cluster = assign_to_nearest_cluster(context)
        simulation = simulate_from_population_priors(
            cluster=cluster,
            context=context,
            available_history=user_history  # use what we have
        )
        simulation["cold_start_used"] = True
        simulation["cold_start_confidence"] = calculate_confidence(
            context, len(user_history)
        )
        return simulation
```

### Cross-Domain — Must Be Handled Explicitly

When user has history in domain A but request is in domain B:

```python
def handle_cross_domain(simulation, target_domain):
    # Behavioral clusters transfer across domains
    # Value-conscious user in food → value-conscious in books
    # Extract domain-agnostic behavioral signals
    # Apply them to target domain catalog
    
    domain_agnostic_signals = extract_transferable_signals(simulation)
    cross_domain_recs = rank_in_domain(
        signals=domain_agnostic_signals,
        domain=target_domain
    )
    return cross_domain_recs
```

### Multi-turn Conversation Support

The brief says "multiturn scenarios". This means:

```
Turn 1: User says "recommend me something for tonight"
Agent returns 10 recommendations + asks clarifying question

Turn 2: User says "something more casual, with friends"
Agent UPDATES the context → re-runs simulation → new recommendations

Implementation: Pass conversation history in request:
{
  "conversation_history": [
    {"role": "user", "content": "recommend me something for tonight"},
    {"role": "assistant", "content": "...previous recommendations..."}
  ],
  "new_message": "something more casual, with friends"
}
```

Add a `/v1/recommend/chat` endpoint for this.

---

## The Evaluation Scripts — What Judges Will Run

### Critical: judges will run these scripts themselves

Your repo must include working evaluation scripts.
Judges will call them directly and expect to see numbers.

### Script 1 — Task A Evaluation

```bash
# Judges run this command
python data/evaluation/run_evaluation.py --task a --dataset yelp

# Expected output:
# ================================================
# ARCHE Task A Evaluation — Yelp Dataset
# ================================================
# Test users evaluated: 500
# 
# Rating Accuracy:
#   RMSE: 0.87  (lower is better, random baseline ~1.5)
#
# Review Text Quality:
#   ROUGE-1: 0.42
#   ROUGE-2: 0.21  
#   ROUGE-L: 0.38
#
# Cold Start Performance (users with < 3 reviews):
#   RMSE: 1.12
#   Test users: 47
# ================================================
```

### Script 2 — Task B Evaluation

```bash
# Judges run this command
python data/evaluation/run_evaluation.py --task b --dataset yelp

# Expected output:
# ================================================
# ARCHE Task B Evaluation — Yelp Dataset
# ================================================
# Test users evaluated: 500
#
# Ranking Quality:
#   NDCG@10:     0.34
#   Hit Rate@10: 0.61
#
# Cold Start Performance (users with < 3 reviews):
#   NDCG@10:     0.22
#   Hit Rate@10: 0.44
#   Test users:  47
#
# Cross-Domain Performance:
#   NDCG@10:     0.28
#   Test pairs:  120
# ================================================
```

### Script 3 — Ablation Study (For Solution Paper)

```bash
# Runs comparison: with simulation vs without simulation
python data/evaluation/ablation.py --dataset yelp

# Expected output:
# ================================================
# ARCHE Ablation Study
# ================================================
# Task A — RMSE:
#   With simulation engine:    0.87
#   Without simulation engine: 1.24
#   Improvement:               28.7%
#
# Task B — NDCG@10:
#   With simulation engine:    0.34
#   Without simulation engine: 0.21
#   Improvement:               61.9%
# ================================================
```

These numbers go directly into the solution paper.
Build these scripts alongside the main system.

---

## The Web Interface — What Both Tasks Need

The brief says "web application OR API endpoint."
Build BOTH. Here is what each task's web interface needs:

### Task A Web Interface

```
Page: /demo/review-simulation

Input panel:
  - User persona builder:
    * Add past reviews (item name, category, rating, text)
    * OR select from pre-built demo personas (Ada, Chidi, Ngozi)
  - Item to review:
    * Item name input
    * Category selector
    * Price tier selector
  - Context:
    * Time of day selector
    * Region/location input

Output panel:
  - Star rating display (1-5 stars visual)
  - Generated review text (full, formatted)
  - Behavioral basis card:
    * Register detected badge
    * Dominant signal badge  
    * Context applied note
    * Cold start indicator if applicable
  - Confidence score display
```

### Task B Web Interface

```
Page: /demo/recommendations

Input panel:
  - User persona builder (same as Task A)
  - Context builder:
    * Time of day
    * Occasion (solo, friends, date, family)
    * Location tier
  - Optional: domain filter
  - Optional: conversation mode toggle

Output panel:
  - 10 recommendation cards, each showing:
    * Item name + category
    * Confidence score
    * Recommendation type badge (PRECISION / EXPLORATION / DISCOVERY)
    * Reasoning (expandable)
  - Diversity score gauge
  - Exploration ratio bar (60/25/15 visualization)
  - Cold start indicator if applicable

Conversation mode (when toggled):
  - Chat interface
  - User can refine: "more casual", "cheaper options", "near me"
  - Agent updates recommendations dynamically
```

### Evaluation Dashboard

```
Page: /demo/evaluation

Shows live metrics from evaluation scripts:
  - Task A: RMSE, ROUGE-1/2/L scores
  - Task B: NDCG@10, Hit Rate@10
  - Dataset used (Yelp / Amazon / Goodreads)
  - Ablation comparison chart
  - Cold start performance separately shown
```

---

## How Judges Assess Code Reproducibility — The Exact Steps

```bash
# Step 1: Clone
git clone https://github.com/yourteam/arche
cd arche

# Step 2: Configure (only thing judge needs to do)
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY=sk-...

# Step 3: Run (one command)
docker-compose up --build

# Step 4: Verify health
curl http://localhost:8000/v1/health
# Must return: {"status": "healthy", "version": "1.0.0"}

# Step 5: Test Task A
curl -X POST http://localhost:8000/v1/simulate-review \
  -H "Content-Type: application/json" \
  -d @demo/sample_task_a_request.json
# Must return valid JSON with predicted_rating and generated_review

# Step 6: Test Task B
curl -X POST http://localhost:8000/v1/recommend \
  -H "Content-Type: application/json" \
  -d @demo/sample_task_b_request.json
# Must return valid JSON with recommendations array

# Step 7: Run evaluation (optional but impressive)
docker-compose exec arche-api \
  python data/evaluation/run_evaluation.py --task both --dataset yelp
# Must print RMSE, ROUGE, NDCG@10, Hit Rate numbers
```

### Files judges need to find in the repo

```
README.md               ← Setup instructions, architecture overview
docker-compose.yml      ← One-command startup
Dockerfile              ← Self-contained build
.env.example            ← Shows required variables (no real keys)
requirements.txt        ← Pinned dependencies
demo/
  sample_task_a_request.json   ← Ready-to-use test input
  sample_task_b_request.json   ← Ready-to-use test input
data/evaluation/
  run_evaluation.py            ← Runnable evaluation script
  task_a_evaluator.py          ← RMSE + ROUGE computation
  task_b_evaluator.py          ← NDCG@10 + Hit Rate computation
  ablation.py                  ← Simulation vs no-simulation comparison
```

---

## The Three Demo Personas — Build These Into The System

These are used for the web interface and the sample request files.
They should be in `demo/personas.json`.

```json
[
  {
    "persona_id": "ada_001",
    "persona_name": "Ada",
    "description": "New user. Zero prior history. Evening. Mobile. Social media referral.",
    "review_history": [],
    "context": {
      "time_of_day": "evening",
      "device": "mobile",
      "entry_point": "social_media",
      "region": "Lagos Island"
    },
    "demo_purpose": "Cold start demonstration"
  },
  {
    "persona_id": "chidi_002",
    "persona_name": "Chidi",
    "description": "Returning user. 5 reviews. Nigerian English register. Value-conscious.",
    "review_history": [
      {
        "item_name": "Chicken Republic Lekki",
        "category": "Fast Food",
        "rating": 4,
        "review_text": "Jollof rice was fire but the service was slow sha. Would go back sha."
      },
      {
        "item_name": "KFC Marina",
        "category": "Fast Food",
        "rating": 3,
        "review_text": "Consistent but overpriced for what you get. The portions too small."
      },
      {
        "item_name": "The Place Lekki",
        "category": "Nigerian Cuisine",
        "rating": 5,
        "review_text": "This place na 5 star abeg. The pepper soup alone is worth the trip."
      },
      {
        "item_name": "Mr Biggs",
        "category": "Fast Food",
        "rating": 2,
        "review_text": "Nostalgic but needs serious upgrade. The food no reach standard."
      },
      {
        "item_name": "Barcelos",
        "category": "Fast Food",
        "rating": 4,
        "review_text": "Not bad at all. The chicken was very okay and value for money sef."
      }
    ],
    "context": {
      "time_of_day": "evening",
      "device": "mobile",
      "region": "Lagos Mainland"
    },
    "demo_purpose": "Nigerian context + returning user demonstration"
  },
  {
    "persona_id": "ngozi_003",
    "persona_name": "Ngozi",
    "description": "Power user. 12 reviews across food + books. Preference drift detectable.",
    "review_history": [
      {
        "item_name": "Things Fall Apart",
        "category": "African Literature",
        "rating": 5,
        "review_text": "A masterpiece. Achebe captures Igbo culture with devastating precision."
      },
      {
        "item_name": "Half of a Yellow Sun",
        "category": "African Literature",
        "rating": 5,
        "review_text": "Adichie is brilliant. This book will stay with you forever."
      },
      {
        "item_name": "The Alchemist",
        "category": "Fiction",
        "rating": 3,
        "review_text": "Overhyped. Some good ideas but too simplistic for serious readers."
      },
      {
        "item_name": "Nok by Alara",
        "category": "Fine Dining",
        "rating": 5,
        "review_text": "Absolutely stunning experience. The food tells a story. Worth every naira."
      },
      {
        "item_name": "Yellowchilli",
        "category": "Nigerian Cuisine",
        "rating": 4,
        "review_text": "Consistently good. The suya pepper is different from anywhere else."
      }
    ],
    "context": {
      "time_of_day": "afternoon",
      "device": "desktop",
      "region": "Abuja"
    },
    "demo_purpose": "Cross-domain (books + food) + power user demonstration"
  }
]
```

---

## Sample Request Files — Must Exist For Reproducibility

### demo/sample_task_a_request.json

```json
{
  "user_persona": {
    "user_id": "chidi_002",
    "review_history": [
      {
        "item_name": "Chicken Republic Lekki",
        "category": "Fast Food",
        "rating": 4,
        "review_text": "Jollof rice was fire but the service was slow sha. Would go back sha."
      },
      {
        "item_name": "KFC Marina",
        "category": "Fast Food",
        "rating": 3,
        "review_text": "Consistent but overpriced for what you get. The portions too small."
      }
    ]
  },
  "item_details": {
    "name": "Domino's Pizza Lagos",
    "category": "Fast Food",
    "price_tier": "mid",
    "attributes": {
      "cuisine": "Western",
      "delivery_available": true,
      "dine_in": true
    }
  },
  "context": {
    "time_of_day": "evening",
    "region": "Lagos Mainland"
  }
}
```

### demo/sample_task_b_request.json

```json
{
  "user_persona": {
    "user_id": "chidi_002",
    "review_history": [
      {
        "item_name": "Chicken Republic Lekki",
        "category": "Fast Food",
        "rating": 4,
        "review_text": "Jollof rice was fire but the service was slow sha."
      },
      {
        "item_name": "The Place Lekki",
        "category": "Nigerian Cuisine",
        "rating": 5,
        "review_text": "This place na 5 star abeg. The pepper soup alone is worth the trip."
      }
    ]
  },
  "context": {
    "time_of_day": "evening",
    "occasion": "dinner with friends",
    "location_tier": "Lagos Mainland"
  },
  "n": 10
}
```

---

## What To Build In This Session

Work through these in exact order.
Confirm all tests pass before moving to the next item.

### Item 1 — Align existing pipeline to agent loop pattern
- Verify pipeline.py follows: retrieve → simulate → act → explain
- Add reasoning trace generation to every response
- Ensure LLM receives simulation snapshot (not raw history)

### Item 2 — Verify Task A endpoint matches exact spec above
- Request schema matches exactly
- Response schema matches exactly
- LLM prompt matches Task A prompt above
- Behavioral basis included in every response
- Nigerian register detection working

### Item 3 — Verify Task B endpoint matches exact spec above
- 60/25/15 exploration split implemented
- Cold start explicitly handled — no errors, no generic fallback
- Cross-domain handling implemented
- Multi-turn /v1/recommend/chat endpoint added
- Reasoning trace on every recommendation item

### Item 4 — Create demo files
- `demo/personas.json` with Ada, Chidi, Ngozi
- `demo/sample_task_a_request.json`
- `demo/sample_task_b_request.json`

### Item 5 — Create evaluation scripts
- `data/evaluation/task_a_evaluator.py` — RMSE + ROUGE
- `data/evaluation/task_b_evaluator.py` — NDCG@10 + Hit Rate
- `data/evaluation/ablation.py` — simulation vs no-simulation
- `data/evaluation/run_evaluation.py` — master runner

### Item 6 — Update web interface
- Add Task A demo page matching spec above
- Add Task B demo page with conversation mode
- Add evaluation dashboard page
- Both tasks accessible from main nav

### Item 7 — Docker + reproducibility
- Dockerfile builds cleanly
- docker-compose up starts everything
- Health check works
- Both sample request files work via curl
- Evaluation script runs inside container

---

## Rules — Do Not Break These

```
1. All existing tests must pass after every change
2. Do not replace pipeline.py, memory_manager.py, or local_vector_store.py
3. LLM always receives simulation snapshot — never raw history directly
4. Every response includes reasoning trace — no black box outputs ever
5. Cold start never returns an error or generic popular items
6. Nigerian calibration applies automatically when register detected
7. Docker must work with only ANTHROPIC_API_KEY in .env
8. mock_data/ stays untouched — Yelp/Amazon/Goodreads data is additive
```

---

*ARCHE Build Clarity Prompt v1.0 — May 2026*
*Give this file alongside:*
*  - ARCHE_Copilot_Alignment_Prompt.md*
*  - ARCHE_HackAlign.md*
*  - ARCHE_Dataset_Pipeline_Prompt.md*
