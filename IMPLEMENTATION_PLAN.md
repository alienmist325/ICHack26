# User Accounts & Property Management - Implementation Plan

## Executive Summary

This document outlines a detailed, phased implementation plan for adding user authentication, property management, shared feeds, and calendar integrations to the Property Rental Finder app.

**Current Stack:**
- Backend: FastAPI + SQLite
- Frontend: React + Vite + Styled Components
- Auth: None (to be added)

**Proposed Additions:**
- JWT + OAuth2 authentication
- PostgreSQL (upgrade from SQLite for scalability)
- WebSocket support for real-time updates
- Calendar integration APIs

---

## Phase 1: Database Schema & Infrastructure

### 1.1 Database Migration Strategy

**Current State:** SQLite with basic properties and ratings tables

**Migration Path:**
1. Keep SQLite during development
2. Add new tables for users and user-related features
3. Create migration scripts for future PostgreSQL upgrade
4. Use Alembic for schema versioning

**Decision:** Start with SQLite, add SQLAlchemy ORM for future DB portability

### 1.2 Complete Database Schema

```sql
-- ============================================================================
-- USERS & AUTHENTICATION
-- ============================================================================

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT,  -- NULL if OAuth-only
    first_name TEXT,
    last_name TEXT,
    profile_picture_url TEXT,
    
    -- OAuth Provider IDs (for multi-provider login)
    google_id TEXT UNIQUE,
    apple_id TEXT UNIQUE,
    microsoft_id TEXT UNIQUE,
    facebook_id TEXT UNIQUE,
    
    -- Account Status
    is_active BOOLEAN DEFAULT 1,
    email_verified BOOLEAN DEFAULT 0,
    email_verified_at TEXT,
    
    -- Timestamps
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TEXT
);

CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    bio TEXT,
    
    -- Preferences
    preferred_min_price REAL,
    preferred_max_price REAL,
    preferred_bedrooms INTEGER,
    preferred_furnishing TEXT,  -- 'furnished', 'unfurnished', 'part-furnished'
    preferred_property_types TEXT,  -- JSON array
    preferred_postcodes TEXT,  -- JSON array
    
    -- Notification Preferences
    notify_new_matches BOOLEAN DEFAULT 1,
    notify_feed_updates BOOLEAN DEFAULT 1,
    notify_viewing_reminders BOOLEAN DEFAULT 1,
    notification_method TEXT DEFAULT 'email',  -- 'email', 'in_app', 'both'
    
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================================
-- BOOKMARKS & PROPERTY INTERACTIONS
-- ============================================================================

CREATE TABLE property_bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    bookmarked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, property_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

-- Property status tracking: viewing → offer → accepted
CREATE TABLE property_status_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('viewing', 'offer', 'accepted')),
    
    -- Timestamps
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, property_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

CREATE TABLE property_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

-- ============================================================================
-- SHARED FEEDS & WISHLISTS
-- ============================================================================

CREATE TABLE shared_feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    
    -- Unique shareable link
    invite_code TEXT UNIQUE NOT NULL,
    max_members INTEGER DEFAULT 8,
    
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE shared_feed_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shared_feed_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(shared_feed_id, user_id),
    FOREIGN KEY (shared_feed_id) REFERENCES shared_feeds(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Properties added to shared feeds
CREATE TABLE shared_feed_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shared_feed_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    added_by_user_id INTEGER NOT NULL,
    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (shared_feed_id) REFERENCES shared_feeds(id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    FOREIGN KEY (added_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================================
-- VIEWING CALENDAR & EVENTS
-- ============================================================================

CREATE TABLE viewing_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    
    scheduled_at TEXT NOT NULL,  -- ISO 8601 datetime
    duration_minutes INTEGER DEFAULT 30,
    
    -- Organizer details
    organizer_name TEXT,
    organizer_phone TEXT,
    organizer_email TEXT,
    
    -- Viewing details
    address TEXT,
    notes TEXT,
    
    -- Calendar integration IDs
    google_calendar_event_id TEXT,
    apple_calendar_event_id TEXT,
    outlook_calendar_event_id TEXT,
    
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

-- ============================================================================
-- VOTING & RATINGS (Updated to support user-based tracking)
-- ============================================================================

-- Modified ratings table to track user votes
-- NOTE: Votes are anonymous to other users, but tracked per user
CREATE TABLE user_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    vote_type TEXT NOT NULL CHECK(vote_type IN ('star', 'unavailable')),
    
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, property_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

-- Anonymous vote aggregation (for admin analytics)
-- Downvotes = "marked unavailable"
CREATE TABLE vote_aggregates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL UNIQUE,
    
    star_count INTEGER DEFAULT 0,  -- Upvotes
    unavailable_count INTEGER DEFAULT 0,  -- Downvotes
    
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

-- ============================================================================
-- SESSIONS & TOKENS
-- ============================================================================

CREATE TABLE refresh_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_google_id ON users(google_id);
CREATE INDEX idx_users_apple_id ON users(apple_id);
CREATE INDEX idx_users_microsoft_id ON users(microsoft_id);
CREATE INDEX idx_users_facebook_id ON users(facebook_id);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);

CREATE INDEX idx_property_bookmarks_user_id ON property_bookmarks(user_id);
CREATE INDEX idx_property_bookmarks_property_id ON property_bookmarks(property_id);

CREATE INDEX idx_property_status_tracking_user_id ON property_status_tracking(user_id);
CREATE INDEX idx_property_status_tracking_property_id ON property_status_tracking(property_id);
CREATE INDEX idx_property_status_tracking_status ON property_status_tracking(status);

CREATE INDEX idx_property_comments_user_id ON property_comments(user_id);
CREATE INDEX idx_property_comments_property_id ON property_comments(property_id);

CREATE INDEX idx_shared_feeds_owner_id ON shared_feeds(owner_id);
CREATE INDEX idx_shared_feeds_invite_code ON shared_feeds(invite_code);

CREATE INDEX idx_shared_feed_members_user_id ON shared_feed_members(user_id);
CREATE INDEX idx_shared_feed_members_shared_feed_id ON shared_feed_members(shared_feed_id);

CREATE INDEX idx_viewing_events_user_id ON viewing_events(user_id);
CREATE INDEX idx_viewing_events_property_id ON viewing_events(property_id);
CREATE INDEX idx_viewing_events_scheduled_at ON viewing_events(scheduled_at);

CREATE INDEX idx_user_votes_user_id ON user_votes(user_id);
CREATE INDEX idx_user_votes_property_id ON user_votes(property_id);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER update_users_timestamp 
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_user_profiles_timestamp 
AFTER UPDATE ON user_profiles
BEGIN
    UPDATE user_profiles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_property_status_tracking_timestamp 
AFTER UPDATE ON property_status_tracking
BEGIN
    UPDATE property_status_tracking SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_property_comments_timestamp 
AFTER UPDATE ON property_comments
BEGIN
    UPDATE property_comments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_shared_feeds_timestamp 
AFTER UPDATE ON shared_feeds
BEGIN
    UPDATE shared_feeds SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_viewing_events_timestamp 
AFTER UPDATE ON viewing_events
BEGIN
    UPDATE viewing_events SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_vote_aggregates_timestamp 
AFTER UPDATE ON vote_aggregates
BEGIN
    UPDATE vote_aggregates SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
```

---

## Phase 2: Backend Implementation

