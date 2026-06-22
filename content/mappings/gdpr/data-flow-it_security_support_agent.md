# GDPR data flow — it_security_support_agent

Per-workflow GDPR data-flow entry for the `it_security_support_agent`
cookbook playbook (`playbook.it_security_support_agent@v1`). Filled
in against [`_data-flow-template.md`](./_data-flow-template.md).
Together the seven sections below form the Art. 30 Record of
Processing Activity entry for this workflow.

Workflow source of truth:
[`content/playbooks/it_security_support_agent/`](../../playbooks/it_security_support_agent/).

---

## 1. Purpose

The workflow exists to handle one operator-supplied IT and security
support request per execution: ingest the request from the operator's
ticketing source, classify it (informational / actionable /
incident-shaped), attempt the declared automated-resolution path
against the operator's self-service surface, and either close the
interaction on a successful automated resolution OR escalate to a
human responder via an explicit, first-class handoff step. The
workflow then emits one interaction-evidence artifact pinning the
request, the classification, the automated-resolution outcome, and
the human-handoff envelope (whether or not a handoff fired). The
purpose is bounded to producing that per-interaction front-line
evidence so an operator can satisfy NIS2 Art. 21(2)(b) incident-
handling-capability obligations on the support-to-incident entry
path; the workflow does not retain support telemetry for analytics,
profiling, or model training, and it does not silently auto-close
support interactions.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(c) — legal obligation**. Where the operator
is a regulated entity under the **NIS2 Directive** and is obliged to
operate an incident-handling capability — detect, triage, contain,
remediate, capture lessons — under **NIS2 Art. 21(2)(b)** as
transposed nationally, the per-interaction support-handoff evidence
this workflow produces is processed to discharge the front-line entry
into that obligation. Operators under sector-specific rules
(DORA ICT-incident-management obligations for financial entities)
inherit the same primary basis.

Secondary: **GDPR Art. 6(1)(f) — legitimate interests**. An operator
not within scope of a statutory incident-handling-capability
obligation still has a legitimate interest in continuously evidencing
that support interactions are either resolved on the declared
self-service surface or handed off to a human responder rather than
silently auto-closed; the processing here — ingesting one request,
classifying it, attempting an automated resolution, and materialising
the closed handoff envelope — is necessary and proportionate to that
interest.

The requester handle this workflow processes and the responder-queue
handle the workflow acknowledges against are operator-supplied and
**role-shaped by design** — a queue handle, a rota id, a workload
identity, or an automation responder role (see §3). For
support interactions invoked against a non-personal service or
workload identity on both sides, no personal data is processed and
GDPR does not engage. The sections below score the worst case: a
support interaction whose requester is attributable to a natural
person (an employee, a customer, a contractor opening a ticket
against the operator's helpdesk).

Special-category data (Art. 9) is not the target of the workflow and
is not read or persisted; the support-request record, the
classification verdict, the automated-resolution observation
envelope, and the human-handoff envelope as enumerated in §3 do not
carry Art. 9 attributes by design.

## 3. Categories of data subjects and personal data

Data subjects (only where the requester or responder handle is
attributable to a natural person; non-personal service / workload
identities fall outside GDPR scope):

- **The requester** — the employee, customer, contractor, or
  workload-identity owner who opened the support request the
  workflow is processing on this execution, where such attribution
  exists. This is the central data subject for the workflow.
- **The human responder** — the on-call shift or rota member that
  the handoff envelope routes to, where the operator-bound
  responder-queue handle is attributable to a natural person.

Categories of personal data:

- **Requester identifiers** — the requester reference carried by
  `__support_request_record_ref__` (mailbox handle, ticket
  submitter id, workload-identity caller). Personal only to the
  extent the operator's ticketing store maps the handle to a
  natural person.
- **Request metadata** — the `request_kind`
  (informational / actionable / incident-shaped), the declared
  symptom string, and the `received_at` timestamp carried by
  `__support_request_record_ref__`. Free-text symptom payloads are
  bounded by the operator's helpdesk inbox policy; the workflow
  does not solicit additional content beyond what the source
  request already carries.
- **Classification metadata** — the closed `category`, severity
  band, and ordered `rule_ids` carried by `__classification_ref__`.
  Triage metadata, not content; personal data only via the
  attributable-requester join.
- **Automated-resolution observation envelope** — the `outcome`
  (resolved / partial / not_attempted / failed) and observed state
  carried by `__automated_resolution_ref__`. Operational metadata,
  not content; personal data only via the attributable-requester
  join.
- **Human-handoff envelope** — the role-shaped responder-queue
  handle, the `handoff_fired` flag, the trigger reason, and the
  acknowledgement reference carried by `__human_handoff_ref__`.
  Routing metadata; personal data only where the queue handle is
  attributable to a named individual.
- **Execution metadata** — the per-execution identifier
  (`__execution_id__`) issued by the compile target's runtime (n8n
  execution id, Temporal workflow run id, LangGraph thread/checkpoint
  id) and the `captured_at` timestamp carried on the emitted
  interaction-evidence artifact.

