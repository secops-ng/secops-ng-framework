# nist_csf_crosswalk — cookbook walkthrough

Practitioner walkthrough of the **NIST Cybersecurity Framework 2.0
crosswalk** shipped under
[`content/mappings/nist_csf/`](../../content/mappings/nist_csf/). This
walkthrough is aimed at operators who already run a control catalogue
against EU statutory obligations (NIS2, DORA, CRA, GDPR) and want a
structural pointer from the CSF 2.0 Core down into the SecOps-NG
playbook and control anchors. It is written for community readers —
regulated-sector operators, contributors landing new anchors, and
researchers reading the crosswalk as reference material — not as
commercial guidance or a legal interpretation of the CSF.

The crosswalk is a **framework-agnostic**, portable artifact. It
carries no compiler-target detail and no runtime binding: the on-disk
YAML is the machine-readable pointer, and this cookbook is the
connective narrative an operator reads once to understand what the
YAML asserts and how to walk it.

> The NIST CSF 2.0 is a US-origin voluntary framework maintained by
> NIST (NIST CSWP 29, published 26 February 2024). It is **not** an
> EU statutory instrument. The crosswalk asserts that the named
> SecOps-NG artifacts exercise the CSF Category and Subcategory
> outcomes in practice; it does not constitute a legal or regulator
> interpretation of the CSF, and it does not replace the EU
> regulatory mappings under `content/mappings/nis2/`,
> `content/mappings/dora/`, `content/mappings/cra/`, or
> `content/mappings/gdpr/` — those remain the authoritative pointer
> for the statutory surface.

## 1. Why this matters

An EU-adjacent operator already has to discharge NIS2 Art. 21 risk-
management measures, DORA Chapter II ICT risk management, CRA vendor
obligations for products with digital elements, and GDPR technical
and organisational measures under Art. 32. Each of those surfaces is
already mapped, article-by-article, under `content/mappings/<axis>/`
and exercised by the shipped playbooks and controls in the SecOps-NG
catalogue.

The CSF 2.0 crosswalk adds a **second axis of navigation**: the same
catalogue, viewed through the CSF's function → category → subcategory
outcome tree. This is useful for practitioners in three concrete
ways.

- **Cross-jurisdictional reasoning.** Where a supplier attestation,
  a customer questionnaire, or a partner audit is framed in CSF
  terms (common in US and cross-border commercial arrangements), the
  operator can point at the CSF outcome and follow the crosswalk
  down to the shipped SecOps-NG artifact that exercises it, without
  maintaining a parallel CSF-only control catalogue.
- **Outcome-oriented gap analysis.** The CSF 2.0 Subcategory layer
  (106 outcomes across Govern / Identify / Protect / Detect / Respond
  / Recover) is finer-grained than the article-level EU mappings.
  Where a Subcategory carries a `gap_note` instead of `playbook_refs`,
  that surfaces an outcome the SecOps-NG catalogue does **not**
  exercise (governance-owned, board-owned, or physical-facility
  outcomes). The operator's own evidence discharges those outcomes;
  the crosswalk names them explicitly so the boundary is visible.
- **CSF-first navigation into EU obligations.** Where a CSF Category
  overlaps an EU obligation the operator already tracks — for
  example CSF `GV.SC` (supply-chain risk management) overlaps NIS2
  Art. 21(2)(d) and DORA Art. 28 — the crosswalk points at the
  playbook that discharges the overlap. Operators who start their
  reasoning from CSF can navigate into the article-level EU mappings
  via the same anchors.

The crosswalk is deliberately a **structural pointer**, not an
implementation. It does not tell an operator which CSF Categories
to prioritise, what tier of CSF Profile to adopt, or how to score
themselves against the CSF Implementation Tiers — those are
operator-owned strategic decisions upstream of the SecOps-NG
catalogue.

## 2. What ships

Under `content/mappings/nist_csf/`:

| File | Contents | Layer |
|------|----------|-------|
| `README.md` | Regime scope, file conventions, CSF 2.0 structure summary. | — |
| `csf-core-functions.yaml` | 22 CSF Category entries (GV.OC, GV.RM, GV.RR, GV.PO, GV.OV, GV.SC / ID.AM, ID.RA, ID.IM / PR.AA, PR.AT, PR.DS, PR.PS, PR.IR / DE.CM, DE.AE / RS.MA, RS.AN, RS.CO, RS.MI / RC.RP, RC.CO), each nesting the CSF Subcategories that belong to it — 106 in total. | SKELETON + CORE |

