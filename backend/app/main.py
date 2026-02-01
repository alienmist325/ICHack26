# backend/app/main.py
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import crud
from app.database import init_db
from app.schemas import (
    Property,
    PropertyCreate,
    PropertyFilters,
    PropertyUpdate,
    PropertyWithScore,
    Rating,
    RatingCreate,
)
from backend.models.rightmove import RightmoveScraperInput
from backend.scraper.scrape import scrape_rightmove

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: Nothing to clean up for SQLite


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
    limit: int = Query(default=10, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    List properties with optional filters and rating scores.

    Results are sorted by rating score (highest first).
    Supports full-text search across listing title, address, and description.
    """
    filters = PropertyFilters(
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
