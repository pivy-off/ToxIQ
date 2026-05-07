from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ml.src.pipeline import PredictError, PredictRequest, run_predict
from backend.models.schemas import PredictRequestBody

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("/")
def predict(payload: PredictRequestBody) -> dict[str, object]:
    """
    Full ML pipeline: RDKit features, PK core + oral curve, toxicity heuristics, safety score,
    organ map, pathway — JSON for the dashboard (same shape as ml demo).
    """
    req = PredictRequest(
        drug_name=payload.drug_name,
        smiles=payload.smiles,
        route=payload.route,
        dose_mg=payload.dose_mg,
        compound_id=payload.compound_id,
    )
    out = run_predict(req)
    if isinstance(out, PredictError):
        if out.code == "not_found":
            raise HTTPException(status_code=404, detail=out.message)
        raise HTTPException(status_code=400, detail=out.message)
    return out
