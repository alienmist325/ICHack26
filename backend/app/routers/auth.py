"""
Authentication routes for user registration, login, and OAuth.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import sqlite3

from app.database import get_db
from app.schemas import (
    UserRegister,
    UserLogin,
    User,
    TokenResponse,
)
from app.security import (
    hash_password,
    verify_password,
    verify_token,
    create_token_pair,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: sqlite3.Connection = Depends(get_db),
) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    token = authorization[7:]  # Remove "Bearer " prefix
    token_data = verify_token(token, token_type="access")

    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Fetch user from database
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, email, is_active, created_at, updated_at FROM users WHERE id = ?",
        (token_data.user_id,),
    )
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=401, detail="User not found")

    user = User(**dict(row))
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    return user


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(user_data: UserRegister, db: sqlite3.Connection = Depends(get_db)):
    """
    Register a new user with email and password.

    Returns tokens for immediate authentication.
    """
    cursor = db.cursor()

    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    cursor.execute(
        "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
        (user_data.email, hashed_password),
    )
    db.commit()

    user_id = cursor.lastrowid or 0
    if user_id == 0:
        raise HTTPException(status_code=500, detail="Failed to create user")

    # Generate tokens
    token_response = create_token_pair(user_id, user_data.email)
    return token_response


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: sqlite3.Connection = Depends(get_db)):
    """
    Login with email and password.

    Returns tokens for authentication.
    """
    cursor = db.cursor()

    # Fetch user
    cursor.execute(
        "SELECT id, email, hashed_password, is_active FROM users WHERE email = ?",
        (user_data.email,),
    )
    user = cursor.fetchone()

    if not user or not verify_password(user_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="User account is inactive")

    # Generate tokens
    token_response = create_token_pair(int(user["id"]), user["email"])
    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    authorization: Optional[str] = Header(None),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Refresh access token using a valid refresh token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

    refresh_token_str = authorization[7:]  # Remove "Bearer " prefix
    token_data = verify_token(refresh_token_str, token_type="refresh")

    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Verify user still exists and is active
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, is_active FROM users WHERE id = ?", (token_data.user_id,)
    )
    user = cursor.fetchone()

    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Generate new tokens
    token_response = create_token_pair(token_data.user_id, token_data.email)
    return token_response


@router.post("/logout", status_code=204)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (invalidate refresh token on client side).
    """
    # In a production app, you'd invalidate the refresh token in the database
    # For now, clients should simply discard the token
    return None


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user
