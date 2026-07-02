# data_exfil — cookbook walkthrough

Data-exfiltration response workflow under NIS2 Article 23, DORA
Article 19, GDPR Articles 33 and 34, and CRA Article 14 severe-
incident notification. The `playbook.data_exfil@v1` CACAO playbook
ingests a DLP or egress signal delivered by the operator's system-
monitoring layer, hydrates it with originating user / asset /
destination context, runs a scope assessment that produces the
resolved data classification, the count of distinct data subjects
affected, and a verdict on whether actual exfiltration occurred,
branches on that verdict into either close-out (false positive or
in-line-prevented egress) or containment (egress-policy tightening
on the named sinks and identity cut-out on the originating
principal), and finally gates regulator and customer notification
on the affected-subjects threshold so the operator can meet the
EU regulator-notification chain audit-evidently.

The playbook is deliberately the **upstream emitter** of the
regulator-notification chain, not the submission engine itself. The
NIS2 Art. 23 24-hour early warning, the 72-hour notification, the
one-month final report, the DORA Art. 19 4-hour initial / 72-hour
intermediate cadence, the CRA Art. 14(3) severe-incident timeline,
and the GDPR Art. 33 / 34 personal-data-breach notification all
run on the downstream `playbook.incident_management@v1` engine —
this playbook's `notify regulator` step composes the structured
incident-finding envelope and hands it off along the operator's
pre-bound regulator channel; `incident_management` renders the
per-stage submissions from that envelope. The GDPR Art. 33 / 34
routing is expressed jointly with NIS2 Art. 23 and DORA Art. 19
at the `regulator notification threshold met?` gate per the
mappings-file closure note in
[`content/playbooks/data_exfil/mappings.yaml`](../../content/playbooks/data_exfil/mappings.yaml).

The upstream hand-off chain closes on `phishing_triage`: the BEC
and credential-harvest branches on `playbook.phishing_triage@v1`
escalate into `playbook.identity_compromise@v1` and, where exfil
follows, into this playbook. The three-workflow chain
`phishing_triage → identity_compromise → data_exfil` feeds the
one submission engine `incident_management` at the tail — the
sovereign-security notification chain expressed as portable content.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the triage,
the scope assessment, the exfil-confirmed branch, the containment
step, the regulator-notification gate, and the two notification
emitters land in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/data_exfil/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.data_exfil@v1)

content/mappings/nis2/article-21-2-b.yaml
                                  # NIS2 Art. 21(2)(b) inbound anchor —
                                  # incident-handling capability; backlinks
                                  # playbook.data_exfil@v1 as the
                                  # operational discharge of detect-through-
                                  # contain-through-notify for the data-
                                  # exfiltration case set
content/mappings/nis2/article-23.yaml
                                  # NIS2 Art. 23 inbound anchor —
                                  # 24-hour early warning and 72-hour
                                  # notification, backlinking to
                                  # playbook.data_exfil@v1 as an
                                  # upstream signal source into the
                                  # regulator-submission engine
content/mappings/dora/article-19-and-28.yaml
                                  # DORA Art. 18 major-classification
                                  # and Art. 19 initial-4h / intermediate-
                                  # 72h notification, backlinking to
                                  # playbook.data_exfil@v1 for the
                                  # regulator-notification chain
content/mappings/cra/article-14-and-annex-i.yaml
                                  # CRA Art. 14(3) severe-incident
                                  # notification — 24h / 72h / 1-month
                                  # timing; playbook.data_exfil@v1 named
                                  # on the entry's playbook_refs
content/mappings/gdpr/data-flow-data_exfil.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity covering the triage /
                                  # scope-assessment / containment /
                                  # notification-payload processing
                                  # against personal-data payloads
content/mappings/gdpr/article-33-34-personal-data-breach-notification.yaml
                                  # GDPR Art. 33 (supervisory-authority
                                  # notification, 72 hours) and Art. 34
                                  # (data-subject communication) anchors
                                  # for the personal-data-breach chain
