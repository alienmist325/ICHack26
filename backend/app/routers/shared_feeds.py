"""
Shared feeds/wishlists endpoints for collaborative property discovery.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Set

from fastapi import APIRouter, Depends, HTTPException, WebSocket

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import (
    SharedFeedCreate,
    SharedFeedDetailResponse,
    SharedFeedResponse,
    User,
)
from app.security import generate_invite_token

router = APIRouter(prefix="/shared-feeds", tags=["shared feeds"])

# Store active WebSocket connections for each feed
active_connections: Dict[int, Set[WebSocket]] = {}


@router.post("", response_model=SharedFeedResponse, status_code=201)
async def create_shared_feed(
    feed: SharedFeedCreate,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Create a new shared feed/wishlist."""
    cursor = db.cursor()

    # Generate unique invite token
    invite_token = generate_invite_token()

    # Create shared feed
    cursor.execute(
        """
        INSERT INTO shared_feeds (name, invite_token, max_members)
        VALUES (?, ?, 8)
        """,
        (feed.name, invite_token),
    )
    db.commit()
    feed_id = cursor.lastrowid or 0

    if feed_id == 0:
        raise HTTPException(status_code=500, detail="Failed to create shared feed")

    # Add creator as first member
    cursor.execute(
        """
        INSERT INTO shared_feed_members (shared_feed_id, user_id)
        VALUES (?, ?)
        """,
        (feed_id, current_user.id),
    )
    db.commit()

    # Fetch and return the created feed
    cursor.execute(
        """
        SELECT id, name, invite_token, max_members, created_at, updated_at
        FROM shared_feeds
        WHERE id = ?
        """,
        (feed_id,),
    )
    row = cursor.fetchone()
    return SharedFeedResponse(**dict(row))


