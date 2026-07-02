# cyber_hygiene_training — cookbook walkthrough

Basic cyber-hygiene and staff cybersecurity-training posture under
NIS2 Article 21(2)(g), DORA Article 13(6), and CRA Article 13(6). The
`playbook.cyber_hygiene_training@v1` CACAO playbook operates the
per-cycle awareness and role-based training discipline an operator
owes their staff: it snapshots the in-scope training roster from the
operator's HR / identity source, schedules the cycle's awareness and
role-based assignments on the learning-management surface, dispatches
the cycle's phishing-simulation exercise to the enrolled cohorts as
documented exercise traffic, tracks completion state and per-cohort
report-rate, publishes a dated training-attestation to the operator's
evidence store, and notifies the training owner of any completion or
report-rate gaps.

The playbook is the **PROACTIVE per-cycle materialisation** of the
awareness-and-training obligation. It is the sibling of the REACTIVE
`playbook.phishing_triage@v1` under the same NIS2 clause: phishing
triage handles a real phishing incident in progress on live mailflow
telemetry; this playbook operates the per-cycle awareness programme,
role-based training tracks, and documented phishing-simulation
exercise that is the audit-evident discharge of the training-and-
hygiene policy itself. The two are complementary, not duplicative:

```
cyber_hygiene_training (per-cycle proactive)
   └── inventory roster ─► schedule cycle ─► run simulation
       ─► track completion ─► attest ─► notify gaps

phishing_triage        (reactive on live incident)
   └── triage suspicious email ─► contain ─► notify affected users
```

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the roster
inventory, the cycle scheduling, the phishing-simulation exercise,
the completion tracking, the training-attestation emission, and the
training-owner notification land in each target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/cyber_hygiene_training/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.cyber_hygiene_training@v1)

content/mappings/nis2/article-21-2-g.yaml
                                  # NIS2 Art. 21(2)(g) inbound anchor —
                                  # basic cyber-hygiene practices and
                                  # cybersecurity training for staff,
                                  # including phishing-simulation
                                  # exercises with completion tracked
content/mappings/dora/article-13-6-training.yaml
                                  # DORA Art. 13(6) inbound anchor —
                                  # ICT security awareness programmes
                                  # and digital operational resilience
                                  # training as compulsory modules in
                                  # the staff training schemes
content/mappings/cra/article-13-6-staff-cyber-hygiene-awareness.yaml
                                  # CRA Art. 13(6) inbound anchor —
                                  # staff cyber-hygiene and awareness
                                  # lane (third sibling under
                                  # Art.13(6), alongside the vuln-
                                  # handling and third-party advisory
                                  # awareness siblings)
content/mappings/gdpr/data-flow-cyber_hygiene_training.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity for the roster read,
                                  # completion tracking, attestation
                                  # emission, and training-owner
                                  # notification steps; personal-data
                                  # surface here is real (staff
                                  # identifiers, completion state,
                                  # per-recipient simulation outcome)
                                  # so the ROPA entry is authoritative