```

The CACAO source is canonical. The seven action steps, two
`if-condition` gates, and two `start` / `end` wiring nodes are the
deterministic policy the playbook *means* — a linear triage-then-
assess chain feeding an exfil-confirmed branch (false-verdict
short-circuits to close-out), then a linear containment step feeding
a regulator-threshold branch, then per-branch notification actions
converging on a common `end`. The three worked examples under
`examples/{n8n,temporal,langgraph}/data_exfil/` are the same
playbook compiled into three orchestrator idioms. Everything else —
the DLP platform producing the signal, the egress chokepoint, the
IdP the containment step cuts the principal out at, the case store,
the pre-bound regulator channel (national CSIRT for NIS2, competent
authority for DORA, supervisory authority for GDPR), and the
customer-notification gateway — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships nine steps: one `start`, five `action`, two
`if-condition`, and one `end`. The first `if-condition` fires on
`__exfil_confirmed__`; `on_success` (confirmed exfiltration) routes
into `containment`, `on_failure` (in-line prevention or false
positive) short-circuits to `end`. The second `if-condition` fires
on `__regulator_required__`; `on_success` (threshold crossed) routes
into `notify regulator` then falls through to `notify customer`;
`on_failure` routes directly to `notify customer`. Both branches
converge on the notify-customer step so the affected-subjects
notification path is reached whenever exfiltration is confirmed —
the regulator submission is the *conditional* leg, not the
affected-subject communication.

| Step suffix | Step                                                | Discipline                                                                                                                                                                                                                              | Status         |
|-------------|-----------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | exfil-start                                         | edge wiring only — no body                                                                                                                                                                                                              | n/a            |
| `…000002`   | triage signal                                       | hydrate the originating DLP / egress signal with originating user / asset / destination context against `__signal_id__` and decide whether the signal warrants scope assessment or is a known benign egress pattern                    | operator-bound |
| `…000003`   | scope assessment                                    | determine the volume and classification of data observed leaving the boundary, the count of distinct data subjects affected, and whether actual exfiltration occurred; sets `__data_classification__`, `__affected_subjects_count__`, `__exfil_confirmed__` | operator-bound |
| `…000004`   | exfil confirmed?                                    | `if-condition` — branches on `__exfil_confirmed__` (true → containment, false → end)                                                                                                                                                    | n/a            |
| `…000005`   | containment                                         | egress-policy tightening on the destination(s) named in the signal (deny / rate-limit at the egress chokepoint), session-token revocation and account disable on the originating principal, forced credential rotation                  | operator-bound |
| `…000006`   | regulator notification threshold met?               | `if-condition` — branches on `__regulator_required__` against affected-subjects count + data classification per the operator's routing policy (NIS2 Art. 23 / DORA Art. 19 / GDPR Art. 33)                                              | n/a            |
| `…000007`   | notify regulator                                    | compose the structured incident-finding envelope from scope-assessment outputs and hand off along the pre-bound regulator channel; feeds `playbook.incident_management@v1` as the downstream submission engine                          | operator-bound |
| `…000008`   | notify customer                                     | compose and dispatch the data-subject / customer-facing notification from scope-assessment outputs along the pre-bound channel; tracked separately from the regulator submission so the notification-SLA KPI reports two timelines      | operator-bound |
| `…000009`   | exfil-end                                           | edge wiring only — no body                                                                                                                                                                                                              | n/a            |

All five action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (detection, control,
telemetry, metric). One execution short-circuits to `end` at the
first gate when scope assessment does not confirm exfiltration
(the close-out is logged for the false-positive KPI by an out-of-
scope card and no containment, regulator, or customer notification
fires). When exfiltration is confirmed, containment runs
unconditionally; regulator notification is conditional on the
threshold; customer notification always runs. Per-case metric
accounting into the MTTD / containment-MTTR / notification-SLA /
regulator-notification-overrun catalogue entries is therefore
unambiguous.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The overlay pins the control, detection, telemetry,
> and metric surface; the n8n reference emitter ships a committed
> `workflow.n8n.json` today, and the Temporal / LangGraph siblings
> ship deterministic emitter output with `NotImplementedError`
> activity / tool bodies pending the per-target CORE cards.
> Cross-target byte-parity goldens live under
> `tests/examples/data_exfil/`.

## 3. Lifecycle contract — the five action states

The per-case payload — signal envelope, hydrated context, resolved
data classification, affected-subjects count, exfil verdict,
containment record, and per-side notification envelope — is
incident-handling content that frequently carries personal data of
natural persons (originating user identifier, downstream customer /
subject identifiers, message payload where classification says so).
The inbound GDPR Art. 30 Record of Processing Activity at
[`content/mappings/gdpr/data-flow-data_exfil.md`](../../content/mappings/gdpr/data-flow-data_exfil.md)
covers the triage / scope-assessment / containment / notification-
payload processing the five steps below operate on, lawful-basis-
grounded in GDPR Art. 6(1)(f) legitimate interests with
Art. 6(1)(c) legal obligation as the secondary basis where NIS2
Art. 21(2)(b), DORA Art. 19, GDPR Art. 33, or CRA Art. 14
transposition applies. The framework treats `__signal_id__` as a
DLP-platform-scoped opaque identifier under the operator's own
naming convention and does not re-derive subject identifiers
outside the operator's own identity surface.

**triage signal** (`…000002`)
:   Hydration step. Reads the operator's DLP / egress-monitoring
    layer for the originating signal against `__signal_id__`,
    joins it with originating user / asset / destination context
    (from IAM, CMDB, and network-flow telemetry), and decides
    whether the signal warrants scope assessment or is a known
    benign egress pattern. Anchored on MITRE D3FEND v1.0.0
    `D3-IRA` (Incident Response Analysis) — the hydration of the
    canonical case object the assessment step reads against.
    Anchored on OSCAL SI-4 (System Monitoring) as the upstream
    control the signal was produced by. Feeds `kpi.mttd_exfil@v1`.

**scope assessment** (`…000003`)
:   Assessment step. Determines the volume and classification of
    data observed leaving the boundary, the count of distinct data
    subjects affected, and whether actual exfiltration occurred or
    was prevented in-line by a control at the egress chokepoint.
    Produces `__data_classification__` (public / internal /
    confidential / restricted / special-category),
    `__affected_subjects_count__`, and `__exfil_confirmed__` on
    the case envelope. Anchored on MITRE D3FEND v1.0.0 `D3-FA`
    (Forensic Analysis) and OSCAL RA-2 (Security Categorization) —
    the resolved data classification is the security-categorization
    verdict the rest of the playbook branches on, driving both
    containment proportionality and regulator-notification routing.
    Consumes OCSF **Detection Finding** (class 2004) at the triage
    step and OCSF **Network Activity** (class 4001) at the scope-
    assessment step to bound observed egress volume.

**exfil confirmed?** (`…000004`, `if-condition`)
:   Deterministic branch on `__exfil_confirmed__`. `on_success`
    (confirmed) routes into `containment`; `on_failure` (false
    positive or in-line-prevented egress) short-circuits to `end`.
    The close-out on the false branch is logged for the false-
    positive KPI by an out-of-scope card and no containment or
    notification fires. Anchored on OSCAL IR-4 (Incident Handling).

**containment** (`…000005`)
:   Containment step. Applies containment proportionate to data
    classification and scope: (a) tightens the egress policy on
    the destination(s) named in the signal (deny or rate-limit at
    the operator's egress chokepoint), (b) invalidates active
    sessions, refresh tokens, and access tokens for the
    originating principal, (c) disables the principal at the IdP
    for the duration of the containment window, and (d) forces
    credential rotation on the impacted identity. Bounded by the
    operator-supplied authorisation policy — the framework binds
    the topology, not the authorisation to disable a live account.
    Anchored on MITRE D3FEND v1.0.0 `D3-NTF` (Network Traffic
    Filtering), `D3-ACI` (Authentication Cache Invalidation), and
    `D3-AL` (Account Locking); OSCAL SC-7 (Boundary Protection),
    AC-4 (Information Flow Enforcement), and AC-2(13) (Account
    Management | Disable Accounts for High-Risk Individuals).
    Emits OCSF **Account Change** (class 3001) per identity cut-
    out so the containment-MTTR KPI can audit on-time containment.
    Stamps `kpi.mttr_containment@v1`. Deeper IdP-side audit
    (session-lineage graph, cross-tenant blast-radius) lives on
    the downstream `playbook.identity_compromise@v1`.

**regulator notification threshold met?** (`…000006`, `if-condition`)
:   Deterministic branch on `__regulator_required__`, evaluated
    against `__affected_subjects_count__` and
    `__data_classification__` per the operator's regulator-routing
    policy. `on_success` (threshold crossed) routes into `notify
    regulator` and then falls through to `notify customer`;
    `on_failure` routes directly to `notify customer`. The
    threshold policy itself is operator-owned — the framework binds
    the gate and the routing surface, not the numeric cut-off. The
    routing key is the joint NIS2 Art. 23 / DORA Art. 19 / GDPR
    Art. 33 predicate per the mappings-file closure note; CRA
    Art. 14(3) severe-incident routing lands through the same
    envelope on `playbook.incident_management@v1`.

**notify regulator** (`…000007`)
:   Regulator-notification emitter. Composes the structured
    incident-finding envelope from the scope-assessment outputs
    (data classification, affected-subjects count, containment
    outcome) and hands it off along the operator's pre-bound
    regulator channel — the national CSIRT for NIS2, the competent
    authority for DORA, the supervisory authority for GDPR, the
    market-surveillance authority for CRA. This step is the
    **upstream emitter** into `playbook.incident_management@v1`;
    the 24-hour / 72-hour / one-month per-stage submissions are
    rendered by that downstream engine from the envelope emitted
    here. Emits OCSF **Incident Finding** (class 2005) as the
    canonical case envelope and OCSF **Compliance Finding**
    (class 2003) per regulator submission (one per NIS2 Art. 23 /
    DORA Art. 19 / GDPR Art. 33 lane) so on-time delivery is
    audit-evident. Anchored on OSCAL IR-6 (Incident Reporting)
    and MITRE D3FEND v1.0.0 `D3-IRA`. Stamps
    `kpi.notification_sla_compliance@v1` and
    `kri.regulator_notification_overrun@v1`.

**notify customer** (`…000008`)
:   Customer-notification emitter. Composes the data-subject /
    customer-facing notification payload from the scope-assessment
    outputs (data classification, affected-subjects count) and
    hands it off along the operator's pre-bound customer-comms
    channel. Tracked separately from the regulator submission so
    the notification-SLA KPI reports the two timelines
    independently — GDPR Art. 34 in particular has a distinct
    "communicate to the data subject without undue delay" clock
    that is not the same as the Art. 33 72-hour supervisory-
    authority clock. Emits OCSF **Compliance Finding** (class 2003)
    per Art. 34 communication, keyed to the case. Anchored on
    MITRE D3FEND v1.0.0 `D3-IRA`. Stamps
    `kpi.notification_sla_compliance@v1`.

The five action steps are operator-bound runtime seams: the
framework ships neither the DLP platform, the egress chokepoint,
the IdP-side session-revocation surface, the pre-bound regulator
channel, nor the notify-customer gateway. The playbook is
the portable description of *what* the operator's stack should do
per case; binding those seams to real endpoints is the operator's
job.

> **LM determinism.** Triage, scope assessment, containment, and
> the two notification emitters are structured reads and writes
> against operator-owned surfaces, not free-text reasoning steps.
> The playbook binds no DSPy signature — there is no LM-driven
> step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If
> an operator wires an LM-driven scope-assessment classifier on
> top of the raw evidence (a private, forward-looking extension),
> the framework-wide EU-resident LM endpoint guard re-applies the
> check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
> Free-text narrative fields on the downstream regulator
> submissions are handled by `playbook.incident_management@v1`
> under its own DSPy signature schema (scoped to narrative, root
> cause, and applied mitigations); this playbook only emits the
> structured envelope.

## 4. Regulatory anchors

**NIS2 Article 21(2)(b)** — incident-handling capability. The
clause requires essential and important entities to operate an
incident-handling capability (detect, triage, contain, remediate,
capture lessons learned). The data_exfil playbook is the
**operational discharge of detect-through-contain-through-notify
for the data-exfiltration case set**, with the regulator-submission
tail handed off to `playbook.incident_management@v1`. Inbound
anchor at
[`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
(`nis2:art-21-2-b`) backlinks `playbook.data_exfil@v1`.

