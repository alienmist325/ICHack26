"""Configuration module for Rightmove scraper and backend services."""

import logging
from pydantic import Field
from pydantic_settings import BaseSettings

# Configure logging for this module
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration for Rightmove scraper."""

    apify_api_key: str = Field(
        ..., description="Apify API key for scraper access from console.apify.com"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        """Initialize settings and log configuration load."""
        super().__init__(**kwargs)
        logger.info("Configuration loaded successfully")


# Create a singleton instance
try:
    settings = Settings()
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise
