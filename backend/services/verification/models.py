"""Data models for Bland AI verification service."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class VerificationStatus(str, Enum):
    """Status of property verification."""

    UNVERIFIED = "UNVERIFIED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNSURE = "UNSURE"


class BlandCallRequest(BaseModel):
    """Request model for Bland AI API call."""

    phone_number: str
    task: str
    language: str = "en"
    voice_id: int = 0


class BlandCallResponse(BaseModel):
    """Response model when initiating a Bland AI call."""

    call_id: str
    status: str


class BlandCallResult(BaseModel):
    """Result model for a completed Bland AI call."""

    call_id: str
    status: str
    duration: int
    transcript: Optional[str] = None
    success: bool
    data: Optional[Dict[str, Any]] = None


class VerificationRequest(BaseModel):
    """Request to verify a property."""

    property_id: int


class VerificationResult(BaseModel):
    """Result of property verification."""

    property_id: int
    verification_status: VerificationStatus
    last_verified_at: str
    verification_notes: Optional[str] = None
    transcript: Optional[str] = None
