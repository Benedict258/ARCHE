# Deployment Guide

This repo contains a FastAPI backend (API) and a minimal Vite+React frontend in `frontend/`.

Overview:

- Frontend: static site (Vite) — recommended deploy target: Vercel.
- Backend: FastAPI application — recommended deploy target: Render, Railway, or Fly using the provided `Dockerfile`.

Environment variables required (set these in the host service):

- `SERPER_API_KEY` — Serper web search key (already set locally).
- `GROQ_API_KEY`, `GROQ_MODEL` — Groq LLM keys (optional).
- `ANTHROPIC_API_KEY` — Anthropic key (optional fallback).
- `ALLOWED_ORIGINS` — comma-separated origins for CORS (e.g., `https://your-frontend.vercel.app`). If unset, CORS will be permissive (demo mode).

Quick steps — Backend (Docker) deploy on Render/Railway:

1. Push repo to GitHub.
2. Create a new service on Render or Railway and choose Docker deployment.
3. Point the service to this repository and set the environment variables listed above.
4. The Dockerfile will run `uvicorn api.main:app` on port `8000`.

Quick steps — Frontend deploy to Vercel:

1. Go to Vercel and import the `frontend` directory as a new project.
2. In `vercel.json`, replace `REPLACE_WITH_BACKEND_URL` with your backend URL (e.g., `https://my-backend.onrender.com`).
3. Set any Vercel environment variables if you want (not required for static frontend).

Local development:

1. Start backend:

```powershell
& .venv\Scripts\Activate.ps1
uvicorn api.main:app --reload
```

2. Start frontend:

```bash
cd frontend
npm install
npm run dev
```

Notes:

- The repo contains `vercel.json` with a rewrite route to the backend — replace the placeholder URL before full deploy.
- The FastAPI app reads `.env` at startup; be sure to add the required keys to your host environment.
