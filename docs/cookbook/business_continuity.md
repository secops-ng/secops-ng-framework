# business_continuity — cookbook walkthrough

Event-driven business-continuity plan-lifecycle under NIS2
Article 21(2)(c), with Article 23 significant-incident notification to
the competent authority and DORA Article 11 response-and-recovery
alignment. The `playbook.business_continuity@v1` CACAO playbook is the
operator-side plan-lifecycle materialisation of the NIS2 Art. 21(2)(c)
business-continuity obligation: on declaration of a business-continuity
event (major outage, ransomware-containment escalation, upstream
dependency failure, facility loss), it activates the operator's
documented BCM plan artifact, isolates the affected surface where the
plan calls for it, fails the service over to the documented backup
site / data replica / standby capacity, dispatches the Art. 23 24h /
72h / one-month cascade to the competent authority where the event
crosses the significant-incident threshold, restores the primary
service against the documented recovery objectives (RTO / RPO), and
persists the post-incident-review record.

The playbook is the plan-lifecycle sibling of the
[`backup_recovery`](backup_recovery.md) restore-drill playbook: both
overlays anchor `nis2:art-21-2-c` and together cover the backup +
disaster-recovery + crisis-management triplet the clause names.
`backup_recovery` pins the periodic non-destructive drill lane
(continuous evidence the apparatus remains exercisable); this playbook
pins the event-driven lane (what the drill was preparing for).

Production state is untouched by the framework itself — every
operator-bound seam (BCM-plan store, isolation surface, failover
surface, competent-authority notification transport, health-signal
probe, evidence store) is a runtime seam the operator wires against
their own infrastructure. The failover targets, isolation targets, and
recovery objectives the workflow reads all live in the operator's
documented BCM plan artifact, which the framework references but does
not author.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the BCM-plan
resolution, the significance-threshold outcome, the Art. 23
notification envelope, and the recovery-and-verification result flow
in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/business_continuity/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / GDPR overlay
└── playbook.cacao.yaml          # canonical CACAO v2 source (playbook.business_continuity@v1)

content/mappings/nis2/article-21-2-c.yaml
                                  # NIS2 Art. 21(2)(c) inbound anchor — backlinks
                                  # playbook.business_continuity@v1 on `playbook_refs`
                                  # alongside the sibling playbook.backup_recovery@v1
content/mappings/dora/article-11.yaml
                                  # DORA Art. 11 response-and-recovery inbound anchor
content/mappings/gdpr/article-32-security-of-processing.yaml
                                  # GDPR Art. 32(1)(c) restore-availability inbound anchor
