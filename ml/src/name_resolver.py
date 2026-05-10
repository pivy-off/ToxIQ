"""Name resolution helpers for free-form SMILES requests."""

from __future__ import annotations

import concurrent.futures
import logging
import os
import re

logger = logging.getLogger("toxiq.name_resolver")

GEMINI_TIMEOUT_SECONDS = 30


def _gemini_model_candidates() -> list[str]:
    preferred = os.getenv("GEMINI_MODEL", "").strip()
    candidates = [
        preferred,
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash",
    ]
    return [c for c in candidates if c]


def _call_gemini_model(model_name: str, prompt: str, api_key: str) -> str | None:
    """Call a single Gemini model with the given prompt. Returns text or None."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        text = (getattr(response, "text", "") or "").strip()
        if not text:
            return None
        line = text.splitlines()[0].strip(" \t-:;,.\"")
        line = re.sub(r"\s+", " ", line)
        if line and len(line) <= 64:
            return line
        return None
    except Exception as e:
        logger.debug("Gemini model %s failed: %s", model_name, str(e))
        return None


def infer_name_from_smiles_with_gemini(smiles: str) -> str | None:
    """
    Use Gemini only as a last-resort naming helper for display labels.

    Returns a concise molecule/common name when available, otherwise None.
    Has a 30-second timeout to prevent hanging.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.debug("No GEMINI_API_KEY set, skipping name inference")
        return None

    logger.info("Starting Gemini name inference for SMILES: %s...", smiles[:30] if smiles else "")

    try:
        prompt = (
            "You are a cheminformatics assistant. "
            "Given this SMILES, return only the most likely common or IUPAC-style name "
            "in under 6 words with no punctuation or extra explanation. "
            f"SMILES: {smiles}"
        )

        for model_name in _gemini_model_candidates():
            logger.debug("Trying Gemini model: %s", model_name)
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_call_gemini_model, model_name, prompt, api_key)
                    try:
                        result = future.result(timeout=GEMINI_TIMEOUT_SECONDS)
                        if result:
                            logger.info("Gemini resolved name: %s (model: %s)", result, model_name)
                            return result
                    except concurrent.futures.TimeoutError:
                        logger.warning("Gemini model %s timed out after %ds", model_name, GEMINI_TIMEOUT_SECONDS)
                        continue
            except Exception as e:
                logger.warning("Gemini model %s error: %s", model_name, str(e))
                continue

        logger.info("All Gemini models failed or timed out, returning None")
        return None
    except Exception as e:
        logger.exception("Gemini name inference failed: %s", str(e))
        return None
