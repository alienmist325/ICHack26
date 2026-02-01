"""
Test for property verification endpoint.

NOTE: These tests are skipped by default during pytest.
To enable verification tests (they use mock phone number), mark them with:
    @pytest.mark.allow_verification_calls

Or run with the pytest marker flag:
    pytest -m allow_verification_calls backend/tests/test_verification_endpoint.py
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
    """Test property verification endpoint.

    These tests are SKIPPED by default during pytest.

    To enable them, either:
    1. Mark individual tests with @pytest.mark.allow_verification_calls
    2. Or run with -m allow_verification_calls flag:
       pytest -m allow_verification_calls backend/tests/test_verification_endpoint.py

    When enabled, all calls use the mock phone number from .env.
    Real agent phone numbers are NEVER called during tests.
    """

    # Skip all tests in this class by default during pytest
    pytestmark = pytest.mark.skip(
        reason="Verification tests skipped by default. "
        "Mark with @pytest.mark.allow_verification_calls to enable, "
        "or use: pytest -m allow_verification_calls"
    )

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