```

The CACAO source is canonical. The seven action steps are the
deterministic policy the playbook *means* — a linear chain through
detection, activation, isolation, failover, notification, restoration,
and post-incident review, with the significance-threshold outcome
routing the notify step between the Art. 23 dispatch envelope and a
locally-logged no-notification record. The three worked examples under
`examples/{n8n,temporal,langgraph}/business_continuity/` are the same
playbook compiled into three orchestrator idioms. Everything else — the
BCM-plan store, the isolation surface, the failover surface, the
competent-authority delivery transport, the health-signal probe, the
evidence store — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships nine steps: one `start`, seven `action`, one `end`.
The chain is linear on the workflow edges; the deterministic branch on
the Art. 23 significant-incident threshold lives *inside* the
`notify-competent-authority` action rather than on a CACAO
`if-condition` node, so the workflow topology stays a single audit
lane regardless of significance outcome. Both branches emit a record —
the Art. 23 envelope on `true`, a locally-logged no-notification
determination on `false` — so accountability is preserved either way.

| Step suffix | Step                          | Discipline                                                                                     | Status         |
|-------------|-------------------------------|-------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | start (`bcm_start`)           | edge wiring only — no body                                                                     | n/a            |
| `…000002`   | detect-and-declare-bcm-event  | event ingestion from the operator's declaration surface; assigns `__event_id__` and stamps `__event_declared_ts__` against the Art. 23 clock | operator-bound |
| `…000003`   | activate-bcm-plan             | BCM-plan retrieval + significance-threshold evaluation (`__bcm_plan_ref__`, `__significant_incident__`) | operator-bound |
| `…000004`   | isolate-affected-systems      | containment of the failure surface per the activated plan (`__isolation_scope__`, empty when the plan documents no isolation for the event class) | operator-bound |
| `…000005`   | switch-to-backup              | failover to the documented backup site / data replica / standby capacity (`__failover_target__`) | operator-bound |
| `…000006`   | notify-competent-authority    | Art. 23 24h / 72h / one-month cascade dispatch (or locally-logged no-notification determination); records `__notification_ref__` | operator-bound |
| `…000007`   | restore-and-verify            | cutback from the failover target, dependency revalidation, health-signal check, observed RTO / RPO recorded (`__recovery_result__`) | operator-bound |
| `…000008`   | post-incident-review          | lessons-learned + BCM-plan revision record persisted to the evidence store (`__pir_ref__`)     | operator-bound |
| `…00000a`   | end (`bcm_end`)               | edge wiring only — no body                                                                     | n/a            |

All seven action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control, telemetry).
One per-event execution emits exactly one post-incident-review record;
the significance branch inside `notify-competent-authority` never
creates a parallel evidence lane — one event, one PIR, one
notification decision recorded.

> The playbook status is SKELETON on the workflow-local README (this
> EXTEND card lands with the cookbook walkthrough). All three
> reference emitters ship committed artifacts under
> `examples/{n8n,temporal,langgraph}/business_continuity/` with
> deterministic stubs for the operator-bound seams; a sibling CORE
> revisit lands the full adapter bindings (BCM-plan store,
> significance-threshold evaluator, per-Member-State competent-
> authority delivery surface, Art. 23 envelope templates).

## 3. Lifecycle contract — the seven states

The event payload — event id, declaration timestamp, BCM plan
reference, isolation scope, failover target, significance flag,
notification reference, recovery result, PIR reference — is
continuity-control content. Where the affected service processes
personal data, GDPR Art. 32(1)(c) attaches as a parallel obligation
surface (see § 4). The framework treats `__event_id__`,
`__bcm_plan_ref__`, `__isolation_scope__`, `__failover_target__`,
`__notification_ref__`, `__recovery_result__`, and `__pir_ref__` as
opaque operator-assigned identifiers.

**detect-and-declare-bcm-event** (`…000002`)
:   Event-ingestion step. Receives a business-continuity trigger on
    the operator's declared event-declaration surface — a major-outage
    escalation from the incident-management lane, a ransomware
    containment escalation from the containment lane, an
    upstream-dependency failure signal, or a facility-loss
    declaration. Assigns `__event_id__` and stamps
    `__event_declared_ts__` against the NIS2 Art. 23 clock. Anchored
    on OSCAL CP-2 (Contingency Plan) as the plan-activation
    envelope's declaration lane. Deliberately not pinned to a D3FEND
    technique: declaration is a coordination-surface read, not a
    runtime countermeasure.

**activate-bcm-plan** (`…000003`)
:   Plan-activation step. Retrieves the documented BCM plan artifact
    for the affected service from the operator's BCM-plan store and
    activates it. Reads the documented isolation targets, failover
    targets, and recovery objectives (RTO / RPO) into workflow state
    (`__bcm_plan_ref__`). Evaluates the event against the operator's
    declared significance-threshold policy and sets
    `__significant_incident__` as the audit-evident boolean the
    notify step reads. Anchored on OSCAL CP-2 (Contingency Plan) —
    the same control the sibling `on_call_rotation` overlay pins on
    its per-shift responder-identification slice.

**isolate-affected-systems** (`…000004`)
:   Containment step. Where the event class and the activated plan
    call for it, contains the failure surface by isolating the
    affected primary systems, network segments, or upstream
    dependencies against the operator's isolation surface per
    `__bcm_plan_ref__`. Records `__isolation_scope__` for the
    downstream cutback discipline. Skipped (empty
    `__isolation_scope__`) where the plan documents no isolation step
    for the event class — a pure availability outage with no
    compromise indicator, for example. Anchored on OSCAL CP-2 as the
    plan-directed containment leg; deliberately not pinned to a
    D3FEND isolation technique at SKELETON — the containment surface
    the plan directs into is operator-defined and the sibling
    `ransomware_containment` overlay already pins the compromise-
    indicator isolation lane.

**switch-to-backup** (`…000005`)
:   Failover step. Executes the failover of the affected service to
    the documented backup site, data replica, or standby capacity per
    `__bcm_plan_ref__`. Records `__failover_target__` for the
    downstream cutback validation. The failover is the
    disaster-recovery leg of the Art. 21(2)(c) triplet — the periodic
    exercise that the failover integrity depends on lives on the
    sibling `backup_recovery` overlay's drill lane, so the two
    overlays stay separately anchored on the same clause without
    cross-pinning. Anchored on OSCAL CP-10 (System Recovery and
    Reconstitution).

**notify-competent-authority** (`…000006`)
:   Notification step. Where `__significant_incident__` is `true`,
    dispatches the NIS2 Art. 23 significant-incident notification to
    the operator's competent authority (the national cybersecurity
    authority per the entity's Member State of establishment) on the
    Art. 23 timeline: 24-hour early warning, 72-hour incident
    notification, one-month final report. The envelope carries
    `__event_id__`, `__event_declared_ts__`, the preliminary
    assessment, the impact scope, and the cross-border-effect
    indicator. Where `__significant_incident__` is `false`, records a
    locally-logged no-notification determination for accountability
    and short-circuits into `restore-and-verify` without emitting an
    Art. 23 envelope. Records `__notification_ref__`. Anchored on
    OSCAL IR-6 (Incident Reporting) — IR-6's
    organisation-defined-time-periods discipline is exactly the
    sector-specific 24h / 72h / one-month cascade the Art. 23 path
    ships.

**restore-and-verify** (`…000007`)
:   Recovery-and-verification step. Returns the primary service to a
    known-good state per `__bcm_plan_ref__`: cutback from
    `__failover_target__` where applicable, dependency revalidation,
    and a health-signal check against the documented recovery
    objectives. Records `__recovery_result__` with the observed
    RTO / RPO delta against the documented objectives and the
    primary-service health signal. Anchored on OSCAL CP-10 (System
    Recovery and Reconstitution) and on MITRE D3FEND v1.0.0 `D3-SRA`
    (System Recovery Analysis) — the same technique the sibling
    `backup_recovery` overlay pins on its periodic drill lane,
    applied here to the event-driven envelope rather than the
    scheduled-exercise envelope. D3FEND frames System Recovery
    Analysis as the analysis of system recovery from a known-good
    state; the playbook narrows that lens to the operator's
    event-driven recovery envelope with the observed RTO / RPO
    recorded on the cutback outcome.

**post-incident-review** (`…000008`)
:   PIR-emission step. Persists the post-incident-review record for
    the event: lessons learned, corrective actions, and any BCM-plan
    revisions surfaced by the event. Records `__pir_ref__` on the
    operator's evidence store keyed to `__event_id__`. Feeds the
    operator's accountability posture and any downstream regulator
    query — the Art. 23 final-report supplement or an Art. 32
    supervisory-authority information request. Anchored on OSCAL
    CP-2 as the plan-review discharge for the event; deliberately
    not pinned to a D3FEND technique — PIR emission is an
    attestation-stream discipline, mirroring the same gap-note
    precedent used on `backup_recovery`'s evidence-capture step and
    on the `crypto_posture_management` / `iam_auditor` /
    `on_call_rotation` overlays.

The seven action states are operator-bound runtime seams: the
framework ships neither the event-declaration surface, the BCM-plan
store, the isolation surface, the failover surface, the
competent-authority delivery transport, the health-signal probe, nor
the evidence store. The playbook is the portable description of
*what* the operator's stack should do on each declared event; binding
those seams to real endpoints is the operator's job.

> **LM determinism.** Event ingestion, plan retrieval, isolation
> execution, failover execution, notification dispatch, recovery
> verification, and PIR persistence are structured reads and writes
> against operator-owned surfaces, not free-text reasoning steps. The
> playbook binds no DSPy signature — there is no LM-driven step at
> this layer. See [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM
> determinism. If an operator wires an LM-driven summariser on top of
> the Art. 23 preliminary-assessment field or the PIR narrative (a
> private, forward-looking extension), the framework-wide EU-resident
> LM endpoint guard re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(c)** — business continuity, backup management,
disaster recovery, and crisis management. The clause requires essential
and important entities to operate business-continuity arrangements
covering the full triplet (backup + disaster recovery + crisis
management). The `business_continuity` playbook is the plan-lifecycle
materialisation of that obligation: the event declaration, the
activation of the documented BCM plan, the isolation of the affected
surface, the failover to the documented backup capacity, the recovery
cutback against the documented objectives, and the PIR record are the
audit-evident discharge of the plan-lifecycle side of the clause. The
sibling `backup_recovery` playbook discharges the drill-lane side.
Inbound anchor at
[`content/mappings/nis2/article-21-2-c.yaml`](../../content/mappings/nis2/article-21-2-c.yaml)
(`nis2:art-21-2-c`) backlinks `playbook.business_continuity@v1` on
`playbook_refs` alongside `playbook.backup_recovery@v1`.

**NIS2 Article 23** — significant-incident reporting to the competent
authority. The 24h early-warning / 72h incident-notification /
one-month final-report cascade is dispatched from the
`notify-competent-authority` step when the event crosses the
operator's declared significance-threshold policy. The competent
authority varies by Member State of establishment and the delivery
surface (portal, S/MIME email, sector-specific API) is the operator's
choice — the framework ships the envelope shape and the timing
schedule; the operator owns the wire. Per-Member-State competent-
authority delivery adapters are a sibling EXTEND card once the
per-authority delivery surfaces stabilise.

**DORA Article 11** — response and recovery, RTO / RPO objectives,
and activation of the response-and-recovery plan. The clause requires
financial entities to put in place a response-and-recovery plan that
specifies RTO / RPO objectives, identifies the actions to be taken
during and after an ICT-related incident, and provides for the
periodic testing of that plan. The `business_continuity` playbook is
the plan-lifecycle materialisation of that obligation on the
operator's event-driven envelope: the `activate-bcm-plan` step reads
the documented plan and the `restore-and-verify` step records the
observed RTO / RPO delta against the documented objectives. Inbound
anchor at
[`content/mappings/dora/article-11.yaml`](../../content/mappings/dora/article-11.yaml)
(`dora:art-11-response-recovery`) closes the graph. The periodic
testing leg (DORA Art. 12) is anchored on the sibling
`backup_recovery` overlay's drill lane, so the two overlays stay
atom-per-obligation without cross-pinning.

**GDPR Article 32(1)(c)** — ability to restore the availability of,
and access to, personal data in a timely manner in the event of a
physical or technical incident. Where the affected service under this
lifecycle processes personal data, the failover to
`__failover_target__` and the cutback validation captured into
`__recovery_result__` are the technical-measure discharge of that
obligation on the plan-lifecycle side; the sibling `backup_recovery`
overlay discharges the periodic-testing leg on Art. 32(1)(d). The
observed RTO / RPO delta against the documented objectives is the
"timely manner" audit-evident signal. Inbound anchor at
[`content/mappings/gdpr/article-32-security-of-processing.yaml`](../../content/mappings/gdpr/article-32-security-of-processing.yaml)
(`gdpr:art-32-1-c-restore-availability`).

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/business_continuity/mappings.yaml`](../../content/playbooks/business_continuity/mappings.yaml)):
CP-2 (Contingency Plan — anchors `detect-and-declare-bcm-event`,
`activate-bcm-plan`, `isolate-affected-systems`, and
`post-incident-review`), CP-10 (System Recovery and Reconstitution —
anchors `switch-to-backup` and `restore-and-verify`), IR-6 (Incident
Reporting — anchors `notify-competent-authority`). CP-9 (System
Backup) is deliberately not pinned here — the backup-management leg
of Art. 21(2)(c) lives on the sibling `backup_recovery` overlay, so
the two overlays cover the triplet without cross-pinning the same
control on both. The in-line note at the top of `mappings.yaml`
documents each omission.

