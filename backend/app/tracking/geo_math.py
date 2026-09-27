"""
Geodesic Mathematics & Spatial Metric Utilities for Event Tracking
"""

import math
from typing import Tuple, List, Optional
import numpy as np


def wrap_longitude(lon: float) -> float:
    """Normalizes longitude into standard international convention [-180.0, 180.0] degrees."""
    w = ((lon + 180.0) % 360.0) - 180.0
    if w == -180.0 and lon > 0:
        return 180.0
    return w


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes Great-Circle distance in kilometers between two geographic coordinates
    using the spherical Haversine formula. Correctly handles longitude wrapping.
    """
    earth_radius_km = 6371.0088

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)

    # Normalize delta lambda across anti-meridian
    d_lon = wrap_longitude(lon2 - lon1)
    delta_lambda = math.radians(d_lon)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return float(earth_radius_km * c)


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, str]:
    """
    Calculates initial forward azimuth (bearing) in degrees [0, 360) and 16-point cardinal compass direction
    from point 1 to point 2 along a Great Circle.
    """
    if abs(lat1 - lat2) < 1e-6 and abs(wrap_longitude(lon2 - lon1)) < 1e-6:
        return 0.0, "STATIONARY"

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_lon = wrap_longitude(lon2 - lon1)
    delta_lambda = math.radians(d_lon)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing_deg = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0

    cardinals = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    index = int((bearing_deg + 11.25) / 22.5) % 16
    return round(bearing_deg, 1), cardinals[index]


def calculate_speed_kmh(distance_km: float, delta_hours: float) -> float:
    """Calculates translation speed in km/h given distance and elapsed hours."""
    if delta_hours <= 0:
        return 0.0
    return round(distance_km / delta_hours, 1)


def calculate_area_change(
    prev_area_km2: Optional[float], curr_area_km2: Optional[float]
) -> Tuple[Optional[float], Optional[float]]:
    """Calculates absolute (km²) and percentage change in footprint area."""
    if prev_area_km2 is None or curr_area_km2 is None or prev_area_km2 <= 0:
        return None, None
    delta_area = round(curr_area_km2 - prev_area_km2, 1)
    pct_change = round((delta_area / prev_area_km2) * 100.0, 1)
    return delta_area, pct_change


def calculate_centroid_dispersion_km(centroids: List[List[float]]) -> float:
    """
    Given a list of [lat, lon] coordinates, computes the mean distance of all centroids
    from the spatial mean centroid (dispersion metric in km).
    """
    if not centroids or len(centroids) < 2:
        return 0.0

    mean_lat = float(np.mean([c[0] for c in centroids]))
    mean_lon = float(np.mean([c[1] for c in centroids]))

    distances = [
        haversine_distance_km(mean_lat, mean_lon, c[0], c[1])
        for c in centroids
    ]
    return round(float(np.mean(distances)), 1)
