from __future__ import annotations

from fastapi import FastAPI

from backend.services.shared.config import DEFAULT_DISCLAIMER, DEFAULT_SAFETY_MODEL_LABEL
from backend.services.shared.knowledge_base import retrieve_documents
from backend.services.shared.medical_llm import answer_follow_up, llm_status
from backend.services.shared.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Chat Service")

EMERGENCY_HINTS = (
    "chest pain",
    "shortness of breath",
    "cannot breathe",
    "slurred speech",
    "face droop",
    "severe bleeding",
    "unconscious",
)
URGENT_QUESTION_HINTS = (
    "urgent",
    "emergency",
    "tonight",
    "wait",
    "worse",
    "worsening",
    "escalate",
    "hospital",
    "111",
    "999",
)


def _sounds_emergency(message: str) -> bool:
    lowered = message.lower()
    return any(hint in lowered for hint in EMERGENCY_HINTS)


def _sounds_urgent_question(message: str) -> bool:
    lowered = message.lower()
    return any(hint in lowered for hint in URGENT_QUESTION_HINTS)


def _triage_urgency(triage_summary: str | None) -> str | None:
    if not triage_summary:
        return None

    prefix = triage_summary.split(":", 1)[0].strip().lower()
    if prefix in {"high", "medium", "low"}:
        return prefix
    return None


def _fallback_chat_reply(request: ChatRequest) -> ChatResponse:
    query = " ".join(part for part in [request.triage_summary or "", request.message] if part).strip()
    urgency = _triage_urgency(request.triage_summary)
    cards = retrieve_documents(query or request.message, urgency=urgency, top_k=4)
    sources = list(dict.fromkeys(card.source for card in cards))

    sections: list[str] = []
    if _sounds_emergency(request.message):
        sections.append(
            "This sounds like a possible emergency. If symptoms are severe now, call 999 or go to emergency care immediately."
        )
    elif urgency == "high":
        sections.append("The current triage already points to urgent in-person care rather than watch-and-wait.")
    elif urgency == "medium" or _sounds_urgent_question(request.message):
        sections.append("This still sounds like something to review the same day if symptoms are worsening or not settling.")
    else:
        sections.append("This still looks suitable for monitoring, as long as no red flags appear.")

    if cards:
        sections.append(cards[0].snippet)

    safety_card = next((card for card in cards if card.category == "safety"), None)
    if safety_card and not _sounds_emergency(request.message):
        sections.append("Watch for red flags: " + safety_card.snippet)

    if urgency == "high":
        sections.append("If symptoms escalate further, do not wait for a callback or routine appointment.")
    elif urgency == "medium":
        sections.append("Use NHS 111 or an urgent treatment centre if you cannot get timely GP review.")
    else:
        sections.append("If symptoms become suddenly worse, seek urgent clinical review.")

    return ChatResponse(
        reply="\n\n".join(dict.fromkeys(section for section in sections if section)),
        model=DEFAULT_SAFETY_MODEL_LABEL,
        sources=sources,
        disclaimer=DEFAULT_DISCLAIMER,
    )


@app.get("/health")
def health() -> dict[str, str | bool]:
    status = llm_status()
    return {
        "status": "ok",
        "service": "chat",
        "llm_enabled": status["chat_enabled"],
        "model": status["chat_model"],
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    query = " ".join(part for part in [request.triage_summary or "", request.message] if part).strip()
    cards = retrieve_documents(query or request.message, top_k=4)
    history = [item.model_dump() for item in request.history]

    llm_response = answer_follow_up(
        message=request.message,
        triage_summary=request.triage_summary,
        history=history,
        cards=cards,
    )
    if llm_response is not None:
        return llm_response

    return _fallback_chat_reply(request)