The SKELETON layer landed the 22 Category-level entries with
`control_refs`, `playbook_refs`, and `notes`. The CORE layer extended
each Category with a `subcategory_entries` block carrying the CSF
Subcategory outcome text (verbatim per CSWP 29) and per-Subcategory
`playbook_refs` where a SecOps-NG artifact exercises the outcome, or
`gap_note` where it does not.

No CSF Informative References ship here. Mappings between the CSF
and NIST SP 800-53r5, ISO/IEC 27001:2022, or CIS Controls v8 are
maintained by NIST and by the source-catalogue owners; the SecOps-NG
crosswalk asserts against the operator's own catalogue, not against
the CSF Informative References.

## 3. Navigating the crosswalk

The file is one YAML document with a top-level `regime: nist_csf`
key and an `entries` list. Each entry is a **Category** — one of
the 22 CSF Categories — and follows the same shape used by the other
regime mappings under `content/mappings/<axis>/`.

### 3.1 Category-level anatomy

A Category entry looks like this (excerpted from `PR.AA`, identity
management, authentication, and access control):

```yaml
- id: nist_csf:pr-aa-identity-management-authentication-and-access-control
  regulation:
    name: NIST CSF 2.0
    instrument: NIST Cybersecurity Framework 2.0 (NIST CSWP 29)
    article: PR.AA
    url: https://doi.org/10.6028/NIST.CSWP.29
  obligation: >-
    Manage access to physical and logical assets and associated
    facilities so that it is limited to authorised users, services,
    and hardware, and managed commensurate with the assessed risk of
    unauthorised access.
  status: draft
  control_refs:
    - control.access_enforcement@v1
    - control.account_management@v1
    - control.mfa_state_probe@v1
    - control.least_privilege@v1
    - control.cloud_identity_least_privilege@v1
    - control.privileged_access_review@v1
    - control.jml_evidence@v1
    - control.service_identification_authentication@v1
  playbook_refs:
    - playbook.iam_auditor@v1
    - playbook.onboarding_offboarding_tracker@v1
    - playbook.mfa_secured_comms@v1
  notes: >-
    PR.AA is the largest single Category by control surface. The
    catalogue anchors carry the identity / authentication /
    authorisation slice end-to-end …
  subcategory_entries:
    - id: PR.AA-01
      outcome: >-
        Identities and credentials for authorized users, services, and
        hardware are managed by the organization
      playbook_refs:
        - playbook.iam_auditor@v1
        - playbook.onboarding_offboarding_tracker@v1
    …
```

Fields worth naming explicitly:

- **`id`** — a stable identifier the crosswalk uses to name the
  entry. The `nist_csf:` prefix distinguishes it from the other
  regime axes.
- **`regulation.article`** — the CSF Category identifier (for
  example `PR.AA`, `GV.SC`, `RC.RP`). This is the label an operator
  reading the CSF 2.0 document itself will match against.
- **`obligation`** — the Category-level outcome statement.
- **`control_refs` / `playbook_refs`** at the Category level — the
  full set of anchors the Category is exercised by, aggregated
  across its Subcategories. This is the "at a glance" pointer.
- **`notes`** — a plain-language paragraph naming which slice of
  the Category the catalogue anchors discharge and which slice is
  operator-owned.
- **`subcategory_entries`** — one entry per CSF Subcategory that
  belongs to this Category. This is the finest-grained pointer the
  crosswalk carries.

### 3.2 Subcategory-level anatomy

Each `subcategory_entries` item follows one of two shapes:

**Exercised by the catalogue** — has `playbook_refs`:

```yaml
- id: DE.CM-01
  outcome: >-
    Networks and network services are monitored to find potentially
    adverse events
  playbook_refs:
    - playbook.detection_engineering@v1
    - playbook.infra_posture_management@v1
```

**Not exercised by the catalogue** — has `gap_note`:

```yaml
- id: DE.CM-02
  outcome: >-
    The physical environment is monitored to find potentially adverse
    events
  gap_note: >-
    Physical-environment monitoring is operator-owned facilities work;
    not exercised by the SecOps-NG catalogue.
```

