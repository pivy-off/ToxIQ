"""Tests for ML pipeline core functions."""

import pytest
from ml.src.pipeline import (
    PredictRequest,
    PredictError,
    run_predict,
)


TYLENOL_SMILES = "CC(=O)Nc1ccc(O)cc1"
ASPIRIN_SMILES = "CC(=O)OC1=CC=CC=C1C(=O)O"


def test_run_predict_with_valid_smiles():
    """Test prediction with valid SMILES."""
    req = PredictRequest(
        drug_name="Tylenol",
        smiles=TYLENOL_SMILES,
        route="oral",
        dose_mg=500,
    )
    result = run_predict(req)

    assert not isinstance(result, PredictError)
    assert "compound" in result
    assert "safety_score" in result
    assert result["compound"]["name"] == "Tylenol"


def test_run_predict_with_invalid_smiles():
    """Test prediction with invalid SMILES returns error."""
    req = PredictRequest(
        drug_name="Invalid",
        smiles="NOT_VALID_SMILES",
        route="oral",
        dose_mg=100,
    )
    result = run_predict(req)

    assert isinstance(result, PredictError)
    assert result.code == "invalid_smiles"


def test_run_predict_empty_smiles():
    """Test prediction with empty SMILES returns error."""
    req = PredictRequest(
        drug_name="Unknown",
        smiles="",
        route="oral",
        dose_mg=100,
    )
    result = run_predict(req)

    assert isinstance(result, PredictError)
    assert result.code == "invalid_smiles"


def test_run_predict_safety_score_range():
    """Test that safety score is within 0-100 range."""
    req = PredictRequest(
        drug_name="Aspirin",
        smiles=ASPIRIN_SMILES,
        route="oral",
        dose_mg=325,
    )
    result = run_predict(req)

    assert not isinstance(result, PredictError)
    score = result["safety_score"]["score"]
    assert 0 <= score <= 100


def test_run_predict_pk_curve_structure():
    """Test that PK curve has correct structure."""
    req = PredictRequest(
        drug_name="Tylenol",
        smiles=TYLENOL_SMILES,
        route="oral",
        dose_mg=500,
    )
    result = run_predict(req)

    assert not isinstance(result, PredictError)
    pk_curve = result["pk_curve"]

    assert "time_hours" in pk_curve
    assert "concentration_mg_per_l" in pk_curve
    assert len(pk_curve["time_hours"]) > 0
    assert len(pk_curve["time_hours"]) == len(pk_curve["concentration_mg_per_l"])


def test_run_predict_dose_affects_concentration():
    """Test that higher doses produce higher concentrations."""
    low_dose = PredictRequest(
        drug_name="Tylenol",
        smiles=TYLENOL_SMILES,
        route="oral",
        dose_mg=100,
    )
    high_dose = PredictRequest(
        drug_name="Tylenol",
        smiles=TYLENOL_SMILES,
        route="oral",
        dose_mg=1000,
    )

    low_result = run_predict(low_dose)
    high_result = run_predict(high_dose)

    assert not isinstance(low_result, PredictError)
    assert not isinstance(high_result, PredictError)

    low_cmax = max(low_result["pk_curve"]["concentration_mg_per_l"])
    high_cmax = max(high_result["pk_curve"]["concentration_mg_per_l"])

    assert high_cmax > low_cmax
