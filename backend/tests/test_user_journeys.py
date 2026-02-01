"""
End-to-end user journey tests.

Tests cover complete user workflows:
- Full authentication flow (register → login → profile → logout)
- Property discovery flow (search → star → status → comment)
- Viewing management flow (schedule → view → export)
- Shared feed collaboration flow (create → invite → share properties)
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.integration
class TestCompleteAuthenticationFlow:
    """Test the complete authentication lifecycle."""

    def test_user_registration_login_logout_flow(self, client):
        """Test user registers, logs in, and logs out."""
        # Step 1: Register
        register_response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
            },
        )

        assert register_response.status_code == 201
        register_data = register_response.json()
        access_token = register_data["access_token"]
        refresh_token = register_data["refresh_token"]

        # Step 2: Access protected endpoint with token
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == "newuser@example.com"

        # Step 3: Refresh token
        refresh_response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]
        assert new_token != access_token

        # Step 4: Logout
        logout_response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {new_token}"},
        )

        assert logout_response.status_code == 200

    def test_user_registration_with_profile_setup(self, client):
        """Test user registration followed by profile setup."""
        # Register
        register_response = client.post(
            "/auth/register",
            json={
                "email": "profileuser@example.com",
                "password": "SecurePassword123!",
            },
        )

        token = register_response.json()["access_token"]

        # Update profile immediately after registration
        profile_response = client.put(
            "/users/profile",
            json={
                "bio": "Looking for 2-bed flat in London",
                "preferences": {
                    "minPrice": 500000,
                    "maxPrice": 1500000,
                    "minBedrooms": 2,
                    "maxBedrooms": 3,
                    "locations": ["London", "Shoreditch"],
                },
                "notifications": {
                    "emailUpdates": True,
                    "pushNotifications": False,
                },
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["bio"] == "Looking for 2-bed flat in London"


@pytest.mark.integration
class TestPropertyDiscoveryFlow:
    """Test the property discovery and interaction workflow."""

    def test_search_star_comment_property_flow(
        self, authenticated_client, mock_property_data
    ):
        """Test discovering, starring, and commenting on a property."""
        from app.crud import create_property

        # Create test property
        prop = create_property(mock_property_data)

        # Step 1: Get property details
        get_response = authenticated_client.get(f"/properties/{prop['id']}")
        assert get_response.status_code == 200

        # Step 2: Star the property
        star_response = authenticated_client.post(f"/properties/{prop['id']}/star")
        assert star_response.status_code == 200

        # Step 3: Add comment
        comment_response = authenticated_client.post(
            f"/properties/{prop['id']}/comments",
            json={"comment": "Love this property! Great location and price."},
        )
        assert comment_response.status_code == 201

        # Step 4: Set status to interested
        status_response = authenticated_client.post(
            f"/properties/{prop['id']}/status",
            json={"status": "interested"},
        )
        assert status_response.status_code == 200

        # Step 5: Retrieve all property details
        final_response = authenticated_client.get(f"/properties/{prop['id']}")
        assert final_response.status_code == 200

    def test_property_status_progression(
        self, authenticated_client, mock_property_data
    ):
        """Test property status progression: interested → viewing → offer → accepted."""
        from app.crud import create_property

        prop = create_property(mock_property_data)

        statuses = ["interested", "viewing", "offer", "accepted"]

        for status in statuses:
            response = authenticated_client.post(
                f"/properties/{prop['id']}/status",
                json={"status": status},
            )

            assert response.status_code == 200
            assert response.json()["status"] == status

    def test_bookmark_multiple_properties_flow(
        self, authenticated_client, mock_property_data, mock_property_data_rental
    ):
        """Test bookmarking multiple properties and retrieving them."""
        from app.crud import create_property

        prop1 = create_property(mock_property_data)
        prop2 = create_property(mock_property_data_rental)

        # Star both properties
        authenticated_client.post(f"/properties/{prop1['id']}/star")
        authenticated_client.post(f"/properties/{prop2['id']}/star")

        # Get bookmarks
        bookmarks_response = authenticated_client.get("/properties/bookmarks")

        assert bookmarks_response.status_code == 200
        bookmarks = bookmarks_response.json()
        assert len(bookmarks) >= 2


@pytest.mark.integration
class TestViewingCalendarFlow:
    """Test the viewing calendar workflow."""

    def test_schedule_viewing_and_export_flow(
        self, authenticated_client, mock_property_data
    ):
        """Test scheduling a viewing and exporting to calendar."""
        from app.crud import create_property

        prop = create_property(mock_property_data)
        viewing_time = (datetime.now() + timedelta(days=5)).isoformat()

        # Step 1: Schedule viewing
        viewing_response = authenticated_client.post(
            "/viewings",
            json={
                "property_id": prop["id"],
                "scheduled_at": viewing_time,
                "duration_minutes": 30,
                "organizer_name": "John Smith",
                "organizer_phone": "020 1234 5678",
                "organizer_email": "john@agents.com",
                "notes": "Main entrance viewings at 2pm",
            },
        )

        assert viewing_response.status_code == 201
        viewing_data = viewing_response.json()
        viewing_id = viewing_data["id"]

        # Step 2: Retrieve viewing details
        get_response = authenticated_client.get(f"/viewings/{viewing_id}")
        assert get_response.status_code == 200

        # Step 3: Export to iCalendar
        ical_response = authenticated_client.get(f"/viewings/{viewing_id}/export/ical")
        assert ical_response.status_code == 200
        assert "BEGIN:VCALENDAR" in ical_response.text
        assert "John Smith" in ical_response.text

    def test_schedule_multiple_viewings_flow(
        self, authenticated_client, mock_property_data, mock_property_data_rental
    ):
        """Test scheduling multiple viewings and exporting all."""
        from app.crud import create_property

        prop1 = create_property(mock_property_data)
        prop2 = create_property(mock_property_data_rental)

        # Schedule two viewings
        for i, prop in enumerate([prop1, prop2], 1):
            authenticated_client.post(
                "/viewings",
                json={
                    "property_id": prop["id"],
                    "scheduled_at": (datetime.now() + timedelta(days=i)).isoformat(),
                    "duration_minutes": 30,
                },
            )

        # Get all viewings
        all_viewings_response = authenticated_client.get("/viewings")
        assert all_viewings_response.status_code == 200
        viewings = all_viewings_response.json()
        assert len(viewings) >= 2

        # Export all to iCalendar
        export_response = authenticated_client.get("/viewings/export/ical")
        assert export_response.status_code == 200
        assert export_response.text.count("BEGIN:VEVENT") >= 2


@pytest.mark.integration
class TestSharedFeedCollaborationFlow:
    """Test shared feed collaboration workflow."""

    def test_create_feed_invite_add_properties_flow(
        self,
        client,
        authenticated_client,
        second_user_tokens,
        mock_property_data,
        mock_property_data_rental,
    ):
        """Test complete shared feed collaboration."""
        from app.crud import create_property

        # Step 1: User 1 creates a shared feed
        feed_response = authenticated_client.post(
            "/shared-feeds",
            json={
                "name": "House Hunting with Sarah",
                "description": "Our dream home wishlist",
                "max_members": 4,
            },
        )

        assert feed_response.status_code == 201
        feed_data = feed_response.json()
        feed_id = feed_data["id"]
        invite_code = feed_data["invite_code"]

        # Step 2: User 1 adds properties to the feed
        prop1 = create_property(mock_property_data)
        prop2 = create_property(mock_property_data_rental)

        authenticated_client.post(
            f"/shared-feeds/{feed_id}/properties",
            json={"property_id": prop1["id"]},
        )
        authenticated_client.post(
            f"/shared-feeds/{feed_id}/properties",
            json={"property_id": prop2["id"]},
        )

        # Step 3: User 2 joins the feed using invite code
        client.headers = {
            "Authorization": f"Bearer {second_user_tokens['access_token']}"
        }
        join_response = client.post(
            "/shared-feeds/join",
            json={"invite_code": invite_code},
        )

        assert join_response.status_code == 200

        # Step 4: User 2 sees the properties in the shared feed
        properties_response = client.get(f"/shared-feeds/{feed_id}/properties")
        assert properties_response.status_code == 200
        properties = properties_response.json()
        assert len(properties) >= 2

        # Step 5: User 2 adds another property
        prop3_data = {
            "rightmove_id": "test_prop_003",
            "listingTitle": "Another great property",
            "listing_url": "https://example.com/prop3",
            "full_address": "999 Oak Street",
            "address": "999 Oak Street",
            "price": 500000,
        }
        from app.crud import create_property

        prop3 = create_property(prop3_data)

        client.post(
            f"/shared-feeds/{feed_id}/properties",
            json={"property_id": prop3["id"]},
        )

        # Step 6: User 1 sees the updated feed
        client.headers = {
            "Authorization": f"Bearer {authenticated_client.headers['Authorization'].replace('Bearer ', '')}"
        }
        final_response = client.get(f"/shared-feeds/{feed_id}/properties")
        assert final_response.status_code == 200
        final_properties = final_response.json()
        assert len(final_properties) >= 3

    def test_multiple_users_collaborating_flow(
        self, authenticated_client, client, second_user_tokens, mock_property_data
    ):
        """Test multiple users collaborating on a shared feed."""
        from app.crud import create_property

        # Create feed
        feed_response = authenticated_client.post(
            "/shared-feeds",
            json={"name": "Team Hunt", "max_members": 8},
        )
        feed_id = feed_response.json()["id"]
        invite_code = feed_response.json()["invite_code"]

        # Multiple users join
        client.headers = {
            "Authorization": f"Bearer {second_user_tokens['access_token']}"
        }
        join_response = client.post(
            "/shared-feeds/join",
            json={"invite_code": invite_code},
        )
        assert join_response.status_code == 200

        # Add property as user 1
        prop = create_property(mock_property_data)
        authenticated_client.post(
            f"/shared-feeds/{feed_id}/properties",
            json={"property_id": prop["id"]},
        )

        # User 2 sees the property
        user2_props = client.get(f"/shared-feeds/{feed_id}/properties")
        assert user2_props.status_code == 200
        assert len(user2_props.json()) >= 1


@pytest.mark.integration
class TestErrorHandlingFlow:
    """Test error handling in various workflows."""

    def test_invalid_credentials_flow(self, client):
        """Test login with invalid credentials."""
        # Try to login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

    def test_access_protected_resource_without_auth(self, client):
        """Test accessing protected resources without authentication."""
        response = client.get("/users/profile")
        assert response.status_code == 401

    def test_nonexistent_property_operations(self, authenticated_client):
        """Test operations on non-existent property."""
        response = authenticated_client.post("/properties/99999/star")
        assert response.status_code == 404

    def test_unauthorized_feed_access(
        self, client, authenticated_client, second_user_tokens
    ):
        """Test that users can't access other users' private feeds."""
        # Create feed as user 1
        feed_response = authenticated_client.post(
            "/shared-feeds",
            json={"name": "Private Feed"},
        )
        feed_id = feed_response.json()["id"]

        # Try to access as user 2 without invitation
        client.headers = {
            "Authorization": f"Bearer {second_user_tokens['access_token']}"
        }
        response = client.get(f"/shared-feeds/{feed_id}")

        # Should be forbidden or not found
        assert response.status_code in [403, 404]
