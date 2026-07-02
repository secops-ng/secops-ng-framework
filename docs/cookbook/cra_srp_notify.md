# cra_srp_notify — cookbook walkthrough

Manufacturer reporting under the EU Cyber Resilience Act
Article 14 to the Single Reporting Platform (SRP). The
`playbook.cra_srp_notify@v1` CACAO playbook operates the
awareness-anchored notification cascade the regulation
prescribes for actively-exploited vulnerabilities and severe
incidents: a 24-hour early warning, a 72-hour full
notification, and a final report at 14 days (Art. 14(2)
actively-exploited vulnerability) or 1 month (Art. 14(3)
severe incident). The playbook expresses the three clocks as
first-class CACAO durable state so any of the three
reference compile targets (n8n, Temporal, LangGraph) can
carry the awareness-anchored deadlines as replayable
workflow state — not as ad-hoc cron jobs on the operator's
side.

The playbook is a **shared regulator-notification chain**
fired by a sibling incident-handling or vulnerability-intake
playbook when the operator's incident-classification step
trips the Art. 14(2) actively-exploited-vulnerability clock
or the Art. 14(3) severe-incident clock. `vuln_intake`
already hands off to the CRA Article 14 notification lane on
a KEV-listed disclosure; `incident_management` hands off on
a severe-incident classification. The two upstream lanes
converge here so the three submission clocks are operated
consistently against the SRP.

This walkthrough wires the SKELETON playbook through all
three reference compile targets (n8n, Temporal, LangGraph)
and shows where the awareness-anchored 24h / 72h / 14d-or-30d
durable delays land in each. The submission-body shape is a
placeholder — the SRP intake schema is not yet published
(Commission page notes a pre-go-live testing period ahead of
11 September 2026); the payload builder lands in a follow-up
card once the SRP schema is public.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

## 1. Why this matters

The Cyber Resilience Act (Regulation (EU) 2024/2847) imposes
manufacturer reporting obligations that read as a strict
timer cascade anchored on the moment the manufacturer became
aware of the actively-exploited vulnerability or severe
incident:

- **Art. 14(1)** — 24-hour early warning to the manufacturer's
  main-establishment CSIRT via the SRP, with simultaneous
  availability to ENISA.
- **Art. 14(2)** — 72-hour full notification, and a final
  report within 14 days after a corrective or mitigating
  measure becomes available (actively-exploited
  vulnerability).
- **Art. 14(3)** — same 24h / 72h shape for severe incidents,
  with the final report due within 1 month.

The three clocks are anchored on the same awareness timestamp
— not on each other — so the 72h and the final-report clocks
run concurrently after the 24h early warning is dispatched.
Missing a clock is a compliance event visible to the
supervisory authority; wiring these clocks into an
orchestration surface that survives worker restart is the
audit-evident discharge of the obligation.

The playbook is the **portable description of that discharge**.
It does not choose the SRP intake technology (the SRP intake
schema is not yet public), does not embed manufacturer
credentials, and does not decide the operator's SBOM /
incident-ledger surface. It describes the workflow shape the
operator's stack should run against the SRP — as a shipped
NGO / EU Digital Commons artifact.

## 2. Source of truth

```
content/playbooks/cra_srp_notify/
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.cra_srp_notify@v1)
└── mappings.yaml                # outbound OSCAL / OCSF / CRA overlay

content/mappings/cra/article-14-and-annex-i.yaml
                                  # CRA Article 14 inbound anchors —
                                  # cra:art-14-early-warning,
                                  # cra:art-14-notification-72h,
                                  # cra:art-14-final-report,
                                  # cra:art-14-severe-incident
```

The CACAO source is canonical. The seven-step topology (one
`start`, three `action`-submission steps, two `action`-delay
steps, one `parallel`, one `end`) is the deterministic policy
the playbook *means*. The three worked examples under
`examples/{n8n,temporal,langgraph}/cra_srp_notify/` are the
same playbook compiled into three orchestrator idioms.

## 3. CACAO topology

The workflow is a two-phase awareness-anchored cascade: a
single 24h early warning, followed by a `parallel` fan-out
that runs the 72h clock and the final-report clock
concurrently. Both later clocks are anchored on the same
`__awareness_ts__` variable, not on each other.

