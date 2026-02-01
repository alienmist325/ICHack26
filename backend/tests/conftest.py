"""
Pytest configuration and fixtures for the Rightmove API tests.

This module provides:
- Test database setup and teardown
- Authentication fixtures (test user, tokens)
- API client fixture (TestClient)
- Database fixture for test isolation
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.database import get_db_context, init_db
from app.security import hash_password, create_access_token, create_refresh_token


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary test database path."""
    temp_dir = tempfile.gettempdir()
    db_path = Path(temp_dir) / "test_rightmove.db"
    return db_path


@pytest.fixture(scope="session", autouse=True)
def setup_test_database(test_db_path):
    """
    Set up test database once per test session.

    This fixture:
    1. Creates a test database
    2. Initializes the schema
    3. Yields control to tests
    4. Cleans up after all tests
    """
    # Override DATABASE_PATH for tests
    import app.database

    original_path = app.database.DATABASE_PATH
    app.database.DATABASE_PATH = test_db_path

    # Initialize the test database
    init_db()

    yield

    # Cleanup: remove test database
    if test_db_path.exists():
        test_db_path.unlink()

    # Restore original path
    app.database.DATABASE_PATH = original_path


@pytest.fixture(autouse=True)
def clear_database(test_db_path, request):
    """
    Clear all tables after each test for isolation.

    This fixture ensures each test starts with a clean database.
    Order matters due to foreign key constraints.

    Skips clearing for integration and routing tests that require shared state.
    """
    yield

    # Skip clearing for integration and routing tests
    if (
        "test_integration" in request.node.nodeid
        or "test_routing_db_integration" in request.node.nodeid
    ):
        return

    # Clear tables in reverse order of foreign key dependencies
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    try:
        # Disable foreign key checks temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")

        tables = [
            "property_comments",
            "property_status_tracking",
            "property_bookmarks",
            "viewing_events",
            "shared_feed_properties",
            "shared_feed_members",
            "shared_feeds",
            "refresh_tokens",
            "oauth_providers",
            "users",
            "ratings",
            "properties",
        ]

        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except sqlite3.OperationalError:
                # Table might not exist
                pass

        # Re-enable foreign key checks
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def client():
    """
    FastAPI TestClient for making HTTP requests to the app.

    Usage:
        def test_something(client):
            response = client.get("/api/endpoint")
    """
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """
    Standard test user data.

    This fixture provides consistent test data across multiple tests.
    """
    return {
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def test_user(test_user_data, test_db_path):
    """
    Create a test user in the database.

    Returns the created user record with hashed password.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        hashed_password = hash_password(test_user_data["password"])
        cursor.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            (test_user_data["email"], hashed_password),
        )
        cursor.execute(
            "SELECT id, email, hashed_password, is_active FROM users WHERE email = ?",
            (test_user_data["email"],),
        )
        row = cursor.fetchone()
        return dict(zip([desc[0] for desc in cursor.description], row)) if row else None


@pytest.fixture
def test_user_tokens(test_user):
    """
    Create access and refresh tokens for a test user.

    Returns a dict with:
        - access_token: JWT token for authentication
        - refresh_token: Token for refreshing access
        - user_id: ID of the test user
    """
    access_token = create_access_token(test_user["id"], test_user["email"])
    refresh_token = create_refresh_token(test_user["id"], test_user["email"])

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": test_user["id"],
    }


@pytest.fixture
def authenticated_client(client, test_user_tokens):
    """
    TestClient with authentication headers already set.

    Usage:
        def test_protected_endpoint(authenticated_client):
            response = authenticated_client.get("/api/users/me")
            assert response.status_code == 200
    """
    client.headers = {"Authorization": f"Bearer {test_user_tokens['access_token']}"}
    return client


@pytest.fixture
def second_test_user():
    """
    Create a second test user for testing multi-user scenarios.
    """
    with get_db_context() as conn:
        cursor = conn.cursor()
        email = "seconduser@example.com"
        hashed_password = hash_password("SecurePassword456!")
        cursor.execute(
            "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
            (email, hashed_password),
        )
        cursor.execute(
            "SELECT id, email, hashed_password, is_active FROM users WHERE email = ?",
            (email,),
        )
        row = cursor.fetchone()
        return dict(zip([desc[0] for desc in cursor.description], row)) if row else None


@pytest.fixture
def second_user_tokens(second_test_user):
    """
    Create tokens for the second test user.
    """
    access_token = create_access_token(
        second_test_user["id"], second_test_user["email"]
    )
    refresh_token = create_refresh_token(
        second_test_user["id"], second_test_user["email"]
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": second_test_user["id"],
    }


@pytest.fixture
def mock_property_data():
    """
    Standard test property data.

    This fixture provides consistent property data across tests.
    """
    return {
        "rightmove_id": "test_prop_001",
        "listingTitle": "Test Property in London",
        "listing_url": "https://www.rightmove.co.uk/properties/test_001",
        "full_address": "123 Test Street, London, SW1A 1AA",
        "address": "123 Test Street, London",
        "price": 450000,
        "bedrooms": 3,
        "bathrooms": 2,
        "property_type": "Detached",
        "text_description": "A lovely 3 bedroom detached house",
        "agent_name": "Test Estate Agents",
        "agent_phone": "020 1234 5678",
        "images": [
            "https://example.com/img1.jpg",
            "https://example.com/img2.jpg",
        ],
        "features": [
            "Garden",
            "Garage",
            "Modern kitchen",
        ],
    }


@pytest.fixture
def mock_property_data_rental():
    """
    Test property data for a rental property.
    """
    return {
        "rightmove_id": "test_prop_002",
        "listingTitle": "2 Bed Flat to Rent in Manchester",
        "listing_url": "https://www.rightmove.co.uk/properties/test_002",
        "full_address": "456 High Street, Manchester, M1 2AB",
        "address": "456 High Street, Manchester",
        "price": 1200,
        "bedrooms": 2,
        "bathrooms": 1,
        "property_type": "Flat",
        "text_description": "Modern 2 bedroom flat in city centre",
        "agent_name": "City Centre Lettings",
        "agent_phone": "0161 999 8888",
        "images": ["https://example.com/img3.jpg"],
        "features": ["Furnished", "Close to transport"],
    }


# Optional: Markers for test categorization
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "auth: mark test as authentication-related")
    config.addinivalue_line("markers", "db: mark test as database-related")