**MITRE D3FEND v1.0.0** — `D3-SRA` (System Recovery Analysis) at
`restore-and-verify`. The declaration, activation, isolation,
failover, notify, and PIR steps are deliberately not pinned to a
D3FEND technique at SKELETON tier because D3FEND v1.0.0 frames its
defensive techniques around runtime countermeasures against adversary
behaviours; coordination-surface reads, plan-activation flows,
notification cascades, and PIR emission are anchored on the OSCAL
controls above instead. The in-line gap notes in `mappings.yaml`
document each deliberate absence, mirroring the `backup_recovery`,
`crypto_posture_management`, `infra_posture_management`,
`iam_auditor`, and `on_call_rotation` precedents.

**OCSF v1.3.0** — two event classes across the seven action steps.
`HTTP Activity` (class_uid 4004, category 4 Network Activity),
direction `emits`, at `detect-and-declare-bcm-event`,
`activate-bcm-plan`, `isolate-affected-systems`, `switch-to-backup`,
and `restore-and-verify`: one availability-activity record per
milestone keyed to `__event_id__` so the operator's availability-
management surface and the observed RTO / RPO delta against the
documented objectives can be computed and audited from the emitted
telemetry alone. `Incident Finding` (class_uid 2005, category 2
Findings), direction `emits`, at `notify-competent-authority` and
`post-incident-review`: one incident-finding record per notification
and per PIR milestone keyed to `__event_id__`, with the
on-time-vs-deadline delta feeding the operator's Art. 23 timeliness
posture. The class_uid 4004 binding is intentional at SKELETON tier
— HTTP Activity is the OCSF v1.3.0 network-activity class the
reference wiring emits; a sibling CORE card revisits the class
selection if a more specific availability class lands in a future
OCSF release.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the lifecycle topology

