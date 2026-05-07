"""Load preset demo compounds from JSON for stable hackathon demos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DemoCompound:
    id: str
    name: str
    smiles: str
    default_dose_mg: float
    toxicity_overrides: dict[str, float] | None
    aliases: tuple[str, ...] = ()
    pathway_steps: tuple[dict[str, str], ...] | None = None
    organ_notes: dict[str, str] | None = None
    # Human teratogens are not predicted from structure in this MVP — flag for honest demo scoring.
    known_teratogen: bool = False


def _ml_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_demo_compounds() -> list[DemoCompound]:
    path = _ml_root() / "data" / "demo_compounds.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: list[DemoCompound] = []
    for row in raw:
        tox = row.get("toxicity_overrides")
        aliases = row.get("aliases") or []
        pathway = row.get("pathway")
        path_t: tuple[dict[str, str], ...] | None = None
        if isinstance(pathway, list) and pathway:
            path_t = tuple(
                {str(k): str(v) for k, v in p.items()}
                for p in pathway
                if isinstance(p, dict)
            )
        org = row.get("organ_notes")
        org_d: dict[str, str] | None = dict(org) if isinstance(org, dict) else None

        out.append(
            DemoCompound(
                id=str(row["id"]),
                name=str(row["name"]),
                smiles=str(row["smiles"]),
                default_dose_mg=float(row.get("default_dose_mg", 100)),
                toxicity_overrides=dict(tox) if isinstance(tox, dict) else None,
                aliases=tuple(str(a) for a in aliases),
                pathway_steps=path_t,
                organ_notes=org_d,
                known_teratogen=bool(row.get("known_teratogen", False)),
            )
        )
    return out


def find_demo_compound(compound_id: str | None) -> DemoCompound | None:
    if not compound_id:
        return None
    cid = compound_id.strip().lower()
    for c in load_demo_compounds():
        if c.id.lower() == cid:
            return c
        if any(cid == a.lower() for a in c.aliases):
            return c
    return None


def resolve_demo_compound(compound_id: str | None, drug_name: str | None) -> DemoCompound | None:
    """
    Resolve a preset by explicit id first, then by drug display name / marketing aliases.
    """
    d = find_demo_compound(compound_id)
    if d is not None:
        return d
    if not drug_name or not drug_name.strip():
        return None
    q = drug_name.strip().lower()

    for c in load_demo_compounds():
        if q == c.id.lower() or q == c.name.lower():
            return c
        if any(q == a.lower() for a in c.aliases):
            return c
    for c in load_demo_compounds():
        if q in c.name.lower() or c.name.lower() in q:
            return c
        if any(a.lower() in q or q in a.lower() for a in c.aliases if len(a) >= 3):
            return c
    return None


def resolve_demo_compound_by_smiles(smiles: str | None) -> DemoCompound | None:
    """Resolve a preset by exact normalized SMILES match."""
    if not smiles:
        return None
    q = smiles.strip()
    if not q:
        return None
    for c in load_demo_compounds():
        if c.smiles.strip() == q:
            return c
    return None


def demo_row_to_public(c: DemoCompound) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "smiles": c.smiles,
        "default_dose_mg": c.default_dose_mg,
        "aliases": list(c.aliases),
    }
