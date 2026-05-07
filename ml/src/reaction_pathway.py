"""
Reaction / mechanism pathway steps for the explainer UI.

Heuristic logic: preset steps from demo_compounds.json when present; otherwise a generic
oral ADME narrative from descriptors.
"""

from __future__ import annotations

from typing import Any

from ml.src.feature_extraction import MolecularFeatures
from ml.utils.registry import DemoCompound


def _generic_pathway(drug_name: str, features: MolecularFeatures) -> list[dict[str, Any]]:
    abs_speed = "moderate" if features.tpsa > 90 else "rapid"
    return [
        {
            "step": 1,
            "title": "Oral ingestion",
            "organ": "GI tract",
            "description": "Solid or liquid dose enters the stomach and moves to the small intestine for dissolution.",
            "importance": "Sets the starting point for absorption-limited exposure in this demo.",
        },
        {
            "step": 2,
            "title": "Absorption",
            "organ": "Small intestine",
            "description": f"Passive permeability and polarity (TPSA about {features.tpsa:.0f}) suggest {abs_speed} uptake into portal blood.",
            "importance": "Drives how much drug reaches systemic circulation in the simulation.",
        },
        {
            "step": 3,
            "title": "First-pass & distribution",
            "organ": "Liver / plasma",
            "description": f"Lipophilicity (logP about {features.logp:.1f}) influences apparent volume and tissue partitioning in the toy model.",
            "importance": "Links structure to where the compound spends time before elimination.",
        },
        {
            "step": 4,
            "title": "Systemic circulation",
            "organ": "Bloodstream",
            "description": "Drug distributes to perfused organs according to the heuristic organ map.",
            "importance": "Feeds the concentration–time curve used for charts.",
        },
        {
            "step": 5,
            "title": "Metabolism",
            "organ": "Liver",
            "description": "Metabolic liability is not modeled atomistically; clearance class summarizes elimination pressure.",
            "importance": "Explains why clearance shapes half-life together with volume.",
        },
        {
            "step": 6,
            "title": "Excretion",
            "organ": "Kidneys",
            "description": "Polar metabolites and free fraction bias renal clearance in this screening narrative.",
            "importance": "Completes the ADME story for judges without claiming measured routes.",
        },
    ]


def build_reaction_pathway(
    drug_display_name: str,
    demo: DemoCompound | None,
    features: MolecularFeatures,
) -> list[dict[str, Any]]:
    if demo and demo.pathway_steps:
        out: list[dict[str, Any]] = []
        for i, row in enumerate(demo.pathway_steps, start=1):
            out.append(
                {
                    "step": i,
                    "title": row.get("title", f"Step {i}"),
                    "organ": row.get("organ", ""),
                    "description": row.get("description", ""),
                    "importance": row.get("importance", ""),
                }
            )
        return out
    return _generic_pathway(drug_display_name, features)
