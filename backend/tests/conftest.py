"""Pytest configuration and fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def tylenol_smiles():
    """SMILES string for acetaminophen (Tylenol)."""
    return "CC(=O)Nc1ccc(O)cc1"


@pytest.fixture
def aspirin_smiles():
    """SMILES string for aspirin."""
    return "CC(=O)OC1=CC=CC=C1C(=O)O"


@pytest.fixture
def invalid_smiles():
    """Invalid SMILES string for error testing."""
    return "NOT_A_VALID_SMILES_STRING"


@pytest.fixture
def predict_payload_tylenol(tylenol_smiles):
    """Standard prediction payload for Tylenol."""
    return {
        "drug_name": "Tylenol",
        "smiles": tylenol_smiles,
        "route": "oral",
        "dose_mg": 500,
    }


@pytest.fixture
def predict_payload_by_name():
    """Prediction payload using only drug name."""
    return {
        "drug_name": "Aspirin",
        "smiles": "",
        "route": "oral",
        "dose_mg": 325,
    }