The two shapes are mutually exclusive at the Subcategory level: a
Subcategory either points at one or more playbook anchors, or it
carries an explicit `gap_note` explaining why the SecOps-NG catalogue
does not exercise it. This matters for reading the file: a
Subcategory with a `gap_note` is not a defect in the crosswalk, it
is an assertion of *catalogue boundary*. The operator's own evidence
(mission statement, board minutes, physical-access log,
risk-appetite statement) discharges those outcomes.

The distribution of `gap_note` entries is not accidental. The bulk
of them sit under **Govern** (organisational mission, risk appetite,
oversight cadence, policy authoring — all board-level or
executive-owned) and under a small number of physical-facility
outcomes (`DE.CM-02`, `PR.AA-06`, `PR.IR-02`). Everything else the
CSF 2.0 Subcategory layer names is exercised by at least one
SecOps-NG playbook.

### 3.3 Reading order

There are two natural reading strategies:

**Function-first.** Read `csf-core-functions.yaml` top-to-bottom.
The Functions appear in the CSF 2.0 canonical order (Govern →
Identify → Protect → Detect → Respond → Recover). Within a Function
the Categories appear in the order NIST fixed in CSWP 29.

**Anchor-first.** If you already know which SecOps-NG playbook or
control you care about, grep the crosswalk for the anchor:

```sh
grep -n "playbook.iam_auditor@v1" content/mappings/nist_csf/csf-core-functions.yaml
```

The result set is the list of CSF outcomes that anchor exercises —
useful for reasoning about coverage from the anchor side rather
than from the CSF side.

## 4. Worked example — mapping an operational requirement

Scenario: the operator has received a supplier-questionnaire
requesting evidence that they identify, validate, and record
vulnerabilities in assets, phrased as "compliance with **NIST CSF
2.0 subcategory ID.RA-01**".

### 4.1 Locate the CSF outcome

`ID.RA-01` lives under the `ID.RA` Category (Risk Assessment), under
the Identify (`ID`) Function. In `csf-core-functions.yaml`, search
for `id: nist_csf:id-ra-risk-assessment`. The entry declares:

```yaml
- id: nist_csf:id-ra-risk-assessment
  regulation:
    article: ID.RA
    …
  obligation: >-
    Understand the cybersecurity risk to the organisation, its assets,
    and its individuals, including exposure to threats,
    vulnerabilities, likelihoods, and impacts.
  control_refs:
    - control.security_assessment@v1
    - control.vuln_disclosure_intake@v1
  playbook_refs:
    - playbook.threat_intel_ingest@v1
    - playbook.dora_ict_risk_selfassess@v1
    - playbook.codebase_vuln_management@v1
  …
```

The Category-level answer is that Identify → Risk Assessment is
exercised by the composite threat-intel + vulnerability + risk-
assessment surface.

### 4.2 Follow into the Subcategory

Under `subcategory_entries`, `ID.RA-01` reads:

```yaml
- id: ID.RA-01
  outcome: >-
    Vulnerabilities in assets are identified, validated, and recorded
  playbook_refs:
    - playbook.codebase_vuln_management@v1
    - playbook.vuln_intake@v1
    - playbook.infra_posture_management@v1
```

The named playbooks are the operator-facing artifacts:

- `playbook.codebase_vuln_management@v1` — SBOM pin, finding
  identification, and per-finding evidence emission for source-owned
  components. See
  [`codebase_vuln_management.md`](codebase_vuln_management.md).
- `playbook.vuln_intake@v1` — the inbound-disclosure surface: how a
  reported vulnerability enters the operator's ticketing and
  attestation flow. See [`vuln_intake.md`](vuln_intake.md).
- `playbook.infra_posture_management@v1` — infrastructure-side
  posture scanning (cloud, endpoint, network), where identified
  vulnerabilities on infrastructure land rather than in code. See
  [`infra_posture_management.md`](infra_posture_management.md).

### 4.3 Compose the evidence

The operator responds to the questionnaire by naming the three
playbooks and pointing at the shipped artifacts each emits:

- codebase-side: the vulnerability findings register produced by
  the codebase vulnerability management playbook (SBOM-anchored,
  per-finding evidence).
- inbound-disclosure side: the intake ticket + triage record
  produced by the vuln intake playbook.
- infrastructure side: the posture-scan evidence emitted by the
  infrastructure posture management playbook.

The operator does not have to invent new evidence; the shipped
artifacts already discharge the outcome. The crosswalk's job is to
name which shipped artifacts point at `ID.RA-01`.

