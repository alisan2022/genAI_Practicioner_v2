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


@dataclass(slots=True)
class BasicAssessment:
    urgency: UrgencyLevel
    summary: str
    reasoning: list[str]
    recommended_actions: list[str]
    self_care_advice: list[str]
    otc_options: list[str]
    search_query: str
    decision_trace: list[str]


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


def assess_request(payload: AITriageRequest) -> BasicAssessment:
    symptoms_text = _normalise(payload.symptoms)
    known_conditions = _extract_conditions(payload.known_conditions)

    score = 0
    reasoning: list[str] = []
    trace = ["Started with deterministic symptom scoring."]

    if payload.emergency_signs_confirmed:
        score = max(score, 6)
        reasoning.append("Emergency warning signs were explicitly confirmed.")
        trace.append("Emergency override was applied.")

    high_hits = _keyword_hits(symptoms_text, HIGH_URGENCY_KEYWORDS)
    if high_hits:
        score = max(score, 4)
        reasoning.extend(HIGH_URGENCY_KEYWORDS[item] for item in high_hits)
        trace.append(f"Matched high-risk symptoms: {', '.join(high_hits[:3])}.")

    medium_hits = _keyword_hits(symptoms_text, MEDIUM_URGENCY_KEYWORDS)
    if medium_hits:
        score += min(len(medium_hits), 2)
        reasoning.extend(MEDIUM_URGENCY_KEYWORDS[item] for item in medium_hits[:2])
        trace.append(f"Matched medium-risk symptoms: {', '.join(medium_hits[:3])}.")

    if payload.pain_level is not None:
        if payload.pain_level >= 8:
            score += 2
            reasoning.append("Pain level is severe.")
            trace.append("Pain score increased urgency.")
        elif payload.pain_level >= 5:
            score += 1
            reasoning.append("Pain level is moderate.")
            trace.append("Moderate pain slightly increased urgency.")

    if payload.duration_hours is not None and payload.duration_hours >= 72:
        score += 1
        reasoning.append("Symptoms have lasted for more than three days.")
        trace.append("Symptom duration increased caution.")

    if payload.age is not None and (payload.age <= 5 or payload.age >= 75):
        score += 1
        reasoning.append("Age increases clinical risk, so earlier escalation is safer.")
        trace.append("Age-based safeguard applied.")

    risky_conditions = sorted(known_conditions.intersection(HIGH_RISK_CONDITIONS))
    if risky_conditions:
        score += 1
        reasoning.append(
            "Known conditions increase risk: " + ", ".join(risky_conditions) + "."
        )
        trace.append("Long-term condition safeguard applied.")

    if payload.mobility_limited:
        trace.append("Mobility limitation captured for transport selection.")

    if score >= 4:
        urgency: UrgencyLevel = "high"
    elif score >= 2:
        urgency = "medium"
    else:
        urgency = "low"

    if not reasoning:
        reasoning.append("No major red flags were detected in the provided details.")

    search_parts = [urgency, symptoms_text]
    if risky_conditions:
        search_parts.append(" ".join(risky_conditions))
    search_query = " ".join(part for part in search_parts if part).strip()
    trace.append(f"Assigned urgency: {urgency}.")

    return BasicAssessment(
        urgency=urgency,
        summary=_summary_for_urgency(urgency),
        reasoning=reasoning[:5],
        recommended_actions=_actions_for_urgency(urgency),
        self_care_advice=LOW_URGENCY_SELF_CARE.copy() if urgency == "low" else [],
        otc_options=_otc_suggestions(symptoms_text, urgency),
        search_query=search_query,
        decision_trace=trace,
    )
