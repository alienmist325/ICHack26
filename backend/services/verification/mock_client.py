"""Mock Bland AI client for testing without making real API calls.

This module provides a MockBlandAIClient that simulates Bland AI behavior
without actually calling the Bland AI API. It's useful for:
- Testing the verification flow without consuming API credits
- Testing without calling real agent phone numbers
- Simulating different call outcomes (success, failure, timeout)

When BLAND_AI_MOCK_MODE=true, the mock client is used instead of the real one.
All calls are routed to the configured test phone number.
"""

import asyncio
import logging
import random
import time
import uuid
from typing import Optional

from backend.services.verification.models import BlandCallResult

# Track completed calls globally to share state between sync and async calls
_completed_calls: dict[str, BlandCallResult] = {}

logger = logging.getLogger(__name__)


class MockBlandAIClient:
    """Mock client for Bland AI API that simulates calls without real API calls."""

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 120):
        """Initialize Mock Bland AI client.

        Args:
            api_key: Ignored (not needed for mock)
            timeout_seconds: Max seconds to wait for call completion
        """
        self.timeout_seconds = timeout_seconds
        self.api_key = "mock"  # Placeholder
        # Use global call storage to share state between sync and async methods
        self._calls = _completed_calls
        logger.info("[MOCK] MockBlandAIClient initialized")

    def make_call(self, phone_number: str, task: str) -> Optional[str]:
        """Initiate a simulated Bland AI call.

        Args:
            phone_number: Phone number to call (will be called for real in mock mode)
            task: Task/prompt for the call

        Returns:
            call_id if successful, None otherwise
        """
        logger.info(f"[MOCK] Initiating simulated call to {phone_number}")
        logger.debug(f"[MOCK] Task: {task}")

        # Generate a realistic-looking call ID
        call_id = f"mock_call_{uuid.uuid4().hex[:12]}"

        # Store call info with initial "in_progress" status
        # We'll update it after simulating delay
        self._calls[call_id] = BlandCallResult(
            call_id=call_id,
            status="in_progress",
            duration=0,
            transcript=None,
            success=False,
            data=None,
        )

        logger.info(f"[MOCK] Mock call {call_id} created (phone: {phone_number})")
        return call_id

    def get_call_result(self, call_id: str) -> Optional[BlandCallResult]:
        """Get the result of a simulated Bland AI call.

        Args:
            call_id: The call ID

        Returns:
            BlandCallResult if call found, None otherwise
        """
        if call_id not in self._calls:
            logger.error(f"[MOCK] Call {call_id} not found")
            return None

        result = self._calls[call_id]
        logger.debug(f"[MOCK] Call {call_id} status: {result.status}")
        return result

    def wait_for_call_completion(
        self,
        call_id: str,
        max_wait_seconds: Optional[int] = None,
        poll_interval_seconds: float = 2.0,
    ) -> Optional[BlandCallResult]:
        """Wait for a simulated Bland AI call to complete with polling.

        Simulates realistic call behavior:
        - 2-5 second call duration
        - Random transcript generation
        - Realistic status progression

        Args:
            call_id: The call ID to wait for
            max_wait_seconds: Maximum seconds to wait (defaults to self.timeout_seconds)
            poll_interval_seconds: Seconds between polls

        Returns:
            BlandCallResult when completed, None if timeout/error
        """
        if call_id not in self._calls:
            logger.error(f"[MOCK] Call {call_id} not found")
            return None

        logger.info(f"[MOCK] Waiting for simulated call {call_id} to complete")

        # Simulate call duration (2-5 seconds)
        simulated_duration = random.uniform(2, 5)
        logger.debug(f"[MOCK] Simulating {simulated_duration:.1f}s call duration")

        max_wait = max_wait_seconds or self.timeout_seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            # Check if we've simulated enough time for call to complete
            time_elapsed = time.time() - start_time

            if time_elapsed >= simulated_duration:
                # Call should be completed now
                result = self._calls[call_id]

                # Only generate transcript once
                if result.transcript is None:
                    result.transcript = self._generate_mock_transcript()
                    result.duration = int(simulated_duration)
                    result.status = "completed"
                    result.success = True

                    logger.info(
                        f"[MOCK] Call {call_id} completed with status: {result.status}"
                    )
                    logger.debug(f"[MOCK] Transcript: {result.transcript}")

                return result

            # Still waiting for simulated duration
            logger.debug(
                f"[MOCK] Call {call_id} still in progress ({time_elapsed:.1f}s/{simulated_duration:.1f}s)"
            )
            time.sleep(poll_interval_seconds)

        logger.warning(
            f"[MOCK] Timeout waiting for call {call_id} after {max_wait} seconds"
        )
        return None

    async def wait_for_call_completion_async(
        self,
        call_id: str,
        max_wait_seconds: Optional[int] = None,
        poll_interval_seconds: float = 2.0,
    ) -> Optional[BlandCallResult]:
        """Async version: Wait for a simulated Bland AI call to complete.

        This is the async equivalent of wait_for_call_completion.
        Used by async verification service for non-blocking call monitoring.

        Args:
            call_id: The call ID to wait for
            max_wait_seconds: Maximum seconds to wait (defaults to self.timeout_seconds)
            poll_interval_seconds: Seconds between polls

        Returns:
            BlandCallResult when completed, None if timeout/error
        """
        if call_id not in self._calls:
            logger.error(f"[MOCK] Async: Call {call_id} not found")
            return None

        logger.info(f"[MOCK] Async: Waiting for simulated call {call_id} to complete")

        # Simulate call duration (2-5 seconds)
        simulated_duration = random.uniform(2, 5)
        logger.debug(
            f"[MOCK] Async: Simulating {simulated_duration:.1f}s call duration"
        )

        max_wait = max_wait_seconds or self.timeout_seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            # Check if we've simulated enough time for call to complete
            time_elapsed = time.time() - start_time

            if time_elapsed >= simulated_duration:
                # Call should be completed now
                result = self._calls[call_id]

                # Only generate transcript once
                if result.transcript is None:
                    result.transcript = self._generate_mock_transcript()
                    result.duration = int(simulated_duration)
                    result.status = "completed"
                    result.success = True

                    logger.info(
                        f"[MOCK] Async: Call {call_id} completed with status: {result.status}"
                    )
                    logger.debug(f"[MOCK] Async: Transcript: {result.transcript}")

                return result

            # Still waiting for simulated duration
            logger.debug(
                f"[MOCK] Async: Call {call_id} still in progress ({time_elapsed:.1f}s/{simulated_duration:.1f}s)"
            )
            await asyncio.sleep(poll_interval_seconds)

        logger.warning(
            f"[MOCK] Async: Timeout waiting for call {call_id} after {max_wait} seconds"
        )
        return None

    def _generate_mock_transcript(self) -> str:
        """Generate a random mock transcript simulating agent responses.

        Returns realistic-sounding agent responses that will trigger different
        verification statuses based on keyword analysis.

        Returns:
            A mock transcript string
        """
        # Available transcripts (for rent listings)
        available_rent = [
            "Yes, that property is still available for rent. We can arrange a viewing whenever you're free.",
            "Yes, we still have that property available. It's listed and ready to rent.",
            "Yes, that one is still available for rent. Would you like to schedule a viewing?",
            "Yes, that's still on our rental list. It's a great property.",
            "Yes, absolutely. That property is still available. We can show it to interested tenants.",
        ]

        # Available transcripts (for sale listings)
        available_sale = [
            "Yes, this property is still on the market. We're actively marketing it.",
            "Yes, we still have this property for sale. It's a great opportunity.",
            "Yes, that's still listed for sale. Would you like more information?",
            "Yes, absolutely. That property is still available for purchase.",
            "Yes, we're still selling that property. It hasn't been sold yet.",
        ]

        # Unavailable transcripts
        unavailable = [
            "Sorry, that property has already been rented out. It's no longer available.",
            "No, that property has been sold. It's off the market now.",
            "I'm afraid that one's been let already. We don't have it anymore.",
            "Sorry, that property is no longer available. It was rented last week.",
            "No, that's been sold. We took it off the listing.",
            "Unfortunately, that property has already found a tenant.",
            "Sorry, that one's no longer available. It sold a few days ago.",
        ]

        # Unsure transcripts
        unsure = [
            "I'm not entirely sure about that one. You'd have to check our online listings.",
            "Hmm, I think so, but I'd need to verify that in our system.",
            "Maybe? I'm not certain about the current status of that property.",
            "I'm not sure off the top of my head. Let me check... sorry, I can't find that one quickly.",
            "I believe so, but I'd recommend checking our website for the most current information.",
            "That one might be available, but I'm not completely certain.",
        ]

        # Randomly choose availability status based on weighted probabilities
        rand = random.random()

        if rand < 0.5:
            # 50% chance: AVAILABLE
            # For demonstration, randomly choose between rent and sale transcripts
            pool = random.choice([available_rent, available_sale])
            transcript = random.choice(pool)
            logger.debug("[MOCK] Generated AVAILABLE transcript")
        elif rand < 0.8:
            # 30% chance: UNAVAILABLE
            transcript = random.choice(unavailable)
            logger.debug("[MOCK] Generated UNAVAILABLE transcript")
        else:
            # 20% chance: UNSURE
            transcript = random.choice(unsure)
            logger.debug("[MOCK] Generated UNSURE transcript")

        return transcript
