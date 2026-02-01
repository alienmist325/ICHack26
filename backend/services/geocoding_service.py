"""
Geocoding service for converting addresses to coordinates.

Handles geocoding via Geopy with multiple provider support.
Provides functions for:
- Geocoding addresses to latitude/longitude coordinates
- Handling various address formats (street addresses, postcodes, place names)
- Error handling for ambiguous or not-found addresses
"""

import logging
from typing import Optional, Tuple

from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)


class GeocodingService:
    """
    Service for geocoding operations using Geopy.

    Uses OpenStreetMap's Nominatim service for free, open-source geocoding.
    Supports multiple address formats and is suitable for development/production use.
    """

    def __init__(self):
        """
        Initialize the geocoding service.

        Creates a Nominatim geocoder with a descriptive user agent.
        """
        # Initialize Nominatim geocoder with a descriptive user agent
        # This is required by Nominatim's terms of service
        self._geocoder = Nominatim(user_agent="property-rental-finder/1.0")
        logger.info("Initialized GeocodingService with Nominatim provider")

    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode an address string to latitude/longitude coordinates.

        Accepts any address format:
        - Street addresses: "123 Main Street, London, UK"
        - Postcodes: "SW1A 1AA"
        - Place names: "Tower Bridge, London"
        - Partial addresses: "Oxford Street, London"

        Uses a lenient approach: returns the top/best match even if confidence
        is lower, rather than failing for ambiguous addresses.

        Args:
            address: Address string in any format

        Returns:
            Tuple of (latitude, longitude) if geocoding succeeds, None otherwise

        Raises:
            ValueError: If address is empty or invalid
            Exception: If geocoding service fails
        """
        # Validate input
        if not address or not isinstance(address, str):
            raise ValueError("Address must be a non-empty string")

        address = address.strip()
        if not address:
            raise ValueError("Address cannot be empty or whitespace-only")

        try:
            logger.info(f"Geocoding address: '{address}'")

            # Call Nominatim geocoder
            location = self._geocoder.geocode(address, timeout=10)

            if location is not None:
                lat = location.latitude
                lon = location.longitude

                logger.info(
                    f"Geocoded '{address}' to ({lat}, {lon}) "
                    f"(full address: {location.address})"
                )
                return (lat, lon)

            logger.warning(f"No geocoding results found for address: '{address}'")
            return None

        except Exception as e:
            logger.error(
                f"Failed to geocode address '{address}': {str(e)}", exc_info=True
            )
            raise
