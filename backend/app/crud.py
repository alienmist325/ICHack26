# backend/app/crud.py
import json
import math
import sqlite3
from datetime import datetime, timedelta
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

# ============================================================================
# Property CRUD operations
# ============================================================================


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

        now = datetime.utcnow().isoformat()
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
        data["last_scraped_at"] = datetime.utcnow().isoformat()

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
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
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

    now = datetime.utcnow()
    upvotes = 0
    downvotes = 0
    weighted_score = 0.0

    for rating in ratings:
        # Calculate age of the vote in days
        voted_at = datetime.fromisoformat(rating.voted_at)
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
) -> List[PropertyWithScore]:
    """
    Get properties with their rating scores.

    Note: This is not optimized for large datasets. For production use,
    consider materializing scores in the database.
    """
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
    return properties_with_scores[:limit]


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
