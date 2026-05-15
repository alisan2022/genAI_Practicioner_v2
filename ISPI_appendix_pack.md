# ISPI Appendix Pack for `GenAI Practitioner v2`

Use this file to build the appendices the brief explicitly asks for. Replace placeholders with your team's real evidence.

## Appendix A. AI Use Statement

The coursework brief requires AI use to be acknowledged.

Suggested structure:

| Section or task | How AI was used | What the team did independently afterwards |
| --- | --- | --- |
| Report planning | AI was used to help structure the report and map content to the brief. | The team selected the final structure and wrote the submitted content. |
| Language support | AI was used to improve clarity, grammar, and phrasing. | The team checked all claims against project evidence and local sources. |
| Idea generation | AI was used to suggest risk categories, evaluation angles, and wording options. | The team chose, edited, and evidenced the final material. |

Add a short note confirming that all final claims, team evidence, and reflections were reviewed and approved by the group.

## Appendix B. Final Proposal

If your team already has a proposal, paste it here. If not, rebuild it from your actual early decisions.

Suggested headings:

- Project title
- Bournemouth-focused problem
- Intended users
- Proposed solution
- Initial technical approach
- Initial risks
- Early delivery plan

## Appendix C. Requirements Traceability Matrix

| Requirement ID | Requirement | Source of requirement | Prototype element | Evidence file / figure |
| --- | --- | --- | --- | --- |
| R1 | Bournemouth-relevant signposting | Coursework brief + local need | Knowledge cards + facility list | Figure 1, Figure 2 |
| R2 | Multi-level urgency support | User safety | LLM-led triage generation | `medical_llm.py` |
| R3 | Red-flag escalation | Safeguarding | Safety guardrails + recommended actions | `triage_logic.py` |
| R4 | Safe next-step guidance, not diagnosis | Ethics | Summary, actions, disclaimer | `App.tsx`, `config.py` |
| R5 | Verified contextual support | Bournemouth grounding | Retrieval layer | `knowledge_base.py` |
| R6 | Actionable nearby care ranking | Usability | Facility and route logic | `facility_catalog.py`, `route_intelligence.py` |
| R7 | Safe LLM fallback behaviour | Reliability | LLM-led triage with `safety-guardrails` fallback | `triage/main.py`, `medical_llm.py` |
| R8 | Follow-up clarification | User journey | Chat flow | `App.tsx`, `chat/main.py` |

## Appendix D. Ethical Impact Assessment Builder

| EIA component | Draft content to adapt with your own wording |
| --- | --- |
| System overview | A Bournemouth-focused mobile triage and care-navigation prototype that helps users move from symptom description to safer local next-step signposting. |
| Privacy risks | Symptoms and optional location are sensitive; minimise inputs, avoid unnecessary identity collection, and define strict retention controls for any production deployment. |
| Bias and fairness risks | LLMs and guardrail keyword checks can both miss unusual phrasing; older adults, people with complex conditions, and digitally excluded users may be disproportionately affected by errors. |
| Misinformation risks | Harm could occur if outputs falsely reassure users, under-escalate red flags, or signpost the wrong service; risk increases if an unconstrained LLM invents details. |
| Safeguarding | Emergency red flags must trigger escalation; follow-up chat must not undermine urgent advice. |
| Signposting strategy | Use NHS 111, UTC, A&E, GP, pharmacy, and Bournemouth/Poole local services according to urgency level. |
| Mitigation plan | LLM-led triage with deterministic safety guardrails, curated local knowledge, visible disclaimers, route-aware actionability, structured JSON validation, and explicit fallbacks. |

## Appendix E. Legal and Social Checklist

### Legal considerations

- [ ] Data is minimised
- [ ] Sensitive information is limited to what is necessary
- [ ] Optional location is permission-based
- [ ] Logging and retention policy is defined for deployment
- [ ] Public information sources are cited appropriately

### Social considerations