No credential material, factor secret, token plaintext, or raw
ticket attachment is read or persisted by the workflow; the workflow
processes references and closed envelopes only, projected through
`telemetry.ocsf.api_activity@v1`.

## 4. Recipients

Internal recipients:

- The **incident-response / on-call function** receiving the
  human handoff — the operator's IR and helpdesk leads who consume
  the interaction-evidence artifacts to evidence that support
  interactions are either resolved on the declared self-service
  surface or handed off explicitly, and to drive the F-WF-05
  incident-management lifecycle on the incident-shaped sub-flow.
- The **metrics layer** consuming the automated-resolution-rate
  KPI and handoff-acknowledgement-time KRI surface — once the
  EXTEND-metrics sibling lands (no metric_refs are pinned at the
  SKELETON layer). The recipient is the aggregated counter, not
  the per-requester identifier.

External / processor recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **ticketing source** the compile target reads at execution time
  (ingest) — the operator's helpdesk runtime, on-prem ITSM,
  Git-managed request inbox, or mailbox bridge. No hosted helpdesk
  / ITSM-SaaS default; no vendor SDK bundling; no default non-EU
  endpoint.
- The **self-service surface** the compile target calls against
  during attempt-automated-resolution — the operator's knowledge-base
  store, parameterised self-service-action runtime, or scripted
  remediation surface. Same sovereign-stack discipline as ingest.
- The **responder queue** the human-handoff envelope acknowledges
  against — the operator's on-call rota, automation responder role,
  or rota-management runtime.
- The **interaction-evidence store** receiving the emitted artifact
  (`content/evidence/incidents/` contributor home; the durable store
  is operator-configured). Destination is operator-wired — no
  default non-EU endpoint.
- The **telemetry / SIEM store** receiving the OCSF API Activity
  records emitted during ingest, classification, resolution,
  handoff, and emission.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record names
the dependency so a sovereignty review can verify it.

## 5. Retention

The workflow itself is stateless — the durable retention horizon is
the operator-owned ticketing source, interaction-evidence store, and
telemetry store:

- The **interaction-evidence artifact** (request reference + closed
  classification + automated-resolution outcome + human-handoff
  envelope + execution metadata) is written to the operator's
  incidents evidence store and inherits that store's retention
  policy. For continuous-attestation use the operator typically
  retains the per-interaction artifacts for the audit window
  required by the governing regulation (NIS2 / DORA
  evidence-retention obligations), enforced by the store's TTL or
  evidence-pack expiry.
- **OCSF activity records** emitted during ingest, classification,
  resolution, handoff, and emission follow the operator's telemetry
  retention policy on the underlying OCSF store.
- The **ticket lifecycle** on the operator's helpdesk runtime
  (open / acknowledged / resolved / closed) is durable on that
  runtime and follows its retention, not the workflow's.

No copy of the support-request record, the classification verdict,
the automated-resolution observation envelope, or the human-handoff
envelope is retained by the workflow beyond the emission span; the
durable artifact is the interaction-evidence record above.

