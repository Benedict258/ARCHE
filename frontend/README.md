# ARCHE Frontend (minimal)

This is a minimal Vite + React frontend used as a simple demo UI for the ARCHE API. It is intentionally light-weight and styled for a clean, responsive light-mode experience.

Quick start:

```bash
cd frontend
npm install
npm run dev
```

The app expects the backend to be running on the same origin (or adjust proxy in Vite config).

# ARCHE Frontend (Vite + React + Tailwind)

This frontend is scaffolded for the UI flow component defined in `BuildDocs/UI.md`.

## Run

```bash
cd frontend
npm install
npm run dev

```

## Build

```bash
cd frontend
npm run build
npm run preview
```

## Structure

- `src/components/ui/story-scroll.tsx`: FlowArt and FlowSection component.
- `src/App.tsx`: Integrated demo sections using project color references.
- `tailwind.config.js` + `postcss.config.js`: Tailwind setup.
- `src/index.css`: Tailwind directives and base font token.
