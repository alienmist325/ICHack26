# Rightmove Scraper API Documentation

## Overview

The backend provides a complete integration between the Rightmove scraper (via Apify) and a property database. This document describes the scraping endpoint and how properties are stored and retrieved.

## Architecture

```
FastAPI Backend
    ↓
POST /api/scrape (accepts RightmoveScraperInput)
    ↓
scrape_rightmove() async function
    ├─ Initializes Apify client
    ├─ Calls dhrumil/rightmove-scraper actor
    ├─ Returns RightmoveResponse with properties
    └─ Properties are parsed into RightmoveProperty objects
    ↓
rightmove_property_to_create() conversion
    ├─ Maps Rightmove API fields to PropertyCreate schema
    ├─ Extracts coordinates (lat/lon)
    ├─ Converts timestamps to ISO format
    └─ Preserves agent information
    ↓
upsert_property() database operation
    ├─ Checks if property already exists by rightmove_id
    ├─ Creates new property if not found
    ├─ Updates existing property with new data
    └─ Updates last_scraped_at timestamp
    ↓
GET /properties (retrieve from database)
    ├─ Filter by price, bedrooms, type, location
    ├─ Include rating scores (upvotes/downvotes)
    ├─ Sort by score (highest first)
    └─ Support pagination
```

## Endpoints

### POST /api/scrape

Scrape Rightmove properties and store them in the database.

**Request Body:**
```json
{
  "listUrls": [
    {
      "url": "https://www.rightmove.co.uk/properties/for_sale/find.html?searchType=SALE&locationIdentifier=POSTCODE%25SW1A1AA"
    }
  ],
  "propertyUrls": [
    {
      "url": "https://www.rightmove.co.uk/properties/12345678"
    }
  ],
  "maxProperties": 100,
  "monitoringMode": false,
  "fullPropertyDetails": true,
  "includePriceHistory": false,
  "includeNearestSchools": false,
  "proxy": {
    "useApifyProxy": false
  }
}
```

**Parameters:**
- `listUrls` (optional): List of search results page URLs to scrape
- `propertyUrls` (optional): List of direct property URLs to scrape
- `maxProperties` (default: 1000): Maximum number of properties to scrape
- `fullPropertyDetails` (default: true): Whether to fetch full property details
- `proxy`: Proxy configuration for scraping

**Response:**
```json
[
  {
    "id": 1,
    "rightmove_id": "12345678",
    "listing_title": "3 bedroom detached house for sale",
    "listing_url": "https://www.rightmove.co.uk/properties/12345678",
    "full_address": "123 Test Street, London, SW1A 1AA",
    "latitude": 51.5,
    "longitude": -0.1,
    "property_type": "Detached",
    "bedrooms": 3,
    "bathrooms": 2,
    "price": 450000,
    "agent_name": "Premium London Properties",
    "agent_phone": "020 1234 5678",
    "images": ["https://example.com/img1.jpg"],
    "created_at": "2026-01-31T19:34:10",
    "updated_at": "2026-01-31T19:34:10",
    "first_scraped_at": "2026-01-31T19:34:10",
    "last_scraped_at": "2026-01-31T19:34:10"
  }
]
```

**Status Codes:**
- `200`: Successfully scraped and stored properties
- `400`: Invalid configuration (e.g., missing API key)
- `500`: Scraping or storage failed

**Error Handling:**
- If individual properties fail to store, they are logged but processing continues
- Returns all successfully stored properties
- Empty list returned if no properties were scraped

### GET /properties

Retrieve stored properties with optional filtering and rating scores.

**Query Parameters:**
- `min_price` (optional): Minimum price in GBP
- `max_price` (optional): Maximum price in GBP
- `min_bedrooms` (optional): Minimum number of bedrooms
- `max_bedrooms` (optional): Maximum number of bedrooms
- `property_type` (optional): Property type (e.g., "Detached", "Flat")
- `furnishing_type` (optional): Furnishing type
- `outcode` (optional): Postal code (outcode)
- `min_score` (optional): Minimum rating score
- `limit` (default: 100, max: 500): Number of results to return
- `offset` (default: 0): Pagination offset

**Response:**
```json
[
  {
    "id": 1,
    "rightmove_id": "12345678",
    "listing_title": "3 bedroom detached house",
    "price": 450000,
    "bedrooms": 3,
    "upvotes": 5,
    "downvotes": 1,
    "total_votes": 6,
    "score": 3.75
  }
]
```

**Sorting:**
- Results are sorted by rating score (highest first)
- Properties with no votes have a score of 0.0

## Data Conversion

### Rightmove API Fields → Database Schema

