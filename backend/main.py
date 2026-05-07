import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Repository root must be on sys.path for `import ml`
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.routes.compare import router as compare_router
from backend.routes.compounds import router as compounds_router
from backend.routes.predict import router as predict_router
from backend.routes.simulate import router as simulate_router
from backend.routes.summary import router as summary_router

load_dotenv()

app = FastAPI(title="Pharmaceutical Safety Simulation API", version="1.0.0")

frontend_url = os.getenv("FRONTEND_URL", "").strip()
allowed_origins = ["http://localhost:3000"]
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(compounds_router)
app.include_router(predict_router)
app.include_router(simulate_router)
app.include_router(compare_router)
app.include_router(summary_router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
