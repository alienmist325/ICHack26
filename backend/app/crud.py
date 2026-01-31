# backend/app/crud.py
import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.database import get_db
from app.schemas import (
    Property,
    PropertyCreate,
    PropertyFilters,
    PropertyUpdate,
    PropertyWithScore,
    Rating,
    RatingCreate,
    VoteType,
)

# Type hint for RightmoveProperty to avoid circular imports
RightmoveProperty = Any

# ============================================================================
# Property CRUD operations
# ============================================================================


def rightmove_property_to_create(
    rightmove_prop: RightmoveProperty,
) -> PropertyCreate:
    """Convert a RightmoveProperty to PropertyCreate for database storage.

    Maps Rightmove API fields to our database schema.
    """
    return PropertyCreate(
        rightmove_id=rightmove_prop.id,
        listing_title=rightmove_prop.title,
        listing_url=rightmove_prop.url,
        full_address=rightmove_prop.displayAddress,
        latitude=rightmove_prop.coordinates.latitude,
        longitude=rightmove_prop.coordinates.longitude,
        property_type=rightmove_prop.propertyType,
        listing_type=rightmove_prop.type,
        bedrooms=rightmove_prop.bedrooms,
        bathrooms=rightmove_prop.bathrooms,
        size=f"{rightmove_prop.sizeSqFeetMin}-{rightmove_prop.sizeSqFeetMax} sq ft"
        if (rightmove_prop.sizeSqFeetMin or rightmove_prop.sizeSqFeetMax)
        else None,
        price=float(rightmove_prop.price),
        text_description=rightmove_prop.description,
        images=rightmove_prop.images,
        agent_name=rightmove_prop.agent,
        agent_phone=rightmove_prop.agentPhone,
        agent_profile_url=rightmove_prop.agentProfileUrl,
        display_status=rightmove_prop.displayStatus
        if rightmove_prop.displayStatus
        else None,
        listing_update_reason=rightmove_prop.listingUpdateReason,
        first_visible_date=rightmove_prop.firstVisibleDate.isoformat(),
        listing_update_date=rightmove_prop.listingUpdateDate.isoformat(),
    )


def _serialize_json_field(value: Any) -> Optional[str]:
    """Serialize a field to JSON if it's not None."""
    if value is None:
        return None
    return json.dumps(value)


def _deserialize_json_field(value: Optional[str]) -> Any:
    """Deserialize a JSON field if it's not None."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _row_to_property(row: sqlite3.Row) -> Property:
    """Convert a database row to a Property schema."""
    data = dict(row)

    # Deserialize JSON fields
    json_fields = [
        "amenities",
        "price_history",
        "images",
        "floorplans",
        "brochures",
        "epc",
        "nearest_schools",
    ]
    for field in json_fields:
        if field in data:
            data[field] = _deserialize_json_field(data[field])

    return Property(**data)


def create_property(property_data: PropertyCreate) -> Property:
    """Create a new property in the database."""
    with get_db() as conn:
        cursor = conn.cursor()

        now = datetime.now(timezone.utc).isoformat()
        data = property_data.model_dump()

        # Serialize JSON fields
        json_fields = [
            "amenities",
            "price_history",
            "images",
            "floorplans",
            "brochures",
            "epc",
            "nearest_schools",
        ]
        for field in json_fields:
            if field in data:
                data[field] = _serialize_json_field(data[field])

        # Add timestamps
        data["first_scraped_at"] = now
        data["last_scraped_at"] = now

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])

        cursor.execute(
            f"INSERT INTO properties ({columns}) VALUES ({placeholders})",
            list(data.values()),
        )

        property_id = cursor.lastrowid
        cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
        row = cursor.fetchone()

        return _row_to_property(row)


def get_property_by_id(property_id: int) -> Optional[Property]:
    """Get a property by its database ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM properties WHERE id = ?", (property_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_property(row)