```

The CACAO source is canonical. The six action steps and the one
`start` / one `end` wiring node are the deterministic policy the
playbook *means* — a linear
roster → schedule → simulate → track → attest → notify chain with no
conditional branching at the workflow layer. The three worked
examples under `examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`
are the same playbook compiled into three orchestrator idioms.
Everything else — the HR / identity source the roster inventory step
reads, the learning-management surface the scheduling and tracking
steps write / read, the phishing-simulation dispatch endpoint the
simulation step calls, the evidence store the attestation step
publishes to, and the training-owner channel the notification step
delivers on — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships eight steps: one `start`, six `action`, and one
`end`. The topology is a linear evaluate-schedule-exercise-track-
attest-notify chain — the completion-tracking step aggregates
mandatory-training overdue, role-based-training overdue, and per-
cohort simulation report-rate against the operator's declared policy
targets, and the notify-gaps step delivers the attestation reference
and the gap summary to the training owner along the operator's
pre-bound channel. There is no conditional branching at the workflow
layer; the deviation classification lives in the Compliance Finding
(class_uid 2003) records emitted by the tracking and simulation
steps.

| Step suffix | Step                        | Discipline                                                                                                                                                                                                                                              | Status         |
|-------------|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | cyber_hygiene_training_start | edge wiring only — no body                                                                                                                                                                                                                             | n/a            |
| `…000002`   | inventory training roster   | read the in-scope training roster from the operator's HR / identity source against `__training_scope__`; resolves per-staff cohort and role-track membership and joiner/leaver state so the cycle assignment is grounded on the current workforce      | operator-bound |
| `…000003`   | schedule training cycle     | publish cycle assignment intents to the operator's learning-management surface: awareness track for all staff, role-based tracks for personnel with security-adjacent roles, on the declared cadence                                                    | operator-bound |
| `…000004`   | run phishing simulation     | dispatch the cycle's phishing-simulation exercise to the enrolled cohorts as **documented exercise traffic** against the simulation endpoint (not against production mailflow controls); records per-recipient delivery, click, and report telemetry   | operator-bound |
| `…000005`   | track completion            | read completion state per staff and per track from the learning-management surface, aggregate per-cohort completion rate and per-cohort simulation click / report rate against the declared policy targets, and emit the per-deviation Compliance Findings | operator-bound |
| `…000006`   | evidence capture            | compose and publish the dated cyber-hygiene and security-training posture attestation to the operator's evidence store: roster snapshot, cycle assignments, simulation outcome aggregate, completion aggregate, per-deviation Findings                    | operator-bound |
| `…000007`   | notify gaps                 | deliver the attestation reference and the gap summary to the training owner along the operator's pre-bound channel (ticketing, chat, email); read-only posture-readiness dispatch — no assignment mutation, no completion-state mutation                | operator-bound |
| `…000008`   | cyber_hygiene_training_end  | edge wiring only — no body (cycle complete)                                                                                                                                                                                                             | n/a            |

All six action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (control,
telemetry). One execution runs the six-step chain (inventory →
schedule → simulate → track → attest → notify) exactly once per
declared training cycle. Per-cycle metric accounting into the
training-completion-rate and phishing-simulation-click-rate catalogue
entries is unambiguous.

> The playbook maturity is `experimental` on the workflow-local
> content marker. The mappings overlay pins the control and
> telemetry surface (OSCAL AT-2 / AT-3 / AT-4, OCSF API Activity and
> Compliance Finding); the n8n, Temporal, and LangGraph reference
> emitters ship deterministic emitter output under
> `examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`.
> Cross-target byte-parity goldens live under
> `tests/examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`.

## 3. Lifecycle contract — the six action states

The per-cycle payload — roster snapshot (per-staff cohort and role-
track membership, joiner/leaver state), cycle assignment record
(awareness track, role-based tracks, due dates), simulation outcome
aggregate (per-cohort delivery / click / report telemetry, no
per-recipient content), completion aggregate (per-staff mandatory
and role-based track completion state), Compliance Findings (per-
deviation records against the declared policy), and the dated
training-attestation record — is workforce-readiness content whose
personal-data surface is real: staff identifiers, completion state,
and per-recipient simulation click/report outcomes are all subject
identifiers within the meaning of GDPR. The GDPR Art. 30 Record of
Processing Activity at
[`content/mappings/gdpr/data-flow-cyber_hygiene_training.md`](../../content/mappings/gdpr/data-flow-cyber_hygiene_training.md)
covers the roster read, cycle scheduling, simulation dispatch,
completion tracking, attestation emission, and training-owner
notification processing; lawful basis is GDPR Art. 6(1)(f)
legitimate interests with Art. 6(1)(c) legal obligation as the
secondary basis where NIS2 Art. 21(2)(g) transposition applies. The
per-recipient simulation click / report outcome is aggregated to the
cohort level in the Compliance Finding stream — the playbook does not
emit per-recipient outcomes into the posture-management layer, so
the finding stream carries cohort-level deviations rather than
individual behaviour records.

**inventory training roster** (`…000002`)
:   Read step. Resolves the in-scope training roster from the
    operator's HR / identity source against `__training_scope__`:
    per-staff cohort membership, per-staff role-track membership,
    joiner/leaver state as of the cycle open. Anchored on OSCAL
    AT-2 (Literacy Training and Awareness) as the awareness-track
    membership surface, and AT-3 (Role-based Training) as the
    role-track membership surface. Emits `__roster_id__` — the
    stable identifier the downstream steps read for the roster
    snapshot. The framework does not bind the HR / identity source;
    the operator wires the seam.

**schedule training cycle** (`…000003`)
:   Write step. Publishes cycle assignment intents to the operator's
    learning-management surface: awareness track for all staff,
    role-based tracks for personnel with security-adjacent roles, on
    the declared cadence. Anchored on OSCAL AT-2 (Literacy Training
    and Awareness) and AT-3 (Role-based Training); the cycle
    assignment is the per-cycle scheduling of the training programme
    against the declared cadence. Emits `__cycle_id__`. The playbook
    does not author training content or track curricula; it operates
    the per-cycle assignment discipline.

**run phishing simulation** (`…000004`)
:   Exercise step. Dispatches the cycle's phishing-simulation
    exercise to the enrolled cohorts as **documented exercise
    traffic** against the simulation endpoint. The simulation is a
    clearly-labelled exercise: it does not trigger incident response,
    does not alter production mailflow controls, and is not routed
    through the operator's live email path. Records per-recipient
    delivery, click, and report telemetry against the simulation
    endpoint's own audit surface. Anchored on OSCAL AT-2(3) (Literacy
    Training and Awareness | Social Engineering and Mining), which
    explicitly contemplates practical exercises that simulate social-
    engineering attacks. Emits `__simulation_id__`. Feeds
    `kpi.phishing_sim_click_rate@v1`.

**track completion** (`…000005`)
:   Aggregation step. Reads completion state per staff and per track
    from the learning-management surface for the cycle's
    assignments, aggregates per-cohort completion rate and per-cohort
    simulation click / report rate against the operator's declared
    policy targets, and emits the per-deviation Compliance Findings:
    staff with mandatory awareness training overdue past the cycle
    due-date, staff with role-based training overdue past the cycle
    due-date, cohorts whose completion rate falls below the declared
    target, cohorts whose simulation click rate exceeds the declared
    threshold, cohorts whose report rate falls below the declared
    threshold, and staff with no declared training requirement in the
    operator's policy (the policy-gap branch — reported separately
    from completion gaps). Anchored on OSCAL AT-4 (Training Records)
    — the per-staff and per-cohort record of completion state
    against the cycle assignments. Emits `__completion_id__` and one
    Compliance Finding per deviation keyed to
    (`__cycle_id__`, staff-or-cohort-id).

**evidence capture** (`…000006`)
:   Attestation step. Composes and publishes the dated cyber-hygiene
    and security-training posture attestation to the operator's
    evidence store, carrying the roster snapshot, cycle assignments,
    simulation outcome aggregate, completion aggregate, and per-
    deviation Compliance Findings. Anchored on OSCAL AT-4 (Training
    Records) — the audit-evident record a reviewer reads against the
    operator's declared retention policy. Emits `__attestation_id__`.
    The playbook does not decide the evidence-store technology
    (object store, GRC platform, evidence lake); the operator binds
    the seam.

**notify gaps** (`…000007`)
:   Notification step. Delivers the attestation reference and the
    gap summary to the training owner along the operator's pre-bound
    channel (ticketing, chat, email). Read-only posture-readiness
    dispatch — the notification does not mutate assignment state or
    completion state, and does not escalate the deviations into the
    incident-response lane; the training owner receives the summary
    and drives remediation off the operator's own cadence.

The six action steps are operator-bound runtime seams: the framework
ships neither the HR / identity source, the learning-management
surface, the phishing-simulation dispatch endpoint, the evidence
store, nor the training-owner notification channel. The playbook is
the portable description of *what* the operator's stack should do per
training cycle; binding those seams to real endpoints is the
operator's job.

> **LM determinism.** Roster inventory, cycle scheduling, simulation
> dispatch, completion tracking, attestation emission, and training-
> owner notification are structured reads and writes against operator-
> owned surfaces, not free-text reasoning steps. The playbook binds no
> DSPy signature — there is no LM-driven step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven enrichment on top of the notify-gaps
> step (rendering the gap summary into a per-owner narrative, for
> instance) as a private extension, the framework-wide EU-resident LM
> endpoint guard re-applies the check at process startup — see
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(g)** — basic cyber-hygiene practices and
cybersecurity training. The clause requires essential and important
entities to operate basic cyber-hygiene practices and cybersecurity
training for staff, and — as ENISA's implementing guidance and the
transposed member-state law elaborate — to run phishing-simulation
exercises with completion tracked. NIS2 enforcement crossed on
2 July 2026; the awareness-and-training obligation is one of the
audit-evident measures a supervisory authority reads first when
assessing the operator's Art. 21 posture. The cyber_hygiene_training
playbook is the **per-cycle materialisation of that obligation**:
the roster snapshot, cycle assignments, simulation run, completion
aggregate, and dated training-attestation record are the audit-
evident discharge of the clause. Inbound anchor at
[`content/mappings/nis2/article-21-2-g.yaml`](../../content/mappings/nis2/article-21-2-g.yaml)
(`nis2:art-21-2-g`) backlinks `playbook.cyber_hygiene_training@v1`
alongside the reactive `playbook.phishing_triage@v1` sibling.

**DORA Article 13(6)** — ICT security awareness programmes and
digital operational resilience training. Regulation (EU) 2022/2554
Art. 13(6) requires financial entities to develop ICT security
awareness programmes and digital operational resilience training as
compulsory modules in their staff training schemes, applicable to
all staff and members of senior management, with a level of
complexity commensurate to the remit of their functions. The
per-cycle discharge shape here is the same one NIS2 Art. 21(2)(g)
anchors on — the training-roster snapshot, the cycle assignments,
the phishing-simulation run, the completion-tracking aggregate, and
the dated training-attestation record. Inbound anchor at
[`content/mappings/dora/article-13-6-training.yaml`](../../content/mappings/dora/article-13-6-training.yaml)
(`dora:art-13-training-awareness`). This is the training-and-
awareness slice of the broader Art. 13 learning-and-evolving surface;
the post-incident-review slice lives on `dora:art-13-learning-evolving`
(operated by `playbook.post_incident_review@v1`), and the two slices
are mapped separately to preserve the atom-per-obligation shape.

**CRA Article 13(6)** — staff cyber-hygiene and awareness. Regulation
(EU) 2024/2847 Art. 13(6) requires manufacturers of products with
digital elements to systematically document and, by implication,
sustain the workforce-readiness posture that underpins the vuln-
handling process. The cyber_hygiene_training playbook is the
**workforce-readiness half** of the Art. 13(6) surface: per-cycle
awareness and role-based training, phishing-simulation exercise,
completion-tracking aggregate, and a dated training-attestation
record. It sits as the third sibling under Art. 13(6) alongside
`cra:art-13-vuln-handling-process` (the documentation-process side,
operated by `playbook.vuln_intake@v1`) and
`cra:art-13-6-third-party-vuln-awareness` (the upstream advisory-feed
and CSIRT-bulletin ingestion side, operated by
`playbook.threat_intel_ingest@v1`). Inbound anchor at
[`content/mappings/cra/article-13-6-staff-cyber-hygiene-awareness.yaml`](../../content/mappings/cra/article-13-6-staff-cyber-hygiene-awareness.yaml)
(`cra:art-13-6-staff-cyber-hygiene-awareness`).

**GDPR Article 30 Record of Processing Activity.** The per-workflow
Art. 30 ROPA at
[`content/mappings/gdpr/data-flow-cyber_hygiene_training.md`](../../content/mappings/gdpr/data-flow-cyber_hygiene_training.md)
covers the roster read, cycle scheduling, simulation dispatch,
completion tracking, attestation emission, and training-owner
notification processing. The personal-data surface is real: staff
identifiers appear on the roster read; per-staff completion state
appears on the tracking read; per-recipient simulation delivery /
click / report state is captured at the simulation endpoint but
aggregated to the cohort level before entering the Compliance
Finding stream and the training-attestation record. Lawful basis:
Art. 6(1)(f) legitimate interests with Art. 6(1)(c) legal obligation
as the secondary basis where NIS2 Art. 21(2)(g) or DORA Art. 13(6)
transposition applies. Retention runs against the operator's
declared retention policy on the training-attestation record.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/cyber_hygiene_training/mappings.yaml`](../../content/playbooks/cyber_hygiene_training/mappings.yaml)):
AT-2 (Literacy Training and Awareness — anchors the inventory-
training-roster, schedule-training-cycle, and run-phishing-simulation
steps; AT-2(3) Social Engineering and Mining explicitly contemplates
the practical phishing-simulation exercise the run step performs),
AT-3 (Role-based Training — anchors the roster snapshot and cycle
scheduling for the role-based tracks), and
AT-4 (Training Records — anchors the completion-tracking aggregate
and the dated training-attestation record emitted by the evidence-
capture step).