`examples/n8n/business_continuity/workflow.n8n.json` carries the
CACAO topology as nine n8n nodes (one `manualTrigger`, seven `set`
nodes, one `noOp`), with node ids preserving the CACAO step ids
verbatim. The seven action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles. The Art. 23 significance branch lives
inside the `notify-competent-authority` Set row rather than a
`n8n-nodes-base.if` node — the row's assignments carry both the
significance-true dispatch fields and the significance-false
no-notification determination fields so the operator wires whichever
branch their significance-threshold policy exercises against the
`__significant_incident__` field. The lossy translation is recorded
in `meta.secops_ng_notes` so the integrator sees exactly which seams
need attention.

Operators bind the Set rows to their connectors:

- `detect and declare bcm event` → the operator's event-declaration
  surface (webhook or upstream orchestrator escalation from the
  incident-management or ransomware-containment lane); the Set row
  records `__event_id__` and `__event_declared_ts__`.
- `activate bcm plan` → the operator's BCM-plan store (documented
  plan artifact + significance-threshold policy); the Set row records
  `__bcm_plan_ref__` and `__significant_incident__`.
- `isolate affected systems` → the operator's isolation surface
  (network-segmentation controller, IAM revocation surface, upstream
  dependency circuit-breaker); the Set row records
  `__isolation_scope__`.
