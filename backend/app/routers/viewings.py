"""
Viewing calendar endpoints for scheduling property viewings.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_db
from app.routers.auth import get_current_user
from app.schemas import User, ViewingEventCreate, ViewingEventResponse

router = APIRouter(prefix="/viewings", tags=["viewings"])


@router.post("", response_model=ViewingEventResponse, status_code=201)
async def create_viewing(
    viewing: ViewingEventCreate,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Create a new viewing event."""
    cursor = db.cursor()

    # Verify property exists
    cursor.execute("SELECT id FROM properties WHERE id = ?", (viewing.property_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Property not found")

    # Validate date format
    try:
        datetime.fromisoformat(viewing.viewing_date)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use ISO format: YYYY-MM-DD"
        )

    # Insert viewing event
    cursor.execute(
        """
        INSERT INTO viewing_events (user_id, property_id, viewing_date, viewing_time, agent_contact, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            current_user.id,
            viewing.property_id,
            viewing.viewing_date,
            viewing.viewing_time,
            viewing.agent_contact,
            viewing.notes,
        ),
    )
    db.commit()
    viewing_id = cursor.lastrowid or 0

    if viewing_id == 0:
        raise HTTPException(status_code=500, detail="Failed to create viewing")

    # Fetch and return the created viewing
    cursor.execute(
        """
        SELECT id, user_id, property_id, viewing_date, viewing_time, agent_contact, notes,
               reminder_sent, created_at, updated_at
        FROM viewing_events
        WHERE id = ?
        """,
        (viewing_id,),
    )
    row = cursor.fetchone()
    return ViewingEventResponse(**dict(row))


@router.get("", response_model=List[ViewingEventResponse])
async def get_viewings(
    current_user: User = Depends(get_current_user),
    upcoming_only: bool = Query(True, description="Only show future viewings"),
    start_date: Optional[str] = Query(
        None, description="Filter from date (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get viewing events for current user."""
    cursor = db.cursor()

    query = """
        SELECT id, user_id, property_id, viewing_date, viewing_time, agent_contact, notes,
               reminder_sent, created_at, updated_at
        FROM viewing_events
        WHERE user_id = ?
    """
    params = [current_user.id]

    # Add date filters
    if upcoming_only:
        query += " AND viewing_date >= DATE('now')"

    if start_date:
        try:
            datetime.fromisoformat(start_date)
            query += " AND viewing_date >= ?"
            params.append(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            datetime.fromisoformat(end_date)
            query += " AND viewing_date <= ?"
            params.append(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    query += " ORDER BY viewing_date ASC, viewing_time ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    return [ViewingEventResponse(**dict(row)) for row in rows]


@router.get("/{viewing_id}", response_model=ViewingEventResponse)
async def get_viewing(
    viewing_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Get a specific viewing event."""
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id, user_id, property_id, viewing_date, viewing_time, agent_contact, notes,
               reminder_sent, created_at, updated_at
        FROM viewing_events
        WHERE id = ? AND user_id = ?
        """,
        (viewing_id, current_user.id),
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Viewing not found")

    return ViewingEventResponse(**dict(row))


@router.put("/{viewing_id}", response_model=ViewingEventResponse)
async def update_viewing(
    viewing_id: int,
    viewing_update: ViewingEventCreate,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Update a viewing event."""
    cursor = db.cursor()

    # Verify viewing exists and belongs to user
    cursor.execute(
        "SELECT id FROM viewing_events WHERE id = ? AND user_id = ?",
        (viewing_id, current_user.id),
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Viewing not found")

    # Verify property exists if different
    cursor.execute(
        "SELECT id FROM properties WHERE id = ?", (viewing_update.property_id,)
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Property not found")

    # Update viewing
    cursor.execute(
        """
        UPDATE viewing_events
        SET property_id = ?, viewing_date = ?, viewing_time = ?,
            agent_contact = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            viewing_update.property_id,
            viewing_update.viewing_date,
            viewing_update.viewing_time,
            viewing_update.agent_contact,
            viewing_update.notes,
            viewing_id,
        ),
    )
    db.commit()

    # Fetch and return updated viewing
    cursor.execute(
        """
        SELECT id, user_id, property_id, viewing_date, viewing_time, agent_contact, notes,
               reminder_sent, created_at, updated_at
        FROM viewing_events
        WHERE id = ?
        """,
        (viewing_id,),
    )
    row = cursor.fetchone()
    return ViewingEventResponse(**dict(row))


@router.delete("/{viewing_id}", status_code=204)
async def delete_viewing(
    viewing_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Delete a viewing event."""
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM viewing_events WHERE id = ? AND user_id = ?",
        (viewing_id, current_user.id),
    )
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Viewing not found")

    return None


@router.post("/{viewing_id}/export/ical")
async def export_to_ical(
    viewing_id: int,
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Export viewing event as iCalendar format (Apple Calendar compatible)."""
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT ve.id, ve.viewing_date, ve.viewing_time, ve.agent_contact, p.full_address, p.listing_title
        FROM viewing_events ve
        JOIN properties p ON ve.property_id = p.id
        WHERE ve.id = ? AND ve.user_id = ?
        """,
        (viewing_id, current_user.id),
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Viewing not found")

    # Generate iCalendar format
    ical_content = _generate_ical(row)

    return {
        "format": "ical",
        "content": ical_content,
        "filename": f"viewing_{viewing_id}.ics",
    }


@router.post("/export/ical/all")
async def export_all_to_ical(
    current_user: User = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    """Export all upcoming viewing events as iCalendar format."""
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT ve.id, ve.viewing_date, ve.viewing_time, ve.agent_contact, p.full_address, p.listing_title
        FROM viewing_events ve
        JOIN properties p ON ve.property_id = p.id
        WHERE ve.user_id = ? AND ve.viewing_date >= DATE('now')
        ORDER BY ve.viewing_date ASC
        """,
        (current_user.id,),
    )
    rows = cursor.fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No upcoming viewings found")

    # Generate iCalendar with multiple events
    ical_content = _generate_ical_multiple(rows)

    return {
        "format": "ical",
        "content": ical_content,
        "filename": "viewings.ics",
        "count": len(rows),
    }


def _generate_ical(viewing_row) -> str:
    """Generate iCalendar format for a single viewing."""
    from datetime import datetime as dt

    viewing_date = viewing_row["viewing_date"]
    viewing_time = viewing_row["viewing_time"] or "10:00"
    address = viewing_row["full_address"]
    title = viewing_row["listing_title"]
    agent = viewing_row["agent_contact"] or "Agent TBD"

    # Parse date and time
    dt_obj = dt.fromisoformat(f"{viewing_date}T{viewing_time}:00")
    dt_end = dt_obj.replace(hour=dt_obj.hour + 1)  # 1 hour duration

    # Format for iCalendar (UTC)
    dt_start = dt_obj.strftime("%Y%m%dT%H%M%S")
    dt_end_str = dt_end.strftime("%Y%m%dT%H%M%S")
    dt_created = dt.now().strftime("%Y%m%dT%H%M%SZ")

    ical = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Property Finder//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{viewing_row["id"]}@property-finder
DTSTAMP:{dt_created}
DTSTART:{dt_start}
DTEND:{dt_end_str}
SUMMARY:Property Viewing - {title}
DESCRIPTION:Address: {address}\\nAgent: {agent}
LOCATION:{address}
END:VEVENT
END:VCALENDAR"""

    return ical


def _generate_ical_multiple(viewing_rows) -> str:
    """Generate iCalendar format for multiple viewings."""
    from datetime import datetime as dt

    events: list = []
    for row in viewing_rows:
        viewing_date = row["viewing_date"]
        viewing_time = row["viewing_time"] or "10:00"
        address = row["full_address"]
        title = row["listing_title"]
        agent = row["agent_contact"] or "Agent TBD"

        dt_obj = dt.fromisoformat(f"{viewing_date}T{viewing_time}:00")
        dt_end = dt_obj.replace(hour=dt_obj.hour + 1)

        dt_start = dt_obj.strftime("%Y%m%dT%H%M%S")
        dt_end_str = dt_end.strftime("%Y%m%dT%H%M%S")
        dt_created = dt.now().strftime("%Y%m%dT%H%M%SZ")

        event = f"""BEGIN:VEVENT
UID:{row["id"]}@property-finder
DTSTAMP:{dt_created}
DTSTART:{dt_start}
DTEND:{dt_end_str}
SUMMARY:Property Viewing - {title}
DESCRIPTION:Address: {address}\\nAgent: {agent}
LOCATION:{address}
END:VEVENT"""
        events.append(event)

    ical = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Property Finder//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
{chr(10).join(events)}
END:VCALENDAR"""

    return ical
