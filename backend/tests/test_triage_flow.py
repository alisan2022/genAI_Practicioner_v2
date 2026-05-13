from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.chat.main import _fallback_chat_reply
from backend.services.shared import facility_catalog
from backend.services.shared.route_intelligence import RouteAssessment
from backend.services.shared.knowledge_base import retrieve_documents
from backend.services.shared.schemas import AITriageRequest, ChatRequest, TransportOptionsRequest
from backend.services.shared.triage_logic import assess_request
from backend.services.transport.main import build_transport_options


def test_low_urgency_cold_returns_self_care() -> None:
    assessment = assess_request(
        AITriageRequest(
            symptoms="Mild cold, blocked nose, and light headache since this morning",
            age=28,
            pain_level=2,
        )
    )

    assert assessment.urgency == "low"
    assert assessment.self_care_advice
    assert "Paracetamol" in assessment.otc_options


def test_high_urgency_chest_pain_is_escalated() -> None:
    assessment = assess_request(
        AITriageRequest(
            symptoms="Sudden chest pain and shortness of breath",
            age=57,
            pain_level=9,
        )
    )

    assert assessment.urgency == "high"
    assert any("999" in action for action in assessment.recommended_actions)


def test_knowledge_retrieval_surfaces_bournemouth_services() -> None:
    cards = retrieve_documents("medium fever urgent same day bournemouth", urgency="medium")

    assert cards
    assert any("Bournemouth" in card.title or "NHS 111" in card.title for card in cards)


def test_transport_prefers_ride_hailing_when_high_delay() -> None:
    options = build_transport_options(
        TransportOptionsRequest(
            urgency="high",
            emergency_signs_confirmed=False,
            ambulance_delay_minutes=45,
            mobility_limited=False,
        )
    )

    assert options[0].mode == "ride_hailing"


def test_location_aware_facility_ranking_exposes_route_metrics(monkeypatch) -> None:
    def fake_assess_route(
        from_latitude: float,
        from_longitude: float,
        to_latitude: float,
        to_longitude: float,
    ) -> RouteAssessment:
        if to_longitude > -1.85:
            return RouteAssessment(
                distance_km=4.0,
                travel_minutes=8,
                average_speed_kmh=30.0,
                traffic_level="moderate",
                source="road_network",
            )
        return RouteAssessment(
            distance_km=7.5,
            travel_minutes=19,
            average_speed_kmh=23.5,
            traffic_level="heavy",
            source="road_network",
        )

    monkeypatch.setattr(facility_catalog, "assess_route", fake_assess_route)

    facilities = facility_catalog.recommend_facilities(
        "medium",
        location_latitude=50.72,
        location_longitude=-1.88,
    )

    assert facilities
    assert facilities[0].route is not None
    assert facilities[0].route.travel_minutes == 8
    assert facilities[0].suitability_score >= facilities[-1].suitability_score


def test_chat_fallback_escalates_urgent_question() -> None:
    reply = _fallback_chat_reply(
        ChatRequest(
            message="Should I go tonight if breathing gets worse?",
            triage_summary="MEDIUM: Fever and sore throat",
        )
    )

    assert "same day" in reply.reply.lower() or "urgent" in reply.reply.lower()