**MITRE D3FEND v1.0.0** — deliberately empty on this playbook. The
`d3fend: []` closure documented in the mappings overlay records the
per-step gap rationale: D3FEND v1.0.0 frames its defensive techniques
around runtime countermeasures against adversary behaviours, and the
discipline this playbook operates (periodic awareness and role-based
training scheduling, phishing-simulation exercise execution,
completion tracking, dated training-attestation emission) is a
posture-readiness exercise rather than a runtime countermeasure. The
`control_xref` files for `control.training_attestation@v1` and
`control.phishing_simulation@v1` do reference D3-UA (User Behavior
Analysis) for the analytic surface that consumes training and
simulation outcomes, but D3-UA names the *downstream* analytic
consumer of the per-cycle artifacts this playbook produces, not the
producer. This closure mirrors the gap-note precedent on
`mfa_secured_comms`, `crypto_posture_management`, `backup_recovery`,
`infra_posture_management`, `iam_auditor`, and `on_call_rotation`.

**OCSF v1.3.0** — two class bindings.
`API Activity` (class_uid 6003, category Application Activity),
direction `both`, is consumed at the inventory-training-roster and
track-completion steps (read calls against the HR / identity source
and the learning-management surface) and emitted at the schedule-
training-cycle, run-phishing-simulation, evidence-capture, and
notify-gaps steps (write calls against the learning-management
surface, the simulation dispatch endpoint, the evidence store, and
the training-owner channel). The API Activity records carry the
request metadata `kpi.training_completion_rate@v1` and
`kpi.phishing_sim_click_rate@v1` read.
`Compliance Finding` (class_uid 2003, category Findings), direction
`emits`, is emitted by the track-completion and run-phishing-
simulation steps as the structured per-deviation record the
posture-management layer routes to the training owner and the SIEM
queries against — one Compliance Finding per deviation
(mandatory-training overdue, role-based-training overdue, cohort
completion-rate below target, cohort click-rate above threshold,
cohort report-rate below threshold, policy-gap staff with no
declared training requirement).

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the training-cycle topology