### 4.4 Reasoning across regimes

The same operational requirement — identify, validate, record
vulnerabilities in assets — is also anchored under EU regimes:

- **DORA Art. 9** (RTS on vulnerability management). See
  `content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml`.
- **NIS2 Art. 21(2)(e)** (vulnerability handling and disclosure).
  See `content/mappings/nis2/article-21-2-e.yaml`.
- **CRA Art. 14** (SRP dispatch cadence for products with digital
  elements — outbound of the vulnerability lifecycle). See
  `content/mappings/cra/`.

The CSF crosswalk and the EU regime mappings converge on the same
playbook anchors. This is intentional: the playbooks discharge the
operator's obligation once, and each regime's mapping asserts that
the same discharge covers its statutory surface. See § 5 for the
overlap detail.

## 5. Cross-reference to EU regulatory mappings

Where a CSF 2.0 Category or Subcategory overlaps an EU obligation
already carried by the SecOps-NG regime mappings, the operator's
statutory surface is discharged by the EU mapping, not by the CSF
crosswalk. The CSF crosswalk points at the same playbook anchors so
the practitioner can navigate from either axis into the operator-
facing artifact, but the **authoritative pointer for statutory
compliance is the EU mapping**.

Concrete overlaps worth naming:

| CSF Category / Subcategory | EU mapping (authoritative) | Shared playbook anchors |
|----------------------------|----------------------------|-------------------------|
| `GV.SC` — Supply-chain risk management | `content/mappings/nis2/article-22.yaml` (NIS2 Art. 22); `content/mappings/dora/article-19-and-28.yaml` (DORA Art. 28) | `playbook.supply_chain_security@v1`, `playbook.contractual_obligations_tracker@v1` |
| `ID.RA` — Risk assessment | `content/mappings/nis2/article-21-2-a.yaml` (NIS2 Art. 21(2)(a) risk-analysis policy); `content/mappings/dora/article-5.yaml`, `article-6.yaml` (DORA Chapter II ICT-risk framework) | `playbook.dora_ict_risk_selfassess@v1`, `playbook.threat_intel_ingest@v1` |
| `ID.RA-01`, `ID.RA-08` — Vulnerability identification and disclosure processes | `content/mappings/nis2/article-21-2-e.yaml` (NIS2 Art. 21(2)(e) vulnerability handling); `content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml` (DORA RTS vulnerability management); `content/mappings/cra/` (CRA CVD + SRP notify) | `playbook.codebase_vuln_management@v1`, `playbook.vuln_intake@v1`, `playbook.cra_cvd@v1` |
| `PR.AA` — Identity management, authentication, and access control | `content/mappings/dora/article-9-access-management.yaml`, `article-9-4-b-authentication.yaml` (DORA Art. 9 access management); `content/mappings/nis2/article-21-2-i.yaml` (NIS2 Art. 21(2)(i) MFA) | `playbook.iam_auditor@v1`, `playbook.mfa_secured_comms@v1`, `playbook.onboarding_offboarding_tracker@v1` |
| `PR.DS` — Data security (encryption at rest / in transit) | `content/mappings/dora/article-9-crypto.yaml` (DORA cryptography); `content/mappings/nis2/article-21-2-h.yaml` (NIS2 Art. 21(2)(h) cryptography) | `playbook.crypto_posture_management@v1` |
| `DE.CM` — Continuous monitoring | `content/mappings/dora/article-10.yaml` (DORA detection); `content/mappings/nis2/article-21-2-i.yaml` (NIS2 Art. 21(2)(i) inbound closure) | `playbook.detection_engineering@v1`, `playbook.threat_intel_ingest@v1` |
| `RS.MA`, `RS.CO` — Incident management + coordination | `content/mappings/dora/article-11.yaml`, `article-14.yaml`, `article-19-and-28.yaml` (DORA Art. 11, 14, 17, 19); `content/mappings/nis2/article-23.yaml` (NIS2 Art. 23 incident notification); `content/mappings/cra/` (CRA Art. 14 SRP notify) | `playbook.incident_management@v1`, `playbook.mfa_secured_comms@v1` |
| `RC.RP`, `RC.CO` — Recovery + recovery communication | `content/mappings/dora/article-11-availability-response.yaml`, `article-12.yaml` (DORA availability + backup); `content/mappings/nis2/article-21-2-c.yaml` (NIS2 Art. 21(2)(c) business continuity) | `playbook.backup_recovery@v1`, `playbook.business_continuity@v1` |

