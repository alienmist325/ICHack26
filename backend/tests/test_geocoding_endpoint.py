"""
Test suite for the geocoding endpoint.

Tests the `/routing/geocode` endpoint with various address formats.
"""

import pytest
from fastapi.testclient import TestClient

import backend.app.main as main_module
from backend.app.main import app
from backend.services.geocoding_service import GeocodingService


@pytest.fixture
def client():
    """Create a test client for the FastAPI app with lifespan."""
    # Initialize services before starting tests
    main_module._routing_service = main_module.RoutingService()
    main_module._geocoding_service = GeocodingService()

    client = TestClient(app)
    yield client

    # Cleanup
    main_module._routing_service = None
    main_module._geocoding_service = None


class TestGeocodeEndpoint:
    """Tests for the geocoding endpoint."""

    def test_geocode_valid_address(self, client):
        """Test geocoding a valid UK address."""
        response = client.post(
            "/routing/geocode",
            json={"address": "10 Downing Street, London, UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "latitude" in data
        assert "longitude" in data
        assert "address" in data
        assert data["address"] == "10 Downing Street, London, UK"
        # Verify coordinates are reasonable (roughly in UK bounds)
        assert 49 < data["latitude"] < 61
        assert -9 < data["longitude"] < 2

    def test_geocode_postcode(self, client):
        """Test geocoding with a UK postcode."""
        response = client.post(
            "/routing/geocode",
            json={"address": "SW1A 1AA"},  # 10 Downing Street postcode
        )
        assert response.status_code == 200
        data = response.json()
        assert "latitude" in data
        assert "longitude" in data

    def test_geocode_place_name(self, client):
        """Test geocoding with a place name."""
        response = client.post(
            "/routing/geocode",
            json={"address": "Tower Bridge, London"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "latitude" in data
        assert "longitude" in data

    def test_geocode_empty_address(self, client):
        """Test geocoding with an empty address."""
        response = client.post(
            "/routing/geocode",
            json={"address": ""},
        )
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_geocode_whitespace_only(self, client):
        """Test geocoding with whitespace-only address."""
        response = client.post(
            "/routing/geocode",
            json={"address": "   "},
        )
        assert response.status_code == 400

    def test_geocode_unknown_address(self, client):
        """Test geocoding with an address that cannot be found."""
        response = client.post(
            "/routing/geocode",
            json={"address": "xyzabc123invalidaddresszzz"},
        )
        # Should return 404 when address cannot be geocoded
        assert response.status_code == 404

    def test_geocode_response_format(self, client):
        """Test that the response has the correct format."""
        response = client.post(
            "/routing/geocode",
            json={"address": "Piccadilly Circus, London"},
        )
        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        assert isinstance(data["latitude"], (int, float))
        assert isinstance(data["longitude"], (int, float))
        assert isinstance(data["address"], str)

        # Verify coordinates are different (not default values)
        assert data["latitude"] != 0.0
        assert data["longitude"] != 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
