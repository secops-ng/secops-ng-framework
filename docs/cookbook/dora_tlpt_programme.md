# dora_tlpt_programme — cookbook walkthrough

Operator-side lifecycle of the DORA Chapter IV **digital operational
resilience testing (DORT) programme** a financial entity discharges
against its ICT risk-management framework — Article 24 (general
requirements for the testing of digital operational resilience) and
Article 26 (advanced testing of ICT tools, systems and processes based
on threat-led penetration testing), anchored on the ECB TIBER-EU
framework as the implementation reference. The
`playbook.dora_tlpt_programme@v1` CACAO playbook composes the
four-step operator-side lifecycle: on the mandatory-TLPT cadence
prescribed by the competent authority (per Art. 26(1) at least every
three years unless the competent authority prescribes otherwise), it
resolves the DORT-scope catalogue against the operator's declared
critical-or-important functions, evaluates the TLPT-mandatory
decision under the JC 2022 03 criteria and notifies the competent
authority, packages the red-team scoping submission for
competent-authority approval, and — after the red-team engagement
concludes — composes the findings register and emits the dated
competent-authority remediation attestation per Art. 26(8).

Distinct from the `dora_ict_risk_selfassess` playbook (whole-Chapter II
roll-up on the Art. 6(5) annual-review cadence) and from the per-section
producing playbooks (`crypto_posture_management`, `detection_engineering`,
`infra_posture_management`, etc. — the per-section surfaces the
Chapter II roll-up aggregates): this playbook is the **Chapter IV
testing-programme discipline**, keyed on the four programme-lifecycle
atoms the operator discharges on the mandatory-TLPT cadence against
the operator's designated critical-or-important functions.

The playbook is the **portable description of the DORT programme
discharge**. It does not designate functions as critical or important,
does not choose the operator's tier-of-significance under JC 2022 03,
does not select the red-team providers, does not author the
findings-register severity rubric, and does not schedule the
mandatory-TLPT cycle. It describes the workflow shape the operator's
stack should run so the four-step lifecycle (scope → trigger →
scoping-approval → remediation-attestation) is auditable, replayable,
and restart-safe — as a shipped Digital Commons artifact for the
financial-services community.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the DORT-scope
catalogue, the TLPT-mandatory decision, the competent-authority
scoping submission and approval, the findings register, and the
dated competent-authority remediation attestation land in each
target. The operator scenario carried through the walkthrough is a
**mandatory-TLPT cycle discharge** — the Art. 26(1) triennial cadence
against a financial entity the competent authority has identified as
in-scope under the JC 2022 03 criteria — with the not-mandatory
branch, the deferred / rejected scoping-approval branches, and the
post-major-incident ad-hoc trigger noted where they diverge.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Why this matters

DORA Chapter IV places the competent authority at the head of the
supervisory posture for the operator's digital operational resilience
testing programme. Article 24 fixes the general requirements — the
operator identifies the ICT-supported critical or important functions
in scope, the supporting ICT assets, and the ICT third-party
dependencies, and discharges a periodic testing programme against
them. Article 26 layers the advanced-testing surface on top: for
financial entities the competent authority identifies as in-scope
against the criteria the ESAs Joint Committee names in JC 2022 03,
threat-led penetration testing is **mandatory** on the cadence
Art. 26(1) prescribes (at least every three years), the scoping
submission is subject to competent-authority approval per Art. 26(3),
and the remediation-tracking output — the findings register and the
dated remediation attestation — is the audit-evident artifact
Art. 26(8) requires the operator to keep and to make available for
supervisory review.

An operator that runs the TLPT engagement itself but delivers the
scoping submission, the notification, and the remediation attestation
on best-effort — a slide deck the day before the supervisory review,
a spreadsheet threaded through email attachments — does not discharge
the write-side lifecycle Chapter IV names. The lifecycle is the
audit-evident thing: a dated scoping submission bound to a declared
scope catalogue, a competent-authority approval record, a findings
register keyed on the approved scoping id, and an attestation with a
remediation-status roll-up per finding against the operator's
declared severity thresholds.

This playbook is that lifecycle. Wiring the four-step programme into
an orchestration surface that survives worker restart, records every
step as durable evidence, and closes on a dated competent-authority
remediation attestation is the audit-evident discharge of the
Art. 24 / Art. 26 write-side obligation; running the programme
end-to-end on ad-hoc spreadsheets is not.

## 2. When to run the programme

Two run-triggers land in the operator's cadence configuration and
supply `__testing_window__` at lifecycle entry. The playbook does not
schedule itself; the operator's scheduler (a Temporal `Schedule`, a
governance cadence surface, or an ad-hoc supervisory trigger)
dispatches one workflow run per declared trigger.

- **Mandatory-TLPT cycle** (`__testing_window__=<cycle-id>`). Per DORA
  Art. 26(1), the mandatory-TLPT cycle runs at least every three
  years for financial entities the competent authority identifies as
  in-scope against the JC 2022 03 criteria (systemic-importance,
  ICT-substitutability, and the qualitative-and-quantitative
  thresholds the Joint Guidelines set out). This is the canonical
  scenario carried through this walkthrough: the operator's
  significance-tier evaluation returns a mandatory-TLPT decision at
  the trigger gate, the red-team scoping submission is dispatched to
  the competent authority for approval, the engagement concludes, and
  the dated remediation attestation lands on the operator's evidence
  store.
- **Ad-hoc supervisory trigger** (`__testing_window__=<trigger-id>`).
  The competent authority may prescribe an off-cycle TLPT engagement
  outside the triennial cadence — commonly post-major-incident
  (mirroring the Art. 6(5) post-major-incident review trigger on the
  read-side self-assessment lane), on a material change to the
  operator's critical-or-important-function catalogue, or on a
  cross-border supervisory-college request. The lifecycle shape is
  identical; only the trigger source and the declared cadence field
  on `__tlpt_trigger_decision__` change.

The not-mandatory branch — when the operator's tier-of-significance
evaluation at the trigger gate returns a not-mandatory outcome —
still emits a dated decision record naming the criteria evaluated so
the audit-evident chain is closed rather than silently
short-circuiting the programme. The audit-evident chain matters: a
supervisory reviewer must be able to see *the operator considered
TLPT for this window and recorded the reason the mandatory branch did
not apply*, not merely that no TLPT run happened.

## 3. Source of truth

