"""
Alternate entrypoint: from repo `backend/` run `uvicorn app.main:app`.
Delegates to the canonical FastAPI app in `backend/main.py` (ML pipeline routes).
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
_repo = _backend.parent
for p in (_repo, _backend):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from main import app  # noqa: E402

__all__ = ["app"]
from ml.src.pipeline import PredictError, PredictRequest, run_predict  # noqa: E402
from ml.utils.registry import demo_row_to_public, load_demo_compounds  # noqa: E402

from .schemas.predict import CompareBody, PredictBody, PredictResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Preload ADMET-AI weights when enabled so the first /predict is not a cold start."""
    from ml.src.admet_bridge import admet_enabled, warmup_admet_model

    if admet_enabled():
        ok, err = warmup_admet_model()
        if ok:
            logger.info("ADMET-AI models warmed up")
        elif err:
            logger.warning("ADMET-AI warmup skipped or failed: %s", err)
    yield


app = FastAPI(
    title="PharmaSim API",
    description="Simulated PK/toxicity demo endpoints — not clinically validated.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/compounds")
def list_compounds() -> dict[str, object]:
    """Preset drugs for chips and compare (ids, names, default dose, aliases)."""
    return {"compounds": [demo_row_to_public(c) for c in load_demo_compounds()]}


@app.post("/predict", response_model=PredictResponse)
def predict(body: PredictBody) -> PredictResponse:
    req = PredictRequest(
        drug_name=body.drug_name,
        smiles=body.smiles,
        route=body.route,
        dose_mg=body.dose_mg,
        compound_id=body.compound_id,
    )
    out = run_predict(req)
    if isinstance(out, PredictError):
        if out.code == "not_found":
            raise HTTPException(status_code=404, detail=out.message)
        raise HTTPException(status_code=400, detail=out.message)
    return PredictResponse.model_validate(out)


@app.post("/compare")
def compare(body: CompareBody) -> dict[str, object]:
    """Side-by-side PK/tox/safety for two compounds (same fields as /predict)."""

    def _one(pb: PredictBody) -> dict[str, object]:
        r = run_predict(
            PredictRequest(
                drug_name=pb.drug_name,
                smiles=pb.smiles,
                route=pb.route,
                dose_mg=pb.dose_mg,
                compound_id=pb.compound_id,
            )
        )
        if isinstance(r, PredictError):
            raise HTTPException(status_code=400, detail=r.message)
        return r

    left = _one(body.a)
    right = _one(body.b)

    def headline() -> str:
        s1 = left["safety_score"]["score"]  # type: ignore[index]
        s2 = right["safety_score"]["score"]  # type: ignore[index]
        if s1 > s2 + 5:
            return "Left compound shows a higher simulated safety score in this MVP model."
        if s2 > s1 + 5:
            return "Right compound shows a higher simulated safety score in this MVP model."
        return "Both compounds are in a similar simulated safety band for this demo."

    return {
        "a": left,
        "b": right,
        "comparison": {
            "pk_summary": {
                "a": left["pk_summary"],  # type: ignore[index]
                "b": right["pk_summary"],  # type: ignore[index]
            },
            "derived_metrics": {
                "a": left["derived_metrics"],  # type: ignore[index]
                "b": right["derived_metrics"],  # type: ignore[index]
            },
            "toxicity": {
                "a": left["toxicity"],  # type: ignore[index]
                "b": right["toxicity"],  # type: ignore[index]
            },
            "safety_score": {
                "a": left["safety_score"],  # type: ignore[index]
                "b": right["safety_score"],  # type: ignore[index]
            },
            "headline": headline(),
        },
    }
