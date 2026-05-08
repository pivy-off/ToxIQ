from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.main import sanitize_drug_name, sanitize_smiles
from ml.src.pipeline import PredictError, PredictRequest, run_predict
from backend.models.schemas import CompareRequestBody, PredictRequestBody

logger = logging.getLogger("toxiq.compare")

router = APIRouter(prefix="/compare", tags=["compare"])


def _one(pb: PredictRequestBody) -> dict[str, Any]:
    """Run prediction for a single compound with sanitization."""
    drug_name = sanitize_drug_name(pb.drug_name)
    smiles = sanitize_smiles(pb.smiles)

    r = run_predict(
        PredictRequest(
            drug_name=drug_name,
            smiles=smiles,
            route=pb.route,
            dose_mg=pb.dose_mg,
            compound_id=pb.compound_id,
        )
    )
    if isinstance(r, PredictError):
        raise HTTPException(status_code=400, detail=r.message)
    return r


@router.post("/")
def compare(payload: CompareRequestBody) -> dict[str, object]:
    """Side-by-side full pipeline outputs for two compounds."""
    logger.info("Compare request: %s vs %s",
                payload.a.drug_name or payload.a.smiles[:20],
                payload.b.drug_name or payload.b.smiles[:20])

    left = _one(payload.a)
    right = _one(payload.b)

    def _score(d: dict[str, Any]) -> float:
        ss = d.get("safety_score") or {}
        return float(ss.get("score", 0.0))

    s1, s2 = _score(left), _score(right)

    def headline() -> str:
        if s1 > s2 + 5:
            return "Left compound shows a higher simulated safety score."
        if s2 > s1 + 5:
            return "Right compound shows a higher simulated safety score."
        return "Both compounds are in a similar simulated safety band."

    logger.info("Compare complete: %s (%.1f) vs %s (%.1f)",
                left["compound"]["name"], s1,
                right["compound"]["name"], s2)

    return {
        "a": left,
        "b": right,
        "comparison": {
            "pk_summary": {
                "a": left["pk_summary"],
                "b": right["pk_summary"],
            },
            "derived_metrics": {
                "a": left["derived_metrics"],
                "b": right["derived_metrics"],
            },
            "toxicity": {
                "a": left["toxicity"],
                "b": right["toxicity"],
            },
            "safety_score": {
                "a": left["safety_score"],
                "b": right["safety_score"],
            },
            "headline": headline(),
        },
    }