```
content/playbooks/dora_tlpt_programme/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / DORA / NIS2 / GDPR overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.dora_tlpt_programme@v1)

content/mappings/dora/article-24-26.yaml
                                  # DORA Chapter IV inbound anchor — backlinks
                                  # playbook.dora_tlpt_programme@v1 on `playbook_refs`
                                  # (dora:art-24-26-dort-tlpt-programme)
content/mappings/nis2/article-21-2-f.yaml
                                  # NIS2 Art. 21(2)(f) inbound anchor — adjacent
                                  # effectiveness-testing lane, co-anchored with
                                  # detection_engineering + nis2_self_assessment
content/mappings/gdpr/article-32-security-of-processing.yaml
                                  # GDPR Art. 32(1)(d) inbound anchor — regular-
                                  # testing and effectiveness-evaluation limb
content/mappings/gdpr/data-flow-dora_tlpt_programme.md
                                  # per-workflow ROPA record (accountability-owner,
                                  # tester-roster, attestation-signatory attribution)
```

The CACAO source is canonical. The four action steps are the
deterministic lifecycle the playbook *means* — a linear chain through
scope definition, trigger-and-planning gate, red-team scoping
approval, and remediation tracking, with the per-branch outcome on
the trigger gate (mandatory / not-mandatory) and the
scoping-approval step (approved / deferred / rejected) recorded on
the action's `out_args` rather than routed via a CACAO
`if-condition` node, so the workflow topology stays a single audit
lane regardless of branch.