`examples/n8n/cyber_hygiene_training/workflow.n8n.json` carries the
CACAO topology as eight n8n nodes (`manualTrigger`, six `set` nodes,
one `noOp` terminal), with node ids preserving the CACAO step ids
verbatim. The six action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles (control, telemetry). The linear
sequencing carries via `on_completion` edges on the emitted
`connections` block. The lossy translations are recorded in
`meta.secops_ng_notes` so the integrator sees exactly which seams
need attention.

Operators bind the Set rows to their connectors:

- `inventory training roster` → the operator's HR / identity source
  (Workday, HiBob, Personio, an in-house directory, or an LDAP /
  SCIM synchroniser); writes `__roster_id__`.
- `schedule training cycle` → the operator's learning-management
  surface (Moodle, Docebo, Rise 360, TalentLMS, an in-house LMS, or
  a security-awareness-training vendor's cycle-assignment API);
  writes `__cycle_id__`.
- `run phishing simulation` → the operator's phishing-simulation
  dispatch endpoint (a dedicated simulation platform, an open-source
  self-hosted simulator such as GoPhish, or a security-awareness-
  training vendor's simulation API), configured as documented
  exercise traffic; writes `__simulation_id__`.
- `track completion` → the operator's learning-management surface's
  completion-state read API and the simulation endpoint's per-cohort
  aggregate outcome read; writes `__completion_id__` and emits per-
  deviation Compliance Findings.
- `evidence capture` → the operator's evidence store (object store,
  GRC platform, evidence lake, or a policy-as-code artifact store);
  writes `__attestation_id__`.
- `notify gaps` → the operator's training-owner channel (a ticketing
  queue, a chat channel, an email alias, or a policy-owner mailbox).

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/cyber_hygiene_training/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/cyber_hygiene_training/workflow.n8n.json`. The workflow
is inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies (SKELETON stub)

`examples/temporal/cyber_hygiene_training/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the six action
activities documenting their operator-bound seam (inventory /
schedule / simulate / track / attest / notify). The committed stub
raises `NotImplementedError` in the activity bodies pending the
CORE-TEMPORAL sibling card that wires the deterministic activity
implementations into the Temporal target; operators can drop the
module next to their worker today to see the topology and the
activity signatures.