## 6. Cross-border transfers

**No transfer.** The workflow is designed to execute end-to-end on
the operator's sovereign-hosted runtime (one of the EU-hostable
reference targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) with EU-pinned
processor endpoints for the operator-bound ticketing source,
self-service surface, responder queue, interaction-evidence store,
and telemetry-store dependencies.

The technical controls that hold this scoring (FOUNDATION property #3
— sovereignty):

- The reference compile targets are framework-agnostic and run on the
  operator's own sovereign-hosted runtime; no SecOps-NG-hosted egress
  path exists in the workflow. The orchestrator the operator already
  runs is the execution boundary.
- The support-request ingest, the classification step, the
  automated-resolution call against the operator's self-service
  surface, and the responder-queue acknowledgement read are
  operator-bound at compile time and target the operator's EU-region
  endpoints directly; the playbook does not call a hosted SecOps-NG
  helpdesk service or a hosted ITSM-SaaS.
- The interaction-evidence artifact emits to the operator's
  EU-region-pinned incidents evidence store; no external aggregation
  is invoked.
- No public-cloud-AI endpoint is called during ingest,
  classification, automated resolution, handoff, or emission.

If an operator binds a non-EU helpdesk / ITSM, a non-EU self-service
surface, a non-EU responder queue, a non-EU interaction-evidence
store, or a non-EU telemetry processor at compile time, this scoring
breaks — the operator MUST re-score this section under "transfer
under SCCs / BCRs / derogation", name the third country and the
transfer instrument, and document the supplementary measures
(encryption-at-rest with operator-held keys, pseudonymisation of the
requester reference before egress) before the binding goes live.
Sovereignty review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** Where the requester or responder handle is
  attributable to a natural person, a Subject Access Request is
  answered by querying the operator's interaction-evidence store on
  the request / responder reference from §3 and the operator's
  telemetry / OCSF store on the same reference across the activity
  records the workflow emitted. The workflow introduces no storage
  location beyond those parents.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes intended to be updated; the
  support-request record, the classification verdict, and the
  automated-resolution envelope are captured-as-declared by the
  upstream ticketing source and the operator's classification
  policy. Rectification at the subject's request is operationally
  meaningful only against the upstream ticketing source — the next
  support interaction reflects the corrected attribution.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing the interaction-evidence
  artifacts and OCSF activity records on the operator's store TTLs
  erases the workflow's copy of the metadata. A standalone
  subject-initiated erasure request flows through the
  interaction-evidence store's erasure procedure, which the workflow
  inherits. Where the lawful basis is **Art. 6(1)(c)** legal
  obligation, erasure may be lawfully refused for the statutory
  evidence-retention window.
- **Objection (Art. 21).** Where the lawful basis is **Art. 6(1)(f)**
  legitimate interests, a data subject can object on grounds relating
  to their particular situation; the operational handling is to
  record the objection and route support-interaction handling for
  that requester through manual review without the automated-
  resolution attempt. Where the basis is **Art. 6(1)(c)** legal
  obligation (most regulated operators), Art. 21 objection does not
  displace the obligation.
- **Automated decision-making (Art. 22).** The workflow classifies
  the support request and may attempt an automated resolution
  against the operator-declared self-service surface, but the
  explicit human-handoff step (`escalate-with-human-handoff`)
  guarantees that no support interaction is closed without either a
  successful automated resolution or a confirmed handoff to a human
  responder. The handoff step is first-class — it always runs, and
  on every path where the automated resolution did not close the
  request a human responder is in the loop. Art. 22(1) (decisions
  based solely on automated processing producing legal or similarly
  significant effects) therefore does not apply to the workflow as
  shipped. If an operator wires the emitted interaction evidence
  into an automated downstream decision that closes the request
  without human review, that downstream decision MUST be re-scored
  where it is defined, not here.

## 8. Outbound personal-data transfer

