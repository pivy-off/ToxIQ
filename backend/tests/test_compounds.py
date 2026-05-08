"""Tests for /compounds endpoint."""


def test_get_compounds(client):
    """Test fetching compound presets."""
    response = client.get("/compounds")
    assert response.status_code == 200
    data = response.json()
    assert "compounds" in data
    assert isinstance(data["compounds"], list)
    assert len(data["compounds"]) > 0

    first_compound = data["compounds"][0]
    assert "id" in first_compound
    assert "name" in first_compound
    assert "smiles" in first_compound


def test_compounds_have_required_fields(client):
    """Test that all compounds have required fields."""
    response = client.get("/compounds")
    data = response.json()

    for compound in data["compounds"]:
        assert "id" in compound
        assert "name" in compound
        assert isinstance(compound["name"], str)
        assert len(compound["name"]) > 0
