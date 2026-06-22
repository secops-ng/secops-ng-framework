# GDPR data flow — cloud_misconfiguration

Per-workflow GDPR data-flow entry for the `cloud_misconfiguration`
cookbook playbook (`playbook.cloud_misconfiguration@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/cloud_misconfiguration/`](../../playbooks/cloud_misconfiguration/).

---

## 1. Purpose

The workflow exists to respond to a Cloud Security Posture Management
(CSPM) finding that flags a sensitive misconfiguration on the
operator's cloud estate — public storage exposure, over-permissive
identity, missing encryption, or a deviating configuration baseline —
so the responsible resource owner can apply an attested remediation
and a re-scan confirms the deviation no longer fires. Concretely, the
workflow ingests the finding identified by `__finding_id__` from the
operator's posture-management platform, enriches it against the
operator's cloud inventory and ownership graph to resolve
`__resource_id__`, `__owner_id__`, and `__severity__`, branches on
`__known_false_positive__` to suppress documented exceptions without
paging, otherwise notifies the owner along the operator's pre-bound
channel, drives a guided remediation against the violated baseline
rule (an IaC pull request or an operator-driven manual change
captured against the change record), triggers a targeted re-scan
that emits `__remediation_verified__`, and either closes the case on
a clean re-scan or escalates to the security-engineering on-call so
the residual exposure surfaces against the recurring-misconfiguration
KRI rather than silently closing on an unverified attempt. The
purpose is bounded to that detect-attest-verify decision and the
metric hooks it produces; the workflow does not act on the data the
misconfiguration may have exposed (that flows through the
incident_management or data_exfil playbooks if a leak is suspected),
does not assess controllership of subjects implicated by the
exposure, and does not feed the finding to any external aggregator.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(f) — legitimate interests**. The operator
has a legitimate interest in maintaining the security of network and
information systems, which **Recital 49** of the GDPR explicitly
recognises as a legitimate interest of the controller, including
processing of personal data strictly necessary and proportionate to
ensuring the security of network and information systems — measuring
the integrity of the configuration baseline of those systems, and
remediating deviations from it, sits inside that recital. The
personal data processed here — the resource owner's identifier, the
identifiers of cloud-IAM principals named in over-permissive-identity
findings, the actor identifier captured by the cloud audit log when
a baseline was modified — is necessary and proportionate to that
interest.

Secondary: where the operator is a regulated entity under the
**NIS2 Directive**, **Art. 6(1)(c) — legal obligation** also
applies. **NIS2 Art. 21(2)(e)** requires essential and important
entities to apply security in network and information systems
acquisition, development and maintenance — a documented
configuration baseline and the handling of deviations from it sits
directly inside that obligation. **NIS2 Art. 21(2)(i)** adds
human-resources security, access control, and asset management,
which the resource-ownership graph and the cloud-identity
least-privilege control surface here exercise. Operators in
scope of the **DORA Regulation** (financial entities) inherit a
parallel basis under **DORA Art. 6** (ICT risk-management
framework) and **DORA Art. 9** (protection and prevention,
specifically secure configuration baselines and continuous
monitoring); a posture exception that becomes incident-grade
escalates under **DORA Art. 19** (major ICT-related incident
reporting). The playbook's `external_references` enumerate these
bases verbatim; this section is grounded against them and adds
nothing beyond what the playbook declares.

Special-category data (Art. 9) is not the target of the workflow.
The personal data the workflow itself processes is operator-side
staff and IAM-principal metadata; Art. 9 attributes are not
captured in the CSPM finding, the enrichment record, or the
remediation evidence. If the underlying misconfiguration has
exposed Art. 9 data (a public storage bucket containing health,
trade-union, or other Art. 9 categories), that exposure is handled
through the data_exfil or incident_management playbook chain, not
through this workflow's data flow.

## 3. Categories of data subjects and personal data

Data subjects:

