# Routing Service Documentation

## Overview

The routing service provides location-based search capabilities for the property rental finder backend. It calculates travel times, distances, and isochrone polygons (areas reachable within a given time duration) using `routingpy`.

## Architecture

```
backend/services/
├── __init__.py                 # Service exports
└── routing_service.py          # Core routing logic (250 LOC)

Integration points:
- backend/config.py            # Configuration for routing providers
- backend/app/schemas.py       # Pydantic models for requests/responses
- backend/app/crud.py          # Database queries with isochrone support
- backend/app/main.py          # API endpoints
```

## Features

### 1. **Isochrone Computation**
Find all areas reachable from a location within a specified time duration.

```python
# Compute isochrone polygon
polygon = routing_service.compute_isochrone(
    lat=51.5074,
    lon=-0.1278,
    duration_seconds=1200  # 20 minutes
)
# Returns GeoJSON polygon of reachable areas
```

### 2. **Travel Time Calculation**
Calculate travel times from a location to multiple destinations.

```python
# Calculate travel times
results = routing_service.get_travel_times_matrix(
    origin=(51.5074, -0.1278),
    destinations=[
        (51.5190, -0.1405),  # Work
        (51.5268, -0.1055),  # School
    ]
)
# Returns [
#   {"destination_lat": 51.5190, "destination_lon": -0.1405, "travel_time_seconds": 900},
#   {"destination_lat": 51.5268, "destination_lon": -0.1055, "travel_time_seconds": 1200},
# ]
```

### 3. **Distance Calculation**
Calculate distances from a location to multiple destinations.

```python
# Calculate distances
results = routing_service.get_distances_matrix(
    origin=(51.5074, -0.1278),
    destinations=[
        (51.5190, -0.1405),
        (51.5268, -0.1055),
    ]
)
# Returns [
#   {"destination_lat": 51.5190, "destination_lon": -0.1405, "distance_meters": 2500},
#   {"destination_lat": 51.5268, "destination_lon": -0.1055, "distance_meters": 3000},
# ]
```

### 4. **Point-in-Polygon Queries**
Find which properties fall within an isochrone polygon.

```python
# Find properties inside isochrone
property_ids = properties_in_polygon(
    polygon=isochrone_geojson,
    properties=[
        {"id": 1, "latitude": 51.5074, "longitude": -0.1278},
        {"id": 2, "latitude": 51.5190, "longitude": -0.1405},
    ]
)
# Returns [1, 2] (properties inside polygon)
```

## API Endpoints

### 1. POST `/routing/isochrone`

Find all properties reachable from a property within a time duration.

**Request:**
```json
{
  "property_id": 123,
  "duration_seconds": 1200
}
```

**Response:**
```json
{
  "property_ids": [1, 2, 5, 7],
  "property_count": 4,
  "center_lat": 51.5074,
  "center_lon": -0.1278
}
```

**Error Cases:**
- `404`: Property not found
- `400`: Invalid coordinates or duration outside range (60-3600 seconds)
- `503`: Routing service unavailable

### 2. POST `/routing/travel-times`

Calculate travel times from a property to multiple destinations.

**Request:**
```json
{
  "property_id": 123,
  "destinations": [
    {
      "latitude": 51.5190,
      "longitude": -0.1405,
      "label": "Work"
    },
    {
      "latitude": 51.5268,
      "longitude": -0.1055,
      "label": "School"
    }
  ]
}
```

**Response:**
```json
{
  "property_id": 123,
  "origin_lat": 51.5074,
  "origin_lon": -0.1278,
  "results": [
    {
      "destination": {
        "latitude": 51.5190,
        "longitude": -0.1405,
        "label": "Work"
      },
      "travel_time_seconds": 900,
      "travel_time_minutes": 15.0
    },
    {
      "destination": {
        "latitude": 51.5268,
        "longitude": -0.1055,
        "label": "School"
      },
      "travel_time_seconds": 1200,
      "travel_time_minutes": 20.0
    }
  ]
}
```

**Limits:**
- Maximum 25 destinations per request
- Coordinates must be within UK bounds

### 3. POST `/routing/distances`

Calculate distances from a property to multiple destinations.

**Request:**
```json
{
  "property_id": 123,
  "destinations": [
    {
      "latitude": 51.5190,
      "longitude": -0.1405,
      "label": "Work"
    }
  ]
}
```

**Response:**
```json
{
  "property_id": 123,
  "origin_lat": 51.5074,
  "origin_lon": -0.1278,
  "results": [
    {
      "destination": {
        "latitude": 51.5190,
        "longitude": -0.1405,
        "label": "Work"
      },
      "distance_meters": 2500,
      "distance_km": 2.5
    }
  ]
}
```

