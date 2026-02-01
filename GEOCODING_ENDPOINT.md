# Geocoding Endpoint Documentation

## Overview

The geocoding endpoint (`/routing/geocode`) converts any address string to latitude and longitude coordinates. It accepts multiple address formats and uses OpenStreetMap's Nominatim service for free, reliable geocoding.

## Endpoint Details

### Request

**Method:** `POST`

**URL:** `http://localhost:8000/routing/geocode`

**Content-Type:** `application/json`

### Request Body

```json
{
  "address": "string"
}
```

| Parameter | Type   | Required | Description                                                                                      |
|-----------|--------|----------|--------------------------------------------------------------------------------------------------|
| `address` | string | Yes      | Any address format: street addresses, postcodes, place names, or partial addresses              |

### Response

**Status:** `200 OK`

```json
{
  "latitude": 51.5034878,
  "longitude": -0.1276965,
  "address": "10 Downing Street, London"
}
```

| Field       | Type   | Description                              |
|-------------|--------|------------------------------------------|
| `latitude`  | number | Latitude coordinate of the address       |
| `longitude` | number | Longitude coordinate of the address      |
| `address`   | string | Echo of the input address                |

### Error Responses

#### 400 Bad Request
**Reason:** Empty or invalid address provided

```json
{
  "detail": "Address cannot be empty"
}
```

#### 404 Not Found
**Reason:** Address could not be geocoded

```json
{
  "detail": "Could not geocode address: 'xyzabc123invalidaddresszzz'"
}
```

#### 503 Service Unavailable
**Reason:** Geocoding service is temporarily unavailable

```json
{
  "detail": "Geocoding service unavailable"
}
```

## Supported Address Formats

The endpoint accepts various address formats:

### Full Street Address
```bash
curl -X POST http://localhost:8000/routing/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "10 Downing Street, London, UK"}'
```

**Response:**
```json
{
  "latitude": 51.5034878,
  "longitude": -0.1276965,
  "address": "10 Downing Street, London, UK"
}
```

### UK Postcode
```bash
curl -X POST http://localhost:8000/routing/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "SW1A 1AA"}'
```

**Response:**
```json
{
  "latitude": 51.5013374,
  "longitude": -0.1417955,
  "address": "SW1A 1AA"
}
```

### Place Name
```bash
curl -X POST http://localhost:8000/routing/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "Tower Bridge, London"}'
```

**Response:**
```json
{
  "latitude": 51.5055158,
  "longitude": -0.0753665,
  "address": "Tower Bridge, London"
}
```

### Partial Address
```bash
curl -X POST http://localhost:8000/routing/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "Oxford Street, London"}'
```

**Response:**
```json
{
  "latitude": 51.5159,
  "longitude": -0.1357,
  "address": "Oxford Street, London"
}
```

## Implementation Details

### Technology Stack
- **Geocoding Provider:** OpenStreetMap Nominatim (free, no API key required)
- **Client Library:** Geopy 2.4.1
- **Framework:** FastAPI
- **Language:** Python 3.12+

### Features
- ✅ **No authentication required** - Uses free OpenStreetMap Nominatim service
- ✅ **Supports multiple address formats** - Street addresses, postcodes, landmarks, place names
- ✅ **Lenient matching** - Returns best match even if address is ambiguous
- ✅ **Fast response times** - Typical response < 500ms
- ✅ **Fully integrated** - Works seamlessly with existing routing endpoints

### Rate Limiting
Nominatim has a rate limit of 1 request per second for each client. The service includes appropriate throttling to respect this limit.

### Accuracy
- **Urban areas:** High accuracy (within 10-50 meters typically)
- **Rural areas:** Moderate accuracy (within 100-500 meters)
- **International addresses:** Supported but may be less accurate than UK addresses

## Error Handling

The endpoint uses a **lenient approach** to geocoding:
- If an address matches multiple locations, returns the **best/first match**
- Returns `404` only if no matches are found
- Returns `400` for malformed/empty requests
- Returns `503` for service failures

## Integration Examples

### Python (Requests)
```python
import requests

response = requests.post(
    "http://localhost:8000/routing/geocode",
    json={"address": "10 Downing Street, London"}
)
data = response.json()
print(f"Latitude: {data['latitude']}, Longitude: {data['longitude']}")
```

### JavaScript (Fetch API)
```javascript
const response = await fetch('http://localhost:8000/routing/geocode', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ address: '10 Downing Street, London' })
});
const data = await response.json();
console.log(`Latitude: ${data.latitude}, Longitude: ${data.longitude}`);
```

### cURL
```bash
curl -X POST http://localhost:8000/routing/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "10 Downing Street, London"}'
```

## Service Dependencies

The geocoding service is initialized during application startup via the FastAPI lifespan manager. It's available in all request handlers through dependency injection:

```python
from backend.services.geocoding_service import GeocodingService

@app.post("/routing/geocode")
async def geocode_address(
    request: GeocodeRequest,
    geocoding_service: GeocodingService = Depends(get_geocoding_service_dep)
):
    coordinates = geocoding_service.geocode_address(request.address)
    # ...
```

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_geocoding_endpoint.py -v
```

Or test manually:

```bash
# Valid address
curl -X POST http://localhost:8000/routing/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "Tower Bridge, London"}'

# Empty address (should fail)
curl -X POST http://localhost:8000/routing/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": ""}'

# Unknown address (should fail)
curl -X POST http://localhost:8000/routing/geocode \
  -H "Content-Type: application/json" \
  -d '{"address": "xyzabc123invalidaddresszzz"}'
```

## API Limits

- **Maximum address length:** No strict limit, but keep addresses reasonable (< 1000 characters)
- **Rate limit:** 1 request/second (Nominatim limit)
- **Response timeout:** 10 seconds per request
- **Supported regions:** Worldwide (optimized for UK addresses)

## Troubleshooting

### Address not found
- Try a simpler address (e.g., just city name or postcode)
- Verify the address spelling
- Use a more standard address format

### Incorrect coordinates
- The endpoint returns the best match; if ambiguous, try a more specific address
- Check if coordinates are within expected bounds

### Service unavailable (503)
- Check internet connectivity
- Nominatim may be temporarily rate-limited; wait and retry
- Check application logs for detailed error messages

## Related Endpoints

- `POST /routing/isochrone` - Find properties within travel time
- `POST /routing/travel-times` - Calculate travel times to destinations
- `POST /routing/distances` - Calculate distances to destinations

## See Also

- [OpenStreetMap Nominatim Documentation](https://nominatim.org/)
- [Geopy Documentation](https://geopy.readthedocs.io/)
- [Property Rental Finder API Documentation](./README.md)
