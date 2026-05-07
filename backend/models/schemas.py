from typing import Any, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PredictRequestBody(BaseModel):
    """Aligned with ml.src.pipeline.PredictRequest — primary contract for /predict and /simulate."""

    drug_name: str = ""
    smiles: str = ""
    route: str = "oral"
    dose_mg: float = Field(default=100.0, ge=0.0)
    compound_id: Optional[str] = Field(
        default=None,
        description="Preset id (e.g. acetaminophen, ibuprofen, thalidomide, candidate_x01).",
    )


class CompareRequestBody(BaseModel):
    a: PredictRequestBody
    b: PredictRequestBody


class DrugInput(BaseModel):
    drug_name: str
    smiles: Optional[str] = None
    dose_mg: float = Field(..., gt=0)
    patient_weight_kg: float = Field(..., gt=0)
    age: int = Field(..., ge=0, le=120)
    renal_function: float = Field(..., ge=0, le=1)
    hepatic_function: float = Field(..., ge=0, le=1)


class PKOutput(BaseModel):
    absorption_rate: float
    clearance: float
    volume_of_distribution: float
    half_life: float
    bioavailability: float


class ToxicityOutput(BaseModel):
    toxicity_risk: float = Field(..., ge=0, le=1)
    safety_score: float = Field(..., ge=0, le=100)
    risk_label: str


class SimulationPoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    time_hours: float = Field(
        ...,
        validation_alias=AliasChoices("time_hours", "x"),
        serialization_alias="x",
    )
    concentration_mgL: float = Field(
        ...,
        validation_alias=AliasChoices("concentration_mgL", "y"),
        serialization_alias="y",
    )


class PredictResponse(BaseModel):
    absorption_rate: float
    clearance: float
    volume_of_distribution: float
    half_life: float
    bioavailability: float
    toxicity_risk: float = Field(..., ge=0, le=1)
    safety_score: float = Field(..., ge=0, le=100)
    risk_label: str


class SimulateResponse(BaseModel):
    drug_name: str
    curve: List[SimulationPoint]
    therapeutic_min: float
    therapeutic_max: float
    peak_concentration: float
    time_to_peak: float


class CompareResponse(BaseModel):
    drug_a: PredictResponse
    drug_b: PredictResponse
    safer_drug: str


class SummaryResponse(BaseModel):
    drug_name: str
    summary: str


class CompareInput(BaseModel):
    drug_a: DrugInput
    drug_b: DrugInput


class SummaryInput(BaseModel):
    """Plain-language summary — uses the same inputs as /predict (ML pipeline)."""

    drug_name: str = ""
    smiles: str = ""
    route: str = "oral"
    dose_mg: float = Field(default=100.0, ge=0.0)
    compound_id: Optional[str] = None


class SimulateResponseML(BaseModel):
    """Chart-oriented subset of pipeline output + optional therapeutic window for UI bands."""

    model_config = ConfigDict(extra="ignore")

    compound: dict[str, Any]
    pk_curve: dict[str, Any]
    pk_summary: dict[str, Any]
    derived_metrics: dict[str, Any]
    peak_concentration: float
    time_to_peak_hours: float
    therapeutic_min: float
    therapeutic_max: float
    disclaimer: str
