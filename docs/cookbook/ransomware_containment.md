# ransomware_containment — cookbook walkthrough

Ransomware-containment response workflow under NIS2 Article 21(2)(b),
NIS2 Article 23, DORA Article 18, DORA Article 19, CRA Annex I §1(h),
CRA Article 14(3), and GDPR Article 30 Record of Processing Activity.
The `playbook.ransomware_containment@v1` CACAO playbook ingests a
ransomware signal (shadow-copy deletion via vssadmin / WMI /
PowerShell, Windows Backup deletion via wbadmin, mass file-rename or
mass file-encrypt activity, overpass-the-hash) delivered by the
operator's malicious-code-protection or EDR layer, hydrates it with
host and principal context, decides whether the event is confirmed,
and — when it is — drives containment through endpoint isolation
(EDR quarantine primary, network-ACL fallback), identity revocation
on the implicated principal, backup-integrity verification against
the most recent known-good snapshot, and a comms-plan step that
pages the IR lead and drafts the NIS2 Article 23 24-hour early
warning within the statutory clock.

The playbook is the **operational anchor** for the ransomware case
set: the endpoint-isolation / identity-revocation / backup-
verification chain runs entirely on this workflow, and the
significance-threshold verdict — impact on essential services,
lateral-movement risk, encrypted-file-scope indicator, financial-
entity classification — is computed off the evidence this playbook
produces. The regulator-submission timeline itself is handed off to
`playbook.incident_management@v1`, and the post-event
lessons-learned / root-cause discipline runs on
`playbook.post_incident_review@v1`:

```
ransomware_containment ─► incident_management
                       └► post_incident_review
```

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the triage, the
confirmed-branch gate, the EDR-available gate, the endpoint
isolation, the identity revocation, the backup verification, and the
comms-plan land in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/ransomware_containment/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.ransomware_containment@v1)

content/mappings/nis2/article-21-2-b.yaml
                                  # NIS2 Art. 21(2)(b) inbound anchor —
                                  # incident-handling capability;
                                  # backlinks playbook.ransomware_containment@v1
                                  # as the operational discharge of
                                  # detect-through-contain-through-notify
                                  # for the ransomware case set
content/mappings/nis2/article-23.yaml
                                  # NIS2 Art. 23 inbound anchor —
                                  # 24-hour early warning and 72-hour
                                  # notification, backlinking to
                                  # playbook.ransomware_containment@v1
                                  # as the upstream signal source that
                                  # feeds the regulator-submission engine
content/mappings/dora/article-19-and-28.yaml
                                  # DORA Art. 18 major-classification
                                  # and Art. 19 initial-4h / intermediate-
                                  # 72h notification, backlinking to
                                  # playbook.ransomware_containment@v1 for
                                  # the financial-sector regulator-
                                  # notification chain
content/mappings/cra/annex-i-1-essential-cybersecurity.yaml
                                  # CRA Annex I §1(h) availability-after-
                                  # incident anchor — the backup-
                                  # verification step is the operational
                                  # evidence that a known-good restore
                                  # option remains exercisable
content/mappings/cra/article-14-and-annex-i.yaml
                                  # CRA Art. 14(3) severe-incident
                                  # notification anchor — 24h/72h/1-month
                                  # timing chain for the product-side
                                  # severe-incident regulator submissions
content/mappings/gdpr/data-flow-ransomware_containment.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity for the host-isolation and
                                  # identity-revocation processing on
                                  # the affected device user / principal
                                  # this playbook operates on
