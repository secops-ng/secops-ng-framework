# soc2_crosswalk — cookbook walkthrough

Practitioner walkthrough of the **SOC 2 Trust Services Criteria (TSC)
crosswalk** shipped under
[`content/mappings/soc2/`](../../content/mappings/soc2/). This
walkthrough is aimed at operators who already run a control catalogue
against EU statutory obligations (NIS2, DORA, CRA, GDPR) and are asked
to answer for the same catalogue in SOC 2 / TSC terms — usually
because a US SaaS vendor, a cross-border customer, or an outsourced
processor frames its due-diligence surface that way. It is written
for community readers — regulated-sector operators, contributors
landing new anchors, and researchers reading the crosswalk as
reference material — not as commercial guidance or a legal / auditor
interpretation of the TSC.

The crosswalk is a **framework-agnostic**, portable artifact. It
carries no compiler-target detail and no runtime binding: the on-disk
YAML per Trust Services category is the machine-readable pointer, and
this cookbook is the connective narrative an operator reads once to
understand what the YAML asserts and how to walk it.

> SOC 2 is a private-sector assurance framework maintained by the
> AICPA (Trust Services Criteria 2017, as revised, delivered under
> attestation standard AT-C 105 / AT-C 205). It is **not** an EU
> statutory instrument. The crosswalk asserts that the named
> SecOps-NG artifacts exercise the criterion in practice; it does not
> constitute a legal, regulator, or auditor interpretation of the
> TSC, and it does not replace the EU regulatory mappings under
> `content/mappings/nis2/`, `content/mappings/dora/`,
> `content/mappings/cra/`, or `content/mappings/gdpr/` — those remain
> the authoritative pointer for the statutory surface an EU-operating
> entity has to discharge.

## 1. Why this matters

An EU-adjacent operator already has to discharge NIS2 Art. 21 risk-
management measures, DORA Chapter II ICT risk management, CRA vendor
obligations for products with digital elements, and GDPR technical
and organisational measures under Art. 32. Each of those surfaces is
already mapped, article-by-article, under `content/mappings/<axis>/`
and exercised by the shipped playbooks and controls in the SecOps-NG
catalogue.

The SOC 2 crosswalk adds a **structural interoperability layer** on
top of that catalogue. This is useful for practitioners in three
concrete ways.

- **US-vendor due diligence.** Where a US SaaS vendor, a cross-border
  customer, or an outsourced processor asks the operator to answer a
  SOC 2 questionnaire — or to attest that a particular criterion is
  discharged — the operator can point at the TSC criterion and walk
  the crosswalk down to the shipped SecOps-NG artifact that exercises
  it, without maintaining a parallel SOC 2-only control catalogue.
- **US-to-EU posture gap analysis.** An organisation that already
  holds a SOC 2 report (Type I or Type II) and is now bringing its
  posture into the EU statutory frame can walk the same catalogue
  from the TSC side and see, criterion by criterion, which anchors
  the EU regime mappings pick up in turn. Where the SecOps-NG
  catalogue does not exercise a TSC criterion (governance, board
  oversight, physical facilities, application-layer processing
  controls, privacy-programme surface) the crosswalk carries an
  explicit gap note naming the boundary.
- **Bridging vocabulary, not replacing evidence.** SOC 2 and the EU
  statutory regimes are not equivalents. SOC 2 is an assurance
  framework describing what an auditor tests; NIS2, DORA, CRA, and
  GDPR are statutory obligations describing what an operator has to
  do. The crosswalk lets the practitioner navigate between the two
  vocabularies against the same set of shipped artifacts. It does
  not fold either surface into the other, and it does not turn a
  SOC 2 report into evidence of EU statutory compliance (or vice
  versa).

The crosswalk is deliberately a **structural pointer**, not an
attestation. It does not tell an operator which criteria to
prioritise, whether to seek a Type I or a Type II opinion, what
trust services categories to include in the report scope, or how a
service auditor would evaluate the shipped evidence. Those are
operator-owned and auditor-owned decisions upstream of the SecOps-NG
catalogue.

## 2. What ships

Under `content/mappings/soc2/`:

| File | Category | Criteria | Count |
|------|----------|----------|-------|
| `tsc-security.yaml` | Security (Common Criteria) | CC1.1–CC9.2 | 33 |
| `tsc-availability.yaml` | Availability | A1.1–A1.3 | 3 |
| `tsc-confidentiality.yaml` | Confidentiality | C1.1–C1.2 | 2 |
| `tsc-processing-integrity.yaml` | Processing Integrity | PI1.1–PI1.5 | 5 |
| `tsc-privacy.yaml` | Privacy | P1.1, P2.1, P3.1, P4.1–P4.3, P5.1, P6.1, P6.7, P7.1 | 10 |
| `oscal-component-definition.json` | — | — | round-trip artifact |
| `README.md` | — | — | regime scope and file conventions |

The Security category (Common Criteria series) is the mandatory
baseline for any SOC 2 report. CC1–CC5 mirror the five COSO 2013
internal-control components (control environment, communication and
information, risk assessment, monitoring activities, control
activities); CC6–CC9 are the extensions specific to information
systems (logical / physical access, system operations, change
management, risk mitigation). The other four categories
(Availability, Confidentiality, Processing Integrity, Privacy) are
optional and included in a report only when the entity commits to
them as part of report scope.

An OSCAL 1.1.2 component definition for the whole SOC 2 surface
ships as `oscal-component-definition.json`, with a round-trip test
under `tests/content/` that pins its shape against the per-category
YAML. The D3FEND crosswalk against SOC 2 lives at
`content/mappings/d3fend/soc2.yaml`.

No AICPA Informative References ship here. Mappings between the
TSC and other catalogues (SP 800-53r5, ISO/IEC 27001:2022, HIPAA,
NIST CSF 2.0) are maintained by the AICPA and by the source-
catalogue owners; the SecOps-NG crosswalk asserts against the
operator's own catalogue only.

## 3. Navigating the crosswalk

Each per-category file is one YAML document with a top-level
`regime: soc2` key and an `entries` list. Each entry is a
**criterion** — one of the TSC criteria in the category — and
follows the same shape used by the other regime mappings under
`content/mappings/<axis>/`.

### 3.1 Criterion anatomy

A criterion entry looks like this (excerpted from `CC6.1`, logical
access controls):

```yaml
- id: soc2:cc6-1-logical-access-controls
  regulation:
    name: SOC 2
    instrument: AICPA Trust Services Criteria (2017, as revised)
    article: CC6.1
    url: https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2
  obligation: >-
    The entity implements logical access security software,
    infrastructure, and architectures over protected information
    assets to protect them from security events to meet the
    entity's objectives. Access is restricted to authorised users
    through identification, authentication, and authorisation
    controls.
  status: draft
  control_refs:
    - control.access_enforcement@v1
    - control.least_privilege@v1
    - control.cloud_identity_least_privilege@v1
  playbook_refs:
    - playbook.iam_auditor@v1
  notes: >-
    access_enforcement, least_privilege, and
    cloud_identity_least_privilege carry the logical-access-control
    anchors across on-prem and cloud; iam_auditor exercises the
    operational access-audit surface.
```

Fields worth naming explicitly:

- **`id`** — a stable identifier of the form
  `soc2:<criterion-slug>` where the slug carries the criterion
  number and a kebab-case phrase (`cc6-1-logical-access-controls`,
  `p4-2-retention`). The `soc2:` prefix distinguishes it from the
  other regime axes.
- **`regulation.article`** — the criterion identifier as it
  appears in the AICPA TSC document itself (for example `CC6.1`,
  `A1.2`, `P4.2`). This is the label an operator answering a SOC 2
  questionnaire matches against.
- **`obligation`** — the criterion text, restated in the crosswalk
  as the outcome the operator is being asked to discharge.
- **`control_refs`** — the SecOps-NG `content/controls/` anchors
  that exercise the criterion at the control-catalogue level.
  Empty (`[]`) with an explanatory `notes` block when the criterion
  is a pure governance / operator-owned obligation.
- **`playbook_refs`** — the SecOps-NG `content/playbooks/` anchors
  that exercise the criterion at the operational-workflow level.
  Empty when there is no operational playbook that discharges the
  criterion (typically governance-only entries).
- **`notes`** — the plain-language paragraph naming which slice of
  the criterion the catalogue anchors discharge and which slice
  remains operator-owned. This is where the boundary between
  SecOps-NG evidence and operator-owned evidence (board minutes,
  org charts, HR records, vendor contracts, privacy-programme
  documents) is drawn explicitly.

The `gap_note` shape used by the NIST CSF crosswalk at the
Subcategory level is not used here; the SOC 2 crosswalk carries the
boundary language inside `notes` on the same entry, and criteria
that the SecOps-NG catalogue does not exercise operationally simply
ship with `playbook_refs: []` and a `notes` paragraph explaining
why.

