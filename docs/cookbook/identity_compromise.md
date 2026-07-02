# identity_compromise — cookbook walkthrough

Identity-compromise response workflow under NIS2 Article 21(2)(b),
NIS2 Article 21(2)(i), NIS2 Article 23, DORA Article 18, DORA Article
19, GDPR Articles 33 and 34, and CRA Annex I §1 authentication /
least-privilege evidence. The `playbook.identity_compromise@v1`
CACAO playbook ingests an identity-protection signal (impossible
travel, password spray, MFA bypass, suspicious OAuth grant, anomalous
sign-in) delivered by the operator's IdP or identity-protection
layer, hydrates it with principal context and recent sign-in history,
decides whether the compromise is confirmed, and — when it is — drives
containment through MFA-factor reset, session and refresh-token
revocation across IdP and downstream SaaS, a lateral-movement hunt
scoped to the compromised principal's blast radius, and a final IAM
audit to remove residual persistence (rogue OAuth consents, app
passwords, conditional-access exceptions) left behind by the
compromise.

The playbook is the **chain anchor** of the sovereign-security
notification chain: `phishing_triage` (BEC and credential-harvest
branches) escalates into `identity_compromise`, and — where data
exfiltration follows — `identity_compromise` hands off into
`data_exfil`. The three workflows feed the one submission engine
`incident_management` at the tail:

```
phishing_triage ─► identity_compromise ─► data_exfil ─► incident_management
```

Identity compromise itself is the upstream signal source for the
NIS2 Art. 23 and DORA Art. 19 notification legs when the case
crosses the significant-incident threshold (impact on essential
services, lateral-movement confirmed, data-exposure indicator, or
financial-entity classification). The 24-hour early warning, the
72-hour notification, the DORA 4-hour initial / 72-hour intermediate
cadence, and the GDPR Art. 33 / 34 breach-notification legs run on
`playbook.incident_management@v1` — this playbook produces the
principal-blast-radius and lateral-movement evidence that feeds the
downstream submissions.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the triage, the
confirmed-branch gate, the MFA reset, the session revocation, the
lateral-movement hunt, and the IAM audit land in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/identity_compromise/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.identity_compromise@v1)

content/mappings/nis2/article-21-2-b.yaml
                                  # NIS2 Art. 21(2)(b) inbound anchor —
                                  # incident-handling capability;
                                  # backlinks playbook.identity_compromise@v1
                                  # as the operational discharge of
                                  # detect-through-contain-through-audit
                                  # for the credential-theft / MFA-bypass
                                  # / suspicious sign-in case set
content/mappings/nis2/article-21-2-i.yaml
                                  # NIS2 Art. 21(2)(i) inbound anchor —
                                  # HR security and access-control
                                  # (joiner-mover-leaver, privileged-
                                  # access review); backlinks the IAM
                                  # audit and persistence-removal step
content/mappings/nis2/article-23.yaml
                                  # NIS2 Art. 23 inbound anchor —
                                  # 24-hour early warning and 72-hour
                                  # notification, backlinking to
                                  # playbook.identity_compromise@v1
                                  # as an upstream signal source into
                                  # the regulator-submission engine
content/mappings/dora/article-19-and-28.yaml
                                  # DORA Art. 18 major-classification
                                  # and Art. 19 initial-4h / intermediate-
                                  # 72h notification, backlinking to
                                  # playbook.identity_compromise@v1 for
                                  # the financial-sector regulator-
                                  # notification chain
content/mappings/cra/annex-i-1-essential-cybersecurity.yaml
                                  # CRA Annex I §1(d) authentication and
                                  # least-privilege anchor —
                                  # playbook.identity_compromise@v1 is the
                                  # agentic anchor for the least-privilege
                                  # evidence on the principal after a
                                  # compromise
content/mappings/gdpr/data-flow-identity_compromise.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity for the principal-identifier
                                  # processing (sign-in metadata, MFA
                                  # state, session-revocation events)
                                  # this playbook operates on
```

The CACAO source is canonical. The five action steps, one
`if-condition`, and one `start` / two `end` wiring nodes are the
deterministic policy the playbook *means* — a triage step feeding a
confirmed-branch gate that either short-circuits to a false-positive
end or drives the linear containment-and-audit chain (MFA reset →
session revocation → lateral-movement hunt → IAM audit) through to
the containment-complete end. The three worked examples under
`examples/{n8n,temporal,langgraph}/identity_compromise/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the IdP the containment step cuts the principal out at, the SaaS-
side session-revocation surface, the API-audit source the lateral-
movement hunt reads, the IAM control plane the audit step tightens,
and the downstream regulator-submission engine — is the operator's
data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships nine steps: one `start`, five `action`, one
`if-condition`, and two `end` (the terminal end and a distinct
false-positive end so the false-verdict branch is audit-evident).
The `if-condition` fires on `__compromise_confirmed__`; `on_success`
routes into `reset MFA factors` and then linearly through the four
containment-and-audit steps; `on_failure` short-circuits to the
false-positive end. Downstream regulator / customer notification is
not on this playbook — the significance-threshold gate and the per-
stage submissions run on `playbook.incident_management@v1` from the
evidence this playbook emits (see § 4 and § 11).

