"""
Shared numeric anchors and thresholds for hackathon-stable demos.

These values are illustrative scaling factors for in silico screening demos,
not patient-specific or clinically calibrated parameters.
"""

from __future__ import annotations

# --- PK bucket → numeric surrogates (L and L/h) for formula consistency ---
# Used only so t½ = 0.693 * Vd / CL is internally consistent with classifications.
CL_NUMERIC_L_PER_H = {"low": 6.0, "medium": 22.0, "high": 55.0}
VD_NUMERIC_L = {"low": 18.0, "medium": 50.0, "high": 140.0}

# Absorption rate constant (1/h) — heuristic range for oral one-compartment demo curves
KA_MIN = 0.8
KA_MAX = 6.0

# PK curve simulation window
PK_TIME_START_H = 0.0
PK_TIME_END_H = 48.0
PK_TIME_STEP_H = 0.25

# Derived metrics — spike heuristic (high peak-to-trough suggests exposure swings)
CMAX_CMIN_RATIO_SPIKE_THRESHOLD = 18.0

# Therapeutic index (MVP proxy) — classification bands
TI_SAFE_MIN = 10.0
TI_HIGH_RISK_MAX = 2.0

# Toxicity outputs are 0–100 for scores; Ames as probability 0–1
TOX_SCORE_MIN = 0.0
TOX_SCORE_MAX = 100.0

DISCLAIMER = (
    "Predictions are simulated, early-stage estimates for research exploration only "
    "and are not clinically validated."
)
