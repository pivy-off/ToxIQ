"""Gemini AI service for pharmaceutical summaries."""

from __future__ import annotations

import logging
import os
from typing import Dict

logger = logging.getLogger("toxiq.gemini")


def _gemini_model_candidates() -> list[str]:
    """Get list of Gemini models to try."""
    preferred = os.getenv("GEMINI_MODEL", "").strip()
    candidates = [
        preferred,
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash",
    ]
    return [c for c in candidates if c]


def _suitability_label(toxicity: Dict[str, float]) -> str:
    """Determine suitability label from toxicity data."""
    risk_label = str(toxicity.get("risk_label", "")).strip().lower()
    risk_value = float(toxicity.get("toxicity_risk", 0.0) or 0.0)

    if risk_label == "favorable" and risk_value < 0.35:
        return "generally favorable in this simulation"
    if risk_label == "caution" or risk_value < 0.6:
        return "mixed and should be used with caution"
    return "not favorable for routine human use in this simulation"


def _fallback_summary(drug_name: str, pk_params: Dict[str, float], toxicity: Dict[str, float]) -> str:
    """Generate fallback summary when Gemini is unavailable."""
    suitability = _suitability_label(toxicity)
    clearance = pk_params.get("clearance", 0)
    vd = pk_params.get("volume_of_distribution", 0)
    absorption = pk_params.get("absorption_rate", 0)
    bio = pk_params.get("bioavailability", 0)
    tox_risk = toxicity.get("toxicity_risk", 0)
    risk_label = toxicity.get("risk_label", "Unknown")

    return (
        f"Overall suitability for the human body in this model is {suitability}. "
        f"{drug_name} is commonly used in clinical care and should be interpreted in the context of patient-specific factors. "
        f"In this simulation, the estimated clearance is {clearance:.2f} and volume of distribution is {vd:.2f}, "
        f"suggesting how quickly the drug may be removed and distributed. "
        f"The absorption rate is approximately {absorption:.2f} with bioavailability near {bio:.2f}. "
        f"The modeled toxicity risk is {tox_risk:.2f}, corresponding to a {risk_label} risk profile. "
        "These outputs are research-only and not clinical advice."
    )


def get_pharmaceutical_summary(
    drug_name: str,
    pk_params: Dict[str, float],
    toxicity: Dict[str, float],
) -> str:
    """
    Generate a pharmaceutical summary using Gemini AI.
    Falls back to template summary if Gemini is unavailable.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        logger.info("GEMINI_API_KEY not configured, using fallback summary for %s", drug_name)
        return _fallback_summary(drug_name, pk_params, toxicity)

    try:
        import google.generativeai as genai

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
                logger.debug("Trying Gemini model: %s", model_name)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = getattr(response, "text", None)
                if text and text.strip():
                    logger.info("Generated summary for %s using %s", drug_name, model_name)
                    return text.strip()
            except Exception as e:
                logger.warning("Gemini model %s failed: %s", model_name, str(e))
                continue

        logger.warning("All Gemini models failed for %s, using fallback", drug_name)
        return _fallback_summary(drug_name, pk_params, toxicity)

    except ImportError:
        logger.error("google-generativeai package not installed")
        return _fallback_summary(drug_name, pk_params, toxicity)
    except Exception as e:
        logger.exception("Gemini service error for %s: %s", drug_name, str(e))
        return _fallback_summary(drug_name, pk_params, toxicity)
