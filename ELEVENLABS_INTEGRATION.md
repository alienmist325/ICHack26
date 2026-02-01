# ElevenLabs Property Verification Integration

## Overview

This document describes the ElevenLabs AI-powered property availability verification system integrated into the Property Rental Finder API.

## Features

- **Automated Phone Verification**: Automatically calls property agents using ElevenLabs AI
- **Natural Conversations**: AI conducts professional, natural conversations to verify availability
- **Intelligent Analysis**: Analyzes agent responses to determine property status (available/sold/unclear)
- **Asynchronous Processing**: Fire-and-forget API with job polling for status
- **Complete Audit Trail**: All verification calls logged with transcripts and confidence scores
- **Flexible Status Handling**: Marks unclear responses for manual review rather than auto-deciding

## Architecture

### System Components

1. **API Endpoints**: HTTP REST endpoints for starting verification and polling status
2. **Job Queue**: AsyncIO-based background job queue for managing verification tasks
3. **ElevenLabs Client**: HTTP wrapper for ElevenLabs Agents API
4. **Verification Service**: Core logic for analyzing agent responses
5. **Database**: SQLite tables for storing verification results and audit trails

### API Flow

```
Client                Backend                    ElevenLabs
  |                     |                            |
  +--POST /verify------>|                            |
  |                     +-- Enqueue Job             |
  |                     +-- Return 202 + job_id     |
  |<----202 Accepted-----                            |
  |                     |
  | [Background Processing]                         |
  |                     |--Make Call + Agent ID----->|
  |                     |                          (Call in progress)
  |                     |<---Call Results + Transcript--|
  |                     +-- Analyze Response
  |                     +-- Store in DB
  |                     |
  +--GET /job/{id}----->|
  |                     +-- Lookup in memory
  |<----200 OK + Result (if complete)
```

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# Required for verification service
ELEVENLABS_API_KEY=sk_your_api_key_here
ELEVENLABS_AGENT_ID=your_agent_id_here
ELEVENLABS_PHONE_NUMBER=+1234567890

# Optional tuning parameters (defaults shown)
VERIFICATION_CALL_TIMEOUT=600           # Max call duration in seconds
VERIFICATION_MAX_CONCURRENT_CALLS=5     # Max concurrent verification calls
```

### Setup Checklist

- [ ] Create ElevenLabs account at https://elevenlabs.io
- [ ] Get API key from Settings → API Keys
- [ ] Create Verification Agent in ElevenLabs dashboard
  - Use system prompt from planning documents
  - Select professional voice
- [ ] Get Twilio phone number (or use ElevenLabs pre-configured)
- [ ] Add credentials to `.env` file
- [ ] Run `python app/database.py` to initialize DB with new verification tables

## API Reference

### Start Verification

```http
POST /api/verify/property/{property_id}
```

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "property_id": 123,
  "status": "queued",
  "message": "Verification job queued successfully",
  "poll_url": "/api/verify/job/550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**
- `404 Not Found`: Property doesn't exist or has no agent phone
- `503 Service Unavailable`: Verification service not configured

### Get Job Status

```http
GET /api/verify/job/{job_id}
```

**Response (200 OK):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-02-01T12:00:00Z",
  "started_at": "2025-02-01T12:00:05Z",
  "completed_at": "2025-02-01T12:02:30Z",
  "result": {
    "property_id": 123,
    "verification_status": "available",
    "confidence_score": 0.95,
    "call_transcript": "Yes, the property is available...",
    "call_duration_seconds": 145,
    "agent_response": "Yes, the property is available for rent.",
    "notes": "Analyzed 256 character transcript",
    "created_at": "2025-02-01T12:02:30Z"
  }
}
```

**Job Status Values:**
- `queued`: Job waiting to be processed
- `processing`: Currently making the call
- `completed`: Call finished successfully
- `failed`: Call failed or unexpected error

### Get Verification Statistics

```http
GET /api/verify/stats
```

**Response:**
```json
{
  "by_status": {
    "pending": 156,
    "available": 45,
    "sold": 12,
    "unclear": 8,
    "failed": 3
  },
  "total_verifications": 68
}
```

## Database Schema

### Verification Columns on Properties Table

```sql
verification_status TEXT DEFAULT 'pending' 
  -- Status: pending, processing, available, sold, rented, unclear, pending_review, failed

last_verified_at TEXT 
  -- Timestamp of last verification

verification_notes TEXT 
  -- Additional notes from verification process
```

### Verification Logs Table

```sql
CREATE TABLE verification_logs (
  id INTEGER PRIMARY KEY,
  property_id INTEGER UNIQUE,
  call_timestamp TEXT,
  call_duration_seconds INTEGER,
  agent_phone TEXT,
  agent_response TEXT,
  verification_status TEXT,
  confidence_score REAL,
  notes TEXT,
  error_message TEXT,
  created_at TEXT,
  
  FOREIGN KEY (property_id) REFERENCES properties(id)
);
```

## Verification Logic

### Transcript Analysis

The verification service analyzes agent responses using keyword matching:

**Available Keywords** (checked first):
- "available" (with word boundaries)
- "currently available"
- "still available"
- "is available"

**Sold/Rented Keywords** (checked second):
- "sold" (with word boundaries)
- "rented", "rented out"
- "let"
- "no longer available"
- "not available"
- "already rented", "already let"

**Result Categories:**
- `AVAILABLE`: Agent confirms property is available (confidence: 70-95%)
- `SOLD`: Agent states property is sold/rented/no longer available (confidence: 70-95%)
- `UNCLEAR`: Agent response is ambiguous (confidence: 30-60%)
- `PENDING_REVIEW`: Short/unclear response (confidence: < 50%)
- `FAILED`: Call failed to connect or agent didn't answer

