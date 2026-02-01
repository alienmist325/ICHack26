"""
Test for property verification endpoint.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crud import create_property


@pytest.mark.auth
@pytest.mark.integration
class TestPropertyVerification:
    """Test property verification endpoint."""

    def test_verify_property_endpoint(self, authenticated_client, mock_property_data):
        """Test triggering property verification via API endpoint."""
        prop = create_property(mock_property_data)

        response = authenticated_client.post(f"/properties/{prop.id}/verify")

        assert response.status_code == 202
        data = response.json()
        assert data["property_id"] == prop.id
        assert data["status"] == "processing"

    def test_verify_nonexistent_property(self, authenticated_client):
        """Test verification endpoint with non-existent property."""
        response = authenticated_client.post("/properties/999999/verify")

        assert response.status_code == 404
        assert "detail" in response.json()
