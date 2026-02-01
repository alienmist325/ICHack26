"""
User profile and preferences tests.

Tests cover:
- User profile creation and retrieval
- Bio management
- Preference settings (price range, bedrooms, locations)
- Notification preferences
- Profile updates
- User deletion
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crud import (
    get_user_by_id,
)


@pytest.mark.auth
@pytest.mark.integration
class TestUserProfileEndpoints:
    """Test user profile API endpoints."""

    def test_update_profile_endpoint(self, authenticated_client, test_user):
        """Test updating profile via API."""
        response = authenticated_client.put(
            "/users/profile",
            json={
                "bio": "Updated bio",
                "preferences": {
                    "minPrice": 500000,
                    "maxPrice": 1000000,
                    "minBedrooms": 2,
                    "maxBedrooms": 4,
                    "locations": ["London", "Manchester"],
                },
                "notifications": {
                    "emailUpdates": True,
                    "pushNotifications": False,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Updated bio"

    def test_profile_endpoint_requires_auth(self, client):
        """Test that profile endpoints require authentication."""
        response = client.get("/users/profile")
        assert response.status_code == 401

        response = client.put("/users/profile", json={"bio": "test"})
        assert response.status_code == 401

    def test_delete_account_endpoint(self, authenticated_client, test_user):
        """Test account deletion via API."""
        response = authenticated_client.delete("/users/profile")

        assert response.status_code == 200

        # Verify user is deleted
        deleted_user = get_user_by_id(test_user["id"])
        assert deleted_user is None or deleted_user["is_active"] is False


@pytest.mark.auth
@pytest.mark.integration
class TestNotificationSettings:
    """Test notification preference management."""

    def test_update_notification_settings(self, authenticated_client):
        """Test updating notification preferences."""
        response = authenticated_client.put(
            "/users/notifications",
            json={
                "email_updates": True,
                "push_notifications": False,
                "sms_notifications": False,
            },
        )

        assert response.status_code == 200

    def test_get_notification_settings(self, authenticated_client, test_user):
        """Test retrieving notification preferences."""
        response = authenticated_client.get("/users/notifications")

        assert response.status_code == 200
        data = response.json()
        assert "email_updates" in data
        assert "push_notifications" in data

    def test_notification_settings_require_auth(self, client):
        """Test that notification endpoints require authentication."""
        response = client.get("/users/notifications")
        assert response.status_code == 401

        response = client.put(
            "/users/notifications",
            json={"email_updates": True},
        )
        assert response.status_code == 401
