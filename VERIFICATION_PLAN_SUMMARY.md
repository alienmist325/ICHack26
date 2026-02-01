# Property Availability Verification - Plan Summary

📋 **Status:** Ready for Review  
📅 **Date:** February 1, 2025  
⏱️ **Estimated Implementation Time:** 10-14 hours  

---

## Quick Overview

We're building an AI-powered property verification system that:
- Makes automated phone calls to property agents using ElevenLabs
- Determines if rental properties are still available
- Stores complete audit trail for compliance
- Provides async job-based API for non-blocking operations

---

## Your Confirmed Preferences

✅ **Single property** verification (not batch)  
✅ **Python asyncio** job queue (not Celery)  
✅ **Neutral caller** identity (no company name)  
✅ **pending_review status** for unclear responses (allows manual verification)  

---

## What Gets Built

### New Files (4 new modules)
```
backend/services/verification/
├── models.py                 # Pydantic schemas
├── elevenlabs_client.py      # 11Labs API wrapper
├── jobs.py                   # Background job queue
└── service.py                # Core verification logic
```

### Updated Files (5 existing modules)
```
backend/
├── app/main.py               # Add 2 new API endpoints
├── app/crud.py               # Add verification DB operations
├── app/schemas.py            # Add verification schemas
├── app/database.py           # Add verification tables
└── config.py                 # Add ElevenLabs settings
```

### New API Endpoints (2)
```
POST   /api/verify/property/{property_id}
GET    /api/verify/job/{job_id}
```

### Database Changes
```
✅ 3 new columns on properties table
✅ 1 new verification_logs table
✅ 3 new performance indexes
```

---

## Architecture Diagram

```
FastAPI Endpoint
      ↓
[POST /api/verify/property/123]
      ↓
✅ Validate property exists
✅ Generate job_id
✅ Queue job
      ↓
Return 202 (job queued)
User gets: job_id
      ↓
Background Worker (asyncio loop)
      ↓
├─ Get job from queue
├─ Fetch property details
├─ Call ElevenLabs API
├─ ElevenLabs dials agent
├─ AI talks & makes decision
├─ Get transcript
├─ Parse with keyword matching
├─ Store in verification_logs
├─ Update properties table
└─ Mark job completed
      ↓
User polls: GET /api/verify/job/{job_id}
Returns: status + results (when done)
```

---

## Data Model

### Verification Statuses
- `pending` - Not yet verified
- `available` - Confirmed available
- `sold` - No longer available
- `unverifiable` - Could not determine
- `pending_review` - Unclear, needs human review

### Job Statuses
- `queued` - Waiting to process
- `processing` - Call in progress
- `completed` - Done successfully
- `failed` - Error occurred

---

## Cost Analysis

| Usage | Plan | Cost | Calls |
|-------|------|------|-------|
| 100/month | Creator | $11 | ~360 |
| 1000/month | Pro | $99 | ~1,800 |
| 5000/month | Scale | $330 | ~9,000 |

**Per Call:** ~$0.25 (ElevenLabs TTS + Twilio)

---

## Testing Plan

### Unit Tests (45 min)
- Keyword matching logic
- Confidence scoring
- Configuration loading
- Mock API responses

### Integration Tests (45 min)
- Full verification workflow
- Database storage
- Job queueing
- Error scenarios

### Manual Testing (30 min)
- End-to-end with real ElevenLabs
- Check database entries
- Verify status transitions

---

## Implementation Phases

### Phase 1: Preparation ✅ (COMPLETE)
- ✅ Research & analysis
- ✅ Architecture designed
- ✅ Spec written
- ✅ Decisions captured

### Phase 2: Implementation (6-8 hours)
Tasks 1-9: Core system build
- Config, Database, Models
- ElevenLabs client, Job queue
- Service logic, CRUD, Endpoints

### Phase 3: Testing (4-6 hours)
Tasks 10-15: Tests & documentation
- Unit tests, Integration tests
- API docs, Implementation guide
- Final verification & commit

**Total:** 10-14 hours → Ready in ~2 days

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| **Asyncio queue** | Built-in, simple, upgradeable to Redis |
| **SQLite** | Existing, sufficient, consistent |
| **Twilio** | Most reliable, ElevenLabs recommended |
| **Keyword matching** | Simple, effective, extensible to LLM |
| **pending_review** | Allows human verification of edge cases |
| **Neutral caller** | Higher success rate with agents |

---

## Risk Mitigation

### Technical Risks
- **API rate limits** → Backoff + queue pacing + plan upgrade
- **DB grows large** → Retention policy, archive old logs
- **Wrong number** → E.164 validation, audit logging
- **Call fails** → Log error, mark unverifiable, retry available

### Compliance Risks
- **TCPA violation** → Follow checklist, legal review (especially US)
- **Data breach** → Use Zero Retention, encryption, audit logs
- **Bad determinations** → Confidence scores + manual review

### Operational Risks
- **System crashes** → Upgrade to Redis for persistence
- **High costs** → Budget alerts, daily monitoring
- **Angry agents** → Professional script, neutral approach

---

## Pre-Implementation Checklist

Before we start, you'll need:

### 🔑 Credentials
- [ ] ElevenLabs API key (from https://elevenlabs.io/app/settings/api-keys)
- [ ] ElevenLabs Agent ID (create one or reuse existing)
- [ ] Twilio phone number (or pre-configured 11Labs number)

### 💻 Verification
- [ ] .env file setup ready
- [ ] Test properties with agent phone numbers
- [ ] Database backup ready

### 📋 Team Communication
- [ ] Support team briefed on new endpoints
- [ ] Compliance team reviewed TCPA requirements (if US)
- [ ] Product manager aware of pending_review workflow

---

## After Implementation

You'll have:

✅ **Production-ready verification system**  
✅ **Complete audit trail** (verification_logs table)  
✅ **100% test coverage**  
✅ **Zero new warnings**  
✅ **Full documentation**  

### Available Immediately
- Verify individual properties via API
- Track all calls with transcriptions
- Review unclear cases manually
- Monitor call success rates

### Future Enhancements (after launch)
1. Batch calling (100+ properties at once)
2. Redis queue (distributed processing)
3. Webhook callbacks (push notifications)
4. Call recording (compliance/review)
5. LLM-based parsing (GPT-4 extraction)

---

## Questions Before We Start?

1. **Have you got ElevenLabs setup?**
   - API key ready?
   - Agent created?
   - Twilio number available?

2. **Timeline preference?**
   - All 3 phases immediately?
   - Or stagger (database → service → tests)?

3. **Production readiness?**
   - Immediate deployment?
   - Staging/testing first?

4. **Support team briefing?**
   - Should I document the API for them?
   - Need runbook for troubleshooting?

---

## Full Documentation

📄 **Detailed spec:** `VERIFICATION_IMPLEMENTATION_PLAN.md` (60 KB, 15 sections)

Includes:
- Complete API endpoint specs
- Full Pydantic models with examples
- Database schema migrations
- Job queue architecture
- ElevenLabs client implementation
- Service logic with agent prompts
- Testing strategy
- Deployment checklist
- Cost analysis
- Compliance & legal
- Risk assessment
- Implementation roadmap

---

## Next Steps

1. **Review the detailed plan** (VERIFICATION_IMPLEMENTATION_PLAN.md)
2. **Answer the 4 questions above**
3. **Confirm you're ready to proceed**
4. **I'll start Phase 2 implementation**

---

**Ready to build? Let me know! 🚀**

