"""Main verification service for property availability checking via Bland AI."""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Optional

from backend.app.crud import get_property_by_id, update_property_verification
from backend.config import settings
from backend.services.verification.bland_client import get_bland_client
from backend.services.verification.models import VerificationStatus

logger = logging.getLogger(__name__)


def _analyze_transcript(
    transcript: Optional[str], listing_type: Optional[str]
) -> VerificationStatus:
    """Analyze call transcript to determine property availability.

    Uses pattern matching and keyword heuristics with proper priority:
    1. User responses (user: Yes/No)
    2. Negation/affirmation patterns (context-aware regex)
    3. Keyword matching (less ambiguous first)

    Args:
        transcript: The call transcript text
        listing_type: Type of listing ('rent', 'sale')

    Returns:
        VerificationStatus indicating availability
    """
    if not transcript:
        return VerificationStatus.UNSURE

    lower_transcript = transcript.lower()
    import re

    # ============================================================================
    # PRIORITY 1: User responses from API format ("user: Yes/No")
    # ============================================================================
    user_response_patterns = [
        r'\buser:\s*["\']?(\w+)["\']?',
        r'\b(?:caller|user|prospect|tenant|buyer)(?:\s+(?:said|responded|replied))?\s*["\']?(\w+)["\']?',
    ]

    user_statements = []
    for pattern in user_response_patterns:
        matches = re.findall(pattern, lower_transcript)
        user_statements.extend(matches)

    logger.debug(f"Extracted user statements: {user_statements}")

    for statement in user_statements:
        if statement in ["no", "nope", "nope.", "no."]:
            logger.info(f"User response: '{statement}' → UNAVAILABLE")
            return VerificationStatus.UNAVAILABLE
        elif statement in ["yes", "yes.", "yep", "yep."]:
            logger.info(f"User response: '{statement}' → AVAILABLE")
            return VerificationStatus.AVAILABLE

    # ============================================================================
    # PRIORITY 2: Context-aware pattern matching (before keyword substring match)
    # This handles negations and prevents false matches from simple keywords
    # ============================================================================

    # Uncertainty patterns - check FIRST to catch "Maybe it's available" scenarios
    # "Maybe" + any affirmation should still be UNSURE
    uncertainty_patterns = [
        r"(?:maybe|i think|i believe|might be|not sure|not certain|could be|can\'t find)",
    ]

    for pattern in uncertainty_patterns:
        if re.search(pattern, lower_transcript):
            logger.info(f"Uncertainty pattern match: {pattern} → UNSURE")
            return VerificationStatus.UNSURE

    # Negation patterns - definitive UNAVAILABLE
    negation_patterns = [
        r"(?:it\'s not|isn\'t|not)\s+(?:available|listed|on the market|for sale)",
        r"(?:no longer|not anymore|never)\s+(?:available|listed|for sale|for rent)",
        r"(?:don\'t have|don\'t have that|can\'t|couldn\'t locate)",
    ]

    for pattern in negation_patterns:
        if re.search(pattern, lower_transcript):
            logger.info(f"Negation pattern match: {pattern} → UNAVAILABLE")
            return VerificationStatus.UNAVAILABLE

    # Affirmation patterns - highest confidence for AVAILABLE
    affirmation_patterns = [
        r"(?:we still have|we\'re still|we continue to|still\s+(?:selling|marketing))",
        r"(?:haven\'t sold|not sold|never sold)",
        r"(?:still\s+(?:available|listed|on\s+market|actively\s+marketing))",
    ]

    for pattern in affirmation_patterns:
        if re.search(pattern, lower_transcript):
            logger.info(f"Affirmation pattern match: {pattern} → AVAILABLE")
            return VerificationStatus.AVAILABLE

    # ============================================================================
    # PRIORITY 3: Keyword matching (only after patterns checked)
    # ============================================================================

    # Keywords for UNAVAILABLE (but exclude false positives like "let me check")
    unavailable_keywords = [
        "sold",
        "rented",
        "taken",
        "off market",
        "withdrawn",
        "delisted",
        "no longer listed",
        "already sold",
        "already rented",
        "been let",
        "been rented",
        "been sold",
    ]

    for keyword in unavailable_keywords:
        if keyword in lower_transcript:
            logger.info(f"Unavailable keyword: '{keyword}' → UNAVAILABLE")
            return VerificationStatus.UNAVAILABLE

    # Keywords for AVAILABLE
    available_keywords = [
        "yes",
        "available",
        "still available",
        "still listed",
        "still on market",
        "on the market",
        "for sale",
        "for rent",
        "can show",
        "can view",
        "can arrange a viewing",
        "viewing available",
        "listed",
        "listing",
        "listing is active",
        "actively marketing",
        "great opportunity",
        "current listing",
    ]

    for keyword in available_keywords:
        if keyword in lower_transcript:
            logger.info(f"Available keyword: '{keyword}' → AVAILABLE")
            return VerificationStatus.AVAILABLE

    # Keywords for UNSURE (must check after confirmed unavailable/available)
    unsure_keywords = [
        "not sure",
        "i think so",
        "maybe",
        "i believe so",
        "might be",
        "need to check",
        "let me check",
        "not entirely sure",
        "i'm not certain",
        "can't find",
    ]

    for keyword in unsure_keywords:
        if keyword in lower_transcript:
            logger.info(f"Unsure keyword: '{keyword}' → UNSURE")
            return VerificationStatus.UNSURE

    # ============================================================================
    # FALLBACK: No clear indicators
    # ============================================================================
    logger.info("No clear patterns matched in transcript → UNSURE")
    return VerificationStatus.UNSURE


