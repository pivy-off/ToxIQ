"""
SMILES validation helpers using RDKit.

Invalid or empty SMILES must fail fast with clear errors for API layers.
"""

from __future__ import annotations

from dataclasses import dataclass

from rdkit import Chem
from rdkit.Chem import Mol


@dataclass(frozen=True)
class SmilesValidationResult:
    """Outcome of parsing a SMILES string."""

    ok: bool
    mol: Mol | None
    error: str | None = None


def validate_smiles(smiles: str) -> SmilesValidationResult:
    """
    Parse SMILES safely. Returns a Mol on success.

    Heuristic logic: RDKit sanitization is the source of truth for demo validity.
    """
    if not smiles or not smiles.strip():
        return SmilesValidationResult(False, None, "SMILES is empty.")

    mol = Chem.MolFromSmiles(smiles.strip())
    if mol is None:
        return SmilesValidationResult(False, None, "RDKit could not parse SMILES.")

    try:
        Chem.SanitizeMol(mol)
    except Exception as exc:  # noqa: BLE001 — demo boundary: return clean API error
        return SmilesValidationResult(False, None, f"Sanitization failed: {exc!s}")

    return SmilesValidationResult(True, mol, None)
