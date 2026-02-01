"""
User profile and preferences routes.
"""

from fastapi import APIRouter, HTTPException, Depends
import json
import sqlite3

from app.database import get_db
from app.schemas import (
    User,
    UserProfile,
    UserProfileResponse,
    NotificationSettings,
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get current user's profile and preferences."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, user_id, bio, dream_property_description,
               preferred_price_min, preferred_price_max, preferred_bedrooms_min,
               preferred_property_types, preferred_locations,
               notification_viewing_reminder_days, notification_email_enabled,
               notification_in_app_enabled, notification_feed_changes_enabled,
               created_at, updated_at
        FROM user_profiles
        WHERE user_id = ?
        """,
        (current_user.id,),
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")

    row_dict = dict(row)
    # Deserialize JSON fields
    if row_dict.get("preferred_property_types"):
        row_dict["preferred_property_types"] = json.loads(
            row_dict["preferred_property_types"]
        )
    if row_dict.get("preferred_locations"):
        row_dict["preferred_locations"] = json.loads(row_dict["preferred_locations"])

    return UserProfileResponse(**row_dict)


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfile,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Update current user's profile and preferences."""
    cursor = db.cursor()

    # Prepare updates
    updates = {}
    if profile_data.bio is not None:
        updates["bio"] = profile_data.bio
    if profile_data.dream_property_description is not None:
        updates["dream_property_description"] = profile_data.dream_property_description
    if profile_data.preferred_price_min is not None:
        updates["preferred_price_min"] = profile_data.preferred_price_min
    if profile_data.preferred_price_max is not None:
        updates["preferred_price_max"] = profile_data.preferred_price_max
    if profile_data.preferred_bedrooms_min is not None:
        updates["preferred_bedrooms_min"] = profile_data.preferred_bedrooms_min
    if profile_data.preferred_property_types is not None:
        updates["preferred_property_types"] = json.dumps(
            profile_data.preferred_property_types
        )
    if profile_data.preferred_locations is not None:
        updates["preferred_locations"] = json.dumps(profile_data.preferred_locations)

    if not updates:
        # Return current profile
        return await get_user_profile(current_user, db)

    # Build UPDATE query
    set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [current_user.id]

    cursor.execute(
        f"UPDATE user_profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        values,
    )
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Return updated profile
    return await get_user_profile(current_user, db)


@router.get("/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get user's notification settings."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT notification_viewing_reminder_days, notification_email_enabled,
               notification_in_app_enabled, notification_feed_changes_enabled
        FROM user_profiles
        WHERE user_id = ?
        """,
        (current_user.id,),
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")

    return NotificationSettings(**dict(row))


@router.put("/notifications", response_model=NotificationSettings)
async def update_notification_settings(
    settings: NotificationSettings,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Update user's notification settings."""
    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE user_profiles
        SET notification_viewing_reminder_days = ?,
            notification_email_enabled = ?,
            notification_in_app_enabled = ?,
            notification_feed_changes_enabled = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """,
        (
            settings.notification_viewing_reminder_days,
            settings.notification_email_enabled,
            settings.notification_in_app_enabled,
            settings.notification_feed_changes_enabled,
            current_user.id,
        ),
    )
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Return updated settings
    return await get_notification_settings(current_user, db)


@router.delete("", status_code=204)
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Delete current user account (soft delete)."""
    cursor = db.cursor()
    cursor.execute(
        "UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (current_user.id,),
    )
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return None
