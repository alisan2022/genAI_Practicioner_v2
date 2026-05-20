from __future__ import annotations

import re
from dataclasses import dataclass

from .schemas import KnowledgeCard, UrgencyLevel


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    id: str
    title: str
    source: str
    category: str
    tags: tuple[str, ...]
    body: str
    urgency_hint: str


DOCUMENTS: tuple[KnowledgeDocument, ...] = (
    KnowledgeDocument(
        id="safety-emergency-signs",
        title="Emergency warning signs",
        source="NHS emergency safety guidance",
        category="safety",
        tags=("chest pain", "stroke", "breathing", "bleeding", "seizure", "999"),
        urgency_hint="high",
        body=(
            "Sudden chest pain, severe shortness of breath, stroke signs, severe bleeding, "
            "collapse, seizures, or confusion should be treated as emergencies. "
            "Do not wait for a routine appointment when red-flag symptoms are present."
        ),
    ),
    KnowledgeDocument(
        id="service-nhs-111",
        title="NHS 111 for urgent non-emergency help",
        source="NHS 111",
        category="service",
        tags=("111", "urgent", "same day", "non emergency", "advice"),
        urgency_hint="medium",
        body=(
            "NHS 111 is suitable when someone needs urgent medical advice but the situation "
            "does not look like a life-threatening emergency. It is a useful step if symptoms "
            "worsen while waiting for a GP or urgent treatment appointment."
        ),
    ),
    KnowledgeDocument(
        id="selfcare-cold-flu",
        title="Self-care for cold, sore throat, and mild fever",
        source="Community pharmacy guidance",
        category="self_care",
        tags=("cold", "flu", "sore throat", "fever", "headache", "cough"),
        urgency_hint="low",
        body=(
            "Mild cold and flu-type symptoms often improve with rest, fluids, temperature "
            "control, and pharmacy support. Seek further assessment if fever persists, "
            "breathing worsens, swallowing becomes difficult, or symptoms keep escalating."
        ),
    ),
    KnowledgeDocument(
        id="selfcare-upset-stomach",
        title="Self-care for vomiting or diarrhoea",
        source="NHS self-care guidance",
        category="self_care",
        tags=("vomiting", "diarrhoea", "diarrhea", "dehydration", "stomach"),
        urgency_hint="medium",
        body=(
            "Vomiting and diarrhoea increase dehydration risk. Small frequent fluids, oral "
            "rehydration products, and careful monitoring are appropriate for mild cases, "
            "but prolonged symptoms or severe weakness need clinical review."
        ),
    ),
    KnowledgeDocument(
        id="service-bournemouth-utc",
        title="Bournemouth Urgent Treatment Centre",
        source="University Hospitals Dorset",
        category="service",
        tags=("urgent treatment", "minor injury", "same day", "bournemouth"),
        urgency_hint="medium",
        body=(
            "Bournemouth Urgent Treatment Centre is useful for urgent but non-life-threatening "
            "problems such as minor injuries, worsening infections, and same-day issues that "
            "need in-person assessment faster than a routine GP appointment."
        ),
    ),
    KnowledgeDocument(
        id="service-royal-bournemouth",
        title="Royal Bournemouth Hospital A&E",
        source="University Hospitals Dorset",
        category="service",
        tags=("a&e", "emergency department", "royal bournemouth hospital", "hospital"),
        urgency_hint="high",
        body=(
            "Royal Bournemouth Hospital is a major emergency destination for serious symptoms "
            "requiring urgent hospital assessment, especially when red flags are present or "
            "urgent treatment centre support is not sufficient."
        ),
    ),
    KnowledgeDocument(
        id="service-poole-hospital",
        title="Poole Hospital A&E",
        source="University Hospitals Dorset",
        category="service",
        tags=("poole", "a&e", "hospital", "emergency department"),
        urgency_hint="high",
        body=(
            "Poole Hospital A&E is another emergency option in the local Dorset area and may "
            "be relevant when it is closer, less busy, or more appropriate for urgent travel."
        ),
    ),
    KnowledgeDocument(
        id="service-pharmacy",
        title="Community pharmacy support",
        source="Local pharmacy guidance",
        category="service",
        tags=("pharmacy", "otc", "self care", "minor illness", "boots"),
        urgency_hint="low",
        body=(
            "Community pharmacies are appropriate for many minor illnesses, medication advice, "
            "and over-the-counter symptom relief. Pharmacists are especially useful when the "
            "user needs help deciding whether home care is enough or whether escalation is needed."
        ),
    ),
    KnowledgeDocument(
        id="transport-guidance",
        title="Choosing 999, NHS 111, ride-hailing, or self travel",
        source="Local transport triage policy",
        category="transport",
        tags=("999", "111", "ambulance", "uber", "taxi", "ride", "self travel"),
        urgency_hint="medium",
        body=(
            "Call 999 for emergency warning signs or severe symptoms now. Use NHS 111 for urgent "
            "but not immediately life-threatening advice. Ride-hailing may be appropriate for "
            "stable low or medium urgency patients who do not need ambulance support. Self travel "
            "is generally suitable only for lower-risk, stable cases."
        ),
    ),
    KnowledgeDocument(
        id="safety-older-adults",
        title="Extra caution for children, older adults, and complex conditions",
        source="Safeguarding checklist",
        category="safety",
        tags=("older adult", "child", "pregnancy", "diabetes", "asthma", "copd"),
        urgency_hint="medium",
        body=(
            "Children, older adults, pregnant people, and patients with long-term conditions "
            "often need earlier escalation because symptoms can worsen faster or present less clearly."
        ),
    ),
    KnowledgeDocument(
        id="followup-clinician-questions",
        title="Questions to ask a clinician",
        source="Follow-up support notes",
        category="follow_up",
        tags=("follow up", "questions", "clinician", "next steps"),
        urgency_hint="medium",
        body=(
            "Helpful follow-up questions include how quickly the patient should be reviewed, "
            "what warning signs should trigger urgent escalation, and which medicines or "
            "self-care steps are appropriate to use or avoid."
        ),
    ),
)

