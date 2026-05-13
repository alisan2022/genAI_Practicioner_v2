from __future__ import annotations

from fastapi import FastAPI, Query

from backend.services.shared.facility_catalog import closest_hospital, recommend_facilities
from backend.services.shared.schemas import (
    ClosestHospitalResponse,
    FacilityRecommendationRequest,
    FacilityRecommendationResponse,
)

app = FastAPI(title="Facility Service")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "facility"}


@app.post("/recommendations", response_model=FacilityRecommendationResponse)
def recommendations(request: FacilityRecommendationRequest) -> FacilityRecommendationResponse:
    return FacilityRecommendationResponse(
        urgency=request.urgency,
        facilities=recommend_facilities(
            request.urgency,
            count=request.count,
            location_latitude=request.location_latitude,
            location_longitude=request.location_longitude,
        ),
    )


@app.get("/closest-hospital", response_model=ClosestHospitalResponse)
def nearest_hospital(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
) -> ClosestHospitalResponse:
    facility, distance_km = closest_hospital(latitude, longitude)
    return ClosestHospitalResponse(hospital=facility, distance_km=distance_km)
