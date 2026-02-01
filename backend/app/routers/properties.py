"""
Property-related endpoints for bookmarks, status, comments, and ratings.
"""

import sqlite3
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import (
    PropertyComment,
    PropertyCommentResponse,
    PropertyStatusResponse,
    PropertyStatusUpdate,
    User,
)

router = APIRouter(prefix="/properties", tags=["properties"])


# ============================================================================
# Property Bookmarks (Stars)
# ============================================================================


@router.post("/{property_id}/star", status_code=201)
async def star_property(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Star/bookmark a property."""
    cursor = db.cursor()

    # Verify property exists
    cursor.execute("SELECT id FROM properties WHERE id = ?", (property_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Property not found")

    # Try to insert or update bookmark
    cursor.execute(
        """
        INSERT OR REPLACE INTO property_bookmarks (user_id, property_id, is_starred)
        VALUES (?, ?, 1)
        """,
        (current_user.id, property_id),
    )
    db.commit()

    return {"status": "starred"}


@router.delete("/{property_id}/star", status_code=204)
async def unstar_property(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Unstar/unbookmark a property."""
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM property_bookmarks WHERE user_id = ? AND property_id = ?",
        (current_user.id, property_id),
    )
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    return None


@router.get("/starred", response_model=List[int])
async def get_starred_properties(
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get list of properties starred by current user."""
    cursor = db.cursor()
    cursor.execute(
        "SELECT property_id FROM property_bookmarks WHERE user_id = ? AND is_starred = 1",
        (current_user.id,),
    )
    rows = cursor.fetchall()
    return [row["property_id"] for row in rows]


# ============================================================================
# Property Status (Viewing, Offer, Accepted)
# ============================================================================


@router.post(
    "/{property_id}/status", response_model=PropertyStatusResponse, status_code=201
)
async def set_property_status(
    property_id: int,
    status_update: PropertyStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Update property status (interested, viewing, offer, accepted)."""
    cursor = db.cursor()

    # Verify property exists
    cursor.execute("SELECT id FROM properties WHERE id = ?", (property_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Property not found")

    # Insert or replace status
    cursor.execute(
        """
        INSERT OR REPLACE INTO property_status (user_id, property_id, status, status_updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (current_user.id, property_id, status_update.status.value),
    )
    db.commit()

    # If comment provided, add it
    if status_update.comment:
        cursor.execute(
            """
            INSERT INTO property_comments (user_id, property_id, comment)
            VALUES (?, ?, ?)
            """,
            (current_user.id, property_id, status_update.comment),
        )
        db.commit()

    # Return the updated status
    cursor.execute(
        """
        SELECT user_id, property_id, status, status_updated_at, created_at
        FROM property_status
        WHERE user_id = ? AND property_id = ?
        """,
        (current_user.id, property_id),
    )
    row = cursor.fetchone()
    return PropertyStatusResponse(**dict(row))


@router.get("/{property_id}/status", response_model=PropertyStatusResponse)
async def get_property_status(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get property status for current user."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT user_id, property_id, status, status_updated_at, created_at
        FROM property_status
        WHERE user_id = ? AND property_id = ?
        """,
        (current_user.id, property_id),
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Status not found")

    return PropertyStatusResponse(**dict(row))


# ============================================================================
# Property Comments
# ============================================================================


@router.post(
    "/{property_id}/comments", response_model=PropertyCommentResponse, status_code=201
)
async def add_property_comment(
    property_id: int,
    comment_data: PropertyComment,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Add a comment to a property."""
    cursor = db.cursor()

    # Verify property exists
    cursor.execute("SELECT id FROM properties WHERE id = ?", (property_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Property not found")

    cursor.execute(
        """
        INSERT INTO property_comments (user_id, property_id, comment)
        VALUES (?, ?, ?)
        """,
        (current_user.id, property_id, comment_data.comment),
    )
    db.commit()
    comment_id = cursor.lastrowid or 0

    # Fetch and return the created comment
    cursor.execute(
        """
        SELECT id, user_id, property_id, comment, created_at, updated_at
        FROM property_comments
        WHERE id = ?
        """,
        (comment_id,),
    )
    row = cursor.fetchone()
    return PropertyCommentResponse(**dict(row))


@router.get("/{property_id}/comments", response_model=List[PropertyCommentResponse])
async def get_property_comments(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get all comments for a property by current user."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, user_id, property_id, comment, created_at, updated_at
        FROM property_comments
        WHERE user_id = ? AND property_id = ?
        ORDER BY created_at DESC
        """,
        (current_user.id, property_id),
    )
    rows = cursor.fetchall()
    return [PropertyCommentResponse(**dict(row)) for row in rows]


@router.put(
    "/{property_id}/comments/{comment_id}", response_model=PropertyCommentResponse
)
async def update_property_comment(
    property_id: int,
    comment_id: int,
    comment_data: PropertyComment,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Update a property comment."""
    cursor = db.cursor()

    # Verify comment exists and belongs to user
    cursor.execute(
        "SELECT id FROM property_comments WHERE id = ? AND user_id = ? AND property_id = ?",
        (comment_id, current_user.id, property_id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Comment not found")

    cursor.execute(
        """
        UPDATE property_comments
        SET comment = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (comment_data.comment, comment_id),
    )
    db.commit()

    # Fetch and return updated comment
    cursor.execute(
        """
        SELECT id, user_id, property_id, comment, created_at, updated_at
        FROM property_comments
        WHERE id = ?
        """,
        (comment_id,),
    )
    row = cursor.fetchone()
    return PropertyCommentResponse(**dict(row))


@router.delete("/{property_id}/comments/{comment_id}", status_code=204)
async def delete_property_comment(
    property_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Delete a property comment."""
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM property_comments WHERE id = ? AND user_id = ? AND property_id = ?",
        (comment_id, current_user.id, property_id),
    )
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Comment not found")

    return None


# ============================================================================
# Property Ratings (Stars & Gone from Market)
# ============================================================================


@router.post("/{property_id}/rate", status_code=201)
async def rate_property(
    property_id: int,
    vote_type: str,  # "star" or "gone_from_market"
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Rate a property - star it or mark as gone from market.
    """
    if vote_type not in ["star", "gone_from_market"]:
        raise HTTPException(status_code=400, detail="Invalid vote type")

    cursor = db.cursor()

    # Verify property exists
    cursor.execute("SELECT id FROM properties WHERE id = ?", (property_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Property not found")

    # Insert rating
    cursor.execute(
        """
        INSERT INTO ratings (user_id, property_id, vote_type)
        VALUES (?, ?, ?)
        """,
        (current_user.id, property_id, vote_type),
    )
    db.commit()

    return {"status": f"property {vote_type}"}


@router.get("/{property_id}/my-rating", response_model=dict)
async def get_user_rating(
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Get current user's rating for a property.
    Users can only see their own ratings.
    """
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT vote_type, voted_at
        FROM ratings
        WHERE user_id = ? AND property_id = ?
        ORDER BY voted_at DESC
        LIMIT 1
        """,
        (current_user.id, property_id),
    )
    row = cursor.fetchone()

    if not row:
        return {"vote_type": None, "voted_at": None}

    return {"vote_type": row["vote_type"], "voted_at": row["voted_at"]}