**NIS2 Article 23** — incident-reporting obligations. Article 23(4)(a)
requires a 24-hour early warning and Article 23(4)(b) requires a
72-hour notification with an initial assessment of severity and
impact. The data_exfil playbook is an **upstream signal source**
into the regulator-submission engine: the scope-assessment outputs
(`__data_classification__`, `__affected_subjects_count__`) feed
the severity / impact / affected-subjects sections of the
assessment that `playbook.incident_management@v1` emits. Inbound
anchors at
[`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
(`nis2:art-23-early-warning`, `nis2:art-23-notification-72h`).

**DORA Article 18(1)** — classification. Requires classification of
ICT-related incidents against the criteria in the JC RTS on
incident classification (Commission Delegated Regulation (EU)
2024/1772). The data_exfil playbook's scope-assessment step
produces the data-classification, affected-subjects-count, and
exfil-confirmed evidence that drives the major-classification
verdict on the downstream `playbook.incident_management@v1` engine.
Inbound anchor at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-18-classification`).

**DORA Article 19** — reporting of major ICT-related incidents.
Article 19(4)(a) requires an initial notification within 4 hours
of major-classification and Article 19(4)(b) requires an
intermediate notification within 72 hours with updated assessment.
The data_exfil playbook's triage and scope-assessment artefacts
anchor the initial notification; the containment-outcome record
(was further exfiltration stopped at the egress filter, was the
implicated principal cut out) and the resolved scope feed the
updated assessment for the intermediate report on the downstream
`playbook.incident_management@v1` engine. Inbound anchors at
[`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
(`dora:art-19-initial-4h`, `dora:art-19-intermediate-72h`).

**GDPR Articles 33 and 34** — personal-data-breach notification.
Article 33 requires supervisory-authority notification within 72
hours when a personal-data breach is likely to result in a risk to
the rights and freedoms of natural persons; Article 34 requires
communication to the affected data subjects without undue delay
when the risk is high. Data exfil is the playbook most likely to
trip the Art. 33 / 34 chain — the regulator-notification-threshold
gate at `…000006` routes against NIS2 Art. 23, DORA Art. 19, and
GDPR Art. 33 **jointly** per the CACAO playbook description; the
customer-notification step at `…000008` is the operational
discharge of Art. 34. Inbound anchor at
[`content/mappings/gdpr/article-33-34-personal-data-breach-notification.yaml`](../../content/mappings/gdpr/article-33-34-personal-data-breach-notification.yaml).
The per-workflow Record of Processing Activity for the personal-
data processing this workflow performs lives at
[`content/mappings/gdpr/data-flow-data_exfil.md`](../../content/mappings/gdpr/data-flow-data_exfil.md).

**CRA Article 14(3)** — severe-incident notification. Requires
the manufacturer to notify severe incidents to the market-
surveillance authority under a 24-hour / 72-hour / one-month
chain. Where the exfil event is a severe incident affecting a
product with digital elements, the data_exfil playbook feeds the
same envelope into `playbook.incident_management@v1` that renders
the CRA Art. 14(3) per-stage submissions. Inbound anchor at
[`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
(`cra:art-14-severe-incident`).

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/data_exfil/mappings.yaml`](../../content/playbooks/data_exfil/mappings.yaml)):
IR-4 (Incident Handling — anchors the playbook end-to-end),
IR-5 (Incident Monitoring — anchors the per-case timeline
signals across triage, containment, and notification),
IR-6 (Incident Reporting — anchors the regulator-notification
step as the upstream emitter into the submission engine),
AC-4 (Information Flow Enforcement — anchors the egress-policy
leg of containment), SC-7 (Boundary Protection — anchors the
network-boundary leg of containment), SI-4 (System Monitoring —
anchors the triage step's upstream signal), RA-2 (Security
Categorization — anchors the scope-assessment data-classification
verdict), AC-2(13) (Account Management | Disable Accounts for
High-Risk Individuals — anchors the identity cut-out leg of
containment).

**MITRE D3FEND v1.0.0** — `D3-IRA` (Incident Response Analysis)
at `triage signal`, `notify regulator`, and `notify customer`;
`D3-FA` (Forensic Analysis) at `scope assessment`; `D3-NTF`
(Network Traffic Filtering), `D3-ACI` (Authentication Cache
Invalidation), and `D3-AL` (Account Locking) at `containment`.
Three techniques on one step (containment) is deliberate: the
egress-filter leg, the session-token-revocation leg, and the
account-disable leg are three concurrent defensive actions the
containment step discharges in a single case.

**OCSF v1.3.0** — `Detection Finding` (class_uid 2004, category
Findings), direction `consumes`. Consumed at the triage step as
the originating DLP / egress signal. `Network Activity`
(class_uid 4001, category Network Activity), direction
`consumes`. Consumed at the scope-assessment step to bound the
observed egress volume against the destination(s) named in the
signal. `Account Change` (class_uid 3001, category IAM),
direction `emits`. Emitted by the containment step per identity
cut-out (session invalidation, token revocation, account
disable). `Incident Finding` (class_uid 2005, category Findings),
direction `emits`. Emitted by the notify-regulator step as the
canonical case envelope the downstream submission engine
consumes. `Compliance Finding` (class_uid 2003, category
Findings), direction `emits`. Emitted by both notification steps
per regulator submission and per customer communication, keyed to
the case, so the notification-SLA KPI and the regulator-
notification-overrun KRI can audit on-time delivery.

> **DLP Activity class.** The playbook's `x_secops_ng.telemetry_refs`
> cites `telemetry.ocsf.dlp_alert@v1` as the upstream telemetry
> class that produces the originating signal. A first-class OCSF
> telemetry binding for DLP Activity is not carried in the overlay
> today because the OCSF v1.3.0 class_uid for DLP Activity could
> not be verified without speculation; the Detection Finding
> binding is used as the upstream carrier instead. Once
> `content/telemetry/dlp_alert.yaml` lands, a follow-up card can
> pin the class without a schema change.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the exfil topology

`examples/n8n/data_exfil/workflow.n8n.json` carries the CACAO
topology as nine n8n nodes (`manualTrigger`, five `set` nodes, two
`if` nodes, one `noOp`), with node ids preserving the CACAO step
ids verbatim. The five action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus
the `x_secops_ng` reference bundles (detection, control, telemetry,
metric). The two `if-condition` nodes emit `n8n-nodes-base.if` with
placeholder conditions the operator wires to the upstream
`out.exfil_confirmed` and `out.regulator_required` fields.
Lossy translations are recorded in `meta.secops_ng_notes` so the
integrator sees exactly which seams need attention.

Operators bind the Set rows to their connectors:

- `triage signal` → the operator's DLP / egress-monitoring layer's
  signal-fetch API against `__signal_id__`.
- `scope assessment` → the operator's data-classification service,
  IAM subject-count query, and egress-flow correlator; writes
  `__data_classification__`, `__affected_subjects_count__`,
  `__exfil_confirmed__`.
- `containment` → the operator's egress chokepoint (deny / rate-
  limit binding on the named destination), IdP session-invalidation
  and account-disable API, and credential-rotation surface.
- `notify regulator` → the operator's pre-bound regulator channel
  (national CSIRT for NIS2, competent authority for DORA,
  supervisory authority for GDPR, market-surveillance authority
  for CRA); the downstream `playbook.incident_management@v1`
  engine consumes the emitted envelope.
- `notify customer` → the operator's pre-bound customer-comms
  channel (in-app notification, email, postal — per the operator's
  GDPR Art. 34 procedure).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/data_exfil/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/data_exfil/workflow.n8n.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot
of intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/data_exfil/workflow.temporal.py` is a standard
Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the five action
activities documenting their operator-bound seam (signal fetch,
scope assessment, containment cut-out, regulator envelope
composition, customer notification). The committed stub raises
`NotImplementedError` in the activity bodies pending the
CORE-TEMPORAL sibling card that wires the deterministic activity
implementations into the Temporal target; operators can drop the
module next to their worker today to see the topology and the
activity signatures.

Temporal is a natural fit for the exfil-response discipline: each
case becomes one workflow run; the exfil-confirmed branch and the
regulator-threshold branch become Temporal conditionals; retries
against transient failures on the DLP platform, the egress
chokepoint, or the pre-bound regulator channel get first-class
Temporal semantics (activity retry policy per seam); replay against
the same Temporal event history re-derives the same containment
record and the same notification envelope once the activity bodies
are wired.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/data_exfil/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes,
conditional edge on `__exfil_confirmed__`, conditional edge on
`__regulator_required__`, linear edges through the notification
steps to `end`); `assemble.py` is the hand-written reference
assembly that wires the GraphSpec + bindings into a
`langgraph.graph.StateGraph`. The committed `state_bindings.py` is
a generated stub: each tool's docstring names the operator-bound
seam it discharges and the body raises `NotImplementedError` until
the CORE-LANGGRAPH sibling card wires the deterministic tool
implementations into the LangGraph target.