The three worked examples under
`examples/{n8n,temporal,langgraph}/dora_tlpt_programme/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the business-service register, the ICT-asset register, the ICT
third-party register, the competent-authority notification and
scoping-approval channels, the red-team engagement platform, the
findings-register store, and the evidence store — is the operator's
data plane.

## 4. CACAO topology and lifecycle binding

The playbook ships six steps: one `start`, four `action`, one `end`.
The chain is linear on the workflow edges; the per-branch selection
on the trigger gate (mandatory / not-mandatory) and the
scoping-approval step (approved / deferred / rejected) lives *inside*
each action's body rather than on a CACAO `if-condition` node, so the
workflow topology stays a single audit lane regardless of branch
outcome.

| Step suffix | Step                              | Discipline                                                                                                                                                                                                                                                                                                                     | Status         |
|-------------|-----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | start (`dora_tlpt_programme_start`) | edge wiring only — no body                                                                                                                                                                                                                                                                                                     | n/a            |
| `…000002`   | define DORT scope                 | read the operator's business-service register, ICT-asset register, and ICT third-party service-provider register; compose the DORT-scope catalogue for the current testing-programme window per Art. 24 (`__dort_scope_catalogue__`)                                                                                            | operator-bound |
| `…000003`   | TLPT trigger and planning gate    | evaluate the TLPT-mandatory decision under the JC 2022 03 criteria against the operator's declared `__entity_significance_tier__` per Art. 26(1); on the mandatory branch emit the competent-authority notification and record cadence + threat-intelligence source + tester-selection posture (`__tlpt_trigger_decision__`)  | operator-bound |
| `…000004`   | red-team scoping approval         | package the red-team scoping submission per Art. 26(3) against the JC RTS Art. 26 tester-selection criteria; dispatch to the competent authority; bind the approval / deferral / rejection outcome (`__red_team_scoping_id__`)                                                                                                  | operator-bound |
| `…000005`   | remediation tracking              | compose the findings register from the red-team engagement, bind each finding to a remediation timeline against the operator's declared severity rubric, and emit the dated competent-authority remediation attestation per Art. 26(8) (`__findings_register_id__`, `__remediation_attestation_id__`)                          | operator-bound |
| `…000006`   | end (`dora_tlpt_programme_end`)   | edge wiring only — no body                                                                                                                                                                                                                                                                                                     | n/a            |

All four action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control,
telemetry). One per-window execution emits exactly one dated
remediation attestation; the per-branch outcomes on the trigger gate
and the scoping-approval step never create a parallel evidence lane —
one window, one attestation, and one findings register keyed on the
approved scoping id.

> The playbook maturity is CORE on the workflow-local README (this
> EXTEND card lands with the cookbook walkthrough). All three
> reference emitters ship committed artifacts under
> `examples/{n8n,temporal,langgraph}/dora_tlpt_programme/` with
> deterministic stubs for the operator-bound seams; a sibling
> EXTEND card lands the adapter Protocols under
> `patterns.dora_tlpt_programme` (competent-authority notification
> adapter, competent-authority scoping-approval adapter, red-team
> engagement platform adapter, findings-register store, evidence
> store) alongside the TIBER-EU red-team choreography, the
> threat-intelligence-source binding, and the purple-team
> lessons-learned loop into `detection_engineering`.

## 5. Lifecycle contract — the four action states

The per-window payload — the DORT-scope catalogue (ICT-supported
critical or important functions, supporting ICT assets, ICT
third-party service providers in scope), the TLPT-mandatory decision
record (criteria evaluated against `__entity_significance_tier__`,
declared programme cadence, competent-authority notification
reference, threat-intelligence source, internal-versus-external
tester posture), the red-team scoping submission (scope statement
bound to `__dort_scope_catalogue__`, tester selection against the JC
RTS criteria, threat-intelligence source, rules of engagement, plus
the competent-authority approval / deferral / rejection outcome), the
findings register (per-finding id, severity, affected function,
affected ICT asset, evidence pointer, initial remediation timeline),
and the dated competent-authority remediation attestation — is
programme-governance content. Where an in-scope critical or important
function processes personal data, GDPR Art. 32(1)(d) attaches as a
parallel obligation surface on the regular-testing limb (see § 6).
The framework treats `__dort_scope_catalogue__`,
`__tlpt_trigger_decision__`, `__red_team_scoping_id__`,
`__findings_register_id__`, and `__remediation_attestation_id__` as
opaque operator-assigned identifiers.

**define DORT scope** (`…000002`)
:   Read step. Composes the DORT-scope catalogue for the current
    testing-programme window against the operator's business-service
    register, ICT-asset register, and ICT third-party service-provider
    register: the ICT-supported critical or important functions in
    scope, the supporting ICT assets pinned to each function, and the
    ICT third-party service providers whose services are in scope
    per DORA Art. 24. Sets `__dort_scope_catalogue__` to an
    operator-assigned identifier of the resolved catalogue so every
    downstream step reads against the same scope and drift between
    the trigger-gate submission and the red-team scoping submission
    is caught at the primitive boundary. Anchored on OSCAL CA-2
    (Control Assessments) — CA-2 requires the operator to develop,
    review, and approve a control-assessment plan against the scope
    of the system and its environment of operation, which is the
    upstream discipline the DORT-scope catalogue discharges at the
    head of the lifecycle. Read-only against the operator's declared
    registers: the primitive does not itself designate functions as
    critical or important — that is the operator's governance
    surface upstream (typically an ICT-risk-management-framework
    surface anchored on DORA Art. 8 identification and the
    per-section producing playbooks). Deliberately not D3FEND-pinned:
    D3FEND v1.0.0 does not carry a defensive technique for
    scope-catalogue composition against the operator's declared
    registers distinct from the downstream activity-mapping surface
    it feeds; the scope catalogue is the upstream of the
    operational-activity-mapping discipline rather than the mapping
    itself. Mirrors the sibling `dora_ict_risk_selfassess` overlay's
    per-step gap-note pattern.

**TLPT trigger and planning gate** (`…000003`)
:   Gate step. Evaluates whether threat-led penetration testing is
    mandatory for the operator in the current window against the
    criteria the ESAs Joint Committee names in JC 2022 03 and the
    operator's declared `__entity_significance_tier__` per DORA
    Art. 26(1). On the **mandatory branch** the primitive (a) emits
    the competent-authority notification against the adapter binding
    declared under `patterns.dora_tlpt_programme` (owned by the
    sibling EXTEND card), (b) records the declared programme cadence
    (per Art. 26(1) the mandatory TLPT cycle is at least every three
    years unless the competent authority prescribes otherwise),
    (c) binds the operator's declared threat-intelligence source
    (a TIBER-EU-aligned threat-intel provider, an ECB-recognised
    threat-intelligence-service provider, or the operator's internal
    threat-intelligence capability where the JC RTS criteria permit),
    and (d) records the internal-versus-external tester selection
    posture the scoping-approval step will bind against. On the
    **not-mandatory branch** the primitive still emits a dated
    decision record naming the criteria evaluated so the audit-evident
    chain is closed rather than silently short-circuiting the
    programme. Records `__tlpt_trigger_decision__`. Anchored on
    OSCAL CA-2. Deliberately not D3FEND-pinned: D3FEND v1.0.0 does
    not carry a defensive technique for mandatory-testing-decision
    governance distinct from the downstream engagement discipline
    it feeds — the JC 2022 03 criteria evaluation and the
    competent-authority notification are a compliance-governance
    surface, not a runtime countermeasure.

**red-team scoping approval** (`…000004`)
:   Gate step. Packages the red-team scoping submission per DORA
    Art. 26(3) with (a) a scope statement bound to
    `__dort_scope_catalogue__` (so the engagement never widens
    beyond the declared critical-or-important-function surface),
    (b) tester selection against the certification and independence
    criteria the JC RTS on ICT risk-management framework
    (Commission Delegated Regulation (EU) 2024/1774) Art. 26 names —
    for external testers the reputation, expertise, technical-and-
    organisational-standards, and professional-indemnity-insurance
    criteria; for internal testers the equivalent independence
    posture the JC RTS permits — (c) the declared threat-intelligence
    source resolved at the trigger gate, and (d) the operator's
    rules of engagement (target windows, exclusion lists, escalation
    contacts, kill-chain-stopping conditions). The submission
    package is dispatched to the competent authority against the
    adapter binding declared under `patterns.dora_tlpt_programme`;
    the primitive records the competent-authority response
    (approved / deferred / rejected) into `__red_team_scoping_id__`
    once the response is bound. On the **deferred / rejected**
    branches the primitive emits the response record and
    short-circuits the downstream engagement — the operator does
    not proceed with the red-team engagement without competent-
    authority approval on the scoping document. Anchored on OSCAL
    CA-2 (which absorbs CA-8 Penetration Testing on the
    effectiveness-testing slice per the mappings.yaml header note).
    Deliberately not D3FEND-pinned: D3FEND v1.0.0 does not carry a
    distinct threat-led-penetration-testing programme technique on
    either the Deceive or Isolate tactics that would capture the
    operator-side scoping-submission discipline; the closest
    candidate is on the offensive ATT&CK-adjacent side of the
    framework rather than on the defensive-technique catalogue
    this file pins. The OSCAL CA-2 surface carries the
    penetration-testing-scoping anchor, and the D3FEND surface
    picks up on the downstream remediation-tracking step where the
    defensive discipline actually applies.

**remediation tracking** (`…000005`)
:   Attestation step. Composes the findings register from the
    red-team engagement bound to `__red_team_scoping_id__`:
    per-finding record with id, severity against the operator's
    declared severity rubric, affected critical or important
    function, affected ICT asset, evidence pointer into the
    operator's evidence store, and initial remediation timeline.
    Sets `__findings_register_id__`. The primitive then composes
    the dated competent-authority remediation attestation per DORA
    Art. 26(8): remediation-status roll-up per finding, aggregated
    closure rate, remaining-open backlog against the declared
    severity thresholds, and the attestation timestamp. The
    attestation record is published to the operator's evidence
    store; the artifact_id is
    `SHA-256(workflow_id|execution_id|captured_at)` so
    `compile_target` does not enter the identifier and the three
    reference compilers re-derive byte-identical bytes from the
    same primitive output. Sets `__remediation_attestation_id__`.
    The primitive is idempotent per `(workflow_id, execution_id)`:
    re-running the remediation-tracking step against the same
    engagement produces the same artifact_id, updating the per-
    finding status roll-up in place rather than emitting a
    duplicate attestation. The attestation is always emitted —
    including the empty-findings-register branch (a clean red-team
    engagement records a zero-finding attestation rather than
    silently omitting the artifact) and including the
    deferred / rejected branches routed through
    `__red_team_scoping_id__` (the response record is the audit-
    evident artifact for that lane). Anchored on OSCAL CA-2 as
    the audit-evident report a supervisory reviewer reads against
    the declared testing-programme scope, and D3FEND-pinned to
    `D3-OAM` (Operational Activity Mapping) — mapping the red-team
    engagement findings onto the operator's declared severity
    rubric and remediation-timeline model IS the operational-
    activity-mapping discipline D3-OAM names. D3-OAM here names
    the write-side activity-mapping discipline (composing the
    operational-activity view from the engagement output),
    distinct from the read-side assessment framing the
    `dora_ict_risk_selfassess` overlay applied on the same
    technique — the two overlays anchor D3-OAM on adjacent but
    non-overlapping surfaces (read-side coverage-scoring vs
    write-side findings-mapping) and both are legitimate under the
    D3FEND technique definition.

The four action steps are operator-bound runtime seams: the
framework ships neither the business-service register, the
ICT-asset register, the ICT third-party register, the competent-
authority notification channel, the competent-authority scoping-
approval channel, the red-team engagement platform, the findings-
register store, nor the evidence store. The playbook is the
portable description of *what* the operator's stack should do on
each declared testing-programme window; binding those seams to
real endpoints is the operator's job.

> **LM determinism.** Scope-catalogue composition, TLPT-mandatory
> decision evaluation, competent-authority notification and
> scoping-approval dispatch, findings-register composition, and
> remediation-attestation emission are structured reads and writes
> against operator-owned surfaces, not free-text reasoning steps.
> The playbook binds no DSPy signature — there is no LM-driven
> step at this layer. See [`docs/FOUNDATION.md`](../FOUNDATION.md)
> § LLM determinism. If an operator wires an LM-driven summariser
> on top of the remediation-tracking step (rendering the per-
> finding record into a per-owner narrative, for instance) as a
> private extension, the framework-wide EU-resident LM endpoint
> guard re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 6. Regulatory anchors

**DORA Article 24** — General requirements for the testing of
digital operational resilience. Regulation (EU) 2022/2554 Art. 24
requires financial entities to establish, maintain, and review a
sound and comprehensive digital operational resilience testing
programme as an integral part of their ICT risk management
framework. The programme covers a full range of tests appropriate
to the size, complexity, and risk profile of the entity; identifies
the ICT-supported critical or important functions in scope, the
supporting ICT assets, and the ICT third-party dependencies; and
runs on a periodic cadence with the coverage review discipline the
JC RTS Art. 25 names as Level 2 detail. The
`dora_tlpt_programme` playbook is the operator-side lifecycle
materialisation of the Art. 24 general-requirements surface: the
scope-definition step composes the audit-evident DORT-scope
catalogue against the declared registers, the trigger gate
evaluates the periodic-cadence decision for the current window, and
the downstream steps discharge the specific-testing-methodology
slice on the Art. 26 advanced-testing branch. Article 25
(specific-methodology surface — vulnerability assessments,
scenario-based tests, compatibility testing, performance testing,
end-to-end testing, penetration testing) is deliberately not
anchored on this playbook: the per-methodology axis is absorbed
onto sibling per-methodology playbooks (`vuln_intake` for
vulnerability-assessment testing, `detection_engineering` for
detection-rule effectiveness testing, and so on) or lifted onto its
own SKELETON in a follow-on card. Inbound anchor at
[`content/mappings/dora/article-24-26.yaml`](../../content/mappings/dora/article-24-26.yaml)
(`dora:art-24-26-dort-tlpt-programme`) backlinks
`playbook.dora_tlpt_programme@v1` on `playbook_refs`.

**DORA Article 26** — Advanced testing of ICT tools, systems and
processes based on threat-led penetration testing. Art. 26(1)
requires in-scope financial entities to carry out at least every
three years advanced testing by means of TLPT, on a cadence the
competent authority may adjust for justified reasons based on the
entity's ICT risk profile. Art. 26(3) requires the operator to
submit the scoping documentation to the competent authority for
validation before the engagement proceeds. Art. 26(8) requires the
operator to keep, and to make available for supervisory review,
the summary of the relevant findings and the remediation plan
following the TLPT. The three primary axes of Art. 26 land on the
three write-side action steps: the trigger gate discharges the
Art. 26(1) mandatory-TLPT decision and cadence declaration; the
red-team scoping-approval step discharges the Art. 26(3)
competent-authority-approval gate; the remediation-tracking step
discharges the Art. 26(8) findings-and-remediation attestation
obligation. Article 27 (Requirements for testers for the carrying
out of TLPT) prescribes the tester-selection criteria the
scoping-approval step reads against; the Art. 27 criteria are
consumed at that step but Art. 27 is not lifted as a separate
top-level atom on the inbound mapping — the criteria are cited in
the mapping's notes body against `dora:art-24-26-dort-tlpt-programme`
rather than fanned out to a per-Article inbound file (a
single-clause child that only gates a step on this playbook does
not warrant a separate atom). Level 2 detail on the testing-
programme scope lives in the JC RTS on ICT risk-management
framework (Commission Delegated Regulation (EU) 2024/1774)
Articles 25 and 26; the **ECB TIBER-EU framework** is the
implementation reference the TLPT-lifecycle steps read against —
the operator's declared threat-intelligence source, the
red-team-engagement rules of engagement, and the internal-versus-
external tester posture all resolve against the TIBER-EU
choreography where the operator's competent authority has
adopted TIBER-EU as its national TLPT implementation reference.

**NIS2 Article 21(2)(f)** — policies and procedures to assess the
effectiveness of cybersecurity risk-management measures. NIS2
enforcement crossed on 2 July 2026; Art. 21(2)(f) sits alongside
the other Art. 21 measures on the operator's technical-and-
organisational-measures posture. NIS2 does not carry a direct
threat-led-penetration-testing programme obligation at the shape
of DORA Art. 26, but Art. 21(2)(f) is the adjacent
effectiveness-testing anchor and the TLPT programme is a
specialised form of effectiveness testing — competent-authority-
notified, cadenced against JC 2022 03, and discharged by an
independent red-team engagement against the operator's declared
critical or important functions. The audit-evident findings
register and dated remediation attestation the TLPT programme
emits are the same effectiveness-evidence shape Art. 21(2)(f)
requires operators to keep. Co-anchored with the sibling
`detection_engineering` playbook (detection-rule effectiveness
lane, per-rule-version effectiveness snapshots) and the sibling
`nis2_self_assessment` playbook (whole-Article-21 self-assessment
roll-up); this playbook adds the TLPT-effectiveness lane on top.
Inbound anchor at
[`content/mappings/nis2/article-21-2-f.yaml`](../../content/mappings/nis2/article-21-2-f.yaml)
(`nis2:art-21-2-f`).

**GDPR Article 32(1)(d)** — a process for regularly testing,
assessing, and evaluating the effectiveness of technical and
organisational measures for ensuring the security of the
processing. Where an in-scope critical or important function
under this lifecycle processes personal data, the TLPT programme
discharged on the mandatory-TLPT cycle prescribed by the competent
authority under DORA Art. 26(1) is a specialised form of that
regular-testing-and-effectiveness discipline for financial entities
in scope of both regimes — the same red-team engagement and its
findings-register / remediation-attestation output discharge the
periodic-testing limb of Art. 32(1)(d) alongside the DORA Art. 26(8)
remediation-tracking obligation. Co-anchored with the sibling
`detection_engineering`, `infra_posture_management`,
`backup_recovery`, `cyber_hygiene_training`, and
`nis2_self_assessment` playbooks already pinned on
`gdpr:art-32-1-d`; the six playbooks together cover the detection,
configuration-baseline, backup-restore, training-organisational-
measures, whole-NIS2-Article-21 self-assessment, and threat-led-
penetration-testing lanes of the regular-testing discipline.
Red-team engagement outputs may incidentally carry personal data
where an in-scope function processes personal data; that
discharge is on the producing surface (the in-scope function's own
playbook and its own data-flow record), not on this testing-
programme lifecycle. The per-workflow GDPR data-flow record at
[`content/mappings/gdpr/data-flow-dora_tlpt_programme.md`](../../content/mappings/gdpr/data-flow-dora_tlpt_programme.md)
remains authoritative for the per-workflow ROPA surface
(accountability-owner attribution, tester-roster attribution,
attestation-signatory attribution). Inbound anchor at
[`content/mappings/gdpr/article-32-security-of-processing.yaml`](../../content/mappings/gdpr/article-32-security-of-processing.yaml)
(`gdpr:art-32-1-d-regular-testing-and-effectiveness`).

**CRA (deferred, reviewed skip).** No CRA inbound entry currently
backlinks `playbook.dora_tlpt_programme@v1`, and this is a durable,
reviewed deferral rather than an open TODO. CRA Annex I is
product-by-product manufacturer scope; the operator-side TLPT
programme discipline is regime-specific to financial entities under
DORA and does not cross-map onto the CRA product-lifecycle surface.
The CRA clause-by-clause review is recorded under the
`dora_tlpt_programme` entry in
`content/mappings/cra/_orphan_skip.yaml`. Mirrors the sibling
`dora_ict_risk_selfassess` CRA-axis precedent.

**EU AI Act (deferred, reviewed skip).** No EU AI Act inbound entry
currently backlinks `playbook.dora_tlpt_programme@v1`, and this is
a durable, reviewed deferral rather than an open TODO. EU AI Act
Art. 15 (accuracy / robustness / cybersecurity) is the closest
neighbouring testing-discipline anchor, but is a product-lifecycle
obligation on providers of high-risk AI systems rather than an
operator-side TLPT programme obligation. The clause-by-clause
review is recorded under the `dora_tlpt_programme` entry in
`content/mappings/eu_ai_act/_orphan_skip.yaml`.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/dora_tlpt_programme/mappings.yaml`](../../content/playbooks/dora_tlpt_programme/mappings.yaml)):
CA-2 (Control Assessments — anchors the playbook end-to-end as the
control-assessment capability against the operator's ICT
operations) and CA-8 (Penetration Testing — absorbed into the
`control.control_effectiveness_test@v1` overlay on the effectiveness-
testing slice; the effectiveness-testing overlay carries the
penetration-testing-scoping anchor on the red-team-scoping-approval
and remediation-tracking steps). The header note in `mappings.yaml`
records the CA-8-absorbed-into-CA-2 choice and the reviewer-selectable
path to lift CA-8 onto its own control overlay in a follow-on
sibling card without changing the outbound-edge graph. CA-7
(Continuous Monitoring) is deliberately NOT pinned: the TLPT
programme is a cadenced, competent-authority-gated engagement
discipline rather than a continuous-monitoring discipline —
continuous monitoring lives on the `dora_ict_risk_selfassess` and
F-CP-06 effectiveness-loop surfaces, and pinning CA-7 here would
misrepresent the mandatory-TLPT-cycle rhythm.