TOKEN_PATTERN = re.compile(r"[a-z0-9']+")


def _tokenize(text: str) -> set[str]:
    return {match.group(0) for match in TOKEN_PATTERN.finditer(text.lower())}


def _score_document(
    document: KnowledgeDocument,
    query_tokens: set[str],
    urgency: UrgencyLevel | None,
) -> float:
    haystack = _tokenize(f"{document.title} {' '.join(document.tags)} {document.body}")
    overlap = len(query_tokens.intersection(haystack))
    if overlap == 0:
        base = 0.0
    else:
        base = overlap / max(len(query_tokens), 1)

    if urgency and document.urgency_hint == urgency:
        base += 0.2
    if document.category == "service":
        base += 0.05
    return min(base, 1.0)


def retrieve_documents(
    query: str,
    *,
    urgency: UrgencyLevel | None = None,
    top_k: int = 4,
) -> list[KnowledgeCard]:
    query_tokens = _tokenize(query or "")
    if not query_tokens and urgency:
        query_tokens = {urgency}

    scored: list[tuple[float, KnowledgeDocument]] = []
    for document in DOCUMENTS:
        score = _score_document(document, query_tokens, urgency)
        if score > 0:
            scored.append((score, document))

    if not scored:
        for document in DOCUMENTS:
            if urgency and document.urgency_hint == urgency:
                scored.append((0.2, document))

    scored.sort(key=lambda item: item[0], reverse=True)

    cards: list[KnowledgeCard] = []
    for score, document in scored[:top_k]:
        cards.append(
            KnowledgeCard(
                id=document.id,
                title=document.title,
                source=document.source,
                category=document.category,  # type: ignore[arg-type]
                snippet=document.body,
                relevance=round(score, 2),
            )
        )

    return cards
