# backend/app/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from contextlib import asynccontextmanager

from app.database import init_db
from app.schemas import (
    Property,
    PropertyCreate,
    PropertyUpdate,
    PropertyWithScore,
    Rating,
    RatingCreate,
    PropertyFilters,
)
from app import crud

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
    lifespan=lifespan
)

# CORS middleware - adjust origins as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
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

@app.get("/properties", response_model=List[PropertyWithScore])
async def list_properties(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    property_type: Optional[str] = None,
    furnishing_type: Optional[str] = None,
    outcode: Optional[str] = None,
    removed: bool = False,
    min_score: Optional[float] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
):
    """
    List properties with optional filters and rating scores.
    
    Results are sorted by rating score (highest first).
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
    
    return crud.get_properties_with_scores(
        filters=filters,
        limit=limit,
        offset=offset,
        min_score=min_score
    )

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
    days: Optional[int] = Query(default=None, description="Only return ratings from the last N days")
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
