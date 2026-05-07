"""
Toxicity-related demo outputs (hepatotoxicity, hERG proxy, Ames proxy).

Hybrid logic:
  - Today: transparent heuristics from RDKit descriptors + optional preset overrides.
  - TODO: replace with models trained on Tox21 / ChEMBL hERG / Ames literature data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from ml.src.feature_extraction import MolecularFeatures
from ml.utils.constants import TOX_SCORE_MAX, TOX_SCORE_MIN

HerGClass = Literal["low", "moderate", "high"]


@dataclass(frozen=True)
class ToxicityResult:
    """Normalized toxicity block for API (scores 0–100; Ames as probability 0–1)."""

    hepatotoxicity: float
    herg_risk_score: float
    herg_risk_class: HerGClass
    ames_mutagenicity_probability: float
    ames_positive: bool
    overall_toxicity: float


def _clamp_score(x: float) -> float:
    return max(TOX_SCORE_MIN, min(TOX_SCORE_MAX, x))


def _herg_class_from_score(score: float) -> HerGClass:
    if score < 30.0:
        return "low"
    if score < 60.0:
        return "moderate"
    return "high"


def predict_toxicity_heuristic(features: MolecularFeatures) -> ToxicityResult:
    """
    Heuristic liver / cardiac / mutagenicity proxies.

    Rationale (demo only): lipophilic, aromatic, low polarity can correlate with
    off-target and metabolic load in screening narratives — not a validated QSAR.
    """
    logp = features.logp
    mw = features.molecular_weight
    arom = features.aromatic_rings
    tpsa = features.tpsa

    # Hepatotoxicity proxy: metabolic burden + lipophilicity
    hep = 18.0 + logp * 8.0 + arom * 6.0 + mw / 80.0 - tpsa / 120.0
    hep = _clamp_score(hep)

    # hERG proxy: lipophilic basic-like patterns are often flagged; we lack pKa here — use logP/aromatics
    herg = 12.0 + logp * 10.0 + arom * 9.0 - tpsa / 150.0
    herg = _clamp_score(herg)
    herg_class = _herg_class_from_score(herg)

    # Ames proxy: nitro / aromatic amine patterns would be ideal; use coarse MW + aromatics
    # TODO: RDKit SMARTS filters for known alert structures
    ames_prob = _clamp_score(8.0 + arom * 5.0 + logp * 3.0) / 100.0
    ames_prob = max(0.0, min(1.0, ames_prob))
    ames_pos = ames_prob >= 0.35

    overall = _clamp_score((hep + herg + ames_prob * 100.0) / 3.0)

    return ToxicityResult(
        hepatotoxicity=hep,
        herg_risk_score=herg,
        herg_risk_class=herg_class,
        ames_mutagenicity_probability=round(ames_prob, 4),
        ames_positive=ames_pos,
        overall_toxicity=overall,
    )


def apply_toxicity_overrides(
    base: ToxicityResult,
    overrides: dict[str, float] | None,
) -> ToxicityResult:
    """
    Merge optional preset overrides from demo_compounds.json (0–100 or 0–1 for Ames prob).
    """
    if not overrides:
        return base

    hep = float(overrides.get("hepatotoxicity", base.hepatotoxicity))
    herg = float(overrides.get("herg_risk_score", base.herg_risk_score))
    ames_p = float(overrides.get("ames_mutagenicity_probability", base.ames_mutagenicity_probability))

    hep = _clamp_score(hep)
    herg = _clamp_score(herg)
    ames_p = max(0.0, min(1.0, ames_p))

    overall = _clamp_score((hep + herg + ames_p * 100.0) / 3.0)

    return ToxicityResult(
        hepatotoxicity=hep,
        herg_risk_score=herg,
        herg_risk_class=_herg_class_from_score(herg),
        ames_mutagenicity_probability=round(ames_p, 4),
        ames_positive=ames_p >= 0.35,
        overall_toxicity=overall,
    )


def toxicity_public(tox: ToxicityResult) -> dict[str, Any]:
    return {
        "hepatotoxicity": round(tox.hepatotoxicity, 2),
        "herg_channel_binding": {
            "score": round(tox.herg_risk_score, 2),
            "class": tox.herg_risk_class,
        },
        "ames_mutagenicity": {
            "probability": tox.ames_mutagenicity_probability,
            "positive": tox.ames_positive,
        },
        "overall_toxicity": round(tox.overall_toxicity, 2),
    }