def get_property_by_rightmove_id(rightmove_id: str) -> Optional[Property]:
    """Get a property by its Rightmove ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM properties WHERE rightmove_id = ?", (rightmove_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_property(row)


def update_property(
    property_id: int, property_data: PropertyUpdate
) -> Optional[Property]:
    """Update an existing property."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get only the fields that were actually set
        data = property_data.model_dump(exclude_unset=True)

        if not data:
            # No fields to update
            return get_property_by_id(property_id)

        # Serialize JSON fields
        json_fields = [
            "amenities",
            "price_history",
            "images",
            "floorplans",
            "brochures",
            "epc",
            "nearest_schools",
        ]
        for field in json_fields:
            if field in data:
                data[field] = _serialize_json_field(data[field])

        # Update last_scraped_at
        data["last_scraped_at"] = datetime.now(timezone.utc).isoformat()

        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = list(data.values()) + [property_id]

        cursor.execute(f"UPDATE properties SET {set_clause} WHERE id = ?", values)

        if cursor.rowcount == 0:
            return None

        return get_property_by_id(property_id)


def upsert_property(property_data: PropertyCreate) -> tuple[Property, bool]:
    """
    Create or update a property based on rightmove_id.
    Returns (Property, created) where created is True if new property was created.
    """
    existing = get_property_by_rightmove_id(property_data.rightmove_id)

    if existing is None:
        return create_property(property_data), True

    # Convert PropertyCreate to PropertyUpdate
    update_data = PropertyUpdate(**property_data.model_dump())
    updated = update_property(existing.id, update_data)
    if updated is None:
        # Should not happen in normal operation, but handle it
        return existing, False
    return updated, False


