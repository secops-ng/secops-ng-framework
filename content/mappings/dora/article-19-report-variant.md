# DORA Article 19 technical-incident report variant — field-derivation mapping (SKELETON)

This document traces each field on the DORA Article 19 technical-incident
report variant schema
(`schemas/evidence/dora-art19-technical-incident-report.schema.json`)
back to the F-WF-05 `incident_management` timeline record it is derived
from. Status: **SKELETON**. Unresolved derivations are marked
`TODO(CORE)` and are out of scope for this card; they will be tightened
in the F-SV-03 CORE sibling once the per-target emitters are exercised
end-to-end.

## Regulatory anchor

- Regulation (EU) 2022/2554 (DORA), Article 19(4) — reporting
  milestones for major ICT-related incidents.
- Commission Implementing Regulation (EU) 2024/2956 — ITS on the
  standard forms, templates and procedures (field-level vocabulary;
  out of SKELETON scope, tightened in EXTEND).
- Commission Delegated Regulation (EU) 2024/1772 — RTS on
  classification of major ICT-related incidents (Article 18(1)
  classifier; recurring-incident rule under Article 18(2)).

## Upstream artifact

The report variant is derived from the F-WF-05 incident-management
timeline records:

- `TimelineSession` — one per `incident_id`, returned by
  `open_timeline()` in
  `content/playbooks/incident_management/primitives/timeline_binding.py`.
- `TimelineEvent[]` — appended to `TimelineSession.events` by
  `record_event()` at each of the three regulator-submission stages
  (and by `open_timeline()` / `close_timeline()` at the chain
  endpoints).
- `RegulatorSubmissionReceipt` — returned by the regulator-submission
  action (see
  `content/playbooks/incident_management/primitives/regulator_submission.py`).
- `TimelineClosure` — returned by `close_timeline()` at the end of the
  workflow.
- `ClassificationVerdict` — output of `classify_significance()` in
  `content/playbooks/incident_management/primitives/classification.py`.
- `FinalReportSubmission` — Pydantic v2 payload returned by the
  one-month final-report stage (free-text fields are the workflow's
  only DSPy reach; see `primitives/signatures.py`).

## Milestone-to-stage mapping

The four entries on the DORA Article 19 chain map onto the F-WF-05
`StageName` alphabet (`stage_clock.py`) as follows:

| DORA Article 19 milestone | enum value (`schemas/dora_art19_report_milestone.json`) | F-WF-05 `StageName` | regulator window |
|---|---|---|---|
| Art. 19(4)(a) initial notification | `initial_4h` | `early_warning` | 4h from major classification (≤24h from awareness) |
| Art. 19(4)(b) intermediate report | `intermediate_72h` | `notification` | 72h from major classification |
| Art. 19(4)(c) final report | `final_1mo` | `final_report` | one month from intermediate (30d in the stage-clock) |
| Art. 19(2) voluntary cyber-threat notification | `voluntary_cyber_threat` | — | no mandatory clock; lighter content shape |

The stage-clock duration interpretation is documented in the
`stage_clock.py` module docstring. The workflow-internal stage names
carry no DORA-specific suffix; the report variant's `report_variant`
field is the regulator-facing handle.

## Field derivations

### Top-level fields

| Schema field | Derived from | Notes |
|---|---|---|
| `schema_version` | constant `"0.1.0"` | SKELETON layer; lifts to `1.0.0` in CORE. |
| `report_id` | `sha256(<incident_id>|<report_variant>|<submitted_at>)` | Deterministic on the three inputs so a replay-vs-original comparison is a single string-equal check. |
| `report_variant` | derived from the F-WF-05 `StageName` of the regulator-submission event by suffixing the regulator window, plus `voluntary_cyber_threat` for the Art. 19(2) lane. | See milestone-to-stage table above. |
| `incident_id` | `TimelineSession.incident_id` (UUID issued by `open_timeline()`) | Same id every milestone on the chain pins against. |
| `regulation_refs` | constant per `report_variant` plus optional `dora:art-18-classification` when the classifier verdict is carried | `initial_4h` → `[dora:art-19-initial-4h]`; `intermediate_72h` → `[dora:art-19-intermediate-72h]`; `final_1mo` → `[dora:art-19-final-one-month]`; `voluntary_cyber_threat` → `[dora:art-19-cyber-threat-voluntary]`. |
| `submitted_at` | `RegulatorSubmissionReceipt.submitted_at` | UTC-aware instant the submission was dispatched. |
| `submission_ref` | `RegulatorSubmissionReceipt.destination_ref` | Opaque operator-side handle, carried verbatim. Optional at SKELETON. |

