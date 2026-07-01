# backup_recovery — cookbook walkthrough

Business-continuity restore-drill workflow under NIS2 Article 21(2)(c),
DORA Article 12, and CRA Annex I §1(h). The
`playbook.backup_recovery@v1` CACAO playbook exercises the operator's
own backup and recovery surface on a scheduled or operator-initiated
drill window: it resolves the candidate backup artifact, validates the
integrity of that artifact against the operator's documented
integrity baseline, executes a non-destructive restore drill against
the operator's documented isolated drill target, captures a dated
attestation and drill-evidence record, and delivers the attestation
reference to the continuity owner along the operator's pre-bound
channel. The playbook is the operationalisation of a backup policy
that lives in the operator's governance documentation; it does not
author the policy itself.

Production state is untouched by construction — the integrity check
is read-only and side-effect-free, and the restore drill lands against
an isolated target rather than a production system. A failed
integrity check short-circuits the drill into a failure-attestation
branch without executing the restore against potentially-corrupt
data.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the
integrity-check outcome, the drill-result payload, and the dated
attestation flow in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/backup_recovery/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.backup_recovery@v1)

content/mappings/nis2/article-21-2-c.yaml
                                  # NIS2 Art. 21(2)(c) inbound anchor — backlinks
                                  # playbook.backup_recovery@v1 on `playbook_refs`
content/mappings/dora/article-12.yaml
                                  # DORA Art. 12 inbound anchor (restoration and
                                  # recovery procedures with periodic testing)
content/mappings/cra/annex-i-1-h-availability-restore-drill.yaml
                                  # CRA Annex I §1(h) restore-drill-lane inbound anchor
content/mappings/gdpr/data-flow-backup_recovery.md
                                  # GDPR data-flow record — SKELETON declares the workflow
                                  # out of scope for personal-data processing at this layer
