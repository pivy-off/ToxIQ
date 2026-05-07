"""
Interpretable safety_score (0–100) from PK-derived exposure stress + toxicity proxies.

Heuristic logic: transparent weighted penalties suitable for judge-facing explanations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ml.src.tox_predictor import ToxicityResult
from ml.utils.constants import (
    CMAX_CMIN_RATIO_SPIKE_THRESHOLD,
    TI_HIGH_RISK_MAX,
    TI_SAFE_MIN,
)

SafetyLabel = Literal["favorable", "caution", "concern"]


@dataclass(frozen=True)
class SafetyScoreResult:
    score: float
    label: SafetyLabel
    components: dict[str, float]
    notes: list[str]


def compute_safety_score(
    *,
    tox: ToxicityResult,
    therapeutic_index: float,
    cmax_cmin_ratio: float,
    bioavailability_f: float,
) -> SafetyScoreResult:
    """
    Start from 100, subtract weighted risk terms.

    - Higher toxicity scores (0–100) reduce safety.
    - Low TI (<2) is heavily penalized; TI ≥10 is a small bonus cap.
    - Large Cmax/Cmin ratio suggests exposure spikes.
    - Very low F reduces confidence slightly (not a penalty on safety itself — uncertainty proxy).
    """
    notes: list[str] = []
    score = 100.0

    tox_penalty = 0.35 * tox.hepatotoxicity + 0.25 * tox.herg_risk_score + 0.2 * (
        tox.ames_mutagenicity_probability * 100.0
    ) + 0.2 * tox.overall_toxicity
    score -= tox_penalty

    if therapeutic_index < TI_HIGH_RISK_MAX:
        score -= 25.0
        notes.append("Therapeutic index proxy is in a high-risk band (MVP heuristic).")
    elif therapeutic_index >= TI_SAFE_MIN:
        score += 5.0
        notes.append("Therapeutic index proxy suggests a wider estimated safety margin.")

    if cmax_cmin_ratio >= CMAX_CMIN_RATIO_SPIKE_THRESHOLD:
        score -= 12.0
        notes.append("High simulated Cmax/Cmin ratio — exposure variability flag for demo.")

    if bioavailability_f < 0.25:
        score -= 3.0
        notes.append("Low estimated oral bioavailability — PK demo uncertainty higher.")

    score = max(0.0, min(100.0, score))

    if score >= 72.0:
        label: SafetyLabel = "favorable"
    elif score >= 45.0:
        label = "caution"
    else:
        label = "concern"

    components = {
        "toxicity_penalty": round(tox_penalty, 3),
        "therapeutic_index": round(therapeutic_index, 3),
        "cmax_cmin_ratio": round(cmax_cmin_ratio, 3),
        "bioavailability_f": round(bioavailability_f, 4),
    }

    return SafetyScoreResult(
        score=round(score, 2),
        label=label,
        components=components,
        notes=notes,
    )


def safety_public(s: SafetyScoreResult) -> dict[str, Any]:
    return {
        "score": s.score,
        "label": s.label,
        "components": s.components,
        "notes": s.notes,
    }
