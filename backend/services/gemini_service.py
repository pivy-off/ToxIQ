from __future__ import annotations

import os
from typing import Dict

import google.generativeai as genai


def _gemini_model_candidates() -> list[str]:
    preferred = os.getenv("GEMINI_MODEL", "").strip()
    candidates = [
        preferred,
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash",
    ]
    return [c for c in candidates if c]


def _suitability_label(toxicity: Dict[str, float]) -> str:
    risk_label = str(toxicity.get("risk_label", "")).strip().lower()
    risk_value = float(toxicity.get("toxicity_risk", 0.0) or 0.0)

    if risk_label == "favorable" and risk_value < 0.35:
        return "generally favorable in this simulation"
    if risk_label == "caution" or risk_value < 0.6:
        return "mixed and should be used with caution"
    return "not favorable for routine human use in this simulation"


def _fallback_summary(drug_name: str, pk_params: Dict[str, float], toxicity: Dict[str, float]) -> str:
    suitability = _suitability_label(toxicity)
    return (
        f"Overall suitability for the human body in this model is {suitability}. "
        f"{drug_name} is commonly used in clinical care and should be interpreted in the context of patient-specific factors. "
        f"In this simulation, the estimated clearance is {pk_params.get('clearance', 0):.2f} and volume of distribution is "
        f"{pk_params.get('volume_of_distribution', 0):.2f}, suggesting how quickly the drug may be removed and distributed. "
        f"The absorption rate is approximately {pk_params.get('absorption_rate', 0):.2f} with bioavailability near "
        f"{pk_params.get('bioavailability', 0):.2f}. "
        f"The modeled toxicity risk is {toxicity.get('toxicity_risk', 0):.2f}, corresponding to a {toxicity.get('risk_label', 'Unknown')} risk profile. "
        "These outputs are research-only and not clinical advice."
    )


def get_pharmaceutical_summary(
    drug_name: str,
    pk_params: Dict[str, float],
    toxicity: Dict[str, float],
) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return _fallback_summary(drug_name, pk_params, toxicity)

    try:
        genai.configure(api_key=api_key)
        suitability = _suitability_label(toxicity)
        prompt = (
            "You are a pharmaceutical safety assistant. Write a clear 4-6 sentence plain-language summary. "
            f"Drug: {drug_name}. "
            "Sentence 1 must start with: 'Overall suitability for the human body in this model is ...' "
            f"and communicate this expected interpretation: {suitability}. "
            "Then include what it is usually used to treat, how it behaves in the body based on PK values, "
            "and a direct caution statement if risk is moderate or high. "
            "Use plain language for a non-technical reader and avoid hedging. "
            "Do not claim clinical proof. "
            f"PK parameters: {pk_params}. Toxicity profile: {toxicity}."
        )

        for model_name in _gemini_model_candidates():
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = getattr(response, "text", None)
                if text and text.strip():
                    return text.strip()
            except Exception:
                continue
        return _fallback_summary(drug_name, pk_params, toxicity)
    except Exception:
        return _fallback_summary(drug_name, pk_params, toxicity)