### 2.1 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app & route definitions
│   ├── database.py                # SQLite/SQLAlchemy setup
│   ├── schemas.py                 # Pydantic models (new user schemas)
│   ├── crud.py                    # CRUD operations
│   ├── models.py                  # SQLAlchemy models (replace if using ORM)
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py         # JWT token creation/validation
│   │   ├── oauth.py               # OAuth2 providers setup
│   │   ├── password.py            # Password hashing
│   │   └── dependencies.py        # FastAPI dependencies (get_current_user)
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                # Register, login, logout, OAuth callbacks
│   │   ├── users.py               # User profiles, preferences, settings
│   │   ├── properties.py          # Star/unstar, mark unavailable, etc.
│   │   ├── property_actions.py    # Viewing state, comments
│   │   ├── viewing_calendar.py    # Calendar CRUD & exports
│   │   ├── shared_feeds.py        # Shared feed management
│   │   ├── feed.py                # Personalized feed
│   │   └── admin.py               # Admin endpoints
│   │
│   └── services/
│       ├── __init__.py
│       ├── notification.py        # Email/in-app notifications
│       ├── calendar_export.py     # Google, Apple, Outlook integrations
│       ├── preference_engine.py   # Preference-based recommendations
│       └── websocket_manager.py   # Real-time feed updates
│
├── config.py                      # Configuration & env vars
├── requirements.txt               # Dependencies (add auth packages)
├── alembic/                       # Database migrations (optional)
└── tests/
    ├── __init__.py
    ├── test_auth.py
    ├── test_users.py
    ├── test_properties.py
    ├── test_shared_feeds.py
    └── test_viewing_calendar.py
```

### 2.2 Dependencies to Add

```toml
# pyproject.toml additions

[project]
dependencies = [
    # Existing
    "apify-client>=2.4.1",
    "fastapi[standard]>=0.128.0",
    "pydantic>=2.12.5",
    "pydantic-settings>=2.0.0",
    "routingpy>=1.3.0",
    "shapely>=2.1.2",
    "websockets>=16.0",
    
    # NEW: Authentication & Security
    "python-jose[cryptography]>=3.3.0",  # JWT tokens
    "passlib[bcrypt]>=1.7.4",             # Password hashing
    "python-multipart>=0.0.5",            # Form data handling
    
    # NEW: OAuth2
    "authlib>=1.2.0",                     # OAuth2 client
    "httpx>=0.24.0",                      # Async HTTP client
    
    # NEW: Database (ORM - optional, for better migration support)
    "sqlalchemy>=2.0.0",                  # ORM
    "alembic>=1.12.0",                    # Migrations
    
    # NEW: Calendar Integration
    "icalendar>=5.0.0",                   # iCal format
    "google-auth-oauthlib>=1.0.0",        # Google OAuth
    "google-auth-httplib2>=0.2.0",        # Google API
    "google-api-python-client>=2.95.0",   # Google Calendar API
    
    # NEW: Email Notifications
    "python-dotenv>=1.0.0",               # Env var management
    "aiosmtplib>=3.0.0",                  # Async email
    
    # NEW: Data Validation
    "email-validator>=2.0.0",             # Email validation
]

[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "pytest-asyncio>=0.21.0",             # Async test support
    "pytest-cov>=4.1.0",                  # Coverage reporting
    "ruff>=0.14.14",
    "httpx[testing]>=0.24.0",             # Testing utilities
]
```

### 2.3 Key Backend Modules

#### 2.3.1 Security: JWT & Password Handling

**File: `backend/app/security/password.py`**

```python
from passlib.context import CryptContext
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

**File: `backend/app/security/jwt_handler.py`**

```python
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from config import settings

def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": str(user_id), "exp": expire}
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[int]:
    """Verify a token and extract user_id."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
        return user_id
    except Exception:
        return None
```

**File: `backend/app/security/dependencies.py`**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from app.security.jwt_handler import verify_token
from app.crud import get_user_by_id

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    user_id = verify_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user
```

#### 2.3.2 Authentication Schemas

**File: `backend/app/schemas.py` (additions)**

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum

# ============================================================================
# Authentication
# ============================================================================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class OAuth2CallbackRequest(BaseModel):
    code: str
    provider: str  # 'google', 'apple', 'microsoft', 'facebook'
    redirect_uri: str

# ============================================================================
# User Profile
# ============================================================================

class NotificationMethod(str, Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    BOTH = "both"

class UserProfileUpdate(BaseModel):
    bio: Optional[str] = None
    preferred_min_price: Optional[float] = None
    preferred_max_price: Optional[float] = None
    preferred_bedrooms: Optional[int] = None
    preferred_furnishing: Optional[str] = None
    preferred_property_types: Optional[list[str]] = None
    preferred_postcodes: Optional[list[str]] = None

class NotificationSettingsUpdate(BaseModel):
    notify_new_matches: Optional[bool] = None
    notify_feed_updates: Optional[bool] = None
    notify_viewing_reminders: Optional[bool] = None
    notification_method: Optional[NotificationMethod] = None

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_picture_url: Optional[str]
    created_at: str

# ============================================================================
# Property Interactions
# ============================================================================

class PropertyStatus(str, Enum):
    VIEWING = "viewing"
    OFFER = "offer"
    ACCEPTED = "accepted"

class PropertyStatusUpdate(BaseModel):
    status: PropertyStatus

class PropertyComment(BaseModel):
    id: int
    user_id: int
    property_id: int
    comment: str
    created_at: str
    updated_at: str

class PropertyCommentCreate(BaseModel):
    comment: str

# ============================================================================
# Viewing Calendar
# ============================================================================

class ViewingEventCreate(BaseModel):
    property_id: int
    scheduled_at: str  # ISO 8601
    duration_minutes: int = 30
    organizer_name: Optional[str] = None
    organizer_phone: Optional[str] = None
    organizer_email: Optional[str] = None
    notes: Optional[str] = None

class ViewingEvent(ViewingEventCreate):
    id: int
    user_id: int
    address: Optional[str]
    created_at: str
    updated_at: str

# ============================================================================
# Shared Feeds
# ============================================================================

class SharedFeedCreate(BaseModel):
    name: str
    description: Optional[str] = None
    max_members: int = 8

class SharedFeed(SharedFeedCreate):
    id: int
    owner_id: int
    invite_code: str
    created_at: str
    updated_at: str

class SharedFeedMember(BaseModel):
    id: int
    user_id: int
    joined_at: str

class SharedFeedWithMembers(SharedFeed):
    members: list[SharedFeedMember]

class JoinSharedFeedRequest(BaseModel):
    invite_code: str
```

#### 2.3.3 Authentication Router

**File: `backend/app/routers/auth.py`**

```python
from fastapi import APIRouter, HTTPException, status
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, OAuth2CallbackRequest
from app.security.password import hash_password, verify_password
from app.security.jwt_handler import create_access_token
from app.crud import (
    create_user, get_user_by_email, get_user_by_oauth_id, 
    create_or_update_oauth_user, create_refresh_token
)
from config import settings
import httpx

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ============================================================================
# Email/Password Authentication
# ============================================================================

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new user with email and password."""
    # Check if user exists
    existing_user = get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with hashed password
    hashed_pwd = hash_password(request.password)
    user = create_user(
        email=request.email,
        hashed_password=hashed_pwd,
        first_name=request.first_name,
        last_name=request.last_name,
    )
    
    # Generate tokens
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email and password."""
    user = get_user_by_email(request.email)
    
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

# ============================================================================
# OAuth2 Integration
# ============================================================================

@router.post("/oauth/callback", response_model=TokenResponse)
async def oauth_callback(request: OAuth2CallbackRequest):
    """Handle OAuth callback from frontend."""
    provider = request.provider.lower()
    
    if provider == "google":
        user_info = await _handle_google_oauth(request.code, request.redirect_uri)
    elif provider == "apple":
        user_info = await _handle_apple_oauth(request.code, request.redirect_uri)
    elif provider == "microsoft":
        user_info = await _handle_microsoft_oauth(request.code, request.redirect_uri)
    elif provider == "facebook":
        user_info = await _handle_facebook_oauth(request.code, request.redirect_uri)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    # Create or update user
    user = create_or_update_oauth_user(provider, user_info)
    
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

async def _handle_google_oauth(code: str, redirect_uri: str) -> dict:
    """Exchange Google OAuth code for user info."""
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
        )
        token_response.raise_for_status()
        tokens = token_response.json()
        
        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        user_response.raise_for_status()
        user_info = user_response.json()
        
        return {
            "oauth_id": user_info["id"],
            "email": user_info["email"],
            "first_name": user_info.get("given_name"),
            "last_name": user_info.get("family_name"),
            "picture_url": user_info.get("picture"),
        }

# Similar implementations for Apple, Microsoft, Facebook...
```

