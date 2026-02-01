# backend/app/database.py
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

DATABASE_PATH = Path(__file__).parent.parent / "data" / "rightmove.db"

# Global shared in-memory database connection for tests
_test_db_connection: Optional[sqlite3.Connection] = None


def _is_test_mode() -> bool:
    """Check if we're running in test mode."""
    return os.environ.get("TEST_MODE", "false").lower() == "true"


def get_db_connection() -> sqlite3.Connection:
    """Create a database connection with row factory."""
    if _is_test_mode():
        # Use in-memory database for testing with thread safety
        global _test_db_connection
        if _test_db_connection is None:
            _test_db_connection = sqlite3.connect(":memory:", check_same_thread=False)
            _test_db_connection.row_factory = sqlite3.Row
        return _test_db_connection

    # Use persistent file database for production
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    if _is_test_mode():
        # In test mode, reuse the in-memory connection without closing
        conn = get_db_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        # Don't close in-memory connection during tests, just commit
    else:
        # In production, create a new connection for each use
        conn = get_db_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db() -> None:
    """Initialize the database with all tables."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Properties table - stores all Rightmove listing data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rightmove_id TEXT UNIQUE NOT NULL,
                listing_title TEXT,
                listing_url TEXT,
                incode TEXT,
                outcode TEXT,
                full_address TEXT,
                latitude REAL,
                longitude REAL,
                
                -- Property details
                property_type TEXT,
                listing_type TEXT,
                bedrooms INTEGER,
                bathrooms INTEGER,
                size TEXT,
                furnishing_type TEXT,
                amenities TEXT,  -- JSON array
                
                -- Pricing
                price REAL,
                deposit REAL,
                price_history TEXT,  -- JSON array
                
                -- Ownership details
                tenure TEXT,
                council_tax_band TEXT,
                council_tax_exempt BOOLEAN,
                years_remaining_on_lease INTEGER,
                annual_ground_rent REAL,
                annual_service_charge REAL,
                ground_rent_percentage_increase REAL,
                
                -- Description
                text_description TEXT,
                formatted_html_description TEXT,
                
                -- Media
                images TEXT,  -- JSON array
                floorplans TEXT,  -- JSON array
                brochures TEXT,  -- JSON array
                epc TEXT,  -- JSON object
                
                -- Agent information
                agent_name TEXT,
                agent_logo TEXT,
                agent_phone TEXT,
                agent_address TEXT,
                agent_profile_url TEXT,
                agent_description TEXT,
                agent_listings_url TEXT,
                
                -- Status
                sold BOOLEAN DEFAULT 0,
                removed BOOLEAN DEFAULT 0,
                display_status TEXT,
                listing_update_reason TEXT,
                
                -- Dates
                first_visible_date TEXT,
                listing_update_date TEXT,
                first_scraped_at TEXT NOT NULL,
                last_scraped_at TEXT NOT NULL,
                
                -- Nearby amenities
                nearest_schools TEXT,  -- JSON array
                
                -- Verification status
                verification_status TEXT DEFAULT 'pending' CHECK(verification_status IN ('pending', 'processing', 'available', 'sold', 'rented', 'unclear', 'pending_review', 'failed')),
                last_verified_at TEXT,
                verification_notes TEXT,

                -- Timestamps
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Ratings table - tracks upvotes/downvotes for listings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL,
                vote_type TEXT NOT NULL CHECK(vote_type IN ('upvote', 'downvote')),
                voted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # Verification logs table - audit trail for property verification calls
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL UNIQUE,
                call_timestamp TEXT,
                call_duration_seconds INTEGER,
                agent_phone TEXT,
                agent_response TEXT,
                verification_status TEXT CHECK(verification_status IN ('available', 'sold', 'rented', 'unclear', 'pending_review', 'failed')),
                confidence_score REAL,
                notes TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_rightmove_id 
            ON properties(rightmove_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_location 
            ON properties(latitude, longitude)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_price 
            ON properties(price)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_bedrooms 
            ON properties(bedrooms)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_property_type 
            ON properties(property_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_removed 
            ON properties(removed)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_properties_outcode 
            ON properties(outcode)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ratings_property_id 
            ON ratings(property_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ratings_voted_at 
            ON ratings(voted_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verification_logs_property_id 
            ON verification_logs(property_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verification_logs_status 
            ON verification_logs(verification_status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verification_logs_created_at 
            ON verification_logs(created_at)
        """)

        # Create trigger to update updated_at timestamp
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS update_properties_timestamp 
            AFTER UPDATE ON properties
            BEGIN
                UPDATE properties 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = NEW.id;
            END
        """)

        conn.commit()


def reset_test_db() -> None:
    """Reset the in-memory test database. Only works in test mode."""
    global _test_db_connection
    if _test_db_connection is not None:
        try:
            _test_db_connection.close()
        except Exception:
            pass
        _test_db_connection = None


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print(f"Database initialized at {DATABASE_PATH}")
