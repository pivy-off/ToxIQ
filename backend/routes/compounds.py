"""Preset compounds for dashboard chips (ids align with ml/data/demo_compounds.json)."""

from __future__ import annotations

from fastapi import APIRouter

from ml.utils.registry import demo_row_to_public, load_demo_compounds

router = APIRouter(tags=["compounds"])


@router.get("/compounds")
def list_compounds() -> dict[str, object]:
    return {"compounds": [demo_row_to_public(c) for c in load_demo_compounds()]}