#### 2.3.4 User Profile Router

**File: `backend/app/routers/users.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import (
    UserResponse, UserProfileUpdate, NotificationSettingsUpdate
)
from app.security.dependencies import get_current_user
from app.crud import (
    get_user_by_id, update_user_profile, 
    get_user_profile, update_notification_settings
)

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(**current_user)

@router.patch("/me/profile", response_model=UserResponse)
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user = Depends(get_current_user)
):
    """Update user profile."""
    updated = update_user_profile(current_user["id"], profile_update)
    return UserResponse(**updated)

@router.get("/me/profile-settings")
async def get_profile_settings(current_user = Depends(get_current_user)):
    """Get detailed profile and preference settings."""
    profile = get_user_profile(current_user["id"])
    return profile

@router.patch("/me/notification-settings")
async def update_notification_settings_endpoint(
    settings_update: NotificationSettingsUpdate,
    current_user = Depends(get_current_user)
):
    """Update notification preferences."""
    updated = update_notification_settings(current_user["id"], settings_update)
    return updated
```

#### 2.3.5 Property Actions Router

**File: `backend/app/routers/property_actions.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import (
    PropertyStatus, PropertyStatusUpdate, PropertyComment,
    PropertyCommentCreate
)
from app.security.dependencies import get_current_user
from app.crud import (
    star_property, unstar_property, mark_unavailable, 
    unmark_unavailable, get_user_stars, get_user_unavailable,
    update_property_status, add_property_comment, 
    get_property_comments, delete_property_comment
)

router = APIRouter(prefix="/api/properties", tags=["property_actions"])

# ============================================================================
# Bookmarks/Stars
# ============================================================================

@router.post("/{property_id}/star")
async def star_property_endpoint(
    property_id: int,
    current_user = Depends(get_current_user)
):
    """Star/bookmark a property."""
    result = star_property(current_user["id"], property_id)
    return {"starred": True, "property_id": property_id}

@router.delete("/{property_id}/star")
async def unstar_property_endpoint(
    property_id: int,
    current_user = Depends(get_current_user)
):
    """Unstar/remove bookmark from property."""
    unstar_property(current_user["id"], property_id)
    return {"starred": False, "property_id": property_id}

@router.get("/me/starred")
async def get_user_starred_properties(
    current_user = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get user's starred properties."""
    starred = get_user_stars(current_user["id"], limit, offset)
    return {"starred_properties": starred}

# ============================================================================
# Mark Unavailable
# ============================================================================

@router.post("/{property_id}/mark-unavailable")
async def mark_property_unavailable(
    property_id: int,
    current_user = Depends(get_current_user)
):
    """Mark property as unavailable."""
    mark_unavailable(current_user["id"], property_id)
    return {"marked_unavailable": True, "property_id": property_id}

@router.delete("/{property_id}/mark-unavailable")
async def unmark_property_unavailable(
    property_id: int,
    current_user = Depends(get_current_user)
):
    """Unmark property as unavailable."""
    unmark_unavailable(current_user["id"], property_id)
    return {"marked_unavailable": False, "property_id": property_id}

@router.get("/me/marked-unavailable")
async def get_user_marked_unavailable(
    current_user = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get user's marked unavailable properties."""
    unavailable = get_user_unavailable(current_user["id"], limit, offset)
    return {"unavailable_properties": unavailable}

# ============================================================================
# Property Status (viewing → offer → accepted)
# ============================================================================

@router.patch("/{property_id}/status")
async def update_property_status_endpoint(
    property_id: int,
    status_update: PropertyStatusUpdate,
    current_user = Depends(get_current_user)
):
    """Update property status (viewing/offer/accepted)."""
    updated = update_property_status(
        current_user["id"], property_id, status_update.status.value
    )
    return updated

# ============================================================================
# Comments
# ============================================================================

@router.post("/{property_id}/comments", response_model=PropertyComment)
async def add_comment(
    property_id: int,
    comment_data: PropertyCommentCreate,
    current_user = Depends(get_current_user)
):
    """Add a comment to a property."""
    comment = add_property_comment(
        current_user["id"], property_id, comment_data.comment
    )
    return comment

@router.get("/{property_id}/comments", response_model=list[PropertyComment])
async def get_comments(
    property_id: int,
    limit: int = 20,
    offset: int = 0
):
    """Get all comments for a property."""
    comments = get_property_comments(property_id, limit, offset)
    return comments

@router.delete("/comments/{comment_id}")
async def delete_comment_endpoint(
    comment_id: int,
    current_user = Depends(get_current_user)
):
    """Delete a comment (must be author)."""
    success = delete_property_comment(comment_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    return {"deleted": True}
```

#### 2.3.6 Viewing Calendar Router

**File: `backend/app/routers/viewing_calendar.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import ViewingEvent, ViewingEventCreate
from app.security.dependencies import get_current_user
from app.crud import (
    create_viewing_event, list_upcoming_viewings, 
    delete_viewing_event, get_viewing_event
)
from app.services.calendar_export import (
    export_to_google_calendar, export_to_apple_calendar,
    export_to_outlook_calendar
)
from datetime import datetime

router = APIRouter(prefix="/api/viewing-calendar", tags=["viewing_calendar"])

@router.post("/viewings", response_model=ViewingEvent)
async def create_viewing(
    viewing_data: ViewingEventCreate,
    current_user = Depends(get_current_user)
):
    """Create a new viewing event."""
    viewing = create_viewing_event(current_user["id"], viewing_data)
    return viewing

@router.get("/viewings", response_model=list[ViewingEvent])
async def get_viewings(
    current_user = Depends(get_current_user),
    upcoming_only: bool = True
):
    """Get viewing events (optionally filtered to upcoming)."""
    viewings = list_upcoming_viewings(
        current_user["id"], 
        upcoming_only=upcoming_only
    )
    return viewings

@router.get("/viewings/{viewing_id}", response_model=ViewingEvent)
async def get_viewing(
    viewing_id: int,
    current_user = Depends(get_current_user)
):
    """Get a specific viewing event."""
    viewing = get_viewing_event(viewing_id)
    if not viewing or viewing["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Viewing not found")
    return viewing

@router.delete("/viewings/{viewing_id}")
async def delete_viewing(
    viewing_id: int,
    current_user = Depends(get_current_user)
):
    """Delete a viewing event."""
    success = delete_viewing_event(viewing_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this viewing"
        )
    return {"deleted": True}

# ============================================================================
# Calendar Exports
# ============================================================================

@router.post("/export/google")
async def export_to_google(
    viewing_id: int,
    current_user = Depends(get_current_user),
    google_access_token: str = None
):
    """Export viewing to Google Calendar."""
    viewing = get_viewing_event(viewing_id)
    if not viewing or viewing["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Viewing not found")
    
    # Requires user to have connected Google Calendar
    result = await export_to_google_calendar(viewing, google_access_token)
    return result

@router.get("/export/apple/{viewing_id}")
async def export_to_apple(
    viewing_id: int,
    current_user = Depends(get_current_user)
):
    """Export viewing to Apple Calendar (returns iCal file)."""
    viewing = get_viewing_event(viewing_id)
    if not viewing or viewing["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Viewing not found")
    
    ical_data = export_to_apple_calendar(viewing)
    return {
        "ical": ical_data,
        "filename": f"viewing-{viewing_id}.ics"
    }

@router.post("/export/outlook")
async def export_to_outlook(
    viewing_id: int,
    current_user = Depends(get_current_user),
    outlook_access_token: str = None
):
    """Export viewing to Outlook calendar."""
    viewing = get_viewing_event(viewing_id)
    if not viewing or viewing["user_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Viewing not found")
    
    result = await export_to_outlook_calendar(viewing, outlook_access_token)
    return result
```