| Step suffix | Step                                     | Discipline                                                                                                        | Status         |
|-------------|------------------------------------------|-------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | cra_srp_notify_start                     | edge wiring only — no body                                                                                        | n/a            |
| `…000002`   | early_warning                            | compose the 24h early-warning submission and dispatch to the SRP with simultaneous availability to ENISA          | operator-bound |
| `…000003`   | parallel fan-out                         | fan out the 72h clock and the final-report clock (both anchored on `__awareness_ts__`)                            | n/a            |
| `…000004`   | wait until 72h deadline                  | durable delay to `__awareness_ts__ + 72h`; survives worker restart                                                | operator-bound |
| `…000005`   | full_notification                        | compose the 72h full notification and dispatch to the SRP with simultaneous availability to ENISA                 | operator-bound |
| `…000006`   | wait until final-report deadline         | durable delay to `+14d` (Art.14(2)) or `+1 month` (Art.14(3)), selected by `__clock_kind__`                       | operator-bound |
| `…000007`   | final_report                             | compose the final report and dispatch to the SRP with simultaneous availability to ENISA                          | operator-bound |
| `…00000a`   | cra_srp_notify_end                       | edge wiring only — no body                                                                                        | n/a            |

The three submission actions carry the CACAO I/O contract
(`in_args` — `__case_id__`, `__clock_kind__`,
`__awareness_ts__`; `out_args` — the corresponding SRP
submission id) plus `x_secops_ng` reference bundles (control,
telemetry, metric refs). The two durable-delay actions read
`__awareness_ts__` (and `__clock_kind__` on the final-report
side) and carry no output — the deadline is a wait, not a
value.

> The playbook maturity is `experimental` on the workflow-
> local content marker. This is a SKELETON: the timer cascade
> topology and the awareness-anchored durable-state contract
> are landed; the submission-body wiring is a placeholder
> pending the SRP intake schema publication. A sibling CORE
> card lands the payload builder against the schema once the
> Commission publishes it.

## 4. Playbook variables

The playbook operates on six workflow-scope variables
declared on the canonical CACAO source. Three are supplied by
the upstream classifier at hand-off; three are stamped by the
submission steps on confirmed receipt:

| Variable                        | External? | Set by                                    | Purpose                                                                                     |
|---------------------------------|-----------|-------------------------------------------|---------------------------------------------------------------------------------------------|
| `__case_id__`                   | yes       | upstream (`vuln_intake`, `incident_management`) | correlation key across the three submission clocks — join early / full / final into one ledger event |
| `__clock_kind__`                | yes       | upstream classifier                       | `actively_exploited_vulnerability` (Art.14(2), +14d final) or `severe_incident` (Art.14(3), +1 month final) |
| `__awareness_ts__`              | yes       | upstream classifier                       | ISO 8601 timestamp when the operator became aware; anchors the 24h / 72h / 14d-or-30d clocks |
| `__srp_early_warning_id__`      | no        | `early_warning` step                      | id of the 24h submission on confirmed SRP receipt                                            |
| `__srp_full_notification_id__`  | no        | `full_notification` step                  | id of the 72h submission on confirmed SRP receipt                                            |
| `__srp_final_report_id__`       | no        | `final_report` step                       | id of the final-report submission on confirmed SRP receipt                                   |

The three id outputs are the audit-evident anchor the
downstream compliance layer joins on to reconstruct the
per-case timeline. The three submission steps do not mutate
the incident state on the upstream lane — they emit
Compliance Finding records on the OCSF telemetry stream and
return the id for the ledger.

## 5. Timer configuration and endpoint binding

The playbook binds two operator-owned surfaces via
**environment variables** — no secrets, no endpoints are
baked into the CACAO source or the three emitted worked
examples. Both surfaces stay with the operator; the
framework describes the shape only.

### 5.1 Timer intervals

The three CRA Article 14 clocks are anchored on
`__awareness_ts__` and are **not** operator-tunable — the
regulation fixes them. The two durable-delay steps read the
following intervals from `__awareness_ts__` and
`__clock_kind__`:

- `wait until 72h deadline` — resolves at `__awareness_ts__ +
  72h`. No environment variable; the interval is regulatory.
- `wait until final-report deadline` — resolves at
  `__awareness_ts__ + 14 days` when `__clock_kind__ =
  actively_exploited_vulnerability` (Art.14(2)), or at
  `__awareness_ts__ + 1 month` when `__clock_kind__ =
  severe_incident` (Art.14(3)). No environment variable; the
  interval is regulatory.