| Step suffix | Step                                                | Discipline                                                                                                                                                                                                                                | Status         |
|-------------|-----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | identity_compromise-start                           | edge wiring only — no body                                                                                                                                                                                                                | n/a            |
| `…000002`   | triage identity signal                              | hydrate the originating identity-protection signal (impossible travel, password spray, MFA bypass, suspicious OAuth grant, anomalous sign-in) with principal context and recent sign-in history; decides `__compromise_confirmed__`         | operator-bound |
| `…000003`   | compromise confirmed?                               | `if-condition` — branches on `__compromise_confirmed__` (true → reset MFA factors, false → false-positive end)                                                                                                                             | n/a            |
| `…000004`   | reset MFA factors                                   | revoke existing TOTP / WebAuthn registrations, invalidate app passwords, and force re-enrolment of authenticators for the compromised principal so the privileged path stays gated by a strong second factor after containment            | operator-bound |
| `…000005`   | revoke active sessions                              | invalidate live sessions, refresh tokens, and persistent device grants across the IdP and downstream SaaS so the attacker is forced back through the gated re-authentication path                                                          | operator-bound |
| `…000006`   | lateral-movement hunt                               | behavioural and traffic review of downstream activity attributable to the compromised principal — STS / AssumeRole traces, OAuth grants, cross-tenant sign-ins, downstream SaaS API hits — over the configured lookback window            | operator-bound |
| `…000007`   | IAM audit and persistence removal                   | review of the principal's IAM surface for residual persistence — rogue OAuth consents, third-party app grants, conditional-access exceptions, lingering role assumptions — and tightening back to the least-privilege baseline             | operator-bound |
| `…000008`   | identity_compromise-end                             | edge wiring only — no body (containment complete)                                                                                                                                                                                          | n/a            |
| `…000009`   | identity_compromise-false-positive-end              | edge wiring only — no body (triage did not confirm compromise)                                                                                                                                                                             | n/a            |

All five action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (detection, control,
telemetry, metric). One execution short-circuits to the false-
positive end when triage does not confirm the compromise, or runs
the linear four-step containment chain (reset MFA → revoke sessions →
lateral-movement hunt → IAM audit) exactly once. Per-case metric
accounting into the MTTD / MTTC / lateral-hunt-coverage catalogue
entries is unambiguous.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The overlay pins the control, detection, telemetry,
> and metric surface; the n8n reference emitter ships a committed
> `workflow.n8n.json` today, and the Temporal / LangGraph siblings
> ship deterministic emitter output with `NotImplementedError`
> activity / tool bodies pending the per-target CORE cards.
> Cross-target byte-parity goldens live under
> `tests/examples/identity_compromise/`.

## 3. Lifecycle contract — the five action states

The per-case payload — principal context, sign-in history, MFA
state, session-revocation record, lateral-movement hunt findings, and
IAM-audit residue — is incident-handling content that carries
personal data of natural persons (the compromised principal's
identifier, group memberships, recent-sign-in geography and device
context). The inbound GDPR Art. 30 Record of Processing Activity at
[`content/mappings/gdpr/data-flow-identity_compromise.md`](../../content/mappings/gdpr/data-flow-identity_compromise.md)
covers the principal-identifier processing the five steps below
operate on, lawful-basis-grounded in GDPR Art. 6(1)(f) legitimate
interests with Art. 6(1)(c) legal obligation as the secondary basis
where NIS2 Art. 21(2)(b) / (2)(i) transposition applies. The
framework treats the principal identifier as an IdP-scoped opaque
identifier under the operator's own naming convention and does not
re-derive subject identifiers outside the operator's own identity
surface.

**triage identity signal** (`…000002`)
:   Hydration step. Reads the operator's IdP / identity-protection
    layer for the originating signal against the principal
    identifier, joins it with principal context (role, group
    memberships, recent sign-in history, MFA state, conditional-
    access decisions) and decides `__compromise_confirmed__`.
    Anchored on MITRE D3FEND v1.0.0 `D3-UBA` (User Behavior
    Analysis) — the hydration of the case object the confirmed-
    branch gate and the downstream containment steps read against.
    Anchored on OSCAL IA-4 (Identifier Management) — the operational
    evidence that the principal is resolved to a unique,
    authoritative identifier before containment acts. Consumes OCSF
    **Detection Finding** (class 2004) as the originating signal and
    OCSF **Authentication** (class 3002) for the sign-in-history
    hydration. Feeds `kpi.mttd_identity_compromise@v1`.

