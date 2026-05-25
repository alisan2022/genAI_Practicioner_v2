from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from .schemas import AITriageRequest, UrgencyLevel

HIGH_RISK_CONDITIONS = {
    "heart disease",
    "copd",
    "asthma",
    "diabetes",
    "cancer",
    "pregnancy",
    "stroke history",
    "immunocompromised",
    "hypertension",
}

HIGH_URGENCY_KEYWORDS = OrderedDict(
    {
        "chest pain": "Chest pain can point to a serious heart or breathing problem.",
        "shortness of breath": "Trouble breathing raises urgency immediately.",
        "cannot breathe": "Severe breathing difficulty is an emergency warning sign.",
        "slurred speech": "Speech changes can be linked to stroke symptoms.",
        "face droop": "Facial droop can signal a stroke emergency.",
        "one sided weakness": "Sudden one-sided weakness can signal a stroke emergency.",
        "severe bleeding": "Heavy bleeding needs urgent medical help.",
        "vomiting blood": "Vomiting blood needs immediate assessment.",
        "coughing blood": "Coughing blood raises concern for urgent review.",
        "black stool": "Black stool can suggest internal bleeding.",
        "collapse": "Collapse or fainting can be a medical emergency.",
        "seizure": "Seizure activity should be treated urgently.",
        "unconscious": "Reduced consciousness needs emergency care.",
    }
)

MEDIUM_URGENCY_KEYWORDS = OrderedDict(
    {
        "fever": "Fever can indicate infection and may need review if it persists.",
        "infection": "Possible infection usually needs timely clinical review.",
        "vomiting": "Vomiting raises dehydration risk.",
        "diarrhoea": "Diarrhoea can lead to dehydration and worsening weakness.",
        "diarrhea": "Diarrhoea can lead to dehydration and worsening weakness.",
        "rash": "A new or worsening rash may need medical review.",
        "urinary": "Urinary symptoms may need same-day assessment.",
        "migraine": "Persistent severe headache can need clinical review.",
        "ear pain": "Significant ear pain can worsen without treatment.",
        "persistent cough": "A persistent cough can need assessment if it is not improving.",
        "sore throat": "Worsening throat symptoms may need pharmacy or GP review.",
    }
)

LOW_URGENCY_SELF_CARE = [
    "Rest, hydrate, and monitor how symptoms change over the next 24 to 48 hours.",
    "Use a pharmacist for advice on minor-illness treatment and suitable over-the-counter options.",
    "Escalate for urgent review if symptoms become suddenly worse, breathing changes, or new red flags appear.",
]

OTC_OPTIONS = {
    "cold": ["Paracetamol", "Saline nasal spray"],
    "headache": ["Paracetamol", "Ibuprofen if normally safe for you"],
    "cough": ["Cough syrup", "Honey with warm fluids"],
    "sore throat": ["Throat lozenges", "Paracetamol"],
    "fever": ["Paracetamol", "Oral rehydration fluids"],
    "diarrhoea": ["Oral rehydration salts"],
    "diarrhea": ["Oral rehydration salts"],
    "allergy": ["Cetirizine", "Loratadine"],
}


@dataclass
class BasicAssessment:
    urgency: UrgencyLevel
    summary: str
    reasoning: list[str]
    recommended_actions: list[str]
    self_care_advice: list[str]
    otc_options: list[str]
    search_query: str
    decision_trace: list[str]


@dataclass
class SafetyAssessment:
    minimum_urgency: UrgencyLevel | None
    red_flags: list[str]
    caution_flags: list[str]
    search_query: str
    decision_trace: list[str]


URGENCY_RANK: dict[UrgencyLevel, int] = {"low": 0, "medium": 1, "high": 2}