- **Operator-internal resource owners** — natural persons (or
  identifiable team mailboxes) identified by `__owner_id__` and
  resolved against the operator's ownership graph during
  enrichment. Owners receive the notification step's payload along
  the pre-bound ticketing / chat / paging channel and are the
  primary subject category implicated by the workflow's normal
  path.
- **Operator-internal cloud-IAM principals** — natural persons
  whose principal identifiers appear inside the affected
  resource's IAM policy when the finding is an
  over-permissive-identity violation against
  `control.cloud_identity_least_privilege@v1`. The enrichment step
  reads the principal set off the resource; the principal
  identifier is recorded against the finding for the remediation
  step.
- **Operator-internal change actors** — the natural person captured
  by the cloud audit log (AWS CloudTrail, Azure Activity Log, GCP
  Cloud Audit Logs) as the actor who modified the baseline that
  the CSPM rule fingerprinted; the upstream Sigma rules enumerated
  in the playbook's `detection_refs`
  (`aws_cloudtrail_disable_logging`,
  `aws_config_disable_recording`,
  `aws_s3_data_management_tampering`,
  `azure_network_security_modified_or_deleted`,
  `azure_keyvault_modified_or_deleted`,
  `gcp_firewall_rule_modified_or_deleted`,
  `gcp_bucket_modified_or_deleted`) all fire on an audit-log event
  whose principal identifier is the change actor.
- **Operator-internal responders and on-call engineers** — the
  security-engineering on-call paged on `escalate` when
  `__remediation_verified__` is false, and the responder whose
  notification, remediation-attempt, and re-scan decisions are
  recorded against `kpi.mttr_cloud_misconfig@v1`,
  `kpi.cloud_posture_coverage@v1`, and
  `kri.recurring_cloud_misconfig@v1` via the metrics layer.
- **Incidental external subjects implicated by the underlying
  exposure** are not subjects of *this* workflow's processing. The
  CSPM finding records that an exposure existed against a
  baseline rule; the personal data potentially leaked through the
  misconfiguration is handled by the data_exfil and
  incident_management playbooks, which carry their own data-flow
  entries. The cloud_misconfiguration workflow neither enumerates
  nor processes the exposed-subject set.

Categories of personal data:

- **Resource-owner identifiers** — the `__owner_id__` resolved
  during enrichment, typically a team mailbox, a user principal
  name, or a chat handle bound to the operator's ownership graph.
- **Cloud-IAM principal identifiers** — for over-permissive-identity
  findings, the principal ARNs / object IDs / member emails that
  appear inside the resource's IAM policy and that the remediation
  step rewrites against `control.cloud_identity_least_privilege@v1`
  and `control.iac_policy_guardrail@v1`.
- **Cloud audit-log actor identifiers** — the principal identifier
  of the change actor captured in the upstream audit-log event
  that the CSPM rule fingerprinted, where the SigmaHQ detection
  pointers above are the rule provenance.
- **Resource identifiers and metadata** — `__resource_id__` (the
  URN / ARN / cloud-resource-id), tenant / project / account
  identifier, region, resource type, resource tags. Tags are a
  known channel for personal-data leakage — `Owner: jdoe@…`,
  `CreatedBy: …` — and are processed as personal data even though
  not all tag values are identifiers.
- **Finding metadata** — `__finding_id__`, the violated baseline
  rule fingerprint, the OCSF Compliance Finding (class_uid 2003)
  record carrying the finding, the OCSF Cloud Resources Inventory
  Info (class_uid 5023) record carrying the enrichment, the
  evaluated baseline, the first-observed timestamp, and
  `__severity__`.
- **Operational counts and case state** — `__known_false_positive__`,
  `__remediation_verified__`, the suppression linkage to an
  exception or known-deviation record, the remediation attempt
  recorded against `control.patch_evidence@v1`, the escalation
  event, and the per-finding metric counters
  (`kpi.mttd_cloud_misconfig@v1`, `kpi.mttr_cloud_misconfig@v1`,
  `kpi.cloud_posture_coverage@v1`,
  `kri.recurring_cloud_misconfig@v1`). The metric layer holds
  aggregated counters; the per-finding identifier is visible in the
  runtime's audit log of the workflow steps.

