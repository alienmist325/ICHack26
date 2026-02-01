# backend/app/main.py
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import crud
from app.database import init_db
from app.routers import auth, personalization, properties, shared_feeds, users, viewings
from app.schemas import (
    DistanceRequest,
    DistanceResponse,
    DistanceResult,
    GeocodeRequest,
    GeocodeResponse,
    IsochroneRequest,
    IsochroneResponse,
    Property,
    PropertyCreate,
    PropertyFilters,
    PropertyUpdate,
    PropertyWithScore,
    Rating,
    RatingCreate,
    TravelTimeRequest,
    TravelTimeResponse,
    TravelTimeResult,
)
from app.routers import auth, users, properties, viewings, shared_feeds, personalization
from backend.models.rightmove import RightmoveScraperInput
from backend.scraper.scrape import scrape_rightmove
from backend.services.geocoding_service import GeocodingService
from backend.services.routing_service import (
    RoutingService,
    properties_in_polygon,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Global state for routing service (initialized in lifespan)
# ============================================================================
_routing_service: Optional[RoutingService] = None
_geocoding_service: Optional[GeocodingService] = None


def get_routing_service_dep() -> RoutingService:
    """
    Dependency for accessing the routing service instance.

    Used with FastAPI's Depends() to inject the routing service into endpoints.
    Ensures the service is properly initialized before use.

    Raises:
        RuntimeError: If routing service was not initialized during app startup

    Returns:
        RoutingService: The initialized routing service instance
    """
    if _routing_service is None:
        raise RuntimeError(
            "Routing service not initialized. "
            "This should not happen if the app started correctly."
        )
    return _routing_service


def get_geocoding_service_dep() -> GeocodingService:
    """
    Dependency for accessing the geocoding service instance.

    Used with FastAPI's Depends() to inject the geocoding service into endpoints.
    Ensures the service is properly initialized before use.

    Raises:
        RuntimeError: If geocoding service was not initialized during app startup

    Returns:
        GeocodingService: The initialized geocoding service instance
    """
    if _geocoding_service is None:
        raise RuntimeError(
            "Geocoding service not initialized. "
            "This should not happen if the app started correctly."
        )
    return _geocoding_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database and routing service
    global _routing_service
    global _geocoding_service
    init_db()
    _routing_service = RoutingService()
    _geocoding_service = GeocodingService()
    logger.info("Routing service initialized at app startup")
    logger.info("Geocoding service initialized at app startup")
    yield
    # Shutdown: Clean up
    _routing_service = None
    _geocoding_service = None
    logger.info("Routing service shutdown")
    logger.info("Geocoding service shutdown")


app = FastAPI(
    title="Property Rental Finder API",
    description="API for finding and rating rental properties from Rightmove",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - adjust origins as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(properties.router)
app.include_router(viewings.router)
app.include_router(shared_feeds.router)
app.include_router(personalization.router)

# ============================================================================
# Property endpoints
# ============================================================================


@app.post("/properties", response_model=Property, status_code=201)
async def create_property(property_data: PropertyCreate):
    """Create a new property listing."""
    try:
        property_obj, created = crud.upsert_property(property_data)
        return property_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/properties/{property_id}", response_model=PropertyWithScore)
async def get_property(property_id: int):
    """Get a specific property by ID with its rating score."""
    property_obj = crud.get_property_with_score(property_id)
    if property_obj is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return property_obj


@app.get("/properties", response_model=dict)
async def list_properties(
    search_query: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    property_type: Optional[str] = None,
    furnishing_type: Optional[str] = None,
    outcode: Optional[str] = None,
    removed: bool = False,
    min_score: Optional[float] = None,
    isochrone_center_property_id: Optional[int] = None,
    isochrone_duration_seconds: int = 600,
    limit: int = Query(default=10, le=500),
    offset: int = Query(default=0, ge=0),
    routing_service: RoutingService = Depends(get_routing_service_dep),
):
    """
    List properties with optional filters and rating scores.

    Results are sorted by rating score (highest first).
    Supports full-text search across listing title, address, and description.

    Additionally supports isochrone-based filtering: if isochrone_center_property_id
    is provided, returns only properties reachable from that property within the
    specified duration, combined with all other filters.

    Query Parameters:
        - search_query: Full-text search
        - min_price, max_price: Price range filter
        - min_bedrooms, max_bedrooms: Bedrooms range filter
        - property_type: Property type filter
        - furnishing_type: Furnishing filter
        - outcode: Postcode filter
        - min_score: Minimum rating score
        - isochrone_center_property_id: If set, compute isochrone from this property
        - isochrone_duration_seconds: Duration for isochrone (default 600s/10min)
        - limit: Results per page (max 500)
        - offset: Pagination offset
    """
    try:
        # Build filters object
        filters = PropertyFilters(
            search_query=search_query,
            min_price=min_price,
            max_price=max_price,
            min_bedrooms=min_bedrooms,
            max_bedrooms=max_bedrooms,
            property_type=property_type,
            furnishing_type=furnishing_type,
            outcode=outcode,
            removed=removed,
            min_score=min_score,
        )

        # Handle isochrone-based filtering if requested
        if isochrone_center_property_id is not None:
            logger.info(
                f"Filtering properties with isochrone from property "
                f"{isochrone_center_property_id} "
                f"({isochrone_duration_seconds}s duration)"
            )

            # Get the center property
            center_property = crud.get_property_by_id(isochrone_center_property_id)
            if center_property is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Property {isochrone_center_property_id} not found",
                )

            if center_property.latitude is None or center_property.longitude is None:
                raise HTTPException(
                    status_code=400,
                    detail="Center property does not have valid coordinates",
                )

            # Compute isochrone
            isochrone_polygon = routing_service.compute_isochrone(
                center_property.latitude,
                center_property.longitude,
                isochrone_duration_seconds,
            )

            # Get the center property
            center_property = crud.get_property_by_id(isochrone_center_property_id)
            if center_property is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Property {isochrone_center_property_id} not found",
                )

            if center_property.latitude is None or center_property.longitude is None:
                raise HTTPException(
                    status_code=400,
                    detail="Center property does not have valid coordinates",
                )

            # Compute isochrone
            isochrone_polygon = routing_service.compute_isochrone(
                center_property.latitude,
                center_property.longitude,
                isochrone_duration_seconds,
            )

            if isochrone_polygon is None:
                raise HTTPException(
                    status_code=503,
                    detail="Routing service failed to compute isochrone",
                )

            # Get all properties with coordinates
            all_properties = crud.get_all_properties_with_coordinates()

            # Find properties inside isochrone
            isochrone_property_ids = properties_in_polygon(
                isochrone_polygon, all_properties
            )

            logger.info(f"Found {len(isochrone_property_ids)} properties in isochrone")

            # Get properties with isochrone AND other filters
            properties, total_count = crud.get_properties_with_isochrone_and_filters(
                isochrone_property_ids,
                filters=filters,
                limit=limit,
                offset=offset,
            )
        else:
            # Normal property filtering (without isochrone)
            properties, total_count = crud.get_properties_with_scores(
                filters=filters,
                limit=limit,
                offset=offset,
                min_score=min_score,
                search_query=search_query,
            )

        return {
            "properties": properties,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list properties: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.patch("/properties/{property_id}", response_model=Property)
async def update_property(property_id: int, property_data: PropertyUpdate):
    """Update an existing property."""
    property_obj = crud.update_property(property_id, property_data)
    if property_obj is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return property_obj


@app.delete("/properties/{property_id}", status_code=204)
async def delete_property(property_id: int):
    """Soft delete a property (sets removed=True)."""
    success = crud.soft_delete_property(property_id)
    if not success:
        raise HTTPException(status_code=404, detail="Property not found")
    return None


# ============================================================================
# Rating endpoints
# ============================================================================


@app.post("/ratings", response_model=Rating, status_code=201)
async def create_rating(rating_data: RatingCreate):
    """Create a new rating (upvote or downvote) for a property."""
    # Check if property exists
    property_obj = crud.get_property_by_id(rating_data.property_id)
    if property_obj is None:
        raise HTTPException(status_code=404, detail="Property not found")

    try:
        return crud.create_rating(rating_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/properties/{property_id}/ratings", response_model=List[Rating])
async def get_property_ratings(
    property_id: int,
    days: Optional[int] = Query(
        default=None, description="Only return ratings from the last N days"
    ),
):
    """Get all ratings for a specific property."""
    # Check if property exists
    property_obj = crud.get_property_by_id(property_id)
    if property_obj is None:
        raise HTTPException(status_code=404, detail="Property not found")

    return crud.get_ratings_for_property(property_id, days=days)


# ============================================================================
# Utility endpoints
# ============================================================================


@app.get("/properties/count")
async def count_properties(
    search_query: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    property_type: Optional[str] = None,
    furnishing_type: Optional[str] = None,
    outcode: Optional[str] = None,
    removed: bool = False,
):
    """Get the total count of properties matching the filters."""
    filters = PropertyFilters(
        search_query=search_query,
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
        max_bedrooms=max_bedrooms,
        property_type=property_type,
        furnishing_type=furnishing_type,
        outcode=outcode,
        removed=removed,
    )

    return {"count": crud.get_property_count(filters)}


@app.get("/outcodes", response_model=List[str])
async def list_outcodes():
    """Get a list of all unique postcodes in the database."""
    return crud.get_unique_outcodes()


@app.get("/property-types", response_model=List[str])
async def list_property_types():
    """Get a list of all unique property types in the database."""
    return crud.get_unique_property_types()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# Scraping endpoints
# ============================================================================
# Routing & Distance endpoints
# ============================================================================


@app.post("/routing/isochrone", response_model=IsochroneResponse)
async def find_properties_in_isochrone(
    request: IsochroneRequest,
    routing_service: RoutingService = Depends(get_routing_service_dep),
):
    """
    Find all properties reachable from a property within a given time duration.

    Uses isochrone routing to create a polygon of all areas reachable within
    the specified duration, then queries the database for properties inside.

    Args:
        request: IsochroneRequest with property_id and duration_seconds

    Returns:
        IsochroneResponse with property IDs inside isochrone

    Raises:
        HTTPException 404: If property not found
        HTTPException 400: If coordinates or duration are invalid
        HTTPException 503: If routing service is unavailable
    """
    try:
        # Get property location
        property_obj = crud.get_property_by_id(request.property_id)
        if property_obj is None:
            raise HTTPException(status_code=404, detail="Property not found")

        if property_obj.latitude is None or property_obj.longitude is None:
            raise HTTPException(
                status_code=400,
                detail="Property does not have valid coordinates",
            )

        logger.info(
            f"Computing isochrone for property {request.property_id} "
            f"with duration {request.duration_seconds}s"
        )

        # Compute isochrone polygon
        isochrone_polygon = routing_service.compute_isochrone(
            property_obj.latitude,
            property_obj.longitude,
            request.duration_seconds,
        )

        if isochrone_polygon is None:
            raise HTTPException(
                status_code=503,
                detail="Routing service failed to compute isochrone",
            )

        # Get all properties with coordinates
        all_properties = crud.get_all_properties_with_coordinates()

        # Find properties inside isochrone
        property_ids = properties_in_polygon(isochrone_polygon, all_properties)

        logger.info(
            f"Found {len(property_ids)} properties inside isochrone "
            f"for property {request.property_id}"
        )

        return IsochroneResponse(
            property_ids=property_ids,
            property_count=len(property_ids),
            center_lat=property_obj.latitude,
            center_lon=property_obj.longitude,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compute isochrone: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Routing service unavailable")


@app.post("/routing/travel-times", response_model=TravelTimeResponse)
async def get_travel_times_endpoint(
    request: TravelTimeRequest,
    routing_service: RoutingService = Depends(get_routing_service_dep),
):
    """
    Calculate travel times from a property to multiple destinations.

    Uses the routing service to compute travel times to up to 25 destinations.

    Args:
        request: TravelTimeRequest with property_id and list of destinations

    Returns:
        TravelTimeResponse with travel times to each destination

    Raises:
        HTTPException 404: If property not found
        HTTPException 400: If coordinates are invalid or too many destinations
        HTTPException 503: If routing service is unavailable
    """
    try:
        # Validate request
        if len(request.destinations) > 25:
            raise HTTPException(
                status_code=400,
                detail="Maximum 25 destinations allowed per request",
            )

        # Get property location
        property_obj = crud.get_property_by_id(request.property_id)
        if property_obj is None:
            raise HTTPException(status_code=404, detail="Property not found")

        if property_obj.latitude is None or property_obj.longitude is None:
            raise HTTPException(
                status_code=400,
                detail="Property does not have valid coordinates",
            )

        logger.info(
            f"Computing travel times from property {request.property_id} "
            f"to {len(request.destinations)} destinations"
        )

        # Convert destinations to coordinate tuples (lat, lon)
        destination_coords = [
            (dest.latitude, dest.longitude) for dest in request.destinations
        ]

        # Compute travel times
        travel_times = routing_service.get_travel_times_matrix(
            (property_obj.latitude, property_obj.longitude),
            destination_coords,
        )

        # Format results with destination labels
        results = []
        for i, travel_time_data in enumerate(travel_times):
            dest = request.destinations[i]
            travel_time_seconds = travel_time_data["travel_time_seconds"]
            travel_time_minutes = travel_time_seconds / 60.0

            results.append(
                TravelTimeResult(
                    destination=dest,
                    travel_time_seconds=travel_time_seconds,
                    travel_time_minutes=travel_time_minutes,
                )
            )

        logger.info(
            f"Computed travel times for property {request.property_id}: "
            f"{len(results)} results"
        )

        return TravelTimeResponse(
            property_id=request.property_id,
            origin_lat=property_obj.latitude,
            origin_lon=property_obj.longitude,
            results=results,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compute travel times: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Routing service unavailable")


@app.post("/routing/distances", response_model=DistanceResponse)
async def get_distances_endpoint(
    request: DistanceRequest,
    routing_service: RoutingService = Depends(get_routing_service_dep),
):
    """
    Calculate distances from a property to multiple destinations.

    Uses the routing service to compute distances to up to 25 destinations.

    Args:
        request: DistanceRequest with property_id and list of destinations

    Returns:
        DistanceResponse with distances to each destination

    Raises:
        HTTPException 404: If property not found
        HTTPException 400: If coordinates are invalid or too many destinations
        HTTPException 503: If routing service is unavailable
    """
    try:
        # Validate request
        if len(request.destinations) > 25:
            raise HTTPException(
                status_code=400,
                detail="Maximum 25 destinations allowed per request",
            )

        # Get property location
        property_obj = crud.get_property_by_id(request.property_id)
        if property_obj is None:
            raise HTTPException(status_code=404, detail="Property not found")

        if property_obj.latitude is None or property_obj.longitude is None:
            raise HTTPException(
                status_code=400,
                detail="Property does not have valid coordinates",
            )

        logger.info(
            f"Computing distances from property {request.property_id} "
            f"to {len(request.destinations)} destinations"
        )

        # Convert destinations to coordinate tuples (lat, lon)
        destination_coords = [
            (dest.latitude, dest.longitude) for dest in request.destinations
        ]

        # Compute distances
        distances = routing_service.get_distances_matrix(
            (property_obj.latitude, property_obj.longitude),
            destination_coords,
        )

        # Format results with destination labels
        results = []
        for i, distance_data in enumerate(distances):
            dest = request.destinations[i]
            distance_meters = distance_data["distance_meters"]
            distance_km = distance_meters / 1000.0

            results.append(
                DistanceResult(
                    destination=dest,
                    distance_meters=distance_meters,
                    distance_km=distance_km,
                )
            )

        logger.info(
            f"Computed distances for property {request.property_id}: "
            f"{len(results)} results"
        )

        return DistanceResponse(
            property_id=request.property_id,
            origin_lat=property_obj.latitude,
            origin_lon=property_obj.longitude,
            results=results,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compute distances: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Routing service unavailable")


@app.post("/routing/geocode", response_model=GeocodeResponse)
async def geocode_address(
    request: GeocodeRequest,
    geocoding_service: GeocodingService = Depends(get_geocoding_service_dep),
):
    """
    Geocode an address string to latitude/longitude coordinates.

    Accepts any address format:
    - Street addresses: "123 Main Street, London, UK"
    - Postcodes: "SW1A 1AA"
    - Place names: "Tower Bridge, London"
    - Partial addresses: "Oxford Street, London"

    Uses a lenient approach: returns the top/best match even if confidence
    is lower, rather than failing for ambiguous addresses.

    Args:
        request: GeocodeRequest with address string

    Returns:
        GeocodeResponse with latitude, longitude, and echo of input address

    Raises:
        HTTPException 400: If address is empty or invalid
        HTTPException 404: If address cannot be geocoded (no results found)
        HTTPException 503: If geocoding service is unavailable
    """
    try:
        # Validate request
        if not request.address or not request.address.strip():
            raise HTTPException(
                status_code=400,
                detail="Address cannot be empty",
            )

        logger.info(f"Geocoding address: '{request.address}'")

        # Call geocoding service
        coordinates = geocoding_service.geocode_address(request.address)

        if coordinates is None:
            logger.warning(f"No geocoding results found for: '{request.address}'")
            raise HTTPException(
                status_code=404,
                detail=f"Could not geocode address: '{request.address}'",
            )

        latitude, longitude = coordinates

        logger.info(
            f"Successfully geocoded '{request.address}' to ({latitude}, {longitude})"
        )

        return GeocodeResponse(
            latitude=latitude,
            longitude=longitude,
            address=request.address,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to geocode address: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Geocoding service unavailable")