- `switch to backup` → the operator's failover surface (backup site
  routing, data-replica promotion, standby-capacity activation); the
  Set row records `__failover_target__`.
- `notify competent authority` → the operator's competent-authority
  delivery transport (per-Member-State portal, S/MIME email,
  sector-specific API); the Set row records `__notification_ref__`.
- `restore and verify` → the operator's health-signal probe and
  cutback discipline; the Set row records `__recovery_result__`.
- `post incident review` → the operator's evidence store (retention
  discipline documented in the operator's governance surface); the
  Set row records `__pir_ref__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/business_continuity/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/business_continuity/workflow.n8n.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/business_continuity/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the seven action
activities documenting their operator-bound seam (event ingestion,
plan retrieval, isolation execution, failover execution, notification
dispatch, recovery verification, PIR persistence). The committed stub
raises `NotImplementedError` in the activity bodies pending the
CORE-TEMPORAL sibling card that wires the deterministic activity
implementations into the Temporal target; operators can drop the
module next to their worker today to see the topology and the activity
signatures.

Temporal is the natural fit for the plan-lifecycle discipline: each
declared event becomes one workflow run; the Art. 23 24h / 72h /
one-month cascade becomes three Temporal timers on the same workflow;
retries against transient failures on the failover activity or the
notification transport get first-class Temporal semantics (activity
retry policy against the operator-bound surface); replay against the
same Temporal event history re-derives the same PIR payload once the
activity bodies are wired. The workflow code the compiler emits stays
pure — every non-deterministic boundary lives on the activity side of
the `@activity.defn` line, so replay determinism survives the
operator's own activity implementations.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/business_continuity/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes, linear
edges through the seven action states, and the internal
significance-branch inside `notify-competent-authority` recorded as a
state field rather than a conditional edge); `assemble.py` is the
hand-written reference assembly that wires the GraphSpec + bindings
into a `langgraph.graph.StateGraph`. The committed `state_bindings.py`
is a generated stub: each tool's docstring names the operator-bound
seam it discharges and the body raises `NotImplementedError` until
the CORE-LANGGRAPH sibling card wires the deterministic tool
implementations into the LangGraph target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven summariser on top of the Art. 23 preliminary-assessment
composition step or the PIR narrative fills that as a private
extension. The framework-wide EU-resident LM endpoint guard re-applies
the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/business_continuity/`,
`examples/temporal/business_continuity/`,
`examples/langgraph/business_continuity/`). The n8n target ships a
committed workflow artifact; the Temporal and LangGraph targets ship
deterministic emitter output with `NotImplementedError` activity /
tool bodies pending the per-target CORE cards. The per-target
byte-parity goldens under `tests/examples/{n8n,temporal,langgraph}/business_continuity/`
pin each per-target artifact against a fresh emitter run from the
canonical CACAO source — the cross-target byte-parity property the
framework relies on.

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
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--b17c0072-…`).          |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--b17c0072-…`).                |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
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

