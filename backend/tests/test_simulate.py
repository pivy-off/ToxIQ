"""Tests for /simulate endpoint."""

import pytest


def test_simulate_endpoint(client, tylenol_smiles):
    """Test PK simulation endpoint."""
    payload = {
        "smiles": tylenol_smiles,
        "dose_mg": 500,
        "route": "oral",
    }
    response = client.post("/simulate/", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "pk_curve" in data or "time_hours" in data


def test_simulate_different_doses(client, tylenol_smiles):
    """Test simulation with different dose values."""
    for dose in [100, 500, 1000]:
        payload = {
            "smiles": tylenol_smiles,
            "dose_mg": dose,
            "route": "oral",
        }
        response = client.post("/simulate/", json=payload)
        assert response.status_code == 200
