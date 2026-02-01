"""Integration tests for mock Bland AI client with verification flow."""

import pytest

from backend.config import settings


def test_mock_client_basic_flow():
    """Test mock Bland AI client basic flow."""
    # Only run this test if mock mode is enabled
    if not settings.bland_ai_mock_mode:
        pytest.skip("Mock mode not enabled - set BLAND_AI_MOCK_MODE=true")

    from backend.services.verification.bland_client import get_bland_client

    client = get_bland_client()

    # Make a mock call using configured phone number
    phone_number = settings.bland_ai_mock_phone_number
    assert phone_number is not None, (
        "BLAND_AI_MOCK_PHONE_NUMBER must be set in .env for mock testing"
    )

    call_id = client.make_call(phone_number, "Test task")
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
    """Test that mock mode setting is properly configurable via .env."""
    # This test just verifies the setting exists and is readable
    # Settings come from .env file, so we just verify the setting exists
    assert hasattr(settings, "bland_ai_mock_mode")
    assert isinstance(settings.bland_ai_mock_mode, bool)
    # The actual value depends on .env file configuration
    # In this case, .env has BLAND_AI_MOCK_MODE=true, so it should be True
    assert settings.bland_ai_mock_mode is True


def test_mock_phone_number_configured():
    """Test that mock phone number is configured."""
    # In mock mode, phone number must be set in .env
    if settings.bland_ai_mock_mode:
        assert settings.bland_ai_mock_phone_number is not None, (
            "BLAND_AI_MOCK_PHONE_NUMBER must be set in .env when BLAND_AI_MOCK_MODE=true"
        )
        assert isinstance(settings.bland_ai_mock_phone_number, str)
        assert settings.bland_ai_mock_phone_number.startswith("+")
    else:
        # When mock mode is off, phone number should be None (default)
        # User must configure in .env if using mock mode
        pass


def test_transcript_analysis_simple_yes():
    """Test analysis correctly identifies 'yes' responses in Bland AI format."""
    from backend.services.verification.service import _analyze_transcript
    from backend.services.verification.models import VerificationStatus

    # Bland AI format: "A: question\n user: answer"
    transcripts = [
        "A: Is it available?\n user: Yes.",
        "A: Status?\n user: Yes",
        "A: Is this property still available?\n user: Yes, it is.",
    ]

    for transcript in transcripts:
        status = _analyze_transcript(transcript, "sale")
        assert status == VerificationStatus.AVAILABLE, f"Failed for: {transcript}"


def test_transcript_analysis_simple_no():
    """Test analysis correctly identifies 'no' responses in Bland AI format."""
    from backend.services.verification.service import _analyze_transcript
    from backend.services.verification.models import VerificationStatus

    # Bland AI format: "user: No." at start of response line
    transcripts = [
        "A: Is it available?\n user: No.",
        "A: Status?\n user: No",
        "A: Still on market?\n user: Nope.",
        "A: Available?\n user: No, sorry.",
    ]

    for transcript in transcripts:
        status = _analyze_transcript(transcript, "sale")
        assert status == VerificationStatus.UNAVAILABLE, f"Failed for: {transcript}"


def test_transcript_analysis_sold_keywords():
    """Test analysis correctly identifies sold/rented properties."""
    from backend.services.verification.service import _analyze_transcript
    from backend.services.verification.models import VerificationStatus

    transcripts = [
        "That property has been sold already.",
        "It was rented out last month.",
        "The property has already been let.",
        "It's off the market - sold.",
        "That one's no longer listed.",
        "The property was withdrawn from the market.",
    ]

    for transcript in transcripts:
        status = _analyze_transcript(transcript, "sale")
        assert status == VerificationStatus.UNAVAILABLE, f"Failed for: {transcript}"


def test_transcript_analysis_available_keywords():
    """Test analysis correctly identifies available properties."""
    from backend.services.verification.service import _analyze_transcript
    from backend.services.verification.models import VerificationStatus

    transcripts = [
        "Yes, the property is still available for rent.",
        "We still have this listed for sale.",
        "It's still on the market actively.",
        "We haven't sold that one yet.",
        "That's still our current listing.",
        "The property is still for sale with us.",
        "We're actively marketing that property.",
    ]

    for transcript in transcripts:
        status = _analyze_transcript(transcript, "sale")
        assert status == VerificationStatus.AVAILABLE, f"Failed for: {transcript}"


def test_transcript_analysis_unsure_keywords():
    """Test analysis correctly identifies ambiguous responses."""
    from backend.services.verification.service import _analyze_transcript
    from backend.services.verification.models import VerificationStatus

    transcripts = [
        "I'm not sure about that property.",
        "Let me check our system... I'm not entirely sure.",
        "Maybe it's still available, I can't find it quickly.",
        "I think so, but I'd need to verify that.",
        "The status might be... I'm not certain.",
        "I can't find that one quickly in our system.",
    ]

    for transcript in transcripts:
        status = _analyze_transcript(transcript, "sale")
        assert status == VerificationStatus.UNSURE, f"Failed for: {transcript}"


def test_transcript_analysis_negation_patterns():
    """Test analysis correctly handles negation patterns."""
    from backend.services.verification.service import _analyze_transcript
    from backend.services.verification.models import VerificationStatus

    unavailable_transcripts = [
        "Unfortunately it's not available anymore.",
        "The property isn't listed anymore.",
        "We don't have that one available.",
        "I couldn't locate that property.",
    ]

    for transcript in unavailable_transcripts:
        status = _analyze_transcript(transcript, "sale")
        assert status == VerificationStatus.UNAVAILABLE, (
            f"Failed (should be UNAVAILABLE): {transcript}"
        )


def test_transcript_analysis_edge_cases():
    """Test analysis with edge cases and real API transcripts."""
    from backend.services.verification.service import _analyze_transcript
    from backend.services.verification.models import VerificationStatus

    # Real transcript from Bland AI API (concatenated_transcript format)
    real_transcript = """A: Hi, I'm calling to check if One Hyde Park, Knightsbridge, London, SW1X is still available for sale. Can you confirm if this property is still on the market? Please just say yes or no. 
 user: No. 
 assistant: Thank you for your time. Goodbye. 
 agent-action: Ended call"""

    status = _analyze_transcript(real_transcript, "sale")
    assert status == VerificationStatus.UNAVAILABLE, (
        "Real API example should classify as UNAVAILABLE"
    )

    # Empty or whitespace
    assert _analyze_transcript("", "sale") == VerificationStatus.UNSURE
    assert _analyze_transcript("   ", "sale") == VerificationStatus.UNSURE
    assert _analyze_transcript(None, "sale") == VerificationStatus.UNSURE

    # Another real format with Yes response
    yes_transcript = """A: Is this property still available?
 user: Yes.
 assistant: Thank you."""
    status = _analyze_transcript(yes_transcript, "sale")
    assert status == VerificationStatus.AVAILABLE, (
        "Real API with Yes should classify as AVAILABLE"
    )
