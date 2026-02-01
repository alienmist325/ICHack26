"""
Personalized feed based on user preferences and starred properties.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
import sqlite3
import json

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import User
from app import crud

router = APIRouter(prefix="/feed", tags=["personalization"])


def _extract_preferences_from_stars(user_id: int, db: sqlite3.Connection) -> dict:
    """Learn user preferences from their starred properties."""
    cursor = db.cursor()

    # Get all starred properties by user
    cursor.execute(
        """
        SELECT p.price, p.bedrooms, p.property_type, p.outcode
        FROM property_bookmarks pb
        JOIN properties p ON pb.property_id = p.id
        WHERE pb.user_id = ? AND pb.is_starred = 1
        """,
        (user_id,),
    )
    starred = cursor.fetchall()

    if not starred:
        return {}

    # Calculate statistics from starred properties
    prices = [p["price"] for p in starred if p["price"]]
    bedrooms = [p["bedrooms"] for p in starred if p["bedrooms"]]
    property_types = {}
    outcodes = {}

    for p in starred:
        if p["property_type"]:
            property_types[p["property_type"]] = (
                property_types.get(p["property_type"], 0) + 1
            )
        if p["outcode"]:
            outcodes[p["outcode"]] = outcodes.get(p["outcode"], 0) + 1

    preferences = {}

    # Price preferences (average of starred)
    if prices:
        avg_price = sum(prices) / len(prices)
        preferences["preferred_price_min"] = int(avg_price * 0.7)  # 70% of average
        preferences["preferred_price_max"] = int(avg_price * 1.3)  # 130% of average

    # Bedroom preferences
    if bedrooms:
        avg_bedrooms = sum(bedrooms) / len(bedrooms)
        preferences["preferred_bedrooms_min"] = max(1, int(avg_bedrooms))

    # Property types (most common starred types)
    if property_types:
        sorted_types = sorted(property_types.items(), key=lambda x: x[1], reverse=True)
        preferences["preferred_property_types"] = [
            t[0] for t in sorted_types[:3]
        ]  # Top 3

    # Locations (most common starred locations)
    if outcodes:
        sorted_outcodes = sorted(outcodes.items(), key=lambda x: x[1], reverse=True)
        preferences["preferred_locations"] = [
            o[0] for o in sorted_outcodes[:5]
        ]  # Top 5

    return preferences


@router.get("/personalized", response_model=dict)
async def get_personalized_feed(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Get personalized property feed based on user preferences and starred properties.
    Learns from user's bio and starred properties to recommend relevant listings.
    """
    cursor = db.cursor()

    # Get user profile
    cursor.execute(
        """
        SELECT bio, dream_property_description, preferred_price_min, preferred_price_max,
               preferred_bedrooms_min, preferred_property_types, preferred_locations
        FROM user_profiles
        WHERE user_id = ?
        """,
        (current_user.id,),
    )
    profile = cursor.fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    profile_dict = dict(profile)

    # Deserialize JSON fields
    if profile_dict.get("preferred_property_types"):
        profile_dict["preferred_property_types"] = json.loads(
            profile_dict["preferred_property_types"]
        )
    if profile_dict.get("preferred_locations"):
        profile_dict["preferred_locations"] = json.loads(
            profile_dict["preferred_locations"]
        )

    # Learn from starred properties
    learned_prefs = _extract_preferences_from_stars(current_user.id, db)

    # Merge explicit preferences with learned ones
    min_price = profile_dict.get("preferred_price_min") or learned_prefs.get(
        "preferred_price_min"
    )
    max_price = profile_dict.get("preferred_price_max") or learned_prefs.get(
        "preferred_price_max"
    )
    min_bedrooms = profile_dict.get("preferred_bedrooms_min") or learned_prefs.get(
        "preferred_bedrooms_min"
    )
    property_types = profile_dict.get("preferred_property_types") or learned_prefs.get(
        "preferred_property_types"
    )
    locations = profile_dict.get("preferred_locations") or learned_prefs.get(
        "preferred_locations"
    )

    # Build query with preferences
    from app.schemas import PropertyFilters

    filters = PropertyFilters(
        min_price=min_price,
        max_price=max_price,
        min_bedrooms=min_bedrooms,
    )

    # Fetch base properties matching preferences
    properties, total_count = crud.get_properties_with_scores(
        filters=filters,
        limit=limit * 3,  # Get more to filter by property type/location
        offset=offset,
    )

    # Filter by property types if specified
    if property_types:
        properties = [p for p in properties if p.property_type in property_types]

    # Filter by locations if specified
    if locations:
        properties = [p for p in properties if p.outcode in locations]

    # Limit to requested amount
    properties = properties[:limit]

    # Score properties based on matching preferences
    for prop in properties:
        prop.score = _calculate_preference_score(prop, profile_dict, learned_prefs)

    # Sort by preference score (descending) then by rating score
    properties.sort(key=lambda p: (p.score, p.total_votes), reverse=True)

    return {
        "properties": properties,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "user_preferences": {
            "explicit": {
                "bio": profile_dict.get("bio"),
                "dream_property": profile_dict.get("dream_property_description"),
                "min_price": profile_dict.get("preferred_price_min"),
                "max_price": profile_dict.get("preferred_price_max"),
                "min_bedrooms": profile_dict.get("preferred_bedrooms_min"),
                "property_types": profile_dict.get("preferred_property_types"),
                "locations": profile_dict.get("preferred_locations"),
            },
            "learned_from_stars": learned_prefs,
        },
    }