Bundle bodies, raw CSPM evaluation payloads, and audit-log envelopes
that exceed the persisted enrichment fields are processed
transiently for the ingest / enrichment / re-scan steps; only the
canonical finding record, the enrichment fields, the remediation
evidence, and the operational counts above are persisted past the
workflow's lifetime.

## 4. Recipients

Internal recipients:

- The **resource owner** identified by `__owner_id__` — the
  notification step's primary recipient, addressed along the
  operator's pre-bound channel (ticketing / chat / paging) per
  `__severity__`.
- The **change-management surface** — the operator's IaC pipeline
  (where the remediation is an IaC pull request bound to
  `control.iac_policy_guardrail@v1`), or the operator's change-record
  store (where the remediation is owner-driven manual) — receives
  the remediation attempt and produces the `control.patch_evidence@v1`
  attestation.
- The **CSPM platform** — re-receives the targeted re-scan invocation
  against the same baseline rule and resource, and produces
  `__remediation_verified__`.
- The **security-engineering on-call** — receives the escalation
  payload (finding, attempted remediation, failing re-scan
  evidence) when `__remediation_verified__` is false.
- The **metrics layer** consuming `kpi.mttd_cloud_misconfig@v1`,
  `kpi.mttr_cloud_misconfig@v1`,
  `kpi.cloud_posture_coverage@v1`, and
  `kri.recurring_cloud_misconfig@v1` — the recipient is the
  aggregated counter, not the per-finding identifier.

External / upstream recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **cloud-provider control plane** (AWS, Azure, GCP, or an
  EU-sovereign equivalent) — the workflow reads from the
  provider's posture surface (Security Hub, Defender for Cloud,
  Security Command Center) at ingest and writes to the provider's
  configuration surface during the remediation step. The provider
  is therefore a processor for the resource-state read/write and a
  controller in its own right for the identity / IAM principal
  records the audit log captures.
- The **operator-bound posture-management processor** (where the
  operator runs a CSPM platform that is not the cloud provider's
  native one) — receives the re-scan request and emits the
  Compliance Finding (2003) and Cloud Resources Inventory Info
  (5023) OCSF events.
- The **operator-bound ticketing / chat / paging processor** —
  receives the notification payload and, in the escalation path,
  the on-call page.
- The **operator-bound IaC pipeline processor** (where the
  remediation is auto-generated as a pull request) — receives the
  proposed change and the resource-and-owner enrichment that
  supports it.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record
names the dependency so a sovereignty review can verify it. The
cloud-provider control plane is the dependency most operators
already cover under a master service agreement with their cloud
provider; the data-flow record names it explicitly so the
sovereignty surface remains auditable.

## 5. Retention

The workflow itself is stateless across findings — the durable
retention horizons are the operator's CSPM platform, the operator's
change-record store, the operator's ticketing / paging processors,
and the metric layer:

- **Finding records** are owned by the operator's CSPM platform.
  Retention follows the platform's policy (typical defaults: 90
  days for closed informational findings, 12 months for closed
  medium-and-above findings driving a remediation, indefinite for
  findings that escalated and remain in the recurring-misconfig
  KRI's correlation window). The workflow does not introduce a
  separate copy of the finding; `__finding_id__` is the
  workflow's handle on the platform's record.
- **Enrichment records** (resource, owner, severity) are derived at
  workflow runtime from the operator's cloud inventory and
  ownership graph; they are not persisted by the workflow itself
  beyond the finding's lifetime. The cloud-inventory record's
  retention is the inventory platform's policy
  (`telemetry.ocsf.cloud_resource_inventory@v1`); the
  ownership-graph record's retention is the operator's HRIS /
  team-directory retention.
