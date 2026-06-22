# GDPR data flow — data_exfil

Per-workflow GDPR data-flow entry for the `data_exfil` cookbook
playbook (`playbook.data_exfil@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/data_exfil/`](../../playbooks/data_exfil/).

---

## 1. Purpose

The workflow exists to respond to a Data Loss Prevention (DLP) /
egress signal identified by `__signal_id__` that indicates possible
exfiltration of sensitive data, so the operator can determine whether
data actually left the boundary, contain confirmed exfiltration
proportionate to the data classification and scope, and meet the
regulator- and affected-subject-notification obligations that follow
when the affected-subjects count and data classification cross the
reporting threshold. Concretely, the workflow triages the signal,
hydrates it with originating user / asset / destination context,
runs a scope assessment that produces `__data_classification__`,
`__affected_subjects_count__`, and `__exfil_confirmed__`, branches
on `__exfil_confirmed__` to either close the case out (false
positive, in-line control prevented egress) or proceed to
containment (session-token revocation, identity / host isolation,
credential rotation, egress-policy tightening on the named
destinations), evaluates `__regulator_required__` against the
affected-subjects count and data classification per the operator's
regulator-routing policy, and emits the regulator notification
(NIS2 Art. 23 to the national CSIRT, DORA Art. 19 to the competent
authority, GDPR Art. 33 to the supervisory authority) and the
affected-subject notification (GDPR Art. 34) along the operator's
pre-bound channels. The purpose is bounded to that
triage-scope-contain-notify decision and the metric hooks it
produces (`kpi.mttd_exfil@v1`, `kpi.mttr_containment@v1`,
`kpi.notification_sla_compliance@v1`,
`kri.regulator_notification_overrun@v1`); the workflow does not
itself reconstruct the leaked payload past what scope assessment
requires, does not pursue the receiving party, and does not feed
the signal to any external aggregator beyond the regulator and
affected-subject channels named in the playbook bindings.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(f) — legitimate interests**. The operator
has a legitimate interest in maintaining the security of network
and information systems, which **Recital 49** of the GDPR
explicitly recognises as a legitimate interest of the controller,
including processing of personal data strictly necessary and
proportionate to ensuring the security of network and information
systems — detecting suspected exfiltration, assessing its scope,
and containing it sits squarely inside that recital. The personal
data processed during triage, scope assessment, and containment
(originating-user identifier, asset / endpoint identifier,
destination identifier, the subject-counting derived from the
payload classification) is necessary and proportionate to that
interest.

Secondary: **Art. 6(1)(c) — legal obligation** applies along two
axes that operate together for this workflow:

- The regulator-notification branch is itself a processing
  operation required to discharge a legal obligation. Operators in
  scope of the **NIS2 Directive** notify the national CSIRT under
  **NIS2 Art. 23** for significant incidents; operators in scope
  of the **DORA Regulation** notify the competent authority under
  **DORA Art. 19** for major ICT-related incidents; controllers
  under the **GDPR** notify the supervisory authority under
  **Art. 33** within 72 hours of becoming aware of a personal
  data breach. The notification payload is processed under
  6(1)(c) for the obligation it satisfies.
- The affected-subject communication branch (the playbook's
  `notify customer` step name is a CACAO-side label; the
  GDPR-side framing here is the Art. 34 affected-subject
  communication) satisfies the controller's obligation to communicate a personal data breach
  to the affected data subjects under **GDPR Art. 34** when the
  breach is likely to result in a high risk to their rights and
  freedoms; the workflow's reach into subject contact data sits
  inside that obligation.

Operators in scope of NIS2 also inherit the
**Art. 21(2)(b)** (incident handling) and **Art. 21(2)(j)**
(communications security) bases for the containment and
detection-baseline maintenance the workflow exercises. The
playbook's `external_references` enumerate these bases verbatim;
this section is grounded against them and adds nothing beyond
what the playbook declares.

