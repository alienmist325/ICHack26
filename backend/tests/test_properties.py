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

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crud import (
    create_property,
    star_property,
    unstar_property,
    get_user_stars,
    set_property_status,
    get_property_status,
    clear_property_status,
    add_property_comment,
    get_property_comments,
    delete_property_comment,
)


@pytest.mark.db
class TestPropertyStarring:
    """Test starring/bookmarking properties."""

    def test_star_property(self, test_user, mock_property_data):
        """Test starring a property."""
        # Create property
        prop = create_property(mock_property_data)

        # Star it
        star_property(test_user["id"], prop["id"])

        # Verify starred
        starred = get_user_stars(test_user["id"], limit=10, offset=0)
        assert len(starred) == 1
        assert starred[0]["id"] == prop["id"]

    def test_unstar_property(self, test_user, mock_property_data):
        """Test unstarring a starred property."""
        # Create and star property
        prop = create_property(mock_property_data)
        star_property(test_user["id"], prop["id"])

        # Unstar it
        unstar_property(test_user["id"], prop["id"])

        # Verify unstarred
        starred = get_user_stars(test_user["id"], limit=10, offset=0)
        assert len(starred) == 0

    def test_star_same_property_twice(self, test_user, mock_property_data):
        """Test that starring the same property twice doesn't create duplicates."""
        prop = create_property(mock_property_data)

        # Star twice
        star_property(test_user["id"], prop["id"])
        star_property(test_user["id"], prop["id"])

        # Should only have one star
        starred = get_user_stars(test_user["id"], limit=10, offset=0)
        assert len(starred) == 1

    def test_get_user_stars_empty(self, test_user):
        """Test getting stars for user with no starred properties."""
        starred = get_user_stars(test_user["id"], limit=10, offset=0)
        assert len(starred) == 0

    def test_get_user_stars_multiple(
        self, test_user, mock_property_data, mock_property_data_rental
    ):
        """Test getting multiple starred properties."""
        prop1 = create_property(mock_property_data)
        prop2 = create_property(mock_property_data_rental)

        star_property(test_user["id"], prop1["id"])
        star_property(test_user["id"], prop2["id"])

        starred = get_user_stars(test_user["id"], limit=10, offset=0)
        assert len(starred) == 2

    def test_different_users_stars_independent(
        self, test_user, second_test_user, mock_property_data
    ):
        """Test that stars from different users are independent."""
        prop = create_property(mock_property_data)

        # User 1 stars property
        star_property(test_user["id"], prop["id"])

        # User 2 doesn't have it starred
        user2_stars = get_user_stars(second_test_user["id"], limit=10, offset=0)
        assert len(user2_stars) == 0

        # User 1 has it starred
        user1_stars = get_user_stars(test_user["id"], limit=10, offset=0)
        assert len(user1_stars) == 1

    def test_star_pagination(
        self, test_user, mock_property_data, mock_property_data_rental
    ):
        """Test pagination of starred properties."""
        prop1 = create_property(mock_property_data)
        prop2 = create_property(mock_property_data_rental)

        star_property(test_user["id"], prop1["id"])
        star_property(test_user["id"], prop2["id"])

        # Get first property only
        page1 = get_user_stars(test_user["id"], limit=1, offset=0)
        assert len(page1) == 1

        # Get second property
        page2 = get_user_stars(test_user["id"], limit=1, offset=1)
        assert len(page2) == 1

        # Different properties
        assert page1[0]["id"] != page2[0]["id"]


