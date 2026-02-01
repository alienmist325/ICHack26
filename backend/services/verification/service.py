"""Main verification service for property availability checking via Bland AI."""

import asyncio
import logging
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

    Uses keyword heuristics and context analysis to determine if property is:
    - AVAILABLE: Agent confirmed property is still available
    - UNAVAILABLE: Agent confirmed property is sold/rented/off market
    - UNSURE: Ambiguous or unclear response

    Args:
        transcript: The call transcript text
        listing_type: Type of listing ('rent', 'sale')

    Returns:
        VerificationStatus indicating availability
    """
    if not transcript:
        return VerificationStatus.UNSURE

    # Normalize transcript for matching
    lower_transcript = transcript.lower()

    # PRIORITY 1: Extract and analyze user responses first (highest priority)
    # This prevents matching keywords in questions
    import re

    user_response_patterns = [
        r'\buser:\s*["\']?(\w+)["\']?',  # "user: No." or user: Yes
        r'\b(?:caller|user|prospect|tenant|buyer)(?:\s+(?:said|responded|replied))?\s*["\']?(\w+)["\']?',
    ]

    user_statements = []
    for pattern in user_response_patterns:
        matches = re.findall(pattern, lower_transcript)
        user_statements.extend(matches)

    logger.debug(f"Extracted user statements: {user_statements}")

    # Check simple yes/no responses from user (HIGHEST PRIORITY)
    for statement in user_statements:
        if statement in ["no", "nope", "nope.", "no."]:
            logger.info(f"Detected user 'no' response: '{statement}' → UNAVAILABLE")
            return VerificationStatus.UNAVAILABLE
        elif statement in ["yes", "yes.", "yep", "yep."]:
            logger.info(f"Detected user 'yes' response: '{statement}' → AVAILABLE")
            return VerificationStatus.AVAILABLE

    # PRIORITY 2: Check for unavailable keywords (from agent's response)
    unavailable_keywords = [
        "sold",
        "let",
        "rented",
        "taken",
        "no longer available",
        "off market",
        "withdrawn",
        "delisted",
        "no longer listed",
        "already sold",
        "already rented",
        "no longer for rent",
        "no longer for sale",
        "no longer selling",
        "been let",
        "been rented",
    ]

    for keyword in unavailable_keywords:
        if keyword in lower_transcript:
            logger.info(f"Found unavailable keyword: '{keyword}'")
            return VerificationStatus.UNAVAILABLE

    # PRIORITY 3: Check for available keywords (from agent's response)
    available_keywords = [
        "yes",
        "available",
        "still available",
        "still listed",
        "still on market",
        "on the market",
        "can show",
        "can view",
        "can arrange a viewing",
        "viewing available",
        "listed",
        "listing is active",
        "still have",
        "still selling",
        "haven't sold",
        "actively marketing",
        "great opportunity",
    ]

    for keyword in available_keywords:
        if keyword in lower_transcript:
            logger.info(f"Found available keyword: '{keyword}'")
            return VerificationStatus.AVAILABLE

    # PRIORITY 4: Check for unsure keywords (from agent's response)
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
            logger.info(f"Found unsure keyword: '{keyword}'")
            return VerificationStatus.UNSURE

    # PRIORITY 5: Advanced pattern-based analysis for more nuanced responses

    # Look for negation patterns (context-aware)
    negation_patterns = [
        r"(?:it\'s not|isn\'t|not)\s+(?:available|listed|on the market|for sale)",
        r"(?:don\'t have|can\'t find|couldn\'t locate)\s+(?:that|this|the property)",
        r"(?:no longer|not anymore|never)\s+(?:available|listed|for sale|for rent)",
    ]

    for pattern in negation_patterns:
        if re.search(pattern, lower_transcript):
            logger.info(f"Detected negation pattern: {pattern}")
            return VerificationStatus.UNAVAILABLE

    # Look for affirmation patterns
    affirmation_patterns = [
        r"(?:we still have|we\'re still|we continue to|currently\s+(?:have|list))",
        r"(?:still\s+(?:available|listed|on\s+market))",
    ]

    for pattern in affirmation_patterns:
        if re.search(pattern, lower_transcript):
            logger.info(f"Detected affirmation pattern: {pattern}")
            return VerificationStatus.AVAILABLE

    # If no patterns matched, status is UNSURE
    logger.info("No clear patterns matched in transcript")
    return VerificationStatus.UNSURE

    # Normalize transcript for matching
    lower_transcript = transcript.lower()

    # Keywords indicating property is AVAILABLE
    available_keywords = [
        "yes",
        "available",
        "still available",
        "still listed",
        "still on market",
        "on the market",
        "can show",
        "can view",
        "can arrange a viewing",
        "viewing available",
        "listed",
        "listing is active",
        "still have",
        "still selling",
        "haven't sold",
        "actively marketing",
        "great opportunity",
    ]

    # Keywords indicating property is UNAVAILABLE
    unavailable_keywords = [
        "sold",
        "let",
        "rented",
        "taken",
        "no longer available",
        "off market",
        "withdrawn",
        "delisted",
        "no longer listed",
        "already sold",
        "already rented",
        "no longer for rent",
        "no longer for sale",
        "no longer selling",
        "been let",
        "been rented",
    ]

    # Keywords indicating UNSURE/AMBIGUOUS response
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

    # Check for unavailable keywords first (higher priority)
    for keyword in unavailable_keywords:
        if keyword in lower_transcript:
            logger.info(f"Found unavailable keyword: '{keyword}'")
            return VerificationStatus.UNAVAILABLE

    # Check for available keywords
    for keyword in available_keywords:
        if keyword in lower_transcript:
            logger.info(f"Found available keyword: '{keyword}'")
            return VerificationStatus.AVAILABLE

    # Check for unsure keywords
    for keyword in unsure_keywords:
        if keyword in lower_transcript:
            logger.info(f"Found unsure keyword: '{keyword}'")
            return VerificationStatus.UNSURE

    # Advanced pattern-based analysis for more nuanced responses
    import re

    # Extract user responses from various transcript formats
    # Format 1: "user: No." (concatenated transcript from Bland AI)
    # Format 2: Plain text with user statements
    user_response_patterns = [
        r'\buser:\s*["\']?(\w+)["\']?',  # "user: No." or user: Yes
        r'\b(?:caller|user|prospect|tenant|buyer)(?:\s+(?:said|responded|replied))?\s*["\']?(\w+)["\']?',  # Alternative formats
    ]

    user_statements = []
    for pattern in user_response_patterns:
        matches = re.findall(pattern, lower_transcript)
        user_statements.extend(matches)

    logger.debug(f"Extracted user statements: {user_statements}")

    # Check simple yes/no responses from user
    for statement in user_statements:
        if statement in ["no", "nope", "nope.", "no."]:
            logger.info(f"Detected 'no' response from user: '{statement}'")
            return VerificationStatus.UNAVAILABLE
        elif statement in ["yes", "yes.", "yep", "yep."]:
            logger.info(f"Detected 'yes' response from user: '{statement}'")
            return VerificationStatus.AVAILABLE

    # Look for negation patterns (context-aware)
    negation_patterns = [
        r"(?:it\'s not|isn\'t|not)\s+(?:available|listed|on the market|for sale)",  # Negated availability
        r"(?:don\'t have|can\'t find|couldn\'t locate)\s+(?:that|this|the property)",  # Can't locate
        r"(?:no longer|not anymore|never)\s+(?:available|listed|for sale|for rent)",  # Time-based negation
    ]

    for pattern in negation_patterns:
        if re.search(pattern, lower_transcript):
            logger.info(f"Detected negation pattern: {pattern}")
            return VerificationStatus.UNAVAILABLE

    # Look for affirmation patterns
    affirmation_patterns = [
        r"(?:we still have|we\'re still|we continue to|currently\s+(?:have|list))",  # Present tense availability
        r"(?:still\s+(?:available|listed|on\s+market))",  # Still available
    ]

    for pattern in affirmation_patterns:
        if re.search(pattern, lower_transcript):
            logger.info(f"Detected affirmation pattern: {pattern}")
            return VerificationStatus.AVAILABLE

    # If no patterns matched, status is UNSURE
    logger.info("No clear patterns matched in transcript")
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

    # ALWAYS use your test phone number for verification calls
    # This prevents accidental calls to real agent numbers
    phone_to_call = settings.bland_ai_mock_phone_number
    logger.info(f"[BLAND_AI] Using test phone number: {phone_to_call} for verification")

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