Operators who run the playbook against a **test SRP
instance** during the Commission's pre-go-live testing period
can compress the clocks for exercise runs. The reference
compile targets each expose one optional environment
variable for that purpose:

```
SECOPS_NG_CRA_SRP_CLOCK_SCALE   # optional float, default 1.0
                                # 1.0 => real clocks (production)
                                # <1.0 => compressed clocks (exercise only)
```

The variable is read by the operator's activity / node body
where it applies the wait; the framework binds no default and
ships no interpolation logic. Operator responsibility: never
set below 1.0 against a real SRP intake. The recommended
guardrail is a startup assertion in the operator's worker
module — if the target endpoint is the real SRP and the scale
is < 1.0, refuse to start.

### 5.2 SRP intake and ENISA availability

The three submission steps target the operator's SRP intake
endpoint. The endpoint URL is not baked into the framework —
it is read from environment variables by the operator's
submission body. The reference pattern:

```
SECOPS_NG_CRA_SRP_ENDPOINT              # SRP intake URL (post-schema publication)
SECOPS_NG_CRA_SRP_ENISA_MIRROR          # ENISA simultaneous-availability endpoint
SECOPS_NG_CRA_SRP_CLIENT_ID             # manufacturer client id (per SRP onboarding)
```

The credentials sit in the operator's secrets manager (Vault,
sealed secrets, a sovereign KMS); they are read at worker
startup, never at emitter time. The compilers ship no secret
material and no default endpoint. The three worked examples
carry TODO markers where the SRP payload builder will land
once the schema is published.

**ENISA simultaneous availability.** Article 14 requires the
manufacturer to make the submission simultaneously available
to ENISA. This is an operator wiring: either the SRP intake
returns an ENISA-mirror receipt on submission, or the
operator dispatches an additional call to the ENISA mirror
endpoint from within the same submission activity /
node body. The two options are equivalent from the CACAO
contract's point of view; the operator's SRP onboarding
choice decides which pattern applies. Both are consistent
with the framework's read-only posture — the submission is
an outbound POST to a regulator surface, not a mutation on
the operator's incident lane.

## 6. Regulatory anchors

**CRA Article 14** — manufacturer reporting obligations. The
regulation prescribes the three clocks the playbook operates:

- **Art. 14(1)** — 24-hour early warning of an
  actively-exploited vulnerability or severe incident, to the
  main-establishment CSIRT via the SRP.
- **Art. 14(2)** — 72-hour full notification and a 14-day
  final report after a corrective or mitigating measure is
  available (actively-exploited vulnerability).
- **Art. 14(3)** — same 24h / 72h shape for severe incidents,
  with the final report due within 1 month.

