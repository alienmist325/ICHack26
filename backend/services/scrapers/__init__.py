"""
Scrapers module - Property scraping services

Provides various scrapers for collecting property data from different sources.
Currently includes Rightmove scraper via Apify API.
"""

from backend.services.scrapers.rightmove import scrape_rightmove

__all__ = ["scrape_rightmove"]