def _normalise(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _extract_conditions(conditions: list[str]) -> set[str]:
    return {_normalise(item) for item in conditions if item.strip()}


def _keyword_hits(text: str, lookup: OrderedDict[str, str]) -> list[str]:
    hits: list[str] = []
    for keyword in lookup:
        if keyword in text:
            hits.append(keyword)
    return hits


def _raise_to_at_least(current: UrgencyLevel, minimum: UrgencyLevel | None) -> UrgencyLevel:
    if minimum is None:
        return current
    return minimum if URGENCY_RANK[minimum] > URGENCY_RANK[current] else current


def _summary_for_urgency(urgency: UrgencyLevel) -> str:
    if urgency == "high":
        return "High urgency. The symptoms described need immediate in-person medical attention."
    if urgency == "medium":
        return "Medium urgency. A same-day GP, urgent treatment centre, or NHS 111 review is appropriate."
    return "Low urgency. The details currently sound more suitable for self-care and pharmacy support."


def _actions_for_urgency(urgency: UrgencyLevel) -> list[str]:
    if urgency == "high":
        return [
            "Seek urgent medical help now and do not wait for a routine appointment.",
            "If severe symptoms are happening now, call 999 immediately.",
            "Go to the nearest suitable hospital or urgent treatment centre as soon as possible.",
        ]
    if urgency == "medium":
        return [
            "Arrange same-day clinical review through a GP, urgent treatment centre, or NHS 111.",
            "Watch closely for breathing problems, confusion, severe pain, or sudden deterioration.",
            "Escalate immediately if emergency warning signs appear.",
        ]
    return [
        "Start with self-care and monitor symptoms closely for the next 24 to 48 hours.",
        "Use community pharmacy support for advice and over-the-counter treatment.",
        "Book GP or urgent review if symptoms are not improving or new warning signs appear.",
    ]


def _otc_suggestions(symptoms_text: str, urgency: UrgencyLevel) -> list[str]:
    if urgency == "high":
        return []

    found: list[str] = []
    for trigger, options in OTC_OPTIONS.items():
        if trigger in symptoms_text:
            for option in options:
                if option not in found:
                    found.append(option)
    return found


def assess_safety_constraints(payload: AITriageRequest) -> SafetyAssessment:
    symptoms_text = _normalise(payload.symptoms)
    known_conditions = _extract_conditions(payload.known_conditions)

    minimum_urgency: UrgencyLevel | None = None
    red_flags: list[str] = []
    caution_flags: list[str] = []
    trace = ["Checked deterministic safety constraints before LLM triage."]

    if payload.emergency_signs_confirmed:
        minimum_urgency = "high"
        red_flags.append("Emergency warning signs were explicitly confirmed.")
        trace.append("Emergency guardrail requires high urgency.")

    high_hits = _keyword_hits(symptoms_text, HIGH_URGENCY_KEYWORDS)
    if high_hits:
        minimum_urgency = "high"
        red_flags.extend(HIGH_URGENCY_KEYWORDS[item] for item in high_hits)
        trace.append(f"High-risk guardrail matched: {', '.join(high_hits[:3])}.")

    medium_hits = _keyword_hits(symptoms_text, MEDIUM_URGENCY_KEYWORDS)
    if medium_hits:
        caution_flags.extend(MEDIUM_URGENCY_KEYWORDS[item] for item in medium_hits[:3])
        trace.append(f"Provided caution hints to LLM: {', '.join(medium_hits[:3])}.")

    if payload.pain_level is not None:
        if payload.pain_level >= 8:
            minimum_urgency = _raise_to_at_least(minimum_urgency or "low", "medium")
            caution_flags.append("Pain level is severe.")
            trace.append("Severe pain guardrail requires at least medium urgency.")
        elif payload.pain_level >= 5:
            caution_flags.append("Pain level is moderate.")
            trace.append("Moderate pain shared with LLM as caution context.")

    if payload.duration_hours is not None and payload.duration_hours >= 72:
        caution_flags.append("Symptoms have lasted for more than three days.")
        trace.append("Long duration shared with LLM as caution context.")

    if payload.age is not None and (payload.age <= 5 or payload.age >= 75):
        minimum_urgency = _raise_to_at_least(minimum_urgency or "low", "medium")
        caution_flags.append("Age increases clinical risk, so earlier escalation is safer.")
        trace.append("Age guardrail requires at least medium urgency.")

    risky_conditions = sorted(known_conditions.intersection(HIGH_RISK_CONDITIONS))
    if risky_conditions:
        minimum_urgency = _raise_to_at_least(minimum_urgency or "low", "medium")
        caution_flags.append("Known conditions increase risk: " + ", ".join(risky_conditions) + ".")
        trace.append("Long-term condition guardrail requires at least medium urgency.")

    if payload.mobility_limited:
        caution_flags.append("Mobility limitation may affect safe transport choice.")
        trace.append("Mobility limitation shared with LLM as caution context.")

    search_parts = [symptoms_text]
    if risky_conditions:
        search_parts.append(" ".join(risky_conditions))
    if red_flags:
        search_parts.append("emergency warning signs")
    if caution_flags:
        search_parts.append("same day urgent care")
    search_query = " ".join(part for part in search_parts if part).strip()

    return SafetyAssessment(
        minimum_urgency=minimum_urgency,
        red_flags=red_flags[:6],
        caution_flags=caution_flags[:6],
        search_query=search_query,
        decision_trace=trace,
    )


def apply_safety_constraints(
    assessment: BasicAssessment,
    safety: SafetyAssessment,
) -> BasicAssessment:
    original_urgency = assessment.urgency
    assessment.urgency = _raise_to_at_least(assessment.urgency, safety.minimum_urgency)

    if assessment.urgency != original_urgency:
        assessment.decision_trace.append(
            f"Safety guardrail raised urgency from {original_urgency} to {assessment.urgency}."
        )
        assessment.reasoning.insert(
            0,
            "Safety guardrails escalated the response because the details include higher-risk features.",
        )

    if safety.red_flags:
        for flag in reversed(safety.red_flags[:2]):
            if flag not in assessment.reasoning:
                assessment.reasoning.insert(0, flag)
        if not any("999" in action for action in assessment.recommended_actions):
            assessment.recommended_actions.insert(
                0,
                "If severe symptoms are happening now, call 999 immediately.",
            )

    if assessment.urgency == "high":
        assessment.self_care_advice = []
        assessment.otc_options = []
        if not any("urgent" in action.lower() or "999" in action for action in assessment.recommended_actions):
            assessment.recommended_actions.insert(0, "Seek urgent medical help now.")
    elif assessment.urgency == "medium":
        if not any("111" in action or "same-day" in action.lower() for action in assessment.recommended_actions):
            assessment.recommended_actions.append(
                "Use NHS 111 or arrange same-day clinical review if symptoms persist or worsen."
            )
    else:
        if not any("red flag" in action.lower() or "worse" in action.lower() for action in assessment.recommended_actions):
            assessment.recommended_actions.append(
                "Escalate urgently if symptoms become suddenly worse or red flags appear."
            )

    assessment.reasoning = assessment.reasoning[:6]
    assessment.recommended_actions = assessment.recommended_actions[:6]
    assessment.self_care_advice = assessment.self_care_advice[:6]
    assessment.otc_options = assessment.otc_options[:6]
    return assessment


def build_safety_fallback_assessment(
    payload: AITriageRequest,
    safety: SafetyAssessment,
) -> BasicAssessment:
    urgency: UrgencyLevel = safety.minimum_urgency or "medium"
    symptoms_text = _normalise(payload.symptoms)
    reasoning = safety.red_flags + safety.caution_flags
    if not reasoning:
        reasoning = [
            "The clinical triage model is unavailable, so the app is using conservative safety guidance only."
        ]

    assessment = BasicAssessment(
        urgency=urgency,
        summary=(
            "Clinical triage model unavailable. Use this as safety signposting only and seek clinical advice if unsure."
            if urgency != "high"
            else "High urgency safety warning. The details include emergency warning signs."
        ),
        reasoning=reasoning[:6],
        recommended_actions=_actions_for_urgency(urgency),
        self_care_advice=LOW_URGENCY_SELF_CARE.copy() if urgency == "low" else [],
        otc_options=_otc_suggestions(symptoms_text, urgency),
        search_query=safety.search_query,
        decision_trace=["Used safety fallback because LLM triage was unavailable."],
    )
    return apply_safety_constraints(assessment, safety)
