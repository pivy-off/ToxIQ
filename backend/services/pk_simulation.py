from __future__ import annotations

from typing import Dict, List

import numpy as np
from scipy.integrate import solve_ivp

from backend.models.schemas import SimulationPoint


def simulate_one_compartment(
    dose_mg: float,
    clearance: float,
    volume_of_distribution: float,
    absorption_rate: float,
    bioavailability: float,
    therapeutic_min: float,
    therapeutic_max: float,
) -> Dict[str, object]:
    dose = max(float(dose_mg), 0.0)
    cl = max(float(clearance), 1e-6)
    vd = max(float(volume_of_distribution), 1e-6)
    ka = max(float(absorption_rate), 1e-6)
    f = float(np.clip(bioavailability, 0.0, 1.0))

    def ode(t: float, y: List[float]) -> List[float]:
        concentration = y[0]
        input_term = (f * ka * dose / vd) * np.exp(-ka * t)
        elimination_term = (cl / vd) * concentration
        dcdt = input_term - elimination_term
        return [dcdt]

    t_eval = np.linspace(0.0, 24.0, 200)
    solution = solve_ivp(
        ode,
        t_span=(0.0, 24.0),
        y0=[0.0],
        t_eval=t_eval,
        method="RK45",
        vectorized=False,
    )

    if not solution.success or solution.y.size == 0:
        raise ValueError("PK simulation failed to converge.")

    concentrations = np.clip(solution.y[0], 0.0, None)
    peak_idx = int(np.argmax(concentrations))
    peak_concentration = float(concentrations[peak_idx])
    time_to_peak = float(solution.t[peak_idx])

    curve = [
        SimulationPoint(time_hours=float(t), concentration_mgL=float(c))
        for t, c in zip(solution.t, concentrations)
    ]

    return {
        "curve": curve,
        "therapeutic_min": float(therapeutic_min),
        "therapeutic_max": float(therapeutic_max),
        "peak_concentration": peak_concentration,
        "time_to_peak": time_to_peak,
    }
