"""
Molecular feature extraction with RDKit.

ML-based logic: real descriptors and Morgan fingerprint bit vectors from structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, Mol

# Morgan fingerprint — deterministic demo settings
MORGAN_RADIUS = 2
MORGAN_N_BITS = 2048

try:
    from rdkit.Chem import rdFingerprintGenerator

    _MORGAN_GEN = rdFingerprintGenerator.GetMorganGenerator(
        radius=MORGAN_RADIUS,
        fpSize=MORGAN_N_BITS,
    )
except Exception:  # noqa: BLE001 — older RDKit without rdFingerprintGenerator
    _MORGAN_GEN = None
    from rdkit.Chem import AllChem  # legacy GetMorganFingerprintAsBitVect


@dataclass(frozen=True)
class MolecularFeatures:
    """Scalar descriptors used by heuristics and future models."""

    molecular_weight: float
    logp: float
    tpsa: float
    h_bond_donors: int
    h_bond_acceptors: int
    rotatable_bonds: int
    aromatic_rings: int
    heavy_atom_count: int
    formal_charge: int
    morgan_fp: tuple[int, ...]

    def to_public_dict(self) -> dict[str, Any]:
        """JSON-friendly view (fingerprint as hex string for compactness)."""
        return {
            "molecular_weight": round(self.molecular_weight, 4),
            "logp": round(self.logp, 4),
            "tpsa": round(self.tpsa, 4),
            "h_bond_donors": self.h_bond_donors,
            "h_bond_acceptors": self.h_bond_acceptors,
            "rotatable_bonds": self.rotatable_bonds,
            "aromatic_rings": self.aromatic_rings,
            "heavy_atom_count": self.heavy_atom_count,
            "formal_charge": self.formal_charge,
            "morgan_fingerprint_bits": MORGAN_N_BITS,
        }


def extract_features(mol: Mol) -> MolecularFeatures:
    """
    Compute RDKit descriptors and a Morgan fingerprint.

    ML-based logic: all values come from the parsed molecule graph.
    """
    mw = float(Descriptors.MolWt(mol))
    logp = float(Descriptors.MolLogP(mol))
    tpsa = float(Descriptors.TPSA(mol))
    h_donors = int(Lipinski.NumHDonors(mol))
    h_acceptors = int(Lipinski.NumHAcceptors(mol))
    rot_bonds = int(Lipinski.NumRotatableBonds(mol))
    arom_rings = int(Lipinski.NumAromaticRings(mol))
    heavy = int(mol.GetNumHeavyAtoms())
    charge = int(Chem.rdmolops.GetFormalCharge(mol))

    if _MORGAN_GEN is not None:
        fp = _MORGAN_GEN.GetFingerprint(mol)
    else:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, MORGAN_RADIUS, nBits=MORGAN_N_BITS)
    bits = tuple(fp.GetOnBits())

    return MolecularFeatures(
        molecular_weight=mw,
        logp=logp,
        tpsa=tpsa,
        h_bond_donors=h_donors,
        h_bond_acceptors=h_acceptors,
        rotatable_bonds=rot_bonds,
        aromatic_rings=arom_rings,
        heavy_atom_count=heavy,
        formal_charge=charge,
        morgan_fp=bits,
    )