async def _verify_property_async(property_id: int) -> None:
    """Background async task to verify a property's availability.

    This function:
    1. Fetches property details from database
    2. Calls Bland AI to speak with agent
    3. Analyzes transcript for availability
    4. Updates database with verification status

    Args:
        property_id: The property to verify
    """
    logger.info(f"Starting async verification for property {property_id}")

    # Fetch property
    property_obj = get_property_by_id(property_id)
    if property_obj is None:
        logger.error(f"Property {property_id} not found")
        return

    # Check for required fields
    agent_phone = property_obj.agent_phone
    if not agent_phone:
        logger.error(f"Property {property_id} has no agent phone number")
        update_property_verification(
            property_id,
            VerificationStatus.UNSURE.value,
            datetime.now(timezone.utc).isoformat(),
            "No agent phone number available",
        )
        return

    # Build task prompt based on listing type
    # Use more natural, conversational prompts that agents will engage with
    listing_type = property_obj.listing_type or "sale"
    full_address = property_obj.full_address or "the property"

    if listing_type.lower() == "rent":
        task = f"""Hi, I'm calling on behalf of a prospective tenant. I wanted to check on the status of {full_address}. 
Is this property still available for rent, or has it been let already? What's the current status?"""
    else:
        task = f"""Hi, I'm calling on behalf of a prospective buyer. I wanted to inquire about {full_address}. 
Is this property still on the market for sale, or has it been sold? Can you give me an update on its status?"""

    logger.info(f"Making Bland AI call to {agent_phone} for property {property_id}")

    # ============================================================================
    # PHONE SELECTION LOGIC (Context-aware)
    # ============================================================================
    # Priority:
    # 1. If running under pytest: ALWAYS use mock phone (safety first)
    # 2. If MOCK_MODE enabled: use mock phone (dev/staging mode)
    # 3. Otherwise: use real agent phone from DB (production)
    # ============================================================================

    is_pytest = "pytest" in sys.modules
    is_mock_mode = settings.bland_ai_mock_mode

    if is_pytest:
        # DURING PYTEST: Always use mock phone for absolute safety
        phone_to_call = settings.bland_ai_mock_phone_number
        logger.warning(f"[BLAND_AI] 🧪 PYTEST MODE: Using mock phone {phone_to_call}")
    elif is_mock_mode:
        # MOCK MODE (production): Use mock phone instead of real agent numbers
        phone_to_call = settings.bland_ai_mock_phone_number
        logger.warning(f"[BLAND_AI] 🟡 MOCK MODE: Using mock phone {phone_to_call}")
    else:
        # PRODUCTION MODE: Use real agent phone from DB
        phone_to_call = agent_phone
        logger.warning(
            f"[BLAND_AI] 🔴 PRODUCTION MODE: Using agent phone {phone_to_call}"
        )

    # Final safety validation
    if is_pytest and phone_to_call != settings.bland_ai_mock_phone_number:
        logger.error(
            f"[BLAND_AI] ❌ SAFETY VIOLATION: Pytest detected but "
            f"not using mock phone! Expected {settings.bland_ai_mock_phone_number}, "
            f"got {phone_to_call}"
        )
        update_property_verification(
            property_id,
            VerificationStatus.UNSURE.value,
            datetime.now(timezone.utc).isoformat(),
            "Safety check failed - pytest mode but not using mock phone",
        )
        return

    if not phone_to_call:
        logger.error(
            f"[BLAND_AI] ❌ NO PHONE NUMBER: Cannot make call without valid phone number"
        )
        update_property_verification(
            property_id,
            VerificationStatus.UNSURE.value,
            datetime.now(timezone.utc).isoformat(),
            "No phone number available",
        )
        return

    # Initiate Bland AI call
    client = get_bland_client()
    call_id = client.make_call(phone_to_call, task)

    if not call_id:
        logger.error(f"Failed to initiate Bland AI call for property {property_id}")
        update_property_verification(
            property_id,
            VerificationStatus.UNSURE.value,
            datetime.now(timezone.utc).isoformat(),
            "Failed to initiate call",
        )
        return

    # Wait for call completion with async polling
    logger.info(f"Waiting for Bland AI call {call_id} to complete")
    result = await _wait_for_call_completion_async(call_id)

    if result is None:
        logger.error(f"Bland AI call {call_id} failed or timed out")
        update_property_verification(
            property_id,
            VerificationStatus.UNSURE.value,
            datetime.now(timezone.utc).isoformat(),
            "Call failed or timed out",
        )
        return

    # Analyze transcript
    transcript = result.transcript or ""
    verification_status = _analyze_transcript(transcript, listing_type)

    logger.info(
        f"Property {property_id} verification status: {verification_status.value}"
    )

    # Update database
    update_property_verification(
        property_id,
        verification_status.value,
        datetime.now(timezone.utc).isoformat(),
        transcript[:500],  # Store first 500 chars of transcript as notes
    )

    logger.info(f"Completed async verification for property {property_id}")