#### 2.3.7 Shared Feeds Router

**File: `backend/app/routers/shared_feeds.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from app.schemas import (
    SharedFeed, SharedFeedCreate, SharedFeedWithMembers,
    JoinSharedFeedRequest
)
from app.security.dependencies import get_current_user
from app.crud import (
    create_shared_feed, get_shared_feed, list_user_feeds,
    add_feed_member, remove_feed_member, list_feed_members,
    get_shared_feed_by_invite_code, add_property_to_feed,
    get_feed_properties
)
from app.services.websocket_manager import manager
import secrets

router = APIRouter(prefix="/api/shared-feeds", tags=["shared_feeds"])

@router.post("/", response_model=SharedFeed)
async def create_feed(
    feed_data: SharedFeedCreate,
    current_user = Depends(get_current_user)
):
    """Create a new shared feed."""
    invite_code = secrets.token_urlsafe(16)
    feed = create_shared_feed(
        owner_id=current_user["id"],
        **feed_data.model_dump(),
        invite_code=invite_code
    )
    return feed

@router.get("/", response_model=list[SharedFeed])
async def list_feeds(current_user = Depends(get_current_user)):
    """List all feeds user is a member of."""
    feeds = list_user_feeds(current_user["id"])
    return feeds

@router.get("/{feed_id}", response_model=SharedFeedWithMembers)
async def get_feed(
    feed_id: int,
    current_user = Depends(get_current_user)
):
    """Get a specific feed (must be member)."""
    feed = get_shared_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    # Check membership
    members = list_feed_members(feed_id)
    is_member = any(m["user_id"] == current_user["id"] for m in members)
    if not is_member and feed["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this feed"
        )
    
    return SharedFeedWithMembers(**feed, members=members)

@router.post("/join")
async def join_feed(
    request: JoinSharedFeedRequest,
    current_user = Depends(get_current_user)
):
    """Join a feed using invite code."""
    feed = get_shared_feed_by_invite_code(request.invite_code)
    if not feed:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    # Check max members
    members = list_feed_members(feed["id"])
    if len(members) >= feed["max_members"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feed is at maximum capacity"
        )
    
    add_feed_member(feed["id"], current_user["id"])
    return {"joined": True, "feed_id": feed["id"]}

@router.delete("/{feed_id}/leave")
async def leave_feed(
    feed_id: int,
    current_user = Depends(get_current_user)
):
    """Leave a feed."""
    remove_feed_member(feed_id, current_user["id"])
    return {"left": True}

@router.get("/{feed_id}/members")
async def get_members(
    feed_id: int,
    current_user = Depends(get_current_user)
):
    """Get feed members."""
    feed = get_shared_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    members = list_feed_members(feed_id)
    return {"members": members}

@router.post("/{feed_id}/properties/{property_id}")
async def add_to_feed(
    feed_id: int,
    property_id: int,
    current_user = Depends(get_current_user)
):
    """Add a property to shared feed."""
    feed = get_shared_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    # Must be feed member
    members = list_feed_members(feed_id)
    is_member = any(m["user_id"] == current_user["id"] for m in members)
    if not is_member and feed["owner_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this feed"
        )
    
    add_property_to_feed(feed_id, property_id, current_user["id"])
    
    # Notify feed members via WebSocket
    await manager.broadcast_to_feed(feed_id, {
        "type": "property_added",
        "property_id": property_id,
        "added_by": current_user["id"]
    })
    
    return {"added": True}

@router.get("/{feed_id}/properties")
async def get_feed_properties_endpoint(
    feed_id: int,
    current_user = Depends(get_current_user)
):
    """Get all properties in a feed."""
    feed = get_shared_feed(feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    
    properties = get_feed_properties(feed_id)
    return {"properties": properties}

# ============================================================================
# WebSocket for Real-Time Feed Updates
# ============================================================================

@router.websocket("/ws/{feed_id}")
async def websocket_endpoint(websocket: WebSocket, feed_id: int):
    """WebSocket connection for real-time feed updates."""
    await manager.connect(websocket, feed_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages
            await manager.broadcast_to_feed(feed_id, {"type": "message", "data": data})
    except Exception:
        manager.disconnect(websocket, feed_id)
```

#### 2.3.8 Personalized Feed Router

**File: `backend/app/routers/feed.py`**

```python
from fastapi import APIRouter, Depends, Query
from app.security.dependencies import get_current_user
from app.crud import (
    get_user_profile, get_properties_with_scores
)
from app.services.preference_engine import get_personalized_feed

router = APIRouter(prefix="/api/feed", tags=["feed"])

@router.get("/personalized")
async def get_personalized_feed(
    current_user = Depends(get_current_user),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0)
):
    """Get personalized property feed based on user preferences."""
    # Get user preferences
    profile = get_user_profile(current_user["id"])
    
    # Get personalized properties
    properties = get_personalized_feed(current_user["id"], profile, limit, offset)
    
    return {
        "properties": properties,
        "limit": limit,
        "offset": offset,
        "total_count": len(properties)  # Should be calculated from DB
    }

@router.get("/starred")
async def get_starred_feed(
    current_user = Depends(get_current_user),
    filter_status: str = None,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Get user's starred properties with optional status filter."""
    # Implementation here
    pass
```

### 2.4 CRUD Operations Enhancement

**File: `backend/app/crud.py` (additions)**

The existing CRUD file should be expanded with user-related operations:

```python
# User CRUD
def create_user(email: str, hashed_password: str, first_name: str = None, last_name: str = None):
    """Create a new user."""
    # Implementation

def get_user_by_id(user_id: int):
    """Get user by ID."""
    # Implementation

def get_user_by_email(email: str):
    """Get user by email."""
    # Implementation

def create_refresh_token(user_id: int) -> str:
    """Create a refresh token."""
    # Implementation

# Property interactions
def star_property(user_id: int, property_id: int):
    """Star/bookmark a property."""
    # Implementation

def unstar_property(user_id: int, property_id: int):
    """Unstar property."""
    # Implementation

def get_user_stars(user_id: int, limit: int, offset: int):
    """Get user's starred properties."""
    # Implementation

def mark_unavailable(user_id: int, property_id: int):
    """Mark property as unavailable for user."""
    # Implementation

def update_property_status(user_id: int, property_id: int, status: str):
    """Update property status (viewing/offer/accepted)."""
    # Implementation

def add_property_comment(user_id: int, property_id: int, comment: str):
    """Add comment to property."""
    # Implementation

# Shared feeds
def create_shared_feed(owner_id: int, name: str, description: str, max_members: int, invite_code: str):
    """Create a shared feed."""
    # Implementation

def add_feed_member(feed_id: int, user_id: int):
    """Add user to feed."""
    # Implementation

# Viewing calendar
def create_viewing_event(user_id: int, property_id: int, scheduled_at: str, ...):
    """Create a viewing event."""
    # Implementation

def list_upcoming_viewings(user_id: int, upcoming_only: bool = True):
    """Get upcoming viewing events."""
    # Implementation
```

### 2.5 Services Layer

#### 2.5.1 Calendar Export Service

**File: `backend/app/services/calendar_export.py`**