Temporal is a natural fit for the training-cycle discipline: each
declared cycle becomes one workflow run; retries against transient
failures on the HR source, the learning-management surface, the
simulation endpoint, or the evidence store get first-class Temporal
semantics (activity retry policy per seam); replay against the same
Temporal event history re-derives the same roster snapshot, the same
completion aggregate, and the same training-attestation record once
the activity bodies are wired. Schedules (Temporal `Schedule`) give
the operator a durable per-cycle trigger without a bespoke cron
surface.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook (SKELETON stub)

`examples/langgraph/cyber_hygiene_training/state_bindings.py` carries
the `TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes and the
linear on-completion edges from inventory through notify-gaps to the
terminal end); `assemble.py` is the hand-written reference assembly
that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`.
The committed `state_bindings.py` is a generated stub: each tool's
docstring names the operator-bound seam it discharges and the body
raises `NotImplementedError` until the CORE-LANGGRAPH sibling card
wires the deterministic tool implementations into the LangGraph
target.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven enrichment on top of the `notify gaps` step (rendering the
per-deviation Compliance Finding stream into a per-training-owner
narrative, for instance) fills that as a private extension. The
framework-wide EU-resident LM endpoint guard re-applies the check at
process startup (`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/cyber_hygiene_training/`,
`examples/temporal/cyber_hygiene_training/`,
`examples/langgraph/cyber_hygiene_training/`). Each ships a
committed emitter artifact (n8n workflow JSON, Temporal worker
module, LangGraph GraphSpec + bindings) with the operator-bound
activity / tool bodies raising `NotImplementedError` pending the
per-target CORE cards. Cross-target byte-parity goldens land under
`tests/examples/{n8n,temporal,langgraph}/cyber_hygiene_training/` —
the same cross-target byte-parity property the framework relies on
for the rest of the playbook set.

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

