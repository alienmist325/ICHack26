"""Integration tests for mock Bland AI client with verification flow."""

import asyncio
import os
import time

import pytest

from backend.app.database import get_db
from backend.app.main import app
from backend.config import settings
from backend.services.verification.service import _verify_property_async


def test_mock_client_basic_flow():
    """Test mock Bland AI client basic flow."""
    # Only run this test if mock mode is enabled
    if not settings.bland_ai_mock_mode:
        pytest.skip("Mock mode not enabled - set BLAND_AI_MOCK_MODE=true")

    from backend.services.verification.bland_client import get_bland_client

    client = get_bland_client()

    # Make a mock call
    call_id = client.make_call("+44 7580 574377", "Test task")
    assert call_id is not None
    assert call_id.startswith("mock_call_")

    # Wait for call to complete
    result = client.wait_for_call_completion(call_id, max_wait_seconds=10)
    assert result is not None
    assert result.status == "completed"
    assert result.transcript is not None
    assert len(result.transcript) > 0
    print(f"Mock transcript: {result.transcript}")


def test_mock_verification_transcript_analysis():
    """Test that mock transcripts are properly analyzed."""
    if not settings.bland_ai_mock_mode:
        pytest.skip("Mock mode not enabled - set BLAND_AI_MOCK_MODE=true")

    from backend.services.verification.service import _analyze_transcript
    from backend.services.verification.models import VerificationStatus

    # Test AVAILABLE transcript
    available_transcript = "Yes, that property is still available for rent."
    status = _analyze_transcript(available_transcript, "rent")
    assert status == VerificationStatus.AVAILABLE

    # Test UNAVAILABLE transcript
    unavailable_transcript = "Sorry, that property has already been sold."
    status = _analyze_transcript(unavailable_transcript, "sale")
    assert status == VerificationStatus.UNAVAILABLE

    # Test UNSURE transcript
    unsure_transcript = "I'm not sure about that one."
    status = _analyze_transcript(unsure_transcript, "rent")
    assert status == VerificationStatus.UNSURE

    print("✅ Transcript analysis working correctly")


def test_mock_client_imported_correctly():
    """Test that mock client can be imported and initialized."""
    if not settings.bland_ai_mock_mode:
        pytest.skip("Mock mode not enabled - set BLAND_AI_MOCK_MODE=true")

    from backend.services.verification.mock_client import MockBlandAIClient

    client = MockBlandAIClient(timeout_seconds=120)
    assert client is not None
    assert client.timeout_seconds == 120


def test_mock_mode_setting_configurable():
    """Test that mock mode setting is properly configurable via environment."""
    # This test just verifies the setting exists and is readable
    # The actual value depends on whether BLAND_AI_MOCK_MODE env var is set
    assert hasattr(settings, "bland_ai_mock_mode")

    # Test that it reflects the environment variable
    mock_mode_env = os.environ.get("BLAND_AI_MOCK_MODE", "false").lower() == "true"
    assert settings.bland_ai_mock_mode == mock_mode_env


def test_mock_phone_number_configured():
    """Test that mock phone number is configured."""
    assert settings.bland_ai_mock_phone_number == "+44 7580 574377"
