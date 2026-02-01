# Verification Feature - Quick Start Guide

## 📄 Documentation Files

Three documents have been created for your review:

### 1. **VERIFICATION_PLAN_SUMMARY.md** ← START HERE
- Quick overview (7.2 KB, 5 min read)
- All key decisions summarized
- Pre-implementation checklist
- Timeline and phases
- 4 questions before starting

### 2. **VERIFICATION_IMPLEMENTATION_PLAN.md** ← DETAILED SPEC
- Complete technical specification (60 KB)
- 15 comprehensive sections
- Full code samples for all modules
- Database schemas
- API endpoint specs
- Pydantic models
- Job queue architecture
- Testing strategy
- Compliance & legal

### 3. **VERIFICATION_QUICK_START.md** ← THIS FILE
- Cliff notes version
- Key diagrams
- Command reference
- Before/after checklist

---

## 🎯 What You're Getting

A complete, production-ready property verification system that:

```
Property Agent Call Flow:
┌─────────────────────────────────────────────────┐
│ User: POST /api/verify/property/123             │
└─────────────────────────────────────────────────┘
                      ↓
         [Validate property & queue]
                      ↓
┌─────────────────────────────────────────────────┐
│ Response: 202 Accepted + job_id                │
│ {job_id: "verify_prop_123_abc123"}             │
└─────────────────────────────────────────────────┘
                      ↓
         [Background Worker]
         ElevenLabs makes call
         AI determines availability
         Stores results
                      ↓
┌─────────────────────────────────────────────────┐
│ User: GET /api/verify/job/{job_id}             │
│ Response: 200 + Results                        │
│ {status: "completed",                          │
│  result: {verification_status: "available"}}  │
└─────────────────────────────────────────────────┘
```

---

## 📊 By The Numbers

**Implementation Effort:** 10-14 hours
- Phase 2 (Implementation): 6-8 hours
- Phase 3 (Testing): 4-6 hours

**Cost Per Call:** ~$0.25
- ElevenLabs TTS: $0.15-0.30
- Twilio: $0.015
- Profit: Verify 400 properties for $11

**New Code:** ~400 lines
- 4 new modules (services/verification/)
- 5 updated modules (app, config)
- 2 new API endpoints
- Complete test coverage

---

## ✅ Your Confirmed Choices

| Decision | You Chose | Why |
|----------|-----------|-----|
| Architecture | Single property | Control, simple, scalable |
| Job Queue | Python asyncio | Built-in, no deps |
| Caller ID | Neutral/Anonymous | Higher success |
| Unclear Cases | pending_review | Manual review enabled |

---

## 🗂️ File Structure (After Implementation)

```
backend/
├── services/                          [NEW]
│   └── verification/                  [NEW]
│       ├── __init__.py               [NEW]
│       ├── models.py                 [NEW] Pydantic schemas
│       ├── elevenlabs_client.py      [NEW] 11Labs API wrapper
│       ├── jobs.py                   [NEW] Background queue
│       └── service.py                [NEW] Core logic
│
├── app/
│   ├── main.py                       [UPDATED] +2 endpoints
│   ├── crud.py                       [UPDATED] +verify functions
│   ├── schemas.py                    [UPDATED] +verify schemas
│   └── database.py                   [UPDATED] +verify tables
│
├── config.py                         [UPDATED] +11Labs settings
│
└── tests/
    ├── test_verification_service.py  [NEW] Unit tests
    └── test_verification_integration [NEW] Integration tests
```

---

## 🚀 Implementation Roadmap

### Phase 1: Preparation ✅ COMPLETE
```
✅ Research 11Labs capabilities
✅ Architecture designed  
✅ Decisions captured
✅ Specification written
✅ Documentation complete
→ YOU'RE HERE: Ready for Phase 2
```

### Phase 2: Implementation (6-8 hours)
```
Task 1:  Config - ELEVENLABS settings          (15 min)
Task 2:  Database - New tables & columns        (15 min)
Task 3:  Models - Pydantic schemas              (15 min)
Task 4:  ElevenLabs Client - API wrapper        (30 min)
Task 5:  Job Queue - Background processing     (30 min)
Task 6:  Service - Core verification logic      (45 min)
Task 7:  CRUD - Database operations            (30 min)
Task 8:  API Endpoints - 2 new routes          (45 min)
Task 9:  Integration - Tie everything          (15 min)
         ├─ Day 1, morning: Tasks 1-5
         ├─ Day 1, afternoon: Tasks 6-7
         └─ Day 2, morning: Tasks 8-9
```

### Phase 3: Testing & Documentation (4-6 hours)
```
Task 10: Unit Tests - Keyword matching         (45 min)
Task 11: Integration Tests - Full workflow     (45 min)
Task 12: API Documentation                     (15 min)
Task 13: Implementation Guide                  (15 min)
Task 14: Testing & Verification                (30 min)
Task 15: Final Commit                          (10 min)
         ├─ Day 2, afternoon: Tasks 10-13
         └─ Day 3, morning: Tasks 14-15
```

**Timeline: 3 business days total (with breaks)**

---

## 🔧 Before We Start

### You Need:

**ElevenLabs Account**
```bash
# Get from https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_API_KEY=sk_your_key_here

# Create agent or get existing ID
ELEVENLABS_AGENT_ID=your_agent_id_here
```

**Twilio Account** (or pre-configured with ElevenLabs)
```bash
# E.164 format: +1234567890
ELEVENLABS_PHONE_NUMBER=+1234567890
```

**Test Data**
```bash
# Properties with agent phone numbers
SELECT id, full_address, agent_phone 
FROM properties 
WHERE agent_phone IS NOT NULL 
LIMIT 5;
```

