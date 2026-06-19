# GDPR data flow — threat_intel_ingest

Per-workflow GDPR data-flow entry for the `threat_intel_ingest`
cookbook playbook (`playbook.threat_intel_ingest@v1`). Filled in
against [`_data-flow-template.md`](./_data-flow-template.md). Together
the seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/threat_intel_ingest/`](../../playbooks/threat_intel_ingest/).

---

## 1. Purpose

The workflow exists to ingest external cyber threat intelligence —
typically a TAXII 2.1 collection or a STIX 2.1 bundle exposed by a
CSIRT, an ISAC, or a community MISP instance — so the response team
can shorten the gap between an indicator being published upstream and
that indicator being actionable inside the operator's defensive
stack. Concretely, the workflow pulls the upstream bundle, normalises
each STIX 2.1 Indicator / Malware / Threat-Actor SDO into the
playbook's canonical normalised-indicator record, branches on a
confidence threshold, propagates high-confidence indicators (IPs,
domains, file hashes) to the operator's perimeter / DNS / EDR
enforcement plane, and activates or refreshes the corresponding
upstream Sigma rules in the operator's SIEM so subsequent telemetry
matching the indicator produces an OCSF Detection Finding
(class_uid 2004). The purpose is bounded to that ingest-and-arm
decision and the metric hooks it produces; the workflow does not
publish indicators back upstream, does not enrich subjects against
external lookup services, and does not retain the raw bundle past
the normalisation step's dedup horizon.

## 2. Lawful basis

Primary: **GDPR Art. 6(1)(f) — legitimate interests**. The operator
has a legitimate interest in maintaining network and information
security, which **Recital 49** of the GDPR explicitly recognises as
a legitimate interest of the controller — including the processing
of personal data strictly necessary and proportionate to ensuring
network and information security against malicious code,
unauthorised access, and degradation of service. The processing
here — ingesting indicators that may include IP addresses or email
addresses attached to attacker or victim infrastructure,
normalising them, and arming defensive controls against them — is
necessary and proportionate to that interest, and the data subjects
implicated in §3 (attacker-side infrastructure operators, source
analysts who authored the indicator, incidental third parties whose
identifiers appear in an IOC tuple) have a reasonable expectation
that indicators published in a defensive-community feed are
consumed by defenders.

Secondary: where the operator is a regulated entity under the
**NIS2 Directive** and is obliged to maintain a threat-intelligence
capability under **NIS2 Art. 21(2)(b)** as transposed nationally,
**Art. 6(1)(c) — legal obligation** also applies. Operators
subject to sector-specific rules (DORA Art. 17 for financial
entities, the eIDAS-2 incident-handling regime for trust-service
providers) inherit the same secondary basis. Operators in the
**EU CSIRTs network** ingesting from the network's own feeds may
additionally rely on **Art. 6(1)(e) — public interest** task as
recognised in their national CSIRT mandate.

Special-category data (Art. 9) is not the target of the workflow.
STIX 2.1 SDOs are not designed to carry Art. 9 attributes; the
normalisation step in §3 retains only indicator value, type,
confidence, valid-from / valid-until, and the upstream
created_by_ref. If an upstream feed publishes Art. 9 attributes
attached to a victim record (a leaked database carrying health
or trade-union identifiers), the normalisation step does not
extract or persist them — the workflow's canonical record carries
indicator-level metadata only.

## 3. Categories of data subjects and personal data

Data subjects:

- **Attacker-side infrastructure operators** — natural persons
  whose IP addresses, registered domains, email addresses, or
  hash-attributable artifacts appear in the upstream feed as
  malicious-indicator values. The CJEU's **Breyer** ruling
  (C-582/14) confirms that dynamic IP addresses are personal data
  in the hands of a controller who has a lawful means to identify
  the subscriber; the workflow assumes that holds for any IP
  indicator the operator receives.
- **Source analysts and source organisations** named on the
  upstream STIX bundle's `created_by_ref` identity SDOs — CSIRT
  analysts, MISP community members, ISAC researchers — whose
  identifiers ride along with the indicators they published.
- **Incidental third parties** whose identifiers appear in an
  indicator tuple because they share infrastructure with the
  attacker (a benign tenant on a compromised host, a forwarder
  on a hijacked domain, an end user whose machine was
  conscripted into an attacker-controlled botnet). The workflow
  cannot disambiguate these from primary attackers at ingest
  time; both are subject to the same processing until later
  evidence narrows the scope.
- **Operator-internal responders** whose `__feed_id__` selection,
  threshold tuning, and propagation decisions are recorded
  against `kpi.mttr_blocklist_propagation@v1` and
  `kpi.coverage_threat_intel_feed@v1` — the responder's
  identifier is not stored in the metric counter itself, but is
  visible in the runtime's audit log of the propagation step.

Categories of personal data:

- **Network identifiers** — IPv4 and IPv6 addresses, IP-range
  CIDRs, autonomous-system numbers, and the geographies derived
  from those addresses, where the indicator type is
  `ipv4-addr` / `ipv6-addr` in the upstream STIX bundle.
- **Domain and URL identifiers** — registered domains, fully
  qualified domain names, URLs, URL paths and query strings,
  where the indicator type is `domain-name` / `url`. WHOIS-style
  registrant fields are not extracted; only the indicator value
  itself is normalised.
- **Email-address identifiers** — sender and reply-to addresses
  where the indicator type is `email-addr` (typical for
  phishing-campaign feeds and BEC indicators).
- **File-content identifiers** — MD5, SHA-1, SHA-256, and
  imphash values, plus filenames as observed on the upstream
  side. Hashes are pseudonymous and are personal data only when
  reasonably linkable to a natural person via the operator's
  surrounding context (a hash of a document the operator knows
  was authored by a named subject); the workflow treats them
  with the same care as the other identifier categories.
- **Provenance metadata** — the upstream feed's `__feed_id__`,
  the source TAXII collection URL, the bundle's `created_by_ref`
  identity (the source analyst or organisation), the STIX
  `valid_from` / `valid_until` window, and the upstream
  confidence score.
- **Operational counts** — `__indicator_count__`,
  `__high_confidence__`, the per-indicator propagation event,
  and the OCSF Detection Finding records emitted on subsequent
  SIEM matches (class_uid 2004) under the operator's existing
  OCSF projection.

Bundle bodies, raw STIX SDOs, and TAXII envelope material are
processed transiently for the normalisation step; only the
canonical normalised-indicator record, the provenance metadata,
and the operational counts above are persisted past the
workflow's lifetime.

## 4. Recipients

Internal recipients:

- The **response team** owning the ingest binding — the operator's
  threat-intel analysts and detection engineers who select the
  feed, tune the confidence threshold, and review the propagation
  outcome.
- The **detection plane** receiving the activated Sigma rule
  references — the operator's SIEM and the SIEM's rule store. The
  SIEM in turn emits `telemetry.ocsf.detection_finding@v1`
  (class_uid 2004) on rule match.
- The **enforcement plane** receiving high-confidence indicators —
  the operator's perimeter firewall, DNS sinkhole, and EDR
  allow/deny list.
- The **metrics layer** consuming
  `kpi.mttd_threat_intel_indicator@v1`,
  `kpi.mttr_blocklist_propagation@v1`, and
  `kpi.coverage_threat_intel_feed@v1` — the recipient is the
  aggregated counter, not the per-indicator identifier.

External / upstream recipients (operator-bound, named in the
compile-target binding rather than the playbook):

- The **upstream feed publisher** identified by `__feed_id__` —
  typically the **ENISA-coordinated EU CSIRTs network** feeds, a
  **national CSIRT** bulletin (CERT-EU, CERT.PT, NCSC-NL,
  BSI-CERT-Bund, ANSSI CERT-FR, and equivalents), or a community
  **MISP** instance the operator participates in. The workflow
  pulls; it does not push, so the upstream is a source rather
  than a recipient of operator-side data. The feed publisher
  becomes a recipient only of the metadata implicit in the TAXII
  poll (the operator's source IP, the operator's TAXII client
  identifier, the polled collection identifier and timestamp).
- The **enforcement-plane processors** (firewall vendor cloud
  console, DNS-filter SaaS, EDR vendor backend) that receive the
  high-confidence indicator push, where the operator binds a
  vendor-hosted control plane rather than a self-hosted one.
- The **SIEM / OCSF telemetry store** receiving the
  `telemetry.ocsf.detection_finding@v1` events emitted on
  subsequent rule match.

Each operator-bound processor MUST have a Data Processing Agreement
(GDPR Art. 28) in place before the binding is wired in production;
the framework does not ship the DPAs, but the data-flow record
names the dependency so a sovereignty review can verify it. Where
the upstream feed publisher is itself a controller under a CSIRTs-
network or ISAC sharing agreement (Art. 26 joint controllership
where applicable), the arrangement governing that controller-to-
controller exchange lives outside the framework but is named here
so the dependency is auditable.

## 5. Retention

The workflow itself is stateless across polls — the durable
retention horizons are the operator's normalised-indicator store,
the operator's detection-rule store, the operator's enforcement
plane, and the operator's OCSF telemetry store:

- **Normalised-indicator records** are keyed by indicator value and
  deduplicated against records seen within the last 24 hours per
  the normalisation step. The persisted record carries the
  indicator value, type, confidence, provenance metadata, and
  `valid_from` / `valid_until`. Retention follows the upstream
  `valid_until` where present; absent that, the operator's
  threat-intel-store policy (typically 90 days for low-confidence
  records, 12 months for high-confidence records that have driven
  a confirmed detection) applies. Records superseded by a more
  recent indicator with the same value are not retained twice.
- **Sigma-rule activation state** is owned by the operator's SIEM
  and follows the SIEM's rule-store retention; the workflow does
  not create a separate copy. When the upstream SigmaHQ rule is
  deprecated or withdrawn, the operator's next ingest cycle
  deactivates the corresponding rule reference in the SIEM.
- **Enforcement-plane entries** (firewall, DNS sinkhole, EDR
  blocklist) inherit the enforcement processor's retention. The
  workflow records the propagation event onto
  `kpi.mttr_blocklist_propagation@v1` for the operator's
  retention window; the blocklist entry itself is aged on the
  enforcement processor's own TTL (typical defaults: 30 days for
  IP, 90 days for domain, indefinite for high-confidence file
  hash, all operator-configurable).
- **OCSF Detection Finding events** emitted on subsequent SIEM
  match follow the operator's telemetry retention policy on the
  underlying OCSF store; the workflow does not introduce a
  separate retention horizon for them.
- **Raw STIX bundles and TAXII envelopes** are processed
  transiently for the normalisation step and are not persisted
  beyond that step's working buffer.

No copy of the raw upstream bundle, the TAXII session credentials,
or the underlying authentication material is retained by the
workflow beyond the poll-and-normalise span; the durable artifacts
are the normalised records, the provenance metadata, the
propagation events, and the OCSF findings.

## 6. Cross-border transfers

**No transfer** for the default sovereign-hosted path. The workflow
is designed to execute end-to-end on the operator's sovereign-hosted
runtime (one of the EU-hostable reference targets — n8n self-host,
Temporal self-host, or LangGraph self-host on Nebul / OVHcloud /
Scaleway / Hetzner) with EU-pinned upstream feeds, EU-pinned
enforcement-plane processors, and the operator's EU-pinned SIEM /
OCSF store.

The technical controls that hold this scoring (FOUNDATION
property #3 — sovereignty):

- The reference compile targets are framework-agnostic and run on
  the operator's own sovereign-hosted runtime; no SecOps-NG-hosted
  egress path exists in the workflow. The orchestrator the
  operator already runs is the execution boundary.
- The default upstream feed binding is an **EU-resident publisher**
  — the **ENISA-coordinated EU CSIRTs network** feeds, a
  **national CSIRT** bulletin from an EU member state, or a
  community **MISP** instance the operator participates in that is
  itself EU-hosted. The TAXII poll therefore stays within the
  EU/EEA.
- The enforcement-plane calls (perimeter, DNS, EDR) are
  operator-bound at compile time and target the operator's
  EU-region control planes directly; the playbook itself does not
  call a hosted SecOps-NG enforcement service.
- The OCSF Detection Finding records emit to the operator's
  telemetry store under the operator's region pinning; no
  external aggregation is invoked.
- No public-cloud-AI endpoint is called during normalisation,
  branching, propagation, or activation; the normalisation step
  is a deterministic STIX→canonical mapping and runs inline.

**Non-EU upstream feeds are an explicit re-score gate.** Threat-
intel feeds, more than most workflows in the catalogue, may
reference or be published by non-EU sources — US-hosted ISAC
feeds, US-government feeds (CISA AIS, FBI flash bulletins),
commercial CTI vendors hosted outside the EU, and APAC-based
community feeds. The default workflow does not bind any of these,
but if an operator binds a non-EU upstream feed publisher,
operator MUST re-score this section under "transfer under SCCs /
BCRs / derogation", name the third country and the transfer
instrument (the EU-US Data Privacy Framework where the publisher
is a certified US recipient, otherwise standard contractual
clauses or an Art. 49 derogation), and document the
supplementary measures (the TAXII client identifier and source
IP are the operator's controlled disclosure to the publisher;
no operator-side telemetry leaves with the poll). The transfer
direction is operator → publisher for the poll metadata and
publisher → operator for the bundle itself; both legs are
scored.

Likewise, if an operator binds a vendor-hosted enforcement-plane
processor whose control plane is outside the EU, or a non-EU
SIEM / telemetry processor, this scoring breaks and the same
re-scoring applies before the binding goes live. Sovereignty
review at compile time is the gate.

## 7. Data subject rights

- **Access (Art. 15).** Most of the personal data in this workflow
  is attacker-side or upstream-publisher metadata that the
  operator does not hold against a natural person it can directly
  contact. Where a data subject does exercise a Subject Access
  Request against the operator and an identifier in §3 (an IP
  address, an email address, a domain, a hash) can be matched
  against the operator's normalised-indicator store, the SAR is
  answered by querying that store on the identifier and the
  operator's OCSF telemetry store on the
  `telemetry.ocsf.detection_finding@v1` events the workflow
  caused to be emitted. Source analysts named on `created_by_ref`
  are answered by querying the provenance metadata on the
  normalised record. The workflow does not introduce a separate
  storage location beyond those parents.
- **Rectification (Art. 16).** The workflow does not store
  subject-supplied attributes — every persisted identifier and
  every piece of provenance metadata is captured-as-observed
  from the upstream bundle. Rectification at a subject's request
  against an indicator the workflow accepted is not operationally
  meaningful; an indicator that turns out to be a false positive
  (a benign IP misclassified upstream, a legitimate domain
  flagged in error) is corrected by an upstream-publisher
  retraction or a confidence override at the operator's next
  ingest cycle, not by an Art. 16 rectification against the
  operator. The operator's downstream incident_management
  playbook is the path for false-positive remediation if an
  enforcement-plane block has caused subject-side harm.
- **Erasure (Art. 17).** The retention hooks in §5 are the
  operational erasure pathway: ageing of the normalised-
  indicator store on the operator's threat-intel retention TTL,
  aging of the enforcement-plane entry on the processor's TTL,
  and ageing of the OCSF event on the telemetry retention TTL
  collectively erase the workflow's copy of the metadata. A
  standalone subject-initiated erasure request flows through
  the operator's threat-intel-store erasure procedure and the
  enforcement-plane processor's erasure procedure, both of
  which the workflow inherits; the operator weighs the
  erasure request against the **Art. 17(3)(e)** exemption
  where retaining the indicator is necessary for the
  establishment, exercise, or defence of legal claims, and
  against the **Recital 49** legitimate-interest ground for
  retaining defensive indicators.
- **Objection (Art. 21).** Where the lawful basis is
  **Art. 6(1)(f)** (most operators), a data subject can object
  to the processing on grounds relating to their particular
  situation. The operational handling is to record the
  objection against the indicator value in the normalised-
  indicator store, suppress that value from the next
  enforcement-plane propagation cycle pending operator review,
  and route the operator's threat-intel analyst to the
  legitimate-interest balancing test for that specific value.
  Operators under the **NIS2 Art. 21(2)(b)** secondary basis
  from §2 should note that the legal-obligation basis is not
  displaced by Art. 21 objection; CSIRTs operating under a
  public-interest mandate per **Art. 6(1)(e)** similarly retain
  the indicator under the public-task basis.
- **Automated decision-making (Art. 22).** The
  `above confidence threshold?` branch is a deterministic
  threshold comparison against an upstream-published confidence
  score, not a machine-learned classifier producing a legal or
  similarly significant effect on a subject. The downstream
  enforcement actions — adding an IP / domain / hash to a
  blocklist, activating a Sigma rule that produces a SIEM alert
  — are bulk defensive actions against infrastructure
  identifiers rather than per-subject adjudications, and the
  operator's incident_management playbook arbitrates any
  subject-side harm a false-positive block causes. Art. 22
  therefore does not apply to the workflow as shipped. If an
  operator binds a machine-learned confidence-scoring model
  whose output sets `__high_confidence__` without analyst
  review and triggers enforcement-plane propagation against a
  natural person — for instance by enriching the indicator
  with attribution to a named subject before propagation — the
  operator MUST re-score this section, surface the Art. 22
  applicability, and document the safeguards (right to obtain
  human intervention, right to contest the decision) the
  operator provides.
