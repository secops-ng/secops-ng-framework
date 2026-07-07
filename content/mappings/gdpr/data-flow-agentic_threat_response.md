# GDPR data flow — agentic_threat_response

Per-workflow GDPR data-flow entry for the `agentic_threat_response`
cookbook playbook (`playbook.agentic_threat_response@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/agentic_threat_response/`](../../playbooks/agentic_threat_response/).

The playbook itself is a SKELETON scaffold — CACAO workflow shape plus
structural content-model anchors — with sibling CORE / EXTEND cards
pinning real OSCAL / D3FEND / OCSF identifiers, telemetry bindings,
and KPI hooks. This data-flow document scopes the personal-data
surface of the scaffold as it stands so the Art. 30 RoPA is closed on
day one and re-armed as the sibling cards land.

---

## 1. Purpose

The workflow exists to detect and initially respond to fully-agentic
adversary activity — autonomous LLM-driven credential harvest, lateral
movement, and encryption chains observed at machine-speed decision
cadence — that static SOAR playbooks are miscalibrated to intercept.
Concretely, the workflow ingests an agentic-threat indicator (anomalous
LLM API call volume from a workload principal, rapid credential-
enumeration bursts inside a sub-minute window, or lateral movement
across identity / network edges within the observed self-correction
window), isolates the affected credential set at the operator's IdP,
contains the lateral-movement path via a network micro-segmentation
call, hands the case envelope off to `playbook.incident_management@v1`
for the NIS2 Article 23 regulator-notification chain, and preserves an
evidence bundle (LLM API call logs, credential-enumeration timeline,
lateral-movement graph, containment-action ledger) for the downstream
notification chain. The purpose is bounded to that detect-through-
contain slice plus the evidence handoff; the workflow does not itself
render the regulator notification, does not enrich the implicated
principal against external identity providers, and does not retain
the raw agent-activity telemetry past the evidence-bundle's own
retention hook.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(f) — legitimate interests**. The operator
has a legitimate interest in maintaining the security of its network
and information systems, which **Recital 49** of the GDPR explicitly
recognises as a legitimate interest of the controller — including the
processing of personal data strictly necessary to prevent unauthorised
access to electronic communications networks, to prevent malicious
code distribution, and to stop denial-of-service and damage attacks.
For operators subject to NIS2, a secondary anchor is **GDPR
Art. 6(1)(c) — legal obligation**: NIS2 Article 21(2)(b) creates a
concrete legal obligation to operate an incident-handling capability,
which this playbook discharges for the agentic-threat case set. No
special-category data (Art. 9) is processed on the happy path; if an
implicated principal happens to be a natural person whose role or
health status was recorded on the same identity record, that
special-category attribute is not read by any workflow step. The
lawful basis for the downstream regulator-notification and (where
personal data is in scope) affected-party-notification submissions
is scored on the incident-management playbook's own GDPR closure,
not here.

## 3. Categories of data subjects and personal data

Categories of data subjects: employees of the operator whose identity
records back the workload principal an agent has authenticated as
(the implicated principal on the credential-isolation step); external
users whose identifiers may appear inside a credential-enumeration
timeline the indicator was drawn from (e.g. usernames the agent
attempted); and, indirectly, any natural person whose account is
adjacent to the lateral-movement graph the containment step
interrupts. Categories of personal data: identity attributes on the
implicated principal (username, IdP subject identifier, tenant
identifier, group memberships, session identifiers), authentication
telemetry (source IP, user-agent, LLM API caller identifier if the
agent authenticated via an OIDC subject), and network-flow attributes
on the lateral-movement edges (source / destination IP addresses,
timestamps, protocol). No content of personal communications is read;
the workflow reads authentication and network-flow metadata, not
message bodies.

## 4. Recipients

Internal recipients: the response team's IAM auditor lane (alerted by
the credential-isolation step for the scope audit and forced-rotation
follow-on), the network-controls lane executing the micro-segmentation
call, and `playbook.incident_management@v1` (upstream-playbook intake
consuming the case envelope for the Article 23 notification chain).
External recipients on the happy path: none — the workflow itself does
not egress personal data outside the operator's primary processing
boundary. Any external recipient reached later (national CSIRT under
NIS2 Art. 23, competent authority under DORA Art. 19, data-subject
notification under GDPR Art. 34) is dispatched by the downstream
incident-management engine and scored on that playbook's GDPR closure.
Processors reached indirectly: the operator's IdP and network-controls
providers, both bound by a Data Processing Agreement (GDPR Art. 28)
outside this framework.

## 5. Retention

The evidence bundle emitted by the preserve-evidence step is retained
for the duration of the parent incident case in the operator's
incident-management system plus the audit-retention period the
operator commits to under its NIS2 / DORA obligation (typically five
years for incidents that trip the significant-incident threshold, one
year otherwise). The bundle identifier is a pointer into that
retention hook; the raw agent-activity telemetry the bundle
summarises is retained per the operator's authentication-log and
network-flow retention policies (typically 90 days for authentication
logs, 30 days for network-flow records) and is not persisted a second
time by this workflow. Session and token records revoked at the
credential-isolation step are audit-logged at the IdP under that
provider's own retention policy. Enforcement mechanism: sealed
evidence-pack expiry on the incident-management side; TTL-driven
purge on the upstream authentication-log and network-flow topics.

## 6. Cross-border transfers

Default posture: **no transfer**. All processing on this workflow's
happy path stays within the EU/EEA — the operator's IdP,
network-controls, and incident-management runtimes are pinned to
EU-resident endpoints under the sovereignty-first directive the
framework ships with, and the workflow does not itself invoke any
public-cloud-AI service or third-country processor. The technical
controls that hold the posture are: region-pinned IdP endpoints, a
sovereign-hosted runtime for the incident-management engine, and an
operator-bound processor-endpoint configuration that a non-EU binding
would break at compile time. If an operator swaps a sovereign
processor for a US-hosted one on any of the touchpoints above, the
swap must be re-scored under Art. 46 (SCCs / BCRs / supplementary
measures) and the change flagged in review before the swap is wired
into production. Cross-border transfers on the downstream regulator-
notification leg are scored on the incident-management playbook's own
data-flow document.

## 7. Data subject rights

Access (Art. 15): the implicated principal's identity attributes and
the authentication and network-flow telemetry against that principal
are located inside the evidence bundle keyed to the parent incident
case; a Subject Access Request is answered against the incident case
record, which the operator's SAR handling process is already bound
to. Rectification (Art. 16): the workflow does not store
subject-supplied attributes that a subject could rectify — the
identity attributes are read from the IdP's own record, and
rectification happens upstream on the IdP. Erasure (Art. 17): the
retention hook in §5 is the answer — the evidence bundle expires when
the parent incident case's retention window elapses, at which point
the bundle is purged along with the case. Objection (Art. 21): the
lawful basis is Art. 6(1)(f); an objection from an implicated
principal is operationally handled by the operator's DPO in
consultation with the response team, but security-incident processing
is generally a compelling legitimate ground the operator can rely on
under Recital 49 to continue processing while the incident is live.
Automated decision-making (Art. 22): the workflow's steps run
deterministically against operator-tuned thresholds; no step produces
a decision with legal or similarly significant effects on the
implicated principal, and downstream personnel actions (if any) are
taken by the operator's HR / security-management chain outside this
workflow.
