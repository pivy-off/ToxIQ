"""
Pharmacokinetic estimation and one-compartment oral curve simulation.

Hybrid logic:
  - Bioavailability (F), clearance class, Vd class: heuristics from descriptors (TODO: trained models).
  - Half-life: **derived only** via t½ = 0.693 * Vd / CL using numeric surrogates for buckets.
  - PK curve: computed from F, dose, ka, ke=CL/Vd, Vd (one-compartment oral, first-order).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np

from ml.src.feature_extraction import MolecularFeatures
from ml.utils.constants import (
    CL_NUMERIC_L_PER_H,
    KA_MAX,
    KA_MIN,
    PK_TIME_END_H,
    PK_TIME_START_H,
    PK_TIME_STEP_H,
    VD_NUMERIC_L,
)

PkBucket = Literal["low", "medium", "high"]
AbsorptionLabel = Literal["slow", "moderate", "fast"]


@dataclass(frozen=True)
class PKCoreResult:
    """Core PK outputs for API pk_summary + inputs to derived metrics."""

    bioavailability_f: float  # 0–1
    clearance_class: PkBucket
    volume_distribution_class: PkBucket
    clearance_l_per_h: float  # numeric surrogate aligned with class
    volume_distribution_l: float  # numeric surrogate aligned with class
    half_life_hours: float  # 0.693 * Vd / CL (not independently predicted)
    absorption_rate_label: AbsorptionLabel
    ka_per_h: float
    ke_per_h: float


@dataclass(frozen=True)
class PKCurveResult:
    """Time–concentration series for charting."""

    time_hours: list[float]
    concentration_mg_per_l: list[float]


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# --- Heuristic logic: oral bioavailability proxy from permeability / solubility proxies ---


def estimate_bioavailability_f(features: MolecularFeatures, route: str) -> float:
    """
    Heuristic F in [0.05, 1.0] using logP, TPSA, MW, rotatable bonds.

    Not a measured human F — a stable demo mapping for in silico screening storytelling.
    """
    route_l = (route or "oral").lower()
    if route_l in {"iv", "intravenous"}:
        return 1.0

    # Lipinski-like penalties for poor absorption
    tpsa = features.tpsa
    mw = features.molecular_weight
    logp = features.logp
    rot = features.rotatable_bonds

    base = 0.85
    base -= _clamp((tpsa - 90.0) / 200.0, 0.0, 0.35)
    base -= _clamp((mw - 350.0) / 600.0, 0.0, 0.25)
    base -= _clamp((rot - 7) / 25.0, 0.0, 0.15)
    # Extreme lipophilicity can reduce effective absorption in this toy model
    base -= _clamp((logp - 4.0) / 10.0, 0.0, 0.2)

    return float(_clamp(base, 0.05, 1.0))


def _classify_clearance_vd(features: MolecularFeatures) -> tuple[PkBucket, PkBucket]:
    """
    Heuristic clearance and Vd buckets from lipophilicity, size, polarity.

    TODO: replace with trained classifiers on PK databases (e.g. PK-DB) when available.
    """
    logp = features.logp
    mw = features.molecular_weight
    tpsa = features.tpsa

    # Clearance tends to track lipophilicity / metabolic liability in this toy model
    clear_score = logp * 12.0 + mw / 120.0 - tpsa / 180.0
    if clear_score < 8.0:
        cl = "low"
    elif clear_score < 16.0:
        cl = "medium"
    else:
        cl = "high"

    # Volume of distribution — lipophilic, less polar → larger apparent Vd (very rough)
    vd_score = logp * 10.0 - tpsa / 100.0 + features.aromatic_rings * 1.5
    if vd_score < 6.0:
        vd = "low"
    elif vd_score < 14.0:
        vd = "medium"
    else:
        vd = "high"

    return cl, vd


def _numeric_from_bucket(
    bucket: PkBucket,
    table: dict[str, float],
    feature_jitter: float,
) -> float:
    """Small deterministic jitter from [0,1) feature hash keeps demos non-identical."""
    base = table[bucket]
    return float(base * (0.92 + 0.16 * feature_jitter))


def half_life_from_cl_vd(cl_l_per_h: float, vd_l: float) -> float:
    """t½ = 0.693 * Vd / CL — standard relationship; CL must be > 0."""
    if cl_l_per_h <= 1e-9:
        return float("inf")
    return 0.693 * vd_l / cl_l_per_h


def estimate_ka(features: MolecularFeatures) -> tuple[float, AbsorptionLabel]:
    """
    Heuristic absorption rate constant ka (1/h) for oral curves from polarity / flexibility.
    """
    tpsa = features.tpsa
    rot = features.rotatable_bonds
    # More polar / flexible → slower absorption in this toy model
    ka = KA_MAX - _clamp(tpsa / 140.0, 0.0, 1.0) * (KA_MAX - KA_MIN) * 0.65
    ka -= _clamp(rot / 18.0, 0.0, 1.0) * (KA_MAX - KA_MIN) * 0.25
    ka = float(_clamp(ka, KA_MIN, KA_MAX))

    if ka < 1.4:
        label: AbsorptionLabel = "slow"
    elif ka < 3.2:
        label = "moderate"
    else:
        label = "fast"

    return ka, label


def _feature_jitter01(features: MolecularFeatures) -> float:
    """Deterministic pseudo-random in [0,1) from fingerprint bits."""
    if not features.morgan_fp:
        return 0.5
    s = sum(features.morgan_fp[: min(40, len(features.morgan_fp))])
    return (s % 997) / 997.0


def predict_pk_core(features: MolecularFeatures, route: str) -> PKCoreResult:
    """
    Produce F, CL/Vd classes, numeric CL & Vd, and half-life from the formula only.
    """
    f_bio = estimate_bioavailability_f(features, route)
    cl_b, vd_b = _classify_clearance_vd(features)
    jitter = _feature_jitter01(features)

    cl_num = _numeric_from_bucket(cl_b, CL_NUMERIC_L_PER_H, jitter)
    vd_num = _numeric_from_bucket(vd_b, VD_NUMERIC_L, 1.0 - jitter)

    t_half = half_life_from_cl_vd(cl_num, vd_num)
    ka, abs_label = estimate_ka(features)
    ke = cl_num / vd_num if vd_num > 1e-9 else 0.0

    return PKCoreResult(
        bioavailability_f=f_bio,
        clearance_class=cl_b,
        volume_distribution_class=vd_b,
        clearance_l_per_h=cl_num,
        volume_distribution_l=vd_num,
        half_life_hours=float(t_half),
        absorption_rate_label=abs_label,
        ka_per_h=ka,
        ke_per_h=float(ke),
    )


def simulate_oral_pk_curve(
    dose_mg: float,
    pk: PKCoreResult,
    *,
    end_h: float = PK_TIME_END_H,
    step_h: float = PK_TIME_STEP_H,
) -> PKCurveResult:
    """
    One-compartment oral absorption with first-order ka and elimination ke=CL/Vd.

    Concentration in mg/L (amount / Vd). Demo-scale, not individualized PK fitting.
    """
    d = max(float(dose_mg), 0.001)
    f = pk.bioavailability_f
    v = max(pk.volume_distribution_l, 1e-6)
    ka = max(pk.ka_per_h, 1e-6)
    ke = max(pk.ke_per_h, 1e-6)

    times = np.arange(PK_TIME_START_H, end_h + 1e-9, step_h, dtype=float)
    coeff = f * d * ka / v

    if abs(ka - ke) < 1e-5:
        # Limiting case ka ≈ ke: use Bateman limit C(t) = (F*D*ka/V)*t*exp(-ka*t)
        conc = coeff * times * np.exp(-ka * times)
    else:
        conc = coeff / (ka - ke) * (np.exp(-ke * times) - np.exp(-ka * times))

    conc = np.clip(conc, 0.0, None)
    return PKCurveResult(
        time_hours=times.round(4).tolist(),
        concentration_mg_per_l=conc.round(6).tolist(),
    )


def pk_summary_public(pk: PKCoreResult) -> dict[str, Any]:
    """Strings for buckets + numeric half-life and rate constants for transparency."""
    return {
        "bioavailability_f": round(pk.bioavailability_f, 4),
        "clearance": pk.clearance_class,
        "volume_distribution": pk.volume_distribution_class,
        "half_life_hours": round(pk.half_life_hours, 4),
        "absorption_rate": pk.absorption_rate_label,
        "clearance_numeric_l_per_h": round(pk.clearance_l_per_h, 4),
        "volume_distribution_numeric_l": round(pk.volume_distribution_l, 4),
        "ka_per_h": round(pk.ka_per_h, 4),
        "ke_per_h": round(pk.ke_per_h, 4),
    }
