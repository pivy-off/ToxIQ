# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## Commands

```bash
npm run dev      # start dev server at http://localhost:3000
npm run build    # production build
npm run lint     # ESLint check
```

No test suite is configured. There is no `npm test` script.

## Architecture

**PharmaSim** is a pre-clinical drug safety simulator. The stack is:

- **Frontend**: Next.js 16 (App Router) + React 19, single-page SPA feel with client-side page state (`"input" | "results" | "science"`)
- **Backend**: External FastAPI service (Python) — not in this repo, runs separately
- **ML**: `ml/` folder contains Python data/model assets; imported by the backend, not the frontend

### How pages and data flow

`app/page.tsx` is a single `"use client"` component that manages all three views via a `currentPage` state switch. There is no routing — everything renders inside one component.

Data flow on analysis:
1. User submits a drug name or SMILES string
2. Frontend calls `POST /api/backend/predict/` → `GET /api/backend/summary/` (Gemini narrative)
3. `lib/backendApi.ts:mapPredictionToDrug()` maps the backend JSON to the `Drug` interface from `lib/drugData.ts`
4. If backend is offline or fails, it falls back to static hardcoded `Drug` entries in `lib/drugData.ts`

### Backend proxy

`next.config.ts` proxies `/api/backend/*` → `http://127.0.0.1:8000/*` (override with `BACKEND_URL` env var). The backend must be running separately (`uvicorn backend.app.main:app --reload` from the backend repo root with `backend/requirements.txt` installed, Python 3.10–3.12).

### Key files

| File | Purpose |
|------|---------|
| `app/page.tsx` | All UI state and three-page layout logic |
| `app/globals.css` | All styles — no Tailwind utility classes in JSX, pure CSS with CSS variables |
| `lib/drugData.ts` | `Drug` interface + static fallback drug data |
| `lib/backendApi.ts` | All fetch calls + `mapPredictionToDrug()` adapter |
| `components/` | Display-only cards: `SafetyScoreCard`, `PKMetricsCard`, `RiskCard`, `PKChart`, `OrganMap`, `PathwayCard`, `Navbar` |

### Styling conventions

All styles live in `app/globals.css` using CSS custom properties (`--accent`, `--text`, etc.). Layout sections use a consistent pattern: `max-width: 960px; margin: 0 auto; padding: 0 28px`. Do not add Tailwind utility classes to JSX — the project uses plain CSS classes only.

### Backend API endpoints used

- `GET /health` → `{ status: "ok" }`
- `GET /compounds` → `{ compounds: CompoundPreset[] }`
- `POST /predict/` → `PredictResponse` (see `lib/backendApi.ts` for full shape)
- `POST /summary/` → `{ drug_name, summary }` (Gemini AI narrative, optional)
