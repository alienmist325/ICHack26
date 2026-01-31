"""Pydantic models for property verification service."""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class VerificationStatus(str, Enum):
    """Possible verification statuses for a property."""

    PENDING = "pending"
    PROCESSING = "processing"
    AVAILABLE = "available"
    SOLD = "sold"
    RENTED = "rented"
    UNCLEAR = "unclear"
    PENDING_REVIEW = "pending_review"
    FAILED = "failed"


class JobStatus(str, Enum):
    """Possible job statuses during verification."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VerificationJob(BaseModel):
    """Represents a property verification job."""

    job_id: str = Field(..., description="Unique job identifier")
    property_id: int = Field(..., description="Property ID to verify")
    status: JobStatus = Field(
        default=JobStatus.QUEUED, description="Current job status"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Job creation time"
    )
    started_at: Optional[datetime] = Field(default=None, description="Job start time")
    completed_at: Optional[datetime] = Field(
        default=None, description="Job completion time"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if job failed"
    )


class ElevenLabsCallResponse(BaseModel):
    """Response from ElevenLabs Agents API call."""

    call_id: str = Field(..., description="Unique call identifier from ElevenLabs")
    status: str = Field(..., description="Call status (e.g., 'initiated', 'completed')")
    transcript: Optional[str] = Field(default=None, description="Call transcript")
    duration_ms: Optional[int] = Field(
        default=None, description="Call duration in milliseconds"
    )
    ended_by: Optional[str] = Field(default=None, description="Who ended the call")


class VerificationResult(BaseModel):
    """Result of property verification."""

    property_id: int = Field(..., description="Property ID")
    verification_status: VerificationStatus = Field(
        ..., description="Verification status determination"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )
    call_transcript: Optional[str] = Field(
        default=None, description="Agent's transcript"
    )
    call_duration_seconds: Optional[int] = Field(
        default=None, description="Call duration"
    )
    agent_response: Optional[str] = Field(
        default=None, description="Summary of agent response"
    )
    notes: Optional[str] = Field(default=None, description="Verification notes")
    error_message: Optional[str] = Field(
        default=None, description="Error details if failed"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation time"
    )


class VerificationRequest(BaseModel):
    """Request to verify a property."""

    property_id: int = Field(..., description="Property ID to verify")

    model_config = ConfigDict(json_schema_extra={"example": {"property_id": 123}})


class JobStatusResponse(BaseModel):
    """Response for job status query."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    created_at: datetime = Field(..., description="Job creation time")
    started_at: Optional[datetime] = Field(default=None, description="Job start time")
    completed_at: Optional[datetime] = Field(
        default=None, description="Job completion time"
    )
    result: Optional[VerificationResult] = Field(
        default=None, description="Verification result if completed"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "job_uuid_here",
                "status": "completed",
                "created_at": "2025-02-01T12:00:00Z",
                "started_at": "2025-02-01T12:00:05Z",
                "completed_at": "2025-02-01T12:02:30Z",
                "result": {
                    "property_id": 123,
                    "verification_status": "available",
                    "confidence_score": 0.95,
                    "call_duration_seconds": 145,
                },
            }
        }
    )


class VerificationStartResponse(BaseModel):
    """Response when verification job is started."""

    job_id: str = Field(..., description="Job identifier for polling")
    property_id: int = Field(..., description="Property being verified")
    status: JobStatus = Field(
        default=JobStatus.QUEUED, description="Initial job status"
    )
    message: str = Field(..., description="Status message")
    poll_url: str = Field(..., description="URL to poll for job status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "job_uuid_here",
                "property_id": 123,
                "status": "queued",
                "message": "Verification job queued successfully",
                "poll_url": "/api/verify/job/job_uuid_here",
            }
        }
    )


class PropertyVerificationStatus(BaseModel):
    """Property verification status in response."""

    property_id: int = Field(..., description="Property ID")
    verification_status: VerificationStatus = Field(
        ..., description="Current verification status"
    )
    last_verified_at: Optional[datetime] = Field(
        default=None, description="Last verification time"
    )
    verification_notes: Optional[str] = Field(
        default=None, description="Verification notes"
    )
