# backend/app/database.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DATABASE_PATH = Path(__file__).parent.parent / "data" / "rightmove.db"


def get_db_connection() -> sqlite3.Connection:
    """Create a database connection with row factory."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Allow cross-thread access for development/testing with FastAPI TestClient
    # SQLite will serialize access internally, so this is safe
    conn = sqlite3.connect(str(DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> sqlite3.Connection:
    """FastAPI dependency to get a database connection.

    Returns a raw sqlite3 connection. FastAPI handles cleanup automatically.
    For manual transaction control, use get_db_context() instead.
    """
    return get_db_connection()


@contextmanager
def get_db_context() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections (for non-FastAPI code).

    Use this in CRUD operations and other code that needs explicit
    transaction control. FastAPI routes should use Depends(get_db).
    """
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
    with get_db_context() as conn:
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

        # Users table - stores user account information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User profiles table - extended user information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                bio TEXT,
                dream_property_description TEXT,
                preferred_price_min INTEGER,
                preferred_price_max INTEGER,
                preferred_bedrooms_min INTEGER,
                preferred_property_types TEXT,  -- JSON array
                preferred_locations TEXT,  -- JSON array (outcodes)
                notification_viewing_reminder_days INTEGER DEFAULT 3,
                notification_email_enabled BOOLEAN DEFAULT 1,
                notification_in_app_enabled BOOLEAN DEFAULT 1,
                notification_feed_changes_enabled BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # OAuth providers table - tracks OAuth integrations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oauth_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,  -- 'google', 'apple', 'microsoft', 'facebook'
                provider_user_id TEXT NOT NULL,
                provider_email TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(provider, provider_user_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Refresh tokens table - for JWT token refresh
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Property bookmarks table - tracks starred/bookmarked properties
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                property_id INTEGER NOT NULL,
                is_starred BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(user_id, property_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # Property status table - tracks user's journey with each property
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                property_id INTEGER NOT NULL,
                status TEXT DEFAULT 'interested',  -- 'interested', 'viewing', 'offer', 'accepted'
                status_updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(user_id, property_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # Property status comments table - notes on properties
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS property_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                property_id INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # Viewing events table - tracks scheduled property viewings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS viewing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                property_id INTEGER NOT NULL,
                viewing_date TEXT NOT NULL,
                viewing_time TEXT,
                agent_contact TEXT,
                notes TEXT,
                reminder_sent BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
        """)

        # Shared feeds table - wishlists shared between multiple users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                invite_token TEXT UNIQUE NOT NULL,
                max_members INTEGER DEFAULT 8,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Shared feed members table - tracks users in a shared feed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_feed_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shared_feed_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(shared_feed_id, user_id),
                FOREIGN KEY (shared_feed_id) REFERENCES shared_feeds(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Ratings table - tracks stars/marked unavailable for listings (now with user tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                property_id INTEGER NOT NULL,
                vote_type TEXT NOT NULL CHECK(vote_type IN ('star', 'gone_from_market')),
                voted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
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
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_bookmarks_user_id 
            ON property_bookmarks(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_bookmarks_property_id 
            ON property_bookmarks(property_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_status_user_id 
            ON property_status(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_status_property_id 
            ON property_status(property_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_comments_user_id 
            ON property_comments(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_property_comments_property_id 
            ON property_comments(property_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_viewing_events_user_id 
            ON viewing_events(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_viewing_events_viewing_date 
            ON viewing_events(viewing_date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oauth_providers_user_id 
            ON oauth_providers(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_oauth_providers_provider_id 
            ON oauth_providers(provider, provider_user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id 
            ON refresh_tokens(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_shared_feed_members_user_id 
            ON shared_feed_members(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_shared_feed_members_shared_feed_id 
            ON shared_feed_members(shared_feed_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ratings_user_id 
            ON ratings(user_id)
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
