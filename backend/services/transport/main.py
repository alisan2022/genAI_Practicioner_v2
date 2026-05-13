from __future__ import annotations

from fastapi import FastAPI

from backend.services.shared.schemas import (
    TransportOption,
    TransportOptionsRequest,
    TransportOptionsResponse,
)

app = FastAPI(title="Transport Service")


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 2)))


def build_transport_options(request: TransportOptionsRequest) -> list[TransportOption]:
    if request.emergency_signs_confirmed:
        return [
            TransportOption(
                mode="ambulance",
                rationale="Emergency warning signs are present, so ambulance support is the safest option.",
                eta_minutes=request.ambulance_delay_minutes,
                suitability_score=1.0,
            ),
            TransportOption(
                mode="ride_hailing",
                rationale="Ride-hailing can be quicker in some cases, but ambulance remains the first choice when emergency signs are confirmed.",
                eta_minutes=10,
                suitability_score=0.25,
            ),
            TransportOption(
                mode="self_travel",
                rationale="Self travel is not appropriate when emergency signs are present.",
                eta_minutes=None,
                suitability_score=0.05,
            ),
        ]

    ambulance_score = 0.25
    ride_score = 0.45
    self_score = 0.5

    if request.urgency == "high":
        ambulance_score = 0.88
        ride_score = 0.52
        self_score = 0.14

    if request.urgency == "medium":
        ambulance_score = 0.28
        ride_score = 0.72
        self_score = 0.58

    if request.urgency == "low":
        ambulance_score = 0.08
        ride_score = 0.4
        self_score = 0.9

    if request.ambulance_delay_minutes is not None and request.urgency == "high":
        if request.ambulance_delay_minutes > 25:
            ambulance_score -= 0.3
            ride_score += 0.3

    if request.mobility_limited:
        ride_score += 0.12
        self_score -= 0.2

    options = [
        TransportOption(
            mode="ambulance",
            rationale="Ambulance becomes stronger when the condition looks severe or could deteriorate quickly.",
            eta_minutes=request.ambulance_delay_minutes,
            suitability_score=_clamp(ambulance_score),
        ),
        TransportOption(
            mode="ride_hailing",
            rationale="Ride-hailing fits urgent but currently stable cases when supported travel is helpful.",
            eta_minutes=10,
            suitability_score=_clamp(ride_score),
        ),
        TransportOption(
            mode="self_travel",
            rationale="Self travel is usually only suitable when symptoms are stable and the person can move safely.",
            eta_minutes=18,
            suitability_score=_clamp(self_score),
        ),
    ]
    return sorted(options, key=lambda item: item.suitability_score, reverse=True)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "transport"}


@app.post("/options", response_model=TransportOptionsResponse)
def options(request: TransportOptionsRequest) -> TransportOptionsResponse:
    return TransportOptionsResponse(options=build_transport_options(request))