**compromise confirmed?** (`…000003`, `if-condition`)
:   Deterministic branch on `__compromise_confirmed__`. `on_success`
    (confirmed) routes into `reset MFA factors` and then linearly
    through the four containment-and-audit steps; `on_failure`
    (false positive) short-circuits to the false-positive end. The
    false-positive branch is a distinct terminal end so the close-
    out is audit-evident on the CACAO trail. Anchored on OSCAL IR-4
    (Incident Handling).

**reset MFA factors** (`…000004`)
:   MFA-reset step. Revokes existing TOTP / WebAuthn registrations,
    invalidates app passwords, and forces re-enrolment of
    authenticators for the compromised principal. Anchored on MITRE
    D3FEND v1.0.0 `D3-MFA` (Multi-factor Authentication) and OSCAL
    IA-5 (Authenticator Management) with IA-2(1) (MFA to Privileged
    Accounts) reinforcing on the privileged-path side. Emits OCSF
    **Account Change** (class 3001) per factor revocation so the
    timeline-signal controls can audit on-time containment.

**revoke active sessions** (`…000005`)
:   Session-revocation step. Invalidates live sessions, refresh
    tokens, and persistent device grants across the IdP and
    downstream SaaS so the attacker is forced back through the gated
    re-authentication path. Anchored on MITRE D3FEND v1.0.0 `D3-ACI`
    (Authentication Cache Invalidation) and OSCAL AC-2(13) (Account
    Management | Disable Accounts for High-Risk Individuals) — the
    operational analogue of disabling a high-risk account for the
    duration of the containment window. Emits OCSF **Account
    Change** (class 3001) per session / token invalidation.
    Stamps `kpi.mttc_identity_compromise@v1`.

**lateral-movement hunt** (`…000006`)
:   Hunt step. Behavioural and traffic review of downstream activity
    attributable to the compromised principal within the configured
    lookback window — STS / AssumeRole traces, OAuth grants, cross-
    tenant sign-ins, downstream SaaS API hits. Anchored on MITRE
    D3FEND v1.0.0 `D3-UBA` (User Behavior Analysis — the behavioural
    leg) and `D3-NTA` (Network Traffic Analysis — the API and audit-
    log traffic leg). Anchored on OSCAL AU-6 (Audit Record Review,
    Analysis, and Reporting). Consumes OCSF **Authentication**
    (class 3002) and OCSF **API Activity** (class 6003) over the
    lookback window. Findings feed the significance-threshold verdict
    that gates the downstream NIS2 Art. 23 / DORA Art. 19
    notification chain on `playbook.incident_management@v1`. Feeds
    `kri.lateral_hunt_coverage@v1`.

**IAM audit and persistence removal** (`…000007`)
:   IAM-audit step. Review of the principal's IAM surface for
    residual persistence — rogue OAuth consents, third-party app
    grants, conditional-access exceptions, lingering role
    assumptions, app-password remnants — and tightening back to the
    least-privilege baseline. Anchored on MITRE D3FEND v1.0.0
    `D3-AM` (Account Monitoring — the IAM-surface review leg),
    `D3-LAM` (Local Account Monitoring — the cloud-IAM least-
    privilege leg), and `D3-SCP` (System Configuration Permissions —
    the configuration-level permissions leg). Anchored on OSCAL AC-2
    (Account Management). Emits OCSF **Account Change** (class 3001)
    per persistence artefact removed. The CRA Annex I §1(d)
    least-privilege evidence is the audit trail this step leaves
    behind — the inbound anchor at
    [`content/mappings/cra/annex-i-1-essential-cybersecurity.yaml`](../../content/mappings/cra/annex-i-1-essential-cybersecurity.yaml)
    (`cra:annex-i-1-access-control`) is discharged here.

The five action steps are operator-bound runtime seams: the
framework ships neither the IdP, the MFA-provider surface, the
SaaS-side session-revocation API, the API-audit source, nor the IAM
control plane. The playbook is the portable description of *what*
the operator's stack should do per case; binding those seams to
real endpoints is the operator's job.

> **LM determinism.** Triage, MFA reset, session revocation,
> lateral-movement hunt, and IAM audit are structured reads and
> writes against operator-owned surfaces, not free-text reasoning
> steps. The playbook binds no DSPy signature — there is no
> LM-driven step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven behavioural classifier on top of the
> triage step or the lateral-movement hunt (a private, forward-
> looking extension), the framework-wide EU-resident LM endpoint
> guard re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
> Free-text narrative fields on the downstream regulator submissions
> are handled by `playbook.incident_management@v1` under its own
> DSPy signature schema.