### `classification`

The DORA Article 18(1) classifier is **not yet** wired into the F-WF-05
classification primitive (the existing primitive is NIS2 Article 23(3)
significance + Article 23(6) cross-border). The SKELETON layer carries
a parallel-flag shape that mirrors the NIS2 `ClassificationVerdict`
dataclass; the CORE sibling card tightens this once the DORA rule pack
lands.

| Schema field | Derived from | Notes |
|---|---|---|
| `classification.major` | `TODO(CORE)`: replace with the dedicated DORA Article 18(1) major flag from a DORA-aware `ClassificationVerdict`. At SKELETON, an emitter sets this from the NIS2 `significant` flag as a stand-in (a NIS2-significant incident is also typically DORA-major, but the materiality thresholds differ and the EU 2024/1772 RTS criteria must be applied to make the call). | Emitter is responsible for not filing an Art. 19 report at all when `major == false`; schema only enforces field presence. |
| `classification.cross_border` | `ClassificationVerdict.cross_border` (NIS2 Article 23(6)) | Used at SKELETON as a stand-in for the DORA cross-border materiality criteria. `TODO(CORE)`: replace with a DORA-specific cross-border indicator once the rule pack lands. |
| `classification.recurring_incident` | `TODO(CORE)`: DORA Article 18(2) recurring-incident rule. Requires the `control.recurring_incident_correlator@v1` control (see `content/mappings/dora/article-19-and-28.yaml` entry `dora:art-18-recurring-incident`) which is not yet on disk. SKELETON emitter sets this to `false` unless the operator threads in an explicit recurring-cluster reference. | EXTEND-schema sibling tightens with a `recurring_cluster_ref`. |
| `classification.reasons` | `ClassificationVerdict.reasons` | Ordered list of human-readable rule-reason strings, carried verbatim. |
| `classification.rule_ids` | `ClassificationVerdict.rule_ids` (or the DORA-aware verdict's rule ids once the rule pack lands) | `TODO(CORE)`: tighten to a shared `dora.<class>.<rule>` alphabet once the DORA rule pack lands. |

### `timeline_refs`

| Schema field | Derived from | Notes |
|---|---|---|
| `timeline_refs.timeline_handle` | `TimelineSession.handle` | Opaque handle, carried verbatim. |
| `timeline_refs.clock_started_at` | for `initial_4h` / `intermediate_72h` / `final_1mo`: `TimelineSession.opened_at` (the major-classification instant the F-WF-05 stage-clock measures from). For `voluntary_cyber_threat`: the operator's awareness instant on the threat. | UTC-aware. |
| `timeline_refs.stage_event_id` | `TimelineEvent.event_id` of the regulator-submission event the report corresponds to (the 16-hex-digit digest returned by `record_event()`). | Pins a replay-vs-original comparison to a single string-equal check. |
| `timeline_refs.previous_milestone_event_id` | for `intermediate_72h`: `TimelineEvent.event_id` of the `early_warning` event. For `final_1mo`: `TimelineEvent.event_id` of the `notification` event. `null` for `initial_4h` and `voluntary_cyber_threat`. | `TODO(CORE)`: pin required for `intermediate_72h` and `final_1mo` via an oneOf/conditional refinement once the per-target emitter work lands. |

### `impact_indicators`

The Art. 19 impact indicators are populated incrementally across the
chain: most fields are `TODO` at `initial_4h`, partially populated at
`intermediate_72h`, and fully populated at `final_1mo`. The
Commission ITS (EU) 2024/2956 field-level vocabulary is **not** pinned
at the SKELETON layer.

| Schema field | Derived from | Notes |
|---|---|---|
| `impact_indicators.affected_functions` | `TODO(CORE)`: operator-supplied identifiers for critical or important functions. F-WF-05 does not currently carry a function catalogue; the CORE sibling card threads one through the workflow's CACAO variables. | Free-text at SKELETON. |
| `impact_indicators.affected_clients_count` | `TODO(CORE)`: operator-graded count not currently carried by F-WF-05. CORE sibling threads it through the workflow's CACAO variables. | `null` allowed at SKELETON. |
| `impact_indicators.duration_minutes` | derived from `incidents.schema.json` lifecycle markers: `recovered_at - detected_at`. `null` while the incident is still open. | `TODO(CORE)`: thread the `kpi_windows` computation across to this field at emission time. |
| `impact_indicators.geographic_scope` | `TODO(CORE)`: operator-supplied ISO-3166 codes. F-WF-05 does not currently carry a geography list; the CORE sibling threads one through. | Empty array allowed at SKELETON. |
| `impact_indicators.data_loss_indicator` | `TODO(CORE)`: derive from the F-WF-05 `ClassificationVerdict.severity` band (already on the incidents evidence schema) plus an operator-supplied CIA-triad classifier. EXTEND-schema sibling lifts the enum into a shared vocabulary. | `"unknown"` at SKELETON when underived. |
| `impact_indicators.indicators_of_compromise` | `NotificationSubmission.indicators_of_compromise` (Pydantic tuple on the F-WF-05 regulator-submission contract). | Empty tuple allowed; typical for `initial_4h`. |

### `mitigation_status`

| Schema field | Derived from | Notes |
|---|---|---|
| `mitigation_status.state` | for `initial_4h` / `intermediate_72h`: `"in_flight"` or `"partially_mitigated"` per operator grade. For `final_1mo`: `"remediated"` (or `"partially_mitigated"` when residual risk remains). | SKELETON-layer enum; EXTEND lifts to a shared vocabulary. |
| `mitigation_status.actions_in_flight` | `TODO(CORE)`: derive from the per-target playbook's containment / mitigation action records. F-WF-05 does not currently carry an action log; the CORE sibling threads one through. | Public-bar text guardrails apply. |
| `mitigation_status.completed_actions` | `TODO(CORE)`: derive from the per-target playbook's completed-action records on close-out. CORE sibling threads it through. | Required content for `final_1mo`; empty for earlier milestones. |
| `mitigation_status.root_cause` | `FinalReportSubmission.root_cause` (the F-WF-05 final-report DSPy-mediated free-text field). | `null` for milestones other than `final_1mo`. `TODO(CORE)`: pin required when `report_variant == final_1mo` via an oneOf/conditional refinement. |
| `mitigation_status.residual_risk` | `TODO(CORE)`: not currently carried by F-WF-05. The CORE sibling adds a `residual_risk` free-text field to `FinalReportSubmission` so the final-report DSPy signature populates it. | `null` for milestones other than `final_1mo`. |

### `provenance`

| Schema field | Derived from | Notes |
|---|---|---|
| `provenance.source_url` | compile target's run-id URL (opaque to this schema). | Per-target; not pinned by SKELETON. |
| `provenance.captured_at` | matches `submitted_at`. | |
| `provenance.commit_sha` | optional commit SHA of the content snapshot the workflow walked. | |

## Out-of-scope siblings

- **CORE-WIRE-{N8N,TMP,LG}** — per-target compiler bindings that read
  the F-WF-05 timeline records and emit reports conforming to this
  schema. Replaces every `TODO(CORE)` marker above.
- **CORE-CLASSIFIER** — the DORA Article 18(1) classifier rule pack
  and its integration into the F-WF-05 `ClassificationVerdict`.
- **EXTEND-SCHEMA** — shared vocabularies at
  `schemas/dora_data_impact.json`,
  `schemas/dora_mitigation_state.json`, and the Commission ITS (EU)
  2024/2956 field-level tightening of `impact_indicators`.
- **EXTEND-METRICS** — DORA-side companion KPIs to the existing NIS2
  Art. 23 milestone KPIs
  (`kpi.dora_initial_4h_on_time@v1`,
  `kpi.dora_intermediate_72h_on_time@v1`,
  `kpi.dora_final_on_time@v1` already declared on the regulatory
  mapping; the per-milestone KPI specs themselves are tightened in
  EXTEND-METRICS).
- **ROADMAP** — flipping F-SV-03 to Shipped is out of SKELETON scope
  and lives with the CORE sibling cards.
