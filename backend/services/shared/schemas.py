from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

UrgencyLevel = Literal["low", "medium", "high"]
FacilityKind = Literal["hospital", "urgent_care", "gp", "pharmacy"]
TransportMode = Literal["ambulance", "ride_hailing", "self_travel"]
KnowledgeCategory = Literal["service", "self_care", "safety", "transport", "follow_up"]
TrafficLevel = Literal["light", "moderate", "heavy", "unknown"]
RouteSource = Literal["road_network", "distance_heuristic"]


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=3000)


class AITriageRequest(BaseModel):
    symptoms: str = Field(min_length=3, max_length=4000)
    known_conditions: list[str] = Field(default_factory=list)
    age: int | None = Field(default=None, ge=0, le=120)
    duration_hours: int | None = Field(default=None, ge=0, le=24 * 365)
    pain_level: int | None = Field(default=None, ge=0, le=10)
    mobility_limited: bool = False
    emergency_signs_confirmed: bool = False
    ambulance_delay_minutes: int | None = Field(default=None, ge=0, le=300)
    location_latitude: float | None = Field(default=None, ge=-90, le=90)
    location_longitude: float | None = Field(default=None, ge=-180, le=180)


class KnowledgeCard(BaseModel):
    id: str
    title: str
    source: str
    category: KnowledgeCategory
    snippet: str
    relevance: float = Field(ge=0, le=1)


class KnowledgeRetrieveRequest(BaseModel):
    query: str = Field(min_length=2, max_length=3000)
    urgency: UrgencyLevel | None = None
    top_k: int = Field(default=4, ge=1, le=8)


class KnowledgeRetrieveResponse(BaseModel):
    cards: list[KnowledgeCard]


class RouteMetrics(BaseModel):
    distance_km: float = Field(ge=0, le=500)
    travel_minutes: int = Field(ge=0, le=600)
    average_speed_kmh: float = Field(ge=0, le=180)
    traffic_level: TrafficLevel
    source: RouteSource


class FacilityRecommendation(BaseModel):
    name: str
    kind: FacilityKind
    address: str
    contact: str
    latitude: float
    longitude: float
    estimated_wait_minutes: int = Field(ge=0, le=1440)
    route: RouteMetrics | None = None
    suitability_score: float = Field(default=0.5, ge=0, le=1)


class ClosestHospitalResponse(BaseModel):
    hospital: FacilityRecommendation
    distance_km: float = Field(ge=0)


class FacilityRecommendationRequest(BaseModel):
    urgency: UrgencyLevel
    count: int = Field(default=3, ge=1, le=6)
    location_latitude: float | None = Field(default=None, ge=-90, le=90)
    location_longitude: float | None = Field(default=None, ge=-180, le=180)


class FacilityRecommendationResponse(BaseModel):
    urgency: UrgencyLevel
    facilities: list[FacilityRecommendation]


class TransportOptionsRequest(BaseModel):
    urgency: UrgencyLevel
    emergency_signs_confirmed: bool = False
    ambulance_delay_minutes: int | None = Field(default=None, ge=0, le=300)
    mobility_limited: bool = False


class TransportOption(BaseModel):
    mode: TransportMode
    rationale: str
    eta_minutes: int | None = Field(default=None, ge=0, le=600)
    suitability_score: float = Field(ge=0, le=1)


class TransportOptionsResponse(BaseModel):
    options: list[TransportOption]


class TransportRecommendation(BaseModel):
    mode: TransportMode
    rationale: str
    eta_minutes: int | None = Field(default=None, ge=0, le=600)
    confidence: float = Field(default=0.5, ge=0, le=1)


class AITriageResponse(BaseModel):
    urgency: UrgencyLevel
    summary: str
    reasoning: list[str]
    recommended_actions: list[str]
    self_care_advice: list[str]
    otc_options: list[str]
    facilities: list[FacilityRecommendation]
    transport: TransportRecommendation
    knowledge_cards: list[KnowledgeCard]
    safety_disclaimer: str
    model: str
    decision_trace: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)
    history: list[HistoryMessage] = Field(default_factory=list)
    triage_summary: str | None = Field(default=None, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    model: str
    sources: list[str] = Field(default_factory=list)
    disclaimer: str
