from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .config import (
    DEFAULT_DISCLAIMER,
    DEFAULT_RULES_MODEL_LABEL,
    MEDICAL_LLM_API_KEY,
    MEDICAL_LLM_BASE_URL,
    MEDICAL_LLM_ENABLED,
    MEDICAL_LLM_MODEL,
)
from .schemas import AITriageResponse, ChatResponse, KnowledgeCard


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
        "model": MEDICAL_LLM_MODEL or DEFAULT_RULES_MODEL_LABEL,
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
        temperature=0.2,
        max_tokens=max_tokens,
    )
    return _extract_text(response)


def maybe_refine_triage(response_model: AITriageResponse) -> AITriageResponse:
    if CLIENT is None:
        response_model.model = DEFAULT_RULES_MODEL_LABEL
        return response_model

    payload = {
        "urgency": response_model.urgency,
        "summary": response_model.summary,
        "reasoning": response_model.reasoning,
        "recommended_actions": response_model.recommended_actions,
        "self_care_advice": response_model.self_care_advice,
        "otc_options": response_model.otc_options,
        "knowledge_cards": [item.model_dump() for item in response_model.knowledge_cards],
    }

    try:
        prompt = """
You are a cautious medical communication assistant.

Rules:
- Do not change the urgency.
- Do not invent diagnoses.
- Do not invent new facilities, transport advice, or medicines.
- Rewrite only for clarity, brevity, and patient-friendly wording.
- Return JSON only with keys: summary, reasoning, recommended_actions, self_care_advice, otc_options.

Payload:
""".strip() + "\n" + json.dumps(payload, ensure_ascii=False)

        raw = _create_completion(prompt, max_tokens=700)
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            if isinstance(parsed.get("summary"), str) and parsed["summary"].strip():
                response_model.summary = parsed["summary"].strip()
            for field_name in ("reasoning", "recommended_actions", "self_care_advice", "otc_options"):
                value = parsed.get(field_name)
                if isinstance(value, list):
                    cleaned = [
                        item.strip()
                        for item in value
                        if isinstance(item, str) and item.strip()
                    ]
                    setattr(response_model, field_name, cleaned[:6])
            response_model.model = MEDICAL_LLM_MODEL
            response_model.decision_trace.append("Refined patient-facing wording with optional medical LLM.")
            return response_model
    except Exception:
        pass

    response_model.model = DEFAULT_RULES_MODEL_LABEL
    return response_model


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