```python
from icalendar import Calendar, Event
from datetime import datetime
import httpx

def export_to_apple_calendar(viewing: dict) -> str:
    """Generate iCal format for Apple Calendar."""
    cal = Calendar()
    cal.add('prodid', '-//Property Finder//EN')
    cal.add('version', '2.0')
    
    event = Event()
    event.add('summary', f"Property Viewing: {viewing['address']}")
    event.add('dtstart', datetime.fromisoformat(viewing['scheduled_at']))
    event.add('description', viewing.get('notes', ''))
    event.add('location', viewing.get('address', ''))
    
    cal.add_component(event)
    return cal.to_ical().decode('utf-8')

async def export_to_google_calendar(viewing: dict, access_token: str):
    """Export to Google Calendar via API."""
    async with httpx.AsyncClient() as client:
        event_body = {
            "summary": f"Property Viewing: {viewing['address']}",
            "start": {"dateTime": viewing['scheduled_at']},
            "end": {"dateTime": viewing['scheduled_at']},  # Add duration
            "description": viewing.get('notes', ''),
            "location": viewing.get('address', ''),
        }
        
        response = await client.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            json=event_body,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        return response.json()

async def export_to_outlook_calendar(viewing: dict, access_token: str):
    """Export to Outlook/Microsoft Calendar."""
    # Similar to Google Calendar implementation
    pass
```

#### 2.5.2 WebSocket Manager

**File: `backend/app/services/websocket_manager.py`**

```python
from fastapi import WebSocket
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        # feed_id -> set of connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, feed_id: int):
        await websocket.accept()
        if feed_id not in self.active_connections:
            self.active_connections[feed_id] = set()
        self.active_connections[feed_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, feed_id: int):
        if feed_id in self.active_connections:
            self.active_connections[feed_id].discard(websocket)
    
    async def broadcast_to_feed(self, feed_id: int, message: dict):
        """Broadcast message to all connected users in a feed."""
        if feed_id in self.active_connections:
            for connection in self.active_connections[feed_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()
```

#### 2.5.3 Preference Engine

**File: `backend/app/services/preference_engine.py`**

```python
from app.crud import get_properties_with_scores, get_user_votes

def get_personalized_feed(user_id: int, profile: dict, limit: int, offset: int):
    """
    Get personalized feed based on:
    1. User preferences (bio settings)
    2. Previously starred properties (learning)
    3. Rating scores
    """
    # Build filter from user preferences
    filters = {
        "min_price": profile.get("preferred_min_price"),
        "max_price": profile.get("preferred_max_price"),
        "min_bedrooms": profile.get("preferred_bedrooms"),
        "furnishing_type": profile.get("preferred_furnishing"),
        "property_types": profile.get("preferred_property_types"),
        "outcodes": profile.get("preferred_postcodes"),
    }
    
    # Get properties matching preferences, sorted by rating
    properties = get_properties_with_scores(filters, limit, offset)
    
    # Get user's vote history for context
    user_votes = get_user_votes(user_id)
    
    # Rank by relevance (starred count, score, recency)
    # Implementation of ranking algorithm here
    
    return properties
```

### 2.6 Configuration

**File: `backend/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./data/rightmove.db"
    
    # Security & Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth2 Credentials
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    APPLE_CLIENT_ID: str = ""
    APPLE_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Email notifications
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Phase 3: Frontend Implementation

### 3.1 Frontend Structure

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   │
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   ├── OAuthButtons.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   │
│   │   ├── property/
│   │   │   ├── PropertyCard.tsx          # Enhanced with star, status, comments
│   │   │   ├── PropertyComments.tsx
│   │   │   ├── PropertyStatus.tsx
│   │   │   ├── StarButton.tsx
│   │   │   └── MarkUnavailableButton.tsx
│   │   │
│   │   ├── feed/
│   │   │   ├── FeedFilter.tsx
│   │   │   ├── PersonalizedFeed.tsx
│   │   │   ├── SharedFeedView.tsx
│   │   │   └── FeedInviteModal.tsx
│   │   │
│   │   ├── calendar/
│   │   │   ├── ViewingCalendar.tsx
│   │   │   ├── ViewingEvent.tsx
│   │   │   ├── AddViewingModal.tsx
│   │   │   └── CalendarExportButtons.tsx
│   │   │
│   │   └── user/
│   │       ├── ProfilePage.tsx
│   │       ├── PreferencesForm.tsx
│   │       ├── NotificationSettings.tsx
│   │       └── WishlistManager.tsx
│   │
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── HomePage.tsx
│   │   ├── ProfilePage.tsx
│   │   ├── SharedFeedPage.tsx
│   │   ├── CalendarPage.tsx
│   │   └── NotFoundPage.tsx
│   │
│   ├── hooks/
│   │   ├── useAuth.ts              # Authentication state & functions
│   │   ├── useUser.ts              # User profile & preferences
│   │   ├── useProperty.ts          # Property interactions (star, comment)
│   │   ├── useViewings.ts          # Calendar & viewing events
│   │   ├── useSharedFeed.ts        # Shared feed operations
│   │   └── useWebSocket.ts         # Real-time updates
│   │
│   ├── services/
│   │   ├── api.ts                  # Axios/fetch instance
│   │   ├── authService.ts
│   │   ├── propertyService.ts
│   │   ├── userService.ts
│   │   ├── viewingService.ts
│   │   ├── sharedFeedService.ts
│   │   └── websocketService.ts
│   │
│   ├── context/
│   │   ├── AuthContext.tsx
│   │   └── NotificationContext.tsx
│   │
│   ├── utils/
│   │   ├── storage.ts              # LocalStorage helpers
│   │   ├── formatters.ts           # Date/currency formatting
│   │   └── validators.ts
│   │
│   └── types/
│       ├── api.ts                  # API response types
│       ├── user.ts
│       ├── property.ts
│       └── feed.ts
│
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### 3.2 Key Pages & Components

#### 3.2.1 Login/Register Flow

**File: `frontend/src/pages/LoginPage.tsx`**

```typescript
import React, { useState } from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import OAuthButtons from '../components/auth/OAuthButtons';
import { useAuth } from '../hooks/useAuth';

const LoginPageContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
`;

const LoginCard = styled.div`
  background: white;
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
`;

const Title = styled.h1`
  text-align: center;
  margin-bottom: 30px;
  color: #333;
`;

const Divider = styled.div`
  display: flex;
  align-items: center;
  margin: 30px 0;
  color: #999;
  
  &::before, &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #ddd;
  }
  
  &::before {
    margin-right: 10px;
  }
  
  &::after {
    margin-left: 10px;
  }
`;

const RegisterLink = styled.p`
  text-align: center;
  margin-top: 20px;
  color: #666;
  
  a {
    color: #667eea;
    text-decoration: none;
    font-weight: bold;
    
    &:hover {
      text-decoration: underline;
    }
  }
`;

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLoginSuccess = () => {
    navigate('/');
  };

  return (
    <LoginPageContainer>
      <LoginCard>
        <Title>Welcome Back</Title>
        <LoginForm onSuccess={handleLoginSuccess} />
        <Divider>or</Divider>
        <OAuthButtons />
        <RegisterLink>
          Don't have an account? <a href="/register">Sign up</a>
        </RegisterLink>
      </LoginCard>
    </LoginPageContainer>
  );
}
```

**File: `frontend/src/components/auth/LoginForm.tsx`**

```typescript
import React, { useState } from 'react';
import styled from 'styled-components';
import { useAuth } from '../../hooks/useAuth';

const FormContainer = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const Input = styled.input`
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const Button = styled.button`
  padding: 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s;
  
  &:hover {
    background: #5568d3;
  }
  
  &:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.p`
  color: #e74c3c;
  font-size: 14px;
  margin: 0;