@pytest.mark.db
class TestPropertyStatus:
    """Test property status tracking."""

    def test_set_property_status_interested(self, test_user, mock_property_data):
        """Test setting property status to 'interested'."""
        prop = create_property(mock_property_data)

        set_property_status(test_user["id"], prop["id"], "interested")

        status = get_property_status(test_user["id"], prop["id"])
        assert status == "interested"

    def test_set_property_status_viewing(self, test_user, mock_property_data):
        """Test setting property status to 'viewing'."""
        prop = create_property(mock_property_data)

        set_property_status(test_user["id"], prop["id"], "viewing")

        status = get_property_status(test_user["id"], prop["id"])
        assert status == "viewing"

    def test_set_property_status_offer(self, test_user, mock_property_data):
        """Test setting property status to 'offer'."""
        prop = create_property(mock_property_data)

        set_property_status(test_user["id"], prop["id"], "offer")

        status = get_property_status(test_user["id"], prop["id"])
        assert status == "offer"

    def test_set_property_status_accepted(self, test_user, mock_property_data):
        """Test setting property status to 'accepted'."""
        prop = create_property(mock_property_data)

        set_property_status(test_user["id"], prop["id"], "accepted")

        status = get_property_status(test_user["id"], prop["id"])
        assert status == "accepted"

    def test_update_property_status(self, test_user, mock_property_data):
        """Test updating existing property status."""
        prop = create_property(mock_property_data)

        # Set initial status
        set_property_status(test_user["id"], prop["id"], "interested")
        assert get_property_status(test_user["id"], prop["id"]) == "interested"

        # Update status
        set_property_status(test_user["id"], prop["id"], "viewing")
        assert get_property_status(test_user["id"], prop["id"]) == "viewing"

    def test_clear_property_status(self, test_user, mock_property_data):
        """Test clearing property status."""
        prop = create_property(mock_property_data)

        set_property_status(test_user["id"], prop["id"], "interested")
        clear_property_status(test_user["id"], prop["id"])

        status = get_property_status(test_user["id"], prop["id"])
        assert status is None

    def test_get_status_nonexistent(self, test_user, mock_property_data):
        """Test getting status for property with no status set."""
        prop = create_property(mock_property_data)

        status = get_property_status(test_user["id"], prop["id"])
        assert status is None

    def test_status_independent_per_user(
        self, test_user, second_test_user, mock_property_data
    ):
        """Test that property status is independent per user."""
        prop = create_property(mock_property_data)

        # User 1 sets status
        set_property_status(test_user["id"], prop["id"], "interested")

        # User 2 sets different status
        set_property_status(second_test_user["id"], prop["id"], "viewing")

        # Verify independent
        assert get_property_status(test_user["id"], prop["id"]) == "interested"
        assert get_property_status(second_test_user["id"], prop["id"]) == "viewing"


@pytest.mark.db
class TestPropertyComments:
    """Test property comments functionality."""

    def test_add_comment(self, test_user, mock_property_data):
        """Test adding a comment to a property."""
        prop = create_property(mock_property_data)
        comment_text = "Great property! Love the location."

        comment = add_property_comment(test_user["id"], prop["id"], comment_text)

        assert comment is not None
        assert comment["comment"] == comment_text
        assert comment["user_id"] == test_user["id"]
        assert comment["property_id"] == prop["id"]

    def test_get_property_comments(self, test_user, mock_property_data):
        """Test retrieving comments for a property."""
        prop = create_property(mock_property_data)
        comment_text = "Great property!"

        add_property_comment(test_user["id"], prop["id"], comment_text)

        comments = get_property_comments(prop["id"])
        assert len(comments) == 1
        assert comments[0]["comment"] == comment_text

    def test_get_comments_multiple(
        self, test_user, second_test_user, mock_property_data
    ):
        """Test retrieving multiple comments."""
        prop = create_property(mock_property_data)

        add_property_comment(test_user["id"], prop["id"], "First comment")
        add_property_comment(second_test_user["id"], prop["id"], "Second comment")

        comments = get_property_comments(prop["id"])
        assert len(comments) == 2

    def test_get_comments_empty(self, mock_property_data):
        """Test that getting comments for property with no comments returns empty."""
        prop = create_property(mock_property_data)

        comments = get_property_comments(prop["id"])
        assert len(comments) == 0

    def test_delete_comment(self, test_user, mock_property_data):
        """Test deleting a comment."""
        prop = create_property(mock_property_data)

        comment = add_property_comment(test_user["id"], prop["id"], "Comment to delete")
        delete_property_comment(comment["id"], test_user["id"])

        comments = get_property_comments(prop["id"])
        assert len(comments) == 0

    def test_delete_comment_wrong_user(
        self, test_user, second_test_user, mock_property_data
    ):
        """Test that user can't delete another user's comment."""
        prop = create_property(mock_property_data)

        comment = add_property_comment(test_user["id"], prop["id"], "Original comment")

        # Try to delete as different user - should fail
        with pytest.raises(Exception):  # Should raise PermissionError or similar
            delete_property_comment(comment["id"], second_test_user["id"])

        # Original comment still exists
        comments = get_property_comments(prop["id"])
        assert len(comments) == 1


