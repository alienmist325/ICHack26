"""
Property interaction tests for the Rightmove API.

Tests cover:
- Starring/bookmarking properties
- Unstarring properties
- Setting property status (interested, viewing, offer, accepted)
- Adding comments to properties
- Retrieving property comments
- Handling invalid property IDs
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crud import (
    create_property,
)


@pytest.mark.auth
@pytest.mark.integration
class TestPropertyEndpoints:
    """Test property interaction API endpoints."""

    def test_star_property_endpoint(self, authenticated_client, mock_property_data):
        """Test starring property via API endpoint."""
        prop = create_property(mock_property_data)

        response = authenticated_client.post(f"/properties/{prop.id}/star")

        assert response.status_code == 201
        assert "status" in response.json()
        assert response.json()["status"] == "starred"

    def test_unstar_property_endpoint(self, authenticated_client, mock_property_data):
        """Test unstarring property via API endpoint."""
        prop = create_property(mock_property_data)

        # Star first
        authenticated_client.post(f"/properties/{prop.id}/star")

        # Then unstar using DELETE method
        response = authenticated_client.delete(f"/properties/{prop.id}/star")

        assert response.status_code == 204

    def test_set_status_endpoint(self, authenticated_client, mock_property_data):
        """Test setting property status via API endpoint."""
        prop = create_property(mock_property_data)

        response = authenticated_client.post(
            f"/properties/{prop.id}/status",
            json={"status": "interested"},
        )

        assert response.status_code == 201

    def test_add_comment_endpoint(self, authenticated_client, mock_property_data):
        """Test adding comment via API endpoint."""
        prop = create_property(mock_property_data)

        response = authenticated_client.post(
            f"/properties/{prop.id}/comments",
            json={"comment": "Great property!"},
        )

        assert response.status_code == 201
        assert response.json()["comment"] == "Great property!"

    def test_get_comments_endpoint(self, authenticated_client, mock_property_data):
        """Test retrieving comments via API endpoint."""
        prop = create_property(mock_property_data)

        authenticated_client.post(
            f"/properties/{prop.id}/comments",
            json={"comment": "Test comment"},
        )

        response = authenticated_client.get(f"/properties/{prop.id}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) == 1
        assert comments[0]["comment"] == "Test comment"

    def test_delete_comment_endpoint(self, authenticated_client, mock_property_data):
        """Test deleting comment via API endpoint."""
        prop = create_property(mock_property_data)

        comment_response = authenticated_client.post(
            f"/properties/{prop.id}/comments",
            json={"comment": "Comment to delete"},
        )
        comment_id = comment_response.json()["id"]

        response = authenticated_client.delete(
            f"/properties/{prop.id}/comments/{comment_id}"
        )

        assert response.status_code == 204

    def test_star_nonexistent_property(self, authenticated_client):
        """Test starring non-existent property returns 404."""
        response = authenticated_client.post("/properties/99999/star")

        assert response.status_code == 404

    def test_property_endpoints_require_auth(self, client, mock_property_data):
        """Test that property endpoints require authentication."""
        prop = create_property(mock_property_data)

        response = client.post(f"/properties/{prop.id}/star")
        assert response.status_code == 401

        response = client.post(f"/properties/{prop.id}/comments")
        assert response.status_code == 401