## 4. Regulatory anchors

**NIS2 Article 21(2)(b)** — incident-handling capability. The clause
requires essential and important entities to operate an incident-
handling capability (detect, triage, contain, remediate, capture
lessons learned). The identity_compromise playbook is the
**operational discharge of detect-through-contain-through-audit for
the credential-theft / MFA-bypass / suspicious sign-in case set**;
the regulator-notification tail is handed off to
`playbook.incident_management@v1`. Inbound anchor at
[`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
(`nis2:art-21-2-b`) backlinks `playbook.identity_compromise@v1`.

**NIS2 Article 21(2)(i)** — HR security and access control. The
clause requires operators to run access-control processes with
joiner-mover-leaver and privileged-access review evidence. The IAM
audit and persistence-removal step is the operational evidence for
least-privilege enforcement on the principal after a compromise.
Inbound anchor at
[`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml)
(`nis2:art-21-2-i`).

**NIS2 Article 23** — incident-reporting obligations. Article 23(4)(a)
requires a 24-hour early warning and Article 23(4)(b) requires a
72-hour notification with an initial assessment of severity and
impact. The identity_compromise playbook is an **upstream signal
source** into the regulator-submission engine: the lateral-movement
hunt findings and the IAM-audit residue feed the assessment that
`playbook.incident_management@v1` emits on the 24-hour and 72-hour
legs. The significance-threshold verdict — impact on essential
services, lateral-movement confirmed, data-exposure indicator — is
computed off the evidence this playbook produces. Inbound anchors at
[`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
(`nis2:art-23-early-warning`, `nis2:art-23-notification-72h`).

**DORA Article 18(1)** — classification. Requires classification of
ICT-related incidents against the criteria in the JC RTS on incident
classification (Commission Delegated Regulation (EU) 2024/1772). The
identity_compromise playbook's triage, lateral-movement hunt, and
IAM-audit outputs produce the principal-blast-radius and lateral-
movement evidence that drives the major-classification verdict on
the downstream `playbook.incident_management@v1` engine. Inbound
anchor at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-18-classification`).

**DORA Article 19** — reporting of major ICT-related incidents.
Article 19(4)(a) requires an initial notification within 4 hours of
major-classification and Article 19(4)(b) requires an intermediate
notification within 72 hours with updated assessment. The
identity_compromise playbook's containment artefacts (MFA reset,
session revocation, principal-scope hunt results) anchor the initial
notification payload; the IAM-audit closure and the lateral-movement
findings feed the updated assessment for the intermediate report on
the downstream `playbook.incident_management@v1` engine. Inbound
anchors at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-19-initial-4h`, `dora:art-19-intermediate-72h`).

**GDPR Articles 33 and 34** — personal-data-breach notification.
Article 33 requires supervisory-authority notification within 72
hours when a personal-data breach is likely to result in a risk to
the rights and freedoms of natural persons; Article 34 requires
communication to the affected data subjects without undue delay
when the risk is high. Identity compromise trips the Art. 33 / 34
chain when principal-identifier processing crosses the threshold —
typically when the lateral-movement hunt confirms downstream data
access on personal data. The routing itself runs jointly with the
NIS2 Art. 23 and DORA Art. 19 lanes on
`playbook.incident_management@v1`; the anchor at
[`content/mappings/gdpr/article-33-34-personal-data-breach-notification.yaml`](../../content/mappings/gdpr/article-33-34-personal-data-breach-notification.yaml)
carries the closure. The per-workflow Record of Processing Activity
for this playbook lives at
[`content/mappings/gdpr/data-flow-identity_compromise.md`](../../content/mappings/gdpr/data-flow-identity_compromise.md).

**CRA Annex I §1(d)** — authentication and least-privilege. Requires
manufacturers to design products with access-control processes that
enforce authentication and least privilege. The identity_compromise
playbook is the **agentic anchor for the least-privilege evidence
on the principal after a compromise** — the IAM audit and
persistence-removal step is the operational trail that residual
persistence has been walked back to the least-privilege baseline.
Inbound anchor at
[`content/mappings/cra/annex-i-1-essential-cybersecurity.yaml`](../../content/mappings/cra/annex-i-1-essential-cybersecurity.yaml)
(`cra:annex-i-1-access-control`). Identity compromise on its own is
sub-threshold for CRA Art. 14 product-side vulnerability
notification; the CRA Art. 14 chain runs on `playbook.vuln_intake@v1`.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/identity_compromise/mappings.yaml`](../../content/playbooks/identity_compromise/mappings.yaml)):
IR-4 (Incident Handling — anchors the playbook end-to-end),
IR-6 (Incident Reporting — anchors the significance-threshold
escalation into the downstream regulator-submission engine),
IA-4 (Identifier Management — anchors the triage step's principal
resolution), IA-5 (Authenticator Management — anchors the MFA-reset
step), IA-2(1) (MFA to Privileged Accounts — reinforces MFA reset on
the privileged path), AC-2 (Account Management — anchors the IAM
audit step), AC-2(13) (Account Management | Disable Accounts for
High-Risk Individuals — anchors the session-revocation step),
AU-6 (Audit Record Review, Analysis, and Reporting — anchors the
lateral-movement hunt).

