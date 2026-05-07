from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ml.src.pipeline import PredictError, PredictRequest, run_predict
from backend.models.schemas import PredictRequestBody, SimulateResponseML
from backend.services.drug_presets import get_therapeutic_window_mg_l

router = APIRouter(prefix="/simulate", tags=["simulate"])


@router.post("/", response_model=SimulateResponseML)
def simulate(payload: PredictRequestBody) -> SimulateResponseML:
    """
    Runs the same prediction pipeline as /predict and returns a chart-focused subset
    (time–concentration series + therapeutic band for visualization).
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

    pk_summary = out["pk_summary"]  # type: ignore[index]
    dm = out["derived_metrics"]  # type: ignore[index]
    compound = out["compound"]  # type: ignore[index]
    cmax = float(dm["cmax"])
    t_ther_min, t_ther_max = get_therapeutic_window_mg_l(str(compound.get("name", "")), cmax)

    return SimulateResponseML(
        compound=dict(compound),
        pk_curve=dict(out["pk_curve"]),  # type: ignore[index]
        pk_summary=dict(pk_summary),
        derived_metrics=dict(dm),
        peak_concentration=cmax,
        time_to_peak_hours=float(pk_summary["tmax_hours"]),
        therapeutic_min=t_ther_min,
        therapeutic_max=t_ther_max,
        disclaimer=str(out["disclaimer"]),  # type: ignore[index]
    )
