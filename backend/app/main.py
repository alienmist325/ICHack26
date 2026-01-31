# backend/app/main.py
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import crud
from app.database import init_db
from app.schemas import (
    DistanceRequest,
    DistanceResponse,
    DistanceResult,
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
    VerificationRequest,
    VerificationStartResponse,
    JobStatusResponse,
    JobStatusEnum,
    VerificationStatusEnum,
)
from backend.models.rightmove import RightmoveScraperInput
from backend.scraper.scrape import scrape_rightmove
from backend.config import settings
from backend.services.routing_service import (
    RoutingService,
    properties_in_polygon,
)
from services.verification.service import PropertyVerificationService
from services.verification.jobs import get_job_queue, init_job_queue

logger = logging.getLogger(__name__)

# ============================================================================
# Global state for routing service (initialized in lifespan)
# ============================================================================
_routing_service: Optional[RoutingService] = None


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database, routing service, and verification job queue
    global _routing_service
    init_db()

    # Initialize routing service
    _routing_service = RoutingService()
    logger.info("Routing service initialized at app startup")

    # Initialize verification service if credentials are configured
    verification_service = None
    job_queue = None
    if settings.elevenlabs_api_key:
        try:
            verification_service = PropertyVerificationService(
                settings.elevenlabs_api_key
            )

            # Initialize job queue
            job_queue = await init_job_queue(
                max_concurrent=settings.verification_max_concurrent_calls
            )

            # Start job processor
            async def process_verification_jobs(job):
                """Job processor for verification tasks."""
                try:
                    if (
                        not settings.elevenlabs_agent_id
                        or not settings.elevenlabs_phone_number
                    ):
                        raise ValueError(
                            "ElevenLabs Agent ID and phone number not configured"
                        )

                    property_data = crud.get_property_for_verification(job.property_id)
                    if not property_data:
                        raise ValueError(
                            f"Property {job.property_id} not found or has no agent phone"
                        )

                    # Perform verification
                    result = await verification_service.verify_property(
                        job=job,
                        agent_id=settings.elevenlabs_agent_id,
                        phone_number=settings.elevenlabs_phone_number,
                        property_address=property_data["address"],
                        agent_phone=property_data["agent_phone"],
                        call_timeout=settings.verification_call_timeout,
                    )

                    # Store result in database
                    crud.create_verification_log(
                        property_id=job.property_id,
                        agent_phone=property_data["agent_phone"],
                        verification_status=result.verification_status.value,
                        call_timestamp=result.created_at.isoformat()
                        if result.created_at
                        else None,
                        call_duration_seconds=result.call_duration_seconds,
                        agent_response=result.agent_response,
                        confidence_score=result.confidence_score,
                        notes=result.notes,
                        error_message=result.error_message,
                    )

                    # Update property verification status
                    crud.update_property_verification_status(
                        job.property_id,
                        result.verification_status.value,
                        result.notes,
                    )

                    return result
                except Exception as e:
                    logger.error(f"Verification job {job.job_id} failed: {e}")

                    # Mark as failed in database
                    crud.update_property_verification_status(
                        job.property_id,
                        "failed",
                        f"Verification failed: {str(e)}",
                    )
                    raise

            # Start background worker
            await job_queue.start(process_verification_jobs)
            logger.info("Verification service initialized and job queue started")
        except Exception as e:
            logger.warning(f"Could not initialize verification service: {e}")
    else:
        logger.warning(
            "ElevenLabs API key not configured - verification service disabled"
        )

    yield

    # Shutdown: Clean up routing service and job queue
    _routing_service = None
    logger.info("Routing service shutdown")

    try:
        if job_queue:
            await job_queue.stop()
            logger.info("Verification job queue stopped")
    except Exception as e:
        logger.warning(f"Error stopping job queue: {e}")


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
# Verification endpoints
# ============================================================================


