# content/metrics/ — KPI / KRI catalog

The metrics catalog is a curated set of operational and risk indicators
that playbooks, detections, and controls in this framework reference by
stable identifier. It is intentionally a thin overlay: SecOps-NG does
not define a new metrics standard. Each entry names a common operator
metric (MTTD, MTTR, coverage, false-positive rate, control
effectiveness, …) and binds it to the lower content layers through the
shared `stable_id` shape used everywhere else in the content model.

## Scope

The catalog answers, for every metric a playbook author wants to emit
or affect:

- What does this metric mean, in one paragraph an operator can read?
- What inputs does it consume — which telemetry classes, detections,
  controls, or playbook step transitions?
- How is it aggregated (p95 latency, ratio, count, …) and over what
  window?
- Is lower or higher better, and what target / threshold bands does the
  community recommend?
- Which upstream regulatory references (NIS2, DORA, ENISA guidance,
  ISO 27004, CIS measures) motivate it?

The catalog is **not** an executable runtime. It is the contract.
Compile targets (n8n / Temporal / LangGraph references in this repo,
plus any community-contributed compiler) are the source of truth for
the executable form.

## ID convention

Stable identifier shape is shared with every other content layer:

```
<namespace>.<slug>@v<major>[.<minor>[.<patch>]]
```

For the metrics catalog the namespace MUST be one of:

- `kpi.*` — performance indicator (how well operations are running),
- `kri.*` — risk indicator (how much residual exposure remains).

The namespace prefix and the `kind` field must agree. The full lexical
shape and the kpi/kri agreement constraint are enforced by the schema.

Examples:

- `kpi.mttd_critical@v1` — mean time to detect, critical-severity
  scope, content version 1.
- `kri.control_effectiveness@v1` — residual exposure indicator from
  control attestation state.

## KPI vs KRI — when to pick which

| Question                                                | Answer is a |
|---------------------------------------------------------|-------------|
| "How fast / well / completely did we run an operation?" | KPI         |
| "How much residual risk remains after our controls?"    | KRI         |

A latency or completion rate is almost always a KPI. A coverage gap, a
suppression rate, an overdue-effectiveness ratio, or a regulator
notification overrun is almost always a KRI. When in doubt, ask
whether the value rising is bad news for the operator (KRI) or for the
ops team's running scorecard (KPI).

## Link policy — how playbooks reference catalog entries

A shipped playbook MUST reference a metric by its catalog `stable_id`,
not by inlining its definition. The two link directions are:

1. **Playbook → metric.** Playbook KPI/KRI hooks list catalog
   `stable_id`s in their `metric_ref` (or equivalent) field.
2. **Metric → playbook.** Catalog entries MAY list `playbook_refs`,
   each pointing to a playbook `stable_id` and optionally pinning a
   specific step. This is documentation; the linter checks target
   existence.

The same shape applies to `detection_refs`, `control_refs`, and
`telemetry_refs` on catalog entries — they bind to the corresponding
layers' `stable_id`s.

OSCAL/D3FEND control mappings under `content/mappings/` may also
reference catalog metrics when a control's effectiveness is defined in
terms of a KPI or KRI; the link direction is the same — by
`stable_id`, never by inlined definition.

## Catalog index

The current catalog at a glance. The `primary regulatory anchors`
column is derived from each entry's `external_refs` (regulator-level
anchors, not the full list); the `mapping back-refs` column points to
the `metric_refs:` entries under `content/mappings/{nis2,dora}/` that
list this catalog id, so the cross-reference is closed in both
directions.

| stable_id                       | kind | unit    | direction          | primary regulatory anchors                  | mapping back-refs                                                |
|---------------------------------|------|---------|--------------------|---------------------------------------------|------------------------------------------------------------------|
| `kpi.mttd@v1`                   | kpi  | minutes | lower_is_better    | NIS2 Art. 21(2)(b)                          | `nis2:art-21-2-b`                                                |
| `kpi.mttr_critical@v1`          | kpi  | minutes | lower_is_better    | NIS2 Art. 21(2)(b); NIS2 Art. 23; DORA Art. 19(4)(a) | `nis2:art-21-2-b`; `dora:art-19-initial-4h`             |
| `kpi.detection_coverage@v1`     | kpi  | ratio   | higher_is_better   | NIS2 Art. 21(2)(b)                          | `nis2:art-21-2-b`                                                |
| `kpi.false_positive_rate@v1`    | kpi  | ratio   | lower_is_better    | NIS2 Art. 21(2)(b)                          | `nis2:art-21-2-b`                                                |
| `kri.control_effectiveness@v1`  | kri  | ratio   | lower_is_better    | NIS2 Art. 21(2)(f); NIS2 Art. 21            | `nis2:art-21-2-f`                                                |

DORA-side anchors on the unscoped detect-pillar baselines (MTTD,
detection coverage, FP rate) are intentionally absent because the
DORA Art. 19 clocks start at classification-as-major, not at first
detection; the per-metric YAML's `external_refs` block carries a
one-line comment explaining why each empty slot is empty, and points
at the natural follow-on (severity-scoped variants, vulnerability
management, supplier register) that does carry a DORA anchor in the
mappings tree.

