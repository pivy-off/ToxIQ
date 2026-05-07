from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ml.src.pipeline import PredictError, PredictRequest, run_predict
from backend.models.schemas import SummaryInput, SummaryResponse
from backend.services.gemini_service import get_pharmaceutical_summary

router = APIRouter(prefix="/summary", tags=["summary"])


@router.post("/", response_model=SummaryResponse)
def summarize_drug(payload: SummaryInput) -> SummaryResponse:
    req = PredictRequest(
        drug_name=payload.drug_name,
        smiles=payload.smiles,
        route=payload.route,
        dose_mg=payload.dose_mg,
        compound_id=payload.compound_id,
    )
    out = run_predict(req)
    if isinstance(out, PredictError):
        raise HTTPException(status_code=400, detail=out.message)

    pk_summary = out["pk_summary"]  # type: ignore[index]
    tox = out["toxicity"]  # type: ignore[index]
    safety = out["safety_score"]  # type: ignore[index]
    name = str(out["compound"].get("name") or payload.drug_name or "Compound")  # type: ignore[index]

    overall_tox = float(tox.get("overall_toxicity") or 0.0)
    pk_params = {
        "clearance": pk_summary.get("clearance_numeric_l_per_h"),
        "volume_of_distribution": pk_summary.get("volume_distribution_numeric_l"),
        "absorption_rate": pk_summary.get("ka_per_h"),
        "half_life": pk_summary.get("half_life_hours"),
        "bioavailability": pk_summary.get("bioavailability_f"),
    }
    toxicity = {
        "toxicity_risk": min(1.0, max(0.0, overall_tox / 100.0)),
        "risk_label": str(safety.get("label", "Unknown")),
    }

    summary = get_pharmaceutical_summary(name, pk_params, toxicity)

    return SummaryResponse(drug_name=name, summary=summary)
