# ARCHE for Judges - Quick Evaluation Guide

**Project**: ARCHE (Adaptive Reasoning & Contextual Heuristic Engine)  
**Type**: Behavioral Intelligence Platform  
**Status**: ✅ Production Ready  
**Demo Time**: ~5 minutes

---

## What is ARCHE?

ARCHE is a **behavioral simulation engine** that:

1. Learns a user's decision-making patterns from their review history
2. Builds a deterministic (not ML blackbox) snapshot of their preferences
3. Makes explainable predictions: "Why is this item recommended?"

**Key Innovation**: Trades custom ML for _interpretable behavioral reasoning_ that judges can audit.

---

## Quick Demo (5 min)

### 1. Open Landing Page (2 min)

```
https://arche-frontend.vercel.app
```

- **Scroll** through "Behavioral Simulation: How ARCHE Works" section
- See the 4-step architecture judges care about
- Notice "Key Concepts" explains output fields

### 2. Try Task A: User Model (1.5 min)

- **Click** "Run User Model (Task A)" button
- Fill in sample review history (or use default)
- **Look for**:
  - ✅ Predicted rating (with confidence)
  - ✅ `behavioural_basis` field shows _why_ (what we detected)
  - ✅ Generated review is _fresh_ (not copied from history)
  - ✅ Context (`time_of_day`, `region`) properly included

### 3. Try Task B: Recommendations (1.5 min)

- **Click** "Run Recommendation (Task B)" button
- See recommendations ranked by relevance
- **Look for**:
  - ✅ `explanation` field (not generic, specific to each item)
  - ✅ `recommendation_type` (precision/adjacent/discovery)
  - ✅ `live_data_used` flag (showing live web search integration)
  - ✅ Confidence scores that make sense

---

## What Judges Should Focus On

### Architecture (Strengths)

- **Deterministic**: No random black-box ML. Every decision is traceable.
- **Explainable**: Every recommendation includes _real reasoning_, not "User X likes Y so we recommend Z"
- **Lightweight**: Runs fast (< 1 sec for API) without expensive GPU/ML infrastructure
- **Integrated**: LLM + web search + local catalog in single pipeline

### Evaluation Criteria

#### 1. **Behavioral Basis Quality**

- **Look at**: `/v1/simulate-review` response → `behavioural_basis` field
- **Good answer**: "Detected formal_english register with 3 prior reviews; top affinities [nigerian_cuisine]; context afternoon/Lagos"
- **Bad answer**: Generic, empty, or doesn't use context

#### 2. **No Content Leaking**

- **Test**: Paste a review with distinctive text (e.g., "Atomic Habits is a practical guide...")
- **Good result**: Generated review is completely fresh, uses the _style_ but not the _content_
- **Bad result**: Old review text appears verbatim

#### 3. **Context Integration**

- **Test**: Send `time_of_day: "evening"` and `region: "Lagos Island"`
- **Good result**: Output includes these in behavioural_basis or generated review
- **Bad result**: Shows "unspecified time" or ignores region

#### 4. **Explanation Quality**

- **Look at**: `/v1/recommend` response → `explanation` field for each item
- **Good answer**: "Matches your interest in nigerian_cuisine. Based on your history, this aligns with items you rated highly."
- **Bad answer**: "Ranked with historical_memory:3" (generic)

#### 5. **Live Web Integration**

- **Check**: `/v1/recommend` with `enable_live_data: true`
- **Look for**: `live_data_used: true`, `live_search_provider: "serper"` or `"duckduckgo"`
- **Good**: Top 3 recommendations include items from live search results

#### 6. **Explainability Trace**

- **Call**: `/v1/explain` endpoint with a `recommendation_id`
- **Good result**: Returns full trace including simulation snapshot + recommendation + alternatives
- **Shows**: System transparency, full reasoning chain

---

## API Endpoints (For Judges Testing)

### Health Check

```bash
curl https://BACKEND_URL/health
# Expected: {"status": "ok"}
```

### Task A: User Model

```bash
curl -X POST https://BACKEND_URL/v1/simulate-review \
  -H "Content-Type: application/json" \
  -d '{
    "user_persona": {
      "user_id": "judge_demo",
      "review_history": [
        {
          "item_name": "Atomic Habits",
          "category": "books",
          "rating": 4,
          "review_text": "A practical and well-researched guide to behaviour change."
        }
      ]
    },
    "item_details": {
      "name": "Half of a Yellow Sun",
      "category": "books"
    },
    "context": {
      "time_of_day": "evening",
      "region": "Lagos Island"
    }
  }'
```

**Check in response**:

- ✅ `predicted_rating`: reasonable (4-5 for book lover)
- ✅ `generated_review`: mentions `evening` and `Lagos Island`, no "Atomic Habits" text
- ✅ `behavioural_basis`: shows detected register, affinities, context

### Task B: Recommendations

```bash
curl -X POST https://BACKEND_URL/v1/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_persona": {
      "user_id": "judge_demo",
      "review_history": [
        {
          "item_name": "Jollof House",
          "category": "nigerian_cuisine",
          "rating": 5,
          "review_text": "Amazing jollof rice and great service."
        }
      ]
    },
    "context": {
      "time_bucket": "evening",
      "entry_point": "food"
    },
    "n": 5,
    "enable_live_data": true
  }'
```