The audit envelope carried per action step names the seven operator-
bound seams explicitly: the event-declaration record on step 002, the
BCM-plan reference and significance-threshold outcome on step 003,
the isolation-scope reference (or empty marker) on step 004, the
failover-target reference on step 005, the Art. 23 notification
reference (or the no-notification determination marker) on step 006,
the recovery-result payload with the observed RTO / RPO delta on step
007, and the PIR reference on step 008. The `__event_id__` correlation
key threads through every record so a reviewer can join the full
continuity lifecycle into a single reportable-event ledger.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default and
never imports a vendor SDK; pointing the exporter at a managed APM is
a downstream choice the operator owns end-to-end. The sovereignty
posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Operator customisation points

The playbook is a plan-lifecycle machine; the *policy* it activates
is the operator's. The customisation seams:

- **BCM-plan artifact location.** The `activate-bcm-plan` step reads
  the documented plan artifact for the affected service from the
  operator's BCM-plan store — a document management system, an
  object store, a governance-tooling API, or a filesystem path
  under the operator's own configuration control. The framework
  binds neither the store nor the plan-artifact schema; the CORE
  sibling card lands the plan-artifact schema as an adapter Protocol
  operators implement against their store.
- **Significance-threshold policy.** The `activate-bcm-plan` step
  evaluates the event against the operator's declared
  significance-threshold policy and sets `__significant_incident__`.
  The threshold is entity-specific and sector-specific under NIS2
  Art. 23 (essential vs important entity, sector-specific impact
  criteria); the framework does not prescribe the threshold. The
  CORE sibling card lands the significance-threshold evaluator as an
  adapter Protocol operators implement against their declared policy.
- **Isolation surface.** The `isolate-affected-systems` step calls
  the operator's isolation surface per the activated plan. Network-
  segmentation controller, IAM revocation surface, upstream
  dependency circuit-breaker, or a combination — the framework binds
  neither the surface shape nor the isolation-scope schema. Skipping
  isolation (empty `__isolation_scope__`) is a documented plan
  outcome for event classes that call for no containment.
- **Failover surface.** The `switch-to-backup` step fails the
  service over to the documented backup site, data replica, or
  standby capacity per the activated plan. The framework binds
  neither the failover-surface shape nor the recovery-objective
  evaluator (observed vs documented RTO / RPO); operators wire the
  failover to whichever backup capacity their BCM plan documents.
- **Competent-authority notification endpoint.** The
  `notify-competent-authority` step dispatches the Art. 23 envelope
  to the operator's competent authority — the national cybersecurity
  authority per the entity's Member State of establishment. The
  delivery surface varies (portal, S/MIME email, sector-specific
  API); the framework ships the envelope shape and the
  24h / 72h / one-month cascade timing, the operator owns the wire.
  Per-Member-State delivery adapters land on a sibling EXTEND card
  once the per-authority delivery surfaces stabilise.
- **Health-signal probe.** The `restore-and-verify` step calls the
  operator's health-signal probe as part of the cutback discipline.
  The probe shape (synthetic transaction, dependency ping, upstream
  SLA readback) is operator-defined; the framework records the
  observed RTO / RPO delta and the health-signal outcome into
  `__recovery_result__`.