`;

interface LoginFormProps {
  onSuccess: () => void;
}

export default function LoginForm({ onSuccess }: LoginFormProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <FormContainer onSubmit={handleSubmit}>
      <Input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <Input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <Button type="submit" disabled={loading}>
        {loading ? 'Signing in...' : 'Sign In'}
      </Button>
    </FormContainer>
  );
}
```

**File: `frontend/src/components/auth/OAuthButtons.tsx`**

```typescript
import React from 'react';
import styled from 'styled-components';
import { FiGithub } from 'react-icons/fi';
import { SiGoogle, SiApple, SiMicrosoft, SiFacebook } from 'react-icons/si';

const ButtonContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const OAuthButton = styled.button<{ provider: string }>`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  transition: all 0.3s;
  
  &:hover {
    background: #f5f5f5;
    border-color: #999;
  }
  
  svg {
    width: 20px;
    height: 20px;
  }
`;

const GoogleButton = styled(OAuthButton)`
  color: #333;
`;

const AppleButton = styled(OAuthButton)`
  color: #000;
`;

const MicrosoftButton = styled(OAuthButton)`
  color: #00a4ef;
`;

const FacebookButton = styled(OAuthButton)`
  color: #1877f2;
`;

export default function OAuthButtons() {
  const handleOAuth = (provider: string) => {
    // Redirect to OAuth authorization endpoint
    const clientId = import.meta.env[`VITE_${provider.toUpperCase()}_CLIENT_ID`];
    const redirectUri = `${window.location.origin}/auth/callback`;
    
    const authUrls: Record<string, string> = {
      google: `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=openid%20email%20profile`,
      apple: `https://appleid.apple.com/auth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=openid%20email%20name`,
      microsoft: `https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=openid%20email%20profile`,
      facebook: `https://www.facebook.com/v17.0/dialog/oauth?client_id=${clientId}&redirect_uri=${redirectUri}&scope=email,public_profile`,
    };
    
    window.location.href = authUrls[provider] || '';
  };

  return (
    <ButtonContainer>
      <GoogleButton provider="google" onClick={() => handleOAuth('google')}>
        <SiGoogle /> Sign in with Google
      </GoogleButton>
      <AppleButton provider="apple" onClick={() => handleOAuth('apple')}>
        <SiApple /> Sign in with Apple
      </AppleButton>
      <MicrosoftButton provider="microsoft" onClick={() => handleOAuth('microsoft')}>
        <SiMicrosoft /> Sign in with Microsoft
      </MicrosoftButton>
      <FacebookButton provider="facebook" onClick={() => handleOAuth('facebook')}>
        <SiFacebook /> Sign in with Facebook
      </FacebookButton>
    </ButtonContainer>
  );
}
```

#### 3.2.2 Enhanced Property Card

**File: `frontend/src/components/property/PropertyCard.tsx`**

```typescript
import React, { useState } from 'react';
import styled from 'styled-components';
import { FiStar, FiMessageCircle, FiCheckCircle } from 'react-icons/fi';
import StarButton from './StarButton';
import MarkUnavailableButton from './MarkUnavailableButton';
import PropertyStatus from './PropertyStatus';
import PropertyComments from './PropertyComments';
import { Property } from '../../types/property';

const Card = styled.div`
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
  }
`;

const ImageContainer = styled.div`
  position: relative;
  width: 100%;
  height: 250px;
  overflow: hidden;
  background: #f0f0f0;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
`;

const Content = styled.div`
  padding: 20px;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 15px;
`;

const Title = styled.h3`
  margin: 0;
  font-size: 18px;
  color: #333;
`;

const Price = styled.div`
  font-size: 20px;
  font-weight: bold;
  color: #667eea;
`;

const Details = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
  margin-bottom: 15px;
  font-size: 14px;
  color: #666;
  
  > div {
    display: flex;
    flex-direction: column;
  }
`;

const Badge = styled.span`
  display: inline-block;
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
`;

const Actions = styled.div`
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
`;

const CommentIcon = styled(FiMessageCircle)`
  cursor: pointer;
  transition: color 0.2s;
  
  &:hover {
    color: #667eea;
  }
`;

interface PropertyCardProps {
  property: Property;
  isAuthenticated?: boolean;
  onPropertyUpdate?: () => void;
}

export default function PropertyCard({ 
  property, 
  isAuthenticated = false,
  onPropertyUpdate 
}: PropertyCardProps) {
  const [showComments, setShowComments] = useState(false);

  return (
    <Card>
      {property.images && property.images.length > 0 && (
        <ImageContainer>
          <img src={property.images[0]} alt={property.listing_title} />
        </ImageContainer>
      )}
      
      <Content>
        <Header>
          <div>
            <Title>{property.listing_title}</Title>
            <Price>£{property.price?.toLocaleString()}/month</Price>
          </div>
        </Header>
        
        <Details>
          <div>
            <Badge>{property.bedrooms} bed</Badge>
          </div>
          <div>
            <Badge>{property.bathrooms} bath</Badge>
          </div>
          <div>
            <Badge>{property.furnishing_type}</Badge>
          </div>
        </Details>
        
        {isAuthenticated && (
          <>
            <Actions>
              <StarButton propertyId={property.id} onUpdate={onPropertyUpdate} />
              <MarkUnavailableButton propertyId={property.id} onUpdate={onPropertyUpdate} />
              <PropertyStatus propertyId={property.id} onUpdate={onPropertyUpdate} />
              <CommentIcon 
                size={20} 
                onClick={() => setShowComments(!showComments)}
              />
            </Actions>
            
            {showComments && (
              <PropertyComments 
                propertyId={property.id} 
                onUpdate={onPropertyUpdate}
              />
            )}
          </>
        )}
      </Content>
    </Card>
  );
}
```

**File: `frontend/src/components/property/StarButton.tsx`**

```typescript
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiStar } from 'react-icons/fi';
import { propertyService } from '../../services/propertyService';

const Button = styled.button<{ starred: boolean }>`
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  border: 1px solid ${props => props.starred ? '#f39c12' : '#ddd'};
  background: ${props => props.starred ? '#fffbf0' : 'white'};
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.2s;
  
  svg {
    width: 18px;
    height: 18px;
    fill: ${props => props.starred ? '#f39c12' : 'none'};
    color: ${props => props.starred ? '#f39c12' : '#999'};
  }
  
  &:hover {
    border-color: #f39c12;
    background: #fffbf0;
  }
`;

interface StarButtonProps {
  propertyId: number;
  onUpdate?: () => void;
}

export default function StarButton({ propertyId, onUpdate }: StarButtonProps) {
  const [starred, setStarred] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if property is starred
    // Implementation
  }, [propertyId]);

  const handleStar = async () => {
    setLoading(true);
    try {
      if (starred) {
        await propertyService.unstarProperty(propertyId);
        setStarred(false);
      } else {
        await propertyService.starProperty(propertyId);
        setStarred(true);
      }
      onUpdate?.();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button 
      starred={starred} 
      onClick={handleStar} 
      disabled={loading}
      title={starred ? 'Remove star' : 'Add to favorites'}
    >
      <FiStar />
      {starred ? 'Starred' : 'Star'}
    </Button>
  );
}
```

#### 3.2.3 Viewing Calendar Page

**File: `frontend/src/pages/CalendarPage.tsx`**

```typescript
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { viewingService } from '../services/viewingService';
import ViewingCalendar from '../components/calendar/ViewingCalendar';
import AddViewingModal from '../components/calendar/AddViewingModal';
import { useAuth } from '../hooks/useAuth';

const PageContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  
  h1 {
    margin: 0;
  }
`;

const Button = styled.button`
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  
  &:hover {
    background: #5568d3;
  }
`;