### 3.2 Reading order

There are two natural reading strategies:

**Category-first.** If the report scope names one or more Trust
Services categories, read the corresponding files top-to-bottom.
`tsc-security.yaml` is always in scope (Common Criteria is the SOC 2
baseline); the other four files are read only when the operator has
committed to the corresponding category in the report scope.
Criteria appear in AICPA canonical order within each file.

**Anchor-first.** If you already know which SecOps-NG playbook or
control you care about, grep across the SOC 2 directory:

```sh
grep -rn "playbook.iam_auditor@v1" content/mappings/soc2/
```

The result set is the list of TSC criteria that anchor exercises —
useful for reasoning about coverage from the anchor side rather
than from the TSC side.

## 4. Worked example — CC6.1 (logical access controls)

Scenario: a US SaaS customer sends a due-diligence questionnaire
asking the operator to describe how they discharge **SOC 2 CC6.1 —
Logical Access Controls**, and to point at evidence a service
auditor would examine.

### 4.1 Locate the criterion

`CC6.1` lives under the Security category. In
`content/mappings/soc2/tsc-security.yaml`, search for
`id: soc2:cc6-1-logical-access-controls`. The entry declares:

```yaml
- id: soc2:cc6-1-logical-access-controls
  regulation:
    article: CC6.1
    …
  obligation: >-
    The entity implements logical access security software,
    infrastructure, and architectures over protected information
    assets to protect them from security events to meet the
    entity's objectives. Access is restricted to authorised users
    through identification, authentication, and authorisation
    controls.
  control_refs:
    - control.access_enforcement@v1
    - control.least_privilege@v1
    - control.cloud_identity_least_privilege@v1
  playbook_refs:
    - playbook.iam_auditor@v1
  …
```

### 4.2 Follow the anchors

The three `control_refs` are the control-catalogue surfaces the
criterion is exercised against:

- `control.access_enforcement@v1` — the on-prem / general access-
  enforcement anchor: authenticated identity, authorised action,
  logged decision.
- `control.least_privilege@v1` — the least-privilege posture anchor:
  role scope, standing entitlements, privilege escalation review.
- `control.cloud_identity_least_privilege@v1` — the cloud-side
  extension: IAM policy shape, break-glass, cross-account trust.

The single `playbook_ref` is the operational workflow that
discharges the criterion end-to-end:

- `playbook.iam_auditor@v1` — the identity and access management
  audit playbook. See [`iam_auditor.md`](iam_auditor.md) for the
  cookbook walkthrough of the playbook itself: what the CACAO
  steps do, which deterministic primitives they bind, and what a
  reference-compiled run emits in n8n, Temporal, and LangGraph.

### 4.3 Compose the evidence

The operator responds to the questionnaire by naming the four
anchors and pointing at the shipped artifacts they emit:

- **Control-catalogue side.** The three control anchors are the
  posture statement: what "authorised access" means, how it is
  enforced, and how the least-privilege boundary is maintained
  across on-prem and cloud identity providers.
- **Operational side.** The IAM auditor playbook produces the
  operator-facing evidence a SOC 2 reviewer walks: identity
  inventory, standing-entitlement review, privilege-escalation
  approvals, and access-audit findings register.

The operator does not have to invent new evidence; the shipped
artifacts already discharge the criterion. The crosswalk's job is
to name which shipped artifacts point at `CC6.1`.

### 4.4 Reasoning across regimes

The same operational requirement — logical access enforcement,
authenticated identity, least privilege — is also anchored under
EU regimes the operator is already exercising:

- **NIS2 Art. 21(2)(i)** (MFA and identity security). See
  `content/mappings/nis2/article-21-2-i.yaml`.
- **DORA Art. 9** (access management and authentication
  requirements under the ICT risk framework). See
  `content/mappings/dora/article-9-access-management.yaml` and
  `article-9-4-b-authentication.yaml`.
- **GDPR Art. 32** (access-control component of technical and
  organisational measures). See `content/mappings/gdpr/`.
- **NIST CSF 2.0 `PR.AA`** (identity management, authentication,
  and access control). See
  `content/mappings/nist_csf/csf-core-functions.yaml` and the
  [NIST CSF crosswalk walkthrough](nist_csf_crosswalk.md).

Each regime's mapping asserts that the same playbook and control
anchors discharge its own surface. This convergence is
intentional: the operator's evidence trail lives with the shipped
artifacts; the mappings navigate to it from different vocabularies.

## 5. Cross-reference to EU regulatory mappings

