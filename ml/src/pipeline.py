"""
End-to-end orchestration: validate SMILES, features, PK, toxicity, derived metrics, safety.

Produces API-ready dicts: PK curve, toxicity, safety, organ map, pathway, risks, trial copy (UI parity).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

logger = logging.getLogger("toxiq.pipeline")

from ml.src.admet_bridge import (
    admet_enabled,
    admet_name_hint,
    admet_public_block,
    blend_bioavailability,
    merge_pk_core_bioavailability,
    oral_bioavailability_from_admet,
    run_admet_raw,
    toxicity_from_admet,
)
from ml.src.feature_extraction import extract_features
from ml.src.pk_predictor import (
    PKCurveResult,
    predict_pk_core,
    pk_summary_public,
    simulate_oral_pk_curve,
)
from ml.src.organ_distribution import (
    default_organ_note,
    estimate_organ_distribution,
    organ_distribution_public,
)
from ml.src.name_resolver import infer_name_from_smiles_with_gemini
from ml.src.prediction_ui import (
    apply_known_teratogen_adjustment,
    build_display_flags,
    build_pk_display,
    build_risk_assessment,
    build_trial_recommendation,
    build_verdict_label,
    protein_binding_heuristic,
)
from ml.src.reaction_pathway import build_reaction_pathway
from ml.src.safety_score import compute_safety_score, safety_public
from ml.src.tox_predictor import apply_toxicity_overrides, predict_toxicity_heuristic, toxicity_public
from ml.utils.constants import (
    CMAX_CMIN_RATIO_SPIKE_THRESHOLD,
    DISCLAIMER,
    TI_HIGH_RISK_MAX,
    TI_SAFE_MIN,
)
from ml.utils.registry import resolve_demo_compound
from ml.utils.registry import resolve_demo_compound_by_smiles
from ml.utils.smiles import validate_smiles


@dataclass(frozen=True)
class PredictRequest:
    drug_name: str
    smiles: str
    route: str = "oral"
    dose_mg: float = 100.0
    compound_id: str | None = None


@dataclass(frozen=True)
class PredictError:
    code: Literal["invalid_smiles", "not_found"]
    message: str


def _auc_trapezoid(time_h: list[float], conc: list[float]) -> float:
    if len(time_h) < 2:
        return 0.0
    t = np.asarray(time_h, dtype=float)
    c = np.asarray(conc, dtype=float)
    # NumPy 2.0+ removed np.trapz; np.trapezoid is the replacement.
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(c, t))
    return float(np.trapz(c, t))


def _cmax_tmax(curve: PKCurveResult) -> tuple[float, float]:
    c = np.asarray(curve.concentration_mg_per_l, dtype=float)
    t = np.asarray(curve.time_hours, dtype=float)
    if c.size == 0:
        return 0.0, 0.0
    i = int(np.argmax(c))
    return float(c[i]), float(t[i])


def _cmin_post_tmax(curve: PKCurveResult) -> float:
    """Trough-like minimum after peak (single-dose oral demo)."""
    c = np.asarray(curve.concentration_mg_per_l, dtype=float)
    t = np.asarray(curve.time_hours, dtype=float)
    if c.size == 0:
        return 0.0
    i_max = int(np.argmax(c))
    tail = c[i_max:]
    if tail.size == 0:
        return float(np.min(c))
    m = float(np.min(tail))
    return max(m, 1e-9)


def _therapeutic_index_proxy(dose_mg: float, tox_overall_0_100: float) -> float:
    """
    MVP TI ≈ TD50 / ED50 (dimensionless proxy for demo charts).

    - ED50 proxy increases mildly with dose (toy “exposure anchor” for the scenario).
    - TD50 proxy expands when overall toxicity scores are lower (wider toxic margin).

    Not a measured therapeutic index — explainable screening fiction only.
    """
    d = max(float(dose_mg), 1.0)
    ed50 = max(12.0, 0.55 * d)
    td50 = ed50 * (1.0 + (100.0 - tox_overall_0_100) / 10.0)
    dose_mod = 0.88 + 0.24 * min(d, 600.0) / 600.0
    ti = (td50 / ed50) * dose_mod
    return float(max(0.4, ti))


def _ti_class(ti: float) -> str:
    if ti >= TI_SAFE_MIN:
        return "safe"
    if ti < TI_HIGH_RISK_MAX:
        return "high_risk"
    return "moderate"


def _is_placeholder_name(name: str) -> bool:
    n = name.strip().lower()
    return n in {"", "unknown", "custom molecule", "custom_molecule", "molecule"}


def run_predict(req: PredictRequest) -> dict[str, Any] | PredictError:
    logger.info("=== PIPELINE START: drug_name=%s, smiles=%s..., dose=%.1f, route=%s ===",
                req.drug_name, req.smiles[:20] if req.smiles else "none", req.dose_mg, req.route)

    logger.info("[STEP 1/10] Resolving demo compound...")
    demo = resolve_demo_compound(req.compound_id, req.drug_name)
    smiles = req.smiles.strip()
    drug_name = req.drug_name.strip() or "Unknown"
    dose = float(req.dose_mg)
    route = req.route or "oral"
    logger.info("[STEP 1/10] Demo compound resolved: %s", demo.name if demo else "None")

    if demo and not smiles:
        smiles = demo.smiles
        logger.info("[STEP 1/10] Using demo SMILES for compound_id=%s", req.compound_id)
    if demo and (not drug_name or drug_name == "Unknown"):
        drug_name = demo.name
    if demo and req.dose_mg <= 0:
        dose = demo.default_dose_mg

    if not smiles:
        logger.warning("[STEP 1/10] FAILED: no SMILES provided")
        return PredictError("invalid_smiles", "SMILES is required (or pass a known compound_id).")

    logger.info("[STEP 2/10] Validating SMILES...")
    val = validate_smiles(smiles)
    if not val.ok or val.mol is None:
        logger.warning("[STEP 2/10] FAILED: invalid SMILES - %s", val.error)
        return PredictError("invalid_smiles", val.error or "Invalid SMILES.")
    logger.info("[STEP 2/10] SMILES validated successfully")

    if demo is None:
        logger.info("[STEP 2/10] No demo found, checking SMILES registry...")
        demo = resolve_demo_compound_by_smiles(smiles)
        if demo is not None and _is_placeholder_name(drug_name):
            drug_name = demo.name
            logger.info("[STEP 2/10] Found demo by SMILES: %s", demo.name)

    mol = val.mol

    logger.info("[STEP 3/10] Extracting molecular features...")
    try:
        features = extract_features(mol)
        logger.info("[STEP 3/10] Features extracted: MW=%.1f, logP=%.2f, TPSA=%.1f",
                    features.molecular_weight, features.logp, features.tpsa)
    except Exception as e:
        logger.exception("[STEP 3/10] FAILED: Feature extraction error: %s", str(e))
        raise

    logger.info("[STEP 4/10] Checking ADMET-AI status (enabled=%s)...", admet_enabled())
    admet_raw, admet_err = (None, None)
    if admet_enabled():
        logger.info("[STEP 4/10] Running ADMET-AI predictions...")
        admet_raw, admet_err = run_admet_raw(smiles)
        if admet_err:
            logger.warning("[STEP 4/10] ADMET-AI error: %s", admet_err)
        else:
            logger.info("[STEP 4/10] ADMET-AI predictions complete")
    else:
        logger.info("[STEP 4/10] ADMET-AI disabled, skipping")

    logger.info("[STEP 5/10] Resolving drug name (current: %s, is_placeholder=%s)...",
                drug_name, _is_placeholder_name(drug_name))
    if _is_placeholder_name(drug_name):
        logger.info("[STEP 5/10] Placeholder name detected, trying Gemini inference...")
        gemini_hint = infer_name_from_smiles_with_gemini(smiles)
        logger.info("[STEP 5/10] Gemini returned: %s", gemini_hint)
        if gemini_hint:
            drug_name = gemini_hint
        else:
            admet_hint = admet_name_hint(admet_raw)
            if admet_hint:
                drug_name = admet_hint
                logger.info("[STEP 5/10] Using ADMET hint: %s", drug_name)
            elif admet_raw is not None and admet_err is None:
                drug_name = "ADMET-AI Candidate"
            else:
                drug_name = "SMILES Candidate"
        logger.info("[STEP 5/10] Final drug name: %s", drug_name)
    else:
        logger.info("[STEP 5/10] Using provided drug name: %s", drug_name)

    logger.info("[STEP 6/10] Computing PK core parameters...")
    pk_core = predict_pk_core(features, route)
    blended_f: float | None = None
    if admet_raw is not None and admet_err is None:
        admet_f = oral_bioavailability_from_admet(admet_raw)
        if admet_f is not None:
            blended = blend_bioavailability(pk_core.bioavailability_f, admet_f)
            blended_f = blended
            pk_core = merge_pk_core_bioavailability(pk_core, blended)
    logger.info("[STEP 6/10] PK core complete: t1/2=%.1fh, F=%.2f, Vd=%.1f",
                pk_core.half_life_hours, pk_core.bioavailability_f, pk_core.volume_of_distribution)

    logger.info("[STEP 7/10] Simulating PK curve...")
    curve = simulate_oral_pk_curve(dose, pk_core)
    cmax, tmax = _cmax_tmax(curve)
    cmin = _cmin_post_tmax(curve)
    ratio = cmax / max(cmin, 1e-9)
    auc = _auc_trapezoid(curve.time_hours, curve.concentration_mg_per_l)
    logger.info("[STEP 7/10] PK curve complete: Cmax=%.3f, Tmax=%.1fh, AUC=%.2f", cmax, tmax, auc)

    logger.info("[STEP 8/10] Computing toxicity predictions...")
    tox_admet = toxicity_from_admet(admet_raw) if admet_raw is not None and admet_err is None else None
    tox_base = tox_admet if tox_admet is not None else predict_toxicity_heuristic(features)
    tox_overrides = None if tox_admet is not None else (demo.toxicity_overrides if demo else None)
    tox = apply_toxicity_overrides(tox_base, tox_overrides)
    logger.info("[STEP 8/10] Toxicity complete: overall=%.1f, hepato=%.1f, cardio=%.1f",
                tox.overall_toxicity, tox.hepatotoxicity, tox.cardiotoxicity)

    ti = _therapeutic_index_proxy(dose, tox.overall_toxicity)
    ti_class = _ti_class(ti)
    spike_flag = ratio >= CMAX_CMIN_RATIO_SPIKE_THRESHOLD

    logger.info("[STEP 9/10] Computing safety score...")
    safety = compute_safety_score(
        tox=tox,
        therapeutic_index=ti,
        cmax_cmin_ratio=ratio,
        bioavailability_f=pk_core.bioavailability_f,
    )
    known_teratogen = bool(demo and demo.known_teratogen)
    if known_teratogen:
        safety = apply_known_teratogen_adjustment(safety)
    logger.info("[STEP 9/10] Safety score: %d (TI=%.2f, class=%s)", safety.score, ti, ti_class)

    logger.info("[STEP 10/10] Computing organ distribution and building response...")
    organ_pct = estimate_organ_distribution(features, tox)
    organ_notes: dict[str, str] = {}
    if demo and demo.organ_notes:
        organ_notes.update(demo.organ_notes)
    for key in organ_pct:
        organ_notes.setdefault(key, default_organ_note(key, drug_name))

    pk_display = build_pk_display(pk_core)
    pk_display["protein_binding_percent"] = round(protein_binding_heuristic(features), 1)

    pk_summary = pk_summary_public(pk_core)
    pk_summary.update(
        {
            "cmax": round(cmax, 4),
            "tmax_hours": round(tmax, 4),
            "cmin": round(cmin, 6),
            "auc": round(auc, 4),
        }
    )

    derived_metrics = {
        "half_life_hours": round(pk_core.half_life_hours, 4),
        "cmax": round(cmax, 4),
        "cmin": round(cmin, 6),
        "cmax_cmin_ratio": round(ratio, 4),
        "therapeutic_index": round(ti, 4),
        "therapeutic_index_class": ti_class,
        "cmax_cmin_spike_flag": spike_flag,
    }

    logger.info("[STEP 10/10] Building final response...")
    logger.info("=== PIPELINE COMPLETE: compound=%s, safety_score=%d, verdict=%s ===",
                drug_name, safety.score, build_verdict_label(safety.score))

    return {
        "compound": {
            "name": drug_name,
            "smiles": smiles,
            "route": route,
            "dose_mg": dose,
            "compound_id": demo.id if demo else None,
        },
        "features": features.to_public_dict(),
        "verdict": build_verdict_label(safety.score),
        "pk_summary": pk_summary,
        "pk_display": pk_display,
        "pk_curve": {
            "time_hours": curve.time_hours,
            "concentration_mg_per_l": curve.concentration_mg_per_l,
        },
        "derived_metrics": derived_metrics,
        "toxicity": toxicity_public(tox),
        "safety_score": safety_public(safety),
        "risk_assessment": build_risk_assessment(
            tox, features, spike_flag, known_teratogen=known_teratogen
        ),
        "display_flags": build_display_flags(
            pk_core, tox, features, known_teratogen=known_teratogen
        ),
        "trial_recommendation": build_trial_recommendation(
            safety, tox, known_teratogen=known_teratogen
        ),
        "organ_distribution": organ_distribution_public(organ_pct, organ_notes),
        "reaction_pathway": build_reaction_pathway(drug_name, demo, features),
        "admet_ai": admet_public_block(
            enabled=admet_enabled(),
            used=admet_raw is not None and admet_err is None,
            error=admet_err,
            raw=admet_raw,
            blended_bioavailability_f=blended_f,
        ),
        "disclaimer": DISCLAIMER,
    }