| Rightmove Field | Database Field | Notes |
|---|---|---|
| `id` | `rightmove_id` | Unique identifier for deduplication |
| `title` | `listing_title` | Property title |
| `url` | `listing_url` | URL to property on Rightmove |
| `displayAddress` | `full_address` | Property address |
| `coordinates.latitude` | `latitude` | Geographic latitude |
| `coordinates.longitude` | `longitude` | Geographic longitude |
| `propertyType` | `property_type` | Type (e.g., "Detached", "Flat") |
| `type` | `listing_type` | Transaction type (e.g., "sale", "rent") |
| `bedrooms` | `bedrooms` | Number of bedrooms |
| `bathrooms` | `bathrooms` | Number of bathrooms |
| `price` | `price` | Price in GBP |
| `description` | `text_description` | Full description |
| `images` | `images` | List of image URLs |
| `agent` | `agent_name` | Agent/estate agent name |
| `agentPhone` | `agent_phone` | Agent phone number |
| `agentProfileUrl` | `agent_profile_url` | Agent profile URL |
| `displayStatus` | `display_status` | Display status |
| `listingUpdateReason` | `listing_update_reason` | Reason for update (e.g., "new", "price_reduced") |
| `firstVisibleDate` | `first_visible_date` | ISO timestamp when first visible |
| `listingUpdateDate` | `listing_update_date` | ISO timestamp of last update |

## Database Schema

### Properties Table

```sql
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rightmove_id TEXT UNIQUE NOT NULL,
    listing_title TEXT,
    listing_url TEXT,
    full_address TEXT,
    latitude REAL,
    longitude REAL,
    
    -- Property details
    property_type TEXT,
    listing_type TEXT,
    bedrooms INTEGER,
    bathrooms INTEGER,
    price REAL,
    agent_name TEXT,
    agent_phone TEXT,
    agent_profile_url TEXT,
    
    -- Images and description
    images TEXT,  -- JSON array
    text_description TEXT,
    
    -- Dates
    first_visible_date TEXT,
    listing_update_date TEXT,
    first_scraped_at TEXT NOT NULL,
    last_scraped_at TEXT NOT NULL,
    
    -- Timestamps
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Ratings Table

```sql
CREATE TABLE ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    vote_type TEXT NOT NULL CHECK(vote_type IN ('upvote', 'downvote')),
    voted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);
```

## Usage Examples

### Scrape with list URLs

```python
import httpx

config = {
    "listUrls": [
        {
            "url": "https://www.rightmove.co.uk/properties/for_sale/find.html?searchType=SALE&locationIdentifier=POSTCODE%25SW1A1AA"
        }
    ],
    "maxProperties": 50
}

async with httpx.AsyncClient() as client:
    response = await client.post("http://localhost:8000/api/scrape", json=config)
    properties = response.json()
    print(f"Scraped {len(properties)} properties")
```

### Scrape specific properties

```python
config = {
    "propertyUrls": [
        {"url": "https://www.rightmove.co.uk/properties/12345678"},
        {"url": "https://www.rightmove.co.uk/properties/87654321"},
    ]
}

async with httpx.AsyncClient() as client:
    response = await client.post("http://localhost:8000/api/scrape", json=config)
    properties = response.json()
```

### Get filtered properties

```python
params = {
    "min_price": 300000,
    "max_price": 500000,
    "min_bedrooms": 2,
    "property_type": "Detached",
    "limit": 50
}

async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/properties", params=params)
    properties = response.json()
    
    for prop in properties:
        print(f"{prop['listing_title']}: £{prop['price']} (Score: {prop['score']})")
```

## Error Handling

### Configuration Errors (400)

```json
{
  "detail": "APIFY_API_KEY not configured. Set it in .env file"
}
```

### Scraping Failures (500)

```json
{
  "detail": "Scraping failed: Actor run failed with status FAILED"
}
```

### Property Not Found (404)

```json
{
  "detail": "Property not found"
}
```

## Features

### Deduplication
- Properties are identified by `rightmove_id`
- Updating a property with the same `rightmove_id` updates the existing record instead of creating a duplicate
- `last_scraped_at` timestamp is updated on each scrape

### Rating System
- Properties can receive upvotes and downvotes
- Scores are time-weighted (recent votes weighted more heavily)
- Exponential decay with 30-day half-life
- Properties with no votes have a score of 0.0

### Filtering
- Filter by price range, bedroom count, property type, location
- Filter by minimum rating score
- Support pagination with `limit` and `offset`

### Logging
- All scraping operations are logged
- Individual property conversion failures are logged but don't stop processing
- Configuration errors are logged with details

## Configuration

Required environment variables in `.env`:

```bash
APIFY_API_KEY=<your-apify-api-key>
```

See `.env.example` for full configuration options.

## Performance

### Query Optimization
- Indexes on: rightmove_id, location, price, bedrooms, property_type, outcode, removed
- Properties sorted by creation date (newest first) by default
- Rating scores sorted by weighted score (highest first)

### Scaling Considerations
- Rating score calculation iterates through all votes (consider materializing in production)
- Filter queries build SQL dynamically - all filters are indexed
- Database is SQLite (suitable for <100k properties)

## Future Enhancements

1. **Bulk Operations**
   - Batch scraping with progress tracking
   - Bulk rating import/export

2. **Real Estate Validation**
   - Cross-check prices against Zoopla, Rightmove historical data
   - Validate coordinates

3. **Notifications**
   - Alert on price reductions
   - Alert on new listings matching criteria

4. **Admin Features**
   - Manual property removal
   - Bulk property operations
   - Scraping job scheduling

5. **API Rate Limiting**
   - Per-IP rate limiting
   - Per-user rate limiting