- **Suppression linkage and exception records** — when the finding
  matches an existing exception or known-deviation record, the
  workflow links the finding to that record and the suppression
  is counted against `kri.recurring_cloud_misconfig@v1`. The
  exception record's own retention (typically time-boxed to the
  exception's expiry plus an audit horizon, often 12 months) is
  owned by the operator's exception-management process; the
  framework records the linkage, not the exception text.
- **Remediation-attempt evidence** — the
  `control.patch_evidence@v1` artifact (IaC pull-request URL,
  change-record identifier, runbook execution log) is retained
  by the operator's change-record store under the operator's
  audit retention policy (typically 2–7 years for regulated
  entities under NIS2 / DORA audit obligations).
- **Re-scan output** — `__remediation_verified__` and the
  re-scan's Compliance Finding (2003) event follow the CSPM
  platform's retention; the workflow does not introduce a
  separate horizon.
- **Notification / escalation payloads** — the ticketing entry, the
  chat message, the page event inherit the respective processor's
  retention (typical defaults: 12 months for ticketing, 90 days
  for chat, 12 months for paging audit-trail).
- **Metric counters** —
  `kpi.mttd_cloud_misconfig@v1`,
  `kpi.mttr_cloud_misconfig@v1`,
  `kpi.cloud_posture_coverage@v1`, and
  `kri.recurring_cloud_misconfig@v1` aggregate over the metric
  layer's rollup horizon and do not retain per-finding identifiers
  past that rollup.

No copy of the cloud provider's credentials, the CSPM platform's
session material, or the IaC pipeline's deployment credentials is
retained by the workflow beyond the per-step call; secret handling
is the runtime's responsibility per directive #7 of the project's
core directives (env-injected, never persisted by the workflow).

## 6. Cross-border transfers

**No transfer** for the default sovereign-hosted path. The workflow
is designed to execute end-to-end on the operator's sovereign-hosted
runtime (one of the EU-hostable reference targets — n8n self-host,
Temporal self-host, or LangGraph self-host on Nebul / OVHcloud /
Scaleway / Hetzner) against an EU-region cloud account, an
EU-region CSPM platform endpoint, an EU-region ticketing /
paging surface, and an EU-region IaC pipeline.

The technical controls that hold this scoring (FOUNDATION
property #3 — sovereignty):

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow.
- The cloud-provider control-plane calls (AWS, Azure, GCP, or an
  EU-sovereign equivalent) are pinned to an EU region by the
  operator's account configuration; the provider's regional
  control plane is the boundary that holds the
  `__resource_id__` lookup, the IAM-policy read, and the
  remediation write within the EU.
- The CSPM platform's read / re-scan endpoints are EU-region
  endpoints (Security Hub / Defender for Cloud / Security
  Command Center in their EU regions; or an EU-hosted
  third-party CSPM platform).
- The ticketing / chat / paging processors are EU-region or
  EU-hostable (self-hosted ticketing / chat / paging are the
  sovereign reference; SaaS variants are operator-bound to an
  EU region).
- The IaC pipeline runs on the operator's EU-hosted CI surface;
  the pull-request review and merge happen inside the
  operator's sovereign repository host.
- The OCSF Compliance Finding (2003) and Cloud Resources
  Inventory Info (5023) events emit to the operator's
  telemetry store under the operator's region pinning.
- No public-cloud-AI endpoint is called during ingest,
  enrichment, branching, notification, remediation, or re-scan;
  the workflow's logic is deterministic against the playbook's
  declared variables and step contract.

**Non-EU processor bindings are explicit re-score gates.** The
cloud_misconfiguration workflow has more processor bindings than
most workflows in the catalogue, and each is a potential
non-sovereign substitution that breaks this scoring:

- **Non-EU cloud-provider region.** If the operator binds an
  account whose control plane is outside the EU (a US-region
  AWS account, an APAC-region GCP project), the
  `__resource_id__` lookup, the IAM-policy read, and the
  remediation write all cross the border. Re-score under
  "transfer under SCCs / BCRs / derogation" (the EU-US Data
  Privacy Framework where the provider is a certified US
  recipient, otherwise standard contractual clauses), name the
  third country, and document the supplementary measures
  (customer-managed encryption keys held in the EU, audit-log
  region pinning to the EU even where the resource sits
  elsewhere).
- **Non-EU CSPM platform.** US-hosted CSPM SaaS is common; if
  the operator binds one, the finding record and the
  enrichment evidence are processed in the US. Re-score under
  the same Chapter V instruments, name the platform's hosting
  country, and document the pseudonymisation or scrubbing
  applied to owner / principal / actor identifiers before they
  leave the EU.
- **Non-EU ticketing / chat / paging processor.** Most of the
  popular SaaS surfaces have US-hosted control planes. The
  notification step's payload (owner identifier, resource
  identifier, severity, finding link) reaches the processor's
  control plane on call; re-score and document the same way.
