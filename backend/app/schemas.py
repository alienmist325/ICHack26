# backend/app/schemas.py
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class VoteType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


class PropertyBase(BaseModel):
    rightmove_id: str
    listing_title: Optional[str] = None
    listing_url: Optional[str] = None
    incode: Optional[str] = None
    outcode: Optional[str] = None
    full_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Property details
    property_type: Optional[str] = None
    listing_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size: Optional[str] = None
    furnishing_type: Optional[str] = None
    amenities: Optional[List[str]] = None

    # Pricing
    price: Optional[float] = None
    deposit: Optional[float] = None
    price_history: Optional[List[Dict[str, Any]]] = None

    # Ownership details
    tenure: Optional[str] = None
    council_tax_band: Optional[str] = None
    council_tax_exempt: Optional[bool] = None
    years_remaining_on_lease: Optional[int] = None
    annual_ground_rent: Optional[float] = None
    annual_service_charge: Optional[float] = None
    ground_rent_percentage_increase: Optional[float] = None

    # Description
    text_description: Optional[str] = None
    formatted_html_description: Optional[str] = None

    # Media
    images: Optional[List[str]] = None
    floorplans: Optional[List[str]] = None
    brochures: Optional[List[str]] = None
    epc: Optional[Dict[str, Any]] = None

    # Agent information
    agent_name: Optional[str] = None
    agent_logo: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_address: Optional[str] = None
    agent_profile_url: Optional[str] = None
    agent_description: Optional[str] = None
    agent_listings_url: Optional[str] = None

    # Status
    sold: bool = False
    removed: bool = False
    display_status: Optional[str] = None
    listing_update_reason: Optional[str] = None

    # Dates
    first_visible_date: Optional[str] = None
    listing_update_date: Optional[str] = None

    # Nearby amenities
    nearest_schools: Optional[List[Dict[str, Any]]] = None


class PropertyCreate(PropertyBase):
    """Schema for creating a new property."""

    pass


class PropertyUpdate(BaseModel):
    """Schema for updating an existing property - all fields optional."""

    listing_title: Optional[str] = None
    listing_url: Optional[str] = None
    incode: Optional[str] = None
    outcode: Optional[str] = None
    full_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = None
    listing_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size: Optional[str] = None
    furnishing_type: Optional[str] = None
    amenities: Optional[List[str]] = None
    price: Optional[float] = None
    deposit: Optional[float] = None
    price_history: Optional[List[Dict[str, Any]]] = None
    tenure: Optional[str] = None
    council_tax_band: Optional[str] = None
    council_tax_exempt: Optional[bool] = None
    years_remaining_on_lease: Optional[int] = None
    annual_ground_rent: Optional[float] = None
    annual_service_charge: Optional[float] = None
    ground_rent_percentage_increase: Optional[float] = None
    text_description: Optional[str] = None
    formatted_html_description: Optional[str] = None
    images: Optional[List[str]] = None
    floorplans: Optional[List[str]] = None
    brochures: Optional[List[str]] = None
    epc: Optional[Dict[str, Any]] = None
    agent_name: Optional[str] = None
    agent_logo: Optional[str] = None
    agent_phone: Optional[str] = None
    agent_address: Optional[str] = None
    agent_profile_url: Optional[str] = None
    agent_description: Optional[str] = None
    agent_listings_url: Optional[str] = None
    sold: Optional[bool] = None
    removed: Optional[bool] = None
    display_status: Optional[str] = None
    listing_update_reason: Optional[str] = None
    first_visible_date: Optional[str] = None
    listing_update_date: Optional[str] = None
    nearest_schools: Optional[List[Dict[str, Any]]] = None


class Property(PropertyBase):
    """Schema for reading a property from the database."""

    id: int
    first_scraped_at: str
    last_scraped_at: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PropertyWithScore(Property):
    """Property with calculated rating score."""

    upvotes: int
    downvotes: int
    score: float
    total_votes: int


class RatingCreate(BaseModel):
    """Schema for creating a rating."""

    property_id: int
    vote_type: VoteType


class Rating(BaseModel):
    """Schema for reading a rating from the database."""

    id: int
    property_id: int
    vote_type: VoteType
    voted_at: str

    class Config:
        from_attributes = True


class PropertyFilters(BaseModel):
    """Schema for filtering properties."""

    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    furnishing_type: Optional[str] = None
    outcode: Optional[str] = None
    removed: bool = False  # By default, don't show removed properties
    min_score: Optional[float] = None  # Minimum rating score
