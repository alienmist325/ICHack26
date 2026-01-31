# Property Availability Verification - Implementation Plan

**Status:** 📋 Ready for Review | **Date:** February 1, 2025  
**Feature:** ElevenLabs AI-based property availability verification  
**Scope:** Single property verification with async background jobs  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture & Design](#architecture--design)
3. [User Preferences & Decisions](#user-preferences--decisions)
4. [Database Schema Changes](#database-schema-changes)
5. [API Endpoint Specifications](#api-endpoint-specifications)
6. [Configuration & Secrets Management](#configuration--secrets-management)
7. [Module Structure & Implementation](#module-structure--implementation)
8. [Detailed Implementation Specifications](#detailed-implementation-specifications)
9. [Testing Strategy](#testing-strategy)
10. [Deployment & Operations](#deployment--operations)
11. [Cost Analysis](#cost-analysis)
12. [Compliance & Legal](#compliance--legal)
13. [Future Enhancements](#future-enhancements)
14. [Risk Assessment & Mitigation](#risk-assessment--mitigation)
15. [Implementation Roadmap](#implementation-roadmap)

---

## Executive Summary

### What We're Building

A property availability verification system that automatically calls property agents using ElevenLabs AI agents to determine if rental properties are still available for rent on Rightmove.

### Key Characteristics

- **Asynchronous Processing**: Fire-and-forget API call with job polling
- **Single Property Focus**: One verification per API call (scalable to batch later)
- **Intelligent AI**: ElevenLabs agents make autonomous decisions
- **Complete Audit Trail**: Every call logged with transcription and confidence score
- **Error Resilience**: Unclear responses flagged for manual review
- **Anonymous Caller**: No company identification (higher success rate)

### Why This Approach

| Aspect | Choice | Reasoning |
|--------|--------|-----------|
| **Queue System** | Python asyncio | Built-in, no external deps, upgradeable to Redis |
| **API Pattern** | Async with polling | Simple, RESTful, works with existing FastAPI |
| **Database** | SQLite (existing) | Sufficient, consistent, familiar to team |
| **Phone Provider** | Twilio | Most reliable, well-documented, ElevenLabs recommended |
| **Call Strategy** | Conversational AI | Higher success, more natural, captures nuance |
| **Error Handling** | pending_review status | Allows human review of ambiguous cases |

---

## Architecture & Design

### System Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                            │
│                                                                    │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────────┐ │
│  │  API Layer   │  ──→ │Service Layer │  ──→ │Verification     │ │
│  │              │      │              │      │Service          │ │
│  │POST /verify/ │      │Queue Job     │      │Execute Call     │ │
│  │GET /job/     │      │Get Property  │      │Parse Response   │ │
│  └──────────────┘      └──────────────┘      └─────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ↓ (async)
                    ┌──────────────────────┐
                    │  Background Job      │
                    │  Queue (asyncio)     │
                    │                      │
                    │ • QUEUED → PROCESSING│
                    │ • COMPLETED/FAILED   │
                    │ • In-memory storage  │
                    └──────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ↓                           ↓
        ┌──────────────┐          ┌─────────────────────┐
        │  SQLite DB   │          │  ElevenLabs API     │
        │              │          │                     │
        │ • properties │          │ • Voice synthesis   │
        │ • verification          │ • Speech recognition│
        │   _logs      │          │ • Agent decision    │
        │              │          │ • Call management   │
        └──────────────┘          └─────────────────────┘
```

### Data Flow Sequence

```
1. User: POST /api/verify/property/123
         └─ Check property exists & has agent_phone
         └─ Generate job_id & queue job
         └─ Return 202 Accepted {job_id, status: "queued"}

2. Background Worker (asyncio event loop)
         └─ Pick job from queue
         └─ Update status to "processing"
         └─ Get property details from DB
         └─ Call ElevenLabs API with agent_phone
         └─ ElevenLabs dials property agent
         └─ AI converses & determines availability
         └─ Get transcript & call result
         └─ Parse response with keyword matching
         └─ Create verification_log entry
         └─ Update property verification_status
         └─ Update job status to "completed"

3. User: GET /api/verify/job/{job_id}
         └─ If status == "processing": Return 202 with current status
         └─ If status == "completed": Return 200 with result
         └─ If status == "failed": Return 200 with error details
```

---

## User Preferences & Decisions

✅ **All captured from your responses:**

### 1. Architecture Approach
**Chosen:** Single property verification (not batch)
- ✅ Per-property control
- ✅ Easier error handling
- ✅ Simpler implementation
- ℹ️ Batch calling available as future enhancement

### 2. Background Job System
**Chosen:** Python asyncio-based queue (not Celery/APScheduler)
- ✅ No external dependencies
- ✅ Lightweight & efficient
- ✅ Built into FastAPI/Python
- 📈 Upgradeable to Redis/Celery later

### 3. Caller Identification
**Chosen:** Neutral/Anonymous (no company name)
- ✅ Higher call success rate
- ✅ Less likely to be screened
- ✅ Professional & natural
- ℹ️ Can be customized per agent if needed later

### 4. Unclear Response Handling
**Chosen:** Mark as `pending_review` (not auto-retry or default unverifiable)
- ✅ Allows human review with full transcript
- ✅ Captures edge cases for analysis
- ✅ Maintains data integrity
- 📝 Reviewers can see exact what agent said

---

## Database Schema Changes

### 2.1 Properties Table Alterations

Add three columns to existing `properties` table:

```sql
-- Column 1: Verification Status
ALTER TABLE properties ADD COLUMN verification_status TEXT DEFAULT 'pending';
-- Values: 'pending', 'available', 'sold', 'unverifiable', 'pending_review'
-- Default 'pending' means: not yet verified

-- Column 2: Last Verification Timestamp
ALTER TABLE properties ADD COLUMN last_verified_at TEXT;
-- Format: ISO 8601 (YYYY-MM-DD HH:MM:SS+00:00)
-- NULL = never verified

-- Column 3: Human-readable Status Notes
ALTER TABLE properties ADD COLUMN verification_notes TEXT;
-- Example: "Agent confirmed available on 2025-02-01"
-- Example: "Voicemail reached, unclear response"
-- Example: "Rented out as of last call"
```

### 2.2 Verification Logs Table (New)

Complete audit trail for compliance & debugging:

```sql
CREATE TABLE verification_logs (
    -- Primary & Foreign Keys
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL UNIQUE,
    
    -- Call Information
    call_timestamp TEXT NOT NULL,           -- When call was made
    call_duration_seconds INTEGER,          -- How long the call lasted
    agent_phone TEXT,                       -- Who we called
    
    -- Results
    agent_response TEXT,                    -- Full transcription/AI output
    verification_status TEXT,               -- 'available', 'sold', 'unverifiable', 'pending_review'
    confidence_score REAL,                  -- 0.0 to 1.0 confidence level
    notes TEXT,                             -- Context/reasoning for decision
    
    -- Error Tracking
    error_message TEXT,                     -- If call failed, error details
    
    -- Metadata
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Relationships
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
);

-- Performance Indexes
CREATE INDEX idx_verification_logs_property_id ON verification_logs(property_id);
CREATE INDEX idx_verification_logs_timestamp ON verification_logs(call_timestamp);
CREATE INDEX idx_verification_logs_status ON verification_logs(verification_status);
```

### Migration Path

```sql
-- Step 1: Add columns to properties table (idempotent)
ALTER TABLE properties ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'pending';
ALTER TABLE properties ADD COLUMN IF NOT EXISTS last_verified_at TEXT;
ALTER TABLE properties ADD COLUMN IF NOT EXISTS verification_notes TEXT;

-- Step 2: Create verification_logs table (idempotent)
CREATE TABLE IF NOT EXISTS verification_logs (...);

-- Step 3: Create indexes (idempotent)
CREATE INDEX IF NOT EXISTS idx_verification_logs_property_id ...;
```

---

## API Endpoint Specifications

### Endpoint 1: Initiate Property Verification

**URL:** `POST /api/verify/property/{property_id}`

**Description:** Queue a verification job for a property

**Path Parameters:**
```
property_id: int (required)
  - Database ID of property to verify
  - Must exist in properties table
  - Must have non-empty agent_phone
```

**Request Body:**
```json
{}
```
(Empty body - all parameters in path)

**Success Response (202 Accepted):**
```json
{
  "job_id": "verify_prop_12345_abc123def456",
  "property_id": 12345,
  "status": "queued",
  "message": "Verification job queued successfully"
}
```

**Error Responses:**

| Status | Error | Reason | User Action |
|--------|-------|--------|-------------|
| 404 | Property not found | Property ID doesn't exist | Use valid property ID |
| 400 | Missing agent_phone | Property has no phone number | Add agent_phone to property |
| 409 | Verification already in progress | Another job pending | Wait or check status |
| 500 | Internal server error | System error | Contact support |

**Example Requests:**
```bash
# Valid request
curl -X POST http://localhost:8000/api/verify/property/12345

# Response
{
  "job_id": "verify_prop_12345_abc123",
  "property_id": 12345,
  "status": "queued",
  "message": "Verification job queued successfully"
}
```

---

### Endpoint 2: Poll Verification Job Status

**URL:** `GET /api/verify/job/{job_id}`

**Description:** Get current status and results of a verification job

**Path Parameters:**
```
job_id: str (required)
  - Returned from POST /api/verify/property/{property_id}
  - Format: "verify_prop_{property_id}_{random_string}"
```

**Query Parameters:** None

**Success Response (200 OK - Completed):**
```json
{
  "job_id": "verify_prop_12345_abc123",
  "property_id": 12345,
  "status": "completed",
  "result": {
    "verification_status": "available",
    "confidence_score": 0.95,
    "notes": "Agent confirmed property is available, lease terms discussed",
    "call_timestamp": "2025-02-01T10:30:00+00:00",
    "call_duration_seconds": 120
  }
}
```

**In Progress Response (202 Accepted):**
```json
{
  "job_id": "verify_prop_12345_abc123",
  "property_id": 12345,
  "status": "processing",
  "message": "Call in progress... (estimated 2 minutes)"
}
```

**Completed with Error Response (200 OK):**
```json
{
  "job_id": "verify_prop_12345_abc123",
  "property_id": 12345,
  "status": "failed",
  "error": "No answer / voicemail reached"
}
```

**Status Enum Values:**
| Value | Meaning | User Should |
|-------|---------|------------|
| `queued` | Waiting in queue | Wait and retry polling |
| `processing` | Call in progress | Wait and retry polling |
| `completed` | Finished successfully | Check result |
| `failed` | Call failed/error | Check error message, may retry |

**Error Responses:**

| Status | Error | Reason |
|--------|-------|--------|
| 404 | Job not found | Job ID is invalid or expired |
| 500 | Internal server error | System error |

**Example Usage:**
```bash
# After getting job_id from POST request
JOB_ID="verify_prop_12345_abc123"

# Poll in loop until completed
for i in {1..30}; do
  curl -s http://localhost:8000/api/verify/job/$JOB_ID | jq .
  sleep 5
done
```

---

## Configuration & Secrets Management

### 4.1 Environment Variables

Create/update `.env` file in project root:

```bash
# ============================================================================
# EXISTING CONFIGURATION
# ============================================================================
APIFY_API_KEY=your_apify_api_key_here

# ============================================================================
# NEW: ElevenLabs Configuration
# ============================================================================

# Required: Your ElevenLabs API Key
# Get from: https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_API_KEY=sk_your_actual_key_here

# Optional: Pre-configured Agent ID for property verification
# Get from: https://elevenlabs.io/app/agents/create or existing agent
ELEVENLABS_AGENT_ID=your_agent_id_here

# Optional: Twilio phone number for outbound calls
# Format: +1234567890 (E.164 format)
# Get from: Twilio console or your existing number
ELEVENLABS_PHONE_NUMBER=+1234567890

# ============================================================================
# VERIFICATION SERVICE CONFIGURATION
# ============================================================================

# Maximum seconds to wait for a call to complete (default: 600 = 10 minutes)
VERIFICATION_CALL_TIMEOUT=600

# Maximum concurrent calls at once (default: 5)
VERIFICATION_MAX_CONCURRENT_CALLS=5
```

### 4.2 Settings Class Update (backend/config.py)

```python
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Configuration for Rightmove scraper and verification services."""
    
    # Existing configuration
    apify_api_key: str = Field(
        ..., 
        description="Apify API key for scraper access"
    )
    
    # ========================================================================
    # NEW: ElevenLabs Verification Configuration
    # ========================================================================
    
    elevenlabs_api_key: str = Field(
        default="",
        description="ElevenLabs API key for voice verification calls"
    )
    
    elevenlabs_agent_id: Optional[str] = Field(
        default=None,
        description="ElevenLabs Agent ID for property verification"
    )
    
    elevenlabs_phone_number: Optional[str] = Field(
        default=None,
        description="Pre-configured phone number for outbound calls (E.164 format)"
    )
    
    verification_call_timeout: int = Field(
        default=600,
        description="Maximum seconds to wait for verification call to complete"
    )
    
    verification_max_concurrent: int = Field(
        default=5,
        description="Maximum concurrent verification calls"
    )
    
    # ========================================================================
    # Configuration Class (Pydantic v2)
    # ========================================================================
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create singleton instance
try:
    settings = Settings()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise
```

### 4.3 Security Best Practices

```
⚠️ SECURITY CHECKLIST:

☑️ Never commit .env file to git (add to .gitignore)
☑️ Use strong, unique API keys
☑️ Rotate keys periodically
☑️ Store secrets in secure vault for production (AWS Secrets Manager, HashiCorp Vault)
☑️ Log API keys as "***" in debug output (never full key)
☑️ Validate all phone numbers (E.164 format)
☑️ Implement rate limiting on API endpoints
☑️ Use HTTPS only for all external API calls
```

---

## Module Structure & Implementation

### 5.1 Directory Layout

```
backend/
├── services/                              # NEW DIRECTORY
│   ├── __init__.py                        # Package marker
│   └── verification/                      # NEW SUBDIRECTORY
│       ├── __init__.py                    # Package marker + exports
│       ├── models.py                      # Pydantic schemas (NEW)
│       ├── elevenlabs_client.py           # 11Labs API wrapper (NEW)
│       ├── jobs.py                        # Background job queue (NEW)
│       └── service.py                     # Core verification logic (NEW)
│
├── app/
│   ├── main.py                            # UPDATED: Add /api/verify/* endpoints
│   ├── crud.py                            # UPDATED: Add verification CRUD operations
│   ├── schemas.py                         # UPDATED: Add verification request/response schemas
│   ├── database.py                        # UPDATED: Add verification tables
│   └── ...other files (unchanged)
│
├── tests/
│   ├── test_verification_service.py       # NEW: Unit tests
│   ├── test_verification_integration.py   # NEW: Integration tests
│   └── test_integration.py                # EXISTING: Maintain existing tests
│
├── config.py                              # UPDATED: Add ElevenLabs settings
└── ...other files
```

### 5.2 What Each File Does

| File | Purpose | New? | Key Exports |
|------|---------|------|-------------|
| `models.py` | Pydantic data models | ✅ | `VerificationStatus`, `JobStatus`, `VerificationResult`, `VerificationJobResponse` |
| `elevenlabs_client.py` | HTTP wrapper for 11Labs API | ✅ | `ElevenLabsClient` class |
| `jobs.py` | Background job queue system | ✅ | `queue_verification_job()`, `get_job_status()`, `process_jobs_background()` |
| `service.py` | Business logic for verification | ✅ | `PropertyVerificationService` class |
| `main.py` | API endpoints | ✈️ | Add `POST /api/verify/property/{property_id}`, `GET /api/verify/job/{job_id}` |
| `crud.py` | Database operations | ✈️ | Add verification-related CRUD functions |
| `schemas.py` | Request/response schemas | ✈️ | Add verification request/response schemas |
| `database.py` | Database initialization | ✈️ | Add verification tables to `init_db()` |
| `config.py` | Configuration settings | ✈️ | Add ElevenLabs credentials |

(✅ = New file, ✈️ = Update existing file)

---

## Detailed Implementation Specifications

### 6.1 Pydantic Models (services/verification/models.py)

```python
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# ============================================================================
# ENUMS
# ============================================================================

class VerificationStatus(str, Enum):
    """Possible verification outcomes for a property."""
    PENDING = "pending"           # Not yet verified
    AVAILABLE = "available"       # Confirmed available for rent
    SOLD = "sold"                 # Property sold/rented out
    UNVERIFIABLE = "unverifiable" # Could not determine
    PENDING_REVIEW = "pending_review"  # Unclear - needs human review

class JobStatus(str, Enum):
    """States a verification job can be in."""
    QUEUED = "queued"             # Waiting to be processed
    PROCESSING = "processing"     # Currently making call
    COMPLETED = "completed"       # Finished successfully
    FAILED = "failed"             # Call failed or errored

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class VerificationRequest(BaseModel):
    """Request to verify a property."""
    property_id: int = Field(
        ..., 
        description="Database ID of property to verify"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "property_id": 12345
            }
        }
    )

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class VerificationResult(BaseModel):
    """Result of a completed verification call."""
    verification_status: VerificationStatus = Field(
        ..., 
        description="Determined availability status"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in determination (0.0 to 1.0)"
    )
    notes: str = Field(
        ...,
        description="Human-readable explanation of result"
    )
    call_timestamp: str = Field(
        ...,
        description="ISO format timestamp when call was made"
    )
    call_duration_seconds: int = Field(
        ...,
        ge=0,
        description="Length of call in seconds"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "verification_status": "available",
                "confidence_score": 0.95,
                "notes": "Agent confirmed property is available for immediate viewings",
                "call_timestamp": "2025-02-01T10:30:00+00:00",
                "call_duration_seconds": 120
            }
        }
    )

class VerificationJobResponse(BaseModel):
    """Response containing job status and optional results."""
    job_id: str = Field(..., description="Unique job identifier")
    property_id: int = Field(..., description="Property being verified")
    status: JobStatus = Field(..., description="Current job status")
    result: Optional[VerificationResult] = Field(
        default=None,
        description="Result if status is completed"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if status is failed"
    )
    message: Optional[str] = Field(
        default=None,
        description="Human-readable status message"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "verify_prop_12345_abc123",
                "property_id": 12345,
                "status": "completed",
                "result": {
                    "verification_status": "available",
                    "confidence_score": 0.95,
                    "notes": "Agent confirmed availability",
                    "call_timestamp": "2025-02-01T10:30:00+00:00",
                    "call_duration_seconds": 120
                },
                "error": None
            }
        }
    )

class InitiateVerificationResponse(BaseModel):
    """Immediate response when queueing a verification job."""
    job_id: str
    property_id: int
    status: JobStatus
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "verify_prop_12345_abc123",
                "property_id": 12345,
                "status": "queued",
                "message": "Verification job queued successfully"
            }
        }
    )
```

### 6.2 Background Job Queue (services/verification/jobs.py)

```python
import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

from .models import JobStatus, VerificationStatus, VerificationResult

# ============================================================================
# JOB DATA STRUCTURE
# ============================================================================

@dataclass
class VerificationJob:
    """Represents a single verification job."""
    job_id: str
    property_id: int
    status: JobStatus = JobStatus.QUEUED
    result: Optional[VerificationResult] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_response(self) -> Dict:
        """Convert job to API response dict."""
        response = {
            "job_id": self.job_id,
            "property_id": self.property_id,
            "status": self.status.value,
        }
        
        if self.result:
            response["result"] = {
                "verification_status": self.result.verification_status.value,
                "confidence_score": self.result.confidence_score,
                "notes": self.result.notes,
                "call_timestamp": self.result.call_timestamp,
                "call_duration_seconds": self.result.call_duration_seconds,
            }
        
        if self.error:
            response["error"] = self.error
        
        if self.status == JobStatus.PROCESSING:
            response["message"] = "Call in progress... (estimated 2 minutes)"
        elif self.status == JobStatus.QUEUED:
            response["message"] = "Verification job queued successfully"
        
        return response

# ============================================================================
# GLOBAL JOB STORE & QUEUE
# ============================================================================

# In-memory storage of all jobs (key: job_id, value: VerificationJob)
# TODO: Upgrade to Redis for distributed systems
_job_store: Dict[str, VerificationJob] = {}

# Async queue of jobs to process
_job_queue: asyncio.Queue = asyncio.Queue()

# Property IDs currently being processed (prevent duplicates)
_processing_properties: set = set()

# ============================================================================
# JOB QUEUE FUNCTIONS
# ============================================================================

def generate_job_id(property_id: int) -> str:
    """Generate unique job ID."""
    random_suffix = str(uuid.uuid4())[:8]
    return f"verify_prop_{property_id}_{random_suffix}"

async def queue_verification_job(property_id: int) -> str:
    """
    Queue a new verification job.
    
    Args:
        property_id: Property to verify
        
    Returns:
        job_id: Unique identifier for this job
        
    Raises:
        ValueError: If property already has pending job
    """
    # Check if already processing this property
    if property_id in _processing_properties:
        raise ValueError(f"Verification already in progress for property {property_id}")
    
    # Generate job ID
    job_id = generate_job_id(property_id)
    
    # Create job object
    job = VerificationJob(
        job_id=job_id,
        property_id=property_id,
        status=JobStatus.QUEUED
    )
    
    # Store job
    _job_store[job_id] = job
    _processing_properties.add(property_id)
    
    # Queue for processing
    await _job_queue.put(job)
    
    logger.info(f"Queued verification job {job_id} for property {property_id}")
    
    return job_id

async def get_job_status(job_id: str) -> Optional[VerificationJob]:
    """
    Retrieve job status.
    
    Args:
        job_id: Job identifier
        
    Returns:
        VerificationJob if found, None otherwise
    """
    return _job_store.get(job_id)

async def _mark_job_complete(job: VerificationJob) -> None:
    """Mark a property as no longer processing."""
    if job.property_id in _processing_properties:
        _processing_properties.discard(job.property_id)

async def process_jobs_background(
    verification_service: "PropertyVerificationService"
) -> None:
    """
    Background worker that continuously processes verification jobs.
    
    This should run in a background asyncio task:
    
    Example:
        asyncio.create_task(process_jobs_background(service))
    
    Args:
        verification_service: Service instance to execute verifications
    """
    logger.info("Starting background job processor...")
    
    while True:
        try:
            # Get next job (blocks until available)
            job = await _job_queue.get()
            
            try:
                # Execute the verification
                await verification_service.verify_property(job)
                
            except Exception as e:
                logger.error(f"Job {job.job_id} failed: {e}", exc_info=True)
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.completed_at = datetime.now(timezone.utc)
                
            finally:
                # Clean up processing flag
                await _mark_job_complete(job)
                
        except Exception as e:
            logger.error(f"Job processor error: {e}", exc_info=True)
            # Continue processing despite errors
            await asyncio.sleep(1)

# ============================================================================
# DEBUGGING/MONITORING
# ============================================================================

async def get_queue_stats() -> Dict:
    """Get current queue statistics (for monitoring)."""
    return {
        "jobs_in_queue": _job_queue.qsize(),
        "jobs_in_store": len(_job_store),
        "currently_processing": len(_processing_properties),
    }

async def list_all_jobs() -> Dict[str, VerificationJob]:
    """List all jobs (for debugging)."""
    return _job_store.copy()
```

### 6.3 ElevenLabs API Client (services/verification/elevenlabs_client.py)

```python
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class PhoneCallResponse:
    """Response from initiating a phone call."""
    def __init__(self, data: Dict[str, Any]):
        self.call_id = data.get("call_id")
        self.status = data.get("status", "initiated")
        self.data = data

class CallResultResponse:
    """Result of a completed phone call."""
    def __init__(self, data: Dict[str, Any]):
        self.call_id = data.get("call_id")
        self.status = data.get("status")
        self.transcript = data.get("transcript", "")
        self.duration = data.get("duration", 0)
        self.call_timestamp = data.get("call_timestamp")
        self.data = data

# ============================================================================
# ELEVENLABS CLIENT
# ============================================================================

class ElevenLabsClient:
    """
    Client for ElevenLabs Agents API.
    
    Handles outbound phone calls and result retrieval.
    
    Documentation: https://elevenlabs.io/docs/agents-platform
    """
    
    def __init__(self, api_key: str):
        """
        Initialize ElevenLabs client.
        
        Args:
            api_key: Your ElevenLabs API key (from https://elevenlabs.io/app/settings/api-keys)
        """
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io"
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    async def make_phone_call(
        self,
        phone_number_to_call: str,
        agent_id: str,
        from_number: str,
        dynamic_variables: Optional[Dict[str, str]] = None,
    ) -> PhoneCallResponse:
        """
        Initiate an outbound phone call using an ElevenLabs agent.
        
        Args:
            phone_number_to_call: Property agent's phone number (E.164 format: +1234567890)
            agent_id: ElevenLabs agent ID (from dashboard)
            from_number: Caller ID / Twilio number to call from
            dynamic_variables: Variables to pass to agent (e.g., property_address)
        
        Returns:
            PhoneCallResponse with call_id and status
        
        Raises:
            httpx.HTTPError: If API call fails
        """
        
        payload = {
            "phone_number": phone_number_to_call,
            "from_number": from_number,
            "agent_id": agent_id,
            "custom_variables": dynamic_variables or {},
        }
        
        logger.info(
            f"Initiating call to {phone_number_to_call} using agent {agent_id}"
        )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/agents/{agent_id}/call-initiate",
                    json=payload,
                    headers=self.headers,
                )
                response.raise_for_status()
                
                result = PhoneCallResponse(response.json())
                logger.info(f"Call initiated: {result.call_id}")
                return result
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"ElevenLabs API error: {e.status_code} - {e.response.text}"
                )
                raise
    
    async def get_call_result(
        self,
        call_id: str,
        agent_id: str
    ) -> CallResultResponse:
        """
        Retrieve results of a completed phone call.
        
        Args:
            call_id: The call ID returned from make_phone_call()
            agent_id: ElevenLabs agent ID (for authorization)
        
        Returns:
            CallResultResponse with transcript, duration, status
        
        Raises:
            httpx.HTTPError: If API call fails
        """
        
        logger.info(f"Retrieving call result: {call_id}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/v1/agents/calls/{call_id}",
                    headers=self.headers,
                )
                response.raise_for_status()
                
                result = CallResultResponse(response.json())
                logger.info(f"Call result retrieved: status={result.status}")
                return result
                
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"ElevenLabs API error: {e.status_code} - {e.response.text}"
                )
                raise
    
    async def wait_for_call_completion(
        self,
        call_id: str,
        agent_id: str,
        timeout_seconds: int = 600,
        poll_interval: int = 5,
    ) -> CallResultResponse:
        """
        Poll until call completes (blocking).
        
        Args:
            call_id: The call ID
            agent_id: Agent ID
            timeout_seconds: Maximum seconds to wait (default 10 min)
            poll_interval: Seconds between polls (default 5)
        
        Returns:
            CallResultResponse when complete
        
        Raises:
            TimeoutError: If call doesn't complete within timeout
            httpx.HTTPError: If API call fails
        """
        
        start_time = datetime.now(timezone.utc)
        
        while True:
            # Check timeout
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed > timeout_seconds:
                raise TimeoutError(
                    f"Call {call_id} did not complete within {timeout_seconds} seconds"
                )
            
            # Get current call status
            try:
                result = await self.get_call_result(call_id, agent_id)
                
                # Check if completed
                if result.status in ["completed", "failed"]:
                    return result
                
                # Still in progress, wait and retry
                logger.debug(f"Call {call_id} status: {result.status}, retrying in {poll_interval}s")
                await asyncio.sleep(poll_interval)
                
            except httpx.HTTPStatusError as e:
                if e.status_code == 404:
                    # Call not found yet, wait and retry
                    logger.debug(f"Call {call_id} not found yet, retrying...")
                    await asyncio.sleep(poll_interval)
                else:
                    raise
```

### 6.4 Verification Service (services/verification/service.py)

```python
import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from backend.config import settings
from app.schemas import Property
from .models import (
    VerificationStatus, 
    VerificationResult,
    JobStatus
)
from .jobs import VerificationJob
from .elevenlabs_client import ElevenLabsClient

logger = logging.getLogger(__name__)

# ============================================================================
# AGENT PROMPT TEMPLATE
# ============================================================================

VERIFICATION_AGENT_PROMPT = """You are a helpful and professional property inquiry assistant.

**YOUR TASK:** Verify if the property at {property_address} is currently available for rent.

**INSTRUCTIONS:**
1. Greet the agent/landlord professionally
2. Explain: "I'm calling to verify the availability of the property at {property_address}"
3. Ask: "Is this property currently available for rent?"
4. Listen carefully to their response
5. If unclear, ask ONE follow-up question
6. End the conversation within 2-3 minutes

**DECISION FRAMEWORK:**
- AVAILABLE: The agent clearly states the property IS available and showing is possible
- SOLD/RENTED: The agent states the property is NO LONGER available, rented out, or sold
- UNCLEAR: The agent is uncertain, wants to check something, or you cannot determine status

**HOW TO END:** Be clear about your determination:
- If available: "This property is AVAILABLE for rent"
- If sold/rented: "This property is SOLD or RENTED"
- If unclear: "I could not determine the status - this requires manual review"

**IMPORTANT:**
- Be brief and professional
- Do NOT identify with any company (stay neutral)
- If you reach voicemail, you may try to leave a brief message
- Always be polite and respectful

---
PROPERTY DETAILS:
- Address: {property_address}
- Agent Phone: {agent_phone}
- Reference: {property_id}
---"""

# ============================================================================
# VERIFICATION SERVICE
# ============================================================================

class PropertyVerificationService:
    """
    Service for verifying property availability via phone calls.
    
    Manages the entire verification workflow:
    1. Get property details
    2. Make phone call via ElevenLabs
    3. Parse AI response
    4. Store results in database
    5. Update property status
    """
    
    def __init__(self, db_service: "CRUDService", config=None):
        """
        Initialize verification service.
        
        Args:
            db_service: CRUD service for database operations
            config: Settings object (defaults to global settings)
        """
        self.db_service = db_service
        self.config = config or settings
        
        # Initialize ElevenLabs client
        if not self.config.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured")
        
        self.elevenlabs_client = ElevenLabsClient(
            api_key=self.config.elevenlabs_api_key
        )
    
    async def verify_property(self, job: VerificationJob) -> None:
        """
        Execute verification for a property.
        
        This is called by the background job processor.
        
        Args:
            job: VerificationJob to execute
        """
        try:
            # Mark as processing
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now(timezone.utc)
            logger.info(f"Starting verification for property {job.property_id}")
            
            # 1. Get property details
            property_obj = self.db_service.get_property(job.property_id)
            if not property_obj:
                raise ValueError(f"Property {job.property_id} not found")
            
            if not property_obj.agent_phone:
                raise ValueError("Property has no agent phone number")
            
            # 2. Prepare agent with dynamic variables
            agent_prompt = VERIFICATION_AGENT_PROMPT.format(
                property_address=property_obj.full_address or "Unknown",
                agent_phone=property_obj.agent_phone,
                property_id=property_obj.rightmove_id,
            )
            
            # 3. Make the phone call
            try:
                call_response = await self.elevenlabs_client.make_phone_call(
                    phone_number_to_call=property_obj.agent_phone,
                    agent_id=self.config.elevenlabs_agent_id,
                    from_number=self.config.elevenlabs_phone_number,
                    dynamic_variables={
                        "property_address": property_obj.full_address or "Unknown",
                        "property_id": property_obj.rightmove_id,
                    }
                )
                
                # 4. Wait for call to complete
                call_result = await self.elevenlabs_client.wait_for_call_completion(
                    call_id=call_response.call_id,
                    agent_id=self.config.elevenlabs_agent_id,
                    timeout_seconds=self.config.verification_call_timeout,
                )
                
                # 5. Parse the result
                verification_result = await self._parse_call_result(
                    call_result=call_result,
                    property_obj=property_obj
                )
                
                # 6. Store in database
                self.db_service.create_verification_log(
                    property_id=job.property_id,
                    call_timestamp=call_result.call_timestamp,
                    call_duration_seconds=call_result.duration,
                    agent_phone=property_obj.agent_phone,
                    agent_response=call_result.transcript,
                    verification_status=verification_result.verification_status.value,
                    confidence_score=verification_result.confidence_score,
                    notes=verification_result.notes,
                    error_message=None,
                )
                
                # 7. Update property verification status
                self.db_service.update_property_verification_status(
                    property_id=job.property_id,
                    status=verification_result.verification_status.value,
                    notes=verification_result.notes,
                    last_verified_at=call_result.call_timestamp,
                )
                
                # 8. Set job result
                job.result = verification_result
                job.status = JobStatus.COMPLETED
                
                logger.info(
                    f"Verification completed for property {job.property_id}: "
                    f"{verification_result.verification_status.value}"
                )
                
            except asyncio.TimeoutError:
                raise ValueError("Call timeout - property agent did not answer")
            except Exception as e:
                raise ValueError(f"Call failed: {str(e)}")
        
        except Exception as e:
            logger.error(
                f"Verification failed for property {job.property_id}: {e}",
                exc_info=True
            )
            job.status = JobStatus.FAILED
            job.error = str(e)
        
        finally:
            job.completed_at = datetime.now(timezone.utc)
    
    async def _parse_call_result(
        self,
        call_result: "CallResultResponse",
        property_obj: Property
    ) -> VerificationResult:
        """
        Parse ElevenLabs call result to determine availability.
        
        Uses keyword matching on the agent's response.
        
        Args:
            call_result: Result from ElevenLabs call
            property_obj: Property being verified
        
        Returns:
            VerificationResult with status and confidence
        """
        transcript = call_result.transcript or ""
        
        # Extract determination
        determination = self._extract_determination(transcript)
        confidence = self._calculate_confidence(transcript)
        
        # Create result
        result = VerificationResult(
            verification_status=determination,
            confidence_score=confidence,
            notes=self._generate_notes(determination, transcript),
            call_timestamp=call_result.call_timestamp or datetime.now(timezone.utc).isoformat(),
            call_duration_seconds=call_result.duration or 0,
        )
        
        return result
    
    def _extract_determination(self, transcript: str) -> VerificationStatus:
        """
        Extract availability determination from transcript.
        
        Uses keyword matching to classify response.
        
        Args:
            transcript: Agent's response/transcript
        
        Returns:
            VerificationStatus (AVAILABLE, SOLD, UNVERIFIABLE, or PENDING_REVIEW)
        """
        transcript_lower = transcript.lower()
        
        # Keywords for different statuses
        # These are tuples of (keywords, status)
        keyword_mappings = [
            (
                ["available", "yes still available", "yes it is", "in stock", "showing"],
                VerificationStatus.AVAILABLE
            ),
            (
                ["sold", "rented", "no longer available", "leased", "taken"],
                VerificationStatus.SOLD
            ),
            (
                ["maybe", "not sure", "check back", "unsure", "i'll check", "let me check"],
                VerificationStatus.PENDING_REVIEW
            ),
        ]
        
        # Check each mapping (order matters - check definitive first)
        for keywords, status in keyword_mappings:
            for keyword in keywords:
                if keyword in transcript_lower:
                    return status
        
        # Default: cannot determine
        return VerificationStatus.UNVERIFIABLE
    
    def _calculate_confidence(self, transcript: str) -> float:
        """
        Calculate confidence score (0.0 to 1.0) for the determination.
        
        Args:
            transcript: Agent's response
        
        Returns:
            Confidence score
        """
        # Very basic confidence calculation
        # More sophisticated: use sentiment analysis, LLM, etc.
        
        transcript_lower = transcript.lower()
        length = len(transcript)
        
        # Short transcripts = less confident
        if length < 50:
            return 0.5
        if length < 100:
            return 0.7
        
        # Check for definitive language
        definitive_words = [
            "yes", "no", "definitely", "confirmed", "absolutely"
        ]
        count = sum(1 for word in definitive_words if word in transcript_lower)
        
        # Scale confidence based on definitive language
        confidence = 0.75 + (count * 0.05)
        return min(confidence, 1.0)
    
    def _generate_notes(
        self,
        determination: VerificationStatus,
        transcript: str
    ) -> str:
        """Generate human-readable notes about the determination."""
        notes_map = {
            VerificationStatus.AVAILABLE: "Agent confirmed property is available for rent",
            VerificationStatus.SOLD: "Agent confirmed property is sold or rented out",
            VerificationStatus.UNVERIFIABLE: "Could not determine availability from call",
            VerificationStatus.PENDING_REVIEW: "Unclear response - manual review required",
        }
        
        base_note = notes_map.get(determination, "Verification completed")
        
        # Add first 200 chars of transcript for context
        if transcript:
            snippet = transcript[:200].replace("\n", " ").strip()
            return f"{base_note}. Agent said: \"{snippet}...\""
        
        return base_note
```

---

## Testing Strategy

### 8.1 Unit Tests (test_verification_service.py)

```python
# Tests for:
# - _extract_determination() with various transcripts
# - _calculate_confidence() with edge cases  
# - _generate_notes() output formatting
# - Keyword matching logic
# - Mock ElevenLabs API responses
# - Configuration loading
# - Error handling

Example tests:
- test_available_detection_with_positive_keywords()
- test_sold_detection_with_negative_keywords()
- test_unclear_detection_with_uncertain_keywords()
- test_confidence_score_calculation()
- test_confidence_increases_with_length()
- test_elevenlabs_client_initialization()
- test_mock_call_completion()
```

### 8.2 Integration Tests (test_verification_integration.py)

```python
# Tests for:
# - End-to-end verification flow with mock API
# - Database storage and retrieval
# - Job queueing and status updates
# - Property status updates
# - Concurrent job handling
# - Error scenarios (missing property, network failures)

Example tests:
- test_full_verification_workflow()
- test_verify_property_endpoint()
- test_poll_job_status()
- test_property_updated_after_verification()
- test_verification_log_created()
- test_concurrent_verifications()
- test_error_property_not_found()
- test_error_missing_agent_phone()
```

### 8.3 Manual Testing Checklist

```
□ Environment Setup
  □ ELEVENLABS_API_KEY configured in .env
  □ ELEVENLABS_AGENT_ID configured
  □ ELEVENLABS_PHONE_NUMBER configured (Twilio number)

□ Database
  □ New columns added to properties table
  □ verification_logs table created
  □ Indexes created successfully

□ API Endpoints
  □ POST /api/verify/property/{id} returns 202 with job_id
  □ GET /api/verify/job/{job_id} returns current status
  □ Polling shows status change from queued → processing → completed
  □ Error handling: missing property returns 404
  □ Error handling: missing phone returns 400
  □ Error handling: duplicate job returns 409

□ Data Storage
  □ verification_logs table populated after call
  □ properties table verification_status updated
  □ properties table last_verified_at set correctly
  □ properties table verification_notes populated

□ Edge Cases
  □ Unclear response marked as pending_review
  □ Call timeout handled gracefully
  □ API error doesn't crash background worker
  □ Multiple concurrent verifications work
```

---

## Deployment & Operations

### 9.1 Pre-Launch Checklist

```
CONFIGURATION
  □ Set ELEVENLABS_API_KEY in .env (or production vault)
  □ Create/configure ElevenLabs Agent
  □ Get Agent ID and configure ELEVENLABS_AGENT_ID
  □ Set up Twilio phone number (or use pre-configured)
  □ Configure ELEVENLABS_PHONE_NUMBER
  □ Test configuration loads without errors

DATABASE
  □ Run database migrations to add new columns
  □ Verify verification_logs table created
  □ Confirm indexes exist
  □ Backup production database

TESTING
  □ Run unit tests (should pass)
  □ Run integration tests (should pass)
  □ Zero pytest warnings
  □ Manual end-to-end test
  □ Test with at least 3 real properties

MONITORING
  □ Set up logging to track verifications
  □ Create alerts for failed jobs
  □ Monitor ElevenLabs API usage
  □ Track success rate

DOCUMENTATION
  □ Update README.md with new endpoints
  □ Document environment variables
  □ Create runbook for support team
  □ Document troubleshooting guide
```

### 9.2 Monitoring & Alerts

```python
# Metrics to track:
- Total verifications per day
- Success rate (completed / total)
- Average call duration
- Error rate by type
- ElevenLabs API usage (credits/month)
- Average confidence score
- Breakdown by status (available/sold/unclear)

# Alerts to set:
- High error rate (> 20%)
- API key invalid
- Phone number invalid
- Unusual call pattern (high volume spike)
```

---

## Cost Analysis

### 11.1 Per-Call Pricing

| Component | Cost | Notes |
|-----------|------|-------|
| ElevenLabs TTS | $0.15-0.30 | 2-3 minute call |
| ElevenLabs STT | Included | No additional cost |
| Twilio (if outbound) | ~$0.015 | May vary by region |
| **Total per call** | **$0.165-0.315** | Average $0.25 |

### 11.2 Scaling Scenarios

| Volume | Plan | Monthly Cost | Calls Included |
|--------|------|--------------|-----------------|
| 100 calls/month | Creator | $11 | ~360 calls |
| 500 calls/month | Creator | $11 | ~360 calls |
| 1000 calls/month | Pro | $99 | ~1,800 calls |
| 5000 calls/month | Scale | $330 | ~9,000 calls |

---

## Compliance & Legal

### 12.1 TCPA Compliance (US)

⚠️ **IMPORTANT**: When making automated calls in the US, comply with the Telephone Consumer Protection Act (TCPA):

```
✓ REQUIRED:
  - Caller ID set correctly
  - Do not call registry checked
  - Consent obtained beforehand
  - Unique identifier for each call
  - Callback number provided
  - Hours of operation disclosed

✗ DO NOT:
  - Call personal cell phones (use business only)
  - Call between 9 PM - 8 AM local time
  - Call numbers on Do Not Call registry
  - Use robocalls without prior written consent
  - Spoof caller ID
```

### 12.2 GDPR Compliance (Europe)

If processing EU data:
- Consent required before calling
- Right to be forgotten must be honoredbr/>- Data retention policy (e.g., delete after 30 days)
- Privacy policy must disclose automated calls

### 12.3 Audit Trail

The `verification_logs` table provides full audit trail:
- Who called (phone number)
- When (timestamp)
- How long (duration)
- What was said (transcript)
- Decision made (status + confidence)
- Any errors

This satisfies most compliance and legal review requirements.

---

## Future Enhancements

### 13.1 Batch Calling

Use ElevenLabs batch calling API for 100+ properties at once:
- CSV upload with phone numbers
- Scheduled execution
- Real-time progress monitoring
- Bulk result download

### 13.2 Redis Job Queue

Upgrade from in-memory to Redis for:
- Distributed processing (multiple servers)
- Job persistence (survive restart)
- Cluster support
- Advanced monitoring

### 13.3 Webhook Callbacks

Instead of polling:
- ElevenLabs calls webhook when done
- Webhook triggers database update
- Faster result notification

### 13.4 Call Recording

Store call audio for:
- Compliance/audit
- Dispute resolution
- Agent quality review
- Training/analysis

### 13.5 LLM-Based Parsing

Use GPT-4 for more sophisticated:
- Sentiment analysis
- Intent extraction
- Structured data collection
- Multi-language support

---

## Risk Assessment & Mitigation

### 14.1 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Call fails (no answer/disconnect) | Low | Log error, mark unverifiable, user can retry |
| API rate limit exceeded | Medium | Implement backoff, queue pacing, plan upgrade |
| Database grows large | Medium | Implement retention policy, archive old logs |
| Concurrent job limit hit | Low | Queue jobs, they process sequentially |
| Malformed phone number | Low | Validate E.164 format before calling |

### 14.2 Compliance Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| TCPA violation | High | Follow compliance checklist, legal review |
| Incorrect determination | Medium | pending_review status, manual verification |
| Data privacy breach | High | Use Zero Retention, data encryption, audit logs |
| Call cost overruns | Medium | Set budget alerts, monitor usage daily |

### 14.3 Operational Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Wrong phone number called | High | Validate before calling, audit logging |
| Agent angry/hostile | Low | Neutral script, professional handling |
| System crashes | Medium | Background job persistence (Redis upgrade) |
| Bad agent determinations | Medium | Confidence score + manual review |

---

## Implementation Roadmap

### Phase 1: Preparation (1-2 hours)
```
□ Research complete ✓ (done)
□ Architecture designed ✓ (done)
□ Specification written ✓ (you're reading it!)
□ API endpoints documented ✓
□ Database schema finalized ✓
→ Ready for Phase 2
```

### Phase 2: Core Implementation (6-8 hours)
```
Task 1: Configuration (15 min)
  □ Update backend/config.py with ElevenLabs settings

Task 2: Database (15 min)
  □ Update backend/app/database.py with new tables
  □ Add migration functions

Task 3: Models (15 min)
  □ Create backend/services/verification/models.py
  □ Add all Pydantic schemas

Task 4: ElevenLabs Client (30 min)
  □ Create backend/services/verification/elevenlabs_client.py
  □ Implement make_phone_call() and wait_for_completion()

Task 5: Job Queue (30 min)
  □ Create backend/services/verification/jobs.py
  □ Implement job storage, queueing, retrieval

Task 6: Verification Service (45 min)
  □ Create backend/services/verification/service.py
  □ Implement _extract_determination() and confidence scoring

Task 7: Database CRUD (30 min)
  □ Update backend/app/crud.py with verification functions
  □ create_verification_log(), update_property_verification_status()

Task 8: API Endpoints (45 min)
  □ Update backend/app/main.py with new endpoints
  □ POST /api/verify/property/{id}
  □ GET /api/verify/job/{id}
  □ Add error handling

Task 9: Integration (15 min)
  □ Tie everything together in main.py lifespan
  □ Start background job processor
```

### Phase 3: Testing & Documentation (4-6 hours)
```
Task 10: Unit Tests (45 min)
  □ Create backend/tests/test_verification_service.py
  □ Test keyword matching, confidence scoring, parsing

Task 11: Integration Tests (45 min)
  □ Create backend/tests/test_verification_integration.py
  □ Test full workflow with mock API

Task 12: API Documentation (15 min)
  □ Update SCRAPER_API.md or create VERIFICATION_API.md
  □ Document endpoints, errors, examples

Task 13: Implementation Guide (15 min)
  □ Create ELEVENLABS_INTEGRATION.md
  □ Setup instructions, troubleshooting, configuration

Task 14: Testing & Verification (30 min)
  □ Run full test suite
  □ Verify 0 warnings
  □ Manual testing checklist

Task 15: Final Commit (10 min)
  □ Review all changes
  □ Create git commit with message
  □ Verify build passes
```

### Timeline Summary

- **Phase 1:** Complete ✓
- **Phase 2:** 6-8 hours → Ready by EOD
- **Phase 3:** 4-6 hours → Ready next day
- **Total:** 10-14 hours implementation time

---

## Questions for Your Review

Before we proceed with implementation, please confirm:

1. **ElevenLabs Setup**: Are you ready to provide:
   - ElevenLabs API key?
   - Agent ID (or should we create one)?
   - Twilio phone number?

2. **Configuration Precedence**: Any special security requirements for:
   - .env file location?
   - Secrets vault integration (AWS, HashiCorp)?
   - Logging requirements?

3. **Timeline**: Given 10-14 hours of work:
   - Should we implement all 3 phases immediately?
   - Or phase it (database → service → tests)?

4. **Testing**: For manual testing:
   - Do you have test properties with agent phone numbers?
   - Any specific edge cases to test?

5. **Deployment**: After implementation:
   - Immediate production deployment?
   - Or staging/testing first?

---

## Summary

**This plan delivers:**

✅ Complete property availability verification system  
✅ Asynchronous background job processing  
✅ Full audit trail for compliance  
✅ Comprehensive error handling  
✅ Production-ready code quality  
✅ Complete test coverage  
✅ Full documentation  

**Next step:** Review this document and confirm answers to the 5 questions above. Then proceed with Phase 2 implementation.

---

**Document Version:** 1.0  
**Last Updated:** February 1, 2025  
**Status:** Ready for Review  
**Ready to implement?** Confirm above and we can begin! 🚀