@app.post(
    "/api/verify/property/{property_id}",
    response_model=VerificationStartResponse,
    status_code=202,
)
async def start_property_verification(property_id: int):
    """
    Start property availability verification.

    This endpoint queues a property for verification via ElevenLabs AI call
    and returns a job ID for polling.

    Returns 202 Accepted with job_id for polling verification status.
    """
    if not settings.elevenlabs_api_key:
        raise HTTPException(
            status_code=503, detail="Verification service not configured"
        )

    # Check if property exists and has agent phone
    property_data = crud.get_property_for_verification(property_id)
    if not property_data:
        raise HTTPException(
            status_code=404,
            detail=f"Property {property_id} not found or has no agent phone number",
        )

    try:
        # Enqueue job
        job_queue = await get_job_queue()
        job = await job_queue.enqueue(property_id)

        return VerificationStartResponse(
            job_id=job.job_id,
            property_id=property_id,
            status=JobStatusEnum.QUEUED,
            message=f"Verification job {job.job_id} queued for property {property_id}",
            poll_url=f"/api/verify/job/{job.job_id}",
        )
    except Exception as e:
        logger.error(f"Failed to queue verification: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to queue verification: {str(e)}"
        )


@app.get("/api/verify/job/{job_id}", response_model=JobStatusResponse)
async def get_verification_job_status(job_id: str):
    """
    Get the status of a verification job.

    Returns:
    - 202 Accepted if job is still processing
    - 200 OK if job is completed or failed
    """
    try:
        job_queue = await get_job_queue()
        job = await job_queue.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Build response
        response = JobStatusResponse(
            job_id=job.job_id,
            status=JobStatusEnum(job.status.value),
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error=job.error,
        )

        # If completed, include verification result from database
        if job.status.value == "completed":
            from app.schemas import VerificationResultResponse
            from datetime import datetime

            verification_log = crud.get_verification_log(job.property_id)
            if verification_log:
                response.result = VerificationResultResponse(
                    property_id=job.property_id,
                    verification_status=VerificationStatusEnum(
                        verification_log["verification_status"]
                    ),
                    confidence_score=verification_log["confidence_score"] or 0.0,
                    call_transcript=verification_log.get("transcript"),
                    call_duration_seconds=verification_log["call_duration_seconds"],
                    agent_response=verification_log["agent_response"],
                    notes=verification_log["notes"],
                    error_message=verification_log["error_message"],
                    created_at=datetime.fromisoformat(verification_log["created_at"])
                    if verification_log["created_at"]
                    else datetime.utcnow(),
                )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error getting job status: {str(e)}"
        )


@app.get("/api/verify/stats")
async def get_verification_statistics():
    """Get verification statistics."""
    try:
        stats = crud.get_verification_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting verification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Scraping endpoints
# ============================================================================


@app.post("/api/scrape", response_model=List[Property], status_code=200)
async def scrape_properties(config: RightmoveScraperInput):
    """
    Scrape Rightmove properties using the provided configuration.

    This endpoint:
    1. Accepts Rightmove scraper configuration
    2. Scrapes properties from Rightmove using Apify
    3. Converts and stores properties in the database
    4. Returns the stored properties

    Args:
        config: RightmoveScraperInput with scraping parameters

    Returns:
        List of Property objects that were stored in the database

    Raises:
        HTTPException 500: If scraping or storage fails
    """
    try:
        logger.info(
            f"Starting Rightmove scrape with config: {config.model_dump(exclude_unset=True)}"
        )

        # Scrape properties from Rightmove using Apify
        response = await scrape_rightmove(config)

        if not response.properties:
            logger.warning("Scrape completed but no properties returned")
            return []

        logger.info(f"Scraped {len(response.properties)} properties from Rightmove")

        # Convert and store each property
        stored_properties: List[Property] = []
        for rightmove_prop in response.properties:
            try:
                # Convert RightmoveProperty to PropertyCreate
                property_data = crud.rightmove_property_to_create(rightmove_prop)

                # Upsert into database (create or update based on rightmove_id)
                property_obj, created = crud.upsert_property(property_data)
                stored_properties.append(property_obj)

                action = "Created" if created else "Updated"
                logger.debug(
                    f"{action} property {rightmove_prop.id}: {rightmove_prop.title}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to store property {rightmove_prop.id}: {str(e)}",
                    exc_info=True,
                )
                # Continue with next property instead of failing entire request
                continue

        logger.info(
            f"Successfully stored {len(stored_properties)} properties in database"
        )
        return stored_properties

    except ValueError as e:
        # Configuration/validation error
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected error
        logger.error(f"Scraping failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


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