## 7. Metrics — what the training-cycle discipline exposes

The training-completion-rate KPI and the phishing-simulation click-
rate KPI are the two catalogue entries this playbook feeds. The
click-rate entry ships today; the completion-rate entry lands with
the EXTEND-METRICS sibling card.

- **`kpi.phishing_sim_click_rate@v1`** — per-cohort share of
  phishing-simulation recipients that clicked the exercise link,
  across the cycle window. Catalogue:
  [`content/metrics/phishing_sim_click_rate.yaml`](../../content/metrics/phishing_sim_click_rate.yaml).
  Stamped by the run-phishing-simulation and track-completion steps.
  Rising values indicate the awareness posture is drifting behind
  the declared threshold; the deviation is captured as a Compliance
  Finding on the emit side.
- **`kpi.training_completion_rate@v1`** (pending EXTEND-METRICS) —
  per-cohort share of mandatory and role-based training completed
  by the cycle due-date. Anchored on the completion-aggregate
  record emitted by the track-completion step. The catalogue entry
  lands with the EXTEND-METRICS card that wires the per-cohort
  training-overdue emitters against the operator's evidence store.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI series against their own metrics backend.

## 8. Detection references — the upstream signal shapes

The playbook does not re-author detection rules. The Compliance
Finding stream emitted by the track-completion and run-phishing-
simulation steps is the **upstream of any Sigma rule** a downstream
consumer chooses to author against missed-training / simulation-
click / report-rate deviations. Rule fingerprints are the operator's
posture-management-layer concern; SecOps-NG does not pin stable Sigma
rule ids on this overlay.

The rule shapes an operator typically authors against the finding
stream:

- **Mandatory-training overdue** — a Compliance Finding with the
  awareness-track key and the overdue-past-due-date flag; the
  fingerprint is stable per (cycle_id, staff_id).
- **Role-based-training overdue** — the same shape keyed on the
  role-track identifier the roster snapshot carries.
- **Cohort completion-rate below target** — a Compliance Finding at
  the cohort granularity; the fingerprint is stable per (cycle_id,
  cohort_id).
- **Cohort simulation click-rate above threshold** — a Compliance
  Finding stamped at the run-phishing-simulation step; the
  fingerprint is stable per (cycle_id, cohort_id, simulation_id).
- **Cohort simulation report-rate below threshold** — the same
  cohort granularity, keyed on the report-rate deviation.
