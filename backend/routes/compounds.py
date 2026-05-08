"""Preset compounds for dashboard chips."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from ml.utils.registry import demo_row_to_public, load_demo_compounds

logger = logging.getLogger("toxiq.compounds")

router = APIRouter(tags=["compounds"])


@router.get("/compounds")
def list_compounds() -> dict[str, object]:
    """Return list of preset compounds for UI chips."""
    compounds = load_demo_compounds()
    logger.info("Returning %d preset compounds", len(compounds))
    return {"compounds": [demo_row_to_public(c) for c in compounds]}
