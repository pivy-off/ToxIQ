# ToxIQ

Pre-clinical drug safety simulation platform. Test any drug before it reaches a patient.

## What It Does

ToxIQ is a drug safety simulator that predicts:

- **Safety Score** — Composite 0-100 score based on toxicity, therapeutic index, and PK parameters
- **Pharmacokinetics (PK)** — Absorption, distribution, metabolism, and excretion predictions
- **PK Curve** — Simulated plasma concentration over time
- **Organ Distribution** — Estimated drug accumulation in brain, liver, kidneys, heart, lungs
- **Risk Assessment** — Automated flags for hERG inhibition, hepatotoxicity, and other concerns
- **AI Summary** — Natural language summary powered by Gemini AI

**Disclaimer:** This is a research tool for pre-clinical screening. Outputs are simulation estimates, not clinical evidence. Do not use for medical decisions.

## Tech Stack

### Frontend
- **Next.js 16** (App Router)
- **React 19**
- **TypeScript** (strict mode)
- **Chart.js** for PK visualizations
- **Motion** for animations

### Backend
- **FastAPI** (Python)
- **RDKit** for molecular feature extraction
- **ADMET-AI** (optional) for ML-based ADMET predictions
- **Gemini AI** (optional) for natural language summaries

### Deployment
- Frontend: **Vercel**
- Backend: **Railway**

## Local Development

### Prerequisites

- Node.js 20+
- Python 3.10-3.12
- npm or yarn

### Frontend Setup

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn main:app --reload
```

API runs at [http://localhost:8000](http://localhost:8000)

API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

### Running Both

For full functionality, run both frontend and backend:

```bash
# Terminal 1: Backend
cd backend && uvicorn main:app --reload

# Terminal 2: Frontend
npm run dev
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Frontend (Next.js)
BACKEND_URL=http://127.0.0.1:8000  # Backend API URL

# Backend (FastAPI)
FRONTEND_URL=https://your-frontend.vercel.app  # For CORS
TOXIQ_DEV_MODE=true  # Enable localhost in CORS (dev only)

# Optional: Gemini AI for drug summaries
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.0-flash

# Optional: ADMET-AI for ML predictions
PHARMASIM_USE_ADMET_AI=true  # Requires admet-ai package
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │InputView │  │ResultView│  │ScienceView│ │   Components     ││
│  │          │  │          │  │           │ │ (Cards, Charts)  ││
│  └────┬─────┘  └────┬─────┘  └────┬──────┘ └────────┬─────────┘│
│       └─────────────┴─────────────┴─────────────────┘          │
│                              │                                   │
│                     useReducer (appState.ts)                     │
│                              │                                   │
│                     backendApi.ts (fetch)                        │
└──────────────────────────────┼───────────────────────────────────┘
                               │ /api/backend/*
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Backend (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │/predict  │  │/compounds│  │/summary  │  │    /simulate     ││
│  └────┬─────┘  └────┬─────┘  └────┬──────┘ └────────┬─────────┘│
│       └─────────────┴─────────────┴─────────────────┘          │
│                              │                                   │
│                      ML Pipeline (ml/src/)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │Features  │  │PK Predict│  │Toxicity  │  │  Safety Score    ││
│  │Extraction│  │          │  │Heuristics│  │                  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/compounds` | GET | List preset compounds |
| `/predict/` | POST | Full prediction pipeline |
| `/summary/` | POST | Generate AI summary |
| `/simulate/` | POST | PK curve simulation |
| `/compare/` | POST | Compare two compounds |

## Testing

### Frontend Tests (Jest)

```bash
npm test              # Run tests
npm run test:watch    # Watch mode
npm run test:coverage # With coverage
```

### Backend Tests (pytest)

```bash
cd backend
pytest tests/ -v
```

### ML Tests (pytest)

```bash
pytest ml/tests/ -v
```

## Deployment

### Vercel (Frontend)

1. Connect repo to Vercel
2. Set environment variable: `BACKEND_URL` = your Railway backend URL
3. Deploy

### Railway (Backend)

1. Connect repo to Railway
2. Set environment variables:
   - `FRONTEND_URL` = your Vercel URL
   - `GEMINI_API_KEY` (optional)
   - `PHARMASIM_USE_ADMET_AI=false` (unless you want ADMET-AI)
3. Deploy

Railway will use `railway.toml` configuration automatically.

## Project Structure

```
├── app/                    # Next.js App Router
│   ├── page.tsx           # Main page component
│   ├── layout.tsx         # Root layout
│   └── globals.css        # Global styles (Apple design)
├── components/             # React components
│   ├── Navbar.tsx
│   ├── SafetyScoreCard.tsx
│   ├── PKChart.tsx
│   └── ...
├── views/                  # Page view components
│   ├── InputView.tsx
│   ├── ResultsView.tsx
│   └── ScienceView.tsx
├── lib/                    # Utilities
│   ├── appState.ts        # useReducer state management
│   ├── backendApi.ts      # API client
│   └── drugData.ts        # Type definitions
├── backend/               # FastAPI backend
│   ├── main.py           # App entrypoint
│   ├── routes/           # API routes
│   ├── services/         # Business logic
│   └── tests/            # pytest tests
├── ml/                    # ML pipeline
│   ├── src/
│   │   ├── pipeline.py   # Main orchestration
│   │   ├── pk_predictor.py
│   │   ├── safety_score.py
│   │   └── ...
│   └── tests/            # pytest tests
└── __tests__/            # Jest frontend tests
```

## License

MIT

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make changes
4. Run tests: `npm test && pytest backend/tests/ ml/tests/`
5. Submit a PR

## Support

Open an issue on GitHub for bugs or feature requests.