Special-category data (Art. 9) is materially in scope for this
workflow in a way it is not for most cookbook playbooks: a
confirmed exfiltration may carry health, biometric, racial or
ethnic, political-opinion, trade-union, religious-belief,
sex-life, or other Art. 9 categories belonging to external data
subjects. The workflow itself does not derive Art. 9 conclusions
about subjects; scope assessment operates against
`control.data_classification_baseline@v1` and surfaces the
classification at the bundle / dataset level (the
`__data_classification__` variable). Where the classification
indicates `special-category`, the regulator-routing policy and
the affected-subject notification routing both escalate accordingly, and
the operator's Art. 9 lawful-basis review (typically Art. 9(2)(f)
— establishment, exercise or defence of legal claims — for the
breach-response leg) is required before the containment branch
executes. The workflow's data-flow record names the dependency;
the operator's lawful-basis register holds the Art. 9 assessment.

## 3. Categories of data subjects and personal data

Data subjects:

- **Operator-internal originating actors** — the natural person
  (or service principal bound to a natural person) identified
  during triage as the source of the egress that produced
  `__signal_id__`. The signal-hydration step pulls the actor's
  identifier off the DLP event; the containment step acts on the
  actor's session and credentials when `__exfil_confirmed__` is
  true. The originating actor is the data subject most directly
  implicated by the workflow's normal path.
- **Operator-internal asset / endpoint owners** — the natural
  person (or team mailbox) responsible for the originating asset
  or endpoint named in the signal. Receive containment-step
  notifications when the action affects an asset they own
  (isolation, egress-policy change), and are addressed via the
  operator's pre-bound channel.
- **External data subjects whose personal data is the payload**
  — the natural persons whose records were observed leaving the
  boundary. The scope-assessment step derives
  `__affected_subjects_count__` against the operator's data
  the affected-subject
  notification step addresses this set under GDPR Art. 34
  routing. Identifiers and contact details for these subjects
  are sourced from the operator's existing data-subject
  registers
  and are read transiently for the notification step.
- **External recipients named in the destination** — natural
  persons identifiable from the destination handle (recipient
  email address, recipient cloud-storage account, recipient
  collaboration-suite identity) the egress targeted. The
  triage step records the destination handle against the
  signal; the containment step's egress-policy tightening acts
  on the destination identifier. The workflow does not pursue
  the recipient or process their data past what the destination
  handle itself carries.
- **Operator-internal responders and on-call engineers** — the
  responder set whose decisions during scope assessment,
  containment, and notification are recorded against
  `kpi.mttd_exfil@v1`, `kpi.mttr_containment@v1`,
  `kpi.notification_sla_compliance@v1`, and
  `kri.regulator_notification_overrun@v1` via the metrics layer.
- **Regulator-side contact subjects** — the natural persons who
  receive the notification at the national CSIRT, the
  competent authority, or the supervisory authority are
  recipients (see §4), not subjects of the workflow's
  processing.

Categories of personal data:

- **Originating-actor identifiers** — user principal name,
  account identifier, session-token reference, source IP and
  user-agent captured by the DLP / egress event.
- **Asset / endpoint identifiers** — host name, device
  identifier, asset URN, owner-team mailbox resolved against
  the operator's ownership graph during hydration.
- **Destination identifiers** — recipient address, recipient
  cloud-storage account, recipient collaboration-suite
  identity, network destination (FQDN, IP, port) named in the
  DLP / egress event.
- **Payload classification metadata** —
  `__data_classification__` (public, internal, confidential,
  restricted, special-category) and the per-bundle counts
  scope assessment produced; the workflow processes
  classification labels, not the payload bytes themselves.
- **Affected-subject count and categorisation** —
  `__affected_subjects_count__` and any subject-category
  attribute (employee / consumer / minor / Art. 9 category)
  scope assessment derived against the data-classification
  baseline.
- **Affected-subject contact attributes** — for the
  affected-subject notification leg, the contact attributes
  (email address, postal address, account identifier) read
  transiently from the operator's data-subject register
  in order to address the notification.
