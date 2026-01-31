"""Backend services module - High-level business logic layer

This module provides high-level services for various backend operations,
including routing, distance calculations, isochrone queries, and property verification.
"""

from backend.services.routing_service import (
    RoutingService,
    properties_in_polygon,
)

__all__ = [
    "RoutingService",
    "properties_in_polygon",
]