## Schema location

The canonical schema for catalog entries lives at:

- `content-model/metrics.schema.json` — JSON Schema Draft 2020-12.

The `content/metrics/_schema/metric.schema.json` file in this
directory is a thin pointer that re-exports the canonical schema, so
catalog authors and validators inside `content/metrics/` can resolve
the schema with a local relative path.

## File layout

```
content/metrics/
├── README.md                   # this file
├── _schema/
│   └── metric.schema.json      # pointer to content-model/metrics.schema.json
├── mttd.yaml                   # seed KPI entry (SKELETON exemplar)
├── mttr.yaml                   # KPI: mean time to respond (critical)
├── detection_coverage.yaml     # KPI: ATT&CK technique coverage
├── false_positive_rate.yaml    # KPI: FP/(FP+TP) per detection class
├── control_effectiveness.yaml  # KRI: residual exposure from attestations
└── …                           # one YAML per catalog entry
```

One catalog entry per YAML file. The filename SHOULD be the slug
portion of the `stable_id` (e.g. `mttd_critical.yaml` for
`kpi.mttd_critical@v1`); the seed entry uses the short form
`mttd.yaml` as a deliberately minimal exemplar.

## Forward-public hygiene reminder

Per the project directive on forward-public hygiene, every catalog
entry — fields, prose, `maintainer`, `external_refs` — must already
pass the public-release bar: community-neutral language, no commercial
framing, no individual contact names (generic role mailboxes only), no
internal infra references, no credentials.

## Current state (v0 CORE: bidirectional links closed; EXTEND populates additional KPI/KRI entries)

SKELETON scaffolded the directory and seed (`mttd.yaml`). CORE added
the unscoped baseline KPIs (MTTR, coverage, false-positive) and the
control-effectiveness KRI. EXTEND closed regulatory back-refs into
`content/mappings/{nis2,dora}/` and added the catalog cross-reference
table above. EXTEND-2 shipped 28 additional granular catalog entries
to back the `metric_ref`s already encoded in shipped playbooks — MTTD
family (phishing, ransomware, exfil, cloud misconfig, identity
compromise, threat-intel indicator), MTTR/MTTC family (containment,
phishing triage, cloud-misconfig remediation, blocklist propagation,
on-call ack, identity_compromise containment), coverage family (cloud
posture, on-call schedule, threat-intel feed, lateral-hunt), five
KRIs (recurring cloud misconfig, regulator-notification overrun,
phishing suppression, escalation-tier breach, corrective-action
overdue), and a no-clean-home set (backup integrity, notification SLA,
handoff-brief SLA, timeline completeness, review completion SLA,
corrective-action close rate, phishing-sim click rate).

The current layer (CORE link-closure) walks every shipped CACAO
playbook under `content/playbooks/*/playbook.cacao.json`, resolves
each step-level `metric_ref` against the catalog, and populates the
corresponding catalog entry's `playbook_refs[]` with one back-reference
per (playbook stable_id, step_id) pair so the loop is closed in both
directions. A focused linter — `tests/content/test_metrics_catalog_links.py`
— asserts (a) every playbook `metric_ref` resolves to a catalog
`stable_id`, (b) every catalog `playbook_refs[]` entry resolves to a
shipped playbook and (when pinned) to an existing workflow step, and
(c) the `kpi.*` / `kri.*` namespace prefix agrees with the entry's
`kind` at the link level.

## OCSF source-data-shape binding lint (G-04)

The catalogue-wide OCSF source-data-shape dimension of the G-04
catalogue-maturity KPI is enforced by
`tools/lint_catalogue_ocsf_bindings.py`: every operator-telemetry
(non-composite) metric in this directory must declare at least one
`telemetry.ocsf.*` ref, and every declared ref must resolve to a
shipped class file under `content/telemetry/<ref>.json`. Composite
metrics (those whose only source is other catalogue entries) are
exempt. Run it locally with:

```sh
python -m tools.lint_catalogue_ocsf_bindings --format text
```

It rides the `catalogue-ocsf-bindings` job in
`.github/workflows/orphan-ci.yml` alongside the per-cluster
`posture-ocsf-bindings` (asset/patch posture cluster) and
`detection-ocsf-bindings` (detection-latency / `mttd_*` cluster) lanes
— same nightly 02:23 UTC schedule, same PR-on-touch and push-on-main
triggers. The per-cluster jobs are finer-grained classifiers kept
green by construction; the catalogue-wide job is the structural floor
that catches a new metric shipped without any OCSF binding before it
reaches main.

The remaining baseline entries (`kpi.mttd@v1`, `kpi.mttr_critical@v1`,
`kpi.detection_coverage@v1`, `kpi.false_positive_rate@v1`,
`kri.control_effectiveness@v1`) intentionally keep `playbook_refs: []`
for now: shipped playbooks pin the granular EXTEND-2 variants instead.
Future EXTEND layers populate additional KPI/KRI entries (severity-
scoped MTTR variants, dwell-time, vulnerability-management KRIs,
supplier-register risk) and extend the back-reference fabric as new
playbooks ship.
