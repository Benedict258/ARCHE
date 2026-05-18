**UI Reference — Compact**

- **Purpose**: Reference for designers/devs integrating the FlowArt UI primitives into the ARCHE frontend. Use as guidance (not a UI spec).

**Design Tokens**

- **Primary / Accent Colors**:
  - `--accent-1`: #fd5200 (orange)
  - `--brand-1`: #1A3DE8 (blue)
  - `--bg-light`: #F5F0E8 (warm light)
  - `--black`: #000000
  - `--white`: #FFFFFF
- **Text colors**: use high-contrast `#000` / `#fff` depending on background
- **Font**: `Plus Jakarta Sans` (system fallback: ui-sans-serif, system-ui, sans-serif)

**Layout & Spacing**

- Full-bleed, min-h-screen sections
- Responsive text using Tailwind clamp pattern (example in demo: `text-[clamp(3.5rem,12vw,14rem)]`)
- Component path: `/components/ui` (create if missing)

**Key Components**

1. `FlowArt` (wrapper)
   - Purpose: Scroll-driven art container; pins and scroll-triggered transforms
   - Props: `className?: string`, `aria-label?: string`, `children: ReactNode`
   - Notes: Requires `gsap` + `ScrollTrigger` + `@gsap/react` to enable scroll animations

2. `FlowSection`
   - Purpose: Full-screen panel inside `FlowArt` supporting background color & content
   - Props: `className?: string`, `style?: React.CSSProperties`, `children: ReactNode`, `aria-label?: string`
   - Styles used in demo: backgroundColor, color, large headings, hr separators, grid/columns for cards

**Recommendation: Tailwind + shadcn + TypeScript**

- Project structure: put primitives under `/components/ui`.
- Tailwind: extend global CSS (Tailwind 4 preferred) with `--font-sans` variable and include `tw-animate-css` if used.

**Dependencies**

- `gsap`, `@gsap/react` (ScrollTrigger usage)
- `tw-animate-css` (optional animation classes)
- `lucide-react` (icons)

**Example usage snippet**

- Import: `import FlowArt, { FlowSection } from "../components/ui/story-scroll.tsx"`
- Example: demo in UI.md shows multiple `FlowSection` blocks with background color tokens, headings, and multi-column info cards.

**Integration Checklist**

- [ ] Create `/components/ui/story-scroll.tsx` with `FlowArt` + `FlowSection` components (copy from BuildDocs/UI.md)
- [ ] Install `gsap`, `@gsap/react`, `lucide-react` if needed
- [ ] Extend Tailwind globals with `--font-sans` and import `tw-animate-css` if using
- [ ] Fill demo assets (Unsplash placeholders recommended)
- [ ] Validate responsive typography with the clamp pattern

**Files referenced**

- BuildDocs/UI.md (source demo + code)
- Suggested new files: `/components/ui/story-scroll.tsx`, a demo page under `app/` or `pages/` depending on framework

**Contact**

- If you want, I can scaffold `/components/ui/story-scroll.tsx` and minimal Tailwind edits next.
