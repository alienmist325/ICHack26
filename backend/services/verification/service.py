"""Core property verification service."""

import logging
import re
from typing import Optional, Tuple
from datetime import datetime

from .models import VerificationStatus, VerificationResult, ElevenLabsCallResponse
from .elevenlabs_client import ElevenLabsClient
from .jobs import VerificationJob

logger = logging.getLogger(__name__)


class PropertyVerificationService:
    """Service for verifying property availability via ElevenLabs AI calls."""

    # Keywords for determining availability status
    AVAILABLE_KEYWORDS = [
        r"\bavailable\b",
        r"we have.*available",
        r"currently available",
        r"yes.*available",
        r"still available",
        r"is available",
        r"property is available",
        r"yes, is available",
    ]

    SOLD_RENTED_KEYWORDS = [
        r"\bsold\b",
        r"rented out",
        r"\brented\b",
        r"\blet\b",
        r"no longer available",
        r"no.*longer.*available",
        r"not available",
        r"no availability",
        r"already rented",
        r"already let",
        r"property has been rented",
        r"property has been let",
        r"property has been sold",
        r"is no longer available",
        r"we don't have.*available",
    ]

    def __init__(self, api_key: str):
        """
        Initialize verification service.

        Args:
            api_key: ElevenLabs API key
        """
        self.client = ElevenLabsClient(api_key)

    async def verify_property(
        self,
        job: VerificationJob,
        agent_id: str,
        phone_number: str,
        property_address: str,
        agent_phone: str,
        call_timeout: int = 600,
    ) -> VerificationResult:
        """
        Execute verification for a property.

        Args:
            job: VerificationJob object
            agent_id: ElevenLabs Agent ID
            phone_number: Phone number to call from
            property_address: Property address to verify
            agent_phone: Agent's phone number to call
            call_timeout: Maximum call duration in seconds

        Returns:
            VerificationResult with determination and confidence score

        Raises:
            Exception: On API errors (should be caught by job queue)
        """
        try:
            logger.info(
                f"Starting verification for property {job.property_id} at {agent_phone}"
            )

            # Prepare system prompt with property details
            system_prompt = self._format_system_prompt(
                property_address, job.property_id, agent_phone
            )

            # Initiate call
            call_response = await self.client.initiate_call(
                agent_id=agent_id,
                phone_number=agent_phone,
                system_prompt=system_prompt,
                first_message="Hello, I'm calling to verify property availability. Is the property still available for rent?",
            )

            call_id = call_response.get("call_id")
            if not call_id:
                raise ValueError("No call_id in API response")

            logger.info(f"Call initiated: {call_id}")

            # Wait for call completion
            final_status = await self.client.wait_for_call_completion(
                agent_id=agent_id,
                call_id=call_id,
                max_wait_seconds=call_timeout,
            )

            # Parse response and determine status
            result = self._parse_call_response(
                final_status, job.property_id, agent_phone
            )

            logger.info(
                f"Property {job.property_id} verification result: "
                f"{result.verification_status.value} "
                f"(confidence: {result.confidence_score:.2f})"
            )

            return result

        except Exception as e:
            logger.error(f"Verification failed for property {job.property_id}: {e}")
            raise

    def _format_system_prompt(
        self, property_address: str, property_id: int, agent_phone: str
    ) -> str:
        """
        Format system prompt with property details.

        Args:
            property_address: Property address
            property_id: Property ID
            agent_phone: Agent phone number

        Returns:
            Formatted system prompt
        """
        return f"""You are a helpful and professional property inquiry assistant.

YOUR TASK: Verify if the property at {property_address} is currently available for rent.

INSTRUCTIONS:
1. Greet the agent/landlord professionally
2. Explain: "I'm calling to verify the availability of the property at {property_address}"
3. Ask: "Is this property currently available for rent?"
4. Listen carefully to their response
5. If unclear, ask ONE follow-up question
6. End the conversation within 2-3 minutes

DECISION FRAMEWORK:
- AVAILABLE: The agent clearly states the property IS available and showing is possible
- SOLD/RENTED: The agent states the property is NO LONGER available, rented out, or sold
- UNCLEAR: The agent is uncertain, wants to check something, or you cannot determine status

HOW TO END: Be clear about your determination:
- If available: "This property is AVAILABLE for rent"
- If sold/rented: "This property is SOLD or RENTED"
- If unclear: "I could not determine the status - this requires manual review"

IMPORTANT:
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

    def _parse_call_response(
        self, call_status: dict, property_id: int, agent_phone: str
    ) -> VerificationResult:
        """
        Parse ElevenLabs call response and determine availability.

        Args:
            call_status: Call status response from API
            property_id: Property ID
            agent_phone: Agent phone number called

        Returns:
            VerificationResult with determination
        """
        # Extract transcript and metadata
        transcript = call_status.get("transcript", "").strip() or ""
        duration_ms = call_status.get("duration_ms")
        duration_seconds = (duration_ms // 1000) if duration_ms else None
        status_str = call_status.get("status", "").lower()

        # Handle failed calls
        if status_str in ["failed", "failed_to_connect", "no_answer"]:
            logger.warning(f"Call to {agent_phone} failed with status: {status_str}")
            return VerificationResult(
                property_id=property_id,
                verification_status=VerificationStatus.FAILED,
                confidence_score=0.0,
                call_transcript=transcript,
                call_duration_seconds=duration_seconds,
                error_message=f"Call failed: {status_str}",
                agent_response=None,
                notes="Call failed to connect or was not answered",
            )

        # Determine status from transcript
        if not transcript:
            logger.warning(f"No transcript for property {property_id}")
            return VerificationResult(
                property_id=property_id,
                verification_status=VerificationStatus.UNCLEAR,
                confidence_score=0.3,
                call_transcript=transcript,
                call_duration_seconds=duration_seconds,
                agent_response="No response received",
                notes="No transcript available from call",
            )

        # Analyze transcript
        status, confidence = self._analyze_transcript(transcript)

        # Determine agent response summary
        agent_response = self._summarize_response(transcript)

        return VerificationResult(
            property_id=property_id,
            verification_status=status,
            confidence_score=confidence,
            call_transcript=transcript,
            call_duration_seconds=duration_seconds,
            agent_response=agent_response,
            notes=f"Analyzed {len(transcript)} character transcript",
        )

    def _analyze_transcript(self, transcript: str) -> Tuple[VerificationStatus, float]:
        """
        Analyze transcript to determine availability.

        Args:
            transcript: Call transcript

        Returns:
            Tuple of (VerificationStatus, confidence_score)
        """
        transcript_lower = transcript.lower()
        transcript_length = len(transcript)

        # Check for SOLD/RENTED first (more important than available)
        for pattern in self.SOLD_RENTED_KEYWORDS:
            if re.search(pattern, transcript_lower, re.IGNORECASE):
                confidence = min(0.95, 0.7 + (transcript_length / 1000))
                return VerificationStatus.SOLD, confidence

        # Check for AVAILABLE second
        for pattern in self.AVAILABLE_KEYWORDS:
            if re.search(pattern, transcript_lower, re.IGNORECASE):
                # Higher confidence with longer transcript
                confidence = min(0.95, 0.7 + (transcript_length / 1000))
                return VerificationStatus.AVAILABLE, confidence

        # No clear determination - mark for manual review
        # Higher confidence with longer conversation
        confidence = min(0.6, 0.3 + (transcript_length / 2000))

        if transcript_length < 100:
            return VerificationStatus.PENDING_REVIEW, confidence

        return VerificationStatus.UNCLEAR, confidence

    def _summarize_response(self, transcript: str) -> str:
        """
        Create a summary of agent's response.

        Args:
            transcript: Call transcript

        Returns:
            Summary string
        """
        # Take first 2-3 sentences as summary
        sentences = transcript.split(".")
        summary_parts = []

        for sentence in sentences[:3]:
            cleaned = sentence.strip()
            if cleaned and len(summary_parts) < 3:
                summary_parts.append(cleaned)

        summary = ". ".join(summary_parts)
        if summary and not summary.endswith("."):
            summary += "."

        return summary if summary else "Agent response recorded"