- **Non-EU IaC pipeline host.** Where the operator's IaC
  pipeline runs on a US-hosted code-forge SaaS, the remediation
  pull request and its provenance metadata cross the border;
  re-score and document.

The transfer direction across these bindings is
operator → processor for the read / call / push and
processor → operator for the response; both legs are scored.
Sovereignty review at compile time is the gate, and the
binding does not go live until the re-scored data-flow entry
is in place.

## 7. Data subject rights

- **Access (Art. 15).** Where a data subject in §3 — most often
  an operator-internal resource owner, IAM principal, change
  actor, or responder — exercises a Subject Access Request
  against the operator, the SAR is answered by querying the
  operator's CSPM platform on `__owner_id__` /
  `__resource_id__` for findings the subject is named on, the
  operator's change-record store on the
  `control.patch_evidence@v1` artifacts the subject authored or
  was named on, the operator's ticketing / chat / paging
  processors on the notification and escalation payloads, and
  the operator's audit-log telemetry on
  `telemetry.ocsf.compliance_finding@v1` events. The workflow
  does not introduce a separate storage location beyond those
  parents; the parents' SAR-response procedures apply.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes — owner identity is resolved
  from the operator's ownership graph at runtime, IAM principal
  identifiers are read from the cloud provider's IAM surface,
  and audit-log actor identifiers are captured-as-emitted by
  the cloud provider. Rectification of an owner attribution
  flows through the operator's ownership-graph maintenance
  process (HRIS / team-directory) and propagates on the next
  enrichment cycle; rectification of an IAM principal record
  flows through the cloud provider's IAM surface; rectification
  of an audit-log actor flows through the cloud provider's
  audit-log corrections process where one exists. Direct
  rectification against the workflow's persisted records is not
  operationally meaningful.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing of the CSPM finding
  record on the platform's TTL, ageing of the change-record on
  the change-store's audit retention, ageing of the
  notification / paging records on the processor's TTL, and
  the metric-layer rollup horizon collectively erase the
  workflow's copy of the metadata. A standalone subject-
  initiated erasure request flows through each parent
  processor's erasure procedure; the operator weighs the
  request against the **Art. 17(3)(b)** exemption (compliance
  with a legal obligation under NIS2 / DORA configuration-
  audit requirements) and the **Art. 17(3)(e)** exemption
  (establishment, exercise, or defence of legal claims arising
  from the misconfiguration). The Recital 49 ground supports
  retention only where the data is still strictly necessary
  and proportionate to maintaining network and information
  security; closed-and-aged findings beyond their audit
  horizon do not satisfy that test.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(f)** (operators outside NIS2 / DORA scope, or
  operators choosing legitimate interests as primary), a data
  subject can object to the processing on grounds relating to
  their particular situation. The subject set in §3 is
  largely operator-internal (the operator's own staff and IAM
  principals); an internal subject's objection is handled by
  the operator's HR / privacy function via the same channel
  that handles workplace-monitoring objections. Operators
  under the **NIS2 Art. 21(2)(e) / 21(2)(i)** or **DORA Art. 9**
  secondary basis from §2 should note that the legal-obligation
  basis is not displaced by Art. 21 objection; the workflow
  continues to process the finding under that basis, with the
  objection recorded and the operator's lawful-basis
  documentation updated.
