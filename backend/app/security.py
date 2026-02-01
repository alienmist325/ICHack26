"""
Security utilities for authentication, password hashing, and JWT tokens.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """JWT token payload data"""

    user_id: int
    email: str
    type: str  # "access" or "refresh"


class TokenResponse(BaseModel):
    """Token response containing access and refresh tokens"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: int, email: str, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "user_id": user_id,
        "email": email,
        "type": "access",
        "exp": expire,
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    user_id: int, email: str, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token."""
    if expires_delta is None:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "user_id": user_id,
        "email": email,
        "type": "refresh",
        "exp": expire,
    }

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify a JWT token and return the payload.

    Args:
        token: The JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        TokenData if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            return None

        user_id = payload.get("user_id")
        email = payload.get("email")

        if user_id is None or email is None:
            return None

        return TokenData(user_id=user_id, email=email, type=token_type)

    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None


def create_token_pair(user_id: int, email: str) -> TokenResponse:
    """
    Create both access and refresh tokens.

    Returns:
        TokenResponse containing both tokens and expiration info
    """
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id, email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
    )


def generate_invite_token() -> str:
    """Generate a secure random token for shared feed invites."""
    import secrets

    return secrets.token_urlsafe(32)