```

The CACAO source is canonical. The five action steps are the
deterministic policy the playbook *means* — a two-lane branch on the
integrity-check outcome, then a linear evidence-and-notify chain. The
three worked examples under `examples/{n8n,temporal,langgraph}/backup_recovery/`
are the same playbook compiled into three orchestrator idioms.
Everything else — the scheduler, the backup store, the
key-management surface, the isolated drill target, the evidence store,
the continuity-owner notification channel — is the operator's data
plane.

## 2. CACAO topology and lifecycle binding

The playbook ships eight steps: one `start`, five `action`, one
`if-condition`, one `end`. The single conditional branch fires on the
integrity-check outcome — a `true` reading routes into the restore
drill; a `false` reading short-circuits directly to evidence capture
with a failure-attestation payload.

| Step suffix | Step                          | Discipline                                                                                    | Status         |
|-------------|-------------------------------|------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | start                         | edge wiring only — no body                                                                    | n/a            |
| `…000002`   | detect-restore-drill-trigger  | scheduler / operator-trigger resolution against the backup-scope catalogue (`__candidate_backup_id__`) | operator-bound |
| `…000003`   | validate-backup-integrity     | checksum / manifest verification against the documented integrity baseline (`__integrity_ok__`) | operator-bound |
| `…000004`   | backup integrity ok?          | `if-condition` — branches on `__integrity_ok__`                                               | n/a            |
| `…000005`   | execute-restore-drill         | non-destructive restore against the isolated drill target with observed RTO / RPO (`__drill_result__`) | operator-bound |
| `…000006`   | evidence-capture              | dated attestation + drill-evidence record to the operator's evidence store (`__attestation_id__`) | operator-bound |
| `…000007`   | notify-continuity-owner       | delivery of the attestation reference to the continuity owner along the operator's pre-bound channel | operator-bound |
| `…000008`   | end                           | edge wiring only — no body                                                                    | n/a            |

All five action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control, telemetry,
metric). One per-drill execution emits exactly one attestation record;
the failure-branch attestation carries the same schema shape as the
success-branch attestation, with the drill-result marker distinguishing
"integrity check failed, drill not executed" from "drill executed,
observed RTO / RPO recorded".

> The playbook status is SKELETON on the workflow-local README: the
> control and regulatory overlay is pinned in `mappings.yaml`, the
> n8n reference emitter ships a committed `workflow.n8n.json` today,
> and the Temporal / LangGraph siblings ship deterministic emitter
> output with `NotImplementedError` activity / tool bodies pending
> the per-target CORE cards. Cross-target byte-parity goldens land
> under `tests/examples/backup_recovery/` in the same wave.

## 3. Lifecycle contract — the five states

The drill payload — candidate backup id, integrity-check outcome,
drill result, attestation id, backup-scope reference — is
continuity-control content, not personal data of a natural person.
The inbound GDPR data-flow record at
[`content/mappings/gdpr/data-flow-backup_recovery.md`](../../content/mappings/gdpr/data-flow-backup_recovery.md)
declares this workflow **out of scope** for GDPR processing at this
layer; the framework treats `__candidate_backup_id__`,
`__backup_scope__`, and `__attestation_id__` as opaque
operator-assigned identifiers. If a documented drill scope is later
extended to include personal-data restoration, a sibling GDPR
data-flow overlay lands per the schema convention used by the other
workflows.

**detect-restore-drill-trigger** (`…000002`)
:   Trigger-resolution step. Reads the operator's scheduler and
    backup-scope catalogue to decide whether a drill window matured
    (cron / Temporal schedule) or an operator-initiated drill request
    landed, and selects `__candidate_backup_id__` — the most recent
    in-scope backup artifact against the resolved `__backup_scope__`.
    Anchored on OSCAL CP-9 (System Backup) — CP-9 pins the
    backup-scope-resolution obligation the trigger reads against.
    Deliberately not pinned to a D3FEND technique: trigger resolution
    is a scheduling-surface read *upstream* of the dated-examination
    discipline, not the examination itself.

**validate-backup-integrity** (`…000003`)
:   Integrity-check step. Runs the documented integrity checks on
    the candidate backup — checksum / manifest verification,
    decryption-key availability against the operator's key-management
    surface, and a presence check against the documented backup-scope
    inventory (no silently-dropped objects). Sets `__integrity_ok__`
    as the audit-evident boolean the branch reads. A `false` outcome
    short-circuits into the evidence-capture failure branch without
    executing the restore against potentially-corrupt data. Anchored
    on OSCAL CP-9 and on MITRE D3FEND v1.0.0 `D3-FH` (File Hashing) —
    the per-artifact integrity-verification discipline narrowed to
    the operator's own backup artifacts and the operator's own
    documented integrity baseline. The same technique anchors the
    verify-backup-snapshot step on the sibling `ransomware_containment`
    overlay, so the discipline is named consistently across both
    halves of the operator's continuity surface. Feeds
    `kri.backup_integrity_failures@v1` (count of false outcomes) and
    `kpi.backup_integrity_pass_rate@v1` (pass rate across the
    evaluation window).

**backup integrity ok?** (`…000004`, `if-condition`)
:   Deterministic branch on `__integrity_ok__`. `true` routes into
    `execute-restore-drill`; `false` routes directly to
    `evidence-capture` with the failure marker attached to the
    attestation record. The condition is lossless: whichever branch
    runs, the evidence-capture step emits an attestation record
    covering the drill window.

**execute-restore-drill** (`…000005`)
:   Restore-exercise step. Executes the non-destructive restore of
    the in-scope objects from `__candidate_backup_id__` against the
    operator's documented isolated drill target (not production).
    Records the observed RTO / RPO against the documented objectives
    and captures the restored-object inventory into
    `__drill_result__`. Anchored on OSCAL CP-10 (System Recovery and
    Reconstitution) and on MITRE D3FEND v1.0.0 `D3-SRA` (System
    Recovery Analysis) — the periodic non-destructive
    restore-exercise discipline narrowed to the operator's own
    backup artifacts and the operator's own documented drill target.
    The restore is non-destructive by construction; production state
    is untouched. Feeds `kpi.restore_drill_cadence@v1` (share of
    in-scope scopes exercised within the documented cadence) and
    `kri.restore_drill_rto_overrun@v1` (count of drills whose
    observed recovery time exceeded the documented RTO objective).

**evidence-capture** (`…000006`)
:   Attestation-emission step. Composes and publishes the dated
    attestation + drill-evidence record to the operator's evidence
    store. The record carries the candidate backup id, the
    integrity-check outcome, the executed drill result (or the
    failure marker for the short-circuit branch), observed RTO / RPO,
    the restored-object inventory, and the drill-window reference,
    returning `__attestation_id__`. Anchored on OSCAL CP-9 and CP-10
    as the audit-evident record CP-9(1) (Testing for Reliability and
    Integrity) reviewers read. Deliberately not pinned to a D3FEND
    technique: evidence emission is an attestation-stream discipline,
    not a runtime countermeasure or a detection step; forcing it onto
    a D3FEND tag would misrepresent the technique. Mirrors the same
    per-step pin-where-it-fits / document-the-gap pattern used on
    `crypto_posture_management`, `infra_posture_management`,
    `iam_auditor`, and `on_call_rotation`. Feeds
    `kpi.restore_drill_attestation_freshness@v1` (share of in-scope
    scopes whose most-recent attestation is fresh against the
    documented cadence).

**notify-continuity-owner** (`…000007`)
:   Delivery step. Delivers the attestation reference to the
    continuity owner along the operator's pre-bound channel
    (ticketing system, chat thread, email). Tracked as a distinct
    step so the evidence-capture artifact and the human-acknowledgement
    record can be audited independently — an attestation written but
    never delivered is a different failure mode than an attestation
    not written at all. Deliberately not pinned to a D3FEND technique:
    delivery is a notification discipline, mirroring the
    `on_call_rotation` handoff-brief gap note and the
    `crypto_posture_management` notify-crypto-owner gap note.

The five action states are operator-bound runtime seams: the
framework ships neither the scheduler, the backup store, the
key-management surface, the isolated drill target, the evidence
store, nor the notification channel. The playbook is the portable
description of *what* the operator's stack should do on each drill
window; binding those seams to real endpoints is the operator's job.

> **LM determinism.** Trigger resolution, integrity verification,
> restore execution, attestation emission, and notification delivery
> are structured reads and writes against operator-owned surfaces,
> not free-text reasoning steps. The playbook binds no DSPy signature
> — there is no LM-driven step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven summariser on top of the notification
> step (a private, forward-looking extension), the framework-wide
> EU-resident LM endpoint guard re-applies the check at process
> startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(c)** — business continuity, backup management,
disaster recovery, and crisis management. The clause requires
essential and important entities to operate business-continuity
arrangements with evidence of execution and tested restore drills.
The backup_recovery playbook is the per-cycle materialisation of that
"tested restore drill" obligation: the integrity check on the
candidate backup, the non-destructive restore against an isolated
target, and the dated attestation + drill-evidence record published
to the operator's evidence store are the audit-evident discharge of
the clause. Inbound anchor at
[`content/mappings/nis2/article-21-2-c.yaml`](../../content/mappings/nis2/article-21-2-c.yaml)
(`nis2:art-21-2-c`) backlinks `playbook.backup_recovery@v1` on
`playbook_refs` and pins the paired controls
(`control.backup_attestation@v1`, `control.restore_drill@v1`).

**DORA Article 12** — backup policies and procedures, restoration
and recovery procedures and methods, with periodic testing. The
clause requires financial entities to develop and document backup
policies specifying the scope of the data subject to backup and the
minimum frequency, together with restoration and recovery procedures
that ensure restoration with minimum downtime and limited disruption,
and to test those procedures periodically. Inbound anchor at
[`content/mappings/dora/article-12.yaml`](../../content/mappings/dora/article-12.yaml)
(`dora:art-12-backup-restore`) closes the graph. The mappings overlay
deliberately does **not** pin DORA Article 11 (response and recovery,
RTO / RPO objectives) directly: Article 11's operational discharge is
broader than the backup-and-restore-drill slice this playbook owns.
The precedent matches `crypto_posture_management` pinning
`dora:art-9-crypto` rather than the broader `dora:art-9-*` family.

**CRA Annex I §1(h)** — availability of essential and basic
functions, restore-drill lane. Inbound anchor at
[`content/mappings/cra/annex-i-1-h-availability-restore-drill.yaml`](../../content/mappings/cra/annex-i-1-h-availability-restore-drill.yaml)
(`cra:annex-i-1-h-availability-restore-drill`) — the periodic
restore-drill discipline that keeps the operator's documented backup
and recovery surface exercisable on the isolated drill target. The
companion inbound anchor `cra:annex-i-1-availability` pins the
sibling `ransomware_containment` playbook as the containment-side
anchor for §1(h); `backup_recovery` pins the periodic restore-drill
lane. Together the two anchors materialise the availability
obligation across both containment (restore known-good after a
compromise) and periodic exercise (continuous evidence the surface
remains recoverable).

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/backup_recovery/mappings.yaml`](../../content/playbooks/backup_recovery/mappings.yaml)):
CP-9 (System Backup — anchors `detect-restore-drill-trigger`,
`validate-backup-integrity`, and the evidence-capture attestation
record), CP-10 (System Recovery and Reconstitution — anchors
`execute-restore-drill`). CP-2 (Contingency Plan), CP-7 (Alternate
Processing Site), and AU-2 (Event Logging) are deliberately not
pinned — the plan-authoring surface, the alternate-processing-site
designation, and the operator's upstream audit-event policy live
outside this playbook. The in-line note at the top of `mappings.yaml`
documents each omission.

