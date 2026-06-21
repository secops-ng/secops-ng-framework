# GDPR data flow — supply_chain_security

Per-workflow GDPR data-flow entry for the `supply_chain_security`
playbook (`playbook.supply_chain_security@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/supply_chain_security/playbook.cacao.json`](../../playbooks/supply_chain_security/playbook.cacao.json).

`SKELETON` layer: the workflow ships the topology and the
placeholder action contracts only; the action bodies (signal-source
ingestion, SBOM correlation, supplier-attestation lookup, evidence
emission) land in the CORE sibling card. The data-flow content below
is written against the contracts the SKELETON pins; the EXTEND
sibling re-reads this document once CORE binds the primitives and
narrows any section that needs refinement against real action logic
rather than the contract.

---

## 1. Purpose

> **GDPR Art. 5(1)(b) — purpose limitation.**

Process one inbound supply-chain signal per execution to detect
supply-chain compromises that reach the operator through a direct
supplier, service provider, or upstream software component, and emit
one supply-chain-evidence artifact pinning the verdict for downstream
review. The operational outcome is a per-execution audit-trail entry
against the NIS2 Article 21(2)(d) supplier-security obligation —
sufficient for a reviewer to see whether each inbound signal closed
as no-impact, was held under watch, or was confirmed as a
supply-chain compromise that opens the F-WF-05
`incident_management` lifecycle. Personal data is touched only
incidentally to identify the affected supplier and route the
verdict; the workflow does not run subject-level analytics.

## 2. Lawful basis

> **GDPR Art. 6(1).**

Primary: **Art. 6(1)(f) legitimate interests** — operating a
supply-chain-security capability under NIS2 Article 21(2)(d) is a
recognised legitimate interest of the operator (and of every EU
recipient of services that depend on the operator's supply chain).

Secondary: **Art. 6(1)(c) legal obligation** — applies where the
operator is in scope of the NIS2 national transposition that gives
Art. 21(2)(d) direct effect against them as an essential or
important entity. When the operator falls under that transposition
they may rely on Art. 6(1)(c) as primary and Art. 6(1)(f) as
secondary; the workflow's data flows do not change.

No special-category data (Art. 9) is in scope: the records the
workflow operates on identify suppliers as organisations and
affected components by name / version / hash, not by data-subject
attributes. Where a signal source incidentally carries a natural
person's contact handle (e.g. a researcher's email on an upstream
CVE advisory), that handle is held only as opaque routing metadata
and is not used to profile the data subject.

## 3. Categories of data subjects and personal data

> **GDPR Art. 30(1)(c).**

Data-subject categories:

- **Operator personnel** named as the recipient of the
  supply-chain-evidence artifact (security-operations role
  handles, responder rota ids).
- **Upstream supplier / service-provider points of contact**
  named on inbound signals — typically the disclosing
  researcher on a CVE advisory, the supplier's security contact
  on a vendor advisory, or the responsible-disclosure mailbox
  on an SBOM-watch alert.

Personal-data categories:

- **Work email addresses and ticketing-source handles** (operator
  personnel, supplier contacts).
- **Role-shaped identifiers** (operator rota id, supplier
  responsible-disclosure mailbox) — the workflow operates against
  role handles by convention; personal-user responder handles are
  out of scope.
- **Signal-payload metadata** that may incidentally carry personal
  identifiers (a researcher's name on a CVE acknowledgement, an
  upstream advisory's contact line).

The workflow does NOT process: end-user account contents, biometric
data, location data, or any Art. 9 special-category data.

## 4. Recipients

> **GDPR Art. 30(1)(d).**

- **Operator security-operations team** — the supply-chain-evidence
  artifact lands on the F-CP-03 supply-chain evidence stream the
  operator's reviewers consume.
- **Downstream playbook
  `playbook.incident_management@v1`** — receives the handoff when
  the verdict is `confirmed_compromise`. The handoff envelope shape
  and the per-step regulator-notification surface land on F-WF-05.
- **No external processor is invoked by this playbook directly.**
  The CORE sibling card may bind primitive helpers to operator-
  supplied signal sources (threat-intel feeds, SBOM-watch tooling,
  supplier-attestation feeds). Any external processor the operator
  configures at compile time is governed by a Data Processing
  Agreement the operator already holds — the agreement itself
  lives outside the framework; the data-flow doc records that the
  dependency exists.

## 5. Retention

> **GDPR Art. 5(1)(e) — storage limitation.**

The CACAO artifact itself holds no personal data at rest. The
per-execution records the workflow produces (the assessment record,
the supply-chain-evidence artifact) are written to operator-bound
stores under the operator's existing retention policy for the
F-CP-03 supply-chain evidence stream. The SKELETON layer does not
pin a default retention period — that policy is operator-supplied
at compile time and is the same policy that governs every artifact
on the F-CP-03 stream. Where a signal incidentally carries a
researcher contact handle, that handle is retained only as long as
the parent evidence artifact and is purged with it.

## 6. Cross-border transfers

> **GDPR Chapter V (Art. 44–50).**

**Score: no transfer at the framework layer.** The framework ships
no default non-EU endpoint, no default hosted feed dependency, and
no vendor SDK bundling. Operator-supplied signal sources MAY route
data through a non-EU processor; the operator is responsible for
scoring the transfer (adequacy / SCC / derogation) at the
configuration boundary. The hygiene-linter forward-public bar
forbids the framework from defaulting to a non-EU endpoint, which
is the technical control that holds this position at the artifact
layer.

## 7. Data subject rights

> **GDPR Art. 12–22.**

- **Access (Art. 15)** — operator answers SARs by querying the
  F-CP-03 supply-chain evidence store for artifacts that carry the
  data subject's handle (operator personnel rota id, upstream
  supplier contact handle).
- **Rectification (Art. 16)** — the workflow does not store
  subject-supplied attributes that may be wrong; rectification is
  handled upstream at the operator's CMDB / supplier directory.
- **Erasure (Art. 17)** — answered by the retention hook in §5 on
  the F-CP-03 stream; expiry of the evidence artifact carries the
  incidental personal-data fields with it.
- **Objection (Art. 21)** — applicable when the lawful basis in §2
  is Art. 6(1)(f). An objection is operationally handled by
  pausing the workflow for the affected supplier contact and
  triaging the verdict manually; the artifact still emits with the
  closed-shape verdict so the audit trail stays continuous.
- **Automated decision-making (Art. 22)** — does not apply: the
  workflow's verdict (`no_impact` / `watch` /
  `confirmed_compromise`) governs the operator's response posture,
  not a legal or similarly significant effect on the data subject.
  The first-class handoff into `incident_management` is the
  technical control that rules Art. 22(1) out for any verdict that
  would otherwise gate a subject-affecting action.