**MITRE D3FEND v1.0.0** — `D3-OAM` (Operational Activity Mapping)
at `remediation tracking`. The Model tactic in D3FEND v1.0.0
carries the write-side activity-mapping discipline this playbook
operates on the findings-mapping surface: mapping the red-team
engagement findings onto the operator's declared severity rubric
and remediation-timeline model IS the operational-activity-mapping
discipline D3-OAM names. The read-side sibling
`dora_ict_risk_selfassess` overlay pins D3-OAM on the read-side
coverage-scoring surface; the write-side lane here pins D3-OAM on
the write-side findings-mapping surface — the two overlays anchor
D3-OAM on adjacent but non-overlapping surfaces and both are
legitimate under the D3FEND technique definition. The
`define_dort_scope`, `tlpt_trigger_and_planning_gate`, and
`red_team_scoping_approval` steps are deliberately NOT
D3FEND-pinned, with per-step gap notes in `mappings.yaml` (scope-
catalogue composition, mandatory-testing-decision governance, and
penetration-testing-scoping-submission disciplines respectively).
This closure mirrors the sibling `dora_ict_risk_selfassess`
overlay's pin-where-it-fits / document-the-gap pattern.

**OCSF v1.3.0** — `API Activity` (class_uid 6003, category 6
Application Activity), direction `both`, consumed at
`define DORT scope` (read calls against the operator's business-
service register, ICT-asset register, and ICT third-party register),
consumed and emitted at `TLPT trigger and planning gate` (reads
against the declared `__entity_significance_tier__` and the JC 2022
03 criteria model; emits the competent-authority notification
against the adapter binding under `patterns.dora_tlpt_programme`),
consumed and emitted at `red-team scoping approval` (packages the
scoping submission and dispatches to the competent-authority
approval channel; records the approval or deferral outcome), and
emitted at `remediation tracking` (write call publishing the dated
competent-authority remediation attestation record to the
operator's evidence store). The class_uid 6003 binding is
intentional at CORE tier — API Activity is the OCSF v1.3.0
consistent class across the write-side and evidence-side surfaces
this playbook interacts with; richer per-step telemetry bindings
(e.g. OCSF Compliance Finding 2003 on the remediation-status
roll-up) are deferred to a sibling EXTEND revisit once stable
upstream signal shapes are selected.

## 7. Per-target hand-off

### 7.1 n8n — operator-edited Set rows over the lifecycle topology

`examples/n8n/dora_tlpt_programme/workflow.n8n.json` carries the
CACAO topology as six n8n nodes (one `manualTrigger`, four `set`
nodes, one `noOp`), with node ids preserving the CACAO step ids
verbatim. The four action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles. The per-branch selection on the
trigger gate (mandatory / not-mandatory) and the scoping-approval
step (approved / deferred / rejected) lives inside each Set row's
assignments rather than fanning out as downstream
`n8n-nodes-base.if` nodes — the row carries every branch's
`out_args` shape so the operator wires whichever branch the trigger
window resolves to against `__tlpt_trigger_decision__` and
`__red_team_scoping_id__`. The lossy translation is recorded in
`meta.secops_ng_notes` so the integrator sees exactly which seams
need attention.

Operators bind the Set rows to their connectors — worked against the
mandatory-TLPT-cycle scenario carried through this walkthrough:

- `define DORT scope` → the operator's business-service register,
  ICT-asset register, and ICT third-party service-provider register
  (a CMDB, an ICT-risk-management-framework surface, a governance
  policy store, or the read-side sibling registers the
  `dora_ict_risk_selfassess` roll-up already consumes); the Set row
  records `__dort_scope_catalogue__` — the resolved catalogue every
  downstream step reads against.
- `TLPT trigger and planning gate` → the operator's competent-
  authority notification channel (a secure supervisory
  correspondence surface, a national-competent-authority portal
  where TIBER-EU is the national implementation reference, or the
  operator's governance mailbox where the competent authority
  accepts email notification); the Set row records
  `__tlpt_trigger_decision__` with the mandatory branch selected,
  the declared programme cadence (Art. 26(1) triennial by default,
  or the competent-authority-prescribed cadence if adjusted), the
  competent-authority notification reference, the declared
  threat-intelligence source, and the internal-versus-external
  tester-selection posture. The not-mandatory branch records the
  same shape with the not-mandatory outcome and the criteria
  evaluation that led there — the audit-evident record is emitted
  either way.
- `red-team scoping approval` → the operator's competent-authority
  scoping-approval channel (the same supervisory-correspondence
  surface used at the trigger gate, or a dedicated TIBER-EU
  scoping-submission portal where applicable); the Set row records
  `__red_team_scoping_id__` with the packaged scoping submission
  (scope statement bound to `__dort_scope_catalogue__`, tester
  selection against the JC RTS Art. 26 criteria, threat-intelligence
  source resolved at the trigger gate, and the rules of engagement)
  plus the competent-authority response (approved / deferred /
  rejected). On the deferred / rejected branch the downstream
  remediation-tracking step still records the response as the
  audit-evident artifact for that lane.
- `remediation tracking` → the operator's red-team engagement
  platform (for the findings-register composition) and the
  operator's evidence store (for the remediation attestation); the
  Set row records `__findings_register_id__` (per-finding id,
  severity, affected function, affected ICT asset, evidence pointer,
  initial remediation timeline) and `__remediation_attestation_id__`
  (the dated competent-authority attestation with the remediation-
  status roll-up per finding and the aggregated closure rate).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/dora_tlpt_programme/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/dora_tlpt_programme/workflow.n8n.json`. The workflow
is inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 7.2 Temporal — `@activity.defn` bodies

`examples/temporal/dora_tlpt_programme/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the four action
activities documenting their operator-bound seam (business-service
/ ICT-asset / ICT third-party register reads at the scope step,
competent-authority notification dispatch at the trigger gate,
competent-authority scoping-approval dispatch at the scoping-
approval step, red-team-engagement findings-register composition
plus evidence-store attestation emission at the remediation-
tracking step). Each activity documents the canonicalisation and
validation contract; the operator wires the surrounding data-plane
call inside the activity body.

Temporal is the natural fit for the mandatory-TLPT-cycle scenario:
each declared testing-programme window becomes one workflow run;
the Art. 26(1) triennial cadence can be realised as a Temporal
`Schedule` that fires the workflow on the operator's declared
cadence without a bespoke cron surface; retries against transient
failures on the competent-authority channel, the red-team engagement
platform, or the evidence store get first-class Temporal semantics
(activity retry policy per seam, with the notification and
scoping-approval dispatch idempotency keyed on
`(workflow_id, execution_id, step_id)` so a re-drive does not
double-notify the competent authority); replay against the same
Temporal event history re-derives the same DORT-scope catalogue,
the same trigger decision, the same scoping-approval record, and
the same remediation attestation once the activity bodies are wired
against deterministic seams. The ad-hoc-supervisory-trigger
scenario is a separate schedule (or an event-signal into a
long-running parent workflow); the workflow code the compiler emits
stays pure — every non-deterministic boundary lives on the activity
side of the `@activity.defn` line, so replay determinism survives
the operator's own activity implementations. The
remediation-tracking activity's idempotency (per
`(workflow_id, execution_id)`) is the Temporal-native realisation
of the "one window, one attestation" property the playbook contract
requires.

