from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.chat.main import _fallback_chat_reply
from backend.services.shared.medical_llm import LLMRunResult
from backend.services.shared import facility_catalog
from backend.services.shared.route_intelligence import RouteAssessment
from backend.services.shared.knowledge_base import retrieve_documents
from backend.services.shared.schemas import AITriageRequest, ChatRequest, TransportOptionsRequest
from backend.services.shared.triage_logic import (
    BasicAssessment,
    apply_safety_constraints,
    assess_safety_constraints,
)
from backend.services.triage import main as triage_main
from backend.services.transport.main import build_transport_options


def test_red_flag_guardrail_requires_high_urgency() -> None:
    safety = assess_safety_constraints(
        AITriageRequest(
            symptoms="Sudden chest pain and shortness of breath",
            age=57,
            pain_level=9,
        )
    )

    assert safety.minimum_urgency == "high"
    assert safety.red_flags


def test_guardrail_raises_unsafe_llm_under_escalation() -> None:
    safety = assess_safety_constraints(
        AITriageRequest(symptoms="Sudden chest pain and shortness of breath")
    )
    unsafe_llm_output = BasicAssessment(
        urgency="low",
        summary="The model incorrectly treated the request as minor.",
        reasoning=["Model said this sounded suitable for pharmacy."],
        recommended_actions=["Rest and monitor symptoms."],
        self_care_advice=["Drink fluids."],
        otc_options=["Paracetamol"],
        search_query="chest pain shortness of breath",
        decision_trace=["Generated clinical triage with medical LLM."],
    )

    assessment = apply_safety_constraints(unsafe_llm_output, safety)

    assert assessment.urgency == "high"
    assert any("999" in action for action in assessment.recommended_actions)
    assert assessment.self_care_advice == []
    assert assessment.otc_options == []


def test_ai_triage_uses_llm_for_core_urgency(monkeypatch) -> None:
    def fake_generate_triage_assessment(*args, **kwargs) -> LLMRunResult:
        return LLMRunResult(
            assessment=BasicAssessment(
                urgency="low",
                summary="Low urgency LLM assessment for mild cold symptoms.",
                reasoning=["The LLM judged this as a mild upper respiratory symptom pattern."],
                recommended_actions=["Use community pharmacy advice if symptoms bother you."],
                self_care_advice=["Rest and hydrate over the next 24 to 48 hours."],
                otc_options=["Paracetamol"],
                search_query="mild cold pharmacy self care Bournemouth",
                decision_trace=["Generated clinical triage with medical LLM."],
            ),
            note="Generated clinical triage with medical LLM.",
            model="m42-health/Llama3-Med42-8B",
        )

    monkeypatch.setattr(triage_main, "generate_triage_assessment", fake_generate_triage_assessment)

    response = triage_main.ai_triage(
        AITriageRequest(
            symptoms="Mild cold, blocked nose, and light headache since this morning",
            age=28,
            pain_level=2,
        )
    )

    assert response.urgency == "low"
    assert response.model == "m42-health/Llama3-Med42-8B"
    assert any("medical LLM" in step for step in response.decision_trace)


def test_knowledge_retrieval_surfaces_bournemouth_services() -> None:
    cards = retrieve_documents("medium fever urgent same day bournemouth", urgency="medium")

    assert cards
    assert any("Bournemouth" in card.title or "NHS 111" in card.title for card in cards)


def test_transport_uses_ambulance_for_high_urgency_even_with_delay() -> None:
    options = build_transport_options(
        TransportOptionsRequest(
            urgency="high",
            emergency_signs_confirmed=False,
            ambulance_delay_minutes=45,
            mobility_limited=False,
        )
    )

    assert options[0].mode == "ambulance"
    assert options[0].suitability_score > next(
        option.suitability_score for option in options if option.mode == "ride_hailing"
    )


def test_transport_allows_ride_hailing_for_stable_medium_urgency() -> None:
    options = build_transport_options(
        TransportOptionsRequest(
            urgency="medium",
            emergency_signs_confirmed=False,
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
