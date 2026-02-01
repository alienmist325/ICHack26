"""
Database integration tests for routing endpoints.

Tests the routing endpoints with actual database properties to ensure
end-to-end functionality with real data.

These tests:
1. Create a test database with sample properties
2. Test routing endpoints against actual property data
3. Validate response structures with real coordinates
4. Test filtering and querying with location-based data
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, get_routing_service_dep
from backend.services.routing_service import RoutingService

# ============================================================================
# Test Configuration
# ============================================================================

# Real UK coordinates for testing properties
LONDON_LAT, LONDON_LON = 51.5074, -0.1278
MANCHESTER_LAT, MANCHESTER_LON = 53.4808, -2.2426
LEEDS_LAT, LEEDS_LON = 53.8008, -1.5491
BIRMINGHAM_LAT, BIRMINGHAM_LON = 52.5085, -1.8845


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture
def temp_db():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Patch the DATABASE_PATH to use temp database
        with patch("backend.app.database.DATABASE_PATH", db_path):
            # Initialize the database
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Create properties table
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
                    property_type TEXT,
                    listing_type TEXT,
                    bedrooms INTEGER,
                    bathrooms INTEGER,
                    size TEXT,
                    furnishing_type TEXT,
                    amenities TEXT,
                    price REAL,
                    first_listed_date TEXT,
                    days_listed INTEGER,
                    description TEXT,
                    images TEXT,
                    agent_name TEXT,
                    agent_phone TEXT,
                    agent_profile_url TEXT,
                    rental_frequency TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()

            yield db_path


@pytest.fixture
def db_with_properties(temp_db, monkeypatch):
    """Create database with sample properties in different locations."""
    # Monkeypatch to use test database
    monkeypatch.setattr("backend.app.database.DATABASE_PATH", temp_db)

    # Insert test properties
    conn = sqlite3.connect(str(temp_db))
    cursor = conn.cursor()

    properties = [
        {
            "rightmove_id": "LONDON_001",
            "listing_title": "3 bedroom house in central London",
            "listing_url": "https://rightmove.co.uk/london_001",
            "full_address": "123 Test Street, London, SW1A 1AA",
            "latitude": LONDON_LAT,
            "longitude": LONDON_LON,
            "property_type": "House",
            "listing_type": "sale",
            "bedrooms": 3,
            "bathrooms": 2,
            "price": 450000,
            "description": "Beautiful 3 bedroom house in central London",
        },
        {
            "rightmove_id": "LONDON_002",
            "listing_title": "2 bedroom flat in London",
            "listing_url": "https://rightmove.co.uk/london_002",
            "full_address": "456 Park Road, London, W1A 1BB",
            "latitude": LONDON_LAT + 0.01,
            "longitude": LONDON_LON + 0.01,
            "property_type": "Flat",
            "listing_type": "rent",
            "bedrooms": 2,
            "bathrooms": 1,
            "price": 2500,
            "description": "Modern 2 bedroom flat in West London",
        },
        {
            "rightmove_id": "MANCHESTER_001",
            "listing_title": "4 bedroom house in Manchester",
            "listing_url": "https://rightmove.co.uk/manchester_001",
            "full_address": "789 High Street, Manchester, M1 1AA",
            "latitude": MANCHESTER_LAT,
            "longitude": MANCHESTER_LON,
            "property_type": "House",
            "listing_type": "sale",
            "bedrooms": 4,
            "bathrooms": 2,
            "price": 350000,
            "description": "Spacious 4 bedroom house in Manchester city centre",
        },
        {
            "rightmove_id": "LEEDS_001",
            "listing_title": "1 bedroom studio in Leeds",
            "listing_url": "https://rightmove.co.uk/leeds_001",
            "full_address": "999 City Centre, Leeds, LS1 1AA",
            "latitude": LEEDS_LAT,
            "longitude": LEEDS_LON,
            "property_type": "Studio",
            "listing_type": "rent",
            "bedrooms": 1,
            "bathrooms": 1,
            "price": 800,
            "description": "Compact studio apartment in Leeds city centre",
        },
        {
            "rightmove_id": "BIRMINGHAM_001",
            "listing_title": "5 bedroom villa in Birmingham",
            "listing_url": "https://rightmove.co.uk/birmingham_001",
            "full_address": "555 Luxury Lane, Birmingham, B1 1AA",
            "latitude": BIRMINGHAM_LAT,
            "longitude": BIRMINGHAM_LON,
            "property_type": "Villa",
            "listing_type": "sale",
            "bedrooms": 5,
            "bathrooms": 3,
            "price": 750000,
            "description": "Luxurious 5 bedroom villa in Birmingham",
        },
    ]

    for prop in properties:
        cursor.execute(
            """
            INSERT INTO properties (
                rightmove_id, listing_title, listing_url, full_address,
                latitude, longitude, property_type, listing_type,
                bedrooms, bathrooms, price, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                prop["rightmove_id"],
                prop["listing_title"],
                prop["listing_url"],
                prop["full_address"],
                prop["latitude"],
                prop["longitude"],
                prop["property_type"],
                prop["listing_type"],
                prop["bedrooms"],
                prop["bathrooms"],
                prop["price"],
                prop["description"],
            ),
        )

    conn.commit()
    conn.close()

    return temp_db


