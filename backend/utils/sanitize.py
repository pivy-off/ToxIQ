"""Input sanitization utilities."""

import html
import re


def sanitize_drug_name(name: str) -> str:
    """
    Sanitize drug name input to prevent prompt injection and XSS.
    - Strip HTML tags
    - Remove dangerous characters
    - Limit length
    - Escape HTML entities
    """
    if not name:
        return ""

    name = re.sub(r"<[^>]*>", "", name)
    name = re.sub(r"[<>\"'`;\\{}]", "", name)
    name = name.strip()[:200]
    name = html.escape(name)
    return name


def sanitize_smiles(smiles: str) -> str:
    """
    Sanitize SMILES string - allow only valid SMILES characters.
    """
    if not smiles:
        return ""

    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@+\\-=#()[]/%.")
    smiles = "".join(c for c in smiles if c in allowed)
    return smiles.strip()[:500]