- **Automated decision-making (Art. 22).** The
  `known false positive?` branch is a deterministic lookup
  against a documented exception or known-deviation record;
  the `remediation verified?` branch is a deterministic
  comparison against the re-scan output. Neither produces a
  legal or similarly significant effect on a natural person:
  the workflow acts on infrastructure-configuration state, not
  on a subject's rights or eligibility. The downstream
  remediation (an IaC pull request bound to
  `control.iac_policy_guardrail@v1`, an IAM-policy rewrite
  bound to `control.cloud_identity_least_privilege@v1`) is a
  bulk-defensive change against the resource's configuration,
  not a per-subject adjudication. Art. 22 therefore does not
  apply to the workflow as shipped. If an operator binds a
  machine-learned severity-scoring model whose output sets
  `__severity__` without human review and triggers an
  automated remediation that materially changes a named IAM
  principal's access rights, the operator MUST re-score this
  section, surface the Art. 22 applicability, and document the
  safeguards (right to obtain human intervention, right to
  contest the decision) the operator provides.

## 8. Outbound personal-data transfer

The workflow's outbound legs that carry personal data outside the
operator's incident-/finding-case boundary are all
**operator-bound processor egress under GDPR Art. 28**, not
controller-to-controller transfers to a regulator or peer operator.
The CSPM finding chain has no statutory outbound-notification leg of
its own — significant breaches uncovered by a misconfiguration hand
off to the `incident_management` and `data_exfil` workflows, which
carry the regulator-submission scoring in their own §8.

**Leg A — Notification processor egress (ticketing / chat / paging).**

- *Destination class.* Operator-bound processor under GDPR Art. 28 —
  the operator's pre-bound notification surface (ticketing,
  chat, paging) that receives the resource-owner notification per
  `__severity__`, and the security-engineering on-call page when
  `__remediation_verified__` is false.
- *Transfer mechanism.* **No transfer** under the default sovereign-
  stack posture: self-hosted ticketing / chat / paging on an EU-region
  endpoint, or an EU-region SaaS variant. A non-EU control plane (a
  US-hosted SaaS ticketing / chat / paging surface, common in the
  market) MUST be re-scored under **SCCs (Art. 46)** with the
  EU-US Data Privacy Framework cited where the processor is a
  certified US recipient; supplementary measures are operator-held
  encryption keys on the notification payload and minimisation of the
  payload's owner / principal identifiers (handle-only, no work
  email) before egress.
- *EU-residency posture (Directive 1).* Default is EU-resident
  notification processors only. The technical controls that hold
  the posture are the operator's compile-time binding of the
  notification channel and the sovereignty review at compile time;
  the framework ships no default endpoint.
- *Data minimisation on egress (Art. 5(1)(c)).* The notification
  payload carries the resource-owner identifier (`__owner_id__`),
  the resource identifier (`__resource_id__`), `__severity__`, and
  the finding link — not the IAM-principal set, not the audit-log
  actor identifier, not the full Compliance Finding (2003) body.
  The escalation page carries the same fields plus the failing
  re-scan evidence; no per-principal identifiers in the page text.

**Leg B — IaC pipeline egress (remediation pull request).**

- *Destination class.* Operator-bound processor under GDPR Art. 28 —
  the operator's IaC pipeline / code-forge surface receiving the
  proposed remediation under `control.iac_policy_guardrail@v1`.
- *Transfer mechanism.* **No transfer** when the IaC pipeline is
  the operator's EU-hosted CI surface. A non-EU code-forge SaaS host
  MUST be re-scored under **SCCs (Art. 46)** naming the third
  country and the transfer instrument; supplementary measures are
  pseudonymisation of the proposed-change provenance metadata
  (commit author / reviewer identifiers) and encryption-at-rest
  with operator-held keys on the pipeline's artifact store.
- *EU-residency posture (Directive 1).* Default is the operator's
  EU-hosted code-forge / pipeline surface; the framework ships no
  default and the binding is operator-bound at compile time.
