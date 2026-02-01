"""
Rightmove Scraper CLI - Command-line interface for scraping Rightmove properties.

This module provides a Click-based CLI for scraping Rightmove properties and storing
them in the database. It's independent of the FastAPI backend and can be run as a
standalone script.

Usage:
    rightmove-scraper --help
    rightmove-scraper --list-url "https://www.rightmove.co.uk/..." --max-properties 100
    rightmove-scraper --list-url "url1" --list-url "url2" --property-url "url3"
"""

import logging
import sys
from typing import List, Optional, Tuple

import click

from backend.cli.scraper import run_scraper
from backend.config import settings
from backend.models.rightmove import (
    ListUrl,
    ProxyConfig,
    PropertyUrl,
    RightmoveScraperInput,
)

# Configure logging for CLI output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--list-url",
    "list_urls",
    multiple=True,
    help="Rightmove list page URL to scrape (e.g., search results page). Can be used multiple times.",
)
@click.option(
    "--property-url",
    "property_urls",
    multiple=True,
    help="Specific property URL to scrape. Can be used multiple times.",
)
@click.option(
    "--max-properties",
    type=int,
    default=1000,
    help="Maximum number of properties to fetch (default: 1000).",
)
@click.option(
    "--full-details",
    is_flag=True,
    default=False,
    help="Fetch full property details instead of basic info.",
)
@click.option(
    "--include-price-history",
    is_flag=True,
    default=False,
    help="Include historical price data for properties.",
)
@click.option(
    "--include-nearest-schools",
    is_flag=True,
    default=False,
    help="Include information about nearest schools.",
)
@click.option(
    "--monitoring-mode",
    is_flag=True,
    default=False,
    help="Enable monitoring mode for continuous updates.",
)
@click.option(
    "--deduplicate-at-task-level",
    is_flag=True,
    default=False,
    help="Deduplicate results at task level.",
)
@click.option(
    "--enable-delisting-tracker",
    is_flag=True,
    default=False,
    help="Enable tracking of delisted properties.",
)
@click.option(
    "--add-empty-tracker-record",
    is_flag=True,
    default=False,
    help="Add empty tracker record in results.",
)
@click.option(
    "--email",
    default="",
    help="Email address for notifications (optional).",
)
@click.option(
    "--proxy-url",
    default=None,
    help="Proxy URL (overrides .env PROXY_URL if set).",
)
@click.option(
    "--proxy-username",
    default=None,
    help="Proxy username (overrides .env PROXY_USERNAME if set).",
)
@click.option(
    "--proxy-password",
    default=None,
    help="Proxy password (overrides .env PROXY_PASSWORD if set).",
)
@click.option(
    "--proxy-country",
    default=None,
    help="Proxy country (overrides .env PROXY_COUNTRY if set).",
)
def main(
    list_urls: Tuple[str, ...],
    property_urls: Tuple[str, ...],
    max_properties: int,
    full_details: bool,
    include_price_history: bool,
    include_nearest_schools: bool,
    monitoring_mode: bool,
    deduplicate_at_task_level: bool,
    enable_delisting_tracker: bool,
    add_empty_tracker_record: bool,
    email: str,
    proxy_url: Optional[str],
    proxy_username: Optional[str],
    proxy_password: Optional[str],
    proxy_country: Optional[str],
) -> None:
    """
    Scrape Rightmove properties and store them in the database.

    Requires at least one of --list-url or --property-url to be specified.
    The Apify API key must be set via APIFY_API_KEY environment variable (.env file).

    Example usage:
        rightmove-scraper --list-url "https://www.rightmove.co.uk/..." --max-properties 100
        rightmove-scraper --list-url "url1" --list-url "url2" --full-details
        rightmove-scraper --property-url "https://www.rightmove.co.uk/properties/..."
    """
    try:
        # Validate that at least one URL is provided
        if not list_urls and not property_urls:
            click.echo(
                click.style(
                    "Error: At least one of --list-url or --property-url must be provided.",
                    fg="red",
                    bold=True,
                ),
                err=True,
            )
            sys.exit(1)

        # Build proxy configuration (combine .env and CLI overrides)
        proxy_config = ProxyConfig(
            url=proxy_url or settings.proxy_url or "",
            username=proxy_username or settings.proxy_username or "",
            password=proxy_password or settings.proxy_password or "",
            country=proxy_country or settings.proxy_country or "",
        )

        # Convert URL strings to model objects
        list_url_objects = [ListUrl(url=url) for url in list_urls]
        property_url_objects = [PropertyUrl(url=url) for url in property_urls]

        # Create scraper configuration
        config = RightmoveScraperInput(
            listUrls=list_url_objects,
            propertyUrls=property_url_objects,
            maxProperties=max_properties,
            fullPropertyDetails=full_details,
            includePriceHistory=include_price_history,
            includeNearestSchools=include_nearest_schools,
            monitoringMode=monitoring_mode,
            deduplicateAtTaskLevel=deduplicate_at_task_level,
            enableDelistingTracker=enable_delisting_tracker,
            addEmptyTrackerRecord=add_empty_tracker_record,
            email=email,
            proxy=proxy_config,
        )

        logger.info("=" * 70)
        logger.info("Rightmove Scraper CLI - Starting scrape job")
        logger.info("=" * 70)

        # Run the scraper
        stats = run_scraper(config)

        # Print summary
        logger.info("=" * 70)
        click.echo("")
        click.echo(
            click.style("✓ Scraping completed successfully!", fg="green", bold=True)
        )
        click.echo(click.style("  Summary:", fg="cyan", bold=True))
        click.echo(f"    Total properties scraped: {stats['total']}")
        click.echo(f"    Created: {stats['created']}")
        click.echo(f"    Updated: {stats['updated']}")
        if stats["failed"] > 0:
            click.echo(click.style(f"    Failed: {stats['failed']}", fg="yellow"))
        else:
            click.echo(f"    Failed: {stats['failed']}")
        click.echo("")

        sys.exit(0)

    except ValueError as e:
        click.echo(
            click.style(f"Configuration Error: {str(e)}", fg="red", bold=True),
            err=True,
        )
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style(f"Error: {str(e)}", fg="red", bold=True),
            err=True,
        )
        logger.exception("Scraping failed with exception:")
        sys.exit(2)


if __name__ == "__main__":
    main()
