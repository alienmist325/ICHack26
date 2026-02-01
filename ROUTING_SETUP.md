# Routing Service Setup Guide

## Quick Start

### 1. Install Dependencies with uv

The routing service dependencies (`routingpy` and `shapely`) are already in `pyproject.toml`. Install them:

```bash
cd /path/to/ic-hack-2026
uv sync
```

This will install all dependencies including:
- `routingpy>=1.3.0` - For routing calculations
- `shapely>=2.1.2` - For point-in-polygon queries

### 2. Configure OSRM (Recommended for Development)

The default configuration uses OSRM (OpenStreetMap Routing Machine) which is free and open-source.

#### Option A: Local OSRM with Docker (Recommended)

```bash
# Pull and run OSRM container
docker run -d -p 5000:5000 --name osrm \
  osrm/osrm-backend \
  osrm_routed /data/great-britain-latest.osrm

# Verify it's running
curl http://localhost:5000/status
# Should return: {"status":0,"message":"Ok"}
```

#### Option B: Install OSRM Locally

See [OSRM Installation Guide](http://project-osrm.org/docs/v5.5.1/building-from-source/)

### 3. Configure Environment Variables

Create or update `.env` file in the project root:

```bash
# Apify API key (required for scraping)
APIFY_API_KEY=<your-apify-key>

# Routing Service Configuration
ROUTING_PROVIDER=osrm
OSRM_BASE_URL=http://localhost:5000
ROUTING_TIMEOUT_SECONDS=30
```

### 4. Run the Backend

```bash
cd backend
uv run fastapi dev app/main.py
```

The API will be available at `http://localhost:8000`

### 5. Test the Routing Service

#### Test Isochrone Endpoint

```bash
curl -X POST http://localhost:8000/routing/isochrone \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": 1,
    "duration_seconds": 1200
  }'
```

#### Test Travel Times

```bash
curl -X POST http://localhost:8000/routing/travel-times \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": 1,
    "destinations": [
      {"latitude": 51.5190, "longitude": -0.1405, "label": "Work"},
      {"latitude": 51.5268, "longitude": -0.1055, "label": "School"}
    ]
  }'
```

#### Test Distances

```bash
curl -X POST http://localhost:8000/routing/distances \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": 1,
    "destinations": [
      {"latitude": 51.5190, "longitude": -0.1405, "label": "Work"}
    ]
  }'
```

#### Test Isochrone-based Property Search

```bash
curl "http://localhost:8000/properties?isochrone_center_property_id=1&isochrone_duration_seconds=1200&min_price=500000&min_bedrooms=2"
```

## Project Structure

```
backend/
├── services/
│   ├── __init__.py                    # Service module exports
│   └── routing_service.py             # Routing logic (250 LOC)
│
├── app/
│   ├── main.py                        # FastAPI app + 3 new endpoints
│   ├── schemas.py                     # 9 new Pydantic models for routing
│   ├── crud.py                        # 3 new database query functions
│   ├── database.py                    # SQLite schema
│   └── models.py
│
├── config.py                          # Routing configuration + UK bounds
└── scraper/
```

## Key Components

### 1. RoutingService Class (`backend/services/routing_service.py`)

High-level service for routing operations:

```python
from backend.services.routing_service import RoutingService

service = RoutingService()

# Compute isochrone
polygon = service.compute_isochrone(51.5074, -0.1278, 1200)

# Get travel times
times = service.get_travel_times_matrix(
    (51.5074, -0.1278),
    [(51.5190, -0.1405), (51.5268, -0.1055)]
)

# Get distances
distances = service.get_distances_matrix(
    (51.5074, -0.1278),
    [(51.5190, -0.1405)]
)
```

### 2. Routing Schemas (`backend/app/schemas.py`)

Nine new Pydantic models:
- `LocationCoordinate` - Geographic point with optional label
- `IsochroneRequest` / `IsochroneResponse`
- `TravelTimeRequest` / `TravelTimeResponse` / `TravelTimeResult`
- `DistanceRequest` / `DistanceResponse` / `DistanceResult`

### 3. Enhanced PropertyFilters

Extended with isochrone parameters:
```python
filters = PropertyFilters(
    isochrone_center_lat=51.5074,
    isochrone_center_lon=-0.1278,
    isochrone_duration_seconds=1200,
    min_price=500000,
    min_bedrooms=3
)
```

### 4. CRUD Functions (`backend/app/crud.py`)

Three new functions:
- `get_properties_by_ids()` - Get multiple properties by ID list
- `get_all_properties_with_coordinates()` - For point-in-polygon queries
- `get_properties_with_isochrone_and_filters()` - Combine isochrone + other filters

## Configuration Reference

### ROUTING_PROVIDER
- `"osrm"` (default) - OpenStreetMap Routing Machine
- `"mapbox"` - Mapbox API

### OSRM_BASE_URL
- Default: `http://localhost:5000`
- Change if running OSRM on different port/host

### ROUTING_TIMEOUT_SECONDS
- Default: 30 seconds
- Increase if OSRM responses are slow
- Decrease for faster failures

### UK_BOUNDS (in config.py)
```python
UK_BOUNDS = {
    "north": 60.86,   # Scottish Islands
    "south": 49.86,   # English coast
    "east": 1.68,     # East Anglia
    "west": -8.65,    # Northern Ireland
}
```

All coordinates are validated against these bounds.

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/routing/isochrone` | Find properties within travel time |
| POST | `/routing/travel-times` | Calculate travel times to destinations |
| POST | `/routing/distances` | Calculate distances to destinations |
| GET | `/properties` | Enhanced with `isochrone_center_property_id` param |

## Error Handling

### Common Errors and Solutions

**"Routing service unavailable" (503)**
- Check if OSRM is running: `curl http://localhost:5000/status`
- Check network connectivity
- Increase timeout in `.env`

**"Invalid coordinates" (400)**
- Verify coordinates are within UK bounds
- Latitude: 49.86° to 60.86°
- Longitude: -8.65° to 1.68°

**"Property not found" (404)**
- Ensure property exists in database
- Check property_id is correct

**"Too many destinations" (400)**
- Maximum 25 destinations per request
- Split into multiple requests if needed

## Testing

### Manual Testing with curl

1. **List properties (basic)**
   ```bash
   curl http://localhost:8000/properties?limit=5
   ```

2. **Get isochrone**
   ```bash
   curl -X POST http://localhost:8000/routing/isochrone \
     -H "Content-Type: application/json" \
     -d '{"property_id": 1, "duration_seconds": 600}'
   ```

3. **Travel times with 3 destinations**
   ```bash
   curl -X POST http://localhost:8000/routing/travel-times \
     -H "Content-Type: application/json" \
     -d '{
       "property_id": 1,
       "destinations": [
         {"latitude": 51.5074, "longitude": -0.1278},
         {"latitude": 51.5190, "longitude": -0.1405},
         {"latitude": 51.5268, "longitude": -0.1055}
       ]
     }'
   ```

4. **Enhanced property search with isochrone**
   ```bash
   curl "http://localhost:8000/properties?isochrone_center_property_id=1&isochrone_duration_seconds=1200&min_bedrooms=2&limit=10"
   ```

### Using Python

```python
import requests

# Isochrone
response = requests.post(
    'http://localhost:8000/routing/isochrone',
    json={'property_id': 1, 'duration_seconds': 1200}
)
print(response.json())

# Travel times
response = requests.post(
    'http://localhost:8000/routing/travel-times',
    json={
        'property_id': 1,
        'destinations': [
            {'latitude': 51.5190, 'longitude': -0.1405, 'label': 'Work'},
            {'latitude': 51.5268, 'longitude': -0.1055, 'label': 'School'}
        ]
    }
)
print(response.json())
```

## Dependencies Installed

Via `uv sync`:
- `routingpy>=1.3.0` - Routing API wrapper
- `shapely>=2.1.2` - Geometry operations
- `fastapi[standard]>=0.128.0` - Web framework
- `pydantic>=2.12.5` - Data validation
- All other existing dependencies

## Documentation

- **Main**: `ROUTING_SERVICE.md` - Full feature documentation
- **Setup**: This file
- **Code**: Extensive docstrings in Python files

## Next Steps

1. ✅ Install dependencies with `uv sync`
2. ✅ Start OSRM server (Docker or local)
3. ✅ Configure `.env` file
4. ✅ Run backend with `uv run fastapi dev`
5. ✅ Test endpoints with curl or Python
6. 📋 Integrate with frontend
7. 📋 Deploy to production

## Support

For issues or questions:
1. Check `ROUTING_SERVICE.md` for detailed documentation
2. Review error messages and troubleshooting section
3. Check logs with `debug` level enabled
4. Verify OSRM server is running and accessible
