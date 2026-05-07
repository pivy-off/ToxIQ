from __future__ import annotations

DRUG_PRESETS = {
    "aspirin": {
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
        "dose_mg": 325.0,
        "clearance": 4.8,
        "volume_of_distribution": 12.0,
        "absorption_rate": 1.2,
        "bioavailability": 0.68,
        "therapeutic_min": 10.0,
        "therapeutic_max": 30.0,
        "toxicity_risk": 0.25,
    },
    "ibuprofen": {
        "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",
        "dose_mg": 400.0,
        "clearance": 3.6,
        "volume_of_distribution": 14.0,
        "absorption_rate": 1.4,
        "bioavailability": 0.8,
        "therapeutic_min": 15.0,
        "therapeutic_max": 35.0,
        "toxicity_risk": 0.3,
    },
    "acetaminophen": {
        "smiles": "CC(=O)NC1=CC=C(O)C=C1",
        "dose_mg": 500.0,
        "clearance": 5.2,
        "volume_of_distribution": 60.0,
        "absorption_rate": 1.1,
        "bioavailability": 0.88,
        "therapeutic_min": 10.0,
        "therapeutic_max": 20.0,
        "toxicity_risk": 0.35,
    },
    "warfarin": {
        "smiles": "CC(=O)CC(C1=CC=CC=C1)C(O)=O",
        "dose_mg": 5.0,
        "clearance": 0.2,
        "volume_of_distribution": 10.0,
        "absorption_rate": 0.6,
        "bioavailability": 0.99,
        "therapeutic_min": 1.0,
        "therapeutic_max": 3.0,
        "toxicity_risk": 0.72,
    },
    "metformin": {
        "smiles": "CN(C)C(=N)N=C(N)N",
        "dose_mg": 500.0,
        "clearance": 9.0,
        "volume_of_distribution": 63.0,
        "absorption_rate": 0.9,
        "bioavailability": 0.55,
        "therapeutic_min": 0.5,
        "therapeutic_max": 2.0,
        "toxicity_risk": 0.2,
    },
}


def get_therapeutic_window_mg_l(drug_name: str, fallback_cmax: float) -> tuple[float, float]:
    """
    Plasma concentration band (mg/L) for chart shading — toy values for demo presets,
    or a heuristic band from simulated Cmax when unknown.
    """
    key = (drug_name or "").strip().lower()
    preset = DRUG_PRESETS.get(key)
    if preset is not None:
        return float(preset["therapeutic_min"]), float(preset["therapeutic_max"])
    cm = max(float(fallback_cmax), 1e-9)
    return 0.12 * cm, 0.88 * cm
