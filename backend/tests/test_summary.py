"""Tests for /summary endpoint."""


def test_summary_endpoint(client, predict_payload_tylenol):
    """Test generating a drug summary."""
    response = client.post("/summary/", json=predict_payload_tylenol)
    assert response.status_code == 200

    data = response.json()
    assert "drug_name" in data
    assert "summary" in data
    assert isinstance(data["summary"], str)
    assert len(data["summary"]) > 0


def test_summary_by_drug_name(client, predict_payload_by_name):
    """Test summary generation by drug name."""
    response = client.post("/summary/", json=predict_payload_by_name)
    assert response.status_code == 200

    data = response.json()
    assert "summary" in data


def test_summary_invalid_smiles(client, invalid_smiles):
    """Test summary with invalid SMILES returns 400."""
    payload = {
        "drug_name": "InvalidDrug",
        "smiles": invalid_smiles,
        "route": "oral",
        "dose_mg": 100,
    }
    response = client.post("/summary/", json=payload)
    assert response.status_code == 400
