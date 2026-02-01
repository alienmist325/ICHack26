"""ElevenLabs Agents API client for making property verification calls."""

import asyncio
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class ElevenLabsClient:
    """HTTP client for ElevenLabs Agents API."""

    BASE_URL = "https://api.elevenlabs.io/v1"
    DEFAULT_TIMEOUT = 30

    def __init__(self, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize ElevenLabs API client.

        Args:
            api_key: ElevenLabs API key
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("ElevenLabs API key is required")

        self.api_key = api_key
        self.timeout = timeout
        self.headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }

    async def initiate_call(
        self,
        agent_id: str,
        phone_number: str,
        system_prompt: Optional[str] = None,
        first_message: Optional[str] = None,
        language_code: str = "en",
    ) -> dict:
        """
        Initiate an outbound call via ElevenLabs Agents API.

        Args:
            agent_id: ElevenLabs Agent ID
            phone_number: Phone number to call (E.164 format: +1234567890)
            system_prompt: Override agent system prompt
            first_message: Override agent first message
            language_code: Language code (default: 'en')

        Returns:
            API response containing call_id and status

        Raises:
            httpx.HTTPError: If API call fails
        """
        url = f"{self.BASE_URL}/agents/{agent_id}/call-initiate"

        payload = {
            "phoneNumber": phone_number,
            "languageCode": language_code,
        }

        if system_prompt:
            payload["systemPrompt"] = system_prompt
        if first_message:
            payload["firstMessage"] = first_message

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"ElevenLabs API error initiating call: {e}")
                raise

    async def get_call_status(self, agent_id: str, call_id: str) -> dict:
        """
        Get the status of an ongoing or completed call.

        Args:
            agent_id: ElevenLabs Agent ID
            call_id: Call ID to check

        Returns:
            API response with call status and details

        Raises:
            httpx.HTTPError: If API call fails
        """
        url = f"{self.BASE_URL}/agents/{agent_id}/calls/{call_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    url,
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"ElevenLabs API error getting call status: {e}")
                raise

    async def wait_for_call_completion(
        self,
        agent_id: str,
        call_id: str,
        max_wait_seconds: int = 600,
        poll_interval_seconds: int = 5,
    ) -> dict:
        """
        Poll call status until completion (with timeout).

        Args:
            agent_id: ElevenLabs Agent ID
            call_id: Call ID to monitor
            max_wait_seconds: Maximum seconds to wait (default: 10 minutes)
            poll_interval_seconds: Polling interval in seconds (default: 5)

        Returns:
            Final call status response

        Raises:
            TimeoutError: If call doesn't complete within max_wait_seconds
            httpx.HTTPError: If API call fails
        """
        elapsed = 0
        max_wait_ms = max_wait_seconds * 1000

        while elapsed < max_wait_ms:
            try:
                status = await self.get_call_status(agent_id, call_id)

                # Check if call is complete
                call_status = status.get("status", "").lower()
                if call_status in [
                    "completed",
                    "failed",
                    "failed_to_connect",
                    "no_answer",
                ]:
                    logger.info(f"Call {call_id} completed with status: {call_status}")
                    return status

                # Not done yet, wait before polling again
                await asyncio.sleep(poll_interval_seconds)
                elapsed += poll_interval_seconds * 1000

            except httpx.HTTPError as e:
                logger.error(f"Error polling call status: {e}")
                raise

        # Timeout reached
        raise TimeoutError(
            f"Call {call_id} did not complete within {max_wait_seconds} seconds"
        )

    async def close(self) -> None:
        """Close any open connections (for cleanup)."""
        # httpx.AsyncClient is context-managed, nothing to do here
        pass