- *Data minimisation on egress (Art. 5(1)(c)).* The pull request
  carries the proposed configuration delta, the violated baseline
  rule fingerprint, and the resource-and-owner enrichment that
  supports it; IAM principal identifiers appear only where the
  remediation rewrites an over-permissive identity binding and the
  rewrite itself is the change. Audit-log actor identifiers are
  not transmitted to the pipeline.

**Leg C — CSPM platform egress (re-scan invocation).**

- *Destination class.* Operator-bound processor under GDPR Art. 28
  (where the CSPM platform is a third-party SaaS) or the cloud
  provider's native posture surface (where the CSPM platform is
  the provider's own — Security Hub / Defender for Cloud / Security
  Command Center). The egress payload is the targeted re-scan
  invocation against the same baseline rule and resource.
- *Transfer mechanism.* **No transfer** when the CSPM platform's
  endpoint is EU-region (the provider's EU-region native CSPM, or
  an EU-hosted third-party CSPM). A non-EU CSPM SaaS host MUST be
  re-scored under **SCCs (Art. 46)** with the EU-US Data Privacy
  Framework cited where applicable; supplementary measures are
  scrubbing of owner / principal / actor identifiers from the
  re-scan request before egress and pseudonymisation of any
  principal identifiers visible in the platform's finding-evidence
  pane.
- *EU-residency posture (Directive 1).* Default is an EU-region
  CSPM endpoint; the binding is operator-bound at compile time and
  the sovereignty review is the gate.
- *Data minimisation on egress (Art. 5(1)(c)).* The re-scan request
  carries `__resource_id__`, the baseline rule fingerprint, and
  the operator's tenant / project / account identifier — not the
  IAM-principal set, not the audit-log actor identifier, not the
  ownership-graph fields used in the internal notification step.

**Leg D — Cloud-provider control-plane egress (IAM-policy read,
remediation write).**

- *Destination class.* The cloud provider's control plane acts as
  a controller in its own right for the identity / IAM principal
  records its audit log captures, and as a processor on the
  operator's behalf for the resource-state read and the remediation
  write. The IAM-principal identifiers in the policy body are
  read at enrichment time; the remediation write rewrites the
  policy under `control.cloud_identity_least_privilege@v1`.
- *Transfer mechanism.* **No transfer** under the default sovereign-
  stack posture: an EU-region cloud account whose control-plane
  region is pinned to the EU (AWS / Azure / GCP EU regions, or an
  EU-sovereign equivalent). A non-EU control-plane region — an
  account whose region is set to a US or APAC home region — MUST
  be re-scored under **SCCs (Art. 46)** with the EU-US Data Privacy
  Framework cited where the provider is a certified US recipient;
  supplementary measures are customer-managed encryption keys
  held in the EU on the IAM-policy store and audit-log region
  pinning to the EU even where the resource sits elsewhere.
- *EU-residency posture (Directive 1).* Default is an EU-region
  control plane. The operator's account-configuration binding is
  the boundary that holds `__resource_id__` lookup, IAM-policy
  read, and remediation write within the EU; sovereignty review
  at compile time refuses non-EU regions on the SKELETON binding.
- *Data minimisation on egress (Art. 5(1)(c)).* The IAM-policy
  read returns only the principal set bound to the violated
  resource; the remediation write rewrites only the bindings the
  violated baseline rule fingerprints. No bulk export of the
  account's IAM graph is performed by the workflow.

Cross-reference §6: the cross-border scoring as a whole is
**no transfer** for the default sovereign-stack posture, consistent
with all four legs above scoring no-transfer under operator-bound
EU-region processor endpoints. Any operator re-scoring of a leg
here (non-EU notification SaaS, non-EU code forge, non-EU CSPM,
non-EU cloud region) MUST be reflected in §6 in the same change so
the two sections do not disagree. The §8 enumerates each leg; the
§6 records the workflow's processing-as-a-whole transfer scoring.
