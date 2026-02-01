"""
User profile and preferences routes.
"""

import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import (
    NotificationSettings,
    User,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UserResponse)
async def get_user(
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get current user's preferences."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, email, is_active, bio, dream_property_description,
               preferred_price_min, preferred_price_max, preferred_bedrooms_min,
               preferred_property_types, preferred_locations,
               notification_viewing_reminder_days, notification_email_enabled,
               notification_in_app_enabled, notification_feed_changes_enabled,
               created_at, updated_at
        FROM users
        WHERE id = ?
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

    return UserResponse(**row_dict)


@router.put("/", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Update current user's profile and preferences."""
    cursor = db.cursor()

    # Prepare updates
    updates = {}
    if user_data.bio is not None:
        updates["bio"] = user_data.bio
    if user_data.dream_property_description is not None:
        updates["dream_property_description"] = user_data.dream_property_description
    if user_data.preferred_price_min is not None:
        updates["preferred_price_min"] = user_data.preferred_price_min
    if user_data.preferred_price_max is not None:
        updates["preferred_price_max"] = user_data.preferred_price_max
    if user_data.preferred_bedrooms_min is not None:
        updates["preferred_bedrooms_min"] = user_data.preferred_bedrooms_min
    if user_data.preferred_property_types is not None:
        updates["preferred_property_types"] = json.dumps(
            user_data.preferred_property_types
        )
    if user_data.preferred_locations is not None:
        updates["preferred_locations"] = json.dumps(user_data.preferred_locations)
    if user_data.notification_viewing_reminder_days is not None:
        updates["notification_viewing_reminder_days"] = (
            user_data.notification_viewing_reminder_days
        )
    if user_data.notification_email_enabled is not None:
        updates["notification_email_enabled"] = user_data.notification_email_enabled
    if user_data.notification_in_app_enabled is not None:
        updates["notification_in_app_enabled"] = user_data.notification_in_app_enabled
    if user_data.notification_feed_changes_enabled is not None:
        updates["notification_feed_changes_enabled"] = (
            user_data.notification_feed_changes_enabled
        )

    if not updates:
        # Return current profile
        return await get_user(current_user, db)

    # Build UPDATE query
    set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [current_user.id]

    cursor.execute(
        f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values,
    )
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Return updated profile
    return await get_user(current_user, db)


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
        FROM users
        WHERE id = ?
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
        UPDATE users
        SET notification_viewing_reminder_days = ?,
            notification_email_enabled = ?,
            notification_in_app_enabled = ?,
            notification_feed_changes_enabled = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
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