**MITRE D3FEND v1.0.0** — `D3-UBA` (User Behavior Analysis) at
`triage identity signal` and at `lateral-movement hunt`; `D3-MFA`
(Multi-factor Authentication) at `reset MFA factors`; `D3-ACI`
(Authentication Cache Invalidation) at `revoke active sessions`;
`D3-NTA` (Network Traffic Analysis) at `lateral-movement hunt`;
`D3-AM` (Account Monitoring), `D3-LAM` (Local Account Monitoring),
and `D3-SCP` (System Configuration Permissions) at `IAM audit and
persistence removal`. Three techniques on the IAM-audit step is
deliberate: the account-surface review, the cloud-IAM least-
privilege evidence, and the configuration-level permissions leg are
three concurrent defensive actions the audit step discharges in a
single case.

**OCSF v1.3.0** — `Detection Finding` (class_uid 2004, category
Findings), direction `consumes`. Consumed at the triage step as the
originating identity-protection signal from the upstream Sigma /
IdP-native detector referenced under `external_references` on the
CACAO playbook. `Authentication` (class_uid 3002, category Identity
& Access Management), direction `consumes`. Consumed at the triage
step (sign-in-history hydration) and at the lateral-movement hunt
(cross-lookback sign-in review). `API Activity` (class_uid 6003,
category Application Activity), direction `consumes`. Consumed at
the lateral-movement hunt step for API-call traces (cloud control-
plane actions, STS / AssumeRole chains, downstream SaaS API hits).
`Account Change` (class_uid 3001, category IAM), direction `emits`.
Emitted by the MFA-reset, session-revocation, and IAM-audit steps
per containment action on the principal so the timeline-signal
controls can audit on-time containment. `Compliance Finding`
(class_uid 2003, category Findings), direction `emits`. Emitted by
the downstream regulator-notification chain on
`playbook.incident_management@v1` from the envelope this playbook
feeds; the outbound overlay records the emission for closure even
though the emission itself lives downstream.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the identity-compromise topology

`examples/n8n/identity_compromise/workflow.n8n.json` carries the
CACAO topology as nine n8n nodes (`manualTrigger`, five `set` nodes,
one `if`, two `noOp` terminals), with node ids preserving the CACAO
step ids verbatim. The five action steps emit `n8n-nodes-base.set`
nodes carrying the CACAO I/O contract as editable assignment rows
plus the `x_secops_ng` reference bundles (detection, control,
telemetry, metric). The `if-condition` node (`compromise confirmed?`)
emits an `n8n-nodes-base.if` with a placeholder condition the
operator wires to the upstream `out.compromise_confirmed` field. The
lossy translations are recorded in `meta.secops_ng_notes` so the
integrator sees exactly which seams need attention.

Operators bind the Set rows to their connectors:

- `triage identity signal` → the operator's IdP / identity-protection
  layer's signal-fetch and sign-in-history APIs against the principal
  identifier; writes `__compromise_confirmed__`.
- `reset MFA factors` → the operator's MFA-provider surface (TOTP /
  WebAuthn revoke + re-enrol; app-password invalidation).
- `revoke active sessions` → the operator's IdP session-invalidation
  API and downstream SaaS session-revocation surface.
- `lateral-movement hunt` → the operator's API-audit source
  (CloudTrail / Azure Activity Log / GCP Audit Logs), IdP sign-in
  logs, and OAuth-grant catalogue.