### 4. Enhanced GET `/properties` with Isochrone Filter

List properties with optional isochrone-based filtering combined with existing filters.

**Query Parameters:**
```
?isochrone_center_property_id=123&isochrone_duration_seconds=1200&min_price=500000&bedrooms=3
```

**How it works:**
1. Computes isochrone from property 123 (20 minutes radius)
2. Finds all properties inside that isochrone
3. Applies additional filters (price ≥ 500000, bedrooms ≥ 3)
4. Returns filtered results scored by rating

**Response:**
```json
{
  "properties": [
    {
      "id": 1,
      "price": 550000,
      "bedrooms": 3,
      "score": 2.5,
      ...
    }
  ],
  "total_count": 1,
  "limit": 10,
  "offset": 0
}
```

## Configuration

### Environment Variables

```bash
# Routing Provider (graphhopper is default, mapbox alternative)
ROUTING_PROVIDER=graphhopper

# GraphHopper API Key (REQUIRED for graphhopper provider)
ROUTING_API_KEY=<your-graphhopper-api-key>

# GraphHopper Base URL (default is cloud API)
GRAPHHOPPER_BASE_URL=https://graphhopper.com/api/1

# Request timeout in seconds
ROUTING_TIMEOUT_SECONDS=30
```

### Providers Supported

#### GraphHopper (Default)
- **Setup**: Free API key from https://www.graphhopper.com/dashboard/sign-up
- **URL**: Default `https://graphhopper.com/api/1` (cloud API)
- **Cost**: Free tier (~1,000 requests/day), paid plans available
- **Data**: OpenStreetMap + proprietary
- **Self-Hosting**: Optional for unlimited requests

```bash
# Example .env for cloud API
ROUTING_API_KEY=<your-api-key>
ROUTING_PROVIDER=graphhopper
```

#### Mapbox
- **Setup**: Requires API key from mapbox.com
- **Cost**: Paid (with free tier)
- **Accuracy**: High
- **Configure**: Set ROUTING_PROVIDER=mapbox and ROUTING_API_KEY

#### OSRM (Deprecated)
- **Status**: No longer supported
- **Migration**: Use GraphHopper instead (see QUICKSTART.md)

## Data Validation

### Coordinate Bounds (UK Only)
The service validates all coordinates are within UK geographic bounds:
- **North**: 60.86° (Scottish Islands)
- **South**: 49.86° (English coast)
- **East**: 1.68° (East Anglia)
- **West**: -8.65° (Northern Ireland)

Invalid coordinates raise `ValueError`.

### Duration Validation
Isochrone durations must be:
- **Minimum**: 60 seconds (1 minute)
- **Maximum**: 3600 seconds (60 minutes)

### Destination Limits
- **Maximum destinations per request**: 25
- Exceeding this raises `ValueError`

## Error Handling

### HTTP Status Codes

| Code | Scenario | Example |
|------|----------|---------|
| 400 | Invalid input (coordinates, duration, too many destinations) | "Latitude 100 outside UK bounds" |
| 404 | Property not found | "Property not found" |
| 503 | Routing service unavailable | "Routing service unavailable" |
| 500 | Internal server error | Generic catch-all |

### Logging

All operations are logged at INFO/DEBUG levels:
```
INFO: Computing isochrone for (51.5074, -0.1278) with duration 1200s
DEBUG: Isochrone computed successfully: <type 'GeoJSON'>
INFO: Found 42 properties inside polygon (checked 500 total)
DEBUG: Travel times computed: 2 results
```

Enable debug logging to see detailed request/response information:
```python
import logging
logging.getLogger("backend.services.routing_service").setLevel(logging.DEBUG)
```

## Database Integration

### New CRUD Functions

#### `get_all_properties_with_coordinates()`
Returns all properties with their coordinates for point-in-polygon queries.

```python
properties = crud.get_all_properties_with_coordinates()
# Returns [{id: 1, latitude: 51.5074, longitude: -0.1278}, ...]
```

#### `get_properties_with_isochrone_and_filters()`
Combines isochrone results with existing filters.

```python
results, total = crud.get_properties_with_isochrone_and_filters(
    isochrone_property_ids=[1, 2, 5],
    filters=PropertyFilters(min_price=500000, min_bedrooms=3),
    limit=10,
    offset=0
)
```

### Filter Composition

The isochrone filter integrates seamlessly with existing filters:

```
Isochrone Results (e.g., 42 properties)
        ↓
+ Price Filter (min_price=500000, max_price=1000000)
        ↓
+ Bedrooms Filter (min_bedrooms=2, max_bedrooms=4)
        ↓
+ Property Type Filter (property_type="House")
        ↓
+ Score Filter (min_score=1.0)
        ↓
Final Sorted Results (by rating score)
```

