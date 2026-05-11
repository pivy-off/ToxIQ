from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.utils.sanitize import sanitize_drug_name, sanitize_smiles
from ml.src.pipeline import PredictError, PredictRequest, run_predict
from backend.models.schemas import SummaryInput, SummaryResponse
from backend.services.gemini_service import get_pharmaceutical_summary

logger = logging.getLogger("toxiq.summary")

router = APIRouter(prefix="/summary", tags=["summary"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=SummaryResponse)
@limiter.limit("20/minute")
def summarize_drug(request: Request, payload: SummaryInput) -> SummaryResponse:
    """Generate a plain-language summary of drug safety profile."""
    drug_name = sanitize_drug_name(payload.drug_name)
    smiles = sanitize_smiles(payload.smiles)

    logger.info("Summary request: drug_name=%s", drug_name)

    req = PredictRequest(
        drug_name=drug_name,
        smiles=smiles,
        route=payload.route,
        dose_mg=payload.dose_mg,
        compound_id=payload.compound_id,
    )

    out = run_predict(req)

    if isinstance(out, PredictError):
        logger.warning("Summary predict error: %s", out.message)
        raise HTTPException(status_code=400, detail=out.message)

    pk_summary = out["pk_summary"]
    tox = out["toxicity"]
    safety = out["safety_score"]
    name = str(out["compound"].get("name") or drug_name or "Compound")

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

    logger.info("Summary generated for %s: %d chars", name, len(summary))

    return SummaryResponse(drug_name=name, summary=summary)