Where a TSC criterion overlaps an EU obligation already carried by
the SecOps-NG regime mappings, the operator's **statutory surface
is discharged by the EU mapping, not by the SOC 2 crosswalk**. The
SOC 2 crosswalk points at the same playbook anchors so that a
SOC 2-framed question resolves to the same evidence trail, but the
authoritative pointer for statutory compliance is the EU mapping.

Concrete overlaps worth naming (non-exhaustive):

| TSC criterion | EU mapping (authoritative for statute) | Shared playbook anchors |
|---------------|-----------------------------------------|-------------------------|
| `CC6.1` — Logical access controls | `content/mappings/nis2/article-21-2-i.yaml` (NIS2 MFA); `content/mappings/dora/article-9-access-management.yaml`, `article-9-4-b-authentication.yaml` (DORA access management + authentication) | `playbook.iam_auditor@v1`, `playbook.mfa_secured_comms@v1`, `playbook.onboarding_offboarding_tracker@v1` |
| `CC6.6`, `CC6.7`, `CC6.8` — Boundary protection, data-in-transit, malicious code | `content/mappings/nis2/article-21-2-h.yaml` (NIS2 cryptography); `content/mappings/dora/article-9-crypto.yaml` (DORA cryptography) | `playbook.crypto_posture_management@v1`, `playbook.detection_engineering@v1`, `playbook.infra_posture_management@v1` |
| `CC7.2`, `CC7.3` — Detection and evaluation of security events | `content/mappings/dora/article-10.yaml` (DORA detection); `content/mappings/nis2/article-21-2-i.yaml` (NIS2 monitoring) | `playbook.detection_engineering@v1`, `playbook.threat_intel_ingest@v1`, `playbook.alert_triage@v1` |
| `CC7.4`, `CC7.5` — Incident response and recovery | `content/mappings/dora/article-11.yaml`, `article-14.yaml`, `article-19-and-28.yaml` (DORA incident management + reporting); `content/mappings/nis2/article-23.yaml` (NIS2 incident notification); `content/mappings/cra/` (CRA Art. 14 SRP notify) | `playbook.incident_management@v1`, `playbook.mfa_secured_comms@v1`, `playbook.cra_srp_notify@v1` |
| `CC8.1` — Change management | `content/mappings/dora/article-9-and-rts-change-mgmt.yaml` (DORA RTS change management) | `playbook.codebase_vuln_management@v1`, `playbook.infra_posture_management@v1` |
| `CC9.2` — Vendor and business-partner risk | `content/mappings/nis2/article-22.yaml` (NIS2 supply-chain risk); `content/mappings/dora/article-19-and-28.yaml` (DORA third-party risk) | `playbook.supply_chain_security@v1`, `playbook.contractual_obligations_tracker@v1` |
| `A1.2`, `A1.3` — Availability infrastructure and recovery testing | `content/mappings/dora/article-11-availability-response.yaml`, `article-12.yaml` (DORA availability + backup); `content/mappings/nis2/article-21-2-c.yaml` (NIS2 business continuity) | `playbook.backup_recovery@v1`, `playbook.business_continuity@v1` |
| `C1.1`, `C1.2` — Confidential information handling and disposal | `content/mappings/gdpr/` (GDPR Art. 32 TOMs); `content/mappings/nis2/article-21-2-h.yaml` (NIS2 cryptography) | `playbook.asset_management@v1`, `playbook.onboarding_offboarding_tracker@v1` |
| `P4.2`, `P5.1`, `P6.1`, `P6.7` — Retention, subject access, disclosure, breach notification | `content/mappings/gdpr/` (GDPR Art. 5, 15-22, 32-34) | `playbook.data_subject_rights@v1`, `playbook.data_protection_impact_assessment@v1`, `playbook.incident_management@v1` |

The convergence is intentional. A regulated-sector operator running
the SecOps-NG catalogue discharges the same underlying artifact
once; each regime's mapping asserts that the artifact covers its
statutory surface, and the SOC 2 crosswalk points at the same
artifact so that a SOC 2-framed question resolves to the same
evidence trail.

The **governance-only Common Criteria** (`CC1.x` control
environment, `CC2.x` communication and information, parts of
`CC3.x` risk assessment, and `CC5.x` control activities) are where
the two axes diverge most. SOC 2 tests these through operator-owned
artifacts (board minutes, code of conduct, org charts, RACI,
policy set); EU regimes carry governance surface in their own
shapes — DORA Art. 5 (ICT-risk framework) and Art. 6 (governance
arrangements), NIS2 Art. 20 (management-body responsibilities).
Where an operator wants to reason about governance obligations,
both axes converge on `control.ict_risk_governance@v1` and
`control.risk_management_policy@v1`; the EU mapping is
authoritative for the statutory surface, and the SOC 2 crosswalk
provides the assurance-framed navigation.