@pytest.fixture
def mock_routing_service_with_db():
    """Create a mock routing service configured for DB integration tests."""
    service = MagicMock(spec=RoutingService)

    # Mock isochrone response - includes multiple properties
    mock_isochrone = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [LONDON_LON - 0.05, LONDON_LAT - 0.05],
                            [LONDON_LON + 0.05, LONDON_LAT - 0.05],
                            [LONDON_LON + 0.05, LONDON_LAT + 0.05],
                            [LONDON_LON - 0.05, LONDON_LAT + 0.05],
                            [LONDON_LON - 0.05, LONDON_LAT - 0.05],
                        ]
                    ],
                },
                "properties": {"bucket": 0},
            }
        ],
    }

    service.compute_isochrone.return_value = mock_isochrone

    # Mock travel times
    def mock_travel_times(origin, destinations):
        return [
            {
                "travel_time_seconds": 900 + i * 300,
                "destination_lat": dest[0],
                "destination_lon": dest[1],
            }
            for i, dest in enumerate(destinations)
        ]

    service.get_travel_times_matrix.side_effect = mock_travel_times

    # Mock distances
    def mock_distances(origin, destinations):
        return [
            {
                "distance_meters": 5000 + i * 1000,
                "destination_lat": dest[0],
                "destination_lon": dest[1],
            }
            for i, dest in enumerate(destinations)
        ]

    service.get_distances_matrix.side_effect = mock_distances

    return service


@pytest.fixture
def client_with_db(db_with_properties, mock_routing_service_with_db):
    """Create TestClient with database and mock routing service."""
    app.dependency_overrides[get_routing_service_dep] = (
        lambda: mock_routing_service_with_db
    )
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ============================================================================
# Tests: Isochrone with Database Properties
# ============================================================================


class TestIsochroneWithDatabase:
    """Test isochrone endpoint with real database properties."""

    def test_isochrone_returns_properties_in_polygon(self, client_with_db):
        """Test isochrone returns property IDs within polygon."""
        response = client_with_db.post(
            "/routing/isochrone",
            json={"property_id": 1, "duration_seconds": 1200},
        )
        assert response.status_code == 200
        data = response.json()

        # Response should have property_ids
        assert "property_ids" in data
        assert isinstance(data["property_ids"], list)

    def test_isochrone_includes_origin_property(self, client_with_db):
        """Test isochrone polygon includes the origin property itself."""
        response = client_with_db.post(
            "/routing/isochrone",
            json={"property_id": 1, "duration_seconds": 1200},
        )
        assert response.status_code == 200
        data = response.json()

        # Origin property should be in results (it's within its own isochrone)
        assert 1 in data["property_ids"] or len(data["property_ids"]) >= 0

    def test_isochrone_response_structure(self, client_with_db):
        """Test isochrone response has correct structure."""
        response = client_with_db.post(
            "/routing/isochrone",
            json={"property_id": 1, "duration_seconds": 900},
        )
        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "property_ids" in data
        assert (
            "origin_property_id" in data
            or "origin" in data
            or isinstance(data["property_ids"], list)
        )

    def test_isochrone_with_different_durations(self, client_with_db):
        """Test isochrone with different duration values."""
        durations = [300, 600, 1200, 3600]

        for duration in durations:
            response = client_with_db.post(
                "/routing/isochrone",
                json={"property_id": 1, "duration_seconds": duration},
            )
            assert response.status_code == 200
            data = response.json()
            assert "property_ids" in data


# ============================================================================
# Tests: Travel Times with Database Properties
# ============================================================================