LangGraph is the agentic target — an operator who wants to layer
an LM-driven scope-assessment classifier on top of the raw
evidence (reading the enriched context and emitting the
`__data_classification__` / `__affected_subjects_count__` /
`__exfil_confirmed__` verdict) fills that as a private extension.
The framework-wide EU-resident LM endpoint guard re-applies the
check at process startup (`compilers/_shared/lm_endpoint_guard.py`),
with the `SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/data_exfil/`, `examples/temporal/data_exfil/`,
`examples/langgraph/data_exfil/`). The n8n target ships a committed
workflow artifact; the Temporal and LangGraph targets ship
deterministic emitter output with `NotImplementedError` activity /
tool bodies pending the per-target CORE cards. Cross-target byte-
parity goldens land under `tests/examples/data_exfil/` — the same
cross-target byte-parity property the framework relies on for the
rest of the playbook set.

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

## 7. Metrics — what the exfil response exposes

Four indicator catalogue entries surface the data_exfil posture to
the operator's metrics dashboard. The catalogue entries live under
`content/metrics/` and read against the OCSF Detection Finding /
Network Activity / Account Change / Incident Finding / Compliance
Finding records the workflow consumes and emits.

- **`kpi.mttd_exfil@v1`** — median time from egress event to the
  triage step's hydration of the reported signal. Catalogue:
  [`content/metrics/mttd_exfil.yaml`](../../content/metrics/mttd_exfil.yaml).
  Rising values indicate the DLP / egress-monitoring surface is
  drifting behind the operational objective (either the detection
  layer is slow to raise the signal or the triage step is slow to
  hydrate it).
