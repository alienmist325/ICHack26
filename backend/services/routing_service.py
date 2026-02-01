"""
Routing service for calculating travel times, distances, and isochrones.

Handles communication with external routing APIs (OSRM, Mapbox, etc.)
via the routingpy library. Provides high-level functions for:
- Computing isochrone polygons
- Calculating travel times between locations
- Calculating distances between locations
- Point-in-polygon queries using Shapely
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import routingpy
from shapely.geometry import Point, shape

from backend.config import (
    OSRM_BASE_URL,
    ROUTING_API_KEY,
    ROUTING_PROVIDER,
    ROUTING_TIMEOUT_SECONDS,
    UK_BOUNDS,
)

logger = logging.getLogger(__name__)


# ============================================================================
# RoutingService Class
# ============================================================================


class RoutingService:
    """
    Service for routing operations using routingpy.

    Handles initialization and caching of routing clients,
    and provides methods for isochrone computation, travel time,
    and distance matrix calculations.
    """

    def __init__(self):
        """Initialize the routing service."""
        self._client: Optional[Any] = None
        self._provider = ROUTING_PROVIDER
        logger.info(f"Initialized RoutingService with provider: {self._provider}")

    def _get_client(self) -> Any:
        """
        Get or create routing client instance.

        Handles provider-specific client initialization.
        """
        if self._client is not None:
            return self._client

        logger.debug(f"Creating routing client for provider: {self._provider}")

        if self._provider.lower() == "osrm":
            self._client = routingpy.OSRM(
                base_url=OSRM_BASE_URL,
                timeout=ROUTING_TIMEOUT_SECONDS,
            )
        elif self._provider.lower() == "mapbox":
            if ROUTING_API_KEY is None:
                raise ValueError("ROUTING_API_KEY required when using Mapbox provider")
            self._client = routingpy.MapboxOSRM(
                api_key=str(ROUTING_API_KEY),
                timeout=ROUTING_TIMEOUT_SECONDS,
            )
        elif self._provider.lower() == "mapbox":
            if ROUTING_API_KEY is None:
                raise ValueError("ROUTING_API_KEY required when using Mapbox provider")
            self._client = routingpy.MapboxOSRM(
                api_key=ROUTING_API_KEY,
                timeout=ROUTING_TIMEOUT_SECONDS,
            )
        else:
            raise ValueError(
                f"Unsupported routing provider: {self._provider}. "
                "Supported providers: osrm, mapbox"
            )

        return self._client

    @staticmethod
    def _validate_coordinates(lat: float, lon: float) -> None:
        """
        Validate that coordinates are within UK bounds.

        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate

        Raises:
            ValueError: If coordinates are outside UK bounds
        """
        if not (UK_BOUNDS["south"] <= lat <= UK_BOUNDS["north"]):
            raise ValueError(
                f"Latitude {lat} outside UK bounds "
                f"({UK_BOUNDS['south']}, {UK_BOUNDS['north']})"
            )

        if not (UK_BOUNDS["west"] <= lon <= UK_BOUNDS["east"]):
            raise ValueError(
                f"Longitude {lon} outside UK bounds "
                f"({UK_BOUNDS['west']}, {UK_BOUNDS['east']})"
            )

    @staticmethod
    def _validate_duration(duration_seconds: int) -> None:
        """
        Validate isochrone duration.

        Args:
            duration_seconds: Duration in seconds

        Raises:
            ValueError: If duration is outside acceptable range
        """
        if duration_seconds < 60:
            raise ValueError("Duration must be at least 60 seconds (1 minute)")
        if duration_seconds > 3600:
            raise ValueError("Duration must be at most 3600 seconds (60 minutes)")

    def compute_isochrone(
        self, lat: float, lon: float, duration_seconds: int
    ) -> Optional[Dict[str, Any]]:
        """
        Compute an isochrone polygon for a given location and duration.

        An isochrone is a polygon showing all areas reachable within a
        specified time duration from a given point.

        Args:
            lat: Latitude of center point
            lon: Longitude of center point
            duration_seconds: Time limit in seconds

        Returns:
            GeoJSON-formatted isochrone polygon, or None if computation fails

        Raises:
            ValueError: If coordinates or duration are invalid
        """
        # Validate inputs
        self._validate_coordinates(lat, lon)
        self._validate_duration(duration_seconds)

        try:
            client = self._get_client()
            logger.info(
                f"Computing isochrone for ({lat}, {lon}) with duration {duration_seconds}s"
            )

            # Call routing API - note routingpy uses (lon, lat) order
            isochrone = client.isochrone(
                locations=[[lon, lat]],
                intervals=[duration_seconds],
                timeout=ROUTING_TIMEOUT_SECONDS,
            )

            logger.debug(f"Isochrone computed successfully: {type(isochrone)}")
            return isochrone

        except Exception as e:
            logger.error(
                f"Failed to compute isochrone for ({lat}, {lon}): {str(e)}",
                exc_info=True,
            )
            raise

    def get_travel_times_matrix(
        self,
        origin: Tuple[float, float],
        destinations: List[Tuple[float, float]],
    ) -> List[Dict[str, Any]]:
        """
        Calculate travel times from an origin to multiple destinations.

        Args:
            origin: (lat, lon) tuple for origin
            destinations: List of (lat, lon) tuples for destinations

        Returns:
            List of dicts with travel_time_seconds and destination coordinates

        Raises:
            ValueError: If coordinates are invalid or too many destinations
            Exception: If routing API call fails
        """
        # Validate origin
        self._validate_coordinates(origin[0], origin[1])

        # Validate destinations
        if len(destinations) > 25:
            raise ValueError("Maximum 25 destinations allowed per request")

        for lat, lon in destinations:
            self._validate_coordinates(lat, lon)

        try:
            client = self._get_client()
            logger.info(
                f"Computing travel times from {origin} to {len(destinations)} destinations"
            )

            # Convert to routingpy format (lon, lat)
            origin_lonlat = [origin[1], origin[0]]
            destinations_lonlat = [[lon, lat] for lat, lon in destinations]

            # Call routing API for distance matrix
            # Returns travel times in seconds
            matrix = client.matrix(
                locations=[origin_lonlat] + destinations_lonlat,
                profile="car",
                timeout=ROUTING_TIMEOUT_SECONDS,
            )

            # Extract travel times from first row (from origin to each destination)
            results = []
            if matrix and hasattr(matrix, "durations") and matrix.durations:
                # First row contains times from origin to all destinations
                travel_times = matrix.durations[0][
                    1:
                ]  # Skip first element (origin to self)

                for (dest_lat, dest_lon), travel_time in zip(
                    destinations, travel_times
                ):
                    results.append(
                        {
                            "destination_lat": dest_lat,
                            "destination_lon": dest_lon,
                            "travel_time_seconds": int(travel_time)
                            if travel_time
                            else 0,
                        }
                    )

            logger.debug(f"Travel times computed: {len(results)} results")
            return results

        except Exception as e:
            logger.error(
                f"Failed to compute travel times from {origin}: {str(e)}",
                exc_info=True,
            )
            raise

    def get_distances_matrix(
        self,
        origin: Tuple[float, float],
        destinations: List[Tuple[float, float]],
    ) -> List[Dict[str, Any]]:
        """
        Calculate distances from an origin to multiple destinations.

        Args:
            origin: (lat, lon) tuple for origin
            destinations: List of (lat, lon) tuples for destinations

        Returns:
            List of dicts with distance_meters and destination coordinates

        Raises:
            ValueError: If coordinates are invalid or too many destinations
            Exception: If routing API call fails
        """
        # Validate origin
        self._validate_coordinates(origin[0], origin[1])

        # Validate destinations
        if len(destinations) > 25:
            raise ValueError("Maximum 25 destinations allowed per request")

        for lat, lon in destinations:
            self._validate_coordinates(lat, lon)

        try:
            client = self._get_client()
            logger.info(
                f"Computing distances from {origin} to {len(destinations)} destinations"
            )

            # Convert to routingpy format (lon, lat)
            origin_lonlat = [origin[1], origin[0]]
            destinations_lonlat = [[lon, lat] for lat, lon in destinations]

            # Call routing API for distance matrix
            # Returns distances in meters
            matrix = client.matrix(
                locations=[origin_lonlat] + destinations_lonlat,
                profile="car",
                timeout=ROUTING_TIMEOUT_SECONDS,
            )

            # Extract distances from first row (from origin to each destination)
            results = []
            if matrix and hasattr(matrix, "distances") and matrix.distances:
                # First row contains distances from origin to all destinations
                distances = matrix.distances[0][
                    1:
                ]  # Skip first element (origin to self)

                for (dest_lat, dest_lon), distance in zip(destinations, distances):
                    results.append(
                        {
                            "destination_lat": dest_lat,
                            "destination_lon": dest_lon,
                            "distance_meters": int(distance) if distance else 0,
                        }
                    )

            logger.debug(f"Distances computed: {len(results)} results")
            return results

        except Exception as e:
            logger.error(
                f"Failed to compute distances from {origin}: {str(e)}",
                exc_info=True,
            )
            raise


# ============================================================================
# Utility Functions
# ============================================================================


def properties_in_polygon(
    polygon: Dict[str, Any], properties: List[Dict[str, Any]]
) -> List[int]:
    """
    Find property IDs that fall within a polygon using point-in-polygon query.

    Args:
        polygon: GeoJSON polygon geometry
        properties: List of property dicts with 'id', 'latitude', 'longitude' keys

    Returns:
        List of property IDs inside the polygon
    """
    try:
        # Convert GeoJSON to Shapely polygon
        if isinstance(polygon, dict):
            if "features" in polygon:
                # FeatureCollection - take first feature's geometry
                polygon = polygon["features"][0]["geometry"]
            elif "geometry" in polygon:
                # Feature - extract geometry
                polygon = polygon["geometry"]

        shapely_polygon = shape(polygon)
        logger.debug(f"Created Shapely polygon: {type(shapely_polygon)}")

        property_ids = []
        for prop in properties:
            if "latitude" not in prop or "longitude" not in prop:
                logger.warning(f"Property {prop.get('id')} missing coordinates")
                continue

            point = Point(prop["longitude"], prop["latitude"])
            if shapely_polygon.contains(point):
                property_ids.append(prop["id"])

        logger.info(
            f"Found {len(property_ids)} properties inside polygon "
            f"(checked {len(properties)} total)"
        )
        return property_ids

    except Exception as e:
        logger.error(
            f"Failed to perform point-in-polygon query: {str(e)}", exc_info=True
        )
        raise


# ============================================================================
# Module-level Singleton & Convenience Functions
# ============================================================================

_service: Optional[RoutingService] = None


def get_routing_service() -> RoutingService:
    """
    Get or create the singleton routing service instance.

    Returns:
        RoutingService instance
    """
    global _service
    if _service is None:
        _service = RoutingService()
    return _service


def compute_isochrone(
    lat: float, lon: float, duration_seconds: int
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to compute an isochrone using the singleton service.

    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        duration_seconds: Time limit in seconds

    Returns:
        GeoJSON-formatted isochrone polygon, or None if computation fails
    """
    service = get_routing_service()
    return service.compute_isochrone(lat, lon, duration_seconds)


def get_travel_times(
    origin: Tuple[float, float],
    destinations: List[Tuple[float, float]],
) -> List[Dict[str, Any]]:
    """
    Convenience function to compute travel times using the singleton service.

    Args:
        origin: (lat, lon) tuple for origin
        destinations: List of (lat, lon) tuples for destinations

    Returns:
        List of dicts with travel times and destination coordinates
    """
    service = get_routing_service()
    return service.get_travel_times_matrix(origin, destinations)


def get_distances(
    origin: Tuple[float, float],
    destinations: List[Tuple[float, float]],
) -> List[Dict[str, Any]]:
    """
    Convenience function to compute distances using the singleton service.

    Args:
        origin: (lat, lon) tuple for origin
        destinations: List of (lat, lon) tuples for destinations

    Returns:
        List of dicts with distances and destination coordinates
    """
    service = get_routing_service()
    return service.get_distances_matrix(origin, destinations)