**MITRE D3FEND v1.0.0** — `D3-FH` (File Hashing) at
`validate-backup-integrity`; `D3-SRA` (System Recovery Analysis) at
`execute-restore-drill`. The trigger, evidence-capture, and notify
steps are deliberately not pinned to a D3FEND technique because D3FEND
v1.0.0 frames its defensive techniques around runtime countermeasures
against adversary behaviours; scheduling-surface reads,
attestation-stream emission, and delivery disciplines are anchored on
the OSCAL controls above instead. The in-line gap notes in
`mappings.yaml` document each deliberate absence, mirroring the
`crypto_posture_management`, `infra_posture_management`, `iam_auditor`,
and `on_call_rotation` precedents.

**OCSF v1.3.0** — `API Activity` (class_uid 6003, category 6
Application Activity), direction `both`. Consumed at the trigger
step (reads against the scheduler, the backup-scope catalogue, and
the backup store), at the integrity-check step (reads against the
backup store and the key-management surface), and at the drill step
(writes against the isolated drill target plus reads for the observed
RTO / RPO measurement). Emitted at the evidence-capture step (write
publishing the dated attestation to the evidence store) and at the
notify step (delivery dispatch to the continuity owner's pre-bound
channel). The API Activity records carry the request metadata the
`kpi.restore_drill_cadence@v1` and `kri.backup_integrity_failures@v1`
metrics read.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the drill topology