- `IAM audit and persistence removal` → the operator's IAM control
  plane (role / policy / third-party-app-grant / conditional-access-
  exception surface).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/identity_compromise/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/identity_compromise/workflow.n8n.json`. The workflow
is inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/identity_compromise/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the five action
activities documenting their operator-bound seam (triage / MFA reset
/ session revocation / hunt / IAM audit). The committed stub raises
`NotImplementedError` in the activity bodies pending the CORE-
TEMPORAL sibling card that wires the deterministic activity
implementations into the Temporal target; operators can drop the
module next to their worker today to see the topology and the
activity signatures.

Temporal is a natural fit for the identity-compromise discipline:
each case becomes one workflow run; the confirmed-branch gate
becomes a Temporal conditional; retries against transient failures
on the IdP / MFA provider / SaaS session API / API-audit source get
first-class Temporal semantics (activity retry policy per seam);
replay against the same Temporal event history re-derives the same
containment record and the same IAM-audit residue once the activity
bodies are wired.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/identity_compromise/state_bindings.py` carries
the `TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes,
conditional edge on `__compromise_confirmed__`, linear edges through
the four containment steps to the terminal end, and the direct edge
from the false-branch to the false-positive end); `assemble.py` is
the hand-written reference assembly that wires the GraphSpec +
bindings into a `langgraph.graph.StateGraph`. The committed
`state_bindings.py` is a generated stub: each tool's docstring names
the operator-bound seam it discharges and the body raises
`NotImplementedError` until the CORE-LANGGRAPH sibling card wires
the deterministic tool implementations into the LangGraph target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven behavioural classifier on top of the `triage identity
signal` or the `lateral-movement hunt` step (reading the enriched
context and emitting the `__compromise_confirmed__` verdict or the
hunt findings summary) fills that as a private extension. The
framework-wide EU-resident LM endpoint guard re-applies the check at
process startup (`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/identity_compromise/`,
`examples/temporal/identity_compromise/`,
`examples/langgraph/identity_compromise/`). The n8n target ships a
committed workflow artifact; the Temporal and LangGraph targets
ship deterministic emitter output with `NotImplementedError`
activity / tool bodies pending the per-target CORE cards. Cross-
target byte-parity goldens land under
`tests/examples/identity_compromise/` — the same cross-target byte-
parity property the framework relies on for the rest of the
playbook set.

## 6. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the operator-
bound seam call or the (pending) primitive body. The mirror runs
unconditionally, ahead of any OTLP exporter, so the audit property
holds even when the operator has not configured a collector —
typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`, `if-condition`). |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
and never imports a vendor SDK; pointing the exporter at a managed
APM is a downstream choice the operator owns end-to-end. The
sovereignty posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Metrics — what the identity-compromise response exposes

Three indicator catalogue entries surface the identity_compromise
posture to the operator's metrics dashboard. Two further entries
(`kri.regulator_notification_overrun@v1`,
`kpi.notification_sla_compliance@v1`) are stamped downstream on
`playbook.incident_management@v1` from the envelope this playbook
feeds when the significance threshold is crossed. The catalogue
entries live under `content/metrics/`.

- **`kpi.mttd_identity_compromise@v1`** — time from earliest
  telemetry evidence to the first authoritative detection firing on
  the identity-compromise case. Catalogue:
  [`content/metrics/mttd_identity_compromise.yaml`](../../content/metrics/mttd_identity_compromise.yaml).
  Rising values indicate the identity-protection surface is drifting
  behind the operational objective.
- **`kpi.mttc_identity_compromise@v1`** — median time from triage
  confirmation to containment completion (MFA reset + session
  revocation completed). Catalogue:
  [`content/metrics/mttc_identity_compromise.yaml`](../../content/metrics/mttc_identity_compromise.yaml).
  Stamped by the session-revocation step; audits on-time containment
  across the two-legged discipline (factor revocation + cache
  invalidation).
- **`kri.lateral_hunt_coverage@v1`** — share of confirmed identity-
  compromise cases whose lateral-movement hunt covered the full
  operator-configured lookback window on both the behavioural
  (Authentication) and traffic (API Activity) surfaces. Catalogue:
  [`content/metrics/lateral_hunt_coverage.yaml`](../../content/metrics/lateral_hunt_coverage.yaml).
  Stamped by the lateral-movement hunt step; low values indicate the
  hunt is running against an incomplete telemetry surface and the
  significance verdict downstream may be under-classifying cases.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI / KRI series against their own metrics backend.

## 8. Detection references — the SigmaHQ named rules

The playbook cites six upstream **SigmaHQ / MITRE ATT&CK-anchored
signal shapes** on its `external_references` (rule ids pinned
upstream at SigmaHQ, not re-authored here):

- **Impossible travel — Azure AD Identity Protection.** Attaches at
  the triage step as the originating signal for the impossible-
  travel case shape.
- **Impossible travel activity — Microsoft 365.** Attaches at the
  triage step as an alternative upstream carrier over Microsoft 365
  audit logs.
- **Password spray — Azure AD Identity Protection.** Attaches at the
  triage step for the credential-access case shape (MITRE ATT&CK
  T1110.003).
- **MFA bypass via legacy client authentication.** Attaches at the
  triage step for the legacy-auth-flow case shape used to sidestep
  conditional access / MFA.
- **MFA disabled to bypass authentication.** Attaches at the IAM
  audit step as a corroborating signal that a factor was disabled
  administratively during the incident window.
- **AWS STS AssumeRole misuse.** Attaches at the lateral-movement
  hunt step for the role-chaining case shape (MITRE ATT&CK
  T1078.004).