All filters are applied as AND operations (property must match ALL filters).

## Usage Examples

### Example 1: Find Properties with 15-Minute Commute

**Frontend Request:**
```javascript
const response = await fetch('/routing/isochrone', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    property_id: 123,  // Work location
    duration_seconds: 900  // 15 minutes
  })
});

const isochrone = await response.json();
console.log(`Found ${isochrone.property_count} properties within 15 minutes`);
```

### Example 2: Filter Properties by Isochrone + Price + Bedrooms

**Frontend Request:**
```javascript
const response = await fetch(
  '/properties?isochrone_center_property_id=123&isochrone_duration_seconds=1200&min_price=500000&min_bedrooms=3',
  { method: 'GET' }
);

const results = await response.json();
console.log(`Found ${results.total_count} properties matching criteria`);
```

### Example 3: Get Travel Times to Multiple Locations

**Frontend Request:**
```javascript
const response = await fetch('/routing/travel-times', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    property_id: 123,
    destinations: [
      { latitude: 51.5190, longitude: -0.1405, label: "Work" },
      { latitude: 51.5268, longitude: -0.1055, label: "School" },
      { latitude: 51.5033, longitude: -0.1195, label: "Gym" }
    ]
  })
});

const times = await response.json();
times.results.forEach(r => {
  console.log(`${r.destination.label}: ${r.travel_time_minutes.toFixed(1)} minutes`);
});
// Output:
// Work: 15.0 minutes
// School: 20.0 minutes
// Gym: 8.0 minutes
```

## Performance Considerations

### Caching Opportunities
The implementation currently makes fresh API calls for each request. For production, consider:

1. **Isochrone Caching**: Cache isochrone polygons for 24-48 hours
   - Key: `isochrone:{lat}:{lon}:{duration}`
   - Significant speedup since isochrones rarely change

2. **Travel Time Caching**: Cache routes for 24 hours
   - Key: `route:{from_lat}:{from_lon}:{to_lat}:{to_lon}`
   - Many users likely have similar commute patterns

3. **Property Coordinate Indexing**: Already indexed on `(latitude, longitude)`
   - Point-in-polygon queries are efficient

### Optimization Tips

- Use isochrone filtering before applying other expensive filters
- Batch similar requests (combine multiple travel times into one request)
- Set appropriate timeout values based on your OSRM server performance

## Troubleshooting

### "Routing service unavailable" (503)

**Causes:**
- OSRM server not running
- Network connectivity issue
- Routing API timeout exceeded

**Solutions:**
1. Check if OSRM is running: `curl http://localhost:5000/status`
2. Increase timeout: `ROUTING_TIMEOUT_SECONDS=60`
3. Check firewall rules for port 5000

### "Invalid coordinates" (400)

**Cause**: Coordinates outside UK bounds

**Solution**: Verify coordinates are within:
- Latitude: 49.86° to 60.86°
- Longitude: -8.65° to 1.68°

### Properties not in isochrone results

**Causes:**
- Properties missing coordinates in database
- Coordinates are on the edge of isochrone polygon
- Routing service computing conservative polygon

**Solutions:**
1. Check property coordinates: `GET /properties/{id}`
2. Increase duration slightly to test polygon boundaries
3. Review OSRM isochrone accuracy with test cases

## Dependencies

- `routingpy>=1.3.0` - Routing API abstraction
- `shapely>=2.1.2` - Geometry operations (point-in-polygon)
- `fastapi` - Already installed
- Python 3.12+

All dependencies are already in `pyproject.toml`.

## Testing

The routing service has comprehensive test coverage with **61 tests** across two test suites:

### Test Files

1. **`backend/tests/test_routing_endpoints.py`** (45 tests)
   - Unit tests for routing endpoints using mocks
   - Validation tests for coordinates and durations
   - Response structure validation
   - Dependency injection testing

2. **`backend/tests/test_routing_db_integration.py`** (16 tests)
   - Database integration tests with real properties
   - End-to-end testing with sample UK properties
   - Response structure validation with actual data

### Running Tests

**All routing tests:**
```bash
pytest backend/tests/test_routing_endpoints.py backend/tests/test_routing_db_integration.py -v
```

**Only unit tests (with mocks):**
```bash
pytest backend/tests/test_routing_endpoints.py -v
```

**Only integration tests (with database):**
```bash
pytest backend/tests/test_routing_db_integration.py -v
```

**Specific test class:**
```bash
pytest backend/tests/test_routing_endpoints.py::TestIsochroneEndpoint -v
```

**Specific test:**
```bash
pytest backend/tests/test_routing_endpoints.py::TestIsochroneEndpoint::test_isochrone_valid_request -v
```

