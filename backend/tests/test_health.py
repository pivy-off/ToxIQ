"""Tests for health check endpoints."""


def test_health_check(client):
    """Test the /health endpoint returns OK status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_root_endpoint(client):
    """Test the root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ToxIQ API"
    assert data["status"] == "running"
    assert "version" in data
