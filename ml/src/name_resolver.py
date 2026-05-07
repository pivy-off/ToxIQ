"""Name resolution helpers for free-form SMILES requests."""

from __future__ import annotations

import os
import re


def _gemini_model_candidates() -> list[str]:
    preferred = os.getenv("GEMINI_MODEL", "").strip()
    candidates = [
        preferred,
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash",
    ]
    return [c for c in candidates if c]


def infer_name_from_smiles_with_gemini(smiles: str) -> str | None:
    """
    Use Gemini only as a last-resort naming helper for display labels.

    Returns a concise molecule/common name when available, otherwise None.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        prompt = (
            "You are a cheminformatics assistant. "
            "Given this SMILES, return only the most likely common or IUPAC-style name "
            "in under 6 words with no punctuation or extra explanation. "
            f"SMILES: {smiles}"
        )

        for model_name in _gemini_model_candidates():
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = (getattr(response, "text", "") or "").strip()
                if not text:
                    continue

                line = text.splitlines()[0].strip(" \t-:;,.\"")
                line = re.sub(r"\s+", " ", line)
                if line and len(line) <= 64:
                    return line
            except Exception:
                continue
        return None
    except Exception:
        return None