def soft_delete_property(property_id: int) -> bool:
    """Soft delete a property by setting removed=True."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE properties SET removed = 1 WHERE id = ?", (property_id,))
        return cursor.rowcount > 0


def get_properties(
    filters: Optional[PropertyFilters] = None, limit: int = 100, offset: int = 0
) -> List[Property]:
    """Get properties with optional filters."""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM properties WHERE 1=1"
        params: List[Any] = []

        if filters:
            if filters.search_query is not None:
                search = filters.search_query
                query += " AND (listing_title LIKE ? OR full_address LIKE ? OR text_description LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

            if filters.min_price is not None:
                query += " AND price >= ?"
                params.append(filters.min_price)

            if filters.max_price is not None:
                query += " AND price <= ?"
                params.append(filters.max_price)

            if filters.min_bedrooms is not None:
                query += " AND bedrooms >= ?"
                params.append(filters.min_bedrooms)

            if filters.max_bedrooms is not None:
                query += " AND bedrooms <= ?"
                params.append(filters.max_bedrooms)

            if filters.property_type is not None:
                query += " AND property_type = ?"
                params.append(filters.property_type)

            if filters.furnishing_type is not None:
                query += " AND furnishing_type = ?"
                params.append(filters.furnishing_type)

            if filters.outcode is not None:
                query += " AND outcode = ?"
                params.append(filters.outcode)

            query += " AND removed = ?"
            params.append(1 if filters.removed else 0)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [_row_to_property(row) for row in rows]


# ============================================================================
# Rating CRUD operations
# ============================================================================


def create_rating(rating_data: RatingCreate) -> Rating:
    """Create a new rating for a property."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO ratings (property_id, vote_type)
            VALUES (?, ?)
            """,
            (rating_data.property_id, rating_data.vote_type.value),
        )

        rating_id = cursor.lastrowid
        cursor.execute("SELECT * FROM ratings WHERE id = ?", (rating_id,))
        row = cursor.fetchone()

        return Rating(**dict(row))


def get_ratings_for_property(
    property_id: int, days: Optional[int] = None
) -> List[Rating]:
    """
    Get all ratings for a property.

    Args:
        property_id: The property ID
        days: If provided, only return ratings from the last N days
    """
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM ratings WHERE property_id = ?"
        params: List[Any] = [property_id]

        if days is not None:
            cutoff_date = (
                datetime.now(timezone.utc) - timedelta(days=days)
            ).isoformat()
            query += " AND voted_at >= ?"
            params.append(cutoff_date)

        query += " ORDER BY voted_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [Rating(**dict(row)) for row in rows]


def calculate_property_score(
    property_id: int, decay_days: float = 30.0
) -> Dict[str, Any]:
    """
    Calculate a time-weighted score for a property.

    More recent votes are weighted more heavily. The weight decays exponentially
    based on the age of the vote.

    Args:
        property_id: The property ID
        decay_days: The half-life for vote decay in days

    Returns:
        Dict with upvotes, downvotes, total_votes, and weighted score
    """
    ratings = get_ratings_for_property(property_id)

    if not ratings:
        return {"upvotes": 0, "downvotes": 0, "total_votes": 0, "score": 0.0}

    now = datetime.now(timezone.utc)
    upvotes = 0
    downvotes = 0
    weighted_score = 0.0

    for rating in ratings:
        # Calculate age of the vote in days
        voted_at = datetime.fromisoformat(rating.voted_at)
        # Make naive datetime offset-aware if it isn't already
        if voted_at.tzinfo is None:
            voted_at = voted_at.replace(tzinfo=timezone.utc)
        age_days = (now - voted_at).total_seconds() / 86400

        # Exponential decay: weight = 0.5 ^ (age_days / decay_days)
        weight = math.pow(0.5, age_days / decay_days)

        if rating.vote_type == VoteType.UPVOTE:
            upvotes += 1
            weighted_score += weight
        else:
            downvotes += 1
            weighted_score -= weight

    return {
        "upvotes": upvotes,
        "downvotes": downvotes,
        "total_votes": upvotes + downvotes,
        "score": weighted_score,
    }


def get_property_with_score(property_id: int) -> Optional[PropertyWithScore]:
    """Get a property with its calculated rating score."""
    property_obj = get_property_by_id(property_id)

    if property_obj is None:
        return None

    score_data = calculate_property_score(property_id)

    return PropertyWithScore(
        **property_obj.model_dump(),
        upvotes=score_data["upvotes"],
        downvotes=score_data["downvotes"],
        total_votes=score_data["total_votes"],
        score=score_data["score"],
    )


def get_properties_with_scores(
    filters: Optional[PropertyFilters] = None,
    limit: int = 100,
    offset: int = 0,
    min_score: Optional[float] = None,
    search_query: Optional[str] = None,
) -> tuple[List[PropertyWithScore], int]:
    """
    Get properties with their rating scores.

    Returns a tuple of (properties_with_scores, total_count).

    Note: This is not optimized for large datasets. For production use,
    consider materializing scores in the database.
    """
    # If search_query is provided, add it to filters
    if search_query is not None:
        if filters is None:
            filters = PropertyFilters(search_query=search_query)
        else:
            filters.search_query = search_query

    # Get total count before limiting
    total_count = get_property_count(filters)

    properties = get_properties(
        filters, limit=limit * 2, offset=offset
    )  # Get more to account for filtering

    properties_with_scores = []
    for prop in properties:
        prop_with_score = get_property_with_score(prop.id)
        if prop_with_score:
            if min_score is None or prop_with_score.score >= min_score:
                properties_with_scores.append(prop_with_score)

    # Sort by score (highest first) and apply limit
    properties_with_scores.sort(key=lambda p: p.score, reverse=True)
    return properties_with_scores[:limit], total_count


# ============================================================================
# Utility functions
# ============================================================================


def get_property_count(filters: Optional[PropertyFilters] = None) -> int:
    """Get the total count of properties matching filters."""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT COUNT(*) FROM properties WHERE 1=1"
        params: List[Any] = []

        if filters:
            if filters.search_query is not None:
                search = filters.search_query
                query += " AND (listing_title LIKE ? OR full_address LIKE ? OR text_description LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

            if filters.min_price is not None:
                query += " AND price >= ?"
                params.append(filters.min_price)

            if filters.max_price is not None:
                query += " AND price <= ?"
                params.append(filters.max_price)

            if filters.min_bedrooms is not None:
                query += " AND bedrooms >= ?"
                params.append(filters.min_bedrooms)

            if filters.max_bedrooms is not None:
                query += " AND bedrooms <= ?"
                params.append(filters.max_bedrooms)

            if filters.property_type is not None:
                query += " AND property_type = ?"
                params.append(filters.property_type)

            if filters.furnishing_type is not None:
                query += " AND furnishing_type = ?"
                params.append(filters.furnishing_type)

            if filters.outcode is not None:
                query += " AND outcode = ?"
                params.append(filters.outcode)

            query += " AND removed = ?"
            params.append(1 if filters.removed else 0)

        cursor.execute(query, params)
        return cursor.fetchone()[0]


def get_unique_outcodes() -> List[str]:
    """Get a list of all unique outcodes in the database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT outcode FROM properties WHERE outcode IS NOT NULL ORDER BY outcode"
        )
        return [row[0] for row in cursor.fetchall()]


