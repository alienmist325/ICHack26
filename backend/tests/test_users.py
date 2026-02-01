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
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crud import (
    create_user_profile,
    get_user_profile,
    update_user_profile,
    get_user_by_id,
)
from app.security import hash_password


@pytest.mark.db
class TestUserProfile:
    """Test user profile management."""

    def test_create_user_profile(self, test_user):
        """Test creating a user profile."""
        profile = create_user_profile(
            user_id=test_user["id"],
            bio="Looking for a 2-bedroom apartment",
            preferred_min_price=500,
            preferred_max_price=2000,
            preferred_bedrooms_min=2,
            preferred_bedrooms_max=3,
            preferred_locations=["London", "Manchester"],
            notify_new_matches=True,
            notify_feed_updates=True,
        )

        assert profile is not None
        assert profile["user_id"] == test_user["id"]
        assert profile["bio"] == "Looking for a 2-bedroom apartment"
        assert profile["preferred_min_price"] == 500
        assert profile["preferred_max_price"] == 2000

    def test_get_user_profile(self, test_user):
        """Test retrieving user profile."""
        create_user_profile(
            user_id=test_user["id"],
            bio="Test bio",
            preferred_min_price=500,
            preferred_max_price=2000,
        )

        profile = get_user_profile(test_user["id"])

        assert profile is not None
        assert profile["user_id"] == test_user["id"]
        assert profile["bio"] == "Test bio"

    def test_get_nonexistent_profile(self, test_user):
        """Test that getting profile for user without one returns None."""
        profile = get_user_profile(test_user["id"])

        # Should either return None or auto-create empty profile
        # depending on implementation
        assert profile is None or profile["user_id"] == test_user["id"]

    def test_update_user_profile(self, test_user):
        """Test updating user profile."""
        # Create initial profile
        create_user_profile(
            user_id=test_user["id"],
            bio="Old bio",
            preferred_min_price=500,
        )

        # Update profile
        updated = update_user_profile(
            user_id=test_user["id"],
            bio="New bio",
            preferred_max_price=3000,
        )

        assert updated["bio"] == "New bio"
        assert updated["preferred_max_price"] == 3000

    def test_update_profile_partial(self, test_user):
        """Test partial profile update preserves existing data."""
        create_user_profile(
            user_id=test_user["id"],
            bio="Original bio",
            preferred_min_price=500,
            preferred_max_price=2000,
        )

        # Update only bio
        updated = update_user_profile(
            user_id=test_user["id"],
            bio="Updated bio",
        )

        assert updated["bio"] == "Updated bio"
        # Other fields should be preserved
        assert updated["preferred_min_price"] == 500
        assert updated["preferred_max_price"] == 2000

    def test_profile_with_locations(self, test_user):
        """Test profile with multiple preferred locations."""
        locations = ["London", "Manchester", "Bristol", "Edinburgh"]

        profile = create_user_profile(
            user_id=test_user["id"],
            bio="Looking for properties",
            preferred_locations=locations,
        )

        assert profile is not None
        assert profile["preferred_locations"] == locations

    def test_profile_notification_settings(self, test_user):
        """Test notification preference settings."""
        profile = create_user_profile(
            user_id=test_user["id"],
            notify_new_matches=True,
            notify_feed_updates=False,
            notify_viewing_reminders=True,
        )

        assert profile["notify_new_matches"] is True
        assert profile["notify_feed_updates"] is False
        assert profile["notify_viewing_reminders"] is True

    def test_profile_price_range(self, test_user):
        """Test setting price range preferences."""
        profile = create_user_profile(
            user_id=test_user["id"],
            preferred_min_price=250000,
            preferred_max_price=750000,
        )

        assert profile["preferred_min_price"] == 250000
        assert profile["preferred_max_price"] == 750000

    def test_profile_bedroom_range(self, test_user):
        """Test setting bedroom preferences."""
        profile = create_user_profile(
            user_id=test_user["id"],
            preferred_bedrooms_min=2,
            preferred_bedrooms_max=4,
        )

        assert profile["preferred_bedrooms_min"] == 2
        assert profile["preferred_bedrooms_max"] == 4


@pytest.mark.auth
@pytest.mark.integration
class TestUserProfileEndpoints:
    """Test user profile API endpoints."""

    def test_get_profile_endpoint(self, authenticated_client, test_user):
        """Test getting user profile via API."""
        # Create profile first
        create_user_profile(
            user_id=test_user["id"],
            bio="Test profile",
            preferred_min_price=500,
        )

        response = authenticated_client.get("/users/profile")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == test_user["id"]
        assert data["bio"] == "Test profile"

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

    def test_cannot_access_other_user_profile(
        self, client, test_user, second_user_tokens
    ):
        """Test that users can only access their own profile."""
        create_user_profile(
            user_id=test_user["id"],
            bio="Secret profile",
        )

        # Try to access as different user
        client.headers = {
            "Authorization": f"Bearer {second_user_tokens['access_token']}"
        }
        response = client.get(f"/users/{test_user['id']}/profile")

        # Should either be 403 or not reveal data
        assert response.status_code in [403, 404]

    def test_get_my_profile_endpoint(self, authenticated_client, test_user):
        """Test getting own profile endpoint."""
        create_user_profile(
            user_id=test_user["id"],
            bio="My profile",
            preferred_min_price=300000,
        )

        response = authenticated_client.get("/users/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user["id"]
        assert data["email"] == test_user["email"]


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
