# UI Setup Quickstart

This file explains how to wire the `FlowArt` / `FlowSection` components into a frontend project.

Install dependencies (npm):

```bash
npm init -y
npm install gsap @gsap/react lucide-react tw-animate-css
# Install Tailwind if not present (example):
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init
```

Tailwind globals snippet (add to your main css, e.g. `styles/globals.css`):

```css
@import "tailwindcss";
@import "tw-animate-css";

:root {
  --font-sans: "Plus Jakarta Sans", ui-sans-serif, system-ui, sans-serif;
}
```

Integration steps

- Create `/components/ui` and copy `story-scroll.tsx` there (already provided).
- Add the demo page at `demo/flow_art_demo.tsx` to preview locally with your React setup.
- Ensure `tailwind.config.js` includes content paths for the project files.
- Provide image assets (Unsplash placeholders recommended).

Run locally

- Use your preferred React dev server (Vite, Next.js, CRA). Example (Vite):

```bash
npx create-vite@latest frontend --template react-ts
# copy components to frontend/src/components/ui
cd frontend
npm install
npm run dev
```

Notes

- The `FlowArt` component uses `prefers-reduced-motion` to respect user settings.
- You can replace GSAP with a simpler scroll library if you prefer a lighter bundle.