```

The CACAO source is canonical. The six action steps, two
`if-condition` nodes, and one `start` / two `end` wiring nodes are
the deterministic policy the playbook *means* — a triage step
feeding a confirmed-branch gate that either short-circuits to a
false-positive end or fans through an EDR-available gate into
endpoint isolation (EDR primary or network-ACL fallback), then
linearly through identity revocation, backup verification, and the
comms-plan step to the containment-complete end. The three worked
examples under `examples/{n8n,temporal,langgraph}/ransomware_containment/`
are the same playbook compiled into three orchestrator idioms.
Everything else — the EDR the isolation step calls, the network
chokepoint the fallback rule lands on, the IdP the revocation step
disables the principal at, the backup catalogue the verification
step reads, and the paging / regulator channel the comms-plan step
drafts into — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships ten steps: one `start`, six `action`, two
`if-condition`, and two `end` (the terminal end and a distinct
false-positive end so the false-verdict branch is audit-evident).
The first `if-condition` fires on `__ransomware_confirmed__`;
`on_success` routes into the EDR-available gate; `on_failure`
short-circuits to the terminal end (no false-positive marker is
carried today — the false close-out is logged for the false-positive
KPI by an out-of-scope card on the operator's ticketing surface).
The second `if-condition` fires on `__edr_available__`; `on_success`
routes into the EDR isolate action; `on_failure` routes into the
network-ACL deny fallback. Both isolation branches converge on the
identity-revocation step and then linearly through backup
verification into the comms-plan step. Downstream regulator /
customer notification is not on this playbook — the significance-
threshold gate and the per-stage submissions run on
`playbook.incident_management@v1` from the evidence this playbook
emits (see § 4 and § 11).

| Step suffix | Step                                                | Discipline                                                                                                                                                                                                                                | Status         |
|-------------|-----------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | ransomware-start                                    | edge wiring only — no body                                                                                                                                                                                                                | n/a            |
| `…000002`   | triage signal                                       | hydrate the originating ransomware signal (shadow-copy deletion, wbadmin backup deletion, mass file-rename / encrypt, overpass-the-hash) with host and principal context; decides `__ransomware_confirmed__` and `__edr_available__`      | operator-bound |
| `…000003`   | ransomware confirmed?                               | `if-condition` — branches on `__ransomware_confirmed__` (true → EDR-available gate, false → terminal end / false-positive close-out)                                                                                                       | n/a            |
| `…000004`   | EDR available?                                      | `if-condition` — branches on `__edr_available__` (true → EDR isolate, false → network-ACL deny fallback); both branches converge on identity revocation                                                                                    | n/a            |
| `…000005`   | endpoint isolation — EDR isolate                    | issue the EDR-vendor isolate action against the affected host so encryption activity stops and lateral / C2 paths are cut off; primary path                                                                                                | operator-bound |
| `…000006`   | endpoint isolation — network ACL deny (fallback)    | fallback path: deny all ingress / egress for the affected host at the operator's network chokepoint (firewall rule, switchport disable, or SDN policy) when the EDR agent is unreachable                                                   | operator-bound |
| `…000007`   | identity revocation                                 | disable the implicated principal at the IdP, revoke active sessions and refresh / access tokens, invalidate the Kerberos TGT where supported, so the attacker cannot pivot off the compromised host through cached credentials             | operator-bound |
| `…000008`   | backup verification                                 | locate the most recent known-good backup snapshot that pre-dates the event window and verify its integrity hash against the backup-catalogue record; produces the `__latest_known_good_snapshot__` and `__snapshot_integrity_ok__` handles | operator-bound |
| `…000009`   | comms plan                                          | page the IR lead and comms officer along the operator's pre-bound channels and draft the NIS2 Art. 23 24-hour early-warning pre-notification (staged for human sign-off, not auto-sent)                                                    | operator-bound |
| `…00000a`   | ransomware-end                                      | edge wiring only — no body (containment complete or false close-out)                                                                                                                                                                       | n/a            |

All six action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (detection, control,
telemetry, metric). One execution short-circuits to the terminal end
when triage does not confirm the event, or runs the linear five-step
containment chain (isolate → revoke → verify → notify) exactly once.
Per-case metric accounting into the MTTD / MTTC / backup-integrity /
notification-SLA / timeline-completeness catalogue entries is
unambiguous.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The overlay pins the control, detection, telemetry,
> and metric surface; the n8n reference emitter ships a committed
> `workflow.n8n.json` today, and the Temporal / LangGraph siblings
> ship deterministic emitter output with `NotImplementedError`
> activity / tool bodies pending the per-target CORE cards.
> Cross-target byte-parity goldens live under
> `tests/examples/ransomware_containment/`.

## 3. Lifecycle contract — the six action states

The per-case payload — host identifier, principal identifier,
process-creation chain around the encryption window, file-system
activity, sign-in metadata for the implicated principal, and the
located backup-snapshot identifier plus its integrity verdict — is
incident-handling content that carries personal data of natural
persons (the device user's principal identifier and the recent-
sign-in metadata the triage step reads). The inbound GDPR Art. 30
Record of Processing Activity at
[`content/mappings/gdpr/data-flow-ransomware_containment.md`](../../content/mappings/gdpr/data-flow-ransomware_containment.md)
covers the host-isolation and identity-revocation processing the six
steps below operate on, lawful-basis-grounded in GDPR Art. 6(1)(f)
legitimate interests with Art. 6(1)(c) legal obligation as the
secondary basis where NIS2 Art. 21(2)(b) transposition applies. The
framework treats the principal identifier as an IdP-scoped opaque
identifier under the operator's own naming convention and does not
re-derive subject identifiers outside the operator's own identity
surface.

**triage signal** (`…000002`)
:   Hydration step. Reads the operator's malicious-code-protection
    / EDR layer for the originating signal against the affected
    host, joins it with process-creation context, file-system
    activity around the encryption window, and recent sign-in
    metadata for the host's logged-on principal; decides
    `__ransomware_confirmed__` and `__edr_available__`. Anchored on
    MITRE D3FEND v1.0.0 `D3-FA` (File Analysis) — the file-system
    artefact analysis leg — and `D3-PSA` (Process Spawn Analysis) —
    the process-creation chain leg. Anchored on OSCAL SI-3
    (Malicious Code Protection) as the originating-signal surface
    and AU-6 (Audit Record Review, Analysis, and Reporting) as the
    correlation surface. Consumes OCSF **Detection Finding** (class
    2004), **Process Activity** (class 1007), **File System
    Activity** (class 1001), and **Authentication** (class 3002).
    Feeds `kpi.mttd_ransomware@v1`.

**ransomware confirmed?** (`…000003`, `if-condition`)
:   Deterministic branch on `__ransomware_confirmed__`. `on_success`
    (confirmed) routes into the EDR-available gate; `on_failure`
    (false positive) routes to the terminal end. Anchored on OSCAL
    IR-4 (Incident Handling).

**EDR available?** (`…000004`, `if-condition`)
:   Deterministic branch on `__edr_available__`. `on_success` (EDR
    reachable) routes to the EDR isolate action; `on_failure` (EDR
    unreachable or absent) routes to the network-ACL deny fallback.
    Both branches converge on identity revocation. Anchored on
    OSCAL IR-4 (Incident Handling).

**endpoint isolation — EDR isolate** (`…000005`)
:   Primary containment step. Issues the EDR-vendor isolate action
    against the affected host via the operator's pre-bound EDR
    agent, bounded by the operator-supplied authorisation policy so
    the isolate call carries the audit trail the operator's
    change-management surface expects. Anchored on MITRE D3FEND
    v1.0.0 `D3-NI` (Network Isolation) and OSCAL SI-3 (Malicious
    Code Protection) with IR-4 (Incident Handling) end-to-end.
    Stamps `kpi.mttr_containment@v1`.

**endpoint isolation — network ACL deny (fallback)** (`…000006`)
:   Fallback containment step. Denies all ingress / egress for the
    affected host at the operator's network chokepoint (firewall
    rule, switchport disable, SDN policy) when the EDR agent is
    unreachable. Anchored on MITRE D3FEND v1.0.0 `D3-NTF` (Network
    Traffic Filtering) and OSCAL SC-7 (Boundary Protection). Stamps
    `kpi.mttr_containment@v1`. The fallback keeps the containment
    cut-out exercisable when the EDR path is unavailable — a
    property NIS2 Art. 21(2)(b) and DORA Art. 18/19 both read
    against under the "capacity to respond" clauses.

**identity revocation** (`…000007`)
:   Identity-side containment step. Disables the implicated
    principal at the IdP, revokes active sessions and refresh /
    access tokens, and invalidates the Kerberos TGT where supported
    so the attacker cannot pivot off the compromised host through
    the principal's cached credentials. Anchored on MITRE D3FEND
    v1.0.0 `D3-ACI` (Authentication Cache Invalidation) and `D3-AL`
    (Account Locking) and OSCAL AC-2(13) (Account Management |
    Disable Accounts for High-Risk Individuals) — the operational
    analogue of disabling a high-risk account for the duration of
    the containment window. Emits OCSF **Account Change** (class
    3001) per containment action so the timeline-signal controls
    can audit on-time containment. Note that this is the *local
    cut-out* on the principal implicated by the ransomware event;
    the deeper IdP-side blast-radius audit — rogue OAuth consents,
    conditional-access exceptions, third-party app grants, lingering
    role assumptions — lives on `playbook.identity_compromise@v1`.

**backup verification** (`…000008`)
:   Recovery-option-preservation step. Locates the most recent
    known-good snapshot that pre-dates the event window on the
    operator's offline / immutable backup tier and verifies its
    integrity hash against the backup-catalogue record; produces
    `__latest_known_good_snapshot__` and `__snapshot_integrity_ok__`.
    Anchored on MITRE D3FEND v1.0.0 `D3-FH` (File Hashing) and
    `D3-EHB` (Encrypted Host-storage Backup) and OSCAL CP-9 (System
    Backup) reinforced by CP-10 (System Recovery and
    Reconstitution). This step does **not** restore — restore is a
    separate, out-of-scope recovery playbook. The property it
    proves is that the recovery option remains exercisable without
    paying the ransom, which is the CRA Annex I §1(h)
    availability-after-incident evidence. Feeds
    `kpi.backup_integrity_pass_rate@v1`.

**comms plan** (`…000009`)
:   Handoff step. Pages the IR lead and the comms officer along the
    operator's pre-bound channels and drafts the NIS2 Art. 23
    24-hour early-warning pre-notification (staged for human
    sign-off, not auto-sent). Anchored on OSCAL IR-6 (Incident
    Reporting). Stamps `kpi.notification_sla_compliance@v1`,
    `kpi.timeline_completeness@v1`, and
    `kri.regulator_notification_overrun@v1`. The comms-plan step is
    the handoff point that closes the containment timeline and
    trips the statutory reporting clocks onto
    `playbook.incident_management@v1`.

The six action steps are operator-bound runtime seams: the framework
ships neither the EDR agent, the network chokepoint API, the IdP,
the backup catalogue, nor the paging / regulator channel. The
playbook is the portable description of *what* the operator's stack
should do per case; binding those seams to real endpoints is the
operator's job.

> **LM determinism.** Triage, endpoint isolation, identity
> revocation, backup verification, and the comms-plan draft are
> structured reads and writes against operator-owned surfaces, not
> free-text reasoning steps. The playbook binds no DSPy signature —
> there is no LM-driven step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven classifier on top of the triage step
> (a private, forward-looking extension) or an LM-driven summariser
> into the comms-plan draft, the framework-wide EU-resident LM
> endpoint guard re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
> Free-text narrative fields on the downstream regulator submissions
> are handled by `playbook.incident_management@v1` under its own
> DSPy signature schema.

## 4. Regulatory anchors

**NIS2 Article 21(2)(b)** — incident-handling capability. The
clause requires essential and important entities to operate an
incident-handling capability (detect, triage, contain, remediate,
capture lessons learned). The ransomware_containment playbook is
the **operational discharge of detect-through-contain-through-notify
for the ransomware case set**; the regulator-notification tail is
handed off to `playbook.incident_management@v1` and the
lessons-learned tail runs on `playbook.post_incident_review@v1`.
Inbound anchor at
[`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
(`nis2:art-21-2-b`) backlinks `playbook.ransomware_containment@v1`.