def _calculate_preference_score(
    property_obj, profile: dict, learned_prefs: dict
) -> float:
    """
    Calculate a score (0-100) for how well a property matches user preferences.
    Based on multiple factors: price, bedrooms, type, location.
    """
    score = 50.0  # Base score

    # Price match (±20 points)
    min_price = profile.get("preferred_price_min") or learned_prefs.get(
        "preferred_price_min"
    )
    max_price = profile.get("preferred_price_max") or learned_prefs.get(
        "preferred_price_max"
    )

    if min_price and max_price and property_obj.price:
        mid_price = (min_price + max_price) / 2
        if min_price <= property_obj.price <= max_price:
            # Perfect match
            score += 20
        else:
            # Partial match based on distance
            distance = abs(property_obj.price - mid_price)
            max_distance = max_price - min_price
            if max_distance > 0:
                match_pct = 1 - (distance / (max_distance * 2))
                score += max(0, match_pct * 20)

    # Bedroom match (±15 points)
    min_bedrooms = profile.get("preferred_bedrooms_min") or learned_prefs.get(
        "preferred_bedrooms_min"
    )
    if min_bedrooms and property_obj.bedrooms and property_obj.bedrooms >= min_bedrooms:
        score += 15

    # Property type match (±20 points)
    property_types = profile.get("preferred_property_types") or learned_prefs.get(
        "preferred_property_types", []
    )
    if property_types and property_obj.property_type in property_types:
        score += 20

    # Location match (±20 points)
    locations = profile.get("preferred_locations") or learned_prefs.get(
        "preferred_locations", []
    )
    if locations and property_obj.outcode in locations:
        score += 20

    # Normalize to 0-100
    return min(100.0, max(0.0, score))


@router.get("/recommendations", response_model=List[dict])
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Get AI-style recommendations based on similar properties to user's stars.
    """
    cursor = db.cursor()

    # Get user's starred properties
    cursor.execute(
        """
        SELECT p.id, p.price, p.bedrooms, p.property_type, p.outcode
        FROM property_bookmarks pb
        JOIN properties p ON pb.property_id = p.id
        WHERE pb.user_id = ? AND pb.is_starred = 1
        ORDER BY pb.created_at DESC
        LIMIT 5
        """,
        (current_user.id,),
    )
    starred = cursor.fetchall()

    if not starred:
        # Return popular properties if user hasn't starred any
        cursor.execute(
            """
            SELECT id FROM ratings
            WHERE vote_type = 'star'
            GROUP BY property_id
            ORDER BY COUNT(*) DESC
            LIMIT 10
            """
        )
        return [{"property_id": row["property_id"]} for row in cursor.fetchall()]

    recommendations = []
    seen_ids = set()

    # For each starred property, find similar ones
    for starred_prop in starred:
        cursor.execute(
            """
            SELECT id FROM properties
            WHERE id != ?
            AND ABS(price - ?) < (? * 0.2)
            AND (bedrooms = ? OR bedrooms = ? + 1 OR bedrooms = ? - 1)
            AND property_type = ?
            AND id NOT IN (
                SELECT property_id FROM property_bookmarks
                WHERE user_id = ?
            )
            LIMIT 5
            """,
            (
                starred_prop["id"],
                starred_prop["price"],
                starred_prop["price"],
                starred_prop["bedrooms"],
                starred_prop["bedrooms"],
                starred_prop["bedrooms"],
                starred_prop["property_type"],
                current_user.id,
            ),
        )

        for row in cursor.fetchall():
            prop_id = row["id"]
            if prop_id not in seen_ids:
                seen_ids.add(prop_id)
                recommendations.append({"property_id": prop_id})

    return recommendations[:20]  # Return top 20 recommendations