- **`kpi.mttr_containment@v1`** — median time from triage to
  containment completion (egress-filter binding + identity cut-
  out). Catalogue:
  [`content/metrics/mttr_containment.yaml`](../../content/metrics/mttr_containment.yaml).
  Stamped by the containment step; audits on-time containment
  across the three-legged discipline (egress filter, session
  revocation, account disable).
- **`kpi.notification_sla_compliance@v1`** — share of cases whose
  regulator and customer notifications landed within the
  applicable statutory deadline in the evaluation window.
  Catalogue:
  [`content/metrics/notification_sla_compliance.yaml`](../../content/metrics/notification_sla_compliance.yaml).
  Stamped by both notification steps so the two timelines
  (regulator submission and customer / data-subject communication)
  are reported independently — the GDPR Art. 34 clock is
  distinct from the Art. 33 clock, and the DORA Art. 19 4-hour
  initial is distinct from the NIS2 Art. 23 24-hour early warning.
- **`kri.regulator_notification_overrun@v1`** — count of cases
  whose hand-off into `playbook.incident_management@v1` crossed
  the NIS2 Art. 23 24-hour, DORA Art. 19 4-hour, or GDPR Art. 33
  72-hour clock in the evaluation window. Catalogue:
  [`content/metrics/regulator_notification_overrun.yaml`](../../content/metrics/regulator_notification_overrun.yaml).
  Stamped by the notify-regulator step so the exfil surface
  surfaces overrun risk at the moment the envelope leaves it.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard
the KPI / KRI series against their own metrics backend.

## 8. Detection references — the SigmaHQ named rules

The playbook cites two upstream **SigmaHQ named rules** on its
`x_secops_ng.detection_refs` (rule ids intentionally not
fabricated; the CORE-layer detection mapping pins the stable
upstream ids once selected):

- **DLP egress alert** — a data-loss-prevention match on outbound
  content matching a classified-payload signature (regex,
  fingerprint, or ML-model hit). Attaches at the triage step as
  the originating signal.
- **Data staging archive created** — creation of an unusually large
  archive on an endpoint or file share, correlated with a
  candidate exfiltration workflow. Attaches at the triage step as
  a corroborating precursor.

Both signals attach at the triage step (`triage signal`), not at
the classifier itself: the signal identifies the case, scope
assessment reads it. See
[`content/playbooks/data_exfil/README.md`](../../content/playbooks/data_exfil/README.md)
for the rule-reference discipline (SecOps-NG does not re-author
Sigma; upstream rule ids are pinned by the CORE-layer detection
mapping) and the `detection_refs` slot on the playbook's
`x_secops_ng` extension for the outbound anchors.

## 9. Operator customisation points

The playbook is an exfil-response machine; the *policy* it
exercises is the operator's. The customisation seams:

- **DLP / egress signal sources.** The `triage signal` step reads
  the operator's DLP or egress-monitoring layer against
  `__signal_id__`. The framework binds neither the vendor nor the
  fetch API; operators wire the step to whichever DLP surface
  (managed vendor, self-hosted egress proxy, DLP agent on
  endpoints, network anomaly detector) their environment runs on.
  The two SigmaHQ named rules on `x_secops_ng.detection_refs`
  document the two upstream signal shapes; other operator
  detectors can attach at the same seam.
