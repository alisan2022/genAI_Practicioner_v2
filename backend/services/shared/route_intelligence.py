from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt

import httpx

from .schemas import RouteMetrics, TrafficLevel

OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"


@dataclass(frozen=True, slots=True)
class RouteAssessment:
    distance_km: float
    travel_minutes: int
    average_speed_kmh: float
    traffic_level: TrafficLevel
    source: str

    def as_schema(self) -> RouteMetrics:
        return RouteMetrics(
            distance_km=round(self.distance_km, 1),
            travel_minutes=self.travel_minutes,
            average_speed_kmh=round(self.average_speed_kmh, 1),
            traffic_level=self.traffic_level,
            source=self.source,  # type: ignore[arg-type]
        )


def _distance_km(
    from_latitude: float,
    from_longitude: float,
    to_latitude: float,
    to_longitude: float,
) -> float:
    earth_radius_km = 6371.0
    d_lat = radians(to_latitude - from_latitude)
    d_lon = radians(to_longitude - from_longitude)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(from_latitude))
        * cos(radians(to_latitude))
        * sin(d_lon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius_km * c


def _traffic_level(average_speed_kmh: float) -> TrafficLevel:
    if average_speed_kmh <= 18:
        return "heavy"
    if average_speed_kmh <= 32:
        return "moderate"
    return "light"


def _heuristic_route(
    from_latitude: float,
    from_longitude: float,
    to_latitude: float,
    to_longitude: float,
) -> RouteAssessment:
    distance_km = _distance_km(from_latitude, from_longitude, to_latitude, to_longitude)

    # Urban Dorset driving fallback tuned for prototype use when live routing is unavailable.
    average_speed_kmh = 28.0 if distance_km >= 4 else 22.0
    travel_minutes = max(4, round((distance_km / max(average_speed_kmh, 1)) * 60 + 3))

    return RouteAssessment(
        distance_km=distance_km,
        travel_minutes=travel_minutes,
        average_speed_kmh=average_speed_kmh,
        traffic_level=_traffic_level(average_speed_kmh),
        source="distance_heuristic",
    )


def assess_route(
    from_latitude: float,
    from_longitude: float,
    to_latitude: float,
    to_longitude: float,
) -> RouteAssessment:
    url = (
        f"{OSRM_ROUTE_URL}/{from_longitude},{from_latitude};{to_longitude},{to_latitude}"
        "?overview=false&alternatives=false&steps=false"
    )

    try:
        response = httpx.get(url, timeout=4.0)
        response.raise_for_status()
        payload = response.json()
        routes = payload.get("routes")
        if isinstance(routes, list) and routes:
            first = routes[0]
            distance_m = float(first.get("distance", 0.0))
            duration_s = float(first.get("duration", 0.0))
            if distance_m > 0 and duration_s > 0:
                distance_km = distance_m / 1000
                travel_minutes = max(1, round(duration_s / 60))
                average_speed_kmh = distance_km / max(duration_s / 3600, 1e-6)
                return RouteAssessment(
                    distance_km=distance_km,
                    travel_minutes=travel_minutes,
                    average_speed_kmh=average_speed_kmh,
                    traffic_level=_traffic_level(average_speed_kmh),
                    source="road_network",
                )
    except Exception:
        pass

    return _heuristic_route(from_latitude, from_longitude, to_latitude, to_longitude)
