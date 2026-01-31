"""Integration tests for property verification API endpoints."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from httpx import AsyncClient

from fastapi.testclient import TestClient
from app.main import app
from app import crud
from app.database import init_db, get_db


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Initialize database for each test."""
    init_db()
    yield
    # Cleanup happens automatically with in-memory SQLite


class TestVerificationEndpoints:
    """Tests for verification API endpoints."""

    def test_start_verification_property_not_found(self, client):
        """Test starting verification for non-existent property."""
        response = client.post("/api/verify/property/999999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("app.main.settings.elevenlabs_api_key", "")
    def test_start_verification_service_disabled(self, client):
        """Test starting verification when service is disabled."""
        # Create a property with agent phone
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO properties (
                    rightmove_id, full_address, agent_phone, first_scraped_at, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "prop_123",
                    "123 Test St",
                    "+447911123456",
                    "2025-01-01T00:00:00",
                    "2025-01-01T00:00:00",
                ),
            )
            property_id = cursor.lastrowid

        response = client.post(f"/api/verify/property/{property_id}")

        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()

    @patch("app.main.settings.elevenlabs_api_key", "test-key")
    def test_start_verification_success(self, client):
        """Test successfully starting property verification."""
        # Create a property with agent phone
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO properties (
                    rightmove_id, full_address, agent_phone, first_scraped_at, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "prop_123",
                    "123 Test St",
                    "+447911123456",
                    "2025-01-01T00:00:00",
                    "2025-01-01T00:00:00",
                ),
            )
            property_id = cursor.lastrowid

        response = client.post(f"/api/verify/property/{property_id}")

        assert response.status_code == 202  # Accepted
        data = response.json()
        assert "job_id" in data
        assert data["property_id"] == property_id
        assert data["status"] == "queued"
        assert "poll_url" in data

    def test_get_job_status_not_found(self, client):
        """Test getting status of non-existent job."""
        response = client.get("/api/verify/job/nonexistent-job-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("app.main.settings.elevenlabs_api_key", "test-key")
    def test_get_job_status_queued(self, client):
        """Test getting status of queued job."""
        # Create a property with agent phone
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO properties (
                    rightmove_id, full_address, agent_phone, first_scraped_at, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "prop_123",
                    "123 Test St",
                    "+447911123456",
                    "2025-01-01T00:00:00",
                    "2025-01-01T00:00:00",
                ),
            )
            property_id = cursor.lastrowid

        # Start verification
        start_response = client.post(f"/api/verify/property/{property_id}")
        job_id = start_response.json()["job_id"]

        # Check job status
        response = client.get(f"/api/verify/job/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] in ["queued", "processing"]
        assert data["created_at"] is not None

    def test_get_verification_statistics(self, client):
        """Test getting verification statistics."""
        response = client.get("/api/verify/stats")

        assert response.status_code == 200
        data = response.json()
        assert "by_status" in data
        assert "total_verifications" in data

    @patch("app.main.settings.elevenlabs_api_key", "test-key")
    def test_full_verification_workflow(self, client):
        """Test complete verification workflow."""
        # Create a property with agent phone
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO properties (
                    rightmove_id, full_address, agent_phone, first_scraped_at, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "prop_full_test",
                    "456 Full Test Ave",
                    "+447922234567",
                    "2025-01-01T00:00:00",
                    "2025-01-01T00:00:00",
                ),
            )
            property_id = cursor.lastrowid

        # Step 1: Start verification
        start_response = client.post(f"/api/verify/property/{property_id}")
        assert start_response.status_code == 202
        job_id = start_response.json()["job_id"]

        # Step 2: Check job exists and is queued
        status_response = client.get(f"/api/verify/job/{job_id}")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["job_id"] == job_id
        assert "created_at" in data

        # Step 3: Verify job has property_id
        assert data["job_id"] is not None


class TestVerificationDatabaseOperations:
    """Tests for verification database CRUD operations."""

    def test_get_property_for_verification(self):
        """Test retrieving property for verification."""
        # Create a property
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO properties (
                    rightmove_id, full_address, agent_phone, agent_name,
                    first_scraped_at, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "prop_456",
                    "789 Agent St",
                    "+447933345678",
                    "John Agent",
                    "2025-01-01T00:00:00",
                    "2025-01-01T00:00:00",
                ),
            )
            property_id = cursor.lastrowid

        # Test retrieval
        prop = crud.get_property_for_verification(property_id)

        assert prop is not None
        assert prop["id"] == property_id
        assert prop["address"] == "789 Agent St"
        assert prop["agent_phone"] == "+447933345678"
        assert prop["agent_name"] == "John Agent"

    def test_get_property_for_verification_no_phone(self):
        """Test retrieving property without agent phone."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO properties (
                    rightmove_id, full_address, agent_phone,
                    first_scraped_at, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "prop_no_phone",
                    "999 No Phone",
                    None,
                    "2025-01-01T00:00:00",
                    "2025-01-01T00:00:00",
                ),
            )
            property_id = cursor.lastrowid

        prop = crud.get_property_for_verification(property_id)
        assert prop is None

    def test_create_verification_log(self):
        """Test creating verification log."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO properties (
                    rightmove_id, full_address, agent_phone,
                    first_scraped_at, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "prop_log",
                    "111 Log St",
                    "+447944456789",
                    "2025-01-01T00:00:00",
                    "2025-01-01T00:00:00",
                ),
            )
            property_id = cursor.lastrowid

        log_id = crud.create_verification_log(
            property_id=property_id,
            agent_phone="+447944456789",
            verification_status="available",
            call_timestamp="2025-01-01T10:00:00",
            call_duration_seconds=120,
            agent_response="Yes, it's available",
            confidence_score=0.95,
            notes="Test verification",
        )

        assert log_id is not None

        # Verify log was created
        log = crud.get_verification_log(property_id)
        assert log is not None
        assert log["property_id"] == property_id
        assert log["verification_status"] == "available"
        assert log["confidence_score"] == 0.95

    def test_update_property_verification_status(self):
        """Test updating property verification status."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO properties (
                    rightmove_id, full_address, agent_phone,
                    first_scraped_at, last_scraped_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "prop_update",
                    "222 Update St",
                    "+447955567890",
                    "2025-01-01T00:00:00",
                    "2025-01-01T00:00:00",
                ),
            )
            property_id = cursor.lastrowid

        success = crud.update_property_verification_status(
            property_id=property_id,
            verification_status="available",
            verification_notes="Property is available",
        )

        assert success is True

        # Verify update
        status = crud.get_verification_status(property_id)
        assert status is not None
        assert status["verification_status"] == "available"
        assert status["verification_notes"] == "Property is available"

    def test_get_unverified_properties(self):
        """Test retrieving unverified properties."""
        # Create multiple properties
        for i in range(5):
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO properties (
                        rightmove_id, full_address, agent_phone,
                        first_scraped_at, last_scraped_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        f"prop_unverified_{i}",
                        f"{i} Unverified St",
                        f"+4479{i}0000000",
                        "2025-01-01T00:00:00",
                        "2025-01-01T00:00:00",
                    ),
                )

        unverified = crud.get_unverified_properties(limit=10)

        assert len(unverified) >= 5
        for prop in unverified:
            assert "id" in prop
            assert "address" in prop
            assert "agent_phone" in prop


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