def get_unique_property_types() -> List[str]:
    """Get a list of all unique property types in the database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT property_type FROM properties WHERE property_type IS NOT NULL ORDER BY property_type"
        )
        return [row[0] for row in cursor.fetchall()]


# ============================================================================
# Routing/Isochrone Query Functions
# ============================================================================


def get_properties_by_ids(property_ids: List[int]) -> List[Property]:
    """
    Get multiple properties by their IDs.

    Args:
        property_ids: List of property IDs to retrieve

    Returns:
        List of Property objects
    """
    if not property_ids:
        return []

    with get_db() as conn:
        cursor = conn.cursor()
        placeholders = ",".join(["?" for _ in property_ids])
        cursor.execute(
            f"SELECT * FROM properties WHERE id IN ({placeholders})", property_ids
        )
        return [_row_to_property(row) for row in cursor.fetchall()]


def get_all_properties_with_coordinates() -> List[Dict[str, Any]]:
    """
    Get all properties with their ID and coordinates.

    Used for point-in-polygon queries against isochrone polygons.

    Returns:
        List of dicts with 'id', 'latitude', 'longitude' keys
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, latitude, longitude
            FROM properties
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND removed = 0
            """
        )
        return [
            {
                "id": row[0],
                "latitude": row[1],
                "longitude": row[2],
            }
            for row in cursor.fetchall()
        ]


# ============================================================================
# Verification CRUD operations
# ============================================================================


def get_property_for_verification(property_id: int) -> Optional[Dict[str, Any]]:
    """
    Get property details needed for verification.

    Args:
        property_id: Property ID

    Returns:
        Property dict with address and agent_phone, or None if not found
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, latitude, longitude
            FROM properties
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND removed = 0
            """
        )
        return [
            {
                "id": row[0],
                "latitude": row[1],
                "longitude": row[2],
            }
            for row in cursor.fetchall()
        ]


def get_property_for_verification(property_id: int) -> Optional[Dict[str, Any]]:
    """
    Get property details needed for verification.

    Args:
        property_id: Property ID

    Returns:
        Property dict with address and agent_phone, or None if not found
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, full_address, agent_phone, agent_name
            FROM properties
            WHERE id = ? AND agent_phone IS NOT NULL AND agent_phone != ''
            """,
            (property_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "address": row[1],
                "agent_phone": row[2],
                "agent_name": row[3],
            }
        return None


def create_verification_log(
    property_id: int,
    agent_phone: str,
    verification_status: str,
    call_timestamp: Optional[str] = None,
    call_duration_seconds: Optional[int] = None,
    agent_response: Optional[str] = None,
    confidence_score: Optional[float] = None,
    notes: Optional[str] = None,
    error_message: Optional[str] = None,
) -> Optional[int]:
    """
    Create a verification log entry.

    Args:
        property_id: Property ID
        agent_phone: Phone number called
        verification_status: Status (available, sold, rented, unclear, failed, etc.)
        call_timestamp: When the call was made
        call_duration_seconds: Call duration
        agent_response: Agent's response summary
        confidence_score: Confidence in determination (0.0-1.0)
        notes: Additional notes
        error_message: Error message if call failed

    Returns:
        verification_logs table row ID or None
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO verification_logs (
                property_id, agent_phone, verification_status,
                call_timestamp, call_duration_seconds, agent_response,
                confidence_score, notes, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                property_id,
                agent_phone,
                verification_status,
                call_timestamp,
                call_duration_seconds,
                agent_response,
                confidence_score,
                notes,
                error_message,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_property_verification_status(
    property_id: int,
    verification_status: str,
    verification_notes: Optional[str] = None,
) -> bool:
    """
    Update property verification status.

    Args:
        property_id: Property ID
        verification_status: New status
        verification_notes: Optional notes

    Returns:
        True if updated, False if property not found
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE properties
            SET verification_status = ?, last_verified_at = ?, verification_notes = ?
            WHERE id = ?
            """,
            (
                verification_status,
                datetime.utcnow().isoformat(),
                verification_notes,
                property_id,
            ),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_verification_status(property_id: int) -> Optional[Dict[str, Any]]:
    """
    Get property verification status.

    Args:
        property_id: Property ID

    Returns:
        Verification status dict or None if not found
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, verification_status, last_verified_at, verification_notes
            FROM properties
            WHERE id = ?
            """,
            (property_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "property_id": row[0],
                "verification_status": row[1],
                "last_verified_at": row[2],
                "verification_notes": row[3],
            }
        return None


def get_verification_log(property_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the latest verification log for a property.

    Args:
        property_id: Property ID

    Returns:
        Latest verification log or None if not found
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id, property_id, call_timestamp, call_duration_seconds,
                agent_phone, agent_response, verification_status,
                confidence_score, notes, error_message, created_at
            FROM verification_logs
            WHERE property_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (property_id,),
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "property_id": row[1],
                "call_timestamp": row[2],
                "call_duration_seconds": row[3],
                "agent_phone": row[4],
                "agent_response": row[5],
                "verification_status": row[6],
                "confidence_score": row[7],
                "notes": row[8],
                "error_message": row[9],
                "created_at": row[10],
            }
        return None


def get_unverified_properties(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get properties that haven't been verified yet.

    Args:
        limit: Maximum number to return

    Returns:
        List of unverified properties
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, full_address, agent_phone, agent_name
            FROM properties
            WHERE (verification_status = 'pending' OR verification_status IS NULL)
            AND agent_phone IS NOT NULL AND agent_phone != ''
            ORDER BY last_scraped_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [
            {
                "id": row[0],
                "address": row[1],
                "agent_phone": row[2],
                "agent_name": row[3],
            }
            for row in cursor.fetchall()
        ]


def get_properties_with_isochrone_and_filters(
    isochrone_property_ids: List[int],
    filters: Optional[PropertyFilters] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[List[PropertyWithScore], int]:
    """
    Get properties that are both inside isochrone AND match other filters.

    This function:
    1. Takes property IDs from an isochrone query
    2. Applies additional filters (price, bedrooms, etc.)
    3. Calculates scores for matched properties
    4. Returns paginated results

    Args:
        isochrone_property_ids: Property IDs inside the isochrone polygon
        filters: Optional additional PropertyFilters to apply
        limit: Maximum number of results to return
        offset: Pagination offset

    Returns:
        Tuple of (properties_with_scores, total_count)
    """
    if not isochrone_property_ids:
        return [], 0

    with get_db() as conn:
        cursor = conn.cursor()

        # Build base query: must be in isochrone results
        placeholders = ",".join(["?" for _ in isochrone_property_ids])
        query = f"SELECT * FROM properties WHERE id IN ({placeholders})"
        params: List[Any] = list(isochrone_property_ids)

        # Apply additional filters if provided
        if filters:
            if filters.search_query is not None:
                search = filters.search_query
                query += " AND (listing_title LIKE ? OR full_address LIKE ? OR text_description LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

            if filters.min_price is not None:
                query += " AND price >= ?"
                params.append(filters.min_price)

            if filters.max_price is not None:
                query += " AND price <= ?"
                params.append(filters.max_price)

            if filters.min_bedrooms is not None:
                query += " AND bedrooms >= ?"
                params.append(filters.min_bedrooms)

            if filters.max_bedrooms is not None:
                query += " AND bedrooms <= ?"
                params.append(filters.max_bedrooms)

            if filters.property_type is not None:
                query += " AND property_type = ?"
                params.append(filters.property_type)

            if filters.furnishing_type is not None:
                query += " AND furnishing_type = ?"
                params.append(filters.furnishing_type)

            if filters.outcode is not None:
                query += " AND outcode = ?"
                params.append(filters.outcode)

        query += " AND removed = 0"  # Always exclude removed properties
        query += " ORDER BY created_at DESC"

        # Get total count before pagination
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # Get paginated results
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        properties = [_row_to_property(row) for row in cursor.fetchall()]

    # Calculate scores for each property
    properties_with_scores = []
    for prop in properties:
        prop_with_score = get_property_with_score(prop.id)
        if prop_with_score:
            min_score = filters.min_score if filters else None
            if min_score is None or prop_with_score.score >= min_score:
                properties_with_scores.append(prop_with_score)

    # Sort by score (highest first)
    properties_with_scores.sort(key=lambda p: p.score, reverse=True)

    return properties_with_scores[:limit], total_count


def get_verification_statistics() -> Dict[str, Any]:
    """
    Get verification statistics.

    Returns:
        Stats dict with counts by status
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT verification_status, COUNT(*) as count
            FROM properties
            GROUP BY verification_status
            ORDER BY count DESC
            """
        )
        stats = {row[0] or "unknown": row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM verification_logs")
        total_verifications = cursor.fetchone()[0]

        return {
            "by_status": stats,
            "total_verifications": total_verifications,
        }
