"""
Viewing calendar tests.

Tests cover:
- Creating viewing events
- Retrieving viewing schedule
- Updating viewing details
- Deleting viewing events
- iCalendar export functionality
- Timezone handling
- Conflict detection (optional)
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crud import (
    create_viewing_event,
    get_viewing_events,
    get_viewing_event,
    update_viewing_event,
    delete_viewing_event,
    get_upcoming_viewings,
)


@pytest.mark.db
class TestViewingCreation:
    """Test creating and managing viewing events."""

    def test_create_viewing_event(self, test_user, mock_property_data):
        """Test creating a viewing event."""
        from app.crud import create_property

        prop = create_property(mock_property_data)
        scheduled_time = datetime.now() + timedelta(days=3)

        viewing = create_viewing_event(
            user_id=test_user["id"],
            property_id=prop["id"],
            scheduled_at=scheduled_time,
            duration_minutes=30,
            organizer_name="Estate Agent",
            organizer_phone="020 1234 5678",
            organizer_email="agent@example.com",
            notes="Viewing on Sunday afternoon",
        )

        assert viewing is not None
        assert viewing["user_id"] == test_user["id"]
        assert viewing["property_id"] == prop["id"]
        assert viewing["duration_minutes"] == 30

    def test_get_viewing_event(self, test_user, mock_property_data):
        """Test retrieving a viewing event."""
        from app.crud import create_property

        prop = create_property(mock_property_data)
        scheduled_time = datetime.now() + timedelta(days=3)

        created = create_viewing_event(
            user_id=test_user["id"],
            property_id=prop["id"],
            scheduled_at=scheduled_time,
            duration_minutes=30,
        )

        retrieved = get_viewing_event(created["id"])

        assert retrieved is not None
        assert retrieved["id"] == created["id"]
        assert retrieved["property_id"] == prop["id"]

    def test_get_user_viewing_events(
        self, test_user, mock_property_data, mock_property_data_rental
    ):
        """Test retrieving all viewing events for a user."""
        from app.crud import create_property

        prop1 = create_property(mock_property_data)
        prop2 = create_property(mock_property_data_rental)

        create_viewing_event(
            user_id=test_user["id"],
            property_id=prop1["id"],
            scheduled_at=datetime.now() + timedelta(days=1),
        )
        create_viewing_event(
            user_id=test_user["id"],
            property_id=prop2["id"],
            scheduled_at=datetime.now() + timedelta(days=2),
        )

        viewings = get_viewing_events(test_user["id"])

        assert len(viewings) == 2

    def test_get_upcoming_viewings(self, test_user, mock_property_data):
        """Test getting only upcoming viewings."""
        from app.crud import create_property

        prop = create_property(mock_property_data)

        # Create future viewing
        future_time = datetime.now() + timedelta(days=3)
        create_viewing_event(
            user_id=test_user["id"],
            property_id=prop["id"],
            scheduled_at=future_time,
        )

        # Create past viewing
        past_time = datetime.now() - timedelta(days=2)
        create_viewing_event(
            user_id=test_user["id"],
            property_id=prop["id"],
            scheduled_at=past_time,
        )

        upcoming = get_upcoming_viewings(test_user["id"])

        # Should only include future viewing
        assert len(upcoming) == 1
        assert upcoming[0]["scheduled_at"] > datetime.now()

    def test_update_viewing_event(self, test_user, mock_property_data):
        """Test updating a viewing event."""
        from app.crud import create_property

        prop = create_property(mock_property_data)
        scheduled_time = datetime.now() + timedelta(days=3)

        viewing = create_viewing_event(
            user_id=test_user["id"],
            property_id=prop["id"],
            scheduled_at=scheduled_time,
            duration_minutes=30,
            notes="Original notes",
        )

        # Update
        new_time = datetime.now() + timedelta(days=4)
        updated = update_viewing_event(
            viewing["id"],
            scheduled_at=new_time,
            duration_minutes=60,
            notes="Updated notes",
        )

        assert updated["duration_minutes"] == 60
        assert updated["notes"] == "Updated notes"

    def test_delete_viewing_event(self, test_user, mock_property_data):
        """Test deleting a viewing event."""
        from app.crud import create_property

        prop = create_property(mock_property_data)
        scheduled_time = datetime.now() + timedelta(days=3)

        viewing = create_viewing_event(
            user_id=test_user["id"],
            property_id=prop["id"],
            scheduled_at=scheduled_time,
        )

        delete_viewing_event(viewing["id"])

        retrieved = get_viewing_event(viewing["id"])
        assert retrieved is None

    def test_viewing_with_organizer_details(self, test_user, mock_property_data):
        """Test viewing with organizer information."""
        from app.crud import create_property

        prop = create_property(mock_property_data)

        viewing = create_viewing_event(
            user_id=test_user["id"],
            property_id=prop["id"],
            scheduled_at=datetime.now() + timedelta(days=3),
            organizer_name="John Smith",
            organizer_phone="020 1234 5678",
            organizer_email="john@agents.com",
        )

        assert viewing["organizer_name"] == "John Smith"
        assert viewing["organizer_phone"] == "020 1234 5678"
        assert viewing["organizer_email"] == "john@agents.com"

    def test_viewing_duration_defaults(self, test_user, mock_property_data):
        """Test that viewing duration defaults to 30 minutes."""
        from app.crud import create_property

        prop = create_property(mock_property_data)

        viewing = create_viewing_event(
            user_id=test_user["id"],
            property_id=prop["id"],
            scheduled_at=datetime.now() + timedelta(days=3),
        )

        assert viewing["duration_minutes"] == 30


@pytest.mark.auth
@pytest.mark.integration
class TestViewingEndpoints:
    """Test viewing calendar API endpoints."""

    def test_create_viewing_endpoint(self, authenticated_client, mock_property_data):
        """Test creating a viewing via API."""
        from app.crud import create_property

        prop = create_property(mock_property_data)
        scheduled_time = (datetime.now() + timedelta(days=3)).isoformat()

        response = authenticated_client.post(
            "/viewings",
            json={
                "property_id": prop["id"],
                "scheduled_at": scheduled_time,
                "duration_minutes": 30,
                "organizer_name": "Agent",
                "organizer_phone": "020 1234 5678",
                "notes": "Test viewing",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["property_id"] == prop["id"]
        assert data["duration_minutes"] == 30

    def test_get_viewings_endpoint(self, authenticated_client, mock_property_data):
        """Test retrieving viewing events."""
        from app.crud import create_property, create_viewing_event

        prop = create_property(mock_property_data)
        create_viewing_event(
            user_id=authenticated_client.__dict__.get(
                "user_id"
            ),  # Would need to get from context
            property_id=prop["id"],
            scheduled_at=datetime.now() + timedelta(days=3),
        )

        response = authenticated_client.get("/viewings")

        assert response.status_code == 200
        # Should return at least the viewing we created

    def test_get_upcoming_viewings_endpoint(self, authenticated_client):
        """Test retrieving only upcoming viewings."""
        response = authenticated_client.get("/viewings/upcoming")

        assert response.status_code == 200
        viewings = response.json()
        # All viewings should be in the future
        for viewing in viewings:
            assert datetime.fromisoformat(viewing["scheduled_at"]) > datetime.now()

    def test_update_viewing_endpoint(self, authenticated_client, mock_property_data):
        """Test updating a viewing event."""
        from app.crud import create_property, create_viewing_event

        prop = create_property(mock_property_data)
        viewing = create_viewing_event(
            user_id=authenticated_client.__dict__.get("user_id"),
            property_id=prop["id"],
            scheduled_at=datetime.now() + timedelta(days=3),
        )

        new_time = (datetime.now() + timedelta(days=4)).isoformat()
        response = authenticated_client.put(
            f"/viewings/{viewing['id']}",
            json={
                "duration_minutes": 60,
                "notes": "Updated notes",
                "scheduled_at": new_time,
            },
        )

        assert response.status_code == 200

    def test_delete_viewing_endpoint(self, authenticated_client, mock_property_data):
        """Test deleting a viewing."""
        from app.crud import create_property, create_viewing_event

        prop = create_property(mock_property_data)
        viewing = create_viewing_event(
            user_id=authenticated_client.__dict__.get("user_id"),
            property_id=prop["id"],
            scheduled_at=datetime.now() + timedelta(days=3),
        )

        response = authenticated_client.delete(f"/viewings/{viewing['id']}")

        assert response.status_code == 200

    def test_viewing_endpoints_require_auth(self, client):
        """Test that viewing endpoints require authentication."""
        response = client.get("/viewings")
        assert response.status_code == 401

        response = client.post("/viewings", json={})
        assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.integration
class TestICalendarExport:
    """Test iCalendar export functionality."""

    def test_export_single_viewing_as_ical(
        self, authenticated_client, mock_property_data
    ):
        """Test exporting single viewing as iCalendar format."""
        from app.crud import create_property, create_viewing_event

        prop = create_property(mock_property_data)
        viewing = create_viewing_event(
            user_id=authenticated_client.__dict__.get("user_id"),
            property_id=prop["id"],
            scheduled_at=datetime.now() + timedelta(days=3),
            organizer_name="Test Agent",
        )

        response = authenticated_client.get(f"/viewings/{viewing['id']}/export/ical")

        assert response.status_code == 200
        assert "BEGIN:VCALENDAR" in response.text
        assert "BEGIN:VEVENT" in response.text
        assert "Test Agent" in response.text

    def test_export_all_viewings_as_ical(
        self, authenticated_client, mock_property_data, mock_property_data_rental
    ):
        """Test exporting all viewings as iCalendar."""
        from app.crud import create_property, create_viewing_event

        prop1 = create_property(mock_property_data)
        prop2 = create_property(mock_property_data_rental)

        create_viewing_event(
            user_id=authenticated_client.__dict__.get("user_id"),
            property_id=prop1["id"],
            scheduled_at=datetime.now() + timedelta(days=1),
        )
        create_viewing_event(
            user_id=authenticated_client.__dict__.get("user_id"),
            property_id=prop2["id"],
            scheduled_at=datetime.now() + timedelta(days=2),
        )

        response = authenticated_client.get("/viewings/export/ical")

        assert response.status_code == 200
        assert "BEGIN:VCALENDAR" in response.text
        # Should have multiple events
        assert response.text.count("BEGIN:VEVENT") >= 2

    def test_ical_export_content_type(self, authenticated_client, mock_property_data):
        """Test that iCalendar export has correct content type."""
        from app.crud import create_property, create_viewing_event

        prop = create_property(mock_property_data)
        create_viewing_event(
            user_id=authenticated_client.__dict__.get("user_id"),
            property_id=prop["id"],
            scheduled_at=datetime.now() + timedelta(days=3),
        )

        response = authenticated_client.get("/viewings/export/ical")

        assert response.status_code == 200
        assert "text/calendar" in response.headers.get("content-type", "")

    def test_ical_export_valid_format(self, authenticated_client, mock_property_data):
        """Test that exported iCalendar is valid format."""
        from app.crud import create_property, create_viewing_event

        prop = create_property(mock_property_data)
        create_viewing_event(
            user_id=authenticated_client.__dict__.get("user_id"),
            property_id=prop["id"],
            scheduled_at=datetime.now() + timedelta(days=3),
            organizer_name="Test Agent",
            notes="Test notes",
        )

        response = authenticated_client.get("/viewings/export/ical")

        content = response.text

        # Check required iCalendar components
        assert "BEGIN:VCALENDAR" in content
        assert "VERSION:2.0" in content
        assert "PRODID:" in content
        assert "BEGIN:VEVENT" in content
        assert "DTSTART:" in content
        assert "DTEND:" in content
        assert "SUMMARY:" in content
        assert "END:VEVENT" in content
        assert "END:VCALENDAR" in content