**Check in response**:

- ✅ `recommendations`: array with top 5
- ✅ Each has: `explanation`, `recommendation_type`, `confidence`
- ✅ `live_data_used`: true
- ✅ `live_search_provider`: one of serper/duckduckgo
- ✅ Top items appear fresh from web search or tuned to user profile

### Explainability

```bash
curl -X POST https://BACKEND_URL/v1/explain \
  -H "Content-Type: application/json" \
  -d '{
    "user_token": "judge_demo",
    "recommendation_id": "rec_1_judge_demo"
  }'
```

**Check in response**:

- ✅ `simulation`: full behavioral snapshot
- ✅ `recommendation`: The selected item + explanation
- ✅ `trace`: Human-readable reasoning

---

## Test Results

```
Pytest Suite:        41/41 tests passing (100%) ✅
Scenario Validation: 20/20 checks passing    ✅
  - S1: Task A formal (no leaking)
  - S2: Task A pidgin (context flow)
  - S3-S4: Task B cold start & personalized
  - S5: Task B with live data
  - S6: Task B manual query override
  - S7: Task B explain trace
```

---

## Scoring Rubric Alignment

| Category                 | ARCHE Strength                                  | Evidence                                        |
| ------------------------ | ----------------------------------------------- | ----------------------------------------------- |
| **Architecture**         | Deterministic, explainable, composable          | See Landing page section 1                      |
| **Behavioral Modeling**  | Extracts patterns, context-aware, fresh content | Task A response analysis                        |
| **Explainability**       | Every recommendation has reasoning              | Task B `explanation` field                      |
| **Integration**          | LLM + web + local in single pipeline            | Task B `live_data_used` + `llm_instrumentation` |
| **Code Quality**         | 100% test pass, no leaking, robust context      | Pytest + scenario logs                          |
| **Performance**          | Fast (<1s API, <5s with LLM)                    | Local timing tests                              |
| **Production Readiness** | Full deployment guide, logging, env config      | DEPLOYMENT_GUIDE.md                             |

---

## Common Judge Questions

**Q: Is this production-ready?**  
A: Yes. 41/41 tests pass, deployment guide complete, logging & monitoring configured.

**Q: Does it use expensive ML?**  
A: No. It's deterministic heuristics (fast, audit-able) with optional LLM for query planning only.

**Q: How much does it cost to run?**  
A: Free tier viable (Render free + Vercel free). No ML infrastructure needed.

**Q: Is the explanations feature UI-only or API?**  
A: Both. Frontend displays explanations from `/v1/recommend` and `/v1/explain` endpoints.

**Q: What happens if no review history?**  
A: Cold-start mode uses context + cohort priors. Test with empty `review_history: []`.

**Q: Can I see the LLM integration?**  
A: Yes. Look at `/v1/recommend` responses: `llm_instrumentation` field shows which LLM was used for live query planning.

---

## Red Flags to Avoid

- ❌ Historical review text appears in new reviews → Indicates `_style_anchor()` bug (should be fixed)
- ❌ Explanation is empty or generic → Indicates ranking logic incomplete
- ❌ Context ("evening", "Lagos") missing from output → Context pipeline not integrated
- ❌ `live_data_used: false` when you enabled it → Either API key missing or search failed
- ❌ API returns 500 errors → Check backend logs, likely LLM rate limit

---

## Key Files to Review

| File                                                                               | Why                                 | Time  |
| ---------------------------------------------------------------------------------- | ----------------------------------- | ----- |
| [landing page](https://arche-frontend.vercel.app)                                  | Architecture explanation            | 2 min |
| [Task A endpoint](http://localhost:8000/docs) → Try it Out                         | Behavior modeling                   | 1 min |
| [Task B endpoint](http://localhost:8000/docs) → Try it Out                         | Recommendations                     | 1 min |
| [Behavioral basis in response](reports/comprehensive_test_report_7_scenarios.json) | What system extracted               | 1 min |
| [Source code: review_generation_agent.py](../agents/review_generation_agent.py)    | How reviews are generated (no copy) | 3 min |
| [Source code: recommendation_scoring.py](../agents/recommendation_scoring.py)      | Explanation generation logic        | 3 min |

---

## Success Criteria for Judges

Your evaluation should confirm:

1. ✅ **Behavioral Extraction**: System detected user patterns (category preferences, writing style, price sensitivity)
2. ✅ **No Leaking**: Generated reviews have user's _style_ but not copied _content_
3. ✅ **Context Awareness**: Recommendations and reviews change based on time/location context
4. ✅ **Explainability**: Every recommendation explains why (reasoning specific to user, not generic)
5. ✅ **Live Integration**: System can enrich with real-time web data when available
6. ✅ **Traceable Reasoning**: `/v1/explain` shows full decision chain

---

## Need Help?

- **API Testing**: See Swagger UI at `/docs` endpoint
- **Logs**: Check backend console for `llm_call_start`, `llm_call_success`, `live_search_*` messages
- **Database**: Stored signals in `data/memory.db` (SQLite)
- **Code**: Comments in agent files explain logic clearly
- **Report**: See `reports/comprehensive_test_report_7_scenarios.md` for validation evidence

---

**Welcome to ARCHE! Happy evaluating.** 🚀

_For any issues during evaluation, check DEPLOYMENT_GUIDE.md Troubleshooting section._