The MITRE ATT&CK anchors on the playbook — T1078 (Valid Accounts)
and T1110 (Brute Force) — pin the case-shape taxonomy the triage and
hunt steps read against. See
[`content/playbooks/identity_compromise/README.md`](../../content/playbooks/identity_compromise/README.md)
for the rule-reference discipline (SecOps-NG does not re-author
Sigma; upstream rule ids are pinned by the CORE-layer detection
mapping).

## 9. Operator customisation points

The playbook is an identity-compromise-response machine; the *policy*
it exercises is the operator's. The customisation seams:

- **MFA-provider bindings.** The `reset MFA factors` step reads the
  operator's MFA-provider surface — the TOTP / WebAuthn revoke +
  re-enrol API and the app-password invalidation surface. The
  framework binds neither the vendor (Duo, Okta, Azure MFA, Google
  Authenticator, YubiKey management, self-hosted) nor the fetch API;
  operators wire the step to whichever provider their environment
  runs on.
- **Session-revocation surface.** The `revoke active sessions` step
  reads two independent surfaces — the IdP's own session-
  invalidation API and the downstream SaaS session-revocation
  surface (per-provider revoke endpoints or a SCIM-driven fan-out).
  The framework binds the topology, not the vendors; operators
  wire the seam to their own IdP and the SaaS providers their
  principals authenticate into.
- **Lateral-movement hunt scope.** The `lateral-movement hunt` step
  reads the operator-configured lookback window and the operator's
  API-audit source. The window itself (24 hours vs 7 days vs longer)
  is operator-owned and tuned against
  `kri.lateral_hunt_coverage@v1`; the API-audit source (CloudTrail,
  Azure Activity Log, GCP Audit Logs, an aggregator, or a mixed
  set) is operator-owned as well. The framework does not prescribe
  the window or the source.
- **Significance threshold for NIS2 Art. 23 / DORA Art. 19 trigger.**
  The significance verdict — impact on essential services, lateral-
  movement confirmed, data-exposure indicator, financial-entity
  classification — is computed off the evidence this playbook
  produces (lateral-movement hunt findings, IAM-audit residue). The
  numeric cut-offs and the qualitative predicates live on the
  downstream `playbook.incident_management@v1` gate, per the
  operator's regulator-routing policy. The framework documents the
  seam but does not prescribe the threshold.
- **Notification-recipient list.** The regulator-notification tail
  itself runs on `playbook.incident_management@v1`. Which authority
  receives which regime's submission — national CSIRT under NIS2,
  competent authority under DORA, supervisory authority under GDPR
  — is per Member State and per sector, and is the operator's to
  configure at the downstream engine's pre-bound regulator channel.
- **IAM control plane.** The `IAM audit and persistence removal`
  step reads the operator's IAM control plane (role / policy /
  third-party-app-grant / conditional-access-exception surface).
  The framework binds the seam, not the vendor.

## 10. Replay and audit story

The byte-parity drift guards land with the CORE-TEMPORAL /
CORE-LANGGRAPH sibling cards under
`tests/examples/identity_compromise/`. Each per-target golden pins
the committed worked-example artifact to a fresh emitter run from
the canonical CACAO source; if the compiler or the playbook changes,
regenerate via the per-target `regenerate.sh` and commit the diff
intentionally.

The cross-target replay property is the harder one: the same case,
fed through n8n / Temporal / LangGraph, produces byte-identical
containment records *and* byte-identical IAM-audit residue once each
target's activity / tool bodies are wired against the same operator
seams and the same OSCAL / OCSF / D3FEND reference bundles. The
`(principal_id, compromise_confirmed, mfa_reset_at, sessions_revoked,
lateral_movement_findings, iam_audit_residue)` key is the string a
regulator can diff to confirm the property holds across targets.

## 11. Playbook chain — where identity_compromise sits

The regulator-notification chain expresses itself as three
workflows feeding one submission engine — identity_compromise is
the middle link:

```
phishing_triage ─► identity_compromise ─► data_exfil ─► incident_management
```

