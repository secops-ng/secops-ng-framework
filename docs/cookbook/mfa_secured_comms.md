# mfa_secured_comms — cookbook walkthrough

Multi-factor and continuous-authentication coverage plus secured
emergency-communications readiness under NIS2 Article 21(2)(j),
DORA Article 9(4)(b), and CRA Annex I §1(d). The
`playbook.mfa_secured_comms@v1` CACAO playbook operates the
per-window measurement discipline the authentication and
secured-communications policy owes: it probes the identity-provider
surface for MFA enrolment and enforcement state across in-scope
principals, assesses whether continuous-authentication signals hold
on long-lived sessions against the declared re-authentication
cadence, verifies each out-of-band emergency-communications channel
is reachable independently of the primary information-system path,
publishes a dated posture-attestation to the operator's evidence
store, and notifies the authentication owner.

The playbook is the **read-only posture-probe materialisation** of
the strong-authentication and secured-communications obligation. It
is the measurement sibling of the reactive
`playbook.identity_compromise@v1`: identity_compromise resets
factors, revokes sessions, and audits a live suspected credential-
theft or MFA-bypass event on the identity surface; this playbook
runs the periodic read-only pass that confirms the MFA and
continuous-authentication enforcement remains in place and the
out-of-band channel remains reachable — no enrolment, no factor
reset, no forced re-authentication, no channel mutation. The two
are complementary, not duplicative:

```
mfa_secured_comms   (per-window posture-probe, read-only)
   └── probe MFA coverage ─► assess continuous auth ─► verify OOB
       ─► attest ─► notify owner

identity_compromise (reactive on live suspected compromise)
   └── triage identity signal ─► reset MFA ─► revoke sessions
       ─► notify affected principals
```

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the MFA
coverage probe, the continuous-authentication assessment, the OOB
channel verification, the posture-attestation emission, and the
authentication-owner notification land in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/mfa_secured_comms/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / OCSF / D3FEND / NIS2 / DORA / CRA overlay
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.mfa_secured_comms@v1)
└── primitives/
    ├── probe.py                 # probe_mfa_coverage — per-principal enrolment / enforcement snapshot
    ├── assess.py                # assess_continuous_auth — per-session staleness verdict list
    ├── verify.py                # verify_oob_channel — per-channel reachability status list
    └── artifact.py              # build_mfa_posture_attestation_artifact — dated attestation record

content/mappings/nis2/article-21-2-j.yaml
                                  # NIS2 Art. 21(2)(j) inbound anchor —
                                  # multi-factor or continuous
                                  # authentication, secured voice /
                                  # video / text communications, and
                                  # secured emergency-communications
                                  # systems
content/mappings/dora/article-9-4-b-authentication.yaml
                                  # DORA Art. 9(4)(b) inbound anchor —
                                  # strong authentication mechanisms
                                  # against the JC RTS on ICT risk
                                  # management framework (Commission
                                  # Delegated Regulation (EU)
                                  # 2024/1774, Arts. 21–22 on access
                                  # management and authentication)
content/mappings/cra/annex-i-1-d-access-control-mfa-coverage.yaml
                                  # CRA Annex I §1(d) inbound anchor —
                                  # authentication-enforcement and
                                  # secured-communications lane
                                  # (fourth sibling under §1(d)
                                  # alongside identity_compromise,
                                  # iam_auditor, and
                                  # onboarding_offboarding_tracker)
content/mappings/gdpr/data-flow-mfa_secured_comms.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity for the identity-provider
                                  # surface read, the session-
                                  # management surface read, the
                                  # posture-attestation emission, and
                                  # the authentication-owner
                                  # notification; personal-data
                                  # surface is real (principal
                                  # identifiers, per-principal
                                  # enrolment / enforcement state,
                                  # per-session staleness verdicts) so
                                  # the ROPA entry is authoritative
```

The CACAO source is canonical. The five action steps and the one
`start` / one `end` wiring node are the deterministic policy the
playbook *means* — a linear
probe → assess → verify → attest → notify chain with no conditional
branching at the workflow layer. The three worked examples under
`examples/{n8n,temporal,langgraph}/mfa_secured_comms/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the identity-provider surface the MFA-coverage probe reads, the
session-management surface the continuous-authentication assessment
reads, the out-of-band channel test endpoints the verify step
exercises as documented test transactions, the evidence store the
attestation step publishes to, and the authentication-owner channel
the notification step delivers on — is the operator's data plane.

The primitive layer (`content/playbooks/mfa_secured_comms/primitives/`)
carries the deterministic canonicalisation / validation / sort logic
each action step binds against. The primitives are pure and
replayable: no network, no clock reads, no LLMs. The compile target's
runtime is the source of truth for the raw observations; the
primitive layer is the byte-parity anchor across the three targets
(same primitive output => same OCSF records, same attestation
`artifact_id`).

## 2. CACAO topology and lifecycle binding

