# identity_access_management_metrics — cookbook walkthrough

Practitioner walkthrough for the identity/access-management KPI/KRI
pair that closes the NIS2 Article 21(2)(i) access-control and
Article 21(2)(j) multi-factor-authentication limbs on the aggregate
identity surface. Two catalogue entries operationalise the pair:

- `kpi.identity_mfa_enforcement_rate@v1` — share of the operator's
  user-account population whose authentication posture carries
  multi-factor enforcement observed on the identity source.
- `kri.access_review_completion_rate@v1` — share of privileged-access
  reviews the operator's declared cadence scheduled inside the
  evaluation window that closed on time with a recertify-or-revoke
  decision recorded against every reviewed binding.

The pair operates *around* the shipped identity-and-access playbooks
rather than inside them:

```
per-workflow playbooks (probe / attest / audit)
    playbook.mfa_secured_comms@v1
    playbook.iam_auditor@v1
    control.privileged_access_review@v1
        └── emit per-account MFA-posture observations
            emit per-review recertify-or-revoke decisions

catalogue metrics (aggregate, per-window)
    kpi.identity_mfa_enforcement_rate@v1
    kri.access_review_completion_rate@v1
        └── read the observations, produce the ratio
            the dashboard / executive_metrics rollup reads

executive_metrics (recurring rollup — see cookbook entry)
    └── consumes the pair alongside the rest of the catalogue
```

The KPI reads the MFA-coverage posture that `mfa_secured_comms`
probes; the KRI reads the review-record store that
`control.privileged_access_review@v1` attests over. Both are aggregate
ratios over the evaluation window — they aggregate the underlying
observations, they do not replace the playbooks that produce them.

## 1. Source of truth

```
content/metrics/
├── identity_mfa_enforcement_rate.yaml       # kpi catalogue entry
├── identity_mfa_enforcement_rate.viz.md     # reference visualisation
├── access_review_completion_rate.yaml       # kri catalogue entry
└── access_review_completion_rate.viz.md     # reference visualisation

content/mappings/nis2/article-21-2-i.yaml    # access-control anchor
content/mappings/nis2/article-21-2-j.yaml    # mfa/continuous-auth anchor
content/mappings/gdpr/article-32-security-of-processing.yaml
                                             # GDPR Art. 32(1)(a) sibling

tools/lint_identity_access_management_ocsf_bindings.py
                                             # G-04 OCSF-binding lint;
                                             # runs in the nightly
                                             # orphan-CI assertion lane
```

The YAML files are canonical. Each entry declares its regulatory
`external_refs`, its telemetry / control / playbook back-references,
its warn / high / breach thresholds, and its aggregation formula. The
sibling `.viz.md` file is the contract for the reference chart shape
the operator's compile target renders against live data.

## 2. What each metric measures

### 2.1 `kpi.identity_mfa_enforcement_rate@v1` — MFA enforcement KPI

**Question answered:** on the aggregate account population, what share
of accounts is enforcing multi-factor authentication at each
authentication event?

**Formula.** For each user account observed on the operator's identity
source during the evaluation window, classify the account as
`mfa_enforced` when the authentication posture recorded by the
`mfa_secured_comms` probe-mfa-coverage step matches the operator's
documented enforcement policy on that account's role (a factor beyond
the primary password credential is bound and required at each
authentication, or continuous-authentication posture is active).

```
enforcement_rate = |{accounts mfa_enforced}| / |{accounts observed}|
```

Documented break-glass and service-account exceptions carried on the
operator's identity-source exception register do **not** drop out of
the denominator. They stay visible in the ratio so the exception
population itself is a first-class number on the dashboard.

**Window.** P30D sliding.

**Direction.** Higher is better; target `>= 0.95`.

**Thresholds.**

| Band | Condition | Severity |
|---|---|---|
| target | `>= 0.95` | — |
| warn | `< 0.95` | warn |
| high | `< 0.90` | high |
| breach | `< 0.80` | critical |

The 0.95 headline target is a community-recommended baseline for the
unscoped catalogue entry. NIS2 essential-entity guidance and ENISA
authentication baselines converge on MFA coverage in the mid-to-high
nineties percentile once break-glass and service-account exceptions
are documented on the identity-source registry. Privileged-role-scoped
variants (for example an admin-account-scoped KPI) tighten the target
above 0.99 and live as separate catalogue entries.

