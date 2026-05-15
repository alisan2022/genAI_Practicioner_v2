from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from .config import (
    DEFAULT_DISCLAIMER,
    DEFAULT_SAFETY_MODEL_LABEL,
    MEDICAL_LLM_API_KEY,
    MEDICAL_LLM_BASE_URL,
    MEDICAL_LLM_ENABLED,
    MEDICAL_LLM_MODEL,
)
from .schemas import AITriageRequest, ChatResponse, KnowledgeCard, UrgencyLevel
from .triage_logic import BasicAssessment, SafetyAssessment


@dataclass(slots=True)
class LLMRunResult:
    assessment: BasicAssessment | None
    note: str
    model: str


def _create_client() -> OpenAI | None:
    if not MEDICAL_LLM_ENABLED:
        return None

    kwargs: dict[str, Any] = {"api_key": MEDICAL_LLM_API_KEY}
    if MEDICAL_LLM_BASE_URL:
        kwargs["base_url"] = MEDICAL_LLM_BASE_URL
    return OpenAI(**kwargs)


CLIENT = _create_client()


def llm_status() -> dict[str, str | bool]:
    return {
        "enabled": bool(CLIENT),
        "model": MEDICAL_LLM_MODEL if CLIENT else DEFAULT_SAFETY_MODEL_LABEL,
    }


def _extract_text(response: object) -> str:
    choices = getattr(response, "choices", None)
    if not isinstance(choices, list):
        return ""

    chunks: list[str] = []
    for choice in choices:
        message = getattr(choice, "message", None)
        if message is None:
            continue

        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            chunks.append(content.strip())
            continue

        if isinstance(content, list):
            for piece in content:
                if getattr(piece, "type", None) == "text":
                    value = getattr(piece, "text", None)
                    if isinstance(value, str) and value.strip():
                        chunks.append(value.strip())

    return "\n".join(chunks).strip()


def _create_completion(prompt: str, *, max_tokens: int = 700) -> str:
    if CLIENT is None:
        return ""

    response = CLIENT.chat.completions.create(
        model=MEDICAL_LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=max_tokens,
    )
    return _extract_text(response)


def _parse_json_object(raw: str) -> dict[str, Any] | None:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _clean_list(value: object, *, limit: int = 6) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned.append(item.strip())
    return cleaned[:limit]


def _coerce_urgency(value: object) -> UrgencyLevel | None:
    if not isinstance(value, str):
        return None
    lowered = value.strip().lower()
    if lowered in {"low", "medium", "high"}:
        return lowered  # type: ignore[return-value]
    return None


def _request_payload(request: AITriageRequest) -> dict[str, Any]:
    return {
        "symptoms": request.symptoms,
        "known_conditions": request.known_conditions,
        "age": request.age,
        "duration_hours": request.duration_hours,
        "pain_level": request.pain_level,
        "mobility_limited": request.mobility_limited,
        "emergency_signs_confirmed": request.emergency_signs_confirmed,
        "location_provided": request.location_latitude is not None and request.location_longitude is not None,
    }