**With coverage report:**
```bash
pytest backend/tests/test_routing_endpoints.py --cov=backend.services.routing_service --cov-report=html
```

### Test Coverage Summary

#### Unit Tests (test_routing_endpoints.py)

**TestIsochroneEndpoint** (7 tests)
- Valid isochrone requests
- Duration validation (too short, too long, default)
- Missing parameters
- Malformed JSON

**TestTravelTimesEndpoint** (8 tests)
- Valid travel time calculations
- Multiple destinations (1-25)
- Destination limits
- Response structure validation

**TestDistancesEndpoint** (8 tests)
- Valid distance calculations
- Multiple destinations (1-25)
- Destination limits
- Response structure validation

**TestRoutingErrorHandling** (3 tests)
- Property not found errors (404)

**TestRoutingCoordinateValidation** (6 tests)
- UK bounds checking (north, south, east, west)
- Valid coordinates (London, Manchester)

**TestRoutingDurationValidation** (5 tests)
- Minimum duration (60 seconds)
- Maximum duration (3600 seconds)
- Typical durations (300s, 600s, 1200s, etc.)

**TestPropertiesWithIsochrone** (4 tests)
- GET /properties without isochrone
- GET /properties with isochrone filtering
- Combined with other filters (bedrooms, price)

**TestRoutingServiceUnit** (2 tests)
- Service initialization
- Singleton pattern removal verification

**TestDependencyInjection** (2 tests)
- FastAPI dependency override mechanism
- Endpoint uses injected dependency

#### Database Integration Tests (test_routing_db_integration.py)

**TestIsochroneWithDatabase** (4 tests)
- Isochrone with real database properties
- Response structure validation with actual data
- Different duration values

**TestTravelTimesWithDatabase** (3 tests)
- Travel times from London to other UK cities
- Response structure validation
- Multiple destination calculations

**TestDistancesWithDatabase** (3 tests)
- Distance calculations across UK cities
- Response structure validation
- Multiple destination calculations

**TestPropertiesFilteringWithDatabase** (3 tests)
- GET /properties with isochrone filtering
- Combined filters (isochrone + price, isochrone + bedrooms)

**TestErrorHandlingWithDatabase** (3 tests)
- Error handling with real database
- Property not found errors

### Test Data

The integration tests use real UK property data:
- **London**: 51.5074°N, -0.1278°W
- **Manchester**: 53.4808°N, -2.2426°W
- **Leeds**: 53.8008°N, -1.5491°W
- **Birmingham**: 52.5085°N, -1.8845°W

### Mocking Strategy

Unit tests use mocked `RoutingService` with:
- Real validation methods (coordinates, duration)
- Configurable mock responses
- Side effects for testing error conditions

Database integration tests use:
- In-memory SQLite database
- Sample properties with realistic data
- Actual response structures

Example mock configuration:
```python
@pytest.fixture
def mock_routing_service():
    """Mock routing service with real validation."""
    service = MagicMock(spec=RoutingService)
    
    # Real validation
    service._validate_coordinates = validate_coordinates
    service._validate_duration = validate_duration
    
    # Mock responses
    service.compute_isochrone.return_value = mock_isochrone_geojson
    service.get_travel_times_matrix.side_effect = mock_travel_times
    
    return service
```

### Test Assertions

Tests validate:
- ✅ HTTP status codes (200, 400, 404, 503)
- ✅ Response structure (required fields, types)
- ✅ Coordinate validation (UK bounds)
- ✅ Duration validation (60-3600 seconds)
- ✅ Data conversions (seconds→minutes, meters→km)
- ✅ Error handling and messages
- ✅ Dependency injection mechanism
- ✅ Database property retrieval

### CI/CD Integration

To run tests in CI/CD pipeline:

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Run all tests with coverage
pytest backend/tests/test_routing*.py --cov=backend --cov-report=xml

# Generate HTML coverage report
pytest backend/tests/test_routing*.py --cov=backend --cov-report=html
```

## Future Enhancements

1. **Public Transit Support**: Add support for routing via bus/train
2. **Alternative Routes**: Return multiple route options with trade-offs
3. **Isochrone Caching**: Cache computed isochrones for performance
4. **Turn Restrictions**: Consider traffic patterns and turn limitations
5. **Multi-Modal Routing**: Combine car + public transit routes
6. **Accessible Routes**: Filter routes for accessibility requirements

## Related Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [routingpy Documentation](https://github.com/gis-ops/routing-py)
- [Shapely Documentation](https://shapely.readthedocs.io/)
- [OSRM API Reference](http://project-osrm.org/docs/v5.5.1/api/overview)
- [GeoJSON Specification](https://tools.ietf.org/html/rfc7946)