- **Data-classification thresholds.** The `scope assessment` step
  emits `__data_classification__` on a closed alphabet (public /
  internal / confidential / restricted / special-category). The
  mapping from raw evidence to that alphabet — which regex / fingerprint
  / ML classifier / IAM label puts a payload in which bucket — is
  operator-owned. Operators tune the classifier against their own
  data-classification baseline; the framework binds the output
  alphabet, not the classification rules.
- **Notification-recipient list.** The `notify regulator` step
  hands off along the operator's pre-bound regulator channel. Which
  authority receives which regime's submission (national CSIRT
  under NIS2, competent authority under DORA, supervisory
  authority under GDPR, market-surveillance authority under CRA)
  is per Member State and per sector, and is the operator's to
  configure at the seam. The `notify customer` step reads the
  operator's customer-comms channel and the affected-subjects list;
  the framework binds neither.
- **Affected-subjects count threshold for GDPR Art. 33 trigger.**
  The `regulator notification threshold met?` gate evaluates
  `__regulator_required__` against `__affected_subjects_count__`
  and `__data_classification__` per the operator's routing policy.
  The joint NIS2 Art. 23 / DORA Art. 19 / GDPR Art. 33 predicate
  is the routing key; the numeric cut-offs (below which the
  regulator submission does not fire) are operator-owned. GDPR
  Art. 33 has no numeric threshold — the trigger is qualitative
  ("likely to result in a risk to the rights and freedoms of
  natural persons") — but operators frequently encode a
  first-approximation numeric proxy at the gate and route the
  edge cases to human review; the framework documents the seam
  but does not prescribe the cut-off.
- **Containment surface bindings.** The containment step reads
  three independent surfaces — the egress chokepoint's deny-rule
  API, the IdP's session-invalidation and account-disable APIs,
  and the credential-rotation surface. All three are operator-
  bound; the framework binds the topology, not the vendors.
- **Regulator-submission engine.** The downstream 24-hour /
  72-hour / one-month per-stage submissions are rendered by
  `playbook.incident_management@v1` from the envelope this playbook
  emits. Operators who diverge on the submission format (per-
  regulator schema, cover-letter template, cross-border routing
  matrix) fork the submission engine, not the exfil-response
  playbook.

## 10. Replay and audit story

The byte-parity drift guards land with the CORE-TEMPORAL /
CORE-LANGGRAPH sibling cards under `tests/examples/data_exfil/`.
Each per-target golden pins the committed worked-example artifact
to a fresh emitter run from the canonical CACAO source; if the
compiler or the playbook changes, regenerate via the per-target
`regenerate.sh` and commit the diff intentionally.

The cross-target replay property is the harder one: the same case,
fed through n8n / Temporal / LangGraph, produces byte-identical
containment records *and* byte-identical regulator- and customer-
notification envelopes once each target's activity / tool bodies
are wired against the same operator seams and the same OSCAL /
OCSF / D3FEND reference bundles. The `(signal_id,
data_classification, affected_subjects_count, exfil_confirmed,
regulator_required)` key is the string a regulator can diff to
confirm the property holds across targets.

## 11. Playbook chain — where data_exfil sits

The regulator-notification chain expresses itself as three
workflows feeding one submission engine:

```
phishing_triage ─┐
                 ├─► identity_compromise ─► data_exfil ─► incident_management
alert_triage ────┘
```

- **Upstream: `phishing_triage`.** The BEC and credential-harvest
  branches on `playbook.phishing_triage@v1` escalate into
  `playbook.identity_compromise@v1` and, where exfil follows, into
  this playbook. `phishing_triage` itself is deliberately
  sub-threshold for DORA Art. 18 major-classification per the
  inbound carve-out at
  [`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml).
- **Upstream: `identity_compromise`.** Session-lineage graph,
  cross-tenant blast-radius, and deeper IdP-side audit of the
  originating principal run on `playbook.identity_compromise@v1`
  before the case escalates into data_exfil. The containment
  step on data_exfil is deliberately the *cut-out* leg (session
  revocation, account disable, credential rotation) and not the
  IdP-audit leg — the latter is upstream.
- **Downstream: `incident_management`.** The regulator-submission
  timeline itself (NIS2 Art. 23 24-hour / 72-hour / one-month,
  DORA Art. 19 4-hour / 72-hour, GDPR Art. 33 72-hour, CRA
  Art. 14(3) 24-hour / 72-hour / one-month) runs on
  `playbook.incident_management@v1`. See
  [`docs/cookbook/incident_management.md`](./incident_management.md).

The chain lets data_exfil stay narrowly focused on egress-signal
triage → scope assessment → containment → notification envelope
composition while the deep IdP-side forensics happen upstream and
the per-stage regulator submissions happen downstream. The chain
is not code-coupled — each playbook is a standalone CACAO artifact
that can be run in isolation — but the audit trail's coherence
across the four workflows is the sovereign-security property the
framework guarantees.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  DLP platform, the egress chokepoint, the IdP, the pre-bound
  regulator channel, the notify-customer gateway, or the
  case store. Connectors are operator-bound at runtime against
  environment variables documented per target.
- **Per-stage regulator submissions.** The 24-hour early warning,
  the 72-hour notification, the one-month final report (NIS2), the
  4-hour initial / 72-hour intermediate (DORA), the 72-hour
  supervisory-authority notification (GDPR Art. 33), and the CRA
  Art. 14(3) chain all run on `playbook.incident_management@v1`.
  This playbook is the upstream emitter of the structured
  incident-finding envelope; the per-stage submissions are
  downstream.
- **Deep IdP-side identity forensics.** Session-lineage graph,
  cross-tenant blast-radius, and lateral-movement reconstruction
  live on `playbook.identity_compromise@v1`. This playbook's
  containment step is the operational cut-out; the audit leg is
  upstream.
- **Product-side CRA vulnerability notification.** CRA Art. 14
  product-side vulnerability-notification obligations continue to
  run on `playbook.vuln_intake@v1`. The severe-incident
  notification leg (Art. 14(3)) at the operator-side runs through
  this playbook's regulator envelope.
- **SigmaHQ rule id pinning.** The playbook cites two upstream
  Sigma rule *names* (DLP egress alert, data staging archive
  created). Stable upstream rule ids are pinned by the CORE-layer
  detection mapping, not by this cookbook; SecOps-NG does not
  re-author Sigma.
- **OCSF DLP Activity binding.** The playbook's telemetry_refs
  cite `telemetry.ocsf.dlp_alert@v1`; the corresponding class_uid
  on OCSF v1.3.0 is deferred to a follow-up card that lands
  `content/telemetry/dlp_alert.yaml`. The Detection Finding
  binding covers the upstream carrier in the interim.

## 13. References

- [`content/playbooks/data_exfil/README.md`](../../content/playbooks/data_exfil/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/data_exfil/mappings.yaml`](../../content/playbooks/data_exfil/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay with
  per-step control anchors and the inbound-closure notes for the
  four regulatory regimes.
- [`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
  — NIS2 Article 21(2)(b) inbound anchor.
- [`content/mappings/nis2/article-23.yaml`](../../content/mappings/nis2/article-23.yaml)
  — NIS2 Article 23 inbound anchor (24-hour early warning,
  72-hour notification).
- [`content/mappings/dora/article-19-and-28.yaml`](../../content/mappings/dora/article-19-and-28.yaml)
  — DORA Articles 18 and 19 inbound anchor (major-classification,
  4-hour initial, 72-hour intermediate).
- [`content/mappings/gdpr/article-33-34-personal-data-breach-notification.yaml`](../../content/mappings/gdpr/article-33-34-personal-data-breach-notification.yaml)
  — GDPR Articles 33 and 34 personal-data-breach notification
  anchor.
- [`content/mappings/gdpr/data-flow-data_exfil.md`](../../content/mappings/gdpr/data-flow-data_exfil.md)
  — GDPR Article 30 Record of Processing Activity.
- [`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
  — CRA Article 14(3) severe-incident notification anchor.
- [`examples/n8n/data_exfil/README.md`](../../examples/n8n/data_exfil/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/data_exfil/README.md`](../../examples/temporal/data_exfil/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/data_exfil/README.md`](../../examples/langgraph/data_exfil/README.md)
  — LangGraph worked-example stub.
- [`docs/cookbook/phishing_triage.md`](./phishing_triage.md)
  — upstream cookbook (BEC and credential-harvest branches).
- [`docs/cookbook/incident_management.md`](./incident_management.md)
  — downstream cookbook (per-stage regulator-submission engine).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