- **Policy-gap staff with no declared training requirement** — a
  Compliance Finding on the staff-with-no-declared-requirement
  branch; the fingerprint is stable per (cycle_id, staff_id) and is
  reported separately from completion gaps to preserve the atom-per-
  deviation shape.

## 9. Operator customisation points

The playbook is a per-cycle training-cycle machine; the *policy* it
exercises is the operator's. The customisation seams:

- **Training scope binding.** The `__training_scope__` workflow-scope
  variable declares which staff are in-scope for the cycle
  (contractors, senior management, security-adjacent roles). The
  framework binds no scope; the operator's HR / identity data model
  and their training policy decide the perimeter.
- **Cycle cadence.** The declared cadence for the awareness and
  role-based tracks (annual, bi-annual, quarterly) is the operator's
  policy choice, bounded by the regulatory floor NIS2 Art. 21(2)(g),
  DORA Art. 13(6), and any transposed member-state law impose. The
  playbook operates whatever cadence the operator declares.
- **Simulation template selection.** The phishing-simulation
  exercise's template — the pretext, the payload style, the enrolled
  cohorts — is the operator's choice against their awareness
  programme's maturity level. The framework binds the seam (a
  documented exercise dispatch against the simulation endpoint) but
  not the content.
- **Completion-rate and click-rate thresholds.** The declared
  policy targets for per-cohort completion rate, per-cohort click
  rate, and per-cohort report rate are the operator's numbers. The
  Compliance Finding stream trips against those thresholds; the
  framework never hard-codes a target.
- **Training-owner routing.** The channel the `notify gaps` step
  dispatches on (ticketing queue, chat channel, email alias, policy-
  owner mailbox) is the operator's decision. The framework binds
  the notification seam but not the channel.

## 10. Replay and audit story

The byte-parity drift guards under
`tests/examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`
each pin the committed worked-example artifact to a fresh emitter
run from the canonical CACAO source; if the compiler or the playbook
changes, regenerate via the per-target `regenerate.sh` and commit
the diff intentionally.

The cross-target replay property is the harder one: the same roster
snapshot, cycle assignments, simulation outcome aggregate, and
completion aggregate, fed through n8n / Temporal / LangGraph, produce
byte-identical Compliance Finding records *and* byte-identical
training-attestation records once each target's activity / tool
bodies are wired against the same operator seams and the same OSCAL
/ OCSF reference bundles. The
`(cycle_id, roster_digest, simulation_id, completion_digest,
attestation_id)` tuple is the string an operator can diff to confirm
the property holds across targets.

## 11. Playbook chain — where cyber_hygiene_training sits

The awareness-and-training chain expresses itself as one proactive
per-cycle workflow that sits alongside the reactive phishing-
incident lane:

```
cyber_hygiene_training (proactive, per-cycle)
    └── attestation ─► operator's evidence store
    └── notify gaps ─► training owner (posture-readiness dispatch)
    └── Compliance Finding stream ─► operator's posture-management layer

phishing_triage (reactive, on live incident)
    └── triage suspicious email ─► contain ─► notify affected users
```

- **Sibling: `phishing_triage`.** Under the same NIS2 Art. 21(2)(g)
  anchor. The training playbook operates the per-cycle awareness
  and simulation discipline; the phishing_triage playbook handles
  real phishing incidents in progress. The two are complementary,
  not duplicative — one is proactive, the other reactive. See
  [`docs/cookbook/phishing_triage.md`](./phishing_triage.md).
- **Adjacent: `post_incident_review`.** DORA Art. 13 companion — the
  learning-and-evolving surface has two slices: this playbook covers
  the training-and-awareness slice
  (`dora:art-13-training-awareness`); `post_incident_review` covers
  the post-ICT-related-incident-review slice
  (`dora:art-13-learning-evolving`). The two slices discharge
  independent operational disciplines and are mapped separately to
  preserve the atom-per-obligation shape. See
  [`docs/cookbook/post_incident_review.md`](./post_incident_review.md).
- **Adjacent: `vuln_intake`.** CRA Art. 13(6) companion — the
  vulnerability-handling-process side. This playbook is the
  workforce-readiness sibling under the same CRA article. See
  [`docs/cookbook/vuln_intake.md`](./vuln_intake.md).
