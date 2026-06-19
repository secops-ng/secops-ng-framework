# DORA Article 19 technical-incident report variant — field-derivation mapping (CORE)

This document traces each field on the DORA Article 19 technical-incident
report variant schema
(`schemas/evidence/dora-art19-technical-incident-report.schema.json`)
back to the F-WF-05 `incident_management` timeline record it is derived
from. Status: **CORE**. The per-target emitter wrappers under
`compilers.{n8n,temporal,langgraph}.evidence.dora_art19_report_*` all
delegate to one framework-agnostic helper at
`compilers._shared.evidence.dora_art19_report`; the field derivations
below are the contract that helper implements.

The Commission Implementing Regulation (EU) 2024/2956 field-level
vocabulary tightening of `impact_indicators` stays deferred to the
EXTEND-schema sibling card per the original SKELETON scope split.

## Regulatory anchor

- Regulation (EU) 2022/2554 (DORA), Article 19(4) — reporting
  milestones for major ICT-related incidents.
- Regulation (EU) 2022/2554 (DORA), Article 19(2) — voluntary
  notification of significant cyber threats.
- Commission Delegated Regulation (EU) 2024/1772 — RTS on
  classification of major ICT-related incidents (Article 18(1)
  classifier; recurring-incident rule under Article 18(2)).
- Commission Implementing Regulation (EU) 2024/2956 — ITS on the
  standard forms, templates and procedures (field-level vocabulary
  tightening deferred to EXTEND).

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

The authoritative `stage -> report_variant` map is pinned by the
emitter at `compilers._shared.evidence.dora_art19_report.\
STAGE_TO_REPORT_VARIANT`; the chain ordering (which prior milestone
each variant references) is pinned by `PREVIOUS_MILESTONE_STAGE` in
the same module. The workflow-internal stage names carry no
DORA-specific suffix; the report variant's `report_variant` field is
the regulator-facing handle.

## Field derivations

### Top-level fields

| Schema field | Derived from | Notes |
|---|---|---|
| `schema_version` | constant `"1.0.0"` | Lifted from SKELETON's `"0.1.0"` at CORE landing. Bumped together with the schema on any breaking change. |
| `report_id` | `sha256(<incident_id>|<report_variant>|<submitted_at>)` (UTF-8 encoded, no separators around the pipes; `submitted_at` is the canonical `%Y-%m-%dT%H:%M:%SZ` rendering used on the wire). | Deterministic on the three inputs so a replay-vs-original comparison is a single string-equal check; produced by `derive_report_id()` in the shared emitter. |
| `report_variant` | derived from the F-WF-05 `StageName` of the regulator-submission event by the `STAGE_TO_REPORT_VARIANT` map, plus `voluntary_cyber_threat` for the Art. 19(2) lane. | See milestone-to-stage table above. |
| `incident_id` | `TimelineSession.incident_id` (UUID issued by `open_timeline()`) | Same id every milestone on the chain pins against. |
| `regulation_refs` | per-variant constants pinned by `DEFAULT_REGULATION_REFS` on the shared emitter; the operator may override with a non-empty, unique-items tuple that matches `^dora:[a-z0-9][a-z0-9.-]*$`. | Defaults: `initial_4h` → `[dora:art-19-initial-4h]`; `intermediate_72h` → `[dora:art-19-intermediate-72h]`; `final_1mo` → `[dora:art-19-final-one-month]`; `voluntary_cyber_threat` → `[dora:art-19-cyber-threat-voluntary]`. Add `dora:art-18-classification` when the classifier verdict is the load-bearing evidence. |
| `submitted_at` | `RegulatorSubmissionReceipt.submitted_at` (chain variants) or operator-supplied submission instant on the voluntary lane. | UTC-aware; canonicalised to `%Y-%m-%dT%H:%M:%SZ` on the wire so two replays of the same submission are byte-identical. |
| `submission_ref` | `RegulatorSubmissionReceipt.destination_ref` | Opaque operator-side handle, carried verbatim. Optional. |

### `classification`

The DORA Article 18(1) classifier rule pack is a sibling card
(CORE-CLASSIFIER) which has not yet landed; the CORE layer of the
report-variant emitter is wired against the existing F-WF-05
`ClassificationVerdict` shape and the operator is responsible for
populating the four DORA-specific fields on the
`DoraClassification` dataclass. When CORE-CLASSIFIER ships, the
emitter's input dataclass will be lifted onto the new verdict shape
in a non-breaking refactor (no schema bump).

