"""Configuration module for Rightmove scraper and backend services."""

import logging
from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

# Configure logging for this module
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration for Rightmove scraper, routing, and verification services."""

    # Apify configuration
    apify_api_key: str = Field(
        ..., description="Apify API key for scraper access from console.apify.com"
    )

    # Routing service configuration
    routing_provider: str = Field(
        default="graphhopper",
        description="Routing provider to use: graphhopper (default), osrm, mapbox, etc.",
    )
    routing_api_key: Optional[str] = Field(
        default=None,
        description="API key for routing service (required for GraphHopper)",
    )
    graphhopper_base_url: str = Field(
        default="https://graphhopper.com/api/1",
        description="Base URL for GraphHopper API (default: official cloud API)",
    )
    routing_timeout_seconds: int = Field(
        default=30,
        description="Timeout for routing API requests in seconds",
    )

    # ElevenLabs verification settings
    elevenlabs_api_key: Optional[str] = Field(
        default="", description="ElevenLabs API key for property verification calls"
    )
    elevenlabs_agent_id: Optional[str] = Field(
        default=None, description="ElevenLabs Agent ID for property verification"
    )
    elevenlabs_phone_number: Optional[str] = Field(
        default=None, description="Twilio/ElevenLabs phone number for outbound calls"
    )

    # Verification service tuning parameters
    verification_call_timeout: int = Field(
        default=600, description="Maximum call duration in seconds (default: 10 min)"
    )
    verification_max_concurrent_calls: int = Field(
        default=5, description="Maximum concurrent verification calls (default: 5)"
    )

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env
    )

    def __init__(self, **kwargs):
        """Initialize settings and log configuration load."""
        super().__init__(**kwargs)
        logger.info("Configuration loaded successfully")

        # Log verification setup status
        if self.elevenlabs_api_key:
            logger.info("ElevenLabs verification service configured")
        else:
            logger.warning(
                "ElevenLabs API key not configured - verification service disabled"
            )


# Create a singleton instance
try:
    settings = Settings()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise

# ============================================================================
# Convenience exports for routing service configuration
# ============================================================================

ROUTING_PROVIDER: str = settings.routing_provider
GRAPHHOPPER_BASE_URL: str = settings.graphhopper_base_url
ROUTING_API_KEY: Optional[str] = settings.routing_api_key
ROUTING_TIMEOUT_SECONDS: int = settings.routing_timeout_seconds

# UK geographic bounds for coordinate validation
UK_BOUNDS = {
    "north": 60.86,  # Scottish Islands
    "south": 49.86,  # English coast
    "east": 1.68,  # East Anglia
    "west": -8.65,  # Northern Ireland
}