The playbook ships seven steps: one `start`, five `action`, and one
`end`. The topology is a linear probe-assess-verify-attest-notify
chain — no if-condition step at the workflow layer; the deviation
classification lives in the Compliance Finding (class_uid 2003)
records emitted by the probe, assess, and verify steps.

| Step suffix | Step                          | Discipline                                                                                                                                                                                                                                                | Status         |
|-------------|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | mfa_secured_comms_start        | edge wiring only — no body                                                                                                                                                                                                                               | n/a            |
| `…000002`   | probe MFA coverage             | read the per-principal MFA enrolment state (which factors are registered against the principal on the identity-provider surface) and enforcement state (whether the access policy that gates the privilege class requires a second factor) against the declared coverage policy | operator-bound |
| `…000003`   | assess continuous auth         | read per-principal session age and observed re-authentication events from the session-management surface, compare against the declared continuous-authentication policy (maximum session age, step-up cadence on sensitive operations), and emit the per-session verdicts | operator-bound |
| `…000004`   | verify OOB channels            | dispatch a **documented test transaction** against each declared out-of-band emergency-communications channel (voice, secure messaging, paging, SMS, email) for reachability and independence-path verification; no real emergency notification is delivered | operator-bound |
| `…000005`   | evidence capture               | compose and publish the dated authentication and secured-communications posture attestation to the operator's evidence store: MFA-coverage snapshot, continuous-authentication verdict list, OOB-channel status list, per-deviation Compliance Findings | operator-bound |
| `…000006`   | notify authentication owner    | deliver the attestation reference and the gap summary to the authentication owner along the operator's pre-bound channel (ticketing, chat, email); read-only posture-readiness dispatch — no enrolment mutation, no session mutation, no channel mutation | operator-bound |
| `…000007`   | mfa_secured_comms_end          | edge wiring only — no body (posture window closed)                                                                                                                                                                                                       | n/a            |

All five action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control,
telemetry). One execution runs the five-step chain (probe → assess
→ verify → attest → notify) exactly once per declared posture window.
Per-window metric accounting into the mfa-coverage-gaps catalogue
entry is unambiguous.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The mappings overlay pins the control and
> telemetry surface (OSCAL IA-2 / CP-8, D3FEND D3-AM on the probe
> and assess halves, OCSF API Activity and Compliance Finding); the
> n8n, Temporal, and LangGraph reference emitters ship deterministic
> emitter output under `examples/{n8n,temporal,langgraph}/mfa_secured_comms/`.
> Cross-target byte-parity goldens live under
> `tests/examples/{n8n,temporal,langgraph}/mfa_secured_comms/`.

## 3. Lifecycle contract — the five action states

The per-window payload — MFA-coverage snapshot (per-principal
enrolment and enforcement state, sorted by `principal_id`), continuous-
authentication verdict list (per-session `fresh` / `overdue` /
`policy_gap`, sorted by `session_id`), OOB-channel status list
(per-channel `ready` / `unreachable` / `independence_failure` /
`policy_gap`, sorted by `channel_id`), per-deviation Compliance
Findings, and the dated posture-attestation record — is authentication-
posture content whose personal-data surface is real: principal
identifiers, per-principal enforcement state, and per-session
staleness verdicts are all subject identifiers within the meaning of
GDPR. The GDPR Art. 30 Record of Processing Activity at
[`content/mappings/gdpr/data-flow-mfa_secured_comms.md`](../../content/mappings/gdpr/data-flow-mfa_secured_comms.md)
covers the identity-provider read, the session-management surface
read, the OOB-channel test transaction, the attestation emission, and
the authentication-owner notification processing; lawful basis is
GDPR Art. 6(1)(f) legitimate interests with Art. 6(1)(c) legal
obligation as the secondary basis where NIS2 Art. 21(2)(j) or
DORA Art. 9(4)(b) transposition applies. Per-principal enforcement
records are not persisted beyond the attestation window on the
Compliance Finding stream — the deviation records aggregate to the
principal-class and channel granularity the operator's posture-
management layer routes on.

**probe MFA coverage** (`…000002`)
:   Read step. Walks the identity providers enumerated in
    `__auth_scope__` for MFA enrolment state (registered factors per
    principal — TOTP, HOTP, WebAuthn, push, SMS, voice, email) and
    enforcement state (`enforced` / `advisory` / `not_required` /
    `policy_gap`) against the declared coverage policy for the
    principal's declared privilege class. Anchored on OSCAL IA-2
    (Identification and Authentication (Organizational Users)) — the
    MFA-coverage snapshot is the per-window measurement of the
    IA-2(1) (MFA to Privileged Accounts) and IA-2(2) (MFA to Non-
    Privileged Accounts) discipline. Anchored on D3FEND D3-AM
    (Account Monitoring) — the read-only per-principal examination
    of authentication-surface state against the operator's declared
    authentication policy. Binds against
    `content.playbooks.mfa_secured_comms.primitives.probe.probe_mfa_coverage`.
    Emits `__mfa_coverage_id__` — the stable identifier the downstream
    steps read for the MFA-coverage snapshot. Feeds
    `kri.mfa_coverage_gaps@v1`. Read-only: no enrolment, no factor
    reset, no policy mutation.

