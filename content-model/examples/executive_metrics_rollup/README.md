# Worked example: `playbook.executive_metrics_rollup@v1`

End-to-end worked example for the SecOps-NG content model, following
the same shape as `content-model/examples/vuln_intake/` and
`content-model/examples/data_exfil/`. Ties together every layer
(playbook → controls → telemetry → metrics) plus regulatory overlays
(NIS2, DORA) and external catalog references (OSCAL, MITRE D3FEND, OCSF)
around a single scenario: a recurring monthly aggregation of the
operator's KPI/KRI catalog into a board-ready summary plus a
control-effectiveness score.

The rollup anchors NIS2 Article 21(2)(f) — effectiveness assessment —
and DORA Article 6 — ICT risk-management framework periodic review —
without prescribing a specific board-pack template.

## Why an executive rollup

The lower layers (detection, control, telemetry, response playbooks)
all produce per-event evidence. Boards and regulators expect the
evidence to be rolled up periodically with a defensible control-
effectiveness narrative attached. This example shows the smallest
realistic workflow that closes the loop: it consumes the operator's
pinned KPI/KRI catalog, evaluates each entry over an ISO-8601 window,
groups evaluations by `control_refs[]` to score control effectiveness,
and emits a structured summary artifact the board-pack pipeline can
consume. Distribution, signing, and archival are operator-owned.

## Scenario narrative

1. Scheduler kicks the playbook monthly with `__rollup_window__` and
   `__catalog_ref__` pinned.
2. The catalog is resolved; entries that fail
   `content-model/metrics.schema.json` are excluded and recorded
   against the catalog-staleness KRI.
3. Each remaining catalog entry is evaluated against the operator's
   telemetry / workflow / control-attestation source for the window;
   each evaluation carries its matched threshold band.
4. Evaluations are grouped by `control_refs[]` and rolled up into a
   programme-level effectiveness score in `0.0..1.0` using the
   operator's scoring policy (weights, KRI penalty, missing-evidence
   treatment).
5. If any evaluation matched its `breach` band the in-flight summary
   is annotated with a board-attention flag.
6. The structured summary artifact is emitted; the board-pack pipeline
   takes it from there.

## Files

| Layer       | File                                                  | Stable ID                                  |
|-------------|-------------------------------------------------------|--------------------------------------------|
| Playbook    | `playbook.json`                                       | `playbook.executive_metrics_rollup@v1`     |
| Metric (KPI)| `metrics/kpi.control_effectiveness_coverage.json`     | `kpi.control_effectiveness_coverage@v1`    |
| Metric (KRI)| `metrics/kri.overdue_effectiveness_tests.json`        | `kri.overdue_effectiveness_tests@v1`       |
| Metric (KRI)| `metrics/kri.metrics_catalog_staleness.json`          | `kri.metrics_catalog_staleness@v1`         |
| Compile target | `langgraph/`                                       | regenerable LangGraph graph_spec + assemble |

The portable CACAO v2 fixture the compilers consume is also published
at `tests/compilers/_shared/fixtures/executive_metrics_rollup.cacao.json`
so the shared parser and per-target compiler suites can pick it up
without reaching into `content/`.

