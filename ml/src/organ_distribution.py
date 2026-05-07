"""
Organ distribution percentages for the body-map UI (hackathon heuristic).

Heuristic logic: shift mass toward brain/fat with lipophilicity, toward kidney/plasma with polarity;
liver reflects hepatotoxicity proxy. Sums to 100 for bar charts.
"""

from __future__ import annotations

from typing import Any

from ml.src.feature_extraction import MolecularFeatures
from ml.src.tox_predictor import ToxicityResult


def estimate_organ_distribution(
    features: MolecularFeatures,
    tox: ToxicityResult,
) -> dict[str, float]:
    """
    Return approximate relative distribution (%) across organs + bloodstream.

    Not PBPK — a stable, explainable demo mapping for visualization only.
    """
    logp = features.logp
    tpsa = features.tpsa
    mw = features.molecular_weight

    # Base template (rough narrative weights)
    brain = 10.0 + max(0.0, min(18.0, (logp - 1.0) * 2.5)) - max(0.0, (tpsa - 60.0) / 80.0)
    lungs = 7.0 + max(0.0, 5.0 - mw / 200.0)
    heart = 4.0 + tox.herg_risk_score / 80.0
    liver = 22.0 + tox.hepatotoxicity * 0.22
    kidneys = 12.0 + max(0.0, min(18.0, tpsa / 25.0))
    bloodstream = 100.0 - (brain + lungs + heart + liver + kidneys)
    bloodstream = max(8.0, bloodstream)

    parts = {
        "brain": brain,
        "lungs": lungs,
        "heart": heart,
        "liver": liver,
        "kidneys": kidneys,
        "bloodstream": bloodstream,
    }
    s = sum(parts.values())
    return {k: round(v / s * 100.0, 2) for k, v in parts.items()}


def organ_distribution_public(
    percentages: dict[str, float],
    organ_notes: dict[str, str] | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"percentages": percentages}
    if organ_notes:
        out["organ_notes"] = organ_notes
    return out


def default_organ_note(organ: str, drug_display_name: str) -> str:
    """Generic explainer when preset copy is missing."""
    return (
        f"Estimated relative exposure in the {organ} compartment for {drug_display_name} "
        "in this MVP model — illustrative only, not quantitatively calibrated."
    )