`examples/n8n/backup_recovery/workflow.n8n.json` carries the CACAO
topology as eight n8n nodes (`manualTrigger`, five `set` nodes, one
`if`, one `noOp`), with node ids preserving the CACAO step ids
verbatim. The five action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles. The single `if-condition` node
(`backup integrity ok?`) emits an `n8n-nodes-base.if` node with a
placeholder condition the operator must wire to the upstream
`out.integrity_ok` field. The lossy translation is recorded in
`meta.secops_ng_notes` so the integrator sees exactly which seams
need attention.

Operators bind the Set rows to their connectors:

- `detect restore-drill trigger` → the operator's scheduler and
  backup-scope catalogue (cron trigger + read against the backup
  store; the Set rows record `__drill_window__`, `__backup_scope__`,
  and `__candidate_backup_id__`).
- `validate backup integrity` → the operator's backup store and
  key-management surface (checksum / manifest read + decryption-key
  availability probe); the Set row records `__integrity_ok__`.
- `execute restore drill` → the operator's isolated drill target
  (write of the in-scope objects, observed RTO / RPO measurement);
  the Set row records `__drill_result__`.
- `evidence capture` → the operator's evidence store (write of the
  dated attestation + drill-evidence record); the Set row records
  `__attestation_id__`.
- `notify continuity owner` → the operator's pre-bound notification
  channel (ticketing webhook, chat thread, email); the Set row
  references `__attestation_id__` and `__backup_scope__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/backup_recovery/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/backup_recovery/workflow.n8n.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/backup_recovery/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the five action
activities documenting their operator-bound seam (trigger resolution,
integrity verification, restore execution, attestation emission,
continuity-owner notification). The committed stub raises
`NotImplementedError` in the activity bodies pending the CORE-TEMPORAL
sibling card that wires the deterministic activity implementations
into the Temporal target; operators can drop the module next to their
worker today to see the topology and the activity signatures.

Temporal is the natural fit for the drill-window discipline: each
per-drill execution becomes one workflow run; the drill window
becomes a Temporal timer; retries against transient failures on the
integrity or drill activity get first-class Temporal semantics
(activity retry policy against the isolated drill target); replay
against the same Temporal event history re-derives the same
attestation payload once the activity bodies are wired.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/backup_recovery/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes,
conditional edge on the integrity outcome, linear edges through
evidence capture and notify); `assemble.py` is the hand-written
reference assembly that wires the GraphSpec + bindings into a
`langgraph.graph.StateGraph`. The committed `state_bindings.py` is a
generated stub: each tool's docstring names the operator-bound seam
it discharges and the body raises `NotImplementedError` until the
CORE-LANGGRAPH sibling card wires the deterministic tool
implementations into the LangGraph target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven notification summariser on top of the `notify-continuity-owner`
state fills that as a private extension. The framework-wide
EU-resident LM endpoint guard re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/backup_recovery/`, `examples/temporal/backup_recovery/`,
`examples/langgraph/backup_recovery/`). The n8n target ships a
committed workflow artifact; the Temporal and LangGraph targets ship
deterministic emitter output with `NotImplementedError` activity /
tool bodies pending the per-target CORE cards. When those land, the
per-target byte-parity goldens under
`tests/examples/backup_recovery/` pin each per-target artifact against
a fresh emitter run from the canonical CACAO source — the
cross-target byte-parity property the framework relies on.

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
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default and
never imports a vendor SDK; pointing the exporter at a managed APM is
a downstream choice the operator owns end-to-end. The sovereignty
posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Metrics — what the drill exposes