Compile-target outputs (n8n + Temporal + LangGraph) plus their
golden-drift tests landed with the CORE card (PR #69); see
`tests/compilers/{n8n,temporal,langgraph}/test_executive_metrics_rollup.py`
and `content-model/examples/executive_metrics_rollup/langgraph/`.

Note on metric set: vuln_intake and data_exfil carry four KPI/KRI
entries each (MTTD / MTTR / coverage / control-effectiveness). The
rollup is intentionally **not** a detection or response workflow — it
consumes KPI/KRI evaluations the lower layers already produced and
does not measure detect-to-fire or fire-to-contain latency. MTTD /
MTTR therefore do not apply here, and inventing detection-shaped
identifiers for them would violate the no-invented-IDs bar. The three
metrics shipped above are exactly the set the SKELETON playbook pins
in its `x_secops_ng.metric_refs` and per-step `metric_refs`.

## Cross-reference graph

```
                  playbook.executive_metrics_rollup@v1
                  (CACAO v2 + x_secops_ng)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
  control.metrics_     control.control_       telemetry.ocsf.
  catalog_governance@  effectiveness_         security_finding@v1
  v1                   test@v1                       │
                              │                     │
                              ▼                     ▼
                kpi.control_effectiveness_coverage@v1
                kri.overdue_effectiveness_tests@v1
                kri.metrics_catalog_staleness@v1
                (measurement.inputs[].{control,telemetry}_ref +
                 playbook_refs[].step_id)
```

Every metric pins which CACAO step it measures
(`playbook_refs[].step_id`) so a dashboard compiler can render the
metric beside the step it observes without inferring topology.

## Regulatory + catalog overlay

The rollup is the agentic slice of the obligation surface that
demands recurring effectiveness reporting. Mapping packs land in
`content/mappings/` and are not re-asserted here; this section is
the documentation cross-link.

### NIS2 — Directive (EU) 2022/2555

- **Article 21(2)(f)** — *policies and procedures to assess the
  effectiveness of cybersecurity risk-management measures*. The
  rollup is the durable workflow that produces those assessment
  results on a pinned cadence. Wired in
  `content/mappings/nis2/article-21-2-f.yaml` under
  `nis2:art-21-2-f` with `control_refs: [control.control_effectiveness_test@v1]`
  and `metric_refs: [kpi.control_effectiveness_coverage@v1,
  kri.overdue_effectiveness_tests@v1]`.
- **Article 21(2)(a)** — *policies on risk analysis and information-
  system security*. Mostly governance (policy text, board approval);
  the agentic re-assessment-cadence slice is mapped under (f) above
  rather than re-asserted here.

This example does **not** anchor NIS2 Article 23 (incident reporting):
Article 23 is an event-driven obligation owned by
`playbook.data_exfil@v1`, `playbook.ransomware_containment@v1`, and
`playbook.identity_compromise@v1`, not by a periodic rollup.

### DORA — Regulation (EU) 2022/2554

- **Article 6** — *ICT risk-management framework, including periodic
  review*. The rollup is the workflow that produces the periodic
  review artifact. The mapping pack for Article 6 is not yet wired.
- **Article 19** is the incident-reporting obligation surface and is
  owned by the response playbooks, not by this rollup.

### OSCAL control catalog refs

The metric `external_refs[]` arrays pin upstream OSCAL / NIST
SP 800-53 control IDs by URL plus catalog version where one exists.
No control bodies are vendored. Anchors used by this example:

- **NIST SP 800-53 CA-2** — *Control Assessments*. The shape of
  per-control effectiveness evaluations the rollup consumes.
- **NIST SP 800-53 PM-6** — *Measures of Performance*. The shape of
  the programme-level effectiveness score the rollup emits.

### MITRE D3FEND technique IDs

D3FEND techniques cover defensive actions taken against an attack;
the rollup is a reporting workflow rather than a defensive action, so
no D3FEND technique is anchored to it. The metric / control bodies
the rollup consumes carry their own D3FEND references where they
apply; the playbook does not. This mirrors the SKELETON's
`x_secops_ng.sources` note.

### OCSF event class refs

OCSF event classes describe wire-format security events. The rollup's
inputs are catalog-shaped (metric evaluations) and its output is a
summary artifact, not an OCSF event. The single OCSF anchor it touches
is the evaluation-emitting telemetry surface:

- **Security Finding (class_uid 2001)** — `telemetry.ocsf.security_finding@v1`.
  The rollup may serialise per-metric evaluations as Security Finding
  events for operators who store evidence in their SIEM under OCSF.
  Detection-flavoured OCSF classes (Process Activity, DNS Activity)
  are **not** anchored — the rollup does not consume them.

### KPI / KRI hooks (board-readable shorthand)

The rollup itself does not pre-compute MTTD/MTTR/coverage for the
detection-shaped workflows — those KPIs live with their owning
playbooks (`playbook.vuln_intake@v1`,
`playbook.data_exfil@v1`, ...) and the rollup is what aggregates them
into the monthly board view. The rollup's own metric hooks express
how well the **effectiveness-assessment workflow itself** is
performing:

- `kpi.control_effectiveness_coverage@v1` — share of in-scope
  controls that produced at least one effectiveness-test evaluation
  in the window. The KPI hooked into NIS2 Art. 21(2)(f) and DORA
  Art. 6.
- `kri.overdue_effectiveness_tests@v1` — count of controls whose last
  effectiveness-test is older than the operator's pinned re-test
  cadence at window end. Surfaces the governance backlog independent
  of the score.
- `kri.metrics_catalog_staleness@v1` — count of catalog entries that
  either fail schema validation or have not been re-attested by the
  catalog governance owner within the review cadence. Protects the
  score from silent input erosion.

## How to validate locally

```
cd secops-ng-framework
pytest tests/ -q
```

The content-model test suite parametrises against every JSON file
under `content-model/examples/` and asserts each artifact validates
against its layer schema. The compiler suites pick up the portable
CACAO fixture and assert deterministic, byte-identical n8n / Temporal /
LangGraph output against the committed goldens (CORE).

## What this example is NOT

- Not a board-pack template. The artifact emitted is content-only;
  rendering, signing, distribution, and archival are operator-owned.
- Not authoritative for upstream catalog IDs (OSCAL / NIST 800-53,
  OCSF, MITRE D3FEND, ISO 27001, NIS2, DORA). Upstream sources are
  pinned by URL plus a control / class / article identifier where one
  exists; the example follows upstream renames by republishing the
  pointer, never by vendoring catalog bodies.
- Not a substitute for a GRC tool. The rollup feeds one; it does not
  replace one.

## Sovereignty note

The artifacts emitted here are descriptions of what the operator's
own runtime should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG
project. The operator runs the orchestrator on infrastructure they
control — we ship the structure, they own the data plane. The
reference compile targets (n8n self-hosted, Temporal, LangGraph) are
all open-source and EU-hostable; hosting the rollup on EU sovereign
infrastructure (Nebul, OVHcloud, Scaleway, Hetzner) is a deployment
choice the operator makes against this artifact, not a vendor
decision baked into it.
