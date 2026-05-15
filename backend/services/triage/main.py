from __future__ import annotations

from typing import Any

import httpx
from fastapi import FastAPI

from backend.services.shared.config import (
    DEFAULT_DISCLAIMER,
    FACILITY_SERVICE_URL,
    KNOWLEDGE_SERVICE_URL,
    TRANSPORT_SERVICE_URL,
)
from backend.services.shared.facility_catalog import recommend_facilities
from backend.services.shared.knowledge_base import retrieve_documents
from backend.services.shared.medical_llm import llm_status, maybe_refine_triage
from backend.services.shared.schemas import (
    AITriageRequest,
    AITriageResponse,
    FacilityRecommendation,
    FacilityRecommendationResponse,
    KnowledgeCard,
    KnowledgeRetrieveResponse,
    TransportOption,
    TransportOptionsRequest,
    TransportOptionsResponse,
    TransportRecommendation,
)
from backend.services.shared.triage_logic import assess_request
from backend.services.transport.main import build_transport_options

app = FastAPI(title="Triage Service")


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(url, json=payload, timeout=12.0)
    response.raise_for_status()
    parsed = response.json()
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid response from {url}")
    return parsed


def _load_knowledge(query: str, urgency: str) -> tuple[list[KnowledgeCard], str]:
    payload = {"query": query, "urgency": urgency, "top_k": 4}
    try:
        parsed = _post_json(f"{KNOWLEDGE_SERVICE_URL}/retrieve", payload)
        response = KnowledgeRetrieveResponse.model_validate(parsed)
        return response.cards, "Loaded knowledge cards from knowledge service."
    except Exception:
        return retrieve_documents(query, urgency=urgency, top_k=4), "Used local RAG fallback."


def _load_facilities(request: AITriageRequest, urgency: str) -> tuple[list[FacilityRecommendation], str]:
    payload = {
        "urgency": urgency,
        "count": 3,
        "location_latitude": request.location_latitude,
        "location_longitude": request.location_longitude,
    }
    try:
        parsed = _post_json(f"{FACILITY_SERVICE_URL}/recommendations", payload)
        response = FacilityRecommendationResponse.model_validate(parsed)
        return response.facilities, "Loaded facility options from facility service."
    except Exception:
        return (
            recommend_facilities(
                urgency,
                location_latitude=request.location_latitude,
                location_longitude=request.location_longitude,
            ),
            "Used local facility fallback.",
        )


def _top_transport_option(request: AITriageRequest, urgency: str) -> tuple[TransportRecommendation, str]:
    payload = TransportOptionsRequest(
        urgency=urgency,
        emergency_signs_confirmed=request.emergency_signs_confirmed,
        ambulance_delay_minutes=request.ambulance_delay_minutes,
        mobility_limited=request.mobility_limited,
    )

    options: list[TransportOption]
    note: str
    try:
        parsed = _post_json(f"{TRANSPORT_SERVICE_URL}/options", payload.model_dump())
        response = TransportOptionsResponse.model_validate(parsed)
        options = response.options
        note = "Loaded transport options from transport service."
    except Exception:
        options = build_transport_options(payload)
        note = "Used local transport fallback."

    selected = options[0]
    return (
        TransportRecommendation(
            mode=selected.mode,
            rationale=selected.rationale,
            eta_minutes=selected.eta_minutes,
            confidence=selected.suitability_score,
        ),
        note,
    )


@app.get("/health")
def health() -> dict[str, Any]:
    status = llm_status()
    return {
        "status": "ok",
        "service": "triage",
        "llm_enabled": status["enabled"],
        "model": status["model"],
    }


@app.post("/ai-triage", response_model=AITriageResponse)
def ai_triage(request: AITriageRequest) -> AITriageResponse:
    assessment = assess_request(request)
    knowledge_cards, knowledge_note = _load_knowledge(assessment.search_query, assessment.urgency)
    facilities, facility_note = _load_facilities(request, assessment.urgency)
    transport, transport_note = _top_transport_option(request, assessment.urgency)

    if facilities and facilities[0].route and transport.mode in {"ride_hailing", "self_travel"}:
        transport.eta_minutes = facilities[0].route.travel_minutes

    response = AITriageResponse(
        urgency=assessment.urgency,
        summary=assessment.summary,
        reasoning=assessment.reasoning,
        recommended_actions=assessment.recommended_actions,
        self_care_advice=assessment.self_care_advice,
        otc_options=assessment.otc_options,
        facilities=facilities,
        transport=transport,
        knowledge_cards=knowledge_cards,
        safety_disclaimer=DEFAULT_DISCLAIMER,
        model="rules+rag",
        decision_trace=[
            *assessment.decision_trace,
            knowledge_note,
            facility_note,
            transport_note,
        ],
    )
    return maybe_refine_triage(response)
