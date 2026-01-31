"""Rightmove scraper module using Apify API."""

import logging
from typing import Optional

from apify_client import ApifyClientAsync

from backend.config import settings
from backend.models.rightmove import (
    RightmoveScraperInput,
    RightmoveResponse,
    RightmoveProperty,
)

# Configure logging
logger = logging.getLogger(__name__)


async def scrape_rightmove(
    scraper_input: RightmoveScraperInput,
) -> RightmoveResponse:
    """
    Scrape properties from Rightmove using the Apify scraper actor.

    This async function takes a RightmoveScraperInput configuration and returns
    a RightmoveResponse containing all scraped properties from Rightmove.

    Args:
        scraper_input: Configuration for the scraper including URLs, options, and limits

    Returns:
        RightmoveResponse: A validated response containing the list of scraped properties

    Raises:
        ValueError: If the Apify API key is not configured
        Exception: If the Apify API call fails or returns no data
    """
    # Validate API key is configured
    if not settings.apify_api_key:
        error_msg = (
            "Apify API key not configured. Please set APIFY_API_KEY in .env file"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(
        f"Starting Rightmove scraper with maxProperties={scraper_input.maxProperties}"
    )
    logger.debug(f"Scraper input: {scraper_input}")

    try:
        # Initialize Apify client
        apify_client = ApifyClientAsync(settings.apify_api_key)
        logger.info("Apify client initialized")

        # Get the actor client for Rightmove scraper
        actor_client = apify_client.actor("dhrumil/rightmove-scraper")
        logger.info("Connected to dhrumil/rightmove-scraper actor")

        # Convert Pydantic model to Apify-compatible dictionary
        run_input = scraper_input.to_apify_dict()
        logger.debug(f"Apify run input prepared: {run_input}")

        # Execute the scraper
        logger.info("Calling Apify actor...")
        call_result = await actor_client.call(run_input=run_input)

        if call_result is None:
            error_msg = "Apify actor call returned None"
            logger.error(error_msg)
            raise Exception(error_msg)

        logger.info(
            f"Apify actor completed successfully. Dataset ID: {call_result.get('defaultDatasetId')}"
        )

        # Fetch results from the Actor run's default dataset
        dataset_client = apify_client.dataset(call_result["defaultDatasetId"])
        logger.info("Fetching results from Apify dataset...")

        list_items_result = await dataset_client.list_items()

        # Extract items - ListPage may have different access patterns
        # Try different ways to access the items
        items = []
        if hasattr(list_items_result, "items"):
            items = list_items_result.items
        elif isinstance(list_items_result, dict) and "items" in list_items_result:
            items = list_items_result["items"]
        else:
            # Fallback: try to iterate  # type: ignore
            items = [item for item in list_items_result]  # type: ignore

        logger.info(f"Retrieved {len(items)} items from dataset")

        # Convert items to RightmoveProperty objects
        properties = []
        for item in items:
            try:
                # Validate item against RightmoveProperty model
                prop = RightmoveProperty(**item)
                properties.append(prop)
            except Exception as e:
                logger.warning(f"Failed to parse property item: {e}")
                logger.debug(f"Invalid item: {item}")
                continue

        logger.info(f"Successfully parsed {len(properties)} properties")

        # Create and return validated response
        response = RightmoveResponse(properties=properties)
        logger.info(
            f"Scraping completed successfully. Returning {len(response.properties)} properties"
        )

        return response

    except ValueError:
        # Re-raise ValueError (API key not found)
        raise
    except Exception as e:
        error_msg = f"Rightmove scraper failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise Exception(error_msg) from e
