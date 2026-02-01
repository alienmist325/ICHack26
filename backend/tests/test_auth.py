"""
Authentication tests for the Rightmove API.

Tests cover:
- Password hashing and verification
- JWT token creation and verification
- User registration
- User login
- Token refresh
- Token expiration and validation
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.crud import create_user, get_user_by_email, get_user_by_id


@pytest.mark.auth
class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_creates_different_hash(self):
        """Test that hashing a password produces a hash different from the original."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert "$2" in hashed  # bcrypt hash format

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "MySecurePassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "MySecurePassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self):
        """Test that empty password doesn't match any hash."""
        hashed = hash_password("some_password")
        assert verify_password("", hashed) is False

    def test_same_password_produces_different_hashes(self):
        """Test that the same password produces different hashes (due to salt)."""
        password = "MySecurePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


@pytest.mark.auth
class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test that access token is created successfully."""
        user_id = 123
        token = create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test that refresh token is created successfully."""
        user_id = 123
        token = create_refresh_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_and_refresh_tokens_are_different(self):
        """Test that access and refresh tokens are different."""
        user_id = 123
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        assert access_token != refresh_token

    def test_verify_token_valid(self):
        """Test that verify_token returns user_id for valid token."""
        user_id = 123
        token = create_access_token(user_id)

        verified_id = verify_token(token)
        assert verified_id == user_id

    def test_verify_token_invalid(self):
        """Test that verify_token returns None for invalid token."""
        invalid_token = "invalid.token.here"
        verified_id = verify_token(invalid_token)

        assert verified_id is None

    def test_verify_token_malformed(self):
        """Test that verify_token handles malformed tokens gracefully."""
        malformed_token = "notavalidjwt"
        verified_id = verify_token(malformed_token)

        assert verified_id is None

    def test_token_contains_user_id(self, test_user):
        """Test that token correctly encodes user_id."""
        user_id = test_user["id"]
        token = create_access_token(user_id)

        verified_id = verify_token(token)
        assert verified_id == user_id


@pytest.mark.auth
class TestUserRegistration:
    """Test user registration functionality."""

    def test_create_user_successfully(self, test_user_data):
        """Test creating a new user."""
        hashed_pwd = hash_password(test_user_data["password"])
        user = create_user(
            email=test_user_data["email"],
            hashed_password=hashed_pwd,
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
        )

        assert user is not None
        assert user["email"] == test_user_data["email"]
        assert user["first_name"] == test_user_data["first_name"]
        assert user["last_name"] == test_user_data["last_name"]
        assert user["is_active"] is True
        assert user["id"] > 0

    def test_create_user_without_password(self):
        """Test creating a user without password (OAuth-only account)."""
        user = create_user(
            email="oauth_user@example.com",
            hashed_password=None,
            first_name="OAuth",
            last_name="User",
        )

        assert user is not None
        assert user["email"] == "oauth_user@example.com"
        assert user["hashed_password"] is None

    def test_create_duplicate_user_fails(self, test_user_data):
        """Test that creating a user with duplicate email fails."""
        hashed_pwd = hash_password(test_user_data["password"])

        # Create first user
        create_user(
            email=test_user_data["email"],
            hashed_password=hashed_pwd,
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
        )

        # Try to create duplicate - should fail
        with pytest.raises(Exception):  # Should raise IntegrityError
            create_user(
                email=test_user_data["email"],
                hashed_password=hash_password("different_password"),
                first_name="Different",
                last_name="User",
            )

    def test_get_user_by_email(self, test_user_data):
        """Test retrieving user by email."""
        hashed_pwd = hash_password(test_user_data["password"])
        created_user = create_user(
            email=test_user_data["email"],
            hashed_password=hashed_pwd,
            first_name=test_user_data["first_name"],
            last_name=test_user_data["last_name"],
        )

        retrieved_user = get_user_by_email(test_user_data["email"])

        assert retrieved_user is not None
        assert retrieved_user["id"] == created_user["id"]
        assert retrieved_user["email"] == test_user_data["email"]

    def test_get_user_by_id(self, test_user):
        """Test retrieving user by ID."""
        retrieved_user = get_user_by_id(test_user["id"])

        assert retrieved_user is not None
        assert retrieved_user["id"] == test_user["id"]
        assert retrieved_user["email"] == test_user["email"]

    def test_get_nonexistent_user(self):
        """Test that retrieving non-existent user returns None."""
        user = get_user_by_email("nonexistent@example.com")
        assert user is None


@pytest.mark.auth
@pytest.mark.integration
class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    def test_register_endpoint(self, client, test_user_data):
        """Test user registration endpoint."""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client, test_user):
        """Test that registering with duplicate email fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user["email"],
                "password": "SomePassword123!",
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json().get("detail", "").lower()

    def test_register_invalid_email(self, client):
        """Test that invalid email format is rejected."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not_an_email",
                "password": "SomePassword123!",
            },
        )

        assert response.status_code == 422

    def test_login_endpoint(self, client, test_user, test_user_data):
        """Test user login endpoint."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user, test_user_data):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user_data["email"],
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401
        assert "invalid" in response.json().get("detail", "").lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!",
            },
        )

        assert response.status_code == 401

    def test_refresh_token_endpoint(self, client, test_user_tokens):
        """Test token refresh endpoint."""
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": f"Bearer {test_user_tokens['refresh_token']}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_with_invalid_token(self, client):
        """Test refresh with invalid token."""
        response = client.post(
            "/auth/refresh",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401

    def test_logout_endpoint(self, client, test_user_tokens):
        """Test logout endpoint."""
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {test_user_tokens['access_token']}"},
        )

        assert response.status_code == 200

    def test_get_current_user(self, client, authenticated_client, test_user):
        """Test getting current user info."""
        response = authenticated_client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user["id"]
        assert data["email"] == test_user["email"]

    def test_get_current_user_without_auth(self, client):
        """Test that getting current user without auth fails."""
        response = client.get("/auth/me")

        assert response.status_code == 401

    def test_get_current_user_with_invalid_token(self, client):
        """Test that invalid token is rejected."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401
