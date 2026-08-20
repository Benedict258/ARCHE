# ARCHE Deployment Guide

**Status**: ✅ Ready for Production  
**Last Updated**: May 26, 2026  
**Test Coverage**: 41/41 tests passing (100%)  
**Scenario Validation**: 20/20 checks passed

---

## Quick Start

### Backend (FastAPI)

```bash
cd C:\Users\HP\Desktop\ARCHE
.\.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --port 8000
```

### Frontend (Vite + React)

```bash
cd C:\Users\HP\Desktop\ARCHE\frontend
npm install
npm run dev        # Local development
npm run build      # Production build
npm run preview    # Preview production build
```

---

## Environment Variables

### Backend Required Variables

Create a `.env` file in the project root:

```env
# LLM Providers (at least one required for live query planning)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
ANTHROPIC_API_KEY=your_anthropic_key_here

# Web Search (optional, enables live search fallback)
SERPER_API_KEY=your_serper_api_key_here
SERPER_BASE_URL=https://google.serper.dev/search

# Features
ENABLE_FALLBACK_WEBSEARCH=true
ARCHE_LOG_LEVEL=INFO

# Security
ARCHE_PRIVACY_SALT=arche-demo-salt  # Change in production
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Optional
DATABASE_URL=sqlite:///data/memory.db
```

### Frontend Environment Variables

Create `.env` in `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
VITE_API_DOCS=http://localhost:8000/docs
```

---

## Deployment Platforms

### Backend Deployment (Recommend: Render or Railway)

#### Render (Free Tier Available)

1. Push repo to GitHub
2. Create new Web Service on Render
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env`
6. Deploy

#### Railway (Alternative)

1. Push repo to GitHub
2. Connect Railway to repo
3. Add environment variables
4. Railway auto-detects Python and configures startup
5. Deploy

### Frontend Deployment (Recommend: Vercel)

#### Vercel (Easiest)

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy frontend
cd frontend
vercel

# Update vercel.json with your backend URL
# Example backend: https://arche-backend.onrender.com
```

Edit [vercel.json](vercel.json) before deploying:

```json
{
  "rewrites": [
    {
      "source": "/v1/(.*)",
      "dest": "https://YOUR_BACKEND_URL/v1/$1"
    }
  ]
}
```

#### GitHub Pages (Free Alternative)

```bash
cd frontend
npm run build
# Deploy dist/ folder to GitHub Pages
```

---

## Pre-Deployment Checklist

### Backend

- [ ] All 41 tests passing locally (`$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; pytest -q`)
- [ ] `.env` file created with required keys
- [ ] GROQ or Claude API key verified (test with `/v1/health`)
- [ ] SERPER_API_KEY set (for live web search)
- [ ] Database file exists or will be created on start
- [ ] ALLOWED_ORIGINS updated for frontend domain
- [ ] Git repo pushed to GitHub

### Frontend

- [ ] `npm install` completed without errors
- [ ] `npm run build` produces valid dist/ folder
- [ ] `vercel.json` points to correct backend URL
- [ ] Environment variables set in Vercel project dashboard
- [ ] Git repo pushed to GitHub
- [ ] Vercel project linked to repo

### Both

- [ ] CORS properly configured (ALLOWED_ORIGINS includes frontend domain)
- [ ] API health check works: `GET /health` returns `{"status": "ok"}`
- [ ] Frontend loads at deployed URL
- [ ] API endpoints accessible from frontend (check browser DevTools Network tab)

---

## Validation After Deployment

### Step 1: Test API Health

```bash
curl https://your-backend-url/health
# Expected: {"status": "ok"}
```

### Step 2: Run Validation Tests

```bash
# Against deployed backend
curl -X POST https://your-backend-url/v1/simulate-review \
  -H "Content-Type: application/json" \
  -d '{
    "user_persona": {
      "user_id": "test_user",
      "review_history": [
        {"item_name": "Test Item", "category": "books", "rating": 4, "review_text": "Good read"}
      ]
    },
    "item_details": {"name": "New Book", "category": "books"},
    "context": {}
  }'
```

### Step 3: Verify Frontend