Five indicator catalogue entries surface the backup-recovery posture
to the operator's metrics dashboard. The catalogue entries live under
`content/metrics/` and read against the attestation records the
`evidence-capture` state emits and the OCSF `API Activity` telemetry
the drill and integrity-check steps produce.

- **`kri.backup_integrity_failures@v1`** — count of
  backup-integrity-check failures observed on the workflow per
  30-day window (each execution whose `__integrity_ok__` was
  `false` contributes one to the count). Catalogue:
  [`content/metrics/backup_integrity_failures.yaml`](../../content/metrics/backup_integrity_failures.yaml).
  Rising values indicate the backup surface is drifting away from a
  recoverable state — the failure mode the "tested restore drill"
  clauses under NIS2 Art. 21(2)(c) and DORA Art. 12 surface when the
  reviewer reads the attestation stream.
- **`kpi.backup_integrity_pass_rate@v1`** — pass rate of the
  integrity-verification step across the evaluation window (the
  complement KPI of the failure-count KRI above). Catalogue:
  [`content/metrics/backup_integrity_pass_rate.yaml`](../../content/metrics/backup_integrity_pass_rate.yaml).
- **`kpi.restore_drill_cadence@v1`** — share of in-scope backup
  scopes that received a completed restore drill within the
  operator's documented drill cadence. Catalogue:
  [`content/metrics/restore_drill_cadence.yaml`](../../content/metrics/restore_drill_cadence.yaml).
  Answers "are we exercising the surface on the cadence the policy
  documents?".