**NIS2 Article 23** — incident-reporting obligations. Article
23(4)(a) requires a 24-hour early warning and Article 23(4)(b)
requires a 72-hour notification with an initial assessment of
severity and impact. The ransomware_containment playbook is an
**upstream signal source** into the regulator-submission engine:
the endpoint-isolation, identity-revocation, and backup-verification
artefacts feed the severity / impact / indicators-of-compromise
sections of the assessment that `playbook.incident_management@v1`
emits on the 24-hour and 72-hour legs. The comms-plan step drafts
the 24-hour early warning within-clock and hands off; the 72-hour
notification and the one-month final report are downstream. Inbound
anchors at
[`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
(`nis2:art-23-early-warning`, `nis2:art-23-notification-72h`).

**DORA Article 18(1)** — classification. Requires classification
of ICT-related incidents against the criteria in the JC RTS on
incident classification (Commission Delegated Regulation (EU)
2024/1772). The ransomware_containment playbook's triage,
endpoint-isolation, identity-revocation, and backup-verification
outputs produce the host-blast-radius, encryption-scope, and
recovery-option evidence that drives the major-classification
verdict on the downstream `playbook.incident_management@v1` engine.
Inbound anchor at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-18-classification`).

**DORA Article 19** — reporting of major ICT-related incidents.
Article 19(4)(a) requires an initial notification within 4 hours of
major-classification and Article 19(4)(b) requires an intermediate
notification within 72 hours with updated assessment. The
ransomware_containment playbook's isolation and identity-revocation
artefacts anchor the initial notification payload; the backup-
verification result and any lateral-movement closure feed the
updated assessment for the intermediate report on the downstream
`playbook.incident_management@v1` engine. Inbound anchors at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-19-initial-4h`, `dora:art-19-intermediate-72h`).

**CRA Annex I §1(h)** — availability after incident. Requires
manufacturers to design products so that availability can be
restored after an incident, backed by backup-attestation and
restore-drill evidence. The ransomware_containment playbook's
backup-verification step is the **operational evidence that the
recovery option remains exercisable** — the located snapshot's
integrity hash checked against the catalogue record is the trail an
assessor reads against the §1(h) availability requirement. Inbound
anchor at
[`content/mappings/cra/annex-i-1-essential-cybersecurity.yaml`](../../content/mappings/cra/annex-i-1-essential-cybersecurity.yaml)
(`cra:annex-i-1-availability`).

**CRA Article 14(3)** — severe-incident notification. Requires
manufacturers to notify a severe incident having an impact on the
security of the product to ENISA and the CSIRT designated as
coordinator in a 24-hour / 72-hour / one-month chain. Ransomware on
an in-market product crosses this threshold on essentially any
positive triage outcome; the ransomware_containment playbook is the
upstream signal source that feeds the notification chain, and the
per-stage submissions themselves land on
`playbook.incident_management@v1`. Inbound anchor at
[`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
(`cra:art-14-severe-incident`).