**Database Backup**
```bash
# Before running migrations
cp backend/data/rightmove.db backend/data/rightmove.db.backup
```

### Checklist

- [ ] ElevenLabs API key obtained
- [ ] ElevenLabs agent created/configured
- [ ] Twilio phone number available
- [ ] Test properties identified (5+)
- [ ] Database backed up
- [ ] .env file ready for updates
- [ ] Understood TCPA requirements (US)

---

## 📈 What Gets Added to Database

### Properties Table (3 new columns)

```sql
ALTER TABLE properties ADD COLUMN verification_status TEXT DEFAULT 'pending';
-- Values: pending, available, sold, unverifiable, pending_review

ALTER TABLE properties ADD COLUMN last_verified_at TEXT;
-- When was this property last verified (ISO timestamp)

ALTER TABLE properties ADD COLUMN verification_notes TEXT;
-- Human-readable explanation
```

### Verification Logs Table (NEW)

```sql
CREATE TABLE verification_logs (
    id INTEGER PRIMARY KEY,
    property_id INTEGER NOT NULL,
    call_timestamp TEXT,           -- When call was made
    call_duration_seconds INTEGER,  -- How long call lasted
    agent_phone TEXT,              -- Who we called
    agent_response TEXT,           -- Full transcript
    verification_status TEXT,      -- available/sold/unverifiable/pending_review
    confidence_score REAL,         -- 0.0-1.0
    notes TEXT,                    -- Reasoning
    error_message TEXT,            -- If failed
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔌 API Endpoints

### Initiate Verification

```bash
# Request
curl -X POST http://localhost:8000/api/verify/property/123

# Response (202 Accepted)
{
  "job_id": "verify_prop_123_abc123",
  "property_id": 123,
  "status": "queued",
  "message": "Verification job queued successfully"
}
```

### Poll Status

```bash
# Request
curl http://localhost:8000/api/verify/job/verify_prop_123_abc123

# Response (202 - Still processing)
{
  "job_id": "verify_prop_123_abc123",
  "property_id": 123,
  "status": "processing",
  "message": "Call in progress... (estimated 2 minutes)"
}

# Response (200 - Complete)
{
  "job_id": "verify_prop_123_abc123",
  "property_id": 123,
  "status": "completed",
  "result": {
    "verification_status": "available",
    "confidence_score": 0.95,
    "notes": "Agent confirmed available",
    "call_timestamp": "2025-02-01T10:30:00+00:00",
    "call_duration_seconds": 120
  }
}
```

---

## 🧪 Testing Your Implementation

### Quick Test Script

```bash
#!/bin/bash
# After implementation is done

# 1. Start the server
python -m uvicorn app.main:app --reload

# 2. In another terminal
PROP_ID=123

# 3. Start verification
JOB=$(curl -s -X POST \
  http://localhost:8000/api/verify/property/$PROP_ID | \
  jq -r .job_id)

echo "Job ID: $JOB"

# 4. Poll status every 5 seconds
for i in {1..12}; do
  echo "Poll $i..."
  curl -s http://localhost:8000/api/verify/job/$JOB | jq .
  sleep 5
done

# 5. Check database
sqlite3 backend/data/rightmove.db \
  "SELECT property_id, verification_status, notes FROM verification_logs;"
```

---

## ⚠️ Important Notes

### TCPA Compliance (US)

If making calls to US phone numbers, you MUST:
- ✅ Get consent before calling
- ✅ Disclose this is automated
- ✅ Respect do-not-call registry
- ✅ Keep audit logs
- ✅ Provide callback number

ElevenLabs provides compliance tools. Ensure proper setup before production.

### Data Privacy

- 🔒 Store API keys in secure vault (not in code)
- 🔒 Use Zero Retention Mode in ElevenLabs if available
- 🔒 Delete old verification logs per retention policy
- 🔒 Encrypt sensitive data in database

### Cost Control

- 📊 Monitor ElevenLabs usage daily
- 📊 Set budget alerts
- 📊 Test with small batches first
- 📊 Use Creator plan ($11) to start

---

## ❓ Common Questions

**Q: Can I stop/cancel a job after starting?**  
A: No, once queued it will execute. You can mark results as invalid manually.

**Q: What if the agent doesn't answer?**  
A: Call marked as failed/unverifiable. You can retry later.

**Q: How long do calls take?**  
A: Typically 2-3 minutes. Max timeout is 10 minutes (configurable).

**Q: Can I verify multiple properties at once?**  
A: Currently one at a time via API. Batch feature available later.

**Q: What happens to call recordings?**  
A: Transcripts stored in verification_logs. Audio can be saved to storage.

---

## 📞 Next Steps

1. **Review VERIFICATION_PLAN_SUMMARY.md** (5 min read)
2. **Review VERIFICATION_IMPLEMENTATION_PLAN.md** (detailed spec)
3. **Gather ElevenLabs credentials**
4. **Prepare test environment**
5. **Answer 4 questions in summary doc**
6. **Confirm ready to proceed**
7. **I'll start Phase 2 implementation**

---

## 📚 Full Documentation Index

| Document | Purpose | Size | Time |
|----------|---------|------|------|
| VERIFICATION_QUICK_START.md | This file, overview | 5 KB | 5 min |
| VERIFICATION_PLAN_SUMMARY.md | Executive summary | 7 KB | 10 min |
| VERIFICATION_IMPLEMENTATION_PLAN.md | Full technical spec | 60 KB | 30 min |

---

**Ready to review? Start with VERIFICATION_PLAN_SUMMARY.md** 📖