- **Adjacent: `threat_intel_ingest`.** CRA Art. 13(6) companion —
  the third-party vulnerability awareness (upstream advisory-feed
  and CSIRT-bulletin ingestion) side. This playbook is the third
  sibling under Art. 13(6). See
  [`docs/cookbook/threat_intel_ingest.md`](./threat_intel_ingest.md).

The chain lets cyber_hygiene_training stay narrowly focused on the
per-cycle awareness-and-training discipline while phishing_triage
handles live incident traffic, post_incident_review handles the
learning-and-evolving surface, and vuln_intake / threat_intel_ingest
handle the vulnerability-handling and upstream-awareness surfaces on
the product / advisory side. The chain is not code-coupled — each
playbook is a standalone CACAO artifact that can be run in
isolation — but the audit trail's coherence across the workflows is
the sovereign-security property the framework guarantees.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  HR / identity source, the learning-management surface, the
  phishing-simulation dispatch endpoint, the evidence store, or the
  training-owner channel. Connectors are operator-bound at runtime
  against environment variables documented per target.
- **Training content authorship.** The playbook operates the per-
  cycle assignment discipline; it does not author training modules,
  curricula, or role-based track content. Authorship is the
  operator's programme concern.
- **Phishing-simulation template design.** The playbook dispatches a
  documented exercise; the pretext, payload style, and cohort
  enrollment are the operator's awareness-programme choices.
- **Live incident response.** The simulation is a clearly-labelled
  exercise and never triggers incident response. When a *real*
  phishing incident occurs on production mailflow, that lane is
  operated by `playbook.phishing_triage@v1`.
- **Per-recipient behavioural analytics.** The playbook aggregates
  per-recipient simulation outcomes to the cohort level before they
  enter the Compliance Finding stream and the training-attestation
  record. Per-recipient behavioural analytics — if the operator
  chooses to author them — run as a downstream D3-UA-aligned
  consumer of the training-outcome artifacts, not as a step on this
  playbook.

## 13. References

- [`content/playbooks/cyber_hygiene_training/README.md`](../../content/playbooks/cyber_hygiene_training/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/cyber_hygiene_training/mappings.yaml`](../../content/playbooks/cyber_hygiene_training/mappings.yaml)
  — outbound OSCAL / OCSF / NIS2 / DORA / CRA overlay with per-step
  control anchors.
- [`content/mappings/nis2/article-21-2-g.yaml`](../../content/mappings/nis2/article-21-2-g.yaml)
  — NIS2 Article 21(2)(g) inbound anchor (basic cyber-hygiene
  practices and staff cybersecurity training).
- [`content/mappings/dora/article-13-6-training.yaml`](../../content/mappings/dora/article-13-6-training.yaml)
  — DORA Article 13(6) inbound anchor (ICT security awareness
  programmes and digital operational resilience training).
- [`content/mappings/cra/article-13-6-staff-cyber-hygiene-awareness.yaml`](../../content/mappings/cra/article-13-6-staff-cyber-hygiene-awareness.yaml)
  — CRA Article 13(6) inbound anchor (staff cyber-hygiene and
  awareness lane).
- [`content/mappings/gdpr/data-flow-cyber_hygiene_training.md`](../../content/mappings/gdpr/data-flow-cyber_hygiene_training.md)
  — GDPR Article 30 Record of Processing Activity.
- [`examples/n8n/cyber_hygiene_training/README.md`](../../examples/n8n/cyber_hygiene_training/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/cyber_hygiene_training/README.md`](../../examples/temporal/cyber_hygiene_training/README.md)
  — Temporal worked-example stub.
- [`examples/langgraph/cyber_hygiene_training/README.md`](../../examples/langgraph/cyber_hygiene_training/README.md)
  — LangGraph worked-example stub.
- [`docs/cookbook/phishing_triage.md`](./phishing_triage.md)
  — sibling cookbook under the same NIS2 anchor (reactive phishing-
  incident handling).
- [`docs/cookbook/post_incident_review.md`](./post_incident_review.md)
  — adjacent cookbook (DORA Art. 13 learning-and-evolving sibling).
- [`docs/cookbook/vuln_intake.md`](./vuln_intake.md)
  — adjacent cookbook (CRA Art. 13(6) vuln-handling sibling).
- [`docs/cookbook/threat_intel_ingest.md`](./threat_intel_ingest.md)
  — adjacent cookbook (CRA Art. 13(6) upstream-advisory sibling).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
