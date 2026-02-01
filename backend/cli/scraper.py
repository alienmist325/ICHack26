"""
Standalone Rightmove scraper module for CLI usage.

Provides functions to scrape Rightmove properties and store them in the database,
independent of the FastAPI backend.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Add backend directory to path to allow relative imports to work
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import crud
from backend.models.rightmove import RightmoveProperty, RightmoveScraperInput
from backend.scraper.scrape import scrape_rightmove

# Configure logging
logger = logging.getLogger(__name__)


def run_scraper(config: RightmoveScraperInput) -> Dict[str, int]:
    """
    Run Rightmove scraper and store properties in database.

    This function:
    1. Validates the scraper configuration
    2. Calls the async scraper to fetch properties from Apify
    3. Converts each property to the database schema
    4. Upserts properties into the database (create or update)
    5. Tracks statistics and returns summary

    Args:
        config: RightmoveScraperInput configuration with scraping parameters

    Returns:
        Dictionary with summary statistics:
        {
            "total": int,      # Total properties scraped
            "created": int,    # Number of new properties created
            "updated": int,    # Number of existing properties updated
            "failed": int,     # Number of properties that failed to store
        }

    Raises:
        ValueError: If configuration is invalid or API key is missing
        Exception: If scraping or database operations fail
    """
    logger.info(
        f"Starting Rightmove scraper with config: {config.model_dump(exclude_unset=True)}"
    )

    try:
        # Run async scraper
        response = asyncio.run(scrape_rightmove(config))

        if not response.properties:
            logger.warning("Scrape completed but no properties returned")
            return {"total": 0, "created": 0, "updated": 0, "failed": 0}

        logger.info(f"Scraped {len(response.properties)} properties from Rightmove")

        # Convert and store each property
        stats = {
            "total": len(response.properties),
            "created": 0,
            "updated": 0,
            "failed": 0,
        }

        for rightmove_prop in response.properties:
            try:
                # Convert RightmoveProperty to PropertyCreate
                property_data = crud.rightmove_property_to_create(rightmove_prop)

                # Upsert into database (create or update based on rightmove_id)
                property_obj, created = crud.upsert_property(property_data)

                if created:
                    stats["created"] += 1
                    logger.debug(
                        f"Created property {rightmove_prop.id}: {rightmove_prop.title}"
                    )
                else:
                    stats["updated"] += 1
                    logger.debug(
                        f"Updated property {rightmove_prop.id}: {rightmove_prop.title}"
                    )

            except Exception as e:
                stats["failed"] += 1
                logger.error(
                    f"Failed to store property {rightmove_prop.id}: {str(e)}",
                    exc_info=True,
                )
                # Continue with next property instead of failing entire operation
                continue

        logger.info(
            f"Successfully processed {stats['created'] + stats['updated']} properties "
            f"({stats['created']} created, {stats['updated']} updated, {stats['failed']} failed)"
        )

        return stats

    except ValueError as e:
        # Configuration/validation error
        logger.error(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        # Unexpected error
        logger.error(f"Scraping failed: {str(e)}", exc_info=True)
        raise