- **Signal and finding metadata** — `__signal_id__`, the upstream
  Sigma rule provenance (`detection.sigma.dlp_egress_alert@v1`,
  `detection.sigma.data_staging_archive_created@v1`), the OCSF
  DLP Activity (class_uid 4006) record carrying the alert, the
  OCSF Security Finding (class_uid 2001) record carrying the
  incident finding emitted to the regulator and
  affected-subject channels, the first-observed timestamp.
- **Operational decision state** — `__exfil_confirmed__`,
  `__regulator_required__`, the containment actions taken
  (`control.network_egress_filtering@v1`,
  `control.dlp_enforcement@v1` evidence), the regulator-
  notification payload hash, the affected-subject notification batch
  identifier, and the per-incident metric counters.

Bundle bodies, raw DLP-event payloads, and the exfiltrated-data
contents themselves are NOT persisted by the workflow. Scope
assessment operates against the classification surface (counts
and labels) rather than the leaked records; the workflow does
not introduce a second copy of the payload. Only the canonical
signal record, the scope-assessment outputs, the containment
evidence, the notification payload references, and the
operational counts above are persisted past the workflow's
lifetime.

## 4. Recipients

Internal recipients:

- The **originating actor's asset / endpoint owner** identified
  during triage — addressed during containment-step
  notification along the operator's pre-bound channel
  (ticketing / chat / paging) when the containment action
  affects their asset.
- The **identity / endpoint enforcement surface** — the
  operator's IdP (session-token revocation, credential
  rotation), the operator's endpoint-management surface
  (host isolation), and the operator's network-egress surface
  (egress-policy tightening) receive the containment-step
  actions and produce the `control.network_egress_filtering@v1`
  and `control.dlp_enforcement@v1` attestations.
- The **DLP platform** — re-receives the post-containment
  validation against the same destination / actor and produces
  the containment-verified state for the metric layer.
- The **incident_management on-call** — receives the incident
  hand-off carrying the scope-assessment outputs, the
  containment evidence, and the notification status; pickup
  is timed against `kpi.mttr_containment@v1`.
- The **metrics layer** consuming `kpi.mttd_exfil@v1`,
  `kpi.mttr_containment@v1`,
  `kpi.notification_sla_compliance@v1`, and
  `kri.regulator_notification_overrun@v1` — the recipient is
  the aggregated counter, not the per-incident identifier.

External / upstream recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **regulator** addressed by the notification branch when
  `__regulator_required__` is true — the **national CSIRT**
  designated under NIS2 Art. 12 for NIS2-scope notifications,
  the **competent authority** designated under DORA Art. 46
  for DORA-scope notifications, and the **supervisory
  authority** designated under GDPR Art. 51 for the GDPR Art.
  33 notification leg. The regulator is a controller in its
  own right for the notification it receives; the operator is
  the controller for the upstream processing leading up to it.
- The **affected data subjects** addressed by the
  affected-subject notification step under GDPR Art. 34. The
  communication channel is operator-bound (email / postal / in-app)
  against the operator's data-subject register.
- The **operator-bound DLP platform processor** — receives the
  signal hydration request and the post-containment
  validation, and emits the DLP Activity (4006) and Security
  Finding (2001) OCSF events.
- The **operator-bound IdP / endpoint-management / network-
  egress processors** — receive the containment actions and
  produce the control-evidence attestations.
- The **operator-bound ticketing / chat / paging processor** —
  receives the asset-owner notification, the on-call hand-off,
  and the operational annotations against the incident.
- The **operator-bound subject-communication processor** —
  receives the affected-subject notification batch.

Each operator-bound processor MUST have a Data Processing
Agreement (GDPR Art. 28) in place before the binding is wired in
production; the framework does not ship the DPAs, but the
data-flow record names the dependency so a sovereignty review
can verify it. The regulator and the affected data subjects are
not processors — they are independent controllers (regulator)
and the data subjects themselves (Art. 34 communication); no
DPA applies to those legs.

## 5. Retention