def generate_triage_assessment(
    *,
    request: AITriageRequest,
    cards: list[KnowledgeCard],
    safety: SafetyAssessment,
) -> LLMRunResult:
    if CLIENT is None:
        return LLMRunResult(
            assessment=None,
            note="LLM triage skipped because no model client is configured.",
            model=DEFAULT_SAFETY_MODEL_LABEL,
        )

    prompt_payload = {
        "patient_input": _request_payload(request),
        "local_knowledge_cards": [card.model_dump() for card in cards],
        "safety_guardrails": {
            "minimum_urgency": safety.minimum_urgency,
            "red_flags": safety.red_flags,
            "caution_flags": safety.caution_flags,
        },
    }

    prompt = """
You are the clinical triage reasoning model inside a Bournemouth urgent-care navigation prototype.

Your job:
- Decide the triage urgency as exactly one of: low, medium, high.
- Use clinical reasoning plus the supplied local knowledge cards.
- Provide signposting, not diagnosis.
- Low means self-care/pharmacy is likely appropriate unless symptoms worsen.
- Medium means same-day GP, NHS 111, or urgent treatment centre review is appropriate.
- High means immediate urgent care, emergency department, or 999 if severe now.

Safety restrictions:
- Never choose an urgency below safety_guardrails.minimum_urgency when it is present.
- Do not provide reassurance that symptoms are safe.
- Do not invent facilities, phone numbers, service hours, medicines, or diagnoses.
- Do not prescribe treatment.
- If severe, sudden, or worsening symptoms are described, escalate.
- If the evidence is uncertain, choose the safer higher urgency.

Return JSON only with these keys:
urgency, summary, reasoning, recommended_actions, self_care_advice, otc_options, search_query.

Each list must contain short patient-friendly strings. Keep otc_options empty for high urgency.

Payload:
""".strip() + "\n" + json.dumps(prompt_payload, ensure_ascii=False)

    try:
        raw = _create_completion(prompt, max_tokens=900)
        parsed = _parse_json_object(raw)
        if parsed is None:
            return LLMRunResult(
                assessment=None,
                note="LLM triage returned non-JSON output.",
                model=MEDICAL_LLM_MODEL,
            )

        urgency = _coerce_urgency(parsed.get("urgency"))
        summary = parsed.get("summary")
        if urgency is None or not isinstance(summary, str) or not summary.strip():
            return LLMRunResult(
                assessment=None,
                note="LLM triage JSON missed required urgency or summary.",
                model=MEDICAL_LLM_MODEL,
            )

        search_query = parsed.get("search_query")
        if not isinstance(search_query, str) or not search_query.strip():
            search_query = " ".join(
                item
                for item in [
                    urgency,
                    request.symptoms,
                    " ".join(request.known_conditions),
                ]
                if item
            )

        assessment = BasicAssessment(
            urgency=urgency,
            summary=summary.strip(),
            reasoning=_clean_list(parsed.get("reasoning")),
            recommended_actions=_clean_list(parsed.get("recommended_actions")),
            self_care_advice=_clean_list(parsed.get("self_care_advice")),
            otc_options=_clean_list(parsed.get("otc_options")),
            search_query=search_query.strip(),
            decision_trace=["Generated clinical triage with medical LLM."],
        )

        if not assessment.reasoning:
            assessment.reasoning = ["The LLM selected urgency from the submitted symptoms and risk context."]
        if not assessment.recommended_actions:
            assessment.recommended_actions = ["Seek clinical advice if symptoms persist, worsen, or feel concerning."]

        return LLMRunResult(
            assessment=assessment,
            note="Generated clinical triage with medical LLM.",
            model=MEDICAL_LLM_MODEL,
        )
    except Exception:
        return LLMRunResult(
            assessment=None,
            note="LLM triage failed and safety fallback was used.",
            model=MEDICAL_LLM_MODEL,
        )


def answer_follow_up(
    *,
    message: str,
    triage_summary: str | None,
    history: list[dict[str, str]],
    cards: list[KnowledgeCard],
) -> ChatResponse | None:
    if CLIENT is None:
        return None

    prompt_payload = {
        "triage_summary": triage_summary,
        "knowledge_cards": [card.model_dump() for card in cards],
        "history": history[-6:],
        "message": message,
    }

    try:
        prompt = """
You are a careful medical information assistant inside a triage app.

Rules:
- Do not diagnose.
- Use the supplied knowledge snippets only.
- Be plain, calm, and short.
- Include emergency escalation if symptoms sound severe.
- Structure the answer as short paragraphs, not long essays.

Conversation payload:
""".strip() + "\n" + json.dumps(prompt_payload, ensure_ascii=False)

        reply = _create_completion(prompt, max_tokens=700)
        if reply:
            return ChatResponse(
                reply=reply,
                model=MEDICAL_LLM_MODEL,
                sources=[card.source for card in cards],
                disclaimer=DEFAULT_DISCLAIMER,
            )
    except Exception:
        return None

    return None