| Schema field | Derived from | Notes |
|---|---|---|
| `classification.major` | `DoraClassification.major` — the DORA Article 18(1) major-classification flag, populated by the operator (and by the CORE-CLASSIFIER rule pack once it lands) against the Commission Delegated Regulation (EU) 2024/1772 materiality thresholds. | The emitter rejects non-bool input; the schema enforces field presence. The operator is responsible for not filing the Art. 19 report at all when `major` is `False`. |
| `classification.cross_border` | `DoraClassification.cross_border`, optional. At CORE this carries the same NIS2 Article 23(6) cross-border indicator the F-WF-05 `ClassificationVerdict` already exposes; CORE-CLASSIFIER will replace it with a DORA-specific cross-border materiality flag once the rule pack lands. | Optional; omitted from the emitted record when `None`. |
| `classification.recurring_incident` | `DoraClassification.recurring_incident`, optional, defaults to unset. Populated by the operator (and by the CORE-CLASSIFIER recurring-incident correlator once it lands) per the DORA Article 18(2) six-month rolling-aggregation rule. | Optional; omitted from the emitted record when `None`. The EXTEND-schema sibling adds a `recurring_cluster_ref` once the correlator lands. |
| `classification.reasons` | `DoraClassification.reasons` | Ordered tuple of human-readable rule-reason strings (1..400 chars each), carried verbatim. Public-bar text guardrails apply. |
| `classification.rule_ids` | `DoraClassification.rule_ids` | Ordered, unique policy rule ids matching `^[a-z][a-z0-9_.]*$`. The EXTEND-schema sibling tightens to the shared `dora.<class>.<rule>` alphabet once CORE-CLASSIFIER ships. |

### `timeline_refs`

| Schema field | Derived from | Notes |
|---|---|---|
| `timeline_refs.timeline_handle` | `TimelineSession.handle` | Opaque handle, carried verbatim. Length 1..200. |
| `timeline_refs.clock_started_at` | for `initial_4h` / `intermediate_72h` / `final_1mo`: `TimelineSession.opened_at` (the major-classification instant the F-WF-05 stage-clock measures from). For `voluntary_cyber_threat`: the operator-supplied awareness instant on the threat (no F-WF-05 session). | UTC-aware; canonicalised to `%Y-%m-%dT%H:%M:%SZ` on the wire. |
| `timeline_refs.stage_event_id` | `TimelineEvent.event_id` of the regulator-submission event the report corresponds to (the 16-hex-digit digest returned by `record_event()`). | Pins a replay-vs-original comparison to a single string-equal check. |
| `timeline_refs.previous_milestone_event_id` | resolved by the emitter from the `timeline_events` log on `DoraArt19ReportContext`: for `intermediate_72h` → `TimelineEvent.event_id` of the `early_warning` event; for `final_1mo` → `TimelineEvent.event_id` of the `notification` event; omitted on `initial_4h` and `voluntary_cyber_threat`. | The emitter fails closed when the prior event is missing — DORA Art. 19(4) chains every report against the preceding milestone. Field is computed, not operator-supplied, so a forged shape cannot bypass the cross-milestone pin. |

### `impact_indicators`

The Art. 19 impact indicators are populated incrementally across the
chain: most fields are empty/`None` at `initial_4h`, partially
populated at `intermediate_72h`, and fully populated at `final_1mo`.
The Commission ITS (EU) 2024/2956 field-level vocabulary tightening
of `data_loss_indicator`, `affected_functions`, and
`geographic_scope` is deferred to the EXTEND-schema sibling card —
the CORE layer pins the closed alphabet on `data_loss_indicator` and
the ISO-3166 alpha-2 pattern on `geographic_scope` so a downstream
EXTEND tightening is non-breaking.

| Schema field | Derived from | Notes |
|---|---|---|
| `impact_indicators.affected_functions` | `ImpactIndicators.affected_functions`, populated by the operator from the workflow's CACAO variables (the workflow does not currently carry a function catalogue; threading one through is the EXTEND-metrics responsibility). | Free-text (1..200 chars per entry, unique), omitted when empty. |
| `impact_indicators.affected_clients_count` | `ImpactIndicators.affected_clients_count`, operator-graded. | Non-negative integer; omitted when `None`. |
| `impact_indicators.duration_minutes` | for `final_1mo`: derived from the F-WF-05 `Lifecycle.recovered_at − Lifecycle.detected_at` and threaded through `ImpactIndicators.duration_minutes` by the workflow's evidence-emission step (the same value the F-CP-02 incidents stream carries on `kpi_windows.mttr_minutes`). For earlier milestones: omitted while the incident is still open. | Non-negative float; omitted when `None`. |
| `impact_indicators.geographic_scope` | `ImpactIndicators.geographic_scope`, operator-supplied ISO-3166 alpha-2 codes. | Pattern-pinned (`^[A-Z]{2}$`), unique. Empty/omitted when unknown. |
| `impact_indicators.data_loss_indicator` | `ImpactIndicators.data_loss_indicator`, populated by the operator from the F-WF-05 `ClassificationVerdict.severity` band plus an operator-supplied CIA-triad classifier. | Closed alphabet at CORE: `none` / `confidentiality` / `integrity` / `availability` / `multiple` / `unknown`. EXTEND lifts the enum into a shared vocabulary at `schemas/dora_data_impact.json`. Omitted when `None`. |
| `impact_indicators.indicators_of_compromise` | `NotificationSubmission.indicators_of_compromise` (Pydantic tuple on the F-WF-05 regulator-submission contract). | 1..200 chars per entry, unique. Typically empty for `initial_4h`. |