async def _wait_for_call_completion_async(
    call_id: str, max_wait_seconds: int = 120, poll_interval: float = 2.0
):
    """Async helper to wait for call completion with polling."""
    client = get_bland_client()

    # If client has async method (MockBlandAIClient), use it
    if hasattr(client, "wait_for_call_completion_async"):
        return await client.wait_for_call_completion_async(
            call_id,
            max_wait_seconds=max_wait_seconds,
            poll_interval_seconds=poll_interval,
        )

    # Fallback: polling implementation for clients without async method
    import time

    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        result = client.get_call_result(call_id)

        if result and result.status in ["completed", "failed", "error"]:
            return result

        await asyncio.sleep(poll_interval)

    return None


def verify_property(property_id: int) -> dict:
    """Public API to trigger property verification.

    This function returns immediately (non-blocking) and starts an async background task
    to verify the property's availability. The verification will complete in the background.

    Args:
        property_id: The property to verify

    Returns:
        dict with status and property_id

    Example:
        >>> result = verify_property(123)
        >>> print(result)
        {'property_id': 123, 'status': 'processing'}
    """
    # Validate property exists
    property_obj = get_property_by_id(property_id)
    if property_obj is None:
        return {"error": f"Property {property_id} not found", "status": "error"}

    # Start background async task (non-blocking)
    asyncio.create_task(_verify_property_async(property_id))

    # Return immediately
    return {"property_id": property_id, "status": "processing"}