Inbound anchors live at
[`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
under the mapping ids `cra:art-14-early-warning`,
`cra:art-14-notification-72h`, `cra:art-14-final-report`, and
`cra:art-14-severe-incident`. Each backlinks
`playbook.cra_srp_notify@v1`.

**Single Reporting Platform.** The Commission's CRA reporting
obligations page announces the SRP as the intake surface,
applicable 11 September 2026, with a pre-go-live testing
period expected ahead of that date. The intake schema is not
yet public — the SKELETON deliberately defers the submission
body shape and marks the payload rows `TODO (CORE)` across
the three reference emitters. A sibling CORE card lands the
schema-conformant payload builder once the schema is
published.

**Parallel-reporting interaction with NIS2 Art. 23 and DORA
Art. 19.** Severe-incident reporting under CRA Art. 14(3)
overlaps with NIS2 Art. 23 (essential / important entity
incident reporting to the operator's national CSIRT) and DORA
Art. 19 (financial-entity major-incident reporting to
national competent authorities). ENISA has not yet
documented the interaction between the three regimes as of
2026-07-02; the outbound overlay carries `todo` placeholders
against a sibling EXTEND card that revisits the graph once
the interaction is documented. The playbook itself is
CRA-scoped by design — parallel reporting to national CSIRTs
lives on the operator's `incident_management` playbook, not
here.

**OSCAL controls** — from
[`content/playbooks/cra_srp_notify/mappings.yaml`](../../content/playbooks/cra_srp_notify/mappings.yaml):
IR-6 (Incident Reporting) anchors the three submission steps
end-to-end. IR-6 requires the organisation to report
suspected incidents to designated authorities within
organisation-defined time periods; CRA Article 14 pins those
periods and names the SRP as the intake surface. The same
OSCAL anchor the `vuln_intake` playbook uses for its
regulator-notification action.

**MITRE D3FEND v1.0.0** — the outbound overlay carries a
`D3-TODO` placeholder. D3FEND v1.0.0 frames its defensive
techniques around runtime countermeasures against adversary
behaviours; regulator-notification is a reporting discipline
rather than a runtime countermeasure and the closest fit is a
documentation / notification tag. A sibling card either
selects the closest-fitting technique or documents the
deliberate gap the way the `backup_recovery` and
`crypto_posture_management` overlays document their
notify-owner gaps.

**OCSF v1.3.0** — one class binding.
`Compliance Finding` (class_uid 2003, category Findings),
direction `emits`, is emitted by the three submission steps
as the structured per-submission record the compliance layer
routes on. One Compliance Finding per 24-hour early warning,
72-hour full notification, and final report, keyed to
`__case_id__` so the incident-timeline-signal control can
audit on-time delivery against the CRA Article 14 clocks.

## 7. Per-target hand-off

### 7.1 n8n — Set nodes over the two-phase cascade

`examples/n8n/cra_srp_notify/workflow.n8n.json` carries the
CACAO topology as eight n8n nodes (one `manualTrigger`, five
`set` nodes, one fan-out `set` for the parallel step, one
`noOp` terminal). Node ids preserve the CACAO step ids
verbatim. The three submission steps and the two durable-
delay steps each emit `n8n-nodes-base.set` nodes carrying the
CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles.

Operators bind the Set rows to their connectors:

- `early_warning` → the operator's SRP intake connector (HTTP
  Request node against `SECOPS_NG_CRA_SRP_ENDPOINT` once the
  schema is public; test-instance connector during the
  pre-go-live period); writes `__srp_early_warning_id__`.
- `wait until 72h deadline` / `wait until final-report
  deadline` → a live integrator swaps the Set node for an
  `n8n-nodes-base.wait` node against their own timer surface,
  reading `__awareness_ts__` and (for the final-report side)
  `__clock_kind__`.
- `full_notification` / `final_report` → same SRP intake
  connector as the early warning, with the different payload
  shape once the schema is public. Writes
  `__srp_full_notification_id__` / `__srp_final_report_id__`.

To regenerate the compiled workflow artifact from the repo
root:

```sh
./examples/n8n/cra_srp_notify/regenerate.sh
```

To import into an n8n instance: open the workflows list,
choose **Import from File**, and select
`examples/n8n/cra_srp_notify/workflow.n8n.json`. The workflow
is inactive by default — review and bind the Set rows to
your own connectors before activating. The emitted workflow
is a *snapshot of intent*, not a runnable playbook.

See
[`examples/n8n/cra_srp_notify/README.md`](../../examples/n8n/cra_srp_notify/README.md)
for the full worked-example walkthrough.

### 7.2 Temporal — `@activity.defn` bodies + durable timers

`examples/temporal/cra_srp_notify/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class
and one `@activity.defn` function per CACAO action step. The
three submission activities delegate their SRP submission
body to an operator-implemented helper (the framework binds
no default); the two durable-delay activities are the natural
Temporal idiom: `await workflow.sleep(...)` against the
awareness-anchored deadline, computed from `__awareness_ts__`
and (for the final-report side) `__clock_kind__`.

Temporal is a natural fit for the awareness-anchored cascade:
each incident becomes one workflow run; the 72h and the
final-report clocks survive worker restart as first-class
Temporal timer state; retries against transient failures on
the SRP intake get first-class Temporal semantics (activity
retry policy per submission). The parallel step compiles into
two child futures awaited via `asyncio.gather(...)` inside
the `run()` method.

See
[`examples/temporal/cra_srp_notify/README.md`](../../examples/temporal/cra_srp_notify/README.md)
for import instructions and the regeneration recipe.

### 7.3 LangGraph — `@tool` wrappers + interrupt-resume waits

`examples/langgraph/cra_srp_notify/state_bindings.py` carries
the `TypedDict` state and the `@tool`-decorated action
wrappers. `graph_spec.json` carries the target-neutral
topology (nodes plus the two branches emerging from the
CACAO `parallel` step); `assemble.py` is the hand-written
reference assembly that wires the GraphSpec + bindings into a
`langgraph.graph.StateGraph`.

The durable delays are expressed as LangGraph nodes whose
body is **interrupt-then-resume-at-timestamp** — the operator
adapts the wait mechanism to their runtime (checkpointer-
backed interrupts, an external scheduler callback, or a
persistence layer that survives worker restart). The
GraphSpec is the intent; the wait mechanism is the seam.

LangGraph is the agentic target — an operator who wants to
layer an LM-driven enrichment on top of a submission step
(rendering the case summary into a submission-body draft for
human review, for instance) fills that as a private
extension. The framework-wide EU-resident LM endpoint guard
re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`); see
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

See
[`examples/langgraph/cra_srp_notify/README.md`](../../examples/langgraph/cra_srp_notify/README.md)
for the assembly recipe.

### 7.4 Cross-target parity

All three reference targets are present in the tree today
(`examples/n8n/cra_srp_notify/`,
`examples/temporal/cra_srp_notify/`,
`examples/langgraph/cra_srp_notify/`). Each ships a committed
emitter artifact (n8n workflow JSON, Temporal worker module,
LangGraph GraphSpec + bindings) driven from the same CACAO
source. Cross-target byte-parity goldens live under
`tests/examples/cra_srp_notify/test_golden.py` — a fresh
regeneration against the canonical CACAO source must match
the committed emitter output byte-for-byte on all three
targets.

The compile-target parity guarantee applies to the emitter
output. The submission-body content is operator-bound at
runtime and does not enter the parity contract — a real SRP
POST payload depends on the operator's manufacturer
identifiers, the case-specific metadata, and the SRP schema
once published.

## 8. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends
an `AuditRecord` to a context-local `AuditTrail` *before* the
operator-bound seam call. The mirror runs unconditionally,
ahead of any OTLP exporter, so the audit property holds even
when the operator has not configured a collector — typical
for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are
stable across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `parallel`, `start`, `end`). |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a
default and never imports a vendor SDK; pointing the exporter
at a managed APM is a downstream choice the operator owns
end-to-end. The sovereignty posture asks for an EU-resident
collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to
drain a trail offline.

## 9. Metrics — the on-time KPIs

The playbook feeds four KPIs on the metrics catalogue,
stamped by the three submission steps:

- **`kpi.cra_early_warning_on_time@v1`** — did the
  `early_warning` submission complete before
  `__awareness_ts__ + 24h`?
- **`kpi.cra_notification_72h_on_time@v1`** — did the
  `full_notification` submission complete before
  `__awareness_ts__ + 72h`?
- **`kpi.cra_final_report_on_time@v1`** — did the
  `final_report` submission complete before
  `__awareness_ts__ + 14d` under `__clock_kind__ =
  actively_exploited_vulnerability`?
- **`kpi.cra_severe_incident_on_time@v1`** — did the
  `final_report` submission complete before
  `__awareness_ts__ + 1 month` under `__clock_kind__ =
  severe_incident`?

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators
dashboard the KPI series against their own metrics backend.

## 10. Operator customisation points

The playbook is the awareness-anchored cascade; the *bindings*
it exercises are the operator's. The customisation seams:

- **Upstream hand-off.** The playbook is fired by a sibling
  incident-handling or vulnerability-intake playbook when the
  operator's incident-classification step trips a CRA Article
  14 clock. The hand-off contract is the three external
  variables (`__case_id__`, `__clock_kind__`,
  `__awareness_ts__`); the operator's upstream classifier
  stamps them.
- **SRP intake endpoint.** Read from
  `SECOPS_NG_CRA_SRP_ENDPOINT` (production) or a test-instance
  URL during the Commission's pre-go-live testing period. The
  framework binds no default.
- **ENISA simultaneous availability.** Either the SRP intake
  returns an ENISA-mirror receipt on submission, or the
  operator dispatches an additional call to
  `SECOPS_NG_CRA_SRP_ENISA_MIRROR` from within the same
  submission activity / node body. Both patterns are
  compatible with the CACAO contract.
- **Submission-body shape.** SKELETON: placeholder payload
  rows across all three worked examples. The CORE card lands
  the schema-conformant payload builder once the SRP schema
  is published.
- **Timer scale for exercise runs.** Optional
  `SECOPS_NG_CRA_SRP_CLOCK_SCALE` (default 1.0). Never set
  below 1.0 against a real SRP intake.

## 11. Playbook chain — where cra_srp_notify sits

The regulator-notification chain sits downstream of both the
vulnerability-intake lane and the incident-handling lane; it
is not fired directly by an operator, only by an upstream
CACAO playbook whose classification step has determined the
Article 14 clock applies:

```
vuln_intake  (actively-exploited disclosure)
   └── CRA Art.14(2) clock trip ─► cra_srp_notify (24h + 72h + 14d)

incident_management  (severe incident)
   └── CRA Art.14(3) clock trip ─► cra_srp_notify (24h + 72h + 1 month)
```

- **Upstream: `vuln_intake`.** The KEV-listed or otherwise
  actively-exploited disclosure trips the Art. 14(2) clock at
  the `assess CRA reporting trigger` step and hands off to
  this playbook with `__clock_kind__ =
  actively_exploited_vulnerability`. See
  [`docs/cookbook/vuln_intake.md`](./vuln_intake.md).
- **Upstream: `incident_management`.** A severe-incident
  classification trips the Art. 14(3) clock and hands off to
  this playbook with `__clock_kind__ = severe_incident`. See
  [`docs/cookbook/incident_management.md`](./incident_management.md).
- **Sibling regime: NIS2 Art. 23 / DORA Art. 19 parallel
  reporting.** Both regimes anchor on the operator's
  `incident_management` playbook, which emits its own
  regulator-notification chain to the operator's national
  CSIRT and (for financial entities) national competent
  authority. `cra_srp_notify` stays CRA-scoped by design; the
  parallel-reporting interaction is on the EXTEND roadmap
  once ENISA / the ESAs document it.

The chain is not code-coupled — each playbook is a standalone
CACAO artifact that can be run in isolation — but the audit
trail's coherence across the workflows (each Compliance
Finding keyed to the same `__case_id__` through the three
submission clocks) is the sovereign-security property the
framework guarantees.

## 12. What this cookbook does not cover

- **SRP intake schema.** The submission-body shape is a
  placeholder until the Commission publishes the SRP intake
  schema. Wiring the schema-conformant payload builder is
  the CORE card that lands next in the CRA lane.
- **Credentials.** No manufacturer client ids, no SRP tokens,
  no ENISA mirror credentials. Secrets are read from
  environment variables at worker startup by the operator's
  submission body; the framework ships no defaults.
- **Real SRP submissions from this cookbook.** The worked
  examples are snapshots of intent. Real submissions require
  the operator's SRP onboarding, the schema publication, and
  the operator's live worker deployment.
- **Upstream classification logic.** Whether a vulnerability
  is "actively exploited" under Art. 14(2) or whether an
  incident is "severe" under Art. 14(3) is the upstream
  classifier's decision, not this playbook's. The upstream
  playbook (`vuln_intake`, `incident_management`) owns the
  classification; this playbook operates the notification
  chain the classification triggers.
- **Parallel reporting to NIS2 / DORA authorities.** Those
  chains live on the operator's `incident_management`
  playbook, not here. The EXTEND roadmap revisits the graph
  once ENISA / the ESAs document the interaction.

## 13. References

- [`content/playbooks/cra_srp_notify/playbook.cacao.json`](../../content/playbooks/cra_srp_notify/playbook.cacao.json)
  — canonical CACAO v2 source (`playbook.cra_srp_notify@v1`).
- [`content/playbooks/cra_srp_notify/mappings.yaml`](../../content/playbooks/cra_srp_notify/mappings.yaml)
  — outbound OSCAL / OCSF / D3FEND / CRA overlay.
- [`content/mappings/cra/article-14-and-annex-i.yaml`](../../content/mappings/cra/article-14-and-annex-i.yaml)
  — CRA Article 14 inbound anchors (early warning, 72h
  notification, 14-day final report, severe-incident chain).
- [`examples/n8n/cra_srp_notify/README.md`](../../examples/n8n/cra_srp_notify/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/cra_srp_notify/README.md`](../../examples/temporal/cra_srp_notify/README.md)
  — Temporal worked-example walkthrough.
- [`examples/langgraph/cra_srp_notify/README.md`](../../examples/langgraph/cra_srp_notify/README.md)
  — LangGraph worked-example walkthrough.
- [`docs/cookbook/vuln_intake.md`](./vuln_intake.md)
  — upstream cookbook (Art. 14(2) actively-exploited-
  vulnerability clock trip).
- [`docs/cookbook/incident_management.md`](./incident_management.md)
  — upstream cookbook (Art. 14(3) severe-incident clock trip).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay
  shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md)
  — four non-negotiable properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md)
  — four-layer runtime.
