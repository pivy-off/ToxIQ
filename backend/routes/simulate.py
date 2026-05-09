from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from backend.utils.sanitize import sanitize_drug_name, sanitize_smiles
from ml.src.pipeline import PredictError, PredictRequest, run_predict
from backend.models.schemas import PredictRequestBody, SimulateResponseML
from backend.services.drug_presets import get_therapeutic_window_mg_l

logger = logging.getLogger("toxiq.simulate")

router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post("/", response_model=SimulateResponseML)
def simulate(payload: PredictRequestBody) -> SimulateResponseML:
    """
    Runs the prediction pipeline and returns a chart-focused subset
    with time-concentration series and therapeutic band for visualization.
    """
    drug_name = sanitize_drug_name(payload.drug_name)
    smiles = sanitize_smiles(payload.smiles)

    logger.info("Simulate request: drug_name=%s, dose=%s", drug_name, payload.dose_mg)

    req = PredictRequest(
        drug_name=drug_name,
        smiles=smiles,
        route=payload.route,
        dose_mg=payload.dose_mg,
        compound_id=payload.compound_id,
    )

    out = run_predict(req)

    if isinstance(out, PredictError):
        logger.warning("Simulate error: code=%s, message=%s", out.code, out.message)
        if out.code == "not_found":
            raise HTTPException(status_code=404, detail=out.message)
        raise HTTPException(status_code=400, detail=out.message)

    pk_summary = out["pk_summary"]
    dm = out["derived_metrics"]
    compound = out["compound"]
    cmax = float(dm["cmax"])
    t_ther_min, t_ther_max = get_therapeutic_window_mg_l(str(compound.get("name", "")), cmax)

    logger.info("Simulate complete: compound=%s, cmax=%.4f", compound.get("name"), cmax)

    return SimulateResponseML(
        compound=dict(compound),
        pk_curve=dict(out["pk_curve"]),
        pk_summary=dict(pk_summary),
        derived_metrics=dict(dm),
        peak_concentration=cmax,
        time_to_peak_hours=float(pk_summary["tmax_hours"]),
        therapeutic_min=t_ther_min,
        therapeutic_max=t_ther_max,
        disclaimer=str(out["disclaimer"]),
    )
