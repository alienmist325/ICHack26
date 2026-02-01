"""Pytest configuration and fixtures for backend tests."""

import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Set TEST_MODE before importing database module
os.environ["TEST_MODE"] = "true"

from backend.app.database import (
    DATABASE_PATH,
    init_db,
    reset_test_db,
    get_db_connection,
)


# Module-level flag to track if we're in integration tests
_integration_tests_completed = False


@pytest.fixture(scope="session", autouse=True)
def enable_test_mode():
    """Verify test mode is enabled for the entire test session."""
    # TEST_MODE should already be set at module level
    assert os.environ.get("TEST_MODE") == "true", (
        "TEST_MODE should be set before imports"
    )
    yield


@pytest.fixture(scope="session", autouse=True)
def setup_session_db():
    """Initialize database for the session."""
    # Initialize database once at session start
    init_db()
    yield
    # Cleanup after all tests
    reset_test_db()


# Track if we've already initialized the session DB
_db_initialized_for_test = False


@pytest.fixture(autouse=True)
def setup_test_db_fixture(request):
    """
    Ensure database is properly initialized for each test.

    This fixture ensures the shared in-memory database is available
    and has the correct schema for all tests. It also clears data
    between tests to prevent test interdependence.
    """
    global _db_initialized_for_test

    # Database is already initialized by setup_session_db at session scope
    # Just verify it's still there; re-initialize if needed
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
        count = cursor.fetchone()[0]
        if count == 0:
            # Tables don't exist, reinitialize
            init_db()
        else:
            # Tables exist, clear data from them (except for integration/db tests)
            is_integration_test = "test_integration.py" in request.node.nodeid
            is_routing_db_integration = (
                "test_routing_db_integration.py" in request.node.nodeid
            )
            if not is_integration_test and not is_routing_db_integration:
                # Clear all data from tables to avoid test interdependence
                cursor.execute("DELETE FROM ratings")
                cursor.execute("DELETE FROM verification_logs")
                cursor.execute("DELETE FROM properties")
                conn.commit()
    except sqlite3.OperationalError:
        # Database is in a bad state, reinitialize
        reset_test_db()
        init_db()

    yield


@pytest.fixture
def temp_db_with_schema():
    """Create a temporary test database with initialized schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Create and initialize the database with schema
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create all required tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rightmove_id TEXT UNIQUE NOT NULL,
                listing_title TEXT,
                listing_url TEXT,
                incode TEXT,
                outcode TEXT,
                full_address TEXT,
                latitude REAL,
                longitude REAL,
                
                -- Property details
                property_type TEXT,
                listing_type TEXT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                size TEXT,
                furnishing_type TEXT,
                amenities TEXT,  -- JSON array
                
                -- Pricing
                price REAL,
                deposit REAL,
                price_history TEXT,  -- JSON array
                
                -- Ownership details
                tenure TEXT,
                council_tax_band TEXT,
                council_tax_exempt BOOLEAN,
                years_remaining_on_lease INTEGER,
                annual_ground_rent REAL,
                annual_service_charge REAL,
                ground_rent_percentage_increase REAL,
                
                -- Description
                text_description TEXT,
                formatted_html_description TEXT,
                
                -- Media
                images TEXT,  -- JSON array
                floorplans TEXT,  -- JSON array
                brochures TEXT,  -- JSON array
                epc TEXT,  -- JSON object
                
                -- Agent information
                agent_name TEXT,
                agent_logo TEXT,
                agent_phone TEXT,
                agent_address TEXT,
                agent_profile_url TEXT,
                agent_description TEXT,
                agent_listings_url TEXT,
                
                -- Status
                sold BOOLEAN DEFAULT 0,
                removed BOOLEAN DEFAULT 0,
                display_status TEXT,
                listing_update_reason TEXT,
                
                -- Dates
                first_visible_date TEXT,
                listing_update_date TEXT,
                first_scraped_at TEXT NOT NULL,
                last_scraped_at TEXT NOT NULL,
                
                -- Nearby amenities
                nearest_schools TEXT,  -- JSON array
                
                -- Verification status
                verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'processing', 'available', 'sold', 'rented', 'unclear', 'pending_review', 'failed')),
                last_verified_at TEXT,
                verification_notes TEXT,

                -- Timestamps
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL,
                vote_type TEXT NOT NULL CHECK(vote_type IN ('upvote', 'downvote')),
                voted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL UNIQUE,
                call_timestamp TEXT,
                call_duration_seconds INTEGER,
                agent_phone TEXT,
                agent_response TEXT,
                verification_status TEXT CHECK(verification_status IN ('available', 'sold', 'rented', 'unclear', 'pending_review', 'failed')),
                confidence_score REAL,
                notes TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_rightmove_id 
            ON properties(rightmove_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_location 
            ON properties(latitude, longitude)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ratings_property_id 
            ON ratings(property_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verification_logs_property_id 
            ON verification_logs(property_id)
        """)

        conn.commit()
        conn.close()

        yield db_path