**GDPR Article 30 Record of Processing Activity.** The per-workflow
Art. 30 ROPA at
[`content/mappings/gdpr/data-flow-ransomware_containment.md`](../../content/mappings/gdpr/data-flow-ransomware_containment.md)
covers the host-isolation and identity-revocation processing on the
affected device user / principal that this playbook operates on.
Lawful basis: Art. 6(1)(f) legitimate interests with Art. 6(1)(c)
legal obligation as the secondary basis where NIS2 Art. 21(2)(b)
transposition applies. Where the ransomware event's blast radius
crosses into personal-data exposure, the GDPR Art. 33 / 34
notification chain runs jointly with the NIS2 Art. 23 and DORA Art.
19 lanes on `playbook.incident_management@v1` — the closure lives
on the downstream engine, not on this playbook.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/ransomware_containment/mappings.yaml`](../../content/playbooks/ransomware_containment/mappings.yaml)):
IR-4 (Incident Handling — anchors the playbook end-to-end),
IR-6 (Incident Reporting — anchors the comms-plan handoff into the
downstream regulator-submission engine),
SI-3 (Malicious Code Protection — anchors the triage step's
originating-signal surface),
SC-7 (Boundary Protection — anchors the network-ACL fallback
containment leg),
CP-9 (System Backup — anchors the backup-verification step),
CP-10 (System Recovery and Reconstitution — reinforces the
backup-verification step on the recovery-option side),
AC-2(13) (Account Management | Disable Accounts for High-Risk
Individuals — anchors the identity-revocation step), and
AU-6 (Audit Record Review, Analysis, and Reporting — anchors the
triage step's process / file / authentication correlation).

**MITRE D3FEND v1.0.0** — `D3-FA` (File Analysis) and `D3-PSA`
(Process Spawn Analysis) at `triage signal`; `D3-NI` (Network
Isolation) at `endpoint isolation — EDR isolate`; `D3-NTF` (Network
Traffic Filtering) at `endpoint isolation — network ACL deny
(fallback)`; `D3-ACI` (Authentication Cache Invalidation) and
`D3-AL` (Account Locking) at `identity revocation`; `D3-FH` (File
Hashing) and `D3-EHB` (Encrypted Host-storage Backup) at `backup
verification`. Two techniques on the isolation lane (EDR / network)
and two on the recovery lane (hash / immutable-tier confirmation)
are deliberate: the primary and fallback of a discipline are
audit-evident as two concurrent defensive actions each.

**OCSF v1.3.0** — `Detection Finding` (class_uid 2004, category
Findings), direction `consumes`. Consumed at the triage step as the
originating ransomware signal from the upstream SigmaHQ / EDR-native
rules referenced under `external_references` on the CACAO playbook.
`Process Activity` (class_uid 1007, category System Activity),
direction `consumes`. Consumed at the triage step for the
process-creation chain (PowerShell / WMI vssadmin / wbadmin
invocations and their parents). `File System Activity` (class_uid
1001, category System Activity), direction `consumes`. Consumed at
the triage step (mass rename / write / delete around the encryption
window) and at the backup-verification step (snapshot-catalogue
file-state records). `Authentication` (class_uid 3002, category
IAM), direction `consumes`. Consumed at the triage step for the
sign-in metadata of the host's logged-on principal so identity
revocation acts on the correct authoritative principal. `Account
Change` (class_uid 3001, category IAM), direction `emits`. Emitted
by the identity-revocation step per containment action on the
implicated principal (account disable, session invalidation, token
revocation, Kerberos TGT invalidation). `Compliance Finding`
(class_uid 2003, category Findings), direction `emits`. Emitted by
the comms-plan step when the incident crosses the NIS2 Art. 23 /
DORA Art. 19 / CRA Art. 14 threshold — one Compliance Finding per
24-hour early-warning, 4-hour DORA initial, 72-hour notification,
and intermediate / final report, keyed to the case so the
timeline-signal controls can audit on-time delivery. The emission
itself lives downstream on `playbook.incident_management@v1`; the
outbound overlay records the emission for closure.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the ransomware topology

`examples/n8n/ransomware_containment/workflow.n8n.json` carries the
CACAO topology as ten n8n nodes (`manualTrigger`, six `set` nodes,
two `if`, two `noOp` terminals), with node ids preserving the CACAO
step ids verbatim. The six action steps emit `n8n-nodes-base.set`
nodes carrying the CACAO I/O contract as editable assignment rows
plus the `x_secops_ng` reference bundles (detection, control,
telemetry, metric). The two `if-condition` nodes emit
`n8n-nodes-base.if` with placeholder conditions the operator wires
to `out.ransomware_confirmed` and `out.edr_available` on the
upstream Set rows. The lossy translations are recorded in
`meta.secops_ng_notes` so the integrator sees exactly which seams
need attention.

Operators bind the Set rows to their connectors:

- `triage signal` → the operator's malicious-code-protection / EDR
  layer's signal-fetch API against the affected host, joined with
  process-creation, file-system, and authentication audit reads
  around the encryption window; writes `__ransomware_confirmed__`,
  `__affected_host__`, `__affected_identity__`, and
  `__edr_available__`.
- `endpoint isolation — EDR isolate` → the operator's EDR vendor's
  isolate action (CrowdStrike, SentinelOne, Microsoft Defender for
  Endpoint, Sophos, or any other agent the operator runs).
- `endpoint isolation — network ACL deny (fallback)` → the
  operator's network chokepoint (firewall rule, switchport disable,
  SDN policy) — used when the EDR agent is unreachable or absent.
- `identity revocation` → the operator's IdP disable / session-
  invalidation / token-revocation surface and — where supported —
  Kerberos TGT invalidation.
- `backup verification` → the operator's backup catalogue and
  offline / immutable backup tier (snapshot locate + hash verify).
- `comms plan` → the operator's paging channel (IR lead / comms
  officer) and the drafted-notification staging path for the NIS2
  Art. 23 24-hour early warning (human sign-off, not auto-send).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/ransomware_containment/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/ransomware_containment/workflow.n8n.json`. The workflow
is inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot
of intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/ransomware_containment/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the six action
activities documenting their operator-bound seam (triage / EDR
isolate / network-ACL fallback / identity revocation / backup
verification / comms plan). The committed stub raises
`NotImplementedError` in the activity bodies pending the
CORE-TEMPORAL sibling card that wires the deterministic activity
implementations into the Temporal target; operators can drop the
module next to their worker today to see the topology and the
activity signatures.

Temporal is a natural fit for the ransomware-containment discipline:
each case becomes one workflow run; the confirmed-branch and
EDR-available gates become Temporal conditionals; retries against
transient failures on the EDR agent, the network chokepoint, the
IdP, the backup catalogue, or the paging channel get first-class
Temporal semantics (activity retry policy per seam); replay against
the same Temporal event history re-derives the same containment
record and the same backup-verification verdict once the activity
bodies are wired.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/ransomware_containment/state_bindings.py`
carries the `TypedDict` state and the `@tool`-decorated action
wrappers. `graph_spec.json` carries the target-neutral topology
(nodes, conditional edges on `__ransomware_confirmed__` and
`__edr_available__`, converging edges through identity revocation,
backup verification, and comms plan to the terminal end, and the
direct edge from the false-branch to the terminal end);
`assemble.py` is the hand-written reference assembly that wires
the GraphSpec + bindings into a `langgraph.graph.StateGraph`. The
committed `state_bindings.py` is a generated stub: each tool's
docstring names the operator-bound seam it discharges and the body
raises `NotImplementedError` until the CORE-LANGGRAPH sibling card
wires the deterministic tool implementations into the LangGraph
target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven classifier on top of the `triage signal` step (reading
the enriched host / principal / process context and emitting the
`__ransomware_confirmed__` verdict) or an LM-driven summariser into
the `comms plan` draft fills that as a private extension. The
framework-wide EU-resident LM endpoint guard re-applies the check
at process startup (`compilers/_shared/lm_endpoint_guard.py`), with
the `SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/ransomware_containment/`,
`examples/temporal/ransomware_containment/`,
`examples/langgraph/ransomware_containment/`). The n8n target ships
a committed workflow artifact; the Temporal and LangGraph targets
ship deterministic emitter output with `NotImplementedError`
activity / tool bodies pending the per-target CORE cards. Cross-
target byte-parity goldens land under
`tests/examples/ransomware_containment/` — the same cross-target
byte-parity property the framework relies on for the rest of the
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

## 7. Metrics — what the ransomware-containment response exposes

Five indicator catalogue entries surface the ransomware_containment
posture to the operator's metrics dashboard. The catalogue entries
live under `content/metrics/`.

- **`kpi.mttd_ransomware@v1`** — time from earliest telemetry
  evidence (shadow-copy deletion, first mass-rename, first
  encryption-signature match) to the first authoritative detection
  firing on the ransomware case. Catalogue:
  [`content/metrics/mttd_ransomware.yaml`](../../content/metrics/mttd_ransomware.yaml).
  Stamped by the triage step. Rising values indicate the
  malicious-code-protection surface is drifting behind the
  operational objective.
- **`kpi.mttr_containment@v1`** — median time from confirmed triage
  to containment completion (endpoint isolation acknowledged plus
  identity revocation completed). Catalogue:
  [`content/metrics/mttr_containment.yaml`](../../content/metrics/mttr_containment.yaml).
  Stamped by both isolation legs and by the identity-revocation
  step; audits on-time containment across the two-legged discipline
  (host cut-out + principal cut-out).
- **`kpi.backup_integrity_pass_rate@v1`** — share of confirmed
  ransomware cases whose located known-good snapshot passed the
  catalogue-hash integrity check. Catalogue:
  [`content/metrics/backup_integrity_pass_rate.yaml`](../../content/metrics/backup_integrity_pass_rate.yaml).
  Stamped by the backup-verification step; low values indicate the
  offline / immutable-tier posture is drifting and the CRA Annex I
  §1(h) evidence is at risk.
- **`kpi.notification_sla_compliance@v1`** — share of drafted
  regulator notifications staged within the statutory clock (24
  hours NIS2 Art. 23(4)(a), 4 hours DORA Art. 19(4)(a), 24 hours
  CRA Art. 14(3) — whichever applies to the operator). Catalogue:
  [`content/metrics/notification_sla_compliance.yaml`](../../content/metrics/notification_sla_compliance.yaml).
  Stamped by the comms-plan step.
- **`kpi.timeline_completeness@v1`** — share of closed cases whose
  detect / contain / notify timeline is fully populated (no missing
  timestamps on the case envelope). Catalogue:
  [`content/metrics/timeline_completeness.yaml`](../../content/metrics/timeline_completeness.yaml).
  Stamped by the comms-plan step at handoff.
- **`kri.regulator_notification_overrun@v1`** — share of drafted
  regulator notifications that overran the statutory clock.
  Catalogue:
  [`content/metrics/regulator_notification_overrun.yaml`](../../content/metrics/regulator_notification_overrun.yaml).
  Stamped by the comms-plan step; the KRI-side counterpart to the
  notification-SLA KPI.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI / KRI series against their own metrics backend.

## 8. Detection references — the SigmaHQ named rules

The playbook cites five upstream **SigmaHQ / MITRE ATT&CK-anchored
signal shapes** on its `external_references` (rule ids pinned
upstream at SigmaHQ, not re-authored here):

- **Shadow Copies Deletion Using Operating Systems Utilities.**
  Attaches at the triage step as the originating signal for the
  vssadmin shadow-copy deletion case shape.
- **Deletion of Volume Shadow Copies via WMI with PowerShell.**
  Attaches at the triage step as the alternative shadow-copy
  deletion vector via WMI / PowerShell.
- **Windows Backup Deleted Via Wbadmin.EXE.** Attaches at the
  triage step for the Windows Backup catalogue deletion case shape
  and again at the backup-verification step as a corroborating
  signal that the on-host backup surface has been actively targeted.
- **Suspicious Appended Extension (ransomware file rename).**
  Attaches at the triage step for the mass-rename / suspicious-
  extension case shape.
- **Successful Overpass the Hash Attempt.** Attaches at the
  identity-revocation step as a corroborating signal that the
  principal's credentials have been used along the pass-the-hash
  path — the anchor for revoking the Kerberos TGT alongside the
  session / token revocation.

The MITRE ATT&CK anchors on the playbook — T1490 (Inhibit System
Recovery), T1486 (Data Encrypted for Impact), and T1550.002
(Pass-the-Hash) — pin the case-shape taxonomy the triage step and
the identity-revocation step read against. See
[`content/playbooks/ransomware_containment/README.md`](../../content/playbooks/ransomware_containment/README.md)
for the rule-reference discipline (SecOps-NG does not re-author
Sigma; upstream rule ids are pinned by the CORE-layer detection
mapping).

## 9. Operator customisation points

The playbook is a ransomware-containment machine; the *policy* it
exercises is the operator's. The customisation seams:

- **EDR isolation API binding.** The `endpoint isolation — EDR
  isolate` step reads the operator's EDR-vendor isolate action.
  The framework binds neither the vendor (CrowdStrike, SentinelOne,
  Microsoft Defender for Endpoint, Sophos, Elastic Endpoint,
  self-hosted OSS, or any other) nor the auth surface; operators
  wire the step to whichever agent runs on their fleet and pin the
  authorisation policy that gates the isolate call on their
  change-management surface.
- **Network-ACL fallback rule surface.** The `endpoint isolation —
  network ACL deny (fallback)` step reads the operator's network
  chokepoint. The chokepoint (perimeter firewall, edge router,
  switchport disable via the switch fabric's API, SDN policy such
  as VMware NSX / Cilium / EVE-NG, or a cloud security-group deny
  rule) is operator-owned. The framework binds the topology, not
  the vendor.
- **IdP session-revocation API binding.** The `identity revocation`
  step reads two independent surfaces — the IdP's account-disable
  and session / refresh-token / access-token invalidation surface,
  and the Kerberos TGT invalidation surface where the environment
  runs Active Directory or a compatible KDC. The framework binds
  neither the IdP (Entra ID, Okta, Keycloak, self-hosted OIDC) nor
  the AD surface; operators wire the seam to their own identity
  layer.
- **Backup snapshot catalogue path.** The `backup verification`
  step reads the operator's backup catalogue and offline /
  immutable backup tier. The catalogue API (Veeam, Commvault, Rubrik,
  Borg / Restic against object-locked storage, or any other) and
  the immutable-tier posture (S3 Object Lock, Azure Blob immutable
  storage, self-hosted WORM tier) are operator-owned. The framework
  binds neither the catalogue vendor nor the immutability
  mechanism.
- **Significance threshold for NIS2 Art. 23 / DORA Art. 19 / CRA
  Art. 14 notification branches.** The significance verdict —
  impact on essential services, lateral-movement risk,
  encryption-scope indicator on personal or regulated data,
  financial-entity classification, product-impact classification
  under CRA — is computed off the evidence this playbook produces
  (host-blast-radius, identity-revocation record, backup-integrity
  verdict). The numeric cut-offs and the qualitative predicates
  live on the downstream `playbook.incident_management@v1` gate,
  per the operator's regulator-routing policy. The framework
  documents the seam but does not prescribe the threshold.
- **Notification-channel binding on the comms-plan step.** The
  `comms plan` step reads the operator's paging channel (IR lead /
  comms officer via PagerDuty, Opsgenie, XMatters, self-hosted
  Alertmanager, or a mail / chat surface) and the drafted-
  notification staging path for the NIS2 Art. 23 24-hour early
  warning. Which authority receives which regime's submission —
  national CSIRT under NIS2, competent authority under DORA, ENISA
  and the coordinator CSIRT under CRA — is per Member State and
  per sector, and the downstream engine is where those channels
  are pre-bound.

## 10. Replay and audit story

The byte-parity drift guards land with the CORE-TEMPORAL /
CORE-LANGGRAPH sibling cards under
`tests/examples/ransomware_containment/`. Each per-target golden
pins the committed worked-example artifact to a fresh emitter run
from the canonical CACAO source; if the compiler or the playbook
changes, regenerate via the per-target `regenerate.sh` and commit
the diff intentionally.

The cross-target replay property is the harder one: the same case,
fed through n8n / Temporal / LangGraph, produces byte-identical
containment records *and* byte-identical backup-verification
verdicts once each target's activity / tool bodies are wired against
the same operator seams and the same OSCAL / OCSF / D3FEND reference
bundles. The `(affected_host, affected_identity, ransomware_confirmed,
isolated_at, revoked_at, latest_known_good_snapshot,
snapshot_integrity_ok, notification_drafted_at)` key is the string
a regulator can diff to confirm the property holds across targets.

## 11. Playbook chain — where ransomware_containment sits

The ransomware-response chain expresses itself as one containment
workflow feeding one submission engine and one review workflow:

```
ransomware_containment ─► incident_management
                       └► post_incident_review