**assess continuous auth** (`…000003`)
:   Assessment step. Walks the session surfaces enumerated in
    `__auth_scope__` and compares per-principal session age and
    observed re-authentication events against the declared continuous-
    authentication policy (maximum session age before re-
    authentication is required on the declared privilege class, step-
    up cadence on sensitive operations). Emits per-session verdicts:
    `fresh` (within cadence), `overdue` (past the declared staleness
    threshold), or `policy_gap` (principal on the declared privilege
    class without a declared continuous-authentication policy —
    reported separately from stale sessions to preserve the atom-per-
    deviation shape). Anchored on OSCAL IA-2 alongside the coverage
    probe; anchored on D3FEND D3-AM as the adjacent dated examination
    of the same authentication surface. Binds against
    `content.playbooks.mfa_secured_comms.primitives.assess.assess_continuous_auth`.
    Emits `__session_assessment__`. Feeds `kri.mfa_coverage_gaps@v1`
    alongside the coverage snapshot. Read-only: no session is
    invalidated, no step-up is forced.

**verify OOB channels** (`…000004`)
:   Verification step. Dispatches a documented test transaction
    against each declared out-of-band emergency-communications
    channel enumerated in `__auth_scope__` (voice, secure messaging,
    paging, SMS, email). The transaction is clearly-labelled as a
    channel-readiness test — it does not deliver a real emergency
    notification, does not trigger incident response, and is not
    routed through the operator's live emergency-notification path.
    Records per-channel reachability status (`ready`, `unreachable`,
    `independence_failure`, `policy_gap`), the operator-supplied
    independence-path observation (the OOB channel transit must not
    share the primary information-system network path), and the
    last-tested timestamp. Anchored on OSCAL CP-8 (Telecommunications
    Services) — the alternate-telecommunications obligation the
    per-window channel-readiness record measures. Deliberately NOT
    pinned to a D3FEND technique (see mappings.yaml — D3FEND v1.0.0
    carries no defensive technique for OOB emergency-communications
    readiness verification distinct from the channel-delivery surface
    itself). Binds against
    `content.playbooks.mfa_secured_comms.primitives.verify.verify_oob_channel`.
    Emits `__oob_verification_id__`. Documented test transactions
    only — no real emergency notification, no channel mutation.

**evidence capture** (`…000005`)
:   Attestation step. Composes and publishes the dated authentication
    and secured-communications posture attestation to the operator's
    evidence store, carrying the MFA-coverage snapshot, the
    continuous-authentication verdict list, the OOB-channel status
    list, and the per-deviation Compliance Findings. Anchored on
    OSCAL IA-2 — the audit-evident record a reviewer reads against
    the declared authentication policy. Binds against
    `content.playbooks.mfa_secured_comms.primitives.artifact.build_mfa_posture_attestation_artifact`.
    The `artifact_id` derives from
    `SHA-256(workflow_id | execution_id | captured_at)` —
    `compile_target` is intentionally omitted from the id derivation
    so the three reference compilers re-derive byte-identical bytes
    from the same execution context (CORE-FANOUT byte-parity
    contract). Emits `__attestation_id__`. The playbook does not
    decide the evidence-store technology (object store, GRC platform,
    evidence lake); the operator binds the seam.

**notify authentication owner** (`…000006`)
:   Notification step. Delivers the attestation reference and the
    gap summary to the authentication owner along the operator's
    pre-bound channel (ticketing queue, chat channel, email alias,
    policy-owner mailbox). Read-only posture-readiness dispatch —
    the notification does not mutate enrolment state, session state,
    or channel configuration, and does not escalate the deviations
    into the incident-response lane; the authentication owner
    receives the summary and drives remediation off the operator's
    own cadence.

The five action steps are operator-bound runtime seams: the framework
ships neither the identity-provider surface, the session-management
surface, the OOB-channel test endpoints, the evidence store, nor the
authentication-owner notification channel. The playbook is the
portable description of *what* the operator's stack should do per
posture window; binding those seams to real endpoints is the
operator's job.