### `mitigation_status`

| Schema field | Derived from | Notes |
|---|---|---|
| `mitigation_status.state` | for `initial_4h` / `intermediate_72h`: `"in_flight"` or `"partially_mitigated"` per operator grade. For `final_1mo`: `"remediated"` (or `"partially_mitigated"` when residual risk remains). For `voluntary_cyber_threat`: operator grade against the threat-handling posture. | CORE-layer closed alphabet: `in_flight` / `partially_mitigated` / `remediated` / `unknown`. EXTEND lifts to a shared vocabulary at `schemas/dora_mitigation_state.json`. |
| `mitigation_status.actions_in_flight` | `MitigationStatus.actions_in_flight`, populated by the operator from the per-target playbook's containment/mitigation action records. | Public-bar text guardrails apply. 1..2000 chars per entry; omitted when empty. |
| `mitigation_status.completed_actions` | `MitigationStatus.completed_actions`, populated by the operator from the per-target playbook's completed-action records on close-out. | Required (non-empty) when `report_variant == final_1mo` — the CORE emitter fails closed when the field is empty on the final-report milestone. Typically empty for earlier milestones; omitted from the emitted record when empty. |
| `mitigation_status.root_cause` | `FinalReportSubmission.root_cause` (the F-WF-05 final-report DSPy-mediated free-text field), threaded through `MitigationStatus.root_cause`. | Required when `report_variant == final_1mo` — the CORE emitter fails closed when `None` on the final-report milestone. `None` / omitted for earlier milestones. 1..4000 chars. |
| `mitigation_status.residual_risk` | `MitigationStatus.residual_risk`. Threaded from the operator's close-out narrative; the F-WF-05 `FinalReportSubmission` carries the field via the closure DSPy signature once CORE-CLASSIFIER lands. | Optional even on `final_1mo` (residual risk may be `"none material"` which the operator captures in `root_cause` instead). 1..4000 chars; omitted from the emitted record when `None`. |

### `provenance`

| Schema field | Derived from | Notes |
|---|---|---|
| `provenance.source_url` | `DoraArt19ReportContext.source_url`. Per-target convention: the compile target's run-id URL (Temporal `wf-run-...`, n8n `https://<host>/execution/<id>`, LangGraph `langgraph-run/<id>`). | Opaque to this schema; the emitter carries it verbatim. |
| `provenance.captured_at` | matches `submitted_at` (canonical `%Y-%m-%dT%H:%M:%SZ` rendering). | Byte-stable replay. |
| `provenance.commit_sha` | `DoraArt19ReportContext.commit_sha`, optional commit SHA of the content snapshot the workflow walked. | 7..64 lowercase hex chars; omitted from the emitted record when `None`. |

## Cross-milestone chain invariant

The DORA Article 19 reporting chain is **ordered**:

```
initial_4h → intermediate_72h → final_1mo
```

The CORE emitter enforces the chain by computing
`timeline_refs.previous_milestone_event_id` from the `timeline_events`
log on the context (rather than accepting it as input). Filing an
`intermediate_72h` report without a recorded `early_warning` event,
or a `final_1mo` report without a recorded `notification` event,
raises `DoraArt19EmitError` — every report past the head of the
chain must reference the preceding milestone's `stage_event_id`.

The `voluntary_cyber_threat` variant sits off-chain and has no prior
milestone; the emitter omits the field.

## Determinism and byte-parity guarantee

Same input → same record bytes, across all three compile targets.
Pinned by:

- `tests/content_model/test_dora_art19_report_variant_schema.py` —
  schema-validation and required-fields surface (already on disk).
- `tests/examples/dora_art19_report/test_golden.py` (CORE) — per-target
  byte-parity goldens under `tests/fixtures/dora_art19_report/`. Each
  target's adapter is exercised against an immutable golden and the
  three targets' goldens are pinned byte-identical at fixture-load
  time; a refactor of the shared emitter that silently changes
  serialisation is caught at the byte level.
- `examples/{n8n,temporal,langgraph}/dora_art19_report/` — runnable
  worked examples, regenerated through the per-target adapters and
  pinned byte-identical to each other.

## Out-of-scope siblings

- **CORE-CLASSIFIER** — the DORA Article 18(1) classifier rule pack
  and its integration into the F-WF-05 `ClassificationVerdict`. The
  CORE emitter accepts the existing operator-populated
  `DoraClassification`; non-breaking lift onto the new verdict shape
  once the rule pack lands.
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
