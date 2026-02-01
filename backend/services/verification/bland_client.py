"""Bland AI API client for making phone calls to verify properties."""

import logging
import sys
import time
from typing import Any, Optional

import requests
from pydantic import ValidationError

from backend.config import settings
from backend.services.verification.models import BlandCallResult

logger = logging.getLogger(__name__)

# Bland AI API endpoints
BLAND_AI_BASE_URL = "https://api.bland.ai"
BLAND_AI_MAKE_CALL = f"{BLAND_AI_BASE_URL}/v1/calls"
BLAND_AI_GET_CALL = f"{BLAND_AI_BASE_URL}/v1/calls"


class BlandAIClient:
    """Client for Bland AI API."""

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 120):
        """Initialize Bland AI client.

        Args:
            api_key: Bland AI API key (defaults to config)
            timeout_seconds: Max seconds to wait for call completion
        """
        self.api_key = api_key or settings.bland_ai_api_key
        self.timeout_seconds = timeout_seconds
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def make_call(self, phone_number: str, task: str) -> Optional[str]:
        """Initiate a Bland AI call.

        Args:
            phone_number: Phone number to call
            task: Task/prompt for the call

        Returns:
            call_id if successful, None otherwise
        """
        if not self.api_key:
            logger.error("Bland AI API key not configured")
            return None

        payload = {
            "phone_number": phone_number,
            "task": task,
            "language": "en",
            "voice_id": 0,
        }

        try:
            response = requests.post(
                BLAND_AI_MAKE_CALL,
                json=payload,
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            call_id = data.get("call_id")
            logger.info(f"Started Bland AI call {call_id} to {phone_number}")
            return call_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to initiate Bland AI call: {e}")
            return None

    def get_call_result(self, call_id: str) -> Optional[BlandCallResult]:
        """Get the result of a Bland AI call.

        Args:
            call_id: The call ID

        Returns:
            BlandCallResult if call completed, None otherwise
        """
        if not self.api_key:
            logger.error("Bland AI API key not configured")
            return None

        try:
            response = requests.get(
                f"{BLAND_AI_GET_CALL}/{call_id}",
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            logger.debug(f"Bland AI API response: {data}")

            # Map API response to BlandCallResult
            # Bland AI API returns: concatenated_transcript (or transcript in some versions)
            # Also returns call_length (not duration), status, etc.
            transcript = data.get("concatenated_transcript") or data.get("transcript")

            # Handle duration conversion safely - Bland AI may return string or int
            call_length = data.get("call_length", 0)
            try:
                duration = int(call_length) if call_length else 0
            except (ValueError, TypeError):
                logger.warning(
                    f"Could not parse call_length as int: {call_length} (type: {type(call_length).__name__})"
                )
                duration = 0

            result = BlandCallResult(
                call_id=call_id,
                status=str(data.get("status", "unknown")),
                duration=duration,
                transcript=transcript,
                success=bool(data.get("success", False)),
                data=data.get("data"),
            )
            logger.debug(
                f"Parsed BlandCallResult: call_id={result.call_id}, status={result.status}, duration={result.duration}s"
            )
            logger.debug(f"Transcript: {transcript[:200] if transcript else 'None'}...")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Bland AI call result: {e}")
            return None
        except ValidationError as e:
            logger.error(f"Pydantic validation error parsing Bland AI response: {e}")
            logger.error(f"Raw API data: {data}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse Bland AI response: {e}")
            return None

    def wait_for_call_completion(
        self,
        call_id: str,
        max_wait_seconds: Optional[int] = None,
        poll_interval_seconds: float = 2.0,
    ) -> Optional[BlandCallResult]:
        """Wait for a Bland AI call to complete with polling.

        Args:
            call_id: The call ID to wait for
            max_wait_seconds: Maximum seconds to wait (defaults to self.timeout_seconds)
            poll_interval_seconds: Seconds between polls

        Returns:
            BlandCallResult when completed, None if timeout/error
        """
        max_wait = max_wait_seconds or self.timeout_seconds
        start_time = time.time()

        while time.time() - start_time < max_wait:
            result = self.get_call_result(call_id)

            if result is None:
                logger.error(f"Error fetching call result for {call_id}")
                time.sleep(poll_interval_seconds)
                continue

            # Check if call completed (status should be "completed", "failed", etc.)
            if result.status in ["completed", "failed", "error"]:
                logger.info(f"Call {call_id} completed with status: {result.status}")
                return result

            # Still in progress, wait before polling again
            logger.debug(f"Call {call_id} still in progress (status: {result.status})")
            time.sleep(poll_interval_seconds)

        logger.warning(f"Timeout waiting for call {call_id} after {max_wait} seconds")
        return None


# Singleton client instance (can be either BlandAIClient or MockBlandAIClient)
_client: Optional[Any] = None


def get_bland_client() -> Any:
    """Get or create the Bland AI client singleton.

    Client selection logic:
    1. If running under pytest: Use MockBlandAIClient (safety layer - no real calls)
    2. Otherwise: Always use real BlandAIClient
       - BLAND_AI_MOCK_MODE=true: Routes calls to mock phone number instead of agent phone
       - BLAND_AI_MOCK_MODE=false: Routes calls to real agent phone numbers (production)

    This ensures pytest can never make real API calls, but mock mode still uses real API.
    """
    global _client
    if _client is None:
        is_pytest = "pytest" in sys.modules

        if is_pytest:
            logger.warning(
                "[PYTEST] Using MockBlandAIClient during pytest (safety layer - no real API calls)"
            )
            from backend.services.verification.mock_client import MockBlandAIClient

            _client = MockBlandAIClient(
                timeout_seconds=settings.bland_ai_timeout_seconds,
            )
        else:
            # Use real client for both MOCK_MODE and PRODUCTION
            # The phone number routing (mock vs real) is handled in the service layer
            is_mock_mode = settings.bland_ai_mock_mode
            mode_str = (
                "MOCK MODE (calling test phone)"
                if is_mock_mode
                else "PRODUCTION MODE (calling agent phone)"
            )
            logger.info(f"[PRODUCTION] Using real BlandAIClient - {mode_str}")
            _client = BlandAIClient(
                timeout_seconds=settings.bland_ai_timeout_seconds,
            )
    return _client