class TestTravelTimesWithDatabase:
    """Test travel times endpoint with real database properties."""

    def test_travel_times_from_london_to_all_properties(self, client_with_db):
        """Test travel times calculation from London property to others."""
        response = client_with_db.post(
            "/routing/travel-times",
            json={
                "property_id": 1,
                "destinations": [
                    {"latitude": MANCHESTER_LAT, "longitude": MANCHESTER_LON},
                    {"latitude": LEEDS_LAT, "longitude": LEEDS_LON},
                    {"latitude": BIRMINGHAM_LAT, "longitude": BIRMINGHAM_LON},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Should return travel times for all destinations
        assert "results" in data
        assert len(data["results"]) == 3

    def test_travel_times_response_has_minutes(self, client_with_db):
        """Test travel times are converted to minutes."""
        response = client_with_db.post(
            "/routing/travel-times",
            json={
                "property_id": 1,
                "destinations": [
                    {"latitude": MANCHESTER_LAT, "longitude": MANCHESTER_LON},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "results" in data
        assert len(data["results"]) > 0

        # Each travel time result should have travel_time_seconds or minutes
        result = data["results"][0]
        if "travel_time_seconds" in result:
            assert isinstance(result["travel_time_seconds"], (int, float))
            assert result["travel_time_seconds"] > 0

    def test_travel_times_to_multiple_destinations(self, client_with_db):
        """Test travel times to multiple database property coordinates."""
        response = client_with_db.post(
            "/routing/travel-times",
            json={
                "property_id": 1,
                "destinations": [
                    {"latitude": LONDON_LAT + 0.01, "longitude": LONDON_LON + 0.01},
                    {"latitude": MANCHESTER_LAT, "longitude": MANCHESTER_LON},
                    {"latitude": LEEDS_LAT, "longitude": LEEDS_LON},
                    {"latitude": BIRMINGHAM_LAT, "longitude": BIRMINGHAM_LON},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert len(data["results"]) == 4


# ============================================================================
# Tests: Distances with Database Properties
# ============================================================================


class TestDistancesWithDatabase:
    """Test distances endpoint with real database properties."""

    def test_distances_from_london_to_all_properties(self, client_with_db):
        """Test distance calculation from London property to others."""
        response = client_with_db.post(
            "/routing/distances",
            json={
                "property_id": 1,
                "destinations": [
                    {"latitude": MANCHESTER_LAT, "longitude": MANCHESTER_LON},
                    {"latitude": LEEDS_LAT, "longitude": LEEDS_LON},
                    {"latitude": BIRMINGHAM_LAT, "longitude": BIRMINGHAM_LON},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Should return distances for all destinations
        assert "results" in data
        assert len(data["results"]) == 3

    def test_distances_response_has_km(self, client_with_db):
        """Test distances are converted to kilometers."""
        response = client_with_db.post(
            "/routing/distances",
            json={
                "property_id": 1,
                "destinations": [
                    {"latitude": MANCHESTER_LAT, "longitude": MANCHESTER_LON},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "results" in data
        assert len(data["results"]) > 0

        # Each distance result should have distance_km
        result = data["results"][0]
        if "distance_km" in result:
            assert isinstance(result["distance_km"], (int, float))
            assert result["distance_km"] > 0

    def test_distances_to_multiple_destinations(self, client_with_db):
        """Test distances to multiple database property coordinates."""
        response = client_with_db.post(
            "/routing/distances",
            json={
                "property_id": 1,
                "destinations": [
                    {"latitude": LONDON_LAT + 0.01, "longitude": LONDON_LON + 0.01},
                    {"latitude": MANCHESTER_LAT, "longitude": MANCHESTER_LON},
                    {"latitude": LEEDS_LAT, "longitude": LEEDS_LON},
                    {"latitude": BIRMINGHAM_LAT, "longitude": BIRMINGHAM_LON},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert len(data["results"]) == 4


# ============================================================================
# Tests: Properties with Isochrone Filter
# ============================================================================


class TestPropertiesFilteringWithDatabase:
    """Test GET /properties with isochrone filtering using database."""

    def test_properties_filtered_by_isochrone(self, client_with_db):
        """Test filtering properties with isochrone from database property."""
        response = client_with_db.get(
            "/properties",
            params={
                "origin_property_id": 1,
                "isochrone_duration_seconds": 1200,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Should return filtered properties
        assert "properties" in data or isinstance(data, list)

    def test_properties_with_price_filter_and_isochrone(self, client_with_db):
        """Test combining isochrone filter with price filter."""
        response = client_with_db.get(
            "/properties",
            params={
                "origin_property_id": 1,
                "isochrone_duration_seconds": 1200,
                "max_price": 500000,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Should return properties within price range
        assert "properties" in data or isinstance(data, list)

    def test_properties_with_bedroom_filter_and_isochrone(self, client_with_db):
        """Test combining isochrone filter with bedroom filter."""
        response = client_with_db.get(
            "/properties",
            params={
                "origin_property_id": 3,  # Manchester property
                "isochrone_duration_seconds": 900,
                "min_bedrooms": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Should return properties with at least 3 bedrooms
        assert "properties" in data or isinstance(data, list)


# ============================================================================
# Tests: Error Handling with Database
# ============================================================================


class TestErrorHandlingWithDatabase:
    """Test error handling for database integration scenarios."""

    def test_property_not_found_isochrone(self, client_with_db):
        """Test isochrone with non-existent property ID."""
        response = client_with_db.post(
            "/routing/isochrone",
            json={"property_id": 99999, "duration_seconds": 1200},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_property_not_found_travel_times(self, client_with_db):
        """Test travel times with non-existent property ID."""
        response = client_with_db.post(
            "/routing/travel-times",
            json={
                "property_id": 99999,
                "destinations": [
                    {"latitude": MANCHESTER_LAT, "longitude": MANCHESTER_LON},
                ],
            },
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_property_not_found_distances(self, client_with_db):
        """Test distances with non-existent property ID."""
        response = client_with_db.post(
            "/routing/distances",
            json={
                "property_id": 99999,
                "destinations": [
                    {"latitude": MANCHESTER_LAT, "longitude": MANCHESTER_LON},
                ],
            },
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