> **LM determinism.** MFA-coverage probing, continuous-authentication
> assessment, OOB-channel verification, attestation emission, and
> authentication-owner notification are structured reads and writes
> against operator-owned surfaces, not free-text reasoning steps. The
> playbook binds no DSPy signature — there is no LM-driven step at
> this layer. See [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM
> determinism. If an operator wires an LM-driven enrichment on top of
> the notify-authentication-owner step (rendering the per-deviation
> Compliance Finding stream into a per-owner narrative, for instance)
> as a private extension, the framework-wide EU-resident LM endpoint
> guard re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(j)** — multi-factor or continuous authentication,
secured voice/video/text communications, and secured emergency-
communications systems inside the entity where appropriate. NIS2
enforcement crossed on 2 July 2026; the authentication-and-secured-
communications obligation is among the audit-evident measures a
supervisory authority reads first when assessing the operator's
Art. 21 posture. The mfa_secured_comms playbook is the **per-window
materialisation of that obligation's measurement and attestation
surface**: the MFA-coverage probe, the continuous-authentication
assessment, the OOB-channel verification, and the dated posture-
attestation record are the audit-evident discharge of the clause.
Inbound anchor at
[`content/mappings/nis2/article-21-2-j.yaml`](../../content/mappings/nis2/article-21-2-j.yaml)
(`nis2:art-21-2-j`) backlinks `playbook.mfa_secured_comms@v1`, pins
`control.mfa_state_probe@v1` and `control.oob_channel_probe@v1`, and
pins `kri.mfa_coverage_gaps@v1` as the metric that trips on MFA-
coverage regressions.

**DORA Article 9(4)(b)** — strong authentication mechanisms.
Regulation (EU) 2022/2554 Art. 9(4)(b) requires financial entities to
implement policies and protocols for strong authentication mechanisms
based on relevant standards and dedicated controls systems, including
for privileged access and remote access, with the supporting
protective measures necessary to ensure the confidentiality,
integrity, and authenticity of the authentication surface and of the
secured-communications channels that operationalise it. The Level 2
detail in the Joint Committee RTS on ICT risk management framework
(Commission Delegated Regulation (EU) 2024/1774), Arts. 21–22 on
access management and authentication, prescribes the discipline the
operator must operate against. The per-window discharge shape here is
the same one NIS2 Art. 21(2)(j) anchors on — the MFA-coverage
snapshot, the continuous-authentication verdict list, the OOB-channel
status list, and the dated posture-attestation record. Inbound anchor
at
[`content/mappings/dora/article-9-4-b-authentication.yaml`](../../content/mappings/dora/article-9-4-b-authentication.yaml)
(`dora:art-9-authentication`). This is the authentication slice of
the broader Art. 9 protection-and-prevention surface; the vuln-
management, access-management, and crypto slices live on their
respective siblings (`dora:art-9-vuln-mgmt`, `dora:art-9-access-mgmt`,
`dora:art-9-crypto`) and are mapped separately to preserve the atom-
per-obligation shape.

**CRA Annex I §1(d)** — access control (authentication-enforcement and
secured-communications lane). Regulation (EU) 2024/2847 Annex I §1(d)
requires manufacturers of products with digital elements to design
and develop products with essential cybersecurity requirements
including access control by authentication, identity or access
management systems, appropriate to the intended purpose and to the
reasonably foreseeable risks. The mfa_secured_comms playbook is the
**authentication-enforcement and secured-communications lane** of
the Annex I §1(d) surface: per-window MFA-coverage probe, continuous-
authentication assessment, and out-of-band channel verification
against the declared policy. It sits as the fourth sibling under
§1(d) alongside `cra:annex-i-1-access-control` (unauthorised-access
response, operated by `playbook.identity_compromise@v1`),
`cra:annex-i-1-d-access-control-iam-auditor` (periodic access-
attestation, operated by `playbook.iam_auditor@v1`), and
`cra:annex-i-1-d-access-control-jml` (lifecycle grant/revoke,
operated by `playbook.onboarding_offboarding_tracker@v1`). Inbound
anchor at
[`content/mappings/cra/annex-i-1-d-access-control-mfa-coverage.yaml`](../../content/mappings/cra/annex-i-1-d-access-control-mfa-coverage.yaml)
(`cra:annex-i-1-d-access-control-mfa-coverage`).

**GDPR Article 30 Record of Processing Activity.** The per-workflow
Art. 30 ROPA at
[`content/mappings/gdpr/data-flow-mfa_secured_comms.md`](../../content/mappings/gdpr/data-flow-mfa_secured_comms.md)
covers the identity-provider surface read, the session-management
surface read, the OOB-channel test transaction, the attestation
emission, and the authentication-owner notification processing. The
personal-data surface is real: principal identifiers appear on the
MFA-coverage snapshot; per-principal enforcement state and per-
session staleness verdicts appear on the assessment; per-channel
reachability is aggregated to the channel-owner-role granularity
rather than the per-recipient level. Lawful basis: Art. 6(1)(f)
legitimate interests with Art. 6(1)(c) legal obligation as the
secondary basis where NIS2 Art. 21(2)(j) or DORA Art. 9(4)(b)
transposition applies. Retention runs against the operator's
declared retention policy on the posture-attestation record.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/mfa_secured_comms/mappings.yaml`](../../content/playbooks/mfa_secured_comms/mappings.yaml)):
IA-2 (Identification and Authentication (Organizational Users) —
anchors the probe-mfa-coverage, assess-continuous-auth, and
evidence-capture steps; IA-2(1) and IA-2(2) require MFA to privileged
and non-privileged accounts, which is the per-principal enforcement
state the coverage probe measures against the declared policy), and
CP-8 (Telecommunications Services — anchors the verify-oob-channels
step; the alternate-telecommunications obligation with priority-of-
service provisions is what the per-channel reachability and
independence-path record measures per window).

**MITRE D3FEND v1.0.0** — `D3-AM` (Account Monitoring) anchors the
probe-mfa-coverage and assess-continuous-auth steps as the dated
per-principal examination of authentication-surface state. The
`d3fend` closure documented in the mappings overlay records the per-
step gap rationale for the other three steps: verify-oob-channels is
a delivery-discipline health check rather than a detection or
countermeasure on the adversary surface (D3FEND v1.0.0 carries no
defensive technique for OOB emergency-communications readiness
verification distinct from the channel-delivery surface itself);
evidence-capture is an attestation-stream emission discipline rather
than a runtime countermeasure or detection step; notify-authentication-
owner is a delivery discipline rather than a defensive technique.
The probe and assess steps are deliberately anchored on the Detect-
tactic `D3-AM` rather than on the Harden-tactic `D3-MFA` (Multi-
factor Authentication), because the MFA technique itself is the
runtime enforcement discipline owned by the identity provider and
exercised under containment by the identity_compromise factor-reset
step; this playbook *measures whether that discipline is in force*, it
does not enforce it. This closure mirrors the gap-note precedent on
`cyber_hygiene_training`, `crypto_posture_management`,
`backup_recovery`, `infra_posture_management`, `iam_auditor`, and
`on_call_rotation`.

**OCSF v1.3.0** — two class bindings.
`API Activity` (class_uid 6003, category Application Activity),
direction `both`, is consumed at the probe-mfa-coverage step (read
calls against the identity-provider surface), the assess-continuous-
auth step (read calls against the session-management surface), and
the verify-oob-channels step (test transactions against the OOB
channel endpoints — modelled as read-only API activity); emitted at
the evidence-capture step (write call publishing the dated posture-
attestation record to the operator's evidence store) and the notify-
authentication-owner step (delivery dispatch to the authentication
owner's pre-bound channel). The API Activity records carry the
request metadata `kri.mfa_coverage_gaps@v1` reads.
`Compliance Finding` (class_uid 2003, category Findings), direction
`emits`, is emitted by the probe-mfa-coverage, assess-continuous-
auth, and verify-oob-channels steps as the structured per-principal
and per-channel deviation record the posture-management layer routes
to the authentication owner and the SIEM queries against — one
Compliance Finding per deviation (principal missing required factor
on the declared privilege class, principal whose enforcement state
is below the declared coverage policy, session past the declared
continuous-authentication staleness threshold, principal on the
declared privilege class without a declared continuous-authentication
policy, OOB channel that failed the reachability probe, OOB channel
whose independence-path verification failed).

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the posture-probe topology

`examples/n8n/mfa_secured_comms/workflow.n8n.json` carries the CACAO
topology as seven n8n nodes (`manualTrigger`, five `set` nodes, one
`noOp` terminal), with node ids preserving the CACAO step ids
verbatim. The five action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles (control, telemetry). The linear
sequencing carries via `on_completion` edges on the emitted
`connections` block. The lossy translations are recorded in
`meta.secops_ng_notes` so the integrator sees exactly which seams
need attention.

Operators bind the Set rows to their connectors:

- `probe MFA coverage` → the operator's identity-provider surface
  (Entra ID / Azure AD, Okta, Ping, Keycloak, an in-house IdP, or an
  IAM aggregator) exposing per-principal enrolled-factor and
  enforcement-state reads; writes `__mfa_coverage_id__`.
- `assess continuous auth` → the operator's session-management
  surface (the IdP's session API, a session broker, or a zero-trust
  proxy that carries the observed re-authentication events) exposing
  per-session age and last-re-authentication reads; writes
  `__session_assessment__`.
- `verify OOB channels` → the operator's out-of-band emergency-
  communications channel endpoints (voice-conferencing test line,
  secure-messaging channel, paging service, SMS test recipient,
  email test alias), configured as documented test transactions;
  writes `__oob_verification_id__`.
- `evidence capture` → the operator's evidence store (object store,
  GRC platform, evidence lake, or a policy-as-code artifact store);
  writes `__attestation_id__`.
- `notify authentication owner` → the operator's authentication-
  owner channel (a ticketing queue, a chat channel, an email alias,
  or a policy-owner mailbox).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/mfa_secured_comms/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/mfa_secured_comms/workflow.n8n.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies

`examples/temporal/mfa_secured_comms/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the five action
activities documenting their operator-bound seam (probe / assess /
verify / attest / notify). Each activity delegates the deterministic
canonicalisation and validation to the shared primitive under
`content/playbooks/mfa_secured_comms/primitives/`; the operator wires
the surrounding data-plane call (identity-provider read, session-
management read, OOB test transaction, evidence-store write,
notification dispatch) inside the activity body.

Temporal is a natural fit for the posture-probe discipline: each
declared posture window becomes one workflow run; retries against
transient failures on the identity-provider surface, the session-
management surface, the OOB test endpoints, or the evidence store
get first-class Temporal semantics (activity retry policy per seam);
replay against the same Temporal event history re-derives the same
MFA-coverage snapshot, the same continuous-authentication verdict
list, the same OOB-channel status list, and the same posture-
attestation record because the primitives are pure. Schedules
(Temporal `Schedule`) give the operator a durable per-window trigger
without a bespoke cron surface.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/mfa_secured_comms/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes and the
linear on-completion edges from probe-mfa-coverage through notify-
authentication-owner to the terminal end); `assemble.py` is the
hand-written reference assembly that wires the GraphSpec + bindings
into a `langgraph.graph.StateGraph`. Each tool wrapper delegates to
the same primitive layer the Temporal and n8n targets bind against.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven enrichment on top of the `notify authentication owner`
step (rendering the per-principal missing-MFA / stale-session
Compliance Finding stream into a per-owner narrative, for instance)
fills that as a private extension. The framework-wide EU-resident LM
endpoint guard re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/mfa_secured_comms/`,
`examples/temporal/mfa_secured_comms/`,
`examples/langgraph/mfa_secured_comms/`). Each ships a committed
emitter artifact (n8n workflow JSON, Temporal worker module,
LangGraph GraphSpec + bindings) with the action bodies delegating to
the shared primitive layer under
`content/playbooks/mfa_secured_comms/primitives/`. Cross-target byte-
parity goldens live under
`tests/examples/{n8n,temporal,langgraph}/mfa_secured_comms/`. The
`artifact_id` derivation
`SHA-256(workflow_id | execution_id | captured_at)` deliberately
omits `compile_target`, so a replay against the same execution
context produces the same attestation bytes on n8n / Temporal /
LangGraph — the CORE-FANOUT byte-parity contract.

## 6. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the operator-
bound seam call or the primitive body. The mirror runs
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
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity
  body, with retries opening a fresh child span per Temporal
  attempt.
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

## 7. Metrics — what the posture-probe discipline exposes

The mfa-coverage-gaps KRI is the catalogue entry this playbook feeds.

- **`kri.mfa_coverage_gaps@v1`** — per-window count of principals
  whose MFA-coverage or continuous-authentication verdict falls
  below the declared policy, plus per-window count of OOB channels
  whose reachability or independence-path verdict fails. Stamped by
  the probe-mfa-coverage, assess-continuous-auth, and verify-oob-
  channels steps. Rising values indicate the authentication and
  secured-communications posture is drifting behind the declared
  policy; each deviation is captured as a Compliance Finding on the
  emit side.

The catalogue entry pins the field-level read contract; the framework
does not ship a hosted dashboard. Operators dashboard the KRI series
against their own metrics backend. The `EXTEND-METRICS` sibling card
lands the session-staleness KPI and OOB-reachability KPI emitters
against the operator's evidence store as the two per-window
observation series a reviewer reads alongside the gap-count KRI.

## 8. Detection references — the upstream signal shapes

The playbook does not re-author detection rules. The Compliance
Finding stream emitted by the probe-mfa-coverage, assess-continuous-
auth, and verify-oob-channels steps is the **upstream of any Sigma
rule** a downstream consumer chooses to author against missing-MFA /
stale-session / unreachable-OOB / independence-path-failure
deviations. Rule fingerprints are the operator's posture-management-
layer concern; SecOps-NG does not pin stable Sigma rule ids on this
overlay.

The rule shapes an operator typically authors against the finding
stream:

- **Principal missing required factor on the declared privilege
  class** — a Compliance Finding with the coverage-probe key and the
  missing-factor branch; the fingerprint is stable per
  (`__mfa_coverage_id__`, principal-id, factor-class).
- **Principal whose enforcement state is below the declared coverage
  policy** — a Compliance Finding with the coverage-probe key and
  the enforcement-below-policy branch; the fingerprint is stable
  per (`__mfa_coverage_id__`, principal-id).
- **Session past the declared continuous-authentication staleness
  threshold** — a Compliance Finding stamped at the assess-
  continuous-auth step with the overdue verdict; the fingerprint is
  stable per (`__mfa_coverage_id__`, session-id).
- **Principal on the declared privilege class without a declared
  continuous-authentication policy** — the policy-gap branch,
  reported separately from stale sessions; the fingerprint is stable
  per (`__mfa_coverage_id__`, principal-id) and preserves the atom-
  per-deviation shape.
- **OOB channel that failed the reachability probe** — a Compliance
  Finding stamped at the verify-oob-channels step with the
  unreachable branch; the fingerprint is stable per
  (`__oob_verification_id__`, channel-id).
- **OOB channel whose independence-path verification failed** — the
  same channel granularity, keyed on the independence-path-failure
  branch of the same channel-readiness record.

## 9. Operator customisation points

The playbook is a per-window authentication-posture machine; the
*policy* it exercises is the operator's. The customisation seams:

- **Authentication scope binding.** The `__auth_scope__` workflow-
  scope variable declares the identity providers, session
  surfaces, and OOB channel endpoints in scope for the window, plus
  the principal-class privilege ladder the coverage and continuous-
  authentication policies key on. The framework binds no scope; the
  operator's IAM topology and their authentication policy decide the
  perimeter.
- **Coverage-policy targets.** The declared factor-class requirement
  per principal-class (WebAuthn on privileged accounts, TOTP-or-
  WebAuthn on service accounts, and so on) is the operator's policy
  choice, bounded by the regulatory floor NIS2 Art. 21(2)(j),
  DORA Art. 9(4)(b), and CRA Annex I §1(d) impose. The probe
  measures whatever the operator declares.
- **Continuous-authentication cadence.** The declared maximum session
  age before re-authentication is required, and the step-up cadence
  on sensitive operations, are the operator's numbers. The verdict
  list trips against those thresholds; the framework never hard-
  codes a target.
- **OOB channel binding and test cadence.** The declared out-of-
  band channels (which voice line, which secure-messaging channel,
  which paging service), the independence-path assertion the
  operator vouches for, and the per-window test cadence are the
  operator's choices against the CP-8 alternate-telecommunications
  obligation. The framework binds the seam (a documented test
  transaction against a channel endpoint) but not the channel.
- **Authentication-owner routing.** The channel the `notify
  authentication owner` step dispatches on (ticketing queue, chat
  channel, email alias, policy-owner mailbox) is the operator's
  decision. The framework binds the notification seam but not the
  channel.

## 10. Replay and audit story

The byte-parity drift guards under
`tests/examples/{n8n,temporal,langgraph}/mfa_secured_comms/` each pin
the committed worked-example artifact to a fresh emitter run from
the canonical CACAO source; if the compiler or the playbook changes,
regenerate via the per-target `regenerate.sh` and commit the diff
intentionally.

The cross-target replay property is the harder one: the same
identity-provider observation set, session-management observation
set, and OOB-channel observation set, fed through n8n / Temporal /
LangGraph, produce byte-identical MFA-coverage snapshots, verdict
lists, channel status lists, Compliance Finding records, *and* byte-
identical posture-attestation records — because the primitive layer
under `content/playbooks/mfa_secured_comms/primitives/` is pure and
the `artifact_id` derivation deliberately omits `compile_target`.
The
`(__mfa_coverage_id__, __session_assessment__, __oob_verification_id__,
 __attestation_id__)` tuple is the string an operator can diff to
confirm the property holds across targets.

## 11. Playbook chain — where mfa_secured_comms sits

The authentication and secured-communications chain expresses itself
as one proactive per-window posture probe that sits alongside the
reactive identity-compromise lane and the periodic access-attestation
and lifecycle grant/revoke siblings under CRA Annex I §1(d):

```
mfa_secured_comms  (proactive, per-window posture-probe)
    └── attestation ─► operator's evidence store
    └── notify authentication owner ─► posture-readiness dispatch
    └── Compliance Finding stream ─► operator's posture-management layer

