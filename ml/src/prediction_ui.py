"""
UI-oriented prediction bundles: risks, trial copy, flags, PK card numbers.

Heuristic logic: maps existing PK/tox/safety outputs into shapes similar to the PharmaSim HTML mockup.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Literal

from ml.src.feature_extraction import MolecularFeatures
from ml.src.pk_predictor import PKCoreResult
from ml.src.safety_score import SafetyLabel, SafetyScoreResult
from ml.src.tox_predictor import ToxicityResult

RiskLevel = Literal["safe", "warn", "danger"]


def apply_known_teratogen_adjustment(s: SafetyScoreResult) -> SafetyScoreResult:
    """
    Floor safety score for preset compounds flagged as known human teratogens.

    Heuristic models here do not predict embryofetal toxicity; without this floor,
    lipophilicity-only proxies can mis-rank infamous examples like thalidomide.
    """
    note = (
        "Preset marked known_teratogen: simulated score floored for education — "
        "this MVP does not compute developmental toxicity from SMILES."
    )
    return replace(
        s,
        score=min(s.score, 22.0),
        label="concern",
        notes=[*list(s.notes), note],
    )


def protein_binding_heuristic(features: MolecularFeatures) -> float:
    """
    Crude plasma protein binding % (0–99) from lipophilicity and polarity.

    TODO: replace with measured or modelled f_u from ADMET tools.
    """
    logp = features.logp
    tpsa = features.tpsa
    mw = features.molecular_weight
    base = 25.0 + logp * 14.0 - tpsa / 12.0 + min(mw, 500) / 80.0
    return float(max(0.0, min(99.0, base)))


def _risk_level_from_score(high_is_bad: float, *, lo: float, hi: float) -> RiskLevel:
    if high_is_bad < lo:
        return "safe"
    if high_is_bad < hi:
        return "warn"
    return "danger"


def build_risk_assessment(
    tox: ToxicityResult,
    features: MolecularFeatures,
    spike_flag: bool,
    *,
    known_teratogen: bool = False,
) -> list[dict[str, Any]]:
    """
    Risk list for the dashboard; optional teratogen row from preset registry (not QSAR).
    """
    # Nephrotoxicity proxy: polarity + MW (toy)
    neph_score = max(0.0, min(100.0, features.tpsa / 4.0 + features.molecular_weight / 25.0 - 15.0))

    hep_lvl = _risk_level_from_score(tox.hepatotoxicity, lo=35, hi=55)
    neph_lvl = _risk_level_from_score(neph_score, lo=45, hi=65)
    card_lvl = _risk_level_from_score(tox.herg_risk_score, lo=35, hi=55)

    # CNS: higher brain penetration narrative when lipophilic + low TPSA
    cns_penetration_proxy = max(0.0, min(100.0, features.logp * 18.0 - features.tpsa / 15.0 + 20.0))
    cns_lvl = _risk_level_from_score(cns_penetration_proxy, lo=50, hi=72)

    interact_lvl: RiskLevel = "warn" if tox.overall_toxicity > 45 or spike_flag else "safe"

    def _badge(lvl: RiskLevel, low: str, mid: str, high: str) -> str:
        return {"safe": low, "warn": mid, "danger": high}[lvl]

    rows: list[dict[str, Any]] = []
    if known_teratogen:
        rows.append(
            {
                "name": "Developmental toxicity (teratogen)",
                "description": (
                    "Known human teratogen in real-world pharmacovigilance — severe fetal harm risk. "
                    "Not inferred from this model’s descriptors; carried as explicit preset context."
                ),
                "level": "danger",
                "badge": "CRITICAL",
                "score": 100.0,
            }
        )

    rows.extend(
        [
        {
            "name": "Hepatotoxicity",
            "description": "Liver burden estimated from screening heuristics (not a DILI diagnosis).",
            "level": hep_lvl,
            "badge": _badge(hep_lvl, "Low", "Monitor", "Elevated"),
            "score": round(tox.hepatotoxicity, 1),
        },
        {
            "name": "Nephrotoxicity",
            "description": "Kidney exposure proxy from size/polarity — illustrative.",
            "level": neph_lvl,
            "badge": _badge(neph_lvl, "Low", "Monitor", "Elevated"),
            "score": round(neph_score, 1),
        },
        {
            "name": "Cardiotoxicity (hERG proxy)",
            "description": "Channel liability proxy — not an ECG prediction.",
            "level": card_lvl,
            "badge": _badge(card_lvl, "Low", "Monitor", "Elevated"),
            "score": round(tox.herg_risk_score, 1),
        },
        {
            "name": "CNS penetration",
            "description": "Blood–brain crossing narrative from logP/TPSA — not a PET study.",
            "level": cns_lvl,
            "badge": _badge(cns_lvl, "Low", "Moderate", "High"),
            "score": round(cns_penetration_proxy, 1),
        },
        {
            "name": "Exposure variability",
            "description": "Peak/trough ratio and overall tox profile — check for narrow therapeutic window stories.",
            "level": interact_lvl,
            "badge": _badge(interact_lvl, "Low", "Monitor", "Elevated"),
            "score": round(tox.overall_toxicity, 1),
        },
        ]
    )
    return rows


def build_display_flags(
    pk: PKCoreResult,
    tox: ToxicityResult,
    features: MolecularFeatures,
    *,
    known_teratogen: bool = False,
) -> list[dict[str, str]]:
    """Small chips for the safety card (safe / warn / danger)."""
    chips: list[tuple[str, str]] = []
    if known_teratogen:
        chips.append(("Teratogen 🚫", "danger"))

    abs_label = pk.absorption_rate_label
    if abs_label == "fast":
        flags = [("Absorption ✓", "safe")]
    elif abs_label == "moderate":
        flags = [("Absorption ○", "warn")]
    else:
        flags = [("Absorption slow", "warn")]

    chips.extend(flags)

    if tox.hepatotoxicity < 32:
        chips.append(("Liver ✓", "safe"))
    elif tox.hepatotoxicity < 50:
        chips.append(("Liver ○", "warn"))
    else:
        chips.append(("Liver ⚠", "warn"))

    cns = features.logp * 18.0 - features.tpsa / 15.0 + 20.0
    if cns < 45:
        chips.append(("CNS ✓", "safe"))
    elif cns < 62:
        chips.append(("CNS ⚠", "warn"))
    else:
        chips.append(("CNS ⚠", "danger"))

    return [{"text": t, "level": lvl} for t, lvl in chips]


def build_trial_recommendation(
    safety: SafetyScoreResult,
    tox: ToxicityResult,
    *,
    known_teratogen: bool = False,
) -> dict[str, Any]:
    """Headline trial narrative — matches hackathon pitch tone, not regulatory advice."""
    if known_teratogen:
        return {
            "trial_ready": False,
            "verdict": "DO NOT ADVANCE",
            "title": "Known human teratogen — not a general screening pass",
            "description": (
                "In real practice, known teratogens cause severe fetal harm and are tightly regulated (e.g. REMS). "
                "This MVP does not predict pregnancy risk from SMILES; presets flagged here are scored as fail for honest storytelling."
            ),
            "badge": "danger",
        }

    score = safety.score
    label = safety.label

    if label == "concern" or score < 40:
        return {
            "trial_ready": False,
            "verdict": "DO NOT ADVANCE",
            "title": "Hold — high simulated risk",
            "description": (
                "Combined toxicity and exposure proxies look poor in this MVP screen. "
                "Revisit structure-activity relationships before any lab work."
            ),
            "badge": "danger",
        }

    if label == "caution" or score < 72:
        return {
            "trial_ready": True,
            "verdict": "CAUTION",
            "title": "Advance with monitoring",
            "description": (
                "Margins are acceptable for an exploratory in vitro pass only. "
                "Track organ-specific liabilities called out in risk_assessment."
            ),
            "badge": "warn",
        }

    return {
        "trial_ready": True,
        "verdict": "FAVORABLE",
        "title": "Suitable for early in vitro screening (simulated)",
        "description": (
            "Simulated safety band and therapeutic-index proxy look reasonable for a first wet-lab triage — "
            "still requires standard validation."
        ),
        "badge": "safe",
    }


def build_verdict_label(score: float) -> str:
    """Large headline SAFE / ACCEPTABLE / DANGEROUS for UI parity with HTML mockup."""
    if score >= 72:
        return "SAFE"
    if score >= 45:
        return "ACCEPTABLE"
    return "HIGH RISK"


def build_pk_display(pk: PKCoreResult) -> dict[str, Any]:
    """
    PK card numbers similar to the static HTML (ka, CL L/h, Vd L/kg, t½ h, F%, protein binding separate).
    """
    vd_l = pk.volume_distribution_l
    vd_l_per_kg = vd_l / 70.0
    f_pct = round(pk.bioavailability_f * 100.0, 1)

    return {
        "absorption_ka_per_h": round(pk.ka_per_h, 3),
        "clearance_l_per_h": round(pk.clearance_l_per_h, 2),
        "volume_distribution_l": round(vd_l, 2),
        "volume_distribution_l_per_kg": round(vd_l_per_kg, 3),
        "half_life_hours": round(pk.half_life_hours, 2),
        "bioavailability_percent": f_pct,
    }