## 6. What the crosswalk deliberately does not cover

- **AICPA Informative References.** The AICPA maintains mappings
  between the TSC and other catalogues (SP 800-53r5,
  ISO/IEC 27001:2022, HIPAA, NIST CSF 2.0). Those mappings are out
  of scope of this directory; the crosswalk asserts against the
  operator's own catalogue only.
- **Type I vs Type II opinion scoping.** SOC 2 reports come in two
  shapes: Type I (design at a point in time) and Type II (operating
  effectiveness over a period, typically 3–12 months). Choosing
  the report type, the reporting period, and the trust services
  categories to include in scope are operator-and-auditor-owned
  decisions upstream of the crosswalk.
- **Auditor workpapers and sampling.** A service auditor performing
  a SOC 2 examination selects samples, designs tests of design and
  tests of operating effectiveness, and evaluates the sufficiency
  of evidence per AT-C 105 / AT-C 205. The crosswalk points at
  where the operator's evidence lives; it does not prescribe how
  an auditor should sample or test it, and it does not constitute
  audit workpapers.
- **TSP Section 100 guidance and Implementation Guides.** The
  AICPA publishes points of focus, Implementation Guides, and TSP
  Section 100 guidance describing how criteria are commonly tested
  in practice. The crosswalk does not reproduce that guidance; the
  operator and their auditor consult those sources directly.
- **Attestation or opinion issuance.** Nothing in the crosswalk is
  a SOC 2 attestation, a service auditor's report, or a statement
  of compliance. It is a structural pointer against the operator's
  own artifacts.
- **Legal interpretation.** SOC 2 is a private-sector assurance
  framework, not an EU statutory instrument. The crosswalk does
  not constitute a legal or regulator interpretation of the TSC,
  and it does not replace the EU regime mappings for statutory
  obligations under NIS2, DORA, CRA, or GDPR.

## 7. Contributor pointers

- **Adding a playbook anchor** to a criterion: land the playbook
  first under `content/playbooks/`, then add the
  `playbook.<name>@v1` reference to the relevant criterion's
  `playbook_refs` in the matching per-category file. Update the
  `notes` block to name what the new anchor discharges.
- **Adding a control anchor**: same shape, at `control_refs` on
  the criterion.
- **Adjusting `notes` for boundary changes**: `notes` paragraphs
  are living assertions of catalogue boundary. When new content
  lands that starts exercising a previously-operator-owned slice
  of a criterion, rewrite the boundary language in the same PR
  that lands the content — the crosswalk should reflect reality,
  not intent.
- **OSCAL round-trip.** Any change to a per-category YAML file
  must keep `oscal-component-definition.json` in sync. The
  round-trip test at
  `tests/content/test_oscal_soc2_component_definition_roundtrip.py`
  guards the shape; run it locally before opening the PR.
- **Tests.** The crosswalk is guarded by
  `tests/content/test_oscal_soc2_component_definition.py`,
  `tests/content/test_oscal_soc2_component_definition_roundtrip.py`,
  and `tests/content/test_d3fend_soc2_crosswalk.py`. Run
  `python -m pytest tests/content/` before opening a PR that
  touches the SOC 2 directory.

## 8. Reference

- AICPA, "Trust Services Criteria for Security, Availability,
  Processing Integrity, Confidentiality, and Privacy" (2017,
  as revised).
  https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2
- AICPA attestation standards AT-C 105 (Concepts Common to All
  Attestation Engagements) and AT-C 205 (Examination Engagements).
- `content/mappings/soc2/README.md` — directory-level regime
  scope and file conventions.
- `content/mappings/soc2/tsc-*.yaml` — per-category crosswalk
  files (Security, Availability, Confidentiality, Processing
  Integrity, Privacy).
- `content/mappings/soc2/oscal-component-definition.json` — the
  OSCAL 1.1.2 component definition for the whole SOC 2 surface.
- Companion EU regime mappings: `content/mappings/nis2/`,
  `content/mappings/dora/`, `content/mappings/cra/`,
  `content/mappings/gdpr/`.
- Companion crosswalk: [`nist_csf_crosswalk.md`](nist_csf_crosswalk.md).