export default function CalendarPage() {
  const { user } = useAuth();
  const [viewings, setViewings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    if (user) {
      loadViewings();
    }
  }, [user]);

  const loadViewings = async () => {
    try {
      const data = await viewingService.getUpcomingViewings();
      setViewings(data);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return <PageContainer>Please log in to view your calendar.</PageContainer>;
  }

  return (
    <PageContainer>
      <Header>
        <h1>Viewing Calendar</h1>
        <Button onClick={() => setShowAddModal(true)}>Add Viewing</Button>
      </Header>

      {loading ? (
        <p>Loading viewings...</p>
      ) : (
        <>
          <ViewingCalendar viewings={viewings} onUpdate={loadViewings} />
          {showAddModal && (
            <AddViewingModal
              onClose={() => setShowAddModal(false)}
              onSuccess={() => {
                setShowAddModal(false);
                loadViewings();
              }}
            />
          )}
        </>
      )}
    </PageContainer>
  );
}
```

**File: `frontend/src/components/calendar/ViewingCalendar.tsx`**

```typescript
import React from 'react';
import styled from 'styled-components';
import { ViewingEvent } from '../../types/api';
import ViewingEventComponent from './ViewingEvent';
import CalendarExportButtons from './CalendarExportButtons';

const Container = styled.div`
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
`;

const EventList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const EmptyState = styled.p`
  text-align: center;
  color: #999;
  padding: 40px 20px;
`;

interface ViewingCalendarProps {
  viewings: ViewingEvent[];
  onUpdate: () => void;
}

export default function ViewingCalendar({ viewings, onUpdate }: ViewingCalendarProps) {
  if (viewings.length === 0) {
    return <EmptyState>No upcoming viewings. Add one to get started!</EmptyState>;
  }

  return (
    <Container>
      <EventList>
        {viewings.map((event) => (
          <ViewingEventComponent
            key={event.id}
            event={event}
            onUpdate={onUpdate}
          />
        ))}
      </EventList>
    </Container>
  );
}
```

#### 3.2.4 Shared Feeds Component

**File: `frontend/src/pages/SharedFeedPage.tsx`**

```typescript
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useParams } from 'react-router-dom';
import { sharedFeedService } from '../services/sharedFeedService';
import { useAuth } from '../hooks/useAuth';
import { useWebSocket } from '../hooks/useWebSocket';
import PropertyCard from '../components/property/PropertyCard';
import FeedInviteModal from '../components/feed/FeedInviteModal';

const PageContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  
  h1 {
    margin: 0;
  }
`;

const Button = styled.button`
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  
  &:hover {
    background: #5568d3;
  }
`;

const MembersSection = styled.div`
  margin-bottom: 30px;
  
  h3 {
    margin: 0 0 15px 0;
  }
`;

const Members = styled.div`
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
`;

const Member = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 20px;
  font-size: 14px;
  
  img {
    width: 24px;
    height: 24px;
    border-radius: 50%;
  }
`;

const PropertiesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
`;

export default function SharedFeedPage() {
  const { feedId } = useParams<{ feedId: string }>();
  const { user } = useAuth();
  const [feed, setFeed] = useState(null);
  const [members, setMembers] = useState([]);
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showInviteModal, setShowInviteModal] = useState(false);

  // Real-time updates via WebSocket
  const { data: wsData } = useWebSocket(
    user && feedId ? `ws://localhost:8000/api/shared-feeds/ws/${feedId}` : null
  );

  useEffect(() => {
    if (feedId) {
      loadFeed();
    }
  }, [feedId]);

  useEffect(() => {
    if (wsData?.type === 'property_added') {
      loadFeed(); // Refresh feed
    }
  }, [wsData]);

  const loadFeed = async () => {
    try {
      const feedData = await sharedFeedService.getFeed(parseInt(feedId!));
      setFeed(feedData);
      setMembers(feedData.members);
      
      const propsData = await sharedFeedService.getFeedProperties(parseInt(feedId!));
      setProperties(propsData);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <PageContainer>Loading...</PageContainer>;
  if (!feed) return <PageContainer>Feed not found</PageContainer>;

  return (
    <PageContainer>
      <Header>
        <div>
          <h1>{feed.name}</h1>
          <p>{feed.description}</p>
        </div>
        <Button onClick={() => setShowInviteModal(true)}>Invite Members</Button>
      </Header>

      <MembersSection>
        <h3>Members ({members.length}/{feed.max_members})</h3>
        <Members>
          {members.map((member) => (
            <Member key={member.id}>
              <div>{member.name}</div>
            </Member>
          ))}
        </Members>
      </MembersSection>

      <h2>Properties</h2>
      <PropertiesGrid>
        {properties.map((property) => (
          <PropertyCard
            key={property.id}
            property={property}
            isAuthenticated={!!user}
            onPropertyUpdate={loadFeed}
          />
        ))}
      </PropertiesGrid>

      {showInviteModal && (
        <FeedInviteModal
          feedId={parseInt(feedId!)}
          inviteCode={feed.invite_code}
          onClose={() => setShowInviteModal(false)}
        />
      )}
    </PageContainer>
  );
}
```

### 3.3 Authentication Hooks

**File: `frontend/src/hooks/useAuth.ts`**

```typescript
import { useState, useCallback, useEffect } from 'react';
import { authService } from '../services/authService';
import { User } from '../types/user';

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>(() => {
    const savedUser = localStorage.getItem('user');
    const savedToken = localStorage.getItem('access_token');
    
    return {
      user: savedUser ? JSON.parse(savedUser) : null,
      loading: false,
      error: null,
    };
  });

  const register = useCallback(async (email: string, password: string, firstName?: string, lastName?: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const { user, access_token, refresh_token } = await authService.register(
        email,
        password,
        firstName,
        lastName
      );
      
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      setState((prev) => ({ ...prev, user, loading: false }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Registration failed',
        loading: false,
      }));
      throw error;
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const { user, access_token, refresh_token } = await authService.login(email, password);
      
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      setState((prev) => ({ ...prev, user, loading: false }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Login failed',
        loading: false,
      }));
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('user');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setState({ user: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    register,
    login,
    logout,
    isAuthenticated: !!state.user,
  };
}
```

### 3.4 API Services

**File: `frontend/src/services/api.ts`**

```typescript
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
});

// Add authorization token to all requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          localStorage.setItem('access_token', data.access_token);
          error.config.headers.Authorization = `Bearer ${data.access_token}`;
          
          return api(error.config);
        } catch {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);
```

**File: `frontend/src/services/authService.ts`**

```typescript
import { api } from './api';

export const authService = {
  async register(email: string, password: string, firstName?: string, lastName?: string) {
    const { data } = await api.post('/auth/register', {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
    });
    return data;
  },

  async login(email: string, password: string) {
    const { data } = await api.post('/auth/login', {
      email,
      password,
    });
    return data;
  },

  async oauthCallback(code: string, provider: string, redirectUri: string) {
    const { data } = await api.post('/auth/oauth/callback', {
      code,
      provider,
      redirect_uri: redirectUri,
    });
    return data;
  },
};
```

---

## Phase 4: Testing Strategy

### 4.1 Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures
├── test_auth.py                   # Authentication tests
├── test_users.py                  # User profile tests
├── test_properties.py             # Property interaction tests
├── test_shared_feeds.py           # Shared feed tests
├── test_viewing_calendar.py       # Calendar tests
├── test_feed.py                   # Personalized feed tests
└── integration/
    ├── __init__.py
    ├── test_auth_flow.py          # Full auth flow
    ├── test_sharing_flow.py       # Shared feed flow
    └── test_viewing_flow.py       # Viewing calendar flow
```

### 4.2 Sample Tests

**File: `backend/tests/test_auth.py`**

