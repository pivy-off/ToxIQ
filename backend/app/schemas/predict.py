"""Pydantic contracts for /predict — early-stage simulated outputs only."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PredictBody(BaseModel):
    drug_name: str = ""
    smiles: str = ""
    route: str = "oral"
    dose_mg: float = Field(default=100.0, ge=0.0)
    compound_id: str | None = Field(
        default=None,
        description="Optional preset id (acetaminophen, ibuprofen, thalidomide, candidate_x01).",
    )


class CompareBody(BaseModel):
    a: PredictBody
    b: PredictBody


class PredictResponse(BaseModel):
    """Loose wrapper — inner shape is built by ml.src.pipeline for chart-friendly JSON."""

    model_config = {"extra": "allow"}

    compound: dict[str, Any]
    features: dict[str, Any]
    pk_summary: dict[str, Any]
    pk_curve: dict[str, Any]
    derived_metrics: dict[str, Any]
    toxicity: dict[str, Any]
    safety_score: dict[str, Any]
    disclaimer: str