@pytest.mark.auth
@pytest.mark.integration
class TestPropertyEndpoints:
    """Test property interaction API endpoints."""

    def test_star_property_endpoint(self, authenticated_client, mock_property_data):
        """Test starring property via API endpoint."""
        prop = create_property(mock_property_data)

        response = authenticated_client.post(f"/properties/{prop['id']}/star")

        assert response.status_code == 200
        assert "starred" in response.json()

    def test_unstar_property_endpoint(self, authenticated_client, mock_property_data):
        """Test unstarring property via API endpoint."""
        prop = create_property(mock_property_data)

        # Star first
        authenticated_client.post(f"/properties/{prop['id']}/star")

        # Then unstar
        response = authenticated_client.post(f"/properties/{prop['id']}/unstar")

        assert response.status_code == 200

    def test_set_status_endpoint(self, authenticated_client, mock_property_data):
        """Test setting property status via API endpoint."""
        prop = create_property(mock_property_data)

        response = authenticated_client.post(
            f"/properties/{prop['id']}/status",
            json={"status": "interested"},
        )

        assert response.status_code == 200

    def test_add_comment_endpoint(self, authenticated_client, mock_property_data):
        """Test adding comment via API endpoint."""
        prop = create_property(mock_property_data)

        response = authenticated_client.post(
            f"/properties/{prop['id']}/comments",
            json={"comment": "Great property!"},
        )

        assert response.status_code == 201
        assert response.json()["comment"] == "Great property!"

    def test_get_comments_endpoint(self, authenticated_client, mock_property_data):
        """Test retrieving comments via API endpoint."""
        prop = create_property(mock_property_data)

        authenticated_client.post(
            f"/properties/{prop['id']}/comments",
            json={"comment": "Test comment"},
        )

        response = authenticated_client.get(f"/properties/{prop['id']}/comments")

        assert response.status_code == 200
        comments = response.json()
        assert len(comments) == 1
        assert comments[0]["comment"] == "Test comment"

    def test_delete_comment_endpoint(self, authenticated_client, mock_property_data):
        """Test deleting comment via API endpoint."""
        prop = create_property(mock_property_data)

        comment_response = authenticated_client.post(
            f"/properties/{prop['id']}/comments",
            json={"comment": "Comment to delete"},
        )
        comment_id = comment_response.json()["id"]

        response = authenticated_client.delete(
            f"/properties/{prop['id']}/comments/{comment_id}"
        )

        assert response.status_code == 200

    def test_star_nonexistent_property(self, authenticated_client):
        """Test starring non-existent property returns 404."""
        response = authenticated_client.post("/properties/99999/star")

        assert response.status_code == 404

    def test_property_endpoints_require_auth(self, client, mock_property_data):
        """Test that property endpoints require authentication."""
        prop = create_property(mock_property_data)

        response = client.post(f"/properties/{prop['id']}/star")
        assert response.status_code == 401

        response = client.post(f"/properties/{prop['id']}/comments")
        assert response.status_code == 401
