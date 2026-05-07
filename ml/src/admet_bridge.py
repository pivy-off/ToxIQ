"""
Optional ADMET-AI integration — in-process use of the PyPI ``admet-ai`` package.

Distribution: https://pypi.org/project/admet-ai/ — ``ADMETModel.predict(smiles=...)``.

ML-based logic: when enabled, predictions come from ``admet_ai`` (Chemprop / TDC-style tasks).
Heuristic logic: if import fails, env is off, or predict raises, callers fall back to local rules.

Env:
  PHARMASIM_USE_ADMET_AI unset — if ``admet-ai`` is installed, use it (team default).
  PHARMASIM_USE_ADMET_AI=0|false|off — never call ADMET (lighter deploys).
  PHARMASIM_USE_ADMET_AI=1|true|on — force on (must still have the package).
"""

from __future__ import annotations

import logging
import os
from dataclasses import replace
from typing import Any

from ml.src.pk_predictor import PKCoreResult
from ml.src.tox_predictor import (
    ToxicityResult,
    _clamp_score,
    _herg_class_from_score,
)

logger = logging.getLogger(__name__)

# Singleton — first prediction downloads/loads weights (can be slow).
_model = None


def admet_enabled() -> bool:
    """
    ADMET-AI is on when the package is installed, unless explicitly disabled.

    Set PHARMASIM_USE_ADMET_AI=0 (or false/off/no) to skip it — e.g. small cloud instances
    without PyTorch. Set to 1 to force on even if you add other auto-detect logic later.
    """
    raw = os.environ.get("PHARMASIM_USE_ADMET_AI", "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return _admet_import_ok()


def _admet_import_ok() -> bool:
    try:
        import admet_ai  # noqa: F401

        return True
    except ImportError:
        return False


def warmup_admet_model() -> tuple[bool, str | None]:
    """
    Eagerly load Chemprop weights so the first /predict is not a long cold start.

    Returns (ok, error_message).
    """
    if not admet_enabled():
        return False, None
    if not _admet_import_ok():
        return False, "admet-ai not installed"
    try:
        _get_model()
        return True, None
    except Exception as exc:  # noqa: BLE001
        logger.exception("ADMET-AI warmup failed")
        return False, str(exc)


def _get_model():
    """Lazy ADMETModel without DrugBank file (faster startup; no percentile columns)."""
    global _model
    if _model is not None:
        return _model
    from admet_ai import ADMETModel

    _model = ADMETModel(drugbank_path=None)
    return _model


def _strip_drugbank_keys(preds: dict[str, float]) -> dict[str, float]:
    """Keep only model outputs; drop DrugBank percentile columns."""
    return {k: float(v) for k, v in preds.items() if "drugbank" not in k.lower()}


def _pick_key(preds: dict[str, float], needles: tuple[str, ...]) -> float | None:
    """First key whose lowercase name contains any needle substring."""
    for name, val in preds.items():
        ln = name.lower()
        if any(n in ln for n in needles):
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return None


def run_admet_raw(smiles: str) -> tuple[dict[str, float] | None, str | None]:
    """
    Run ADMET-AI for one SMILES. Returns (filtered_predictions, error_message).
    """
    if not admet_enabled():
        return None, None
    if not _admet_import_ok():
        return None, "admet-ai package not installed (pip install admet-ai)."

    try:
        preds = _get_model().predict(smiles=smiles)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ADMET-AI predict failed")
        return None, f"ADMET-AI error: {exc!s}"

    if not isinstance(preds, dict):
        return None, "ADMET-AI returned unexpected type."

    return _strip_drugbank_keys(preds), None


def oral_bioavailability_from_admet(preds: dict[str, float]) -> float | None:
    """
    Map oral bioavailability probability (0–1) if present in ADMET output.

    TDC / ADMET-AI task names vary; we match common substrings.
    """
    v = _pick_key(preds, ("bioavailability", "hia", "biovailability"))
    if v is None:
        return None
    # Regression tasks might be 0–100 or log scale — clamp to plausible prob range
    if v > 1.0:
        v = v / 100.0
    return max(0.05, min(1.0, v))


def toxicity_from_admet(preds: dict[str, float]) -> ToxicityResult | None:
    """
    Build ToxicityResult from ADMET classification probabilities (0–1 scale expected).

    Hepatotoxicity: DILI / liver injury style tasks.
    hERG: blocking / inhibitor tasks.
    Ames: mutagenicity tasks.
    """
    herg_p = _pick_key(preds, ("herg",))
    clintox_p = _pick_key(preds, ("clintox", "clin_tox"))
    ames_p = _pick_key(preds, ("ames", "mutagen"))
    dili_p = _pick_key(preds, ("dili", "hepatotox", "liver", "drug_induced_liver"))

    if herg_p is None and clintox_p is None and ames_p is None and dili_p is None:
        return None  # no recognizable tox endpoints in this ADMET version’s columns

    def _prob01(x: float | None) -> float | None:
        if x is None:
            return None
        if x > 1.0:
            x = x / 100.0
        return max(0.0, min(1.0, x))

    herg_p = _prob01(herg_p)
    clintox_p = _prob01(clintox_p)
    ames_p = _prob01(ames_p)
    dili_p = _prob01(dili_p)

    # hERG risk score: probability of blocking channel → higher = worse
    if herg_p is not None:
        herg_score = herg_p * 100.0
    elif clintox_p is not None:
        herg_score = clintox_p * 70.0
    else:
        herg_score = 25.0

    if dili_p is not None:
        hep = dili_p * 100.0
    elif clintox_p is not None:
        hep = clintox_p * 85.0
    else:
        hep = 30.0

    if ames_p is None:
        ames_p = clintox_p * 0.35 if clintox_p is not None else 0.12

    hep = _clamp_score(hep)
    herg_score = _clamp_score(herg_score)
    ames_p = max(0.0, min(1.0, ames_p))
    overall = _clamp_score((hep + herg_score + ames_p * 100.0) / 3.0)

    return ToxicityResult(
        hepatotoxicity=hep,
        herg_risk_score=herg_score,
        herg_risk_class=_herg_class_from_score(herg_score),
        ames_mutagenicity_probability=round(ames_p, 4),
        ames_positive=ames_p >= 0.35,
        overall_toxicity=overall,
    )


def blend_bioavailability(heuristic_f: float, admet_f: float | None, *, weight: float = 0.55) -> float:
    """Blend heuristic F with ADMET oral bioavailability when available."""
    if admet_f is None:
        return heuristic_f
    w = max(0.0, min(1.0, weight))
    return float(max(0.05, min(1.0, (1.0 - w) * heuristic_f + w * admet_f)))


def merge_pk_core_bioavailability(pk: PKCoreResult, new_f: float) -> PKCoreResult:
    """Replace F only; ke/ka unchanged — curve shape scales with absorbed fraction."""
    return replace(pk, bioavailability_f=new_f)


def admet_public_block(
    *,
    enabled: bool,
    used: bool,
    error: str | None,
    raw: dict[str, float] | None,
    blended_bioavailability_f: float | None,
) -> dict[str, Any]:
    """Small, frontend-friendly provenance object."""
    return {
        "enabled": enabled,
        "used": used,
        "source": "ADMET-AI (Chemprop / TDC) — predictive, not clinically validated",
        "error": error,
        "blended_bioavailability_f": blended_bioavailability_f,
        "property_count": len(raw) if raw else 0,
        "sample_properties": _sample_props(raw, limit=12),
    }


def _sample_props(raw: dict[str, float] | None, limit: int) -> dict[str, float]:
    if not raw:
        return {}
    items = sorted(raw.items(), key=lambda kv: kv[0].lower())[:limit]
    return {k: round(v, 6) if isinstance(v, float) else v for k, v in items}


def admet_name_hint(preds: dict[str, float] | None) -> str | None:
    """
    Best-effort name extraction from ADMET outputs.

    Current ADMET-AI predictions are typically numeric endpoints only, but this keeps
    the naming path forward-compatible if metadata keys are added upstream.
    """
    if not preds:
        return None
    for key, value in preds.items():
        key_l = key.lower()
        if any(token in key_l for token in ("name", "compound", "molecule", "drug")):
            if isinstance(value, str):
                text = value.strip()
                if text:
                    return text
    return None
