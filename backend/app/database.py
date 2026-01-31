# backend/app/database.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from datetime import datetime

DATABASE_PATH = Path(__file__).parent.parent / "data" / "rightmove.db"

def get_db_connection() -> sqlite3.Connection:
    """Create a database connection with row factory."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
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

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print(f"Database initialized at {DATABASE_PATH}")