- **`kpi.restore_drill_attestation_freshness@v1`** — share of
  in-scope backup scopes whose most-recent restore-drill attestation
  is fresh against the operator's documented cadence. Catalogue:
  [`content/metrics/restore_drill_attestation_freshness.yaml`](../../content/metrics/restore_drill_attestation_freshness.yaml).
  Answers "if a regulator asked today, could we produce a recent
  dated attestation per scope?".
- **`kri.restore_drill_rto_overrun@v1`** — count of executed restore
  drills whose observed recovery time exceeded the documented RTO
  objective. Catalogue:
  [`content/metrics/restore_drill_rto_overrun.yaml`](../../content/metrics/restore_drill_rto_overrun.yaml).
  Rising values indicate the recovery capability is drifting behind
  the documented objective — the DORA Art. 11 signal that Art. 12's
  periodic testing surfaces even without pinning Art. 11 directly.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI / KRI series against their own metrics backend.

## 8. Operator customisation points

The playbook is a drill-window machine; the *policy* it exercises is
the operator's. The customisation seams:

- **Restore-drill cadence.** The
  `kpi.restore_drill_cadence@v1` and
  `kpi.restore_drill_attestation_freshness@v1` catalogue entries read
  against the operator's documented cadence — the operator sets the
  cadence per backup scope (weekly, monthly, quarterly, whichever
  the operator's continuity policy documents). The playbook does not
  prescribe the cadence; a small operator running a single-scope
  restore drill will run one wide window, a regulated operator with
  many in-scope scopes will run per-scope windows on a rolling
  schedule.
- **RTO overrun threshold.** The
  `kri.restore_drill_rto_overrun@v1` catalogue entry reads the
  observed RTO / RPO recorded on `__drill_result__` and compares
  against the operator's documented recovery-time objective per
  scope. The threshold values (`warn` / `breach`) are the operator's
  audit-evident policy on how far a drill may drift from the
  documented RTO before it counts as an overrun; the catalogue's
  default thresholds are a starting point, not a mandate.
- **Backup-integrity failure threshold.** The
  `kri.backup_integrity_failures@v1` catalogue entry counts the
  false-outcome executions in the evaluation window; the `warn`
  (>=1) and `breach` (>=3) thresholds documented in the catalogue
  are the framework's opinionated starting point — one failure is
  worth a look, three in a 30-day window is worth an audit trail.
  Operators who want a stricter or looser bar override the threshold
  values in their local metric override without re-authoring the
  catalogue entry itself.
- **Isolated drill target.** The `execute-restore-drill` step
  restores against the operator's *documented isolated drill target*;
  the framework binds neither the target's shape (dedicated cluster,
  ephemeral sandbox, per-drill VM, staging environment gated against
  production traffic) nor the isolation-verification discipline the
  operator applies. The mappings overlay's file-header deliberately
  omits OSCAL CP-7 (Alternate Processing Site) — the isolated drill
  target is a documented isolation surface, not a production-failover
  site.
- **Backup-scope catalogue.** The `detect-restore-drill-trigger` step
  reads `__backup_scope__` against the operator's own catalogue of
  in-scope backup surfaces; the framework does not prescribe the
  scope discovery mechanism. Operators wire the trigger to whichever
  backup-scope catalogue their backup platform maintains.