The workflow itself is stateless across signals — the durable
retention horizons are the operator's DLP / SIEM platform, the
operator's incident-record store, the operator's identity /
endpoint enforcement surfaces, the regulator's own retention,
and the metric layer:

- **Signal records** are owned by the operator's DLP platform.
  Retention follows the platform's policy (typical defaults:
  90 days for closed informational signals, 12 months for
  closed signals that drove a containment action, indefinite
  for signals tied to an incident that crossed the regulator
  threshold and remains under the audit horizon).
  `__signal_id__` is the workflow's handle on the platform's
  record; the workflow does not introduce a separate copy.
- **Scope-assessment outputs** — `__data_classification__`,
  `__affected_subjects_count__`, `__exfil_confirmed__` — are
  derived at workflow runtime and persisted against the
  incident-record store under the operator's incident-record
  retention (typically 2–7 years for regulated entities under
  NIS2 / DORA audit obligations, longer where the incident
  remains relevant to legal claims under Art. 17(3)(e)).
- **Affected-subject contact attributes** read for the
  affected-subject-notification leg are not retained by the workflow
  — the attributes are read transiently from the operator's
  data-subject register at notification time. The
  notification batch identifier (not the per-subject
  attributes) is retained against the incident record.
- **Containment evidence** — the
  `control.network_egress_filtering@v1` and
  `control.dlp_enforcement@v1` attestations (session-token
  revocation event, host-isolation event, egress-policy
  change record, credential-rotation event) are retained by
  the respective enforcement surface under that surface's
  audit retention (typically 12–24 months for IdP audit
  logs, 12 months for endpoint-management actions, 2–7
  years for egress-policy change records under the
  operator's change-control retention).
- **Regulator-notification payload** — retained against the
  incident record for the duration the notification remains
  legally relevant (typically the regulator's own statute-of-
  limitations horizon for the notification, plus the
  operator's audit horizon). The regulator's own copy is
  retained under the regulator's controller-side policy and
  is out of scope for this record.
- **Customer-notification payload** — the batch reference and
  the audit trail of dispatch are retained against the
  incident record under the same incident-record retention.
- **Notification / paging payloads** — the ticketing entry,
  chat message, page event inherit the respective processor's
  retention (typical defaults: 12 months for ticketing, 90
  days for chat, 12 months for paging audit-trail).
- **Metric counters** — `kpi.mttd_exfil@v1`,
  `kpi.mttr_containment@v1`,
  `kpi.notification_sla_compliance@v1`, and
  `kri.regulator_notification_overrun@v1` aggregate over the
  metric layer's rollup horizon and do not retain per-incident
  identifiers past that rollup.

No copy of the exfiltrated payload bytes, the actor's session
material, the endpoint's full memory state, the IdP's session
secrets, or the subject-communication processor's session
material is retained by the workflow beyond the per-step call;
secret handling is the runtime's responsibility per directive
#7 of the project's core directives (env-injected, never
persisted by the workflow).

## 6. Cross-border transfers

**No transfer** for the default sovereign-hosted path. The
workflow is designed to execute end-to-end on the operator's
sovereign-hosted runtime (one of the EU-hostable reference
targets — n8n self-host, Temporal self-host, or LangGraph
self-host on Nebul / OVHcloud / Scaleway / Hetzner) against an
EU-region DLP platform endpoint, an EU-region IdP / endpoint-
management / network-egress surface, an EU-region ticketing /
paging surface, EU-region regulator channels (the national
CSIRT under NIS2, the competent authority under DORA, the
supervisory authority under GDPR), and an EU-region
subject-communication processor.

The technical controls that hold this scoring (FOUNDATION
property #3 — sovereignty):

- The reference compile targets are framework-agnostic and run
  on the operator's own sovereign-hosted runtime; no
  SecOps-NG-hosted egress path exists in the workflow.
- The DLP platform's read / validation endpoints are
  EU-region endpoints (an EU-hosted DLP platform, or the EU
  region of a major DLP SaaS).
- The IdP / endpoint-management / network-egress surfaces
  are EU-region or EU-hostable (self-hosted IdP / endpoint /
  network are the sovereign reference; SaaS variants are
  operator-bound to an EU region).
- The ticketing / chat / paging processors are EU-region or
  EU-hostable on the same terms.
- The subject-communication processor (transactional email /
  postal aggregator / in-app messaging) is EU-region; the
  notification batch's content remains within EU jurisdiction.
- The regulator channel is by construction EU-internal — the
  national CSIRT, competent authority, and supervisory
  authority are EU bodies under their respective directives /
  regulation.
- The OCSF DLP Activity (4006) and Security Finding (2001)
  events emit to the operator's telemetry store under the
  operator's region pinning.
- No public-cloud-AI endpoint is called during triage, scope
  assessment, branching, containment, or notification; the
  workflow's logic is deterministic against the playbook's
  declared variables and step contract.

**Non-EU processor bindings are explicit re-score gates.** The
data_exfil workflow's bindings to the DLP platform, the IdP /
endpoint-management / network-egress surfaces, the ticketing /
paging surface, and the subject-communication processor are
each a potential non-sovereign substitution that breaks this
scoring:

- **Non-EU DLP platform.** US-hosted DLP SaaS is common; if
  the operator binds one, the signal record and the
  scope-assessment evidence are processed in the US. Re-score
  under "transfer under SCCs / BCRs / derogation" (the EU-US
  Data Privacy Framework where the provider is a certified
  US recipient, otherwise standard contractual clauses),
  name the third country, and document the supplementary
  measures (pseudonymisation of actor / destination / asset
  identifiers before they leave the EU, operator-managed
  encryption keys held in the EU).
- **Non-EU IdP / endpoint-management / network-egress
  processor.** Where the operator's identity, endpoint, or
  network surface runs on a US-hosted SaaS, the containment-
  step actions and their evidence cross the border. Re-score
  and document on the same Chapter V instruments; the
  session-token revocation and the credential-rotation event
  in particular carry the originating-actor identifier and
  require the supplementary-measure documentation.
- **Non-EU ticketing / chat / paging processor.** Most
  popular SaaS surfaces have US-hosted control planes. The
  notification payload (actor identifier, asset identifier,
  destination identifier, severity, incident link) reaches
  the processor's control plane on call; re-score and
  document the same way.
- **Non-EU subject-communication processor.** Where the
  transactional email or in-app messaging surface is
  US-hosted, the affected-subject notification batch carries the
  affected-subject contact attributes to the US on dispatch.
  This binding is the highest-risk substitution because the
  subjects the notification addresses are by construction
  the subjects of a confirmed personal-data breach; re-score
  under SCCs / DPF, document the supplementary measures
  (envelope encryption with operator-held keys where the
  processor supports it, minimal-attribute templating so the
  processor sees only what is necessary to deliver the
  notification), and the sovereignty review at compile time
  is the gate for this binding more than any other.

The transfer direction across these bindings is
operator → processor for the read / call / push and
processor → operator for the response; both legs are scored.
Sovereignty review at compile time is the gate, and the
binding does not go live until the re-scored data-flow entry
is in place.

## 7. Data subject rights

- **Access (Art. 15).** Where a data subject in §3 exercises a
  Subject Access Request against the operator, the SAR is
  answered by querying the operator's DLP platform on the
  actor / asset / destination identifier for signals the
  subject is named on, the operator's incident-record store
  on the scope-assessment outputs and the
  control-evidence attestations referencing the subject, the
  operator's IdP / endpoint-management / network-egress
  surfaces on the containment-action records, the operator's
  ticketing / chat / paging processors on the notification
  and hand-off payloads, the operator's subject-
  communication processor on the dispatch record (for
  externally-affected subjects exercising access against the
  notification they received), and the operator's audit-log
  telemetry on `telemetry.ocsf.dlp_alert@v1` and
  `telemetry.ocsf.incident_finding@v1` events. The workflow
  does not introduce a separate storage location beyond
  those parents; the parents' SAR-response procedures apply.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes — originating-actor identity is
  resolved from the operator's IdP at runtime, asset / endpoint
  identifiers are read from the operator's inventory, and
  destination identifiers are captured-as-emitted by the DLP
  platform. Rectification of an actor attribution flows
  through the operator's IdP maintenance process and
  propagates on the next hydration cycle; rectification of an
  asset attribution flows through the operator's inventory /
  ownership-graph maintenance; rectification of an
  affected-subject contact attribute flows through the
  operator's data-subject register (the workflow reads
  the register transiently, it does not own the canonical
  copy). Direct rectification against the workflow's
  persisted records is not operationally meaningful.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing of the DLP signal on
  the platform's TTL, ageing of the incident record on the
  operator's incident-record retention, ageing of the
  control-evidence records on the respective surfaces'
  retention, ageing of the notification / paging records on
  the processor's TTL, and the metric-layer rollup horizon
  collectively erase the workflow's copy of the metadata. A
  standalone subject-initiated erasure request flows through
  each parent processor's erasure procedure; the operator
  weighs the request against the **Art. 17(3)(b)** exemption
  (compliance with a legal obligation under NIS2 Art. 23 /
  DORA Art. 19 / GDPR Art. 33 incident-notification
  retention), the **Art. 17(3)(c)** exemption (reasons of
  public interest in the area of public health, where
  Art. 9 health data was in the exfiltrated set), and the
  **Art. 17(3)(e)** exemption (establishment, exercise, or
  defence of legal claims arising from the breach). The
  Recital 49 ground supports retention only where the data
  is still strictly necessary and proportionate to
  maintaining network and information security; closed-and-
  aged incidents beyond their audit horizon and beyond the
  legal-claims relevance window do not satisfy that test.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(f)** (the workflow's primary basis), a data
  subject can object to the processing on grounds relating
  to their particular situation. The operator-internal
  subject set in §3 (originating actors, asset owners,
  responders) is handled by the operator's HR / privacy
  function via the same channel that handles workplace-
  monitoring objections; the legitimate-interest balancing
  test for incident response weighs heavily against an
  objection raised by the originating actor of a confirmed
  exfiltration. For externally-affected subjects, the
  affected-subject-notification leg under Art. 34 is not subject to
  Art. 21 objection (the lawful basis there is Art. 6(1)(c)
  legal obligation, which Art. 21 does not displace). For
  external-recipient subjects identifiable from the
  destination handle, an objection is registered and the
  operator weighs it against the legitimate-interest in
  containing the egress and meeting the notification
  obligation; in practice the containment action against the
  destination has typically already executed by the time an
  objection is raised.
- **Automated decision-making (Art. 22).** The
  `exfil confirmed?` branch is a deterministic evaluation
  against scope assessment's `__exfil_confirmed__` output;
  the `regulator notification threshold met?` branch is a
  deterministic evaluation against `__regulator_required__`
  per the operator's regulator-routing policy. Neither
  branch produces a legal or similarly significant effect
  on a natural person by itself: the containment branch
  acts on the originating actor's session and credentials
  and on the operator's network-egress posture, which is a
  bulk-defensive operational action against the operator's
  own infrastructure rather than a per-subject adjudication.
  The affected-subject-notification leg does produce a significant
  effect on the affected subjects (they learn their data
  was breached and may take action), but that effect is the
  controller discharging an Art. 34 obligation, not an
  automated decision Art. 22 addresses. Art. 22 therefore
  does not apply to the workflow as shipped. If an operator
  binds a machine-learned scope-assessment model whose
  output sets `__data_classification__` or
  `__affected_subjects_count__` without human review and
  materially changes a named actor's access rights through
  the containment branch, the operator MUST re-score this
  section, surface the Art. 22 applicability, and document
  the safeguards (right to obtain human intervention, right
  to contest the decision) the operator provides.

## 8. Outbound personal-data transfer

The workflow has four classes of outbound leg that carry personal
data outside the operator's incident-record store. Each is scored
below against GDPR Chapter V (Art. 44–49); the EU-residency posture
is sovereignty-first by default per Directive 1, and the operator's
compile-time bindings are the knobs that can break the scoring.

**Leg A — Regulator submissions (national CSIRT under NIS2 Art. 12,
competent authority under DORA Art. 46, supervisory authority under
GDPR Art. 33).**

- *Destination class.* Regulator under independent-controller
  routing — the national CSIRT designated under NIS2 Art. 12 for
  NIS2-scope notifications, the competent authority designated
  under DORA Art. 46 for DORA-scope notifications, and the
  supervisory authority designated under GDPR Art. 51 for the
  GDPR Art. 33 personal-data-breach notification leg. The
  regulator is a controller in its own right for the notification
  it receives; the operator is the controller for the upstream
  exfiltration processing. The framework ships no default
  regulator endpoint; the destination is operator-supplied through
  playbook variables.
- *Transfer mechanism.* **No transfer.** EU competent authorities
  under NIS2 Art. 12, DORA Art. 46, and GDPR Art. 51 are EU/EEA-
  resident by construction. The technical control that holds this
  is that the regulator endpoint URLs are operator-supplied through
  compile-time variables and sovereignty review at compile time
  refuses any non-EU endpoint.
- *EU-residency posture.* Default is EU-resident regulator
  destinations only. A non-EU binding (a third-country sectoral
  regulator notified because the exfiltrated set touches that
  jurisdiction's subjects) MUST be re-scored under Art. 46 SCCs
  with operator-held encryption keys on the submission envelope,
  or under Art. 49(1)(d) "important reasons of public interest"
  derogation where the cross-border notification is mandated by a
  statute the operator is bound by.
- *Data minimisation on egress.* The regulator notification
  payload carries `__affected_subjects_count__`, the
  `__data_classification__` category labels, the OCSF Security
  Finding (2001) reference, the containment-evidence references,
  and the operator's nominated contact. Per-subject identifiers
  (originating actor's session metadata, asset identifiers,
  destination handles) are NOT included in the regulator
  submission; aggregate counts and category labels under
  Art. 5(1)(c) data minimisation are the regulator-template
  shape.

**Leg B — Affected-subject notification under GDPR Art. 34.**

- *Destination class.* The data subjects themselves whose records
  were observed leaving the boundary — the affected-subject set
  derived during scope assessment against the operator's
  data-subject register. The communication is controller-to-
  subject under Art. 34, not a processor leg in its own right.
  The subject-communication processor (transactional email,
  postal aggregator, in-app messaging) that physically carries
  the notification is scored as a separate Art. 28 processor under
  Leg D.
- *Transfer mechanism.* **No transfer** for the controller-to-
  subject leg itself: the GDPR Art. 34 communication is addressed
  to the affected subjects directly and the Chapter V regime
  applies to processor / sub-processor routing under it (Leg D),
  not to the controller-to-subject relationship. Where an
  affected subject is resident in a third country at the time of
  notification (cross-border breach scope), the operator's
  outbound channel routing for that subject MUST be re-scored
  against the Chapter V instrument that authorises the routing.
- *EU-residency posture.* Default is EU-resident subject set
  served by EU-region subject-communication processor (Leg D).
  Where the affected set spans non-EU subjects, the routing per
  subject is operator-bound and re-scored.
- *Data minimisation on egress.* The notification template
  carries the breach description, the categories of personal data
  affected, the likely consequences, the operator's contact for
  follow-up, and the recommended mitigations the subject can
  take — the GDPR Art. 34(2) template shape. Per-subject
  identifiers from the operator's data-subject register are
  dereferenced transiently to address the notification; the
  notification batch identifier (not the per-subject attributes)
  is retained against the incident record per §5.

**Leg C — Operator-bound DLP / IdP / endpoint / network egress
processors.**

- *Destination class.* Operator-bound processors under GDPR
  Art. 28 — the DLP platform (signal hydration, post-containment
  validation), the IdP (session-token revocation, credential
  rotation), the endpoint-management surface (host isolation), and
  the network-egress surface (egress-policy tightening) that
  receive the containment-step actions and produce the
  `control.network_egress_filtering@v1` and
  `control.dlp_enforcement@v1` attestations.
- *Transfer mechanism.* **No transfer** under the default
  EU-pinned binding: the reference compile targets are
  framework-agnostic and run on the operator's own sovereign-
  hosted runtime, and the framework ships no SecOps-NG-hosted
  egress path. If the operator binds a non-EU DLP SaaS control
  plane, a US-region IdP tenant (Azure AD / Entra ID, Okta), a
  non-EU endpoint-management or network-egress SaaS, the binding
  MUST be re-scored under Art. 46 SCCs (EU-US Data Privacy
  Framework where the provider is a certified US recipient,
  otherwise standard contractual clauses) with supplementary
  measures (pseudonymisation of originating-actor / destination /
  asset identifiers before egress, operator-managed encryption
  keys held in the EU) before the binding goes live.
- *EU-residency posture.* Default is EU-region processor tenants
  on every operator-bound endpoint above. The compile-time
  sovereignty review is the gate; the operator's DPA inventory
  under GDPR Art. 28 is the durable record of the binding the
  scoring depends on.
- *Data minimisation on egress.* The payload to each processor is
  scoped to what the containment action requires — actor
  identifier and session-token reference to the IdP for
  revocation, host identifier to the endpoint-management surface
  for isolation, destination identifier to the network-egress
  surface for policy tightening, signal reference to the DLP
  platform for re-validation. Payload bytes from the exfiltrated
  data are NOT routed through these processors; the workflow
  operates against the classification surface, not the leaked
  records (§3).

**Leg D — Operator-bound subject-communication and ticketing /
paging processors.**

- *Destination class.* Operator-bound processors under GDPR
  Art. 28 — the subject-communication processor (transactional
  email, postal aggregator, in-app messaging) that physically
  carries the Art. 34 notification batch (Leg B), and the
  ticketing / chat / paging processor that carries the
  asset-owner notification, the on-call hand-off, and the
  operational annotations against the incident.
- *Transfer mechanism.* **No transfer** under the default
  EU-region binding. The subject-communication processor is the
  highest-risk substitution in this workflow because the
  notification batch carries the affected-subject contact
  attributes by construction; a non-EU subject-communication
  processor (US-hosted transactional email SaaS) MUST be
  re-scored under Art. 46 SCCs / DPF with supplementary measures
  (envelope encryption with operator-held keys where the
  processor supports it, minimal-attribute templating so the
  processor sees only what is necessary to deliver the
  notification) before the binding goes live. Non-EU ticketing /
  chat / paging processors carry the actor / asset / destination
  identifiers and the incident link on call; re-score on the same
  Chapter V instruments.
- *EU-residency posture.* Default is EU-region processor tenant
  for both legs. Sovereignty review at compile time is the gate
  for the subject-communication binding more than any other in
  this workflow, given the breach-by-construction nature of the
  notification recipients.
- *Data minimisation on egress.* The subject-communication batch
  carries the Art. 34(2) template fields (Leg B) plus the
  per-subject contact attribute (email address, postal address,
  account identifier) dereferenced transiently from the
  operator's data-subject register. The ticketing / chat / paging
  payload carries actor identifier, asset identifier, destination
  identifier, severity, and the incident link — no payload bytes
  from the exfiltrated data and no Art. 9 attribute beyond the
  `__data_classification__` label.

The §6 cross-border scoring as a whole is **no transfer** for the
default EU-pinned binding — consistent with all four legs above
scoring no-transfer. Any operator re-scoring of a leg here MUST be
reflected in §6 in the same change so the two sections do not
disagree; the non-EU subject-communication processor binding is the
re-score gate this workflow is most likely to hit.
