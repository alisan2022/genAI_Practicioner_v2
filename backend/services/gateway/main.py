from __future__ import annotations

from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.services.shared.config import (
    CHAT_SERVICE_URL,
    FACILITY_SERVICE_URL,
    KNOWLEDGE_SERVICE_URL,
    TRIAGE_SERVICE_URL,
)
from backend.services.shared.schemas import (
    AITriageRequest,
    AITriageResponse,
    ChatRequest,
    ChatResponse,
    ClosestHospitalResponse,
    KnowledgeRetrieveRequest,
    KnowledgeRetrieveResponse,
)

app = FastAPI(title="GenAI Practitioner v2 Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _proxy_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = httpx.post(url, json=payload, timeout=20.0)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Service unavailable: {exc}") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    parsed = response.json()
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=502, detail=f"Invalid payload returned from {url}")
    return parsed


@app.get("/health")
def health() -> dict[str, Any]:
    checks = {
        "gateway": {"status": "ok"},
        "triage": {"status": "unknown"},
        "knowledge": {"status": "unknown"},
        "facility": {"status": "unknown"},
        "chat": {"status": "unknown"},
    }

    service_urls = {
        "triage": f"{TRIAGE_SERVICE_URL}/health",
        "knowledge": f"{KNOWLEDGE_SERVICE_URL}/health",
        "facility": f"{FACILITY_SERVICE_URL}/health",
        "chat": f"{CHAT_SERVICE_URL}/health",
    }

    for name, url in service_urls.items():
        try:
            response = httpx.get(url, timeout=5.0)
            checks[name] = response.json() if response.status_code == 200 else {"status": "down"}
        except Exception as exc:  # noqa: BLE001
            checks[name] = {"status": "down", "error": str(exc)}

    return {"status": "ok", "services": checks}


@app.post("/ai-triage", response_model=AITriageResponse)
def ai_triage(request: AITriageRequest) -> AITriageResponse:
    payload = _proxy_post(f"{TRIAGE_SERVICE_URL}/ai-triage", request.model_dump())
    return AITriageResponse.model_validate(payload)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    payload = _proxy_post(f"{CHAT_SERVICE_URL}/chat", request.model_dump())
    return ChatResponse.model_validate(payload)


@app.post("/knowledge", response_model=KnowledgeRetrieveResponse)
def knowledge(request: KnowledgeRetrieveRequest) -> KnowledgeRetrieveResponse:
    payload = _proxy_post(f"{KNOWLEDGE_SERVICE_URL}/retrieve", request.model_dump())
    return KnowledgeRetrieveResponse.model_validate(payload)


@app.get("/nearest-hospital", response_model=ClosestHospitalResponse)
def nearest_hospital(
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
) -> ClosestHospitalResponse:
    try:
        response = httpx.get(
            f"{FACILITY_SERVICE_URL}/closest-hospital",
            params={"latitude": latitude, "longitude": longitude},
            timeout=10.0,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Facility service unavailable: {exc}") from exc

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    payload = response.json()
    if not isinstance(payload, dict):
        raise HTTPException(status_code=502, detail="Invalid closest hospital response")
    return ClosestHospitalResponse.model_validate(payload)