```

- **Downstream: `incident_management`.** The regulator-submission
  timeline itself (NIS2 Art. 23 24-hour / 72-hour / one-month,
  DORA Art. 19 4-hour / 72-hour, CRA Art. 14 24-hour / 72-hour /
  one-month, GDPR Art. 33 72-hour where personal-data exposure
  crosses the threshold) runs on
  `playbook.incident_management@v1`. See
  [`docs/cookbook/incident_management.md`](./incident_management.md).
- **Downstream: `post_incident_review`.** The lessons-learned /
  root-cause discipline that closes the case out to
  organisation-wide learning runs on
  `playbook.post_incident_review@v1`. See
  [`docs/cookbook/post_incident_review.md`](./post_incident_review.md).
- **Adjacent: `identity_compromise`.** The local identity cut-out
  on the implicated principal (account disable, session / token
  invalidation, TGT invalidation) is on this playbook; the deeper
  IdP-side blast-radius audit — rogue OAuth consents,
  conditional-access exceptions, third-party app grants,
  lingering role assumptions — lives on
  `playbook.identity_compromise@v1`. Operators who suspect the
  ransomware event's identity leg extends past the immediate
  principal should hand off into identity_compromise for the
  full IAM audit. See
  [`docs/cookbook/identity_compromise.md`](./identity_compromise.md).
- **Adjacent: `backup_recovery`.** The backup-verification step on
  this playbook proves the recovery *option* is exercisable; it
  does not restore. The restore-from-snapshot discipline runs on
  the backup-recovery cookbook. See
  [`docs/cookbook/backup_recovery.md`](./backup_recovery.md).

The chain lets ransomware_containment stay narrowly focused on the
host-side containment-and-backup-verification discipline while the
per-stage regulator submissions happen on `incident_management`,
the lessons-learned closure happens on `post_incident_review`, the
deeper IAM audit (when needed) happens on `identity_compromise`,
and the actual restore (when needed) happens on `backup_recovery`.
The chain is not code-coupled — each playbook is a standalone
CACAO artifact that can be run in isolation — but the audit trail's
coherence across the workflows is the sovereign-security property
the framework guarantees.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  EDR agent, the network chokepoint, the IdP, the KDC, the backup
  catalogue, the paging channel, or the downstream regulator-
  submission engine. Connectors are operator-bound at runtime
  against environment variables documented per target.
- **Per-stage regulator submissions.** The 24-hour early warning,
  the 72-hour notification, the one-month final report (NIS2), the
  4-hour initial / 72-hour intermediate (DORA), the 24-hour /
  72-hour / one-month severe-incident chain (CRA Art. 14), and
  the 72-hour supervisory-authority notification (GDPR Art. 33)
  all run on `playbook.incident_management@v1`. This playbook
  drafts the NIS2 Art. 23 24-hour early warning as a comms-plan
  handoff; the per-stage submissions themselves are downstream.
- **Restore-from-snapshot.** The backup-verification step proves
  the recovery option is exercisable; it does not restore. The
  restore-from-snapshot discipline runs on the backup-recovery
  cookbook.
- **Deeper IdP blast-radius audit.** The identity-revocation step
  is the *local cut-out* on the principal implicated by the
  ransomware event. Rogue OAuth consents, conditional-access
  exceptions, third-party app grants, and lingering role
  assumptions on the same principal are audited on
  `playbook.identity_compromise@v1`.
- **SigmaHQ rule id pinning.** The playbook cites five upstream
  Sigma rule *names* (shadow-copy deletion, WMI / PowerShell
  shadow-copy deletion, wbadmin backup deletion, ransomware file
  extension rename, overpass-the-hash). Stable upstream rule ids
  are pinned by the CORE-layer detection mapping, not by this
  cookbook; SecOps-NG does not re-author Sigma.

## 13. References

- [`content/playbooks/ransomware_containment/README.md`](../../content/playbooks/ransomware_containment/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/ransomware_containment/mappings.yaml`](../../content/playbooks/ransomware_containment/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay with
  per-step control anchors.
- [`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
  — NIS2 Article 21(2)(b) inbound anchor (incident-handling
  capability).
- [`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
  — NIS2 Article 23 inbound anchor (24-hour early warning, 72-hour
  notification).
- [`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
  — DORA Articles 18 and 19 inbound anchor (major-classification,
  4-hour initial, 72-hour intermediate).
- [`content/mappings/cra/annex-i-1-essential-cybersecurity.yaml`](../../content/mappings/cra/annex-i-1-essential-cybersecurity.yaml)
  — CRA Annex I §1(h) availability-after-incident inbound anchor.
- [`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
  — CRA Article 14(3) severe-incident notification inbound anchor.
- [`content/mappings/gdpr/data-flow-ransomware_containment.md`](../../content/mappings/gdpr/data-flow-ransomware_containment.md)
  — GDPR Article 30 Record of Processing Activity.
- [`examples/n8n/ransomware_containment/README.md`](../../examples/n8n/ransomware_containment/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/ransomware_containment/README.md`](../../examples/temporal/ransomware_containment/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/ransomware_containment/README.md`](../../examples/langgraph/ransomware_containment/README.md)
  — LangGraph worked-example stub.
- [`docs/cookbook/incident_management.md`](./incident_management.md)
  — downstream cookbook (per-stage regulator-submission engine).
- [`docs/cookbook/post_incident_review.md`](./post_incident_review.md)
  — downstream cookbook (lessons-learned / root-cause discipline).
- [`docs/cookbook/identity_compromise.md`](./identity_compromise.md)
  — adjacent cookbook (deeper IdP blast-radius audit).
- [`docs/cookbook/backup_recovery.md`](./backup_recovery.md)
  — adjacent cookbook (restore-from-snapshot discipline).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
