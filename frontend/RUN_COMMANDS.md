# ARCHE Frontend - Run Commands

## Quick Start

### 1. Backend Setup (from project root)

```bash
# Activate Python virtual environment
.venv\Scripts\Activate.ps1

# Start the backend API server
python api/main.py
```

Backend will be available at: `http://localhost:8000`

**Check health:**

```bash
curl http://localhost:8000/v1/health
```

### 2. Frontend Setup (from frontend directory)

```bash
cd frontend

# Install dependencies (if not already installed)
npm install

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

### 3. Testing the Integration

Once both are running:

1. Open `http://localhost:5173` in your browser
2. Click "Try Demo →" button
3. Enter a user token (default: `demo-user-001`)
4. Click "Get Recommendations"
5. View recommendations and click "Explain" to get deep insights

## Build Commands

### Development

```bash
npm run dev
```

### Production Build

```bash
npm run build
```

### Preview Built Version

```bash
npm run preview
```

## API Integration

The frontend communicates with the backend via these endpoints:

| Endpoint        | Method | Purpose                              |
| --------------- | ------ | ------------------------------------ |
| `/v1/health`    | GET    | Health check                         |
| `/v1/ingest`    | POST   | Send user signals/interactions       |
| `/v1/simulate`  | POST   | Get behavioral snapshot              |
| `/v1/recommend` | POST   | Get personalized recommendations     |
| `/v1/explain`   | POST   | Get explanation for a recommendation |

## Environment Configuration

The frontend uses the following environment variables:

```
VITE_API_BASE_URL=http://localhost:8000  # Backend API URL
```

Update `.env.local` to point to your backend service.

## Frontend Structure

```
frontend/
├── src/
│   ├── App.tsx                  # Main app component with navigation
│   ├── main.tsx                 # Vite entry point
│   ├── index.css                # Global styles with Tailwind
│   ├── components/
│   │   └── ui/
│   │       └── story-scroll.tsx # FlowArt UI primitives
│   ├── pages/
│   │   └── RecommendationDemo.tsx
│   ├── hooks/
│   │   └── useAPI.ts            # Custom React hooks for API calls
│   └── services/
│       └── api.ts               # Backend API client
├── public/                      # Static assets
├── dist/                        # Production build output
├── vite.config.ts              # Vite configuration
├── tailwind.config.js          # Tailwind CSS configuration
├── postcss.config.js           # PostCSS configuration
└── package.json                # Dependencies and scripts
```

## Technology Stack

- **React 18** - UI framework
- **Vite** - Build tool & dev server
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **GSAP + ScrollTrigger** - Scroll-driven animations
- **tw-animate-css** - Animation utilities

## Troubleshooting

### "Cannot connect to backend"

- Ensure backend is running: `python api/main.py`
- Check backend is on `http://localhost:8000`
- Update `.env.local` if backend is on different URL

### Build errors

- Clear `node_modules` and reinstall: `npm install`
- Clear build cache: `rm -r dist`
- Rebuild: `npm run build`

### Development server won't start

- Ensure port 5173 is not in use
- Clear `.vite` cache: `rm -r .vite`
- Restart: `npm run dev`