### 7.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/dora_tlpt_programme/state_bindings.py` carries
the `TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes and
the linear on-completion edges from define-DORT-scope through
remediation-tracking to the terminal end, with the internal
per-branch selection on the trigger gate and the scoping-approval
step recorded as state fields rather than conditional edges);
`assemble.py` is the hand-written reference assembly that wires the
GraphSpec + bindings into a `langgraph.graph.StateGraph`.
`_audit_mirror.py` is the dependency-free audit-mirror sibling (see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)).

LangGraph is the agentic target — an operator who wants to layer
an LM-driven enrichment on top of the remediation-tracking step
(rendering the per-finding record into a per-owner narrative, a
purple-team debrief note for the sibling `detection_engineering`
lane, or an executive-summary of the attestation for the
management-body reporting surface) fills that as a private
extension. The framework-wide EU-resident LM endpoint guard
re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK. The purple-team lessons-
learned loop — where findings from the red-team engagement seed
new detection rules on the sibling `detection_engineering` lane —
is called out as a candidate LangGraph extension on the sibling
EXTEND card, not on the CORE compile-target artifact.

### 7.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/dora_tlpt_programme/`,
`examples/temporal/dora_tlpt_programme/`,
`examples/langgraph/dora_tlpt_programme/`). Each ships a committed
emitter artifact (n8n workflow JSON, Temporal worker module,
LangGraph GraphSpec + bindings) with the action bodies documenting
the operator-bound seam and the CACAO I/O contract. The per-target
byte-parity goldens under
`tests/examples/{n8n,temporal,langgraph}/dora_tlpt_programme/` pin
each per-target artifact against a fresh emitter run from the
canonical CACAO source — the cross-target byte-parity property the
framework relies on.

