"""Tests for /predict endpoint."""

import pytest


def test_predict_with_smiles(client, predict_payload_tylenol):
    """Test prediction with valid SMILES."""
    response = client.post("/predict/", json=predict_payload_tylenol)
    assert response.status_code == 200

    data = response.json()
    assert "compound" in data
    assert "safety_score" in data
    assert "pk_curve" in data
    assert "risk_assessment" in data

    assert data["compound"]["name"] == "Tylenol"
    assert data["compound"]["dose_mg"] == 500


def test_predict_by_drug_name(client, predict_payload_by_name):
    """Test prediction using drug name lookup."""
    response = client.post("/predict/", json=predict_payload_by_name)
    assert response.status_code == 200

    data = response.json()
    assert "compound" in data
    assert "safety_score" in data


def test_predict_invalid_smiles(client, invalid_smiles):
    """Test prediction with invalid SMILES returns 400."""
    payload = {
        "drug_name": "InvalidDrug",
        "smiles": invalid_smiles,
        "route": "oral",
        "dose_mg": 100,
    }
    response = client.post("/predict/", json=payload)
    assert response.status_code == 400


def test_predict_empty_smiles_no_name(client):
    """Test prediction with empty SMILES and unknown name returns 400."""
    payload = {
        "drug_name": "",
        "smiles": "",
        "route": "oral",
        "dose_mg": 100,
    }
    response = client.post("/predict/", json=payload)
    assert response.status_code == 400


def test_predict_response_structure(client, predict_payload_tylenol):
    """Test that prediction response has expected structure."""
    response = client.post("/predict/", json=predict_payload_tylenol)
    data = response.json()

    required_fields = [
        "compound",
        "verdict",
        "pk_summary",
        "pk_display",
        "pk_curve",
        "toxicity",
        "safety_score",
        "risk_assessment",
        "display_flags",
        "trial_recommendation",
        "organ_distribution",
        "reaction_pathway",
        "disclaimer",
    ]

    for field in required_fields:
        assert field in data, f"Missing field: {field}"


def test_predict_safety_score_range(client, predict_payload_tylenol):
    """Test that safety score is within valid range."""
    response = client.post("/predict/", json=predict_payload_tylenol)
    data = response.json()

    score = data["safety_score"]["score"]
    assert 0 <= score <= 100


def test_predict_pk_curve_data(client, predict_payload_tylenol):
    """Test that PK curve has time and concentration arrays."""
    response = client.post("/predict/", json=predict_payload_tylenol)
    data = response.json()

    pk_curve = data["pk_curve"]
    assert "time_hours" in pk_curve
    assert "concentration_mg_per_l" in pk_curve
    assert isinstance(pk_curve["time_hours"], list)
    assert isinstance(pk_curve["concentration_mg_per_l"], list)
    assert len(pk_curve["time_hours"]) == len(pk_curve["concentration_mg_per_l"])