- **Continuity-owner notification channel.** The
  `notify-continuity-owner` step delivers the attestation reference
  along the operator's pre-bound channel — ticketing system, chat
  thread, email, or the operator's incident-notification lane. The
  framework does not prescribe the channel.

## 9. Replay and audit story

The byte-parity drift guards land with the CORE-TEMPORAL /
CORE-LANGGRAPH sibling cards under `tests/examples/backup_recovery/`.
Each per-target golden pins the committed worked-example artifact
to a fresh emitter run from the canonical CACAO source; if the
compiler or the playbook changes, regenerate via the per-target
`regenerate.sh` and commit the diff intentionally.

The cross-target replay property is the harder one: the same drill
execution, fed through n8n / Temporal / LangGraph, produces a
byte-identical attestation record once each target's activity /
tool bodies are wired against the same operator seams and the same
OSCAL / OCSF / D3FEND reference bundles. The
`(candidate_backup_id, drill_window, attestation_id)` key is the
string a regulator can diff to confirm the property holds across
targets.

## 10. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  backup store, the key-management surface, the isolated drill
  target, the evidence store, or the notification channel.
  Connectors are operator-bound at runtime against environment
  variables documented per target.
- **Backup-policy authorship.** The playbook operationalises a
  documented backup policy; it does not author one. Scope, retention,
  frequency, encryption posture, and the isolated drill target's
  isolation-verification discipline all live in the operator's
  governance documentation upstream of this workflow.
- **Restore-target misconfiguration detection.** Detection bindings
  for restore-target misconfiguration (restore landing in production,
  drill target reachable from production network) are owned by a
  sibling EXTEND card once stable upstream rule ids are selected;
  the mappings overlay's file-header records the deferral.
- **Alternate processing site.** CP-7 (Alternate Processing Site) is
  deliberately not pinned — the isolated drill target is an isolation
  surface, not a production-failover site. Failover / DR-site
  designation is a different discipline anchored elsewhere.
- **Contingency-plan authorship.** CP-2 (Contingency Plan) is
  deliberately not pinned — this playbook operates the periodic
  restore-drill lane within the contingency-plan lifecycle; the
  plan-authoring surface lives in the operator's governance
  documentation. CP-2 anchors the `on_call_rotation` overlay where
  the per-shift responder-identification slice of the same plan
  lives.

## 11. References

- [`content/playbooks/backup_recovery/README.md`](../../content/playbooks/backup_recovery/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/backup_recovery/mappings.yaml`](../../content/playbooks/backup_recovery/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay with
  per-step control anchors and the in-line closure notes for the
  deliberate OSCAL / D3FEND / GDPR omissions.
- [`content/mappings/nis2/article-21-2-c.yaml`](../../content/mappings/nis2/article-21-2-c.yaml)
  — NIS2 Article 21(2)(c) inbound anchor.
- [`content/mappings/dora/article-12.yaml`](../../content/mappings/dora/article-12.yaml)
  — DORA Article 12 inbound anchor.
- [`content/mappings/cra/annex-i-1-h-availability-restore-drill.yaml`](../../content/mappings/cra/annex-i-1-h-availability-restore-drill.yaml)
  — CRA Annex I §1(h) restore-drill-lane inbound anchor.
- [`content/mappings/gdpr/data-flow-backup_recovery.md`](../../content/mappings/gdpr/data-flow-backup_recovery.md)
  — GDPR data-flow record (out of scope at this layer).
- [`examples/n8n/backup_recovery/README.md`](../../examples/n8n/backup_recovery/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/backup_recovery/README.md`](../../examples/temporal/backup_recovery/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/backup_recovery/README.md`](../../examples/langgraph/backup_recovery/README.md)
  — LangGraph worked-example stub.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