- Open `https://your-frontend-url`
- Click "Run Recommendation (Task B)"
- Verify API calls succeed in DevTools Network tab
- Check response includes explanations and live data indicators

---

## Troubleshooting

### Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'api'`

```bash
# Solution: Ensure PYTHONPATH is set
$env:PYTHONPATH=$PWD
python -m uvicorn api.main:app --port 8000
```

### LLM Provider Errors

**Error**: `HTTP 400 Bad Request` from Groq/Claude

- Verify API key is correct
- Check API key has correct permissions
- Fall back to deterministic mode (LLM not required, used only for live query planning)

### Live Search Returns Empty

- Verify SERPER_API_KEY is valid
- Check ENABLE_FALLBACK_WEBSEARCH=true to use DuckDuckGo fallback
- If both fail, recommendations still work from local catalog

### CORS Errors on Frontend

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

- Update ALLOWED_ORIGINS to include frontend domain
- Verify vercel.json rewrite rules are correct
- Restart backend after changing env vars

### Tests Fail After Changes

```bash
# Clear database and re-run
Remove-Item .\data\memory.db -Force
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
pytest -q
```

---

## Local Development Workflow

### Start Backend

```bash
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH=$PWD
python -m uvicorn api.main:app --port 8000 --reload
```

### Start Frontend (Separate Terminal)

```bash
cd frontend
npm run dev
# Opens http://localhost:5173
```

### Run Tests

```bash
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
pytest -q
```

### Generate Reports

```bash
python scripts/generate_7_scenario_report.py
# Output: reports/comprehensive_test_report_7_scenarios.md
```

---

## Key Files & Endpoints

### Backend Endpoints

- **Task A (User Model)**: `POST /v1/simulate-review` — Predict review rating
- **Task B (Recommendations)**: `POST /v1/recommend` — Get ranked suggestions
- **Explain**: `POST /v1/explain` — Get reasoning trace for recommendation
- **Docs**: `GET /docs` — Interactive Swagger UI
- **Health**: `GET /health` — Server status

### Frontend Pages

- **Landing**: `/` — Overview & architecture explanation
- **Task A Demo**: `/task-a` — User model simulator
- **Task B Demo**: `/task-b` — Recommendation engine
- **SDK Guide**: `/sdk` — Integration examples

### Key Configuration Files

- `vercel.json` — Frontend rewrite rules to backend
- `.env` — Backend secrets (Git-ignored)
- `requirements.txt` — Python dependencies
- `frontend/package.json` — JS dependencies

---

## Performance Notes

- **Cold start**: ~2-3s on Render free tier (warms up over time)
- **LLM query latency**: ~8-12s (Groq) or ~15-20s (Claude)
- **Live search latency**: ~2-4s (Serper cached)
- **API response**: <500ms without LLM/live search, <5s with both
- **Frontend build**: ~45s (optimized production build)

---

## Security Considerations

- ✅ Privacy abstraction: user tokens are hashed automatically
- ✅ LLM credentials: stored in environment variables only
- ✅ CORS: restricted to allowed frontend domains
- ✅ Input validation: Pydantic schemas enforce types
- ⚠️ **TODO (future)**: Add API key authentication for /v1/\* endpoints

---

## Rollback Plan

If deployment fails:

1. **Backend**: Render auto-maintains previous deployment (switch in dashboard)
2. **Frontend**: Vercel maintains deployment history (rollback via dashboard)
3. **Local**: Git commit ensures you can rebuild locally anytime

---

## Next Steps

1. ✅ **Tests**: Run `pytest -q` locally (41/41 passing)
2. ✅ **Scenarios**: Run `python scripts/generate_7_scenario_report.py` (20/20 passing)
3. 🔄 **Deploy Backend**: Push to Render/Railway
4. 🔄 **Deploy Frontend**: Push to Vercel
5. 🔄 **Validate**: Run acceptance tests against live URLs
6. 📊 **Monitor**: Check logs and error rates

---

## Support

For issues or questions:

- Check logs: `Render > Logs` or `Railway > Logs`
- Test locally: Recreate issue with `npm run dev`
- Review error stack traces in DevTools
- Check this guide's Troubleshooting section

**Status**: Ready for production deployment! 🚀