- **Upstream: `phishing_triage`.** The BEC and credential-harvest
  branches on `playbook.phishing_triage@v1` escalate into
  identity_compromise. `phishing_triage` itself is deliberately
  sub-threshold for DORA Art. 18 major-classification per the
  inbound carve-out at
  [`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml);
  the DORA / NIS2 / GDPR backlinks live on identity_compromise and
  data_exfil, not on phishing_triage. See
  [`docs/cookbook/phishing_triage.md`](./phishing_triage.md).
- **Downstream: `data_exfil`.** When the lateral-movement hunt or
  the IAM audit reveals downstream data access on personal data,
  the case escalates into `playbook.data_exfil@v1` for egress-
  signal triage, scope assessment, containment on the egress
  chokepoint, and regulator- / customer-notification-envelope
  composition. See
  [`docs/cookbook/data_exfil.md`](./data_exfil.md).
- **Downstream: `incident_management`.** The regulator-submission
  timeline itself (NIS2 Art. 23 24-hour / 72-hour / one-month,
  DORA Art. 19 4-hour / 72-hour, GDPR Art. 33 72-hour) runs on
  `playbook.incident_management@v1`. See
  [`docs/cookbook/incident_management.md`](./incident_management.md).

The chain lets identity_compromise stay narrowly focused on the
principal-side containment-and-audit discipline while the upstream
BEC / credential-harvest triage happens on `phishing_triage`, the
downstream egress-signal response happens on `data_exfil`, and the
per-stage regulator submissions happen on `incident_management`.
The chain is not code-coupled — each playbook is a standalone CACAO
artifact that can be run in isolation — but the audit trail's
coherence across the four workflows is the sovereign-security
property the framework guarantees.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  IdP, the MFA provider, the SaaS session-revocation surface, the
  API-audit source, the IAM control plane, or the downstream
  regulator-submission engine. Connectors are operator-bound at
  runtime against environment variables documented per target.
- **Per-stage regulator submissions.** The 24-hour early warning,
  the 72-hour notification, the one-month final report (NIS2), the
  4-hour initial / 72-hour intermediate (DORA), and the 72-hour
  supervisory-authority notification (GDPR Art. 33) all run on
  `playbook.incident_management@v1`. This playbook produces the
  principal-blast-radius and lateral-movement evidence that feeds
  the downstream submissions; the per-stage submissions are
  downstream.
- **Downstream egress-signal response.** DLP / egress-signal
  triage, scope assessment on affected-subjects count and data
  classification, and egress-side containment run on
  `playbook.data_exfil@v1`. The lateral-movement hunt on this
  playbook is scoped to the principal's blast radius on the
  identity surface — the egress side is downstream.
- **Product-side CRA vulnerability notification.** CRA Art. 14
  product-side vulnerability-notification obligations run on
  `playbook.vuln_intake@v1`. The Annex I §1(d) authentication /
  least-privilege leg (this playbook) and the Art. 14 product-side
  notification leg are separate lanes.
- **SigmaHQ rule id pinning.** The playbook cites six upstream
  Sigma / IdP-native rule *names* (impossible travel, password
  spray, MFA bypass via legacy auth, MFA disabled, STS AssumeRole
  misuse, M365 impossible-travel activity). Stable upstream rule
  ids are pinned by the CORE-layer detection mapping, not by this
  cookbook; SecOps-NG does not re-author Sigma.

## 13. References

- [`content/playbooks/identity_compromise/README.md`](../../content/playbooks/identity_compromise/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/identity_compromise/mappings.yaml`](../../content/playbooks/identity_compromise/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay with
  per-step control anchors.
- [`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
  — NIS2 Article 21(2)(b) inbound anchor (incident-handling
  capability).
- [`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml)
  — NIS2 Article 21(2)(i) inbound anchor (HR security /
  access-control review).
- [`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
  — NIS2 Article 23 inbound anchor (24-hour early warning, 72-hour
  notification).
- [`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
  — DORA Articles 18 and 19 inbound anchor (major-classification,
  4-hour initial, 72-hour intermediate).
- [`content/mappings/gdpr/article-33-34-personal-data-breach-notification.yaml`](../../content/mappings/gdpr/article-33-34-personal-data-breach-notification.yaml)
  — GDPR Articles 33 and 34 personal-data-breach notification
  anchor.
- [`content/mappings/gdpr/data-flow-identity_compromise.md`](../../content/mappings/gdpr/data-flow-identity_compromise.md)
  — GDPR Article 30 Record of Processing Activity.
- [`content/mappings/cra/annex-i-1-essential-cybersecurity.yaml`](../../content/mappings/cra/annex-i-1-essential-cybersecurity.yaml)
  — CRA Annex I §1(d) authentication / least-privilege inbound
  anchor.
- [`examples/n8n/identity_compromise/README.md`](../../examples/n8n/identity_compromise/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/identity_compromise/README.md`](../../examples/temporal/identity_compromise/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/identity_compromise/README.md`](../../examples/langgraph/identity_compromise/README.md)
  — LangGraph worked-example stub.
- [`docs/cookbook/phishing_triage.md`](./phishing_triage.md)
  — upstream cookbook (BEC and credential-harvest branches escalate
  in).
- [`docs/cookbook/data_exfil.md`](./data_exfil.md)
  — downstream cookbook (egress-signal response when data exfil
  follows).
- [`docs/cookbook/incident_management.md`](./incident_management.md)
  — downstream cookbook (per-stage regulator-submission engine).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
