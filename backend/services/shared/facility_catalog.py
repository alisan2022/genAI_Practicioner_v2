from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .route_intelligence import assess_route
from .schemas import FacilityKind, FacilityRecommendation, UrgencyLevel


@dataclass(frozen=True, slots=True)
class FacilityRecord:
    name: str
    kind: FacilityKind
    address: str
    contact: str
    base_wait_minutes: int
    latitude: float
    longitude: float


BOURNEMOUTH_FACILITIES: tuple[FacilityRecord, ...] = (
    FacilityRecord(
        name="Royal Bournemouth Hospital - A&E",
        kind="hospital",
        address="Castle Lane East, Bournemouth, BH7 7DW",
        contact="0300 019 4899",
        base_wait_minutes=95,
        latitude=50.7461,
        longitude=-1.8238,
    ),
    FacilityRecord(
        name="Poole Hospital - A&E",
        kind="hospital",
        address="Longfleet Road, Poole, BH15 2JB",
        contact="0300 019 8499",
        base_wait_minutes=85,
        latitude=50.7164,
        longitude=-1.9622,
    ),
    FacilityRecord(
        name="Bournemouth Urgent Treatment Centre",
        kind="urgent_care",
        address="Castle Lane East, Bournemouth, BH7 7DW",
        contact="0300 019 4899",
        base_wait_minutes=60,
        latitude=50.7461,
        longitude=-1.8238,
    ),
    FacilityRecord(
        name="Westbourne Medical Centre",
        kind="gp",
        address="24 Poole Road, Bournemouth, BH4 9DW",
        contact="01202 767499",
        base_wait_minutes=130,
        latitude=50.7225,
        longitude=-1.9016,
    ),
    FacilityRecord(
        name="Stour Surgery",
        kind="gp",
        address="49 Poole Lane, Bournemouth, BH11 9DY",
        contact="01202 723062",
        base_wait_minutes=145,
        latitude=50.7632,
        longitude=-1.8878,
    ),
    FacilityRecord(
        name="Boots Bournemouth Castlepoint Pharmacy",
        kind="pharmacy",
        address="Castlepoint Shopping Park, Bournemouth, BH8 9UZ",
        contact="01202 521441",
        base_wait_minutes=20,
        latitude=50.7472,
        longitude=-1.8398,
    ),
    FacilityRecord(
        name="Superdrug Pharmacy Bournemouth",
        kind="pharmacy",
        address="The Arcade, Bournemouth, BH1 2AF",
        contact="01202 297737",
        base_wait_minutes=15,
        latitude=50.7202,
        longitude=-1.8793,
    ),
)


def _wait_multiplier(hour: int) -> float:
    if 10 <= hour <= 14:
        return 1.2
    if 17 <= hour <= 20:
        return 1.15
    if 0 <= hour <= 6:
        return 0.82
    return 1.0


def estimate_wait_minutes(record: FacilityRecord, now: datetime | None = None) -> int:
    current = now or datetime.now()
    return round(record.base_wait_minutes * _wait_multiplier(current.hour))


def recommend_facilities(
    urgency: UrgencyLevel,
    *,
    count: int = 3,
    now: datetime | None = None,
    location_latitude: float | None = None,
    location_longitude: float | None = None,
) -> list[FacilityRecommendation]:
    kinds_by_urgency: dict[UrgencyLevel, tuple[FacilityKind, ...]] = {
        "high": ("hospital", "urgent_care"),
        "medium": ("urgent_care", "gp"),
        "low": ("pharmacy", "gp"),
    }
    kind_penalties: dict[UrgencyLevel, dict[FacilityKind, float]] = {
        "high": {"hospital": 0.0, "urgent_care": 9.0, "gp": 20.0, "pharmacy": 28.0},
        "medium": {"urgent_care": 0.0, "gp": 7.0, "hospital": 12.0, "pharmacy": 24.0},
        "low": {"pharmacy": 0.0, "gp": 6.0, "urgent_care": 15.0, "hospital": 20.0},
    }
    wait_weights: dict[UrgencyLevel, float] = {"high": 0.6, "medium": 0.8, "low": 1.0}
    travel_weights: dict[UrgencyLevel, float] = {"high": 1.2, "medium": 0.9, "low": 0.6}
    traffic_penalties = {"heavy": 9.0, "moderate": 4.0, "light": 0.0, "unknown": 2.0}

    shortlisted = [
        item for item in BOURNEMOUTH_FACILITIES if item.kind in kinds_by_urgency[urgency]
    ]
    ranked_entries: list[tuple[float, FacilityRecommendation]] = []

    for item in shortlisted:
        wait_minutes = estimate_wait_minutes(item, now)
        route = None
        burden_score = wait_minutes * wait_weights[urgency] + kind_penalties[urgency][item.kind]

        if location_latitude is not None and location_longitude is not None:
            route = assess_route(
                location_latitude,
                location_longitude,
                item.latitude,
                item.longitude,
            ).as_schema()
            burden_score += route.travel_minutes * travel_weights[urgency]
            burden_score += traffic_penalties[route.traffic_level]

        ranked_entries.append(
            (
                round(burden_score, 2),
                FacilityRecommendation(
                    name=item.name,
                    kind=item.kind,
                    address=item.address,
                    contact=item.contact,
                    latitude=item.latitude,
                    longitude=item.longitude,
                    estimated_wait_minutes=wait_minutes,
                    route=route,
                ),
            )
        )

    ranked_entries.sort(key=lambda item: item[0])
    top_entries = ranked_entries[:count]

    if not top_entries:
        return []

    lowest_score = top_entries[0][0]
    highest_score = top_entries[-1][0]
    spread = max(highest_score - lowest_score, 1.0)

    results: list[FacilityRecommendation] = []
    for score, facility in top_entries:
        facility.suitability_score = round(max(0.3, 1 - ((score - lowest_score) / spread) * 0.45), 2)
        results.append(facility)
    return results


def closest_hospital(
    latitude: float,
    longitude: float,
    *,
    now: datetime | None = None,
) -> tuple[FacilityRecommendation, float]:
    hospitals = [item for item in BOURNEMOUTH_FACILITIES if item.kind == "hospital"]
    winner = hospitals[0]
    winner_distance = assess_route(
        latitude,
        longitude,
        winner.latitude,
        winner.longitude,
    ).distance_km

    for hospital in hospitals[1:]:
        candidate = assess_route(
            latitude,
            longitude,
            hospital.latitude,
            hospital.longitude,
        ).distance_km
        if candidate < winner_distance:
            winner = hospital
            winner_distance = candidate

    recommendation = FacilityRecommendation(
        name=winner.name,
        kind=winner.kind,
        address=winner.address,
        contact=winner.contact,
        latitude=winner.latitude,
        longitude=winner.longitude,
        estimated_wait_minutes=estimate_wait_minutes(winner, now),
        route=assess_route(latitude, longitude, winner.latitude, winner.longitude).as_schema(),
        suitability_score=0.9,
    )
    return recommendation, round(winner_distance, 2)
