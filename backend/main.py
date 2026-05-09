"""
ToxIQ FastAPI Backend
Single canonical entrypoint for all API routes.
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from backend.utils.sanitize import sanitize_drug_name, sanitize_smiles
from backend.routes.compare import router as compare_router
from backend.routes.compounds import router as compounds_router
from backend.routes.predict import router as predict_router
from backend.routes.simulate import router as simulate_router
from backend.routes.summary import router as summary_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("toxiq")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle handler."""
    from ml.src.admet_bridge import admet_enabled, warmup_admet_model

    logger.info("ToxIQ API starting up...")

    if admet_enabled():
        ok, err = warmup_admet_model()
        if ok:
            logger.info("ADMET-AI models warmed up successfully")
        elif err:
            logger.warning("ADMET-AI warmup skipped: %s", err)

    yield

    logger.info("ToxIQ API shutting down...")


app = FastAPI(
    title="ToxIQ API",
    description="Pre-clinical drug safety simulation API. Not clinically validated.",
    version="1.0.0",
    lifespan=lifespan,
)


def get_allowed_origins() -> list[str]:
    """Get CORS allowed origins from environment."""
    origins = [
        "https://toxiq-app.vercel.app",
    ]

    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)

    if os.getenv("TOXIQ_DEV_MODE", "").lower() in ("true", "1"):
        origins.extend([
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ])

    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def sanitize_inputs_middleware(request: Request, call_next):
    """Middleware to log requests and handle errors."""
    logger.info("%s %s", request.method, request.url.path)

    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.exception("Unhandled error in %s %s: %s", request.method, request.url.path, str(e))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again."},
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTP %d on %s: %s", exc.status_code, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again."},
    )


app.include_router(compounds_router)
app.include_router(predict_router)
app.include_router(simulate_router)
app.include_router(compare_router)
app.include_router(summary_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/", tags=["health"])
def root() -> dict[str, str]:
    """Root endpoint with API info."""
    return {
        "name": "ToxIQ API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
