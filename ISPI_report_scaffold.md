# ISPI Report Scaffold for `GenAI Practitioner v2`

## Important note before you use this

Your coursework brief says generative AI may be used for:

- generating ideas
- clarifying concepts
- improving written communication

It also says any AI use must be acknowledged in an appendix. Because of that, this file is an annotated drafting scaffold, not a submission-ready report to hand in unchanged. You should replace prompts, placeholders, and team-evidence sections with your own wording and your team's genuine records.

## What this scaffold is designed to optimise

This structure is aimed at the distinction criteria in the brief:

- a clearly scoped Bournemouth-focused problem
- strong requirement-to-prototype traceability
- well-justified design decisions, especially the LLM approach
- convincing ethical analysis with realistic mitigations
- evidence of professional practice and teamwork
- a reflective explanation of major project changes

## Suggested word budget for the main report

Keep the main body under 3,500 words. A practical split is:

- Problem context and definition: 400 to 500 words
- Requirements and traceability: 450 to 550 words
- Design rationale and technical approach: 900 to 1,050 words
- Ethical considerations and mitigations: 600 to 750 words
- Evaluation and ethical validation: 350 to 500 words
- Reflection on major decisions and changes: 250 to 350 words
- Conclusion: 100 to 150 words

## Recommended title

`GenAI Practitioner v2: A Bournemouth-Focused AI-Supported Health Triage and Local Care Navigation Prototype`

## Suggested report structure

### 1. Introduction

Write this section in your own voice. Cover:

- what the system is
- what Bournemouth-local problem it addresses
- why the problem matters
- what the report will cover

Project-specific points you can use:

- The project is a Bournemouth-focused mobile triage and care-navigation prototype.
- It helps users describe symptoms, receive a conservative urgency estimate, view Bournemouth-relevant services, and ask a follow-up question.
- The system is not framed as diagnosis; it is framed as triage, signposting, and safer next-step support.
- The current version deliberately uses the LLM for core clinical triage, while deterministic code only acts as a safety guardrail against dangerous under-escalation.

Good sources to cite here:

- BCP Council JSNA and Health and Wellbeing Strategy
- NHS 111 guidance
- University Hospitals Dorset urgent treatment and emergency department pages

### 2. Problem Context and Definition

Answer the marker's core question: why does Bournemouth need this, and what exact problem are you solving?

Use a structure like this:

1. Local context
2. Practical user problem
3. Consequence if the problem is not addressed
4. Final scoped problem statement

Project-specific points you can adapt:

- BCP's public health and wellbeing strategy explicitly focuses on improving health and wellbeing and reducing health inequalities.
- BCP's JSNA materials show that disability-limiting day-to-day activity rises sharply with age, which strengthens the case for simple, accessible, signposted local support.
- NHS urgent care journeys can be confusing for people deciding between self-care, pharmacy, NHS 111, urgent treatment, and emergency care.
- A Bournemouth-focused tool is useful because service signposting must be local, not generic.

Evidence points from official sources:

- BCP Council states that the Health and Wellbeing Board exists to improve health and wellbeing and reduce health inequalities.
- The BCP Strategic Assessment reports that 8% of the BCP population are limited a lot by disability, rising to 24% for ages 75 to 85 and 47% for people over 85.
- University Hospitals Dorset states that Royal Bournemouth and Poole both provide urgent/emergency access points, while UTC access is for serious but non-life-threatening issues and patients should call 111 first.

Example scope definition points to cover:

- In scope:
  - symptom-led triage support
  - local service signposting
  - route-aware facility ranking
  - follow-up clarification
- Out of scope:
  - diagnosis
  - prescribing
  - clinical record integration
  - ambulance dispatch
  - replacing clinicians

### 3. Requirements

This section should show that your requirements are clear, justified, and traceable to the prototype.

Use a short introductory paragraph, then present a requirement table.

Suggested requirements table:

| ID | Requirement | Why it matters | Prototype evidence |
| --- | --- | --- | --- |
| R1 | The system must provide Bournemouth-relevant service signposting. | The brief requires local grounding; generic advice is not enough. | Local knowledge cards and facility catalogue include Bournemouth and Poole services. |
| R2 | The system must distinguish between low, medium, and high urgency scenarios using LLM-led triage. | Users need differentiated next steps rather than a single generic answer. | LLM triage generation in `backend/services/shared/medical_llm.py`. |
| R3 | High-risk red flags must trigger immediate escalation advice. | Safeguarding is a core assessment criterion. | Safety guardrails, red-flag minimum urgency, and emergency override in `triage_logic.py`. |
| R4 | The system must return safe next actions, not diagnoses. | Reduces legal and ethical risk. | Disclaimers, structured LLM output, and constrained prompts. |
| R5 | The system should retrieve supporting guidance from verified local or NHS-style sources. | Improves transparency and Bournemouth relevance. | Knowledge retrieval layer and surfaced knowledge cards. |
| R6 | The system should rank nearby care options using urgency and optional route context. | Makes recommendations actionable, not merely descriptive. | Facility and route-ranking logic plus location-aware UI. |
| R7 | The prototype must degrade safely if the LLM is unavailable. | The app should not crash, but fallback should not pretend to be full clinical triage. | `safety-guardrails` fallback mode and conservative safety signposting. |
| R8 | The mobile UI must support a realistic end-to-end user journey. | This is explicitly assessed in the prototype criterion. | Symptom form, safety toggles, transport, facility cards, retrieval view, and follow-up chat. |
| R9 | The system should minimise unnecessary personal data collection. | Supports UK GDPR-oriented data minimisation. | No account creation; only symptoms, basic context, and optional location. |
| R10 | The team must be able to justify decisions and evidence them professionally. | Required for report and appendix marks. | Proposal, meeting records, task board, risk log, evaluation artefacts. |

After the table, write 1 short paragraph explaining how these requirements influenced later design choices.

### 4. Design Rationale and Technical Approach

This is the highest-value section for your mark. Keep it analytical, not descriptive.

Suggested subsection structure:

#### 4.1 Overview of the proposed solution

Describe the overall product briefly:

- mobile-first user interaction
- gateway as single entry point
- separate services for triage, knowledge, facility, transport, and chat
- LLM-led triage bounded by deterministic safety guardrails

#### 4.2 Why the architecture was chosen

Make explicit justifications, not just component lists.

Arguments you can develop:

- A microservice-style split supports separation of concerns.
- The gateway simplifies the mobile client and creates one stable API surface.
- Triage logic is isolated so its safety rules are easier to inspect and test.
- Knowledge retrieval is isolated so local content can be curated without changing scoring logic.
- Facility and transport services are separated because route ranking and transport suitability are operational concerns distinct from symptom assessment.
- Chat is separated because conversational follow-up has a different risk profile from first-pass triage.

#### 4.3 Why the project moved to LLM-led triage with guardrails

This is likely your strongest reflection-based design argument.

State clearly that Version 2 changed the technical strategy because:

- the project requirement is for the LLM to perform the clinical triage reasoning
- deterministic rules should not replace that LLM decision path
- health-related LLM output still needs guardrails because hallucination and under-escalation are high-impact risks
- a safe prototype can combine LLM reasoning, RAG grounding, structured output validation, and post-response safety constraints

Then explain the final sequence:

1. safety guardrails identify minimum escalation constraints
2. retrieval supplies local/NHS-style support content to the LLM
3. the medical LLM chooses urgency, reasoning, actions, and search query
4. guardrails post-check the LLM output and raise unsafe under-escalation
5. facility and transport services act on the final guarded urgency

#### 4.4 How the LLM is constrained

This is important for distinction-level justification.

Points directly supported by the code:

- The LLM does set urgency, but only within guardrail minimums.
- The triage prompt explicitly says to return JSON with urgency, summary, reasoning, actions, self-care advice, OTC options, and search query.
- The LLM is told not to invent diagnoses, facilities, phone numbers, service hours, transport advice, or medicines.
- The follow-up assistant is told to use only supplied knowledge snippets.
- If the model is unavailable or fails, the system falls back to conservative `safety-guardrails` output.

You should explicitly explain why this matters:

- it preserves deterministic enforcement around the highest-risk safety boundaries
- it reduces hallucination scope
- it improves explainability
- it makes the prototype professionally defensible

#### 4.5 Information sources and Bournemouth grounding

Explain that the current prototype grounds responses in:

- curated local knowledge cards
- Bournemouth and Poole facility data
- official urgent-care pathways such as NHS 111 and UTC/A&E escalation

You can also acknowledge the current limitation:

- the knowledge base is manually curated and still small
- therefore its strength is control and safety, but its weakness is coverage and update burden

That critical balance will improve the report.

#### 4.6 User journey and UI rationale

Describe the main journey:

1. user enters symptoms
2. user provides contextual details
3. user confirms safety and mobility flags
4. optional location is requested
5. system returns urgency, reasoning, next steps, transport, nearby care, retrieval snippets
6. user can ask a follow-up question

Why this flow is justified:

- it keeps the first interaction short
- it gathers only data needed for safer routing
- it moves from assessment to action
- it supports both low-urgency signposting and urgent escalation

#### 4.7 Feasibility and graceful degradation

This is a strong professional point. Explain that the system can still operate when:

- the medical LLM is unavailable, because conservative safety fallback remains available
- the routing service fails, because a heuristic distance fallback exists
- dependent services fail, because local fallbacks are implemented in the triage service

This shows professional resilience, not just feature ambition.

### 5. Ethical, Legal, and Social Considerations

Use the lab structure, but write it as report prose supported by one or two tables.

#### 5.1 Ethical risk overview

Introduce the principle clearly:

- The project handles health-related prompts, so the main risk is not only technical failure but harmful advice, misplaced trust, and inappropriate escalation or under-escalation.

#### 5.2 Risk analysis table

Use or adapt this table:

| Risk category | Example risk | Severity | Likely impact on Bournemouth users | Mitigation in the prototype |
| --- | --- | --- | --- | --- |
| Technical | LLM hallucination or unstable output | High | Unsafe or misleading health advice | LLM output is structured, RAG-grounded, and post-checked by safety guardrails; fallback mode available |
| Technical | Routing API failure | Medium | Poor facility ranking or missing travel estimates | Heuristic route fallback |
| Ethical | Over-reliance on AI advice | High | Users may delay proper care | Clear disclaimer, emergency escalation, service signposting |
| Ethical | Under-escalation of serious symptoms | High | Harm through delayed treatment | Red-flag minimum urgency, emergency override, conservative escalation |
| Data | Over-collection of personal information | Medium | Unnecessary privacy exposure | Minimal input set, optional location only |
| Data | Sensitive logs retained inappropriately | Medium | Privacy and compliance risk | Explain that production deployment should minimise, anonymise, and control retention |
| Social | Low digital literacy or stress reduces usability | Medium | Vulnerable users may misunderstand next steps | Simple form flow, short output, visible recommended actions |
| Social | Bias against older adults or complex cases | High | Unsafe advice for higher-risk groups | Earlier escalation for age and long-term conditions |
| Safeguarding | Severe symptoms not redirected quickly enough | High | Immediate harm | 999 guidance, A&E/UTC signposting, urgent transport logic |
| Safeguarding | Follow-up chat gives false reassurance | High | Users continue self-care when escalation is needed | Chat prompt includes emergency escalation rules and limited source scope |

#### 5.3 Legal and data-handling considerations

Discuss these directly:

- data minimisation
- optional location consent
- no unnecessary identity collection in the prototype
- health data sensitivity in a production deployment
- logging and retention controls that would be needed beyond prototype stage

Be explicit that:

- the current prototype is safer because it stores very little user information
- however, any real deployment would need a fuller DPIA-style review, privacy notice, secure hosting, audit logging policy, and retention controls

#### 5.4 Social considerations and fairness

Use Bournemouth context rather than generic AI ethics.

Points you can use:

- BCP public-health material emphasises health inequalities and local service coordination.
- Older adults and people with disability-limiting conditions may benefit from clearer service navigation, but also face higher harm if advice is wrong.
- People under stress may need direct signposting rather than verbose explanations.
- Diverse language and symptom phrasing may reduce keyword-matching accuracy, so the current prototype is safer as a conservative aid, not an autonomous advisor.

#### 5.5 Signposting strategy

Explain how the prototype operationalises safe signposting:

- emergency symptoms -> 999 / emergency department
- urgent but non-life-threatening cases -> NHS 111 / UTC / same-day review
- lower-risk cases -> pharmacy / self-care / GP if symptoms persist
- location-aware ranking improves actionability for Bournemouth-area users

### 6. Evaluation and Ethical Validation

This section is not the biggest one in the brief, but it will strengthen the report because Lab 8 and Lab 9 clearly push you to defend your design using evaluation evidence.

Use one evaluation theme. The safest choice for this project is:

- safeguarding and misinformation control

#### 6.1 Evaluation goal

Suggested wording to adapt:

- Evaluate whether the prototype consistently produces safe urgency categories and Bournemouth-relevant signposting across low-, medium-, and high-risk symptom scenarios.

#### 6.2 Evaluation question

Suggested wording to adapt:

- Does the system avoid unsafe reassurance and maintain appropriate escalation, service signposting, and fallback behaviour when symptom severity, risk factors, and service availability vary?

#### 6.3 Evaluation method

A mixed-method approach is easiest to justify:

- quantitative:
  - scenario-based pass/fail checks
  - counts of correct escalation outcomes
  - fallback behaviour under simulated service failures
- qualitative:
  - inspection of reasoning clarity
  - inspection of signposting usefulness
  - review of whether follow-up answers remain bounded and non-diagnostic

#### 6.4 Evidence you already have in the project

Use these repo-backed points:

