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

### 2. Get a GraphHopper API Key

The default configuration uses GraphHopper which provides cloud-based routing with a generous free tier.

#### Option A: Cloud API (Recommended - No Setup Required)

1. Sign up for free at: https://www.graphhopper.com/dashboard/sign-up
2. Go to your dashboard and create a new API key
3. The free tier includes ~1,000 requests per day
4. Add the API key to your `.env` file (see below)

#### Option B: Self-Hosted GraphHopper (Advanced)

For unlimited requests or private data:
1. Follow the [GraphHopper Installation Guide](https://www.graphhopper.com/blog/2017/09/29/installation-guide-routing-engine/)
2. Update `GRAPHHOPPER_BASE_URL` in `.env` to your server URL
3. Generate your own API key if required by your installation

### 3. Configure Environment Variables

Create or update `.env` file in the project root:

```bash
# Apify API key (required for scraping)
APIFY_API_KEY=<your-apify-key>

# Routing Service Configuration - GraphHopper
ROUTING_PROVIDER=graphhopper
ROUTING_API_KEY=<your-graphhopper-api-key>
GRAPHHOPPER_BASE_URL=https://graphhopper.com/api/1
ROUTING_TIMEOUT_SECONDS=30
```

**Important**: `ROUTING_API_KEY` is required for GraphHopper. Without it, the service will raise a helpful error directing you to get a free key.

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
- `"graphhopper"` (default) - GraphHopper cloud API
- `"mapbox"` - Mapbox API (alternative)

### ROUTING_API_KEY
- **Required** for GraphHopper and Mapbox
- Get free key at: https://www.graphhopper.com/dashboard/sign-up
- Free tier: ~1,000 requests per day

### GRAPHHOPPER_BASE_URL
- Default: `https://graphhopper.com/api/1`
- For self-hosted: Use your server URL
- Change if running GraphHopper on different host

### ROUTING_TIMEOUT_SECONDS
- Default: 30 seconds
- Increase if API responses are slow
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

**"ROUTING_API_KEY environment variable is required for GraphHopper provider" (400)**
- Sign up at: https://www.graphhopper.com/dashboard/sign-up
- Create an API key in your dashboard
- Add to `.env`: `ROUTING_API_KEY=<your-key>`
- Restart the application

**"Cannot connect to GraphHopper API" (503)**
- Check internet connection
- Verify ROUTING_API_KEY is valid
- Check API key hasn't exceeded rate limits (1,000/day on free tier)
- Check GraphHopper status at: https://status.graphhopper.com/

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
4. Verify GraphHopper API key is valid at: https://www.graphhopper.com/dashboard/
5. For GraphHopper issues, see: https://docs.graphhopper.com/