## 8. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the
operator-bound seam call or the primitive body. The mirror runs
unconditionally, ahead of any OTLP exporter, so the audit property
holds even when the operator has not configured a collector —
typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are
stable across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--55d0e1f2-…`).          |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--55000000-…`).                |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at
  workflow entry; activity span (`activity.<step_id>`) on every
  activity body, with retries opening a fresh child span per
  Temporal attempt (so a notification-dispatch retry against a
  transient competent-authority-channel failure is auditable as
  its own span rather than collapsed into the parent).
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The audit envelope carried per action step names the four
operator-bound seams explicitly: the DORT-scope catalogue on step
002, the TLPT-mandatory decision plus competent-authority
notification reference on step 003, the scoping-submission and
competent-authority approval outcome on step 004, and the findings
register plus remediation attestation on step 005. The
`__dort_scope_catalogue__` correlation key threads through every
record so a reviewer can join the full write-side lifecycle into a
single reportable-window ledger, and the `(__tlpt_trigger_decision__,
__red_team_scoping_id__, __remediation_attestation_id__)` tuple is
the audit-evident chain a supervisory reviewer diffs to confirm the
Art. 26(1) / Art. 26(3) / Art. 26(8) discharge across the window.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
and never imports a vendor SDK; pointing the exporter at a managed
APM is a downstream choice the operator owns end-to-end. The
sovereignty posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline. Where the operator's competent authority has
adopted TIBER-EU as its national TLPT implementation reference,
the same audit-trail envelope also serves the TIBER-EU test-manager
review posture — the JSONL replay is a superset of the
correspondence surface a TIBER Cyber Team reads against.

## 9. Operator customisation points

The playbook is a write-side lifecycle machine; the *programme* it
discharges is the operator's. The customisation seams:

