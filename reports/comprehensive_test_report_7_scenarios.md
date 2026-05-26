# ARCHE Comprehensive Test Report (7 Scenarios)

- Generated at (UTC): `2026-05-26T09:12:47.377458+00:00`
- API Base URL: `http://localhost:8000`

## S1 - Task A Formal Persona
- Endpoint: `/v1/simulate-review`
- HTTP Status: `200`
- has_llm_instrumentation: `PASS`
- has_behavioural_basis: `PASS`
- no_atomic_copy_leak: `PASS`
- Predicted rating: `4`
- Review excerpt: `Half of a Yellow Sun presents as solid across african_literature offerings. In the context of afternoon and given the Lagos Island location, this item demonstrates consistent value`
- LLM instrumentation: `{"used": false, "provider": null, "model": null}`

## S2 - Task A Mixed Pidgin Persona
- Endpoint: `/v1/simulate-review`
- HTTP Status: `200`
- has_llm_instrumentation: `PASS`
- context_reflected: `PASS`
- no_mr_biggs_copy_leak: `PASS`
- Predicted rating: `4`
- Review excerpt: `The Place Restaurant Lekki presents as solid across food offerings. In the context of evening and given the Lagos Mainland location, this item demonstrates consistent value. cuisin`
- LLM instrumentation: `{"used": false, "provider": null, "model": null}`

## S3 - Task B Cold Start No Live
- Endpoint: `/v1/recommend`
- HTTP Status: `200`
- cold_start_handled: `PASS`
- live_data_used_false: `PASS`
- has_explanations: `PASS`
- Top 3 recommendations:
  - 1. `Suya Spot` | type=`precision` | explanation=`Matches your interest in food. Based on your history, this aligns with items you rated highly.`
  - 2. `Palmwine Diner` | type=`precision` | explanation=`Matches your interest in food. Based on your history, this aligns with items you rated highly.`
  - 3. `Evening Eats` | type=`precision` | explanation=`Matches your interest in food. Based on your history, this aligns with items you rated highly.`

## S4 - Task B Personalized No Live
- Endpoint: `/v1/recommend`
- HTTP Status: `200`
- cold_start_handled_false: `PASS`
- live_data_used_false: `PASS`
- has_precision_items: `PASS`
- Top 3 recommendations:
  - 1. `Suya Spot` | type=`precision` | explanation=`Matches your interest in food. Based on your history, this aligns with items you rated highly.`
  - 2. `Palmwine Diner` | type=`precision` | explanation=`Matches your interest in food. Based on your history, this aligns with items you rated highly.`
  - 3. `Evening Eats` | type=`precision` | explanation=`Matches your interest in food. Based on your history, this aligns with items you rated highly.`

## S5 - Task B Personalized With Live Data
- Endpoint: `/v1/recommend`
- HTTP Status: `200`
- live_data_used_true: `PASS`
- has_live_provider: `PASS`
- has_llm_instrumentation: `PASS`
- Top 3 recommendations:
  - 1. `The Best Places to Eat in San Antonio | Top Restaurants` | type=`precision` | explanation=`Matches your interest in food. Based on your history, this aligns with items you rated highly.`
  - 2. `What restaurants are must try if you're going for the San Antonio ...` | type=`precision` | explanation=`Matches your interest in food. Based on your history, this aligns with items you rated highly.`
  - 3. `THE 10 BEST Restaurants in San Antonio (Updated May 2026)` | type=`precision` | explanation=`Matches your interest in food. Based on your history, this aligns with items you rated highly.`

## S6 - Task B Manual Live Query Override
- Endpoint: `/v1/recommend`
- HTTP Status: `200`
- manual_source: `PASS`
- query_echoed: `PASS`
- live_data_used: `PASS`
- Top 3 recommendations:
  - 1. `Breakfast Corner` | type=`precision` | explanation=`Matches your interest in breakfast. Based on your history, this aligns with items you rated highly.`
  - 2. `Editor's Choice: 20 Most Anticipated Books of 2026` | type=`precision` | explanation=`Ranked highly for books category. Consistent with your demonstrated preferences.`
  - 3. `10 Writers Remaking African Literature in 2026` | type=`precision` | explanation=`Ranked highly for books category. Consistent with your demonstrated preferences.`

## S7 - Task B Explain Trace
- Endpoint: `/v1/explain`
- HTTP Status: `200`
- has_trace: `PASS`
- has_recommendation: `PASS`
- Response excerpt: `{"user_token": "s6_manual_query", "recommendation_id": "rec_1_s6_manual_query", "simulation": {"user_token": "s6_manual_query", "simulated_at": "2026-05-26T09:12:47.246100Z", "behavioral_snapshot": {"current_intent": "ex`

## Summary
- Checks passed: `20/20`
- Scenario count: `7`