identity_compromise (reactive, on suspected credential-theft / MFA-bypass)
    └── triage identity signal ─► reset MFA factors ─► revoke sessions
        ─► notify affected principals
```

- **Sibling: `identity_compromise`.** Under the same CRA Annex I
  §1(d) surface. The mfa_secured_comms playbook operates the per-
  window measurement of MFA-coverage, continuous-authentication, and
  OOB-readiness discipline; the identity_compromise playbook handles
  suspected credential-theft or MFA-bypass events in progress. The
  two are complementary, not duplicative — one is proactive and read-
  only, the other reactive and mutating. See
  [`docs/cookbook/identity_compromise.md`](./identity_compromise.md).
- **Sibling: `iam_auditor`.** Third sibling under CRA Annex I §1(d).
  The iam_auditor playbook operates the periodic access-attestation
  discipline (which principals hold which entitlements against the
  declared authorisation policy); mfa_secured_comms operates the
  authentication-enforcement half of the access-control surface. The
  two overlap on the OSCAL AT-2-adjacent audit-evidence discipline
  but discharge different atoms under §1(d). See
  [`docs/cookbook/iam_auditor.md`](./iam_auditor.md).
- **Sibling: `onboarding_offboarding_tracker`.** Fourth sibling under
  CRA Annex I §1(d). The JML tracker operates the lifecycle grant /
  revoke discipline against the declared joiner / mover / leaver
  policy; mfa_secured_comms operates the authentication-enforcement
  lane on the same principal set. See
  [`docs/cookbook/onboarding_offboarding_tracker.md`](./onboarding_offboarding_tracker.md).
- **Adjacent: `crypto_posture_management`.** DORA Art. 9 companion —
  the confidentiality-and-integrity slice
  (`dora:art-9-crypto`) is operated by `crypto_posture_management`;
  mfa_secured_comms operates the authentication slice
  (`dora:art-9-authentication`). Both are per-window read-only
  posture-probes that emit a dated attestation and per-deviation
  Compliance Findings; the two slices discharge independent
  operational disciplines and are mapped separately to preserve the
  atom-per-obligation shape.

The chain lets mfa_secured_comms stay narrowly focused on the per-
window authentication-and-secured-communications measurement
discipline while identity_compromise handles live suspected
compromise, iam_auditor handles the periodic entitlement attestation,
and onboarding_offboarding_tracker handles the lifecycle grant /
revoke surface. The chain is not code-coupled — each playbook is a
standalone CACAO artifact that can be run in isolation — but the
audit trail's coherence across the workflows is the sovereign-
security property the framework guarantees.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  identity-provider surface, the session-management surface, the OOB
  channel endpoints, the evidence store, or the authentication-owner
  channel. Connectors are operator-bound at runtime against
  environment variables documented per target.
- **Policy authorship.** The playbook operates the per-window
  measurement discipline; it does not author the coverage policy,
  the continuous-authentication cadence, or the OOB channel binding.
  Authorship is the operator's governance concern.
- **MFA enrolment or factor reset.** The playbook is read-only-by-
  contract: no factor is registered, no factor is revoked, no
  re-enrolment is forced. The reactive MFA-reset discipline is
  operated by `playbook.identity_compromise@v1` under containment on
  a confirmed compromise.
- **Session invalidation or forced re-authentication.** The
  continuous-authentication assessment records overdue sessions; it
  does not terminate them. Session revocation under containment is
  operated by `playbook.identity_compromise@v1`.
- **Real emergency notification.** The OOB channel verification is a
  documented test transaction and never delivers a real emergency
  notification. When a real emergency requires the OOB channel,
  that dispatch lives on the operator's incident-response lane, not
  on this playbook.
- **Sigma rule ids.** The Compliance Finding stream is the upstream
  of any missing-MFA / stale-session / unreachable-OOB / independence-
  path-failure rule the operator's posture-management layer chooses
  to author; SecOps-NG does not pin stable Sigma rule ids on this
  overlay.

## 13. References

- [`content/playbooks/mfa_secured_comms/README.md`](../../content/playbooks/mfa_secured_comms/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/mfa_secured_comms/mappings.yaml`](../../content/playbooks/mfa_secured_comms/mappings.yaml)
  — outbound OSCAL / OCSF / D3FEND / NIS2 / DORA / CRA overlay with
  per-step control anchors.