### 2.2 `kri.access_review_completion_rate@v1` — privileged-access review KRI

**Question answered:** of the privileged-access reviews the operator's
declared cadence scheduled inside the evaluation window, what share
closed on time with a recertify-or-revoke decision recorded against
every binding in the review scope?

**Formula.** For each privileged-access review the operator's
documented cadence policy scheduled with a review-due timestamp
falling inside the evaluation window, classify the review as
`completed_on_time` when the review record carries a `closed_at`
timestamp on or before the review-due timestamp AND every binding in
the review scope carries an explicit recertify-or-revoke decision on
the review record.

```
completion_rate = |{reviews completed_on_time}| / |{reviews scheduled}|
```

Two shape decisions matter for reading this ratio honestly:

- **Late-closed reviews count against the denominator.** A review
  closed after the review-due timestamp is a completion the operator's
  access-control posture recorded, but the cadence obligation was not
  met. This KRI reads the *on-time* slice, not the *ever-closed*
  slice.
- **Missing per-binding decisions block on-time classification.** A
  review whose scope contains any binding without a
  recertify-or-revoke decision is treated as not `completed_on_time`
  per the primitive contract, so partially-attested reviews do not
  silently disappear from the ratio.

**Window.** P90D sliding.

**Direction.** Higher is better; target `>= 0.90`.

**Thresholds.**

| Band | Condition | Severity |
|---|---|---|
| target | `>= 0.90` | — |
| warn | `< 0.90` | warn |
| high | `< 0.80` | high |
| breach | `< 0.60` | critical |

The 0.90 headline target is the community-recommended starting point
for the unscoped catalogue entry. Mature access-review programmes
under NIS2 and ISO/IEC 27001 Annex A.5.18/A.8.2 hold on-time
completion above 0.95 at steady state once the scheduling, reminder,
and escalation lanes are disciplined against the documented cadence
policy.

## 3. Wiring the OCSF feeds

The catalogue entries pin their upstream telemetry surface through
OCSF class bindings. The nightly orphan-CI assertion lane at
[`tools/lint_identity_access_management_ocsf_bindings.py`](../../tools/lint_identity_access_management_ocsf_bindings.py)
enforces that every metric in the identity/access-management cluster
declares at least one OCSF `telemetry_ref`, so an operator can rely on
the source-data shape being pinned alongside the internal
evidence-artifact field bindings.

| Metric | OCSF class binding | Role in the ratio |
|---|---|---|
| `kpi.identity_mfa_enforcement_rate@v1` | Authentication (class 3002) — `telemetry.ocsf.authentication@v1` | Per-authentication observed factor set; folded into per-account enforcement state over the window. |
| `kpi.identity_mfa_enforcement_rate@v1` | Account Change (class 3001) — `telemetry.ocsf.account_change@v1` | Bounds the denominator to accounts observed on the identity source during the evaluation window. |
| `kri.access_review_completion_rate@v1` | Account Change (class 3001) — `telemetry.ocsf.account_change@v1` | Grounds the review scope to the accounts and bindings the operator's identity source knows about. |

The KPI leans on Authentication (3002) for the numerator observation
(each authentication is a chance to see whether the second factor was
required) and Account Change (3001) for the denominator scope. The KRI
uses Account Change (3001) to ground the review-scope binding
inventory; the review-record store the KRI reads against is the
`control.privileged_access_review@v1` attestation surface, which is
not itself an OCSF class — the OCSF binding sits on the account
inventory that scopes the reviews.

Operators wiring these feeds:

1. Emit or receive OCSF Authentication (3002) events from the
   identity provider (ADFS / Entra ID / Keycloak / Zitadel / ...)
   into the SIEM or event bus the `mfa_secured_comms` probe reads.
2. Emit or receive OCSF Account Change (3001) events for account
   inventory and lifecycle transitions from the same identity
   provider.
3. Point the KPI evaluator at those two feeds against the P30D
   sliding window; point the KRI evaluator at the review-record store
   the operator's access-review cadence writes to, scoped by the
   account inventory the OCSF Account Change feed grounds.

## 4. Cross-references to the shipped IAM playbooks