- **Evidence-store retention.** The `post-incident-review` step
  persists the PIR record to the operator's evidence store. The
  retention discipline (per-record TTL, immutability posture,
  regulator-query response SLA) is operator-defined and documented
  in the operator's governance surface upstream of this workflow.

## 8. Replay and audit story

The byte-parity drift guards land under
`tests/examples/{n8n,temporal,langgraph}/business_continuity/`. Each
per-target golden pins the committed worked-example artifact to a
fresh emitter run from the canonical CACAO source; if the compiler
or the playbook changes, regenerate via the per-target
`regenerate.sh` and commit the diff intentionally.

The cross-target replay property is the harder one: the same declared
event, fed through n8n / Temporal / LangGraph, produces a
byte-identical PIR record and a byte-identical Art. 23 notification
envelope once each target's activity / tool bodies are wired against
the same operator seams and the same OSCAL / OCSF / D3FEND reference
bundles. The `(event_id, event_declared_ts, notification_ref,
pir_ref)` tuple is the string a regulator can diff to confirm the
property holds across targets, and the `__event_id__` correlation key
is the join column that threads through every audit record from
declaration to PIR.

## 9. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  BCM-plan store, the isolation surface, the failover surface, the
  competent-authority delivery transport, the health-signal probe, or
  the evidence store. Connectors are operator-bound at runtime
  against environment variables documented per target.
- **BCM-plan authorship.** The playbook operationalises a documented
  BCM plan; it does not author one. Plan scope, isolation targets,
  failover targets, and recovery objectives (RTO / RPO) all live in
  the operator's governance documentation upstream of this workflow.
- **Significance-threshold policy authorship.** The significance-
  threshold policy the `activate-bcm-plan` step reads is
  entity-specific and sector-specific under NIS2 Art. 23; the
  framework does not prescribe it.
- **Per-Member-State competent-authority delivery adapters.** The
  Art. 23 envelope shape and the 24h / 72h / one-month cascade timing
  ship at SKELETON; per-Member-State delivery adapters (per-authority
  portal, S/MIME email, sector-specific API) land on a sibling EXTEND
  card once the per-authority delivery surfaces stabilise.
- **Cutback-misconfiguration detection.** Detection bindings for
  cutback misconfiguration (partial cutback, health-signal
  false-positive on the restored primary) are owned by a sibling
  EXTEND card once stable upstream rule ids are selected.
- **CRA parallel obligation.** CRA Annex I §1(h) frames availability
  of essential and basic functions in a product-security
  (manufacturer-side) context; NIS2 Art. 21(2)(c) is an operator-side
  essential/important-entity obligation surface. Cross-pinning the
  plan-lifecycle to the CRA anchor would misrepresent the scope; the
  drill-lane CRA anchor is already pinned on the sibling
  `backup_recovery` overlay
  (`cra:annex-i-1-h-availability-restore-drill`).

## 10. References

- [`content/playbooks/business_continuity/README.md`](../../content/playbooks/business_continuity/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/business_continuity/mappings.yaml`](../../content/playbooks/business_continuity/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / GDPR overlay with
  per-step control anchors and the in-line closure notes for the
  deliberate OSCAL / D3FEND / CRA omissions.
- [`content/mappings/nis2/article-21-2-c.yaml`](../../content/mappings/nis2/article-21-2-c.yaml)
  — NIS2 Article 21(2)(c) inbound anchor (co-anchored with the
  sibling `backup_recovery` playbook).
- [`content/mappings/dora/article-11.yaml`](../../content/mappings/dora/article-11.yaml)
  — DORA Article 11 response-and-recovery inbound anchor.
- [`content/mappings/gdpr/article-32-security-of-processing.yaml`](../../content/mappings/gdpr/article-32-security-of-processing.yaml)
  — GDPR Article 32(1)(c) restore-availability inbound anchor.
- [`docs/cookbook/backup_recovery.md`](backup_recovery.md)
  — sibling restore-drill cookbook (periodic exercise-lifecycle
  lane; both anchor NIS2 Art. 21(2)(c)).
- [`examples/n8n/business_continuity/README.md`](../../examples/n8n/business_continuity/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/business_continuity/README.md`](../../examples/temporal/business_continuity/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/business_continuity/README.md`](../../examples/langgraph/business_continuity/README.md)
  — LangGraph worked-example stub.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