The convergence is intentional. A regulated-sector operator running
the SecOps-NG catalogue discharges the same underlying artifact once;
each regime's mapping asserts that the artifact covers its statutory
surface, and the CSF crosswalk points at the same artifact so that a
CSF-framed question resolves to the same evidence trail.

The **Govern** Function is where the two axes diverge most. CSF 2.0
promoted governance concerns out of Identify into their own Function
(GV) covering organisational context (`GV.OC`), risk-management
strategy (`GV.RM`), roles and responsibilities (`GV.RR`), policy
(`GV.PO`), oversight (`GV.OV`), and supply-chain risk management
(`GV.SC`). EU regimes carry governance surface in their own shapes
— DORA Art. 5 (ICT-risk framework) and Art. 6 (governance
arrangements), NIS2 Art. 20 (management-body responsibilities). Where
the operator wants to reason about governance obligations, both axes
converge on `control.ict_risk_governance@v1`, `control.risk_management_policy@v1`,
and `playbook.dora_ict_risk_selfassess@v1` — the EU mapping is
authoritative for the statutory surface, and the CSF crosswalk
provides the outcome-oriented navigation.

## 6. What the crosswalk deliberately does not cover

- **CSF Profile authoring.** The CSF 2.0 introduces Organisational
  and Community Profiles as a way to express a target posture
  against the CSF Core. Building a Profile is operator-owned
  strategic work; the crosswalk is a structural pointer, not a
  Profile.
- **CSF Implementation Tiers.** The four Tiers (Partial → Risk
  Informed → Repeatable → Adaptive) are the CSF's self-assessment
  scale. Scoring an operator against the Tiers is not exercised
  by the crosswalk.
- **CSF Informative References.** NIST maintains mappings between
  the CSF and other catalogues (SP 800-53r5, ISO/IEC 27001:2022,
  CIS Controls v8). Those mappings are out of scope of this
  directory; the crosswalk asserts against the operator's own
  catalogue only.
- **Legal interpretation.** CSF 2.0 is a voluntary US-origin
  framework. The crosswalk does not constitute a legal or regulator
  interpretation of the CSF, and it does not replace the EU regime
  mappings for statutory obligations.
- **Prioritisation.** Which CSF Categories to address first, what
  target maturity to aim for, and how to sequence investment are
  operator-owned decisions upstream of the SecOps-NG catalogue.

## 7. Contributor pointers

- **Adding a playbook anchor** to a Category or Subcategory: land
  the playbook first under `content/playbooks/`, then add the
  `playbook.<name>@v1` reference to the relevant Category entry
  and to each Subcategory the playbook exercises. If the addition
  changes the "at a glance" Category view, mirror the anchor at
  the Category `playbook_refs` level as well.
- **Adding a control anchor**: same shape, at the Category
  `control_refs` level. Subcategory-level `control_refs` are
  deliberately not shipped in the CORE layer to keep the file
  navigable; if a Subcategory needs its own control-level detail,
  raise the shape change on a new ROADMAP card.
- **Adjusting a `gap_note`**: `gap_note` entries are living
  assertions of catalogue boundary. When new content lands that
  starts exercising a previously-gap-noted outcome, replace the
  `gap_note` with `playbook_refs` in the same PR that lands the
  content — the crosswalk should reflect reality, not intent.
- **Tests.** The crosswalk is guarded by
  `tests/content/test_nist_csf_crosswalk.py` (shape tests on the
  YAML structure and on the Subcategory `id` matching the CSF 2.0
  layout). Run `python -m pytest tests/content/test_nist_csf_crosswalk.py`
  before opening a PR that touches the file.

## 8. Reference

- NIST CSWP 29, "The NIST Cybersecurity Framework (CSF) 2.0",
  26 February 2024. https://doi.org/10.6028/NIST.CSWP.29
- `content/mappings/nist_csf/README.md` — directory-level regime
  scope and file conventions.
- `content/mappings/nist_csf/csf-core-functions.yaml` — the
  canonical crosswalk file.
- Companion EU regime mappings: `content/mappings/nis2/`,
  `content/mappings/dora/`, `content/mappings/cra/`,
  `content/mappings/gdpr/`.