- **Register sources.** The `define DORT scope` step reads the
  operator's business-service register, ICT-asset register, and
  ICT third-party service-provider register from wherever they
  live (a CMDB, an ICT-risk-management-framework surface, a
  governance policy store, the read-side sibling registers the
  `dora_ict_risk_selfassess` roll-up already consumes). The
  framework binds no register source; the operator's governance
  topology decides where the registers live and how the
  scope-definition step reads them.
- **Competent-authority correspondence surfaces.** The trigger-
  gate and scoping-approval steps dispatch against the operator's
  competent-authority notification and scoping-approval channels.
  Where the operator's competent authority has adopted TIBER-EU
  as its national TLPT implementation reference, the TIBER-EU
  correspondence surface (test-manager notification, scoping-
  document exchange) is the natural adapter target; where the
  competent authority runs its own portal or accepts email
  correspondence, the operator's own surface binds instead. The
  adapter Protocols under `patterns.dora_tlpt_programme` land on
  the sibling EXTEND card.
- **Threat-intelligence source.** The trigger gate records the
  operator's declared threat-intelligence source (a TIBER-EU-
  aligned threat-intel provider, an ECB-recognised threat-
  intelligence-service provider, or the operator's internal
  threat-intelligence capability where the JC RTS criteria
  permit). The framework binds no threat-intelligence source; the
  operator's declared provider — bounded by the JC RTS Art. 26
  criteria and, where TIBER-EU applies, by the TIBER-EU
  threat-intelligence-provider criteria — decides.
- **Tester selection.** The scoping-approval step packages the
  tester selection (internal or external) against the JC RTS
  Art. 26 criteria. For external testers the reputation,
  expertise, technical-and-organisational-standards, and
  professional-indemnity-insurance criteria apply; for internal
  testers the equivalent independence posture the JC RTS permits
  applies. The framework binds no tester-selection surface; the
  operator's declared roster and the competent authority's
  approval on it decide.
- **Findings-register severity rubric.** The remediation-tracking
  step composes the findings register against the operator's
  declared severity rubric (critical / high / medium / low, or an
  operator-specific finer-grained rubric). The framework binds no
  rubric; the operator's declared severity model, bounded by the
  supervisory-severity posture the competent authority reads
  against, decides.
- **Evidence-store retention.** The remediation-tracking step
  publishes the dated attestation to the operator's evidence
  store; the retention discipline (per-record TTL, immutability
  posture, regulator-query response SLA) is operator-defined and
  documented in the operator's governance surface upstream of
  this workflow. Bounded by the DORA Art. 12 backup-and-retention
  discipline and by the general audit-retention practice
  applicable to the operator's competent authority.

## 10. Replay and audit story

The byte-parity drift guards land under
`tests/examples/{n8n,temporal,langgraph}/dora_tlpt_programme/`.
Each per-target golden pins the committed worked-example artifact
to a fresh emitter run from the canonical CACAO source; if the
compiler or the playbook changes, regenerate via the per-target
`regenerate.sh` and commit the diff intentionally.

The cross-target replay property is the harder one: the same
declared testing-programme window, fed through n8n / Temporal /
LangGraph, produces a byte-identical dated competent-authority
remediation attestation and a byte-identical findings register
once each target's activity / tool bodies are wired against the
same operator seams and the same OSCAL / OCSF / D3FEND reference
bundles. The `(__dort_scope_catalogue__, __tlpt_trigger_decision__,
__red_team_scoping_id__, __findings_register_id__,
__remediation_attestation_id__)` tuple is the string a supervisory
reviewer can diff to confirm the property holds across targets,
and the `__dort_scope_catalogue__` correlation key is the join
column that threads through every audit record from scope
resolution to attestation.

The remediation-tracking step is deliberately idempotent per
`(workflow_id, execution_id)`: a re-drive against a partially
completed window updates the per-finding remediation-status roll-up
in place rather than emitting a duplicate attestation. That
property matters at Art. 26(8) audit time — the competent authority
reads a single dated attestation per window, not a chain of
re-emissions that shift the closure-rate arithmetic between
readings.

## 11. Playbook chain — where dora_tlpt_programme sits

The DORA-testing chain expresses itself as one write-side lifecycle
programme playbook (this one) that sits alongside the read-side
Chapter II roll-up and the per-section producing playbooks the
roll-up aggregates, and hands purple-team learnings into the
detection-engineering effectiveness lane:

```
dora_tlpt_programme  (Chapter IV testing-programme write-side lifecycle —
                       DORT scope, TLPT trigger gate, scoping approval,
                       findings register + dated remediation attestation)
    └── scoping submission ─► competent-authority approval channel (Art. 26(3))
    └── remediation attestation ─► operator's evidence store (Art. 26(8))
    └── purple-team learnings ─► detection_engineering
                                    ▲
                                    │ feeds effectiveness snapshots into
                                    │
dora_ict_risk_selfassess  (whole-Chapter II read-side roll-up on the
                            Art. 6(5) annual-review cadence)
    └── dated self-assessment attestation ─► operator's evidence store
```

- **Sibling: `dora_ict_risk_selfassess`.** The whole-Chapter II
  read-side roll-up. The read-side playbook aggregates per-section
  evidence from the five Chapter II section atoms (Arts. 6, 7, 8,
  10, 11) into one dated self-assessment attestation on the
  Art. 6(5) annual-review cadence; this playbook operates the
  Chapter IV testing-programme write-side lifecycle on the
  mandatory-TLPT cadence prescribed by the competent authority.
  Both playbooks anchor DORA obligations but on different chapters
  and different cadences — pinning both under one roof gives the
  supervisory reviewer the whole-ICT-risk-management-framework
  posture (Chapter II) plus the advanced-testing-programme posture
  (Chapter IV) in coherent audit-evident form. See
  [`docs/cookbook/dora_ict_risk_selfassess.md`](./dora_ict_risk_selfassess.md).
- **Adjacent: `detection_engineering`.** The detection-rule
  effectiveness lane. Findings from the red-team engagement that
  expose detection-coverage gaps (missing detection rules,
  low-fidelity rules, false-negative windows on the operator's
  detection surface) feed the `detection_engineering` playbook as
  purple-team learnings — the operator's detection engineers
  author new Sigma rules or refine existing ones against the
  gap surface the red-team engagement uncovered. This playbook
  is the write-side counterpart on the operator's testing-
  programme cadence; the detection lane operates on its own
  per-rule-version effectiveness snapshots. See
  [`docs/cookbook/detection_engineering.md`](./detection_engineering.md).
- **Adjacent: per-section producing playbooks.** The
  `crypto_posture_management`, `infra_posture_management`,
  `iam_auditor`, `backup_recovery`, `vuln_intake`, etc. playbooks
  discharge the per-section Chapter II obligations the
  `dora_ict_risk_selfassess` roll-up aggregates; some of them
  (`infra_posture_management`, `backup_recovery`) share the
  GDPR Art. 32(1)(d) regular-testing anchor with this playbook and
  co-anchor the effectiveness-testing lane from their own axes.