- [`content/playbooks/mfa_secured_comms/primitives/`](../../content/playbooks/mfa_secured_comms/primitives/)
  — pure canonicalisation / validation / sort layer the three
  reference compilers bind against (probe / assess / verify /
  artifact).
- [`content/mappings/nis2/article-21-2-j.yaml`](../../content/mappings/nis2/article-21-2-j.yaml)
  — NIS2 Article 21(2)(j) inbound anchor (multi-factor or continuous
  authentication and secured emergency communications).
- [`content/mappings/dora/article-9-4-b-authentication.yaml`](../../content/mappings/dora/article-9-4-b-authentication.yaml)
  — DORA Article 9(4)(b) inbound anchor (strong authentication
  mechanisms; JC RTS on ICT risk management framework, Arts. 21–22).
- [`content/mappings/cra/annex-i-1-d-access-control-mfa-coverage.yaml`](../../content/mappings/cra/annex-i-1-d-access-control-mfa-coverage.yaml)
  — CRA Annex I §1(d) inbound anchor (authentication-enforcement and
  secured-communications lane).
- [`content/mappings/gdpr/data-flow-mfa_secured_comms.md`](../../content/mappings/gdpr/data-flow-mfa_secured_comms.md)
  — GDPR Article 30 Record of Processing Activity.
- [`examples/n8n/mfa_secured_comms/README.md`](../../examples/n8n/mfa_secured_comms/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/mfa_secured_comms/README.md`](../../examples/temporal/mfa_secured_comms/README.md)
  — Temporal worked-example walkthrough.
- [`examples/langgraph/mfa_secured_comms/README.md`](../../examples/langgraph/mfa_secured_comms/README.md)
  — LangGraph worked-example walkthrough.
- [`docs/cookbook/identity_compromise.md`](./identity_compromise.md)
  — sibling cookbook under CRA Annex I §1(d) (reactive credential-
  theft / MFA-bypass handling).
- [`docs/cookbook/iam_auditor.md`](./iam_auditor.md)
  — sibling cookbook under CRA Annex I §1(d) (periodic access-
  attestation).
- [`docs/cookbook/onboarding_offboarding_tracker.md`](./onboarding_offboarding_tracker.md)
  — sibling cookbook under CRA Annex I §1(d) (lifecycle grant/revoke).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