### Confidence Score

Confidence is calculated based on:
1. **Keyword Match**: Initial 70% if definitive keyword found
2. **Transcript Length**: +0.3% per 1000 characters
3. **Maximum**: Capped at 95% for human review

## System Prompts

### Agent Instructions

The ElevenLabs Agent is configured with professional instructions:

1. Greet agent/landlord professionally
2. Explain: "I'm calling to verify availability of [property address]"
3. Ask clearly: "Is this property currently available for rent?"
4. Listen carefully to response
5. Ask ONE follow-up if unclear
6. End within 2-3 minutes
7. Be neutral (don't identify with company)
8. Handle voicemail gracefully

### Example Call Flow

```
AI: "Hello, I'm calling to verify property availability..."
Agent: "Yes, how can I help?"
AI: "Is the property at 123 Main St currently available for rent?"
Agent: "Yes, it's available. Would you like to schedule a viewing?"
AI: "This property is AVAILABLE for rent. Thank you for your time."
```

## Error Handling

### Common Error Scenarios

| Scenario | Status | Action |
|----------|--------|--------|
| Call fails to connect | FAILED | No transcript; mark for manual review |
| Agent doesn't answer | FAILED | Voicemail attempt; mark for retry |
| Agent says "I'll check" | UNCLEAR | Insufficient info; mark pending_review |
| Agent clearly confirms available | AVAILABLE | Confidence 90%+ |
| Agent says property sold | SOLD | Confidence 90%+ |

### Retry Logic

- Failed jobs are NOT automatically retried
- All status changes are logged for audit trail
- Manual review required for unclear cases

## Performance Considerations

### Concurrency

- Default: 5 concurrent verification calls
- Configurable via `VERIFICATION_MAX_CONCURRENT_CALLS`
- Queue automatically throttles incoming requests

### Call Timeout

- Default: 600 seconds (10 minutes)
- Configurable via `VERIFICATION_CALL_TIMEOUT`
- Handles long conversation scenarios

### Database

- Single property_id unique constraint on verification_logs
- Only latest result per property stored in log
- Indexes on property_id, status, created_at for fast queries

## Compliance & Legal

### TCPA Compliance (US)

The system is designed for compliance but requires careful implementation:

- **Disclosure**: AI must disclose automated call nature
- **Consent**: Get prior written consent before calling
- **Do Not Call**: Respect National Do Not Call Registry
- **Time Restrictions**: Call between 8 AM - 9 PM recipient's timezone

### GDPR Compliance (EU)

- **Consent**: GDPR consent required before calling
- **Right to be Forgotten**: Support deletion requests
- **Data Retention**: Consider retention policies (recommend: 90 days)
- **Data Processor**: ElevenLabs is data processor

### Recommended Safeguards

1. Obtain explicit consent from agents/landlords
2. Maintain audit trail of all calls (verification_logs table)
3. Implement data retention policy
4. Document compliance procedures
5. Train on responsible use

## Testing

### Unit Tests (15 tests passing)

```bash
python -m pytest backend/tests/test_verification_service.py -v
```

Tests coverage:
- Service initialization and configuration
- Transcript analysis (available, sold, unclear scenarios)
- Response summarization
- Job lifecycle management
- Error handling

### Integration Tests

```bash
python -m pytest backend/tests/test_verification_integration.py -v
```

Tests coverage:
- API endpoint validation
- Database CRUD operations
- Job queue functionality
- Full workflow simulation

### Manual Testing

1. **Startup Check**:
   ```bash
   curl http://localhost:8000/health
   # Should return {"status": "healthy"}
   ```

2. **Start Verification**:
   ```bash
   curl -X POST http://localhost:8000/api/verify/property/1
   # Returns: {"job_id": "...", "status": "queued", ...}
   ```

3. **Check Status**:
   ```bash
   curl http://localhost:8000/api/verify/job/{job_id}
   # Returns: Current job status and result if complete
   ```

## Troubleshooting

### Service Won't Start

**Problem**: "ElevenLabs API key not configured"
- **Solution**: Add `ELEVENLABS_API_KEY` to `.env` file

**Problem**: "Verification service disabled"
- **Solution**: Ensure all 3 required env vars are set (API key, Agent ID, Phone number)

### Jobs Stuck in Queue

**Problem**: Jobs remain "queued" indefinitely
- **Solution**: Check background worker is running (`await job_queue.start()`)

### Wrong Verification Results

**Problem**: Property marked as "sold" when it should be "available"
- **Solution**: Check transcript keywords; may need to adjust regex patterns

### Call Not Connecting

**Problem**: All calls get FAILED status
- **Solution**: Verify phone number format (+1234567890); check ElevenLabs Agent configuration

## Future Enhancements

- [ ] Batch verification endpoint for multiple properties
- [ ] Automatic retry for failed calls
- [ ] Custom response templates per agent type
- [ ] Sentiment analysis in addition to keyword matching
- [ ] Phone number validation and carrier lookup
- [ ] Integration with CallKit or other phone systems
- [ ] Redis backend for distributed job queue
- [ ] Webhook callbacks instead of polling
- [ ] Fine-tuned LLM for response analysis
- [ ] Multi-language support

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review test cases in `backend/tests/test_verification_*.py`
3. Consult ElevenLabs API documentation: https://elevenlabs.io/docs
4. Open an issue with full context and logs

## References

- **ElevenLabs Docs**: https://elevenlabs.io/docs
- **Implementation Plan**: `VERIFICATION_IMPLEMENTATION_PLAN.md`
- **Quick Start**: `VERIFICATION_QUICK_START.md`
- **Test Files**: `backend/tests/test_verification_*.py`