The KPI/KRI pair is designed to sit alongside the identity-and-access
cookbook entries the framework already ships:

- **`mfa_secured_comms`** — canonical CACAO source for the MFA-coverage
  probe, the continuous-authentication assessment, and the OOB-channel
  verification lane. The KPI's per-account MFA-posture observations
  come out of this playbook's probe-mfa-coverage step
  (`action--52000000-0000-4000-8000-000000000002`). See
  [`mfa_secured_comms.md`](mfa_secured_comms.md).
- **`iam_auditor`** — identity-lifecycle auditor with capability
  grant/revoke tracking. The primitives package
  (`content/playbooks/iam_auditor/primitives/identity.py`) carries the
  deterministic caller-identity and capability-list logic that the
  access-review record store draws from when a review's binding scope
  is materialised. See [`iam_auditor.md`](iam_auditor.md).

The KPI/KRI pair does **not** duplicate what these playbooks do; it
consumes their output and produces an aggregate ratio for the
dashboard and the recurring `executive_metrics` rollup.

## 5. Regulatory-anchor closure

The pair contributes to the following inbound anchors:

- **NIS2 Article 21(2)(j)** — 'use of multi-factor authentication or
  continuous authentication solutions'. The KPI is the aggregate
  MFA-enforcement ratio operators read against this clause on the
  identity surface.
- **NIS2 Article 21(2)(i)** — 'human resources security, access
  control policies and asset management'. The KRI is the on-time
  privileged-access-review completion residual-risk signal.
- **DORA Article 5(2)** — ICT risk-management framework requirement
  that policies, procedures and tools include strong authentication
  mechanisms. The KPI reads across as the strong-authentication
  coverage signal on the ICT-account surface.
- **GDPR Article 32(1)(a)** — security of processing (access to
  personal data). Both entries carry an EDPB-consistent reading of
  the access-control organisational-measures limb, with the KRI as
  the periodic-review evidence signal.
- **ISO/IEC 27001:2022 Annex A.8.2** — Privileged access rights
  (KRI companion anchor).
- **ISO/IEC 27004** — Information security measurement guidance
  (KPI and KRI methodology anchor).

The KPI additionally pins ENISA authentication baselines and OCSF
v1.3.0 Authentication (class 3002) as external references so the
methodology and the source-data shape are both citable on the entry.

## 6. Reading the dashboard

Both entries commit a reference visualisation contract in their
sibling `.viz.md` file. The chart shape the compile target renders
against operator data is:

- A ratio-headline gauge with the warn / high / breach threshold bands
  drawn as visible zones behind the current-value needle.
- A drill-down stacked bar showing coverage-versus-gap sliced by
  identity source (KPI) or on-time-completed versus overdue-or-
  incomplete review counts sliced by cadence-window (KRI).

The `.viz.md` files are the contract for the chart shape. The compile
target is free to render them in whatever front-end the operator
already runs (Grafana, Superset, Metabase, a homegrown board pack),
provided the shape and the threshold banding are preserved so the
audit reading stays the same.

## 7. What this cookbook deliberately does not cover

- **Identity-provider choice.** The catalogue entries are
  identity-vendor-neutral. Which IdP the operator runs (ADFS,
  Entra ID, Keycloak, Zitadel, Authentik, Ory, ...) is an operator
  data-plane decision; the OCSF class bindings are the interop
  surface.
- **Review-record store choice.** The KRI is scoped to the
  `control.privileged_access_review@v1` attestation contract; the
  concrete review-record store (a governance tool, a homegrown
  service, an audit spreadsheet backed by change-controlled records)
  is the operator's declaration.
- **Cadence policy authoring.** *Which* privileged bindings are in
  scope for periodic review, and *how often* each cadence fires, is
  the operator's cadence-policy declaration — the KRI operates
  against the policy it is handed, not against a framework-declared
  cadence.
- **Break-glass and service-account exception policy.** The exception
  register the KPI reads against is an operator declaration, not a
  framework taxonomy. The KPI keeps documented exceptions in the
  denominator so the exception population is visible in the ratio.
- **Credentials.** No IdP admin credential, no OCSF collector token,
  and no review-record-store credential belongs in the metric YAML,
  the linter, or any compiled dashboard artifact. The operator wires
  each at the compile-target config layer.
