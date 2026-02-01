# backend/app/schemas.py
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class VoteType(str, Enum):
    STAR = "star"
    GONE_FROM_MARKET = "gone_from_market"


class PropertyStatus(str, Enum):
    INTERESTED = "interested"
    VIEWING = "viewing"
    OFFER = "offer"
    ACCEPTED = "accepted"


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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class PropertyFilters(BaseModel):
    """Schema for filtering properties."""

    search_query: Optional[str] = None  # Full-text search
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_bedrooms: Optional[int] = None
    max_bedrooms: Optional[int] = None
    property_type: Optional[str] = None
    furnishing_type: Optional[str] = None
    outcode: Optional[str] = None
    removed: bool = False  # By default, don't show removed properties
    min_score: Optional[float] = None  # Minimum rating score


# ============================================================================
# User Authentication Schemas
# ============================================================================


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: str
    password: str


class UserLogin(BaseModel):
    """Schema for user login."""

    email: str
    password: str


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserBase(BaseModel):
    """Base schema for user information."""

    email: str
    is_active: bool = True


class User(UserBase):
    """Schema for reading a user from the database."""

    id: int
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

    bio: Optional[str] = None
    dream_property_description: Optional[str] = None
    preferred_price_min: Optional[int] = None
    preferred_price_max: Optional[int] = None
    preferred_bedrooms_min: Optional[int] = None
    preferred_property_types: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    notification_viewing_reminder_days: Optional[int] = 3
    notification_email_enabled: Optional[bool] = True
    notification_in_app_enabled: Optional[bool] = True
    notification_feed_changes_enabled: Optional[bool] = True


class UserUpdate(BaseModel):
    """Schema for updating user profile - all fields optional."""

    bio: Optional[str] = None
    dream_property_description: Optional[str] = None
    preferred_price_min: Optional[int] = None
    preferred_price_max: Optional[int] = None
    preferred_bedrooms_min: Optional[int] = None
    preferred_property_types: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    notification_viewing_reminder_days: Optional[int] = None
    notification_email_enabled: Optional[bool] = None
    notification_in_app_enabled: Optional[bool] = None
    notification_feed_changes_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for reading user profile from the database."""

    id: int
    email: str
    is_active: bool
    bio: Optional[str] = None
    dream_property_description: Optional[str] = None
    preferred_price_min: Optional[int] = None
    preferred_price_max: Optional[int] = None
    preferred_bedrooms_min: Optional[int] = None
    preferred_property_types: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    notification_viewing_reminder_days: int
    notification_email_enabled: bool
    notification_in_app_enabled: bool
    notification_feed_changes_enabled: bool
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class NotificationSettings(BaseModel):
    """Schema for user notification settings."""

    notification_viewing_reminder_days: int = 3
    notification_email_enabled: bool = True
    notification_in_app_enabled: bool = True
    notification_feed_changes_enabled: bool = True


# ============================================================================
# Property Bookmark & Status Schemas
# ============================================================================


class PropertyBookmark(BaseModel):
    """Schema for property bookmarks."""

    property_id: int
    is_starred: bool = True


class PropertyStatusUpdate(BaseModel):
    """Schema for updating property status."""

    status: PropertyStatus
    comment: Optional[str] = None


class PropertyStatusResponse(BaseModel):
    """Schema for reading property status from the database."""

    user_id: int
    property_id: int
    status: str
    status_updated_at: str
    created_at: str


class PropertyComment(BaseModel):
    """Schema for property comments."""

    comment: str


class PropertyCommentResponse(PropertyComment):
    """Schema for reading property comments from the database."""

    id: int
    user_id: int
    property_id: int
    created_at: str
    updated_at: str


# ============================================================================
# Viewing Event Schemas
# ============================================================================


class ViewingEventCreate(BaseModel):
    """Schema for creating viewing events."""

    property_id: int
    viewing_date: str  # ISO format: YYYY-MM-DD
    viewing_time: Optional[str] = None  # HH:MM format
    agent_contact: Optional[str] = None
    notes: Optional[str] = None


class ViewingEventResponse(ViewingEventCreate):
    """Schema for reading viewing events from the database."""

    id: int
    user_id: int
    reminder_sent: bool
    created_at: str
    updated_at: str


# ============================================================================
# Shared Feed Schemas
# ============================================================================


class SharedFeedCreate(BaseModel):
    """Schema for creating a shared feed."""

    name: str


class SharedFeedMember(BaseModel):
    """Schema for shared feed members."""

    user_id: int
    joined_at: str


class SharedFeedResponse(BaseModel):
    """Schema for reading shared feeds from the database."""

    id: int
    name: str
    invite_token: str
    max_members: int
    created_at: str
    updated_at: str


class SharedFeedDetailResponse(SharedFeedResponse):
    """Shared feed with member details."""

    members: List[User] = []
    member_count: int = 0
    # Isochrone-based filtering
    isochrone_center_lat: Optional[float] = None
    isochrone_center_lon: Optional[float] = None
    isochrone_duration_seconds: Optional[int] = None


# ============================================================================
# Routing Service Schemas
# ============================================================================


class LocationCoordinate(BaseModel):
    """A geographic location coordinate."""

    latitude: float
    longitude: float
    label: Optional[str] = None  # e.g., "Work", "School", "Home"


class IsochroneRequest(BaseModel):
    """Request to find properties within an isochrone."""

    property_id: int
    duration_seconds: int = 600  # default 10 minutes


class IsochroneResponse(BaseModel):
    """Response with property IDs inside an isochrone."""

    property_ids: List[int]
    property_count: int
    center_lat: float
    center_lon: float


class TravelTimeResult(BaseModel):
    """Travel time calculation result."""

    destination: LocationCoordinate
    travel_time_seconds: int
    travel_time_minutes: float


class TravelTimeRequest(BaseModel):
    """Request to calculate travel times."""

    property_id: int
    destinations: List[LocationCoordinate]


class TravelTimeResponse(BaseModel):
    """Response with travel times to multiple destinations."""

    property_id: int
    origin_lat: float
    origin_lon: float
    results: List[TravelTimeResult]


class DistanceResult(BaseModel):
    """Distance calculation result."""

    destination: LocationCoordinate
    distance_meters: int
    distance_km: float


class DistanceRequest(BaseModel):
    """Request to calculate distances."""

    property_id: int
    destinations: List[LocationCoordinate]


class DistanceResponse(BaseModel):
    """Response with distances to multiple destinations."""

    property_id: int
    origin_lat: float
    origin_lon: float
    results: List[DistanceResult]


# ============================================================================
# Geocoding Service Schemas
# ============================================================================


class GeocodeRequest(BaseModel):
    """Request to geocode an address to coordinates."""

    address: str  # Address string in any format


class GeocodeResponse(BaseModel):
    """Response with geocoded coordinates."""

    latitude: float
    longitude: float
    address: str  # Echo back the input address