- LLM-led endpoint test shows the LLM result owns low-urgency output
- guardrail tests show chest pain and breathlessness force high-urgency safety constraints
- knowledge retrieval surfaces Bournemouth or NHS 111 cards
- transport logic prefers ride-hailing when ambulance delay is high but no emergency red flag exists
- location-aware facility ranking exposes route metrics
- follow-up chat fallback escalates urgent wording

These come from:

- `backend/tests/test_triage_flow.py`

#### 6.5 Limitations to acknowledge honestly

This is important for higher marks.

- The current evaluation is scenario-based and developer-defined rather than clinician-validated.
- The knowledge base is curated but limited in coverage.
- Guardrail keyword matching can miss unusual symptom phrasing, so the LLM prompt and user-facing escalation wording must also remain conservative.
- Live service data is simplified rather than fully integrated from operational NHS systems.
- Real user evaluation with Bournemouth residents has not yet been completed.

#### 6.6 Why this still supports the design

Your key claim should be:

- Even with these limitations, the prototype demonstrates a safer and more defensible design choice than an unconstrained LLM-only approach, because LLM clinical reasoning is bounded by inspectable, testable safety guardrails.

### 7. Reflection on Major Decisions and Changes

This section should feel reflective, not like a second design section.

Strong reflection points for this project:

- The move from the original multi-client direction to one Expo mobile app simplified delivery and improved coherence.
- The move from unclear triage ownership to LLM-led triage plus RAG plus safety guardrails improved consistency, explainability, and demonstrability.
- The addition of location-aware ranking made recommendations more actionable.
- The fallback-first mindset changed the project from a fragile demo into a more professionally defensible prototype.

Questions to answer in your own wording:

- What did the team initially overestimate?
- What changed once ethical risk was considered seriously?
- Which trade-offs were accepted?
- What would the team do next with more time?

### 8. Conclusion

Keep this brief:

- restate the Bournemouth problem
- restate what the prototype demonstrates
- restate why the final architecture is justified
- restate that the prototype supports signposting, not diagnosis

## Figures and tables you should insert

- Figure 1: System architecture diagram
- Figure 2: End-to-end user journey wireframe
- Figure 3: Prompt workflow / control flow diagram
- Table 1: Requirements matrix
- Table 2: Ethical risk analysis
- Table 3: Evaluation evidence summary

## Repo evidence you can cite while drafting

- `README.md`
- `backend/services/shared/triage_logic.py`
- `backend/services/shared/knowledge_base.py`
- `backend/services/shared/facility_catalog.py`
- `backend/services/shared/route_intelligence.py`
- `backend/services/shared/medical_llm.py`
- `backend/services/triage/main.py`
- `backend/services/gateway/main.py`
- `backend/tests/test_triage_flow.py`
- `mobile-app/App.tsx`

## Official sources you can reference

- BCP Council JSNA: <https://www.bcpcouncil.gov.uk/communities/public-health/joint-strategic-needs-assessment-jsna/joint-strategic-needs-assessment-jsna-needs-assessments-and-insights>
- BCP Health and Wellbeing Strategy: <https://www.bcpcouncil.gov.uk/about-the-council/strategies-plans-and-policies/health-and-wellbeing-strategy>
- BCP Strategic Assessment 2023/24: <https://democracy.bcpcouncil.gov.uk/documents/s45854/Appendix%20A-%20BCP%20Strategic%20Assessment%2023-24.pdf>
- NHS 111 guidance: <https://www.nhs.uk/nhs-services/urgent-and-emergency-care-services/when-to-use-111/>
- University Hospitals Dorset Urgent Treatment Centre: <https://www.uhd.nhs.uk/services/urgent-treatment-centre>
- Royal Bournemouth ED update: <https://www.uhd.nhs.uk/news/latest-news/2025-news/2243-royal-bournemouth-hospital-emergency-department-opens-in-new-beach-building>

## Recommended reference points to cite

These are the strongest factual anchors I found:

- BCP Health and Wellbeing Strategy says the local board's purpose is to improve health and wellbeing and reduce health inequalities.
- BCP Strategic Assessment reports a 2021 BCP population estimate of 400,300 and states that 24% of the local population is expected to be aged over 65 by 2028.
- The same assessment reports that 8% of people in BCP are limited a lot by disability, rising to 24% for ages 75 to 85 and 47% for people over 85.
- NHS 111 says it can direct users to the best place to get help, including 999, urgent treatment centres, pharmacists, GP services, or safe self-care.
- University Hospitals Dorset says its UTCs are for serious but non-life-threatening problems and asks patients to call 111 before attending.

## Final drafting advice

When you turn this scaffold into the real report:

- write in report prose, not bullets
- keep every design choice tied to a requirement or risk
- do not claim clinical accuracy you have not evidenced
- do not fabricate team evidence
- add an appendix stating exactly how AI was used
