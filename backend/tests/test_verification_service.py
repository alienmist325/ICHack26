"""Unit tests for property verification service."""

import pytest
from unittest.mock import AsyncMock

from services.verification.service import PropertyVerificationService
from services.verification.models import VerificationStatus
from services.verification.jobs import VerificationJob


class TestPropertyVerificationService:
    """Tests for PropertyVerificationService."""

    @pytest.fixture
    def verification_service(self):
        """Create a verification service instance."""
        return PropertyVerificationService(api_key="test-api-key")

    def test_service_initialization(self, verification_service):
        """Test that service initializes correctly."""
        assert verification_service.client is not None
        assert verification_service.client.api_key == "test-api-key"

    def test_service_initialization_without_key(self):
        """Test that service raises error without API key."""
        with pytest.raises(ValueError):
            PropertyVerificationService(api_key="")

    def test_format_system_prompt(self, verification_service):
        """Test that system prompt is formatted correctly."""
        prompt = verification_service._format_system_prompt(
            property_address="123 Test St, London",
            property_id=999,
            agent_phone="+447911123456",
        )

        assert "123 Test St, London" in prompt
        assert "999" in prompt
        assert "+447911123456" in prompt
        assert "professional property inquiry assistant" in prompt
        assert "Do NOT identify with any company" in prompt

    def test_analyze_transcript_available(self, verification_service):
        """Test transcript analysis for available properties."""
        transcript = "Yes, the property is currently available for rent. We can arrange a viewing."

        status, confidence = verification_service._analyze_transcript(transcript)

        assert status == VerificationStatus.AVAILABLE
        assert confidence > 0.7

    def test_analyze_transcript_sold(self, verification_service):
        """Test transcript analysis for sold properties."""
        transcript = "That property has been sold already. It's no longer available."

        status, confidence = verification_service._analyze_transcript(transcript)

        assert status == VerificationStatus.SOLD
        assert confidence > 0.7

    def test_analyze_transcript_unclear(self, verification_service):
        """Test transcript analysis for unclear responses."""
        transcript = "Maybe, I'm not sure. You might want to check back next week."

        status, confidence = verification_service._analyze_transcript(transcript)

        assert status in [VerificationStatus.UNCLEAR, VerificationStatus.PENDING_REVIEW]

    def test_analyze_transcript_empty(self, verification_service):
        """Test transcript analysis with empty transcript."""
        status, confidence = verification_service._analyze_transcript("")

        assert status == VerificationStatus.PENDING_REVIEW
        assert confidence < 0.5

    def test_analyze_transcript_rented(self, verification_service):
        """Test transcript analysis for rented properties."""
        transcript = "Sorry, that property has been rented out already."

        status, confidence = verification_service._analyze_transcript(transcript)

        assert status == VerificationStatus.SOLD  # Rented = not available
        assert confidence > 0.7

    def test_summarize_response(self, verification_service):
        """Test response summarization."""
        transcript = (
            "Yes, the property is available. We have a showing available this weekend."
        )

        summary = verification_service._summarize_response(transcript)

        assert len(summary) > 0
        assert "available" in summary.lower()

    def test_summarize_response_short(self, verification_service):
        """Test response summarization with short transcript."""
        transcript = "Yes."

        summary = verification_service._summarize_response(transcript)

        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_verify_property_success(self, verification_service):
        """Test successful property verification."""
        # Mock the ElevenLabs client
        mock_call_response = {"call_id": "call_123"}
        mock_final_status = {
            "status": "completed",
            "transcript": "Yes, the property is available for rent.",
            "duration_ms": 120000,
        }

        verification_service.client.initiate_call = AsyncMock(
            return_value=mock_call_response
        )
        verification_service.client.wait_for_call_completion = AsyncMock(
            return_value=mock_final_status
        )

        job = VerificationJob(property_id=123)

        result = await verification_service.verify_property(
            job=job,
            agent_id="agent_123",
            phone_number="+1234567890",
            property_address="123 Test St",
            agent_phone="+447911123456",
            call_timeout=600,
        )

        assert result.property_id == 123
        assert result.verification_status == VerificationStatus.AVAILABLE
        assert result.confidence_score > 0
        assert result.call_duration_seconds == 120
        assert result.call_transcript is not None

    @pytest.mark.asyncio
    async def test_verify_property_call_failed(self, verification_service):
        """Test verification when call fails."""
        # Mock the ElevenLabs client
        mock_call_response = {"call_id": "call_456"}
        mock_final_status = {
            "status": "failed",
            "transcript": "",
        }

        verification_service.client.initiate_call = AsyncMock(
            return_value=mock_call_response
        )
        verification_service.client.wait_for_call_completion = AsyncMock(
            return_value=mock_final_status
        )

        job = VerificationJob(property_id=123)

        result = await verification_service.verify_property(
            job=job,
            agent_id="agent_123",
            phone_number="+1234567890",
            property_address="123 Test St",
            agent_phone="+447911123456",
        )

        assert result.property_id == 123
        assert result.verification_status == VerificationStatus.FAILED
        assert result.confidence_score == 0.0
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_verify_property_no_call_id(self, verification_service):
        """Test verification when API doesn't return call_id."""
        mock_call_response = {}  # No call_id

        verification_service.client.initiate_call = AsyncMock(
            return_value=mock_call_response
        )

        job = VerificationJob(property_id=123)

        with pytest.raises(ValueError):
            await verification_service.verify_property(
                job=job,
                agent_id="agent_123",
                phone_number="+1234567890",
                property_address="123 Test St",
                agent_phone="+447911123456",
            )


class TestVerificationJob:
    """Tests for VerificationJob."""

    def test_job_initialization(self):
        """Test that job initializes correctly."""
        job = VerificationJob(property_id=123)

        assert job.property_id == 123
        assert job.job_id is not None
        assert len(job.job_id) == 36  # UUID4 format
        assert job.status.value == "queued"
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None
        assert job.error is None

    def test_job_to_dict(self):
        """Test job serialization to dict."""
        job = VerificationJob(property_id=123)
        job_dict = job.to_dict()

        assert job_dict["property_id"] == 123
        assert job_dict["job_id"] == job.job_id
        assert job_dict["status"] == "queued"
        assert job_dict["created_at"] is not None
        assert job_dict["started_at"] is None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
