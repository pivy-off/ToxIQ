from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.utils.sanitize import sanitize_drug_name, sanitize_smiles
from ml.src.pipeline import PredictError, PredictRequest, run_predict
from backend.models.schemas import PredictRequestBody

logger = logging.getLogger("toxiq.predict")

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("/")
def predict(payload: PredictRequestBody) -> dict[str, object]:
    """
    Full ML pipeline: RDKit features, PK core + oral curve, toxicity heuristics, safety score,
    organ map, pathway — JSON for the dashboard.
    """
    drug_name = sanitize_drug_name(payload.drug_name)
    smiles = sanitize_smiles(payload.smiles)

    logger.info("Predict request: drug_name=%s, smiles=%s..., dose=%s",
                drug_name, smiles[:20] if smiles else "none", payload.dose_mg)

    req = PredictRequest(
        drug_name=drug_name,
        smiles=smiles,
        route=payload.route,
        dose_mg=payload.dose_mg,
        compound_id=payload.compound_id,
    )

    out = run_predict(req)

    if isinstance(out, PredictError):
        logger.warning("Predict error: code=%s, message=%s", out.code, out.message)
        if out.code == "not_found":
            raise HTTPException(status_code=404, detail=out.message)
        raise HTTPException(status_code=400, detail=out.message)

    logger.info("Predict success: compound=%s, safety_score=%s",
                out.get("compound", {}).get("name"),
                out.get("safety_score", {}).get("score"))

    return out