```python
import pytest
from app.security.password import hash_password, verify_password
from app.security.jwt_handler import create_access_token, verify_token
from app.crud import create_user, get_user_by_email

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "securepassword123",
        "first_name": "Test",
        "last_name": "User",
    }

def test_password_hashing():
    password = "mypassword"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_create_and_verify_token():
    user_id = 123
    token = create_access_token(user_id)
    
    assert token is not None
    verified_id = verify_token(token)
    assert verified_id == user_id

def test_create_user(test_user_data):
    hashed_pwd = hash_password(test_user_data["password"])
    user = create_user(
        email=test_user_data["email"],
        hashed_password=hashed_pwd,
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
    )
    
    assert user["id"] > 0
    assert user["email"] == test_user_data["email"]
    assert user["is_active"] == True

def test_get_user_by_email(test_user_data):
    hashed_pwd = hash_password(test_user_data["password"])
    create_user(
        email=test_user_data["email"],
        hashed_password=hashed_pwd,
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
    )
    
    user = get_user_by_email(test_user_data["email"])
    assert user is not None
    assert user["email"] == test_user_data["email"]
```

**File: `backend/tests/test_properties.py`**

```python
import pytest
from app.crud import (
    star_property, unstar_property, get_user_stars,
    mark_unavailable, unmark_unavailable
)

@pytest.fixture
def setup_data(test_user_data):
    """Setup test user and property."""
    from app.crud import create_user, create_property
    from app.security.password import hash_password
    
    user = create_user(
        email=test_user_data["email"],
        hashed_password=hash_password(test_user_data["password"]),
    )
    
    property_data = {
        "rightmove_id": "test_prop_123",
        "listing_title": "Test Property",
        "price": 1200,
    }
    prop = create_property(property_data)
    
    return {"user": user, "property": prop}

def test_star_property(setup_data):
    user = setup_data["user"]
    property = setup_data["property"]
    
    star_property(user["id"], property["id"])
    starred = get_user_stars(user["id"], 10, 0)
    
    assert len(starred) == 1
    assert starred[0]["id"] == property["id"]

def test_unstar_property(setup_data):
    user = setup_data["user"]
    property = setup_data["property"]
    
    star_property(user["id"], property["id"])
    unstar_property(user["id"], property["id"])
    starred = get_user_stars(user["id"], 10, 0)
    
    assert len(starred) == 0

def test_mark_unavailable(setup_data):
    user = setup_data["user"]
    property = setup_data["property"]
    
    mark_unavailable(user["id"], property["id"])
    unavailable = get_user_unavailable(user["id"], 10, 0)
    
    assert len(unavailable) == 1
```

**File: `backend/tests/integration/test_auth_flow.py`**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_registration_and_login_flow(client):
    # Register
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "first_name": "New",
            "last_name": "User",
        }
    )
    
    assert register_response.status_code == 201
    register_data = register_response.json()
    assert "access_token" in register_data
    assert "refresh_token" in register_data
    
    # Logout (optional)
    # ...
    
    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "newuser@example.com",
            "password": "securepassword123",
        }
    )
    
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data

def test_protected_endpoint_requires_auth(client):
    # Try to access protected endpoint without token
    response = client.get("/api/users/me")
    assert response.status_code == 401
    
    # Register and get token
    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
        }
    )
    token = register_response.json()["access_token"]
    
    # Access protected endpoint with token
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

### 4.3 Pytest Configuration

**File: `backend/tests/conftest.py`**

```python
import pytest
import sqlite3
from pathlib import Path
import tempfile
from app.database import init_db, DATABASE_PATH

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database and initialize schema."""
    # Use temporary database for tests
    test_db = Path(tempfile.gettempdir()) / "test_rightmove.db"
    
    # Patch DATABASE_PATH
    import app.database
    original_path = app.database.DATABASE_PATH
    app.database.DATABASE_PATH = test_db
    
    # Initialize database
    init_db()
    
    yield
    
    # Cleanup
    if test_db.exists():
        test_db.unlink()
    
    app.database.DATABASE_PATH = original_path

@pytest.fixture(autouse=True)
def clear_database():
    """Clear database before each test."""
    from app.database import get_db
    
    with get_db() as conn:
        cursor = conn.cursor()
        # Disable foreign key checks
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        tables = [
            "property_comments",
            "property_status_tracking",
            "property_bookmarks",
            "user_votes",
            "vote_aggregates",
            "refresh_tokens",
            "shared_feed_properties",
            "shared_feed_members",
            "shared_feeds",
            "viewing_events",
            "user_profiles",
            "users",
            "ratings",
            "properties",
        ]
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        
        # Re-enable foreign key checks
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
    
    yield
```

---

## Phase 5: Implementation Roadmap

### Phased Rollout (Recommended)

**Phase 1 (Week 1-2): Core Authentication**
- [x] Database schema for users
- [ ] Password hashing & JWT implementation
- [ ] Register/login endpoints
- [ ] Frontend auth pages
- [ ] Protected routes

**Phase 2 (Week 3-4): User Profiles & Preferences**
- [ ] User profile endpoints
- [ ] Preference management
- [ ] Notification settings
- [ ] Frontend profile pages

**Phase 3 (Week 5-6): Property Interactions**
- [ ] Star/bookmark system
- [ ] Property status tracking (viewing → offer → accepted)
- [ ] Comments system
- [ ] Enhanced property cards

**Phase 4 (Week 7-8): Viewing Calendar**
- [ ] Calendar CRUD operations
- [ ] Calendar export services (Google, Apple, Outlook)
- [ ] Frontend calendar component
- [ ] Viewing reminders

**Phase 5 (Week 9-10): Shared Feeds**
- [ ] Shared feed creation & management
- [ ] Invite system with shareable codes
- [ ] WebSocket real-time updates
- [ ] Frontend shared feed pages

**Phase 6 (Week 11-12): Personalization & Polish**
- [ ] Preference-based feed recommendations
- [ ] OAuth2 integration (Google, Apple, Microsoft, Facebook)
- [ ] Testing & bug fixes
- [ ] Performance optimization

---

## Phase 6: Migration Strategy for Existing Data

### SQLite to PostgreSQL (Future)

If you need to upgrade from SQLite to PostgreSQL:

1. **Add Alembic for migrations:**
   ```bash
   pip install alembic
   alembic init alembic
   ```

2. **Create migration from existing schema:**
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   ```

3. **Keep data intact:**
   ```bash
   # Export from SQLite
   sqlite3 rightmove.db .dump > backup.sql
   
   # Import to PostgreSQL
   psql -U postgres database_name < backup.sql
   ```

### Backward Compatibility

- Support both old (unauthenticated) and new (authenticated) property endpoints for transition period
- Properties remain accessible without authentication
- User features are optional add-ons

---

## Environment Variables

**`.env` template:**

```env
# Database
DATABASE_URL=sqlite:///./data/rightmove.db

# Security
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth2
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
APPLE_CLIENT_ID=your-apple-client-id
APPLE_CLIENT_SECRET=your-apple-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret

# Frontend
FRONTEND_URL=http://localhost:5173

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@propertyfinder.com

# API Keys
APIFY_API_TOKEN=your-apify-token
GOOGLE_CALENDAR_API_KEY=your-api-key
```

---

## Summary

This implementation plan provides:

1. **Complete database schema** with all user, property interaction, and calendar tables
2. **FastAPI endpoints** for all features (auth, profile, properties, calendar, shared feeds)
3. **React components** for all pages and features
4. **Authentication system** with JWT, OAuth2, and refresh tokens
5. **Real-time updates** via WebSocket for shared feeds
6. **Calendar integrations** for Google, Apple, and Outlook
7. **Testing strategy** with unit and integration tests
8. **Phased rollout plan** to implement features incrementally
9. **Migration path** from SQLite to PostgreSQL if needed

The total estimated implementation time is **12 weeks** for a team of 2-3 developers.

**Next Steps:**
1. Review and finalize database schema
2. Set up development environment with dependencies
3. Implement Phase 1 (authentication)
4. Add integration tests as you go
5. Deploy to staging/production incrementally