The workflow has two classes of outbound leg that carry personal
data outside the operator's primary support-interaction store. Each
is scored below against GDPR Chapter V (Art. 44–49); the
EU-residency posture is sovereignty-first by default per Directive
1, and the operator's compile-time bindings are the knobs that can
break the scoring.

**Leg A — Operator-bound ticketing / ITSM processor egress
(ingest source, self-service surface, responder queue,
interaction-evidence store).**

- *Destination class.* Operator-bound processors under GDPR
  Art. 28 — the operator's helpdesk runtime / on-prem ITSM /
  Git-managed request inbox / mailbox bridge providing the
  ticketing source; the operator's knowledge-base or scripted
  remediation runtime providing the self-service surface; the
  operator's on-call rota or rota-management runtime providing
  the responder queue; the operator's incidents-evidence store
  receiving the emitted interaction artifact. The framework
  ships no hosted-helpdesk / ITSM-SaaS default and no vendor SDK
  bundling; every binding is operator-supplied at compile time.
- *Transfer mechanism.* **No transfer** under the default
  binding: the reference compile targets (n8n / Temporal /
  LangGraph self-host on Nebul / OVHcloud / Scaleway / Hetzner)
  are EU-hostable and the four processor destinations are
  operator-pinned to EU-resident endpoints. If the operator
  binds a non-EU helpdesk SaaS, a non-EU knowledge-base store, a
  non-EU rota system, or a non-EU evidence store, the binding
  MUST be re-scored under Art. 46 SCCs with supplementary
  measures (encryption-at-rest with operator-held keys,
  pseudonymisation of requester and responder identifiers in the
  ticket envelope and interaction-evidence record before
  egress) before the binding goes live.
- *EU-residency posture.* Default is EU-resident endpoints
  across all four processor surfaces. The compile-time
  sovereignty review is the gate; the framework ships no default
  endpoint and no fallback that could route a ticket read, a
  self-service action, a responder-queue acknowledgement, or an
  evidence write outside the EU. The operator's DPA inventory
  (GDPR Art. 28) is the durable record of each processor
  binding.
- *Data minimisation on egress.* The ticketing-source read
  carries the request reference and the requester identifier the
  operator's helpdesk runtime requires to address the ticket;
  the self-service-surface call carries the classification and
  the minimum requester context the action requires; the
  responder-queue acknowledgement carries the human-handoff
  envelope without duplicating the underlying request body; the
  interaction-evidence artifact carries the closed classification
  + automated-resolution outcome + handoff envelope + execution
  metadata as §3 enumerates, with no additional projection of
  requester telemetry.

**Leg B — Telemetry / SIEM store egress (OCSF API Activity
records emitted during ingest, classification, resolution,
handoff, and emission).**

- *Destination class.* Operator-bound processor under GDPR
  Art. 28 — the operator's SIEM or OCSF-shaped telemetry store
  receiving the API Activity records the workflow emits across
  its five state transitions.
- *Transfer mechanism.* **No transfer** under the default
  binding: the OCSF store is operator-pinned to an EU-resident
  endpoint and the reference compile targets emit through the
  operator's own logging path with no SecOps-NG-hosted
  intermediary. If the operator binds a non-EU SIEM, the binding
  MUST be re-scored under Art. 46 SCCs with pseudonymisation of
  requester and responder identifiers in the activity-record
  envelope before egress.
- *EU-residency posture.* EU-resident SIEM / OCSF store only by
  default. The compile-time sovereignty review is the gate; the
  framework emits to the operator's configured logging endpoint
  and ships no fallback.
- *Data minimisation on egress.* OCSF API Activity records carry
  the state transition, the request reference, and the minimum
  classification context required by the activity-record shape;
  the underlying request body and the self-service-action
  parameters are not duplicated into the telemetry leg.

The §6 cross-border scoring as a whole is **no transfer** —
consistent with both legs above scoring no-transfer under the
default sovereign-stack posture. Any operator re-scoring of a leg
here MUST be reflected in §6 in the same change so the two
sections do not disagree.