- [ ] Bournemouth services are clearly signposted
- [ ] Outputs are understandable under stress
- [ ] Users with low digital literacy are considered
- [ ] Older adults and vulnerable groups are considered
- [ ] Local health inequalities are acknowledged

## Appendix F. Evaluation Plan and Evidence List

### Evaluation design

| Element | Entry to adapt |
| --- | --- |
| Ethical risk addressed | Safeguarding and misinformation |
| Evaluation goal | Verify that the system escalates urgent cases safely and signposts Bournemouth-relevant care pathways appropriately. |
| Evaluation question | Does the prototype maintain safe urgency classification, local signposting, and bounded follow-up behaviour across representative scenarios? |
| Evaluation type | Mixed-method |

### Evidence list

| Evidence item | What it demonstrates | Where it appears |
| --- | --- | --- |
| Test case: mild cold | LLM-led endpoint can return low-risk self-care and OTC support | Appendix / test evidence |
| Test case: chest pain + shortness of breath | Safety guardrails prevent under-escalation and force urgent escalation | Appendix / test evidence |
| Test case: knowledge retrieval | Local or NHS cards are surfaced | Appendix / retrieval evidence |
| Test case: route-aware ranking | Nearby care is ranked using route metrics | Appendix / facility evidence |
| Test case: chat fallback | Follow-up guidance remains safety-oriented | Appendix / chat evidence |
| Screenshot: initial symptom form | Realistic mobile user journey | Prototype appendix |
| Screenshot: assessment output | Actionable output structure | Prototype appendix |

### Ethical validation paragraph prompt

Write 4 to 6 sentences explaining:

- what evidence would convince a reviewer that your mitigation works
- why the evidence is sufficient for a prototype-stage project
- what still remains unvalidated

## Appendix G. Risk and Issue Log

| ID | Risk or issue | Type | Probability | Impact | Mitigation | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RL1 | LLM returns misleading or under-escalated triage | Technical / ethical | Medium | High | Constrain prompt, validate JSON, RAG-ground output, and enforce deterministic safety guardrails | Team | Open |
| RL2 | Local service details become outdated | Information quality | Medium | High | Cite official sources and review before submission/demo | Team | Open |
| RL3 | Route API unavailable | Technical | Medium | Medium | Use heuristic fallback | Team | Managed |
| RL4 | Prototype gathers more sensitive data than needed | Privacy | Low | High | Keep inputs minimal and location optional | Team | Managed |
| RL5 | Team evidence is incomplete near deadline | Project management | Medium | High | Maintain shared folder, weekly minutes, and named owners | Team | Open |

## Appendix H. Team Meeting Record Template

The brief requires at least five group meeting records. Use one copy of the structure below for each real meeting.

### Meeting record

- Meeting number:
- Date and time:
- Attendees:
- Apologies:
- Agenda:
- Decisions made:
- Actions agreed:
- Owners:
- Deadlines:
- Risks/issues raised:
- Evidence generated:

## Appendix I. Example Meeting Topics

Use these only as prompts if they reflect your real process:

1. Topic selection and Bournemouth problem definition
2. Requirements and scope agreement
3. Architecture choice and LLM strategy revision
4. Ethics, safeguarding, and signposting decisions
5. Evaluation planning and report integration

## Appendix J. Conflict Management Plan

Write a short paragraph or bullets covering:

- how the team allocates work
- how deadlines are tracked
- how missed work is escalated internally first
- when evidence is brought to the unit leader
- how disagreements are resolved using requirements, risks, and assessment criteria rather than opinion alone

Suggested points:

- assign named owners to tasks
- review progress weekly
- record non-completion and reallocation decisions
- resolve design disagreements by checking user need, safety, and rubric fit
- escalate persistent contribution issues early, with evidence

## Appendix K. Reflection Evidence Prompts

Use these to produce a stronger reflective section:

- What changed most between the earliest concept and Version 2?
- Which risk changed the architecture most?
- Which feature was deliberately simplified, and why?
- What did the team learn about balancing innovation with safety?
- What would be the next professional step before any real-world deployment?