@router.get("", response_model=List[SharedFeedDetailResponse])
async def get_user_shared_feeds(
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get all shared feeds the user is a member of."""
    cursor = db.cursor()

    # Get feeds user is member of
    cursor.execute(
        """
        SELECT sf.id, sf.name, sf.invite_token, sf.max_members, sf.created_at, sf.updated_at
        FROM shared_feeds sf
        JOIN shared_feed_members sfm ON sf.id = sfm.shared_feed_id
        WHERE sfm.user_id = ?
        ORDER BY sf.created_at DESC
        """,
        (current_user.id,),
    )
    rows = cursor.fetchall()

    feeds = []
    for row in rows:
        feed_dict = dict(row)

        # Get members for this feed
        cursor.execute(
            """
            SELECT u.id, u.email, u.is_active, u.created_at, u.updated_at
            FROM users u
            JOIN shared_feed_members sfm ON u.id = sfm.user_id
            WHERE sfm.shared_feed_id = ?
            """,
            (feed_dict["id"],),
        )
        members = [User(**dict(member)) for member in cursor.fetchall()]

        feed_dict["members"] = members
        feed_dict["member_count"] = len(members)
        feeds.append(SharedFeedDetailResponse(**feed_dict))

    return feeds


@router.get("/{feed_id}", response_model=SharedFeedDetailResponse)
async def get_shared_feed(
    feed_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get a specific shared feed with members."""
    cursor = db.cursor()

    # Verify user is member of feed
    cursor.execute(
        """
        SELECT sf.id, sf.name, sf.invite_token, sf.max_members, sf.created_at, sf.updated_at
        FROM shared_feeds sf
        JOIN shared_feed_members sfm ON sf.id = sfm.shared_feed_id
        WHERE sf.id = ? AND sfm.user_id = ?
        """,
        (feed_id, current_user.id),
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=404, detail="Shared feed not found or access denied"
        )

    feed_dict = dict(row)

    # Get all members
    cursor.execute(
        """
        SELECT u.id, u.email, u.is_active, u.created_at, u.updated_at
        FROM users u
        JOIN shared_feed_members sfm ON u.id = sfm.user_id
        WHERE sfm.shared_feed_id = ?
        """,
        (feed_id,),
    )
    members = [User(**dict(member)) for member in cursor.fetchall()]

    feed_dict["members"] = members
    feed_dict["member_count"] = len(members)
    return SharedFeedDetailResponse(**feed_dict)


@router.post("/join/{invite_token}")
async def join_shared_feed(
    invite_token: str,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Join a shared feed using an invite token."""
    cursor = db.cursor()

    # Find feed by token
    cursor.execute(
        """
        SELECT id, max_members FROM shared_feeds WHERE invite_token = ?
        """,
        (invite_token,),
    )
    feed = cursor.fetchone()

    if not feed:
        raise HTTPException(status_code=404, detail="Invite token not found")

    feed_id = feed["id"]

    # Check if user already member
    cursor.execute(
        """
        SELECT id FROM shared_feed_members
        WHERE shared_feed_id = ? AND user_id = ?
        """,
        (feed_id, current_user.id),
    )
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Already a member of this feed")

    # Check member limit
    cursor.execute(
        "SELECT COUNT(*) as count FROM shared_feed_members WHERE shared_feed_id = ?",
        (feed_id,),
    )
    member_count = cursor.fetchone()["count"]
    if member_count >= feed["max_members"]:
        raise HTTPException(status_code=409, detail="Feed is full")

    # Add user to feed
    cursor.execute(
        """
        INSERT INTO shared_feed_members (shared_feed_id, user_id)
        VALUES (?, ?)
        """,
        (feed_id, current_user.id),
    )
    db.commit()

    return {"status": "joined", "feed_id": feed_id}


@router.post("/{feed_id}/leave")
async def leave_shared_feed(
    feed_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Leave a shared feed (user can remove themselves only)."""
    cursor = db.cursor()

    # Verify user is member
    cursor.execute(
        """
        SELECT id FROM shared_feed_members
        WHERE shared_feed_id = ? AND user_id = ?
        """,
        (feed_id, current_user.id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Not a member of this feed")

    # Remove user from feed
    cursor.execute(
        """
        DELETE FROM shared_feed_members
        WHERE shared_feed_id = ? AND user_id = ?
        """,
        (feed_id, current_user.id),
    )
    db.commit()

    return {"status": "left"}


@router.get("/{feed_id}/properties", response_model=List[int])
async def get_shared_feed_properties(
    feed_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get all starred properties in a shared feed (from all members)."""
    cursor = db.cursor()

    # Verify user is member
    cursor.execute(
        """
        SELECT id FROM shared_feed_members
        WHERE shared_feed_id = ? AND user_id = ?
        """,
        (feed_id, current_user.id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Not a member of this feed")

    # Get all members of feed
    cursor.execute(
        """
        SELECT user_id FROM shared_feed_members WHERE shared_feed_id = ?
        """,
        (feed_id,),
    )
    member_ids = [row["user_id"] for row in cursor.fetchall()]

    if not member_ids:
        return []

    # Get properties starred by any member
    placeholders = ",".join("?" * len(member_ids))
    cursor.execute(
        f"""
        SELECT DISTINCT property_id FROM property_bookmarks
        WHERE user_id IN ({placeholders}) AND is_starred = 1
        ORDER BY property_id
        """,
        member_ids,
    )

    return [row["property_id"] for row in cursor.fetchall()]


@router.post("/{feed_id}/properties/{property_id}/star")
async def star_in_shared_feed(
    feed_id: int,
    property_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Add a property star in context of shared feed (broadcasts via WebSocket)."""
    cursor = db.cursor()

    # Verify user is member of feed
    cursor.execute(
        """
        SELECT id FROM shared_feed_members
        WHERE shared_feed_id = ? AND user_id = ?
        """,
        (feed_id, current_user.id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Not a member of this feed")

    # Verify property exists
    cursor.execute("SELECT id FROM properties WHERE id = ?", (property_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Property not found")

    # Star property (user-specific)
    cursor.execute(
        """
        INSERT OR REPLACE INTO property_bookmarks (user_id, property_id, is_starred)
        VALUES (?, ?, 1)
        """,
        (current_user.id, property_id),
    )
    db.commit()

    # Broadcast to WebSocket connections
    await _broadcast_feed_update(
        feed_id,
        {
            "type": "property_starred",
            "feed_id": feed_id,
            "property_id": property_id,
            "user_id": current_user.id,
            "timestamp": datetime.now().isoformat(),
        },
    )

    return {"status": "starred_in_feed"}


async def _broadcast_feed_update(feed_id: int, message: dict):
    """Broadcast update to all WebSocket clients connected to a feed."""
    if feed_id in active_connections:
        disconnected = []
        for ws in active_connections[feed_id]:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        # Clean up disconnected clients
        for ws in disconnected:
            active_connections[feed_id].discard(ws)


@router.websocket("/ws/{feed_id}/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    feed_id: int,
    token: str,
    db: sqlite3.Connection = Depends(get_db),
):
    """WebSocket endpoint for real-time feed updates."""
    from app.security import verify_token

    # Verify token
    token_data = verify_token(token, token_type="access")
    if not token_data:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # Verify user is member of feed
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id FROM shared_feed_members
        WHERE shared_feed_id = ? AND user_id = ?
        """,
        (feed_id, token_data.user_id),
    )
    if not cursor.fetchone():
        await websocket.close(code=1008, reason="Not a member of this feed")
        return

    await websocket.accept()

    # Register connection
    if feed_id not in active_connections:
        active_connections[feed_id] = set()
    active_connections[feed_id].add(websocket)

    try:
        while True:
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                # Broadcast message to all other clients
                await _broadcast_feed_update(
                    feed_id,
                    {
                        **data,
                        "user_id": token_data.user_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections[feed_id].discard(websocket)
        if not active_connections[feed_id]:
            del active_connections[feed_id]
