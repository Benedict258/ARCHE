# ARCHE Hackathon Demo Script (MVP Freeze)

## Goal

Show complete user journey: `ingest -> recommend -> explain` with deterministic inputs.

## Environment

- Backend: `python api/main.py`
- Frontend: `cd frontend ; npm run dev`
- API Base: `http://127.0.0.1:8000`
- UI Base: `http://localhost:5173`

## Deterministic Persona

Use `demo/mock_data/deterministic_scenario.json`:

- user_token: `demo_user_june10`
- context: evening + mobile + social
- signal: fashion interaction

## Live Demo Steps

1. Open UI and click `Try Demo`.
2. Enter user token: `demo_user_june10`.
3. Trigger recommendations.
4. Show returned list with types:

- precision
- adjacent_exploration
- discovery

5. Click `Explain` on one recommendation.
6. Show explanation trace and alternatives considered.

## API Backup Path (Terminal)

1. Ingest

```powershell
curl -X POST http://127.0.0.1:8000/v1/ingest -H "Content-Type: application/json" -d "{\"user_token\":\"demo_user_june10\",\"signal\":{\"event_type\":\"view\",\"item_token\":\"prod_ankara_tote\",\"item_category\":\"fashion\",\"session_context\":{\"time_bucket\":\"evening\",\"device_class\":\"mobile\",\"entry_point\":\"social\"},\"engagement_depth\":0.88,\"dwell_time_seconds\":55}}"
```

2. Recommend

```powershell
curl -X POST http://127.0.0.1:8000/v1/recommend -H "Content-Type: application/json" -d "{\"user_token\":\"demo_user_june10\",\"context\":{\"time_bucket\":\"evening\",\"device_class\":\"mobile\",\"entry_point\":\"social\"},\"n\":5}"
```

3. Explain (use recommendation_id from previous response)

```powershell
curl -X POST http://127.0.0.1:8000/v1/explain -H "Content-Type: application/json" -d "{\"user_token\":\"demo_user_june10\",\"recommendation_id\":\"<rec_id>\"}"
```

## Backup Recording

Run:

```powershell
python demo/demo_recorder.py
```

Output:

- `demo/recordings/demo_results_<timestamp>.json`

## Judge-Facing Talking Points

- Privacy: deterministic hash-and-redact in ingest.
- Simulation first: recommendation uses simulation basis.
- Exploration aware: precision + adjacent + discovery mix.
- Explainability: explicit trace and alternatives.