The chain is not code-coupled — each playbook is a standalone
CACAO artifact that can be run in isolation — but the audit
trail's coherence across the workflows is the sovereign-security
property the framework guarantees.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for
  the register sources, the competent-authority correspondence
  channels, the red-team engagement platform, the findings-
  register store, or the evidence store. Connectors are
  operator-bound at runtime against environment variables
  documented per target.
- **Function designation.** The playbook operates the write-side
  lifecycle discipline; it does not itself designate functions as
  critical or important. Designation is the operator's governance
  concern upstream (typically an ICT-risk-management-framework
  surface anchored on DORA Art. 8 identification), bounded by the
  competent authority's supervisory posture and by the sibling
  `dora_ict_risk_selfassess` roll-up's Chapter II framing.
- **Tier-of-significance evaluation.** The playbook consumes the
  operator's declared `__entity_significance_tier__` at the
  trigger gate; the underlying evaluation against the JC 2022 03
  criteria (systemic-importance, ICT-substitutability, and the
  qualitative-and-quantitative thresholds the Joint Guidelines set
  out) is the operator's governance discipline upstream. The
  competent authority is the ultimate arbiter of the operator's
  in-scope status under Art. 26(1); the operator's self-declared
  tier is the input the trigger gate reads, not a substitute for
  competent-authority identification.
- **Adapter Protocols under `patterns.dora_tlpt_programme`.**
  Competent-authority notification adapter, competent-authority
  scoping-approval adapter, red-team engagement platform adapter,
  findings-register store, and evidence-store adapter Protocols
  land on a sibling EXTEND card. The CORE tier ships
  deterministic emitter output with documented seams; the adapter
  binding lands next.
- **TIBER-EU red-team choreography.** The end-to-end TIBER-EU
  choreography (Generic Threat Landscape resolution, targeted
  threat-intelligence report, red-team-scenario authoring, TIBER
  Cyber Team liaison, blue-team engagement rules, purple-team
  replay session) is a candidate advanced-feature slice on the
  sibling EXTEND card. The current CORE lifecycle names the
  TIBER-EU choreography as the implementation reference the
  Art. 26 lifecycle reads against without prescribing the full
  choreography sequence — that stays on the sibling card.
- **Threat-intelligence-source binding.** The declared
  threat-intelligence source is recorded on
  `__tlpt_trigger_decision__` but the operator's binding to a
  specific TI provider (a TIBER-EU-aligned provider, an
  ECB-recognised TIS provider, or the operator's internal TI
  capability) is not pinned by the framework — the JC RTS
  Art. 26 criteria bound the operator's choice.
- **Purple-team lessons-learned loop into
  `detection_engineering`.** The write-side purple-team debrief
  where findings feed the sibling detection-engineering lane is
  documented as the chain relationship in § 11, but the
  operational replay session (blue-team walk-through, detection-
  rule authoring, effectiveness-snapshot regeneration) lives on
  the sibling EXTEND card and on the `detection_engineering`
  playbook itself.
- **Article 25 specific-methodology testing.** Vulnerability
  assessments, scenario-based tests, compatibility testing,
  performance testing, end-to-end testing, and (non-TLPT)
  penetration testing per DORA Art. 25 are absorbed onto sibling
  per-methodology playbooks (`vuln_intake` for vulnerability-
  assessment testing, `detection_engineering` for detection-rule
  effectiveness testing, and so on) or a follow-on SKELETON card,
  not on this playbook.
- **Article 27 detailed tester-requirements register.** The
  tester-selection criteria are consumed at the scoping-approval
  step and cited in the inbound-mapping notes body; a per-tester
  register (roster CVs, certification evidence, insurance
  certificates) is the operator's HR / procurement surface
  upstream and is not authored by this playbook.
- **OCSF Compliance Finding 2003 binding.** The remediation-
  tracking step currently pins the OCSF API Activity class only;
  richer per-step telemetry bindings (OCSF Compliance Finding
  2003 on the remediation-status roll-up, per-severity finding
  events on the composition surface) are deferred to a sibling
  EXTEND revisit once stable upstream signal shapes are selected.

## 13. References

- [`content/playbooks/dora_tlpt_programme/README.md`](../../content/playbooks/dora_tlpt_programme/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/dora_tlpt_programme/mappings.yaml`](../../content/playbooks/dora_tlpt_programme/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / DORA / NIS2 / GDPR overlay
  with per-step control anchors and the in-line closure notes for
  the deliberate OSCAL / D3FEND / CRA / EU AI Act omissions.
- [`content/mappings/dora/article-24-26.yaml`](../../content/mappings/dora/article-24-26.yaml)
  — DORA Chapter IV inbound anchor (`dora:art-24-26-dort-tlpt-programme`).
- [`content/mappings/nis2/article-21-2-f.yaml`](../../content/mappings/nis2/article-21-2-f.yaml)
  — NIS2 Article 21(2)(f) inbound anchor (adjacent effectiveness-
  testing lane; co-anchored with sibling `detection_engineering`
  and `nis2_self_assessment` playbooks).
- [`content/mappings/gdpr/article-32-security-of-processing.yaml`](../../content/mappings/gdpr/article-32-security-of-processing.yaml)
  — GDPR Article 32(1)(d) inbound anchor (regular-testing and
  effectiveness-evaluation limb).
- [`content/mappings/gdpr/data-flow-dora_tlpt_programme.md`](../../content/mappings/gdpr/data-flow-dora_tlpt_programme.md)
  — per-workflow GDPR data-flow record (accountability-owner,
  tester-roster, attestation-signatory attribution).
- [`docs/cookbook/dora_ict_risk_selfassess.md`](dora_ict_risk_selfassess.md)
  — sibling Chapter II read-side roll-up cookbook (whole-Chapter II
  self-assessment lane; the two playbooks together give the
  supervisory reviewer the whole-ICT-risk-management-framework
  posture plus the advanced-testing-programme posture).
- [`docs/cookbook/detection_engineering.md`](detection_engineering.md)
  — adjacent cookbook (detection-rule effectiveness lane; the
  write-side purple-team lessons-learned loop feeds this playbook
  as candidate detection-coverage improvements).
- [`examples/n8n/dora_tlpt_programme/README.md`](../../examples/n8n/dora_tlpt_programme/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/dora_tlpt_programme/README.md`](../../examples/temporal/dora_tlpt_programme/README.md)
  — Temporal worked-example walkthrough.
- [`examples/langgraph/dora_tlpt_programme/README.md`](../../examples/langgraph/dora_tlpt_programme/README.md)
  — LangGraph worked-example walkthrough.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay
  shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer
  runtime.
