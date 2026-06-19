# Worked example: `playbook.vuln_intake@v1`

This directory is the canonical end-to-end worked example for the SecOps-NG
content model. It ties together all five layers around a single playbook
— **vulnerability intake** — so a reviewer can trace one piece of work
from initial signal to operator-facing metric without leaving the example.

## Why vuln intake

Vulnerability intake is the smallest realistic workflow that exercises
every layer. A scan finding (telemetry) is enriched with host context
(detection + control attestation) and routed by a CACAO playbook into a
triage outcome the operator can act on. The metrics layer then reports
mean-time-to-detect, mean-time-to-triage, telemetry coverage, and
control-effectiveness over a rolling window.

## Files

| Layer       | File                               | Stable ID                                 |
|-------------|------------------------------------|--------------------------------------------|
| Playbook    | `playbook.json`                    | `playbook.vuln_intake@v1`                  |
| Detection   | `detection.json`                   | `detection.powershell_encoded_cmd@v1`      |
| Control     | `control.json`                     | `control.edr_script_block_logging@v1`      |
| Telemetry   | `telemetry.json`                   | `telemetry.host_process_create@v1`         |
| Telemetry sample | `telemetry.sample.json`        | (OCSF Process Activity payload)            |
| Metric (KPI)| `metrics/kpi.mttd_critical.json`   | `kpi.mttd_critical@v1`                     |
| Metric (KPI)| `metrics/kpi.mttr_triage.json`     | `kpi.mttr_triage@v1`                       |
| Metric (KPI)| `metrics/kpi.telemetry_coverage.json` | `kpi.telemetry_coverage@v1`             |
| Metric (KRI)| `metrics/kri.control_effectiveness.json` | `kri.control_effectiveness@v1`       |

## Cross-reference graph

The graph is closed and bidirectional — every edge from one artifact
to another is mirrored on the target. The linter (when it ships) will
enforce this; for now `tests/content_model/test_vuln_intake_example.py`
asserts the closure inline.

```
                       playbook.vuln_intake@v1
                       (CACAO v2 + x_secops_ng)
                                 │
       ┌─────────────────────────┼──────────────────────────┐
       │                         │                          │
detection.                  control.                    telemetry.
powershell_                 edr_script_                 host_process_
encoded_cmd@v1              block_logging@v1            create@v1
       │                         │                          │
       │  ◄────── mutually reference ──────►                 │
       └────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    kpi.mttd_critical@v1
                    kpi.mttr_triage@v1
                    kpi.telemetry_coverage@v1
                    kri.control_effectiveness@v1
                    (measurement.inputs[].{detection,control,telemetry,playbook}_ref)
```

Every metric pins which CACAO step it measures (`playbook_refs[].step_id`)
so a dashboard compiler can render the metric beside the step it observes
without inferring topology.

## How to validate locally

```
cd secops-ng-framework
pytest tests/content_model/ -q
```

The test suite parametrises against every JSON file in this directory and
asserts:
- each artifact validates against its layer's schema,
- the cross-reference graph is closed (every edge has a mirror),
- every metric input that names a `*_ref` resolves to a sibling artifact
  in this example,
- the OCSF sample payload's `class_uid` matches the telemetry binding's
  `class_uid`.

## What this example is NOT

- Not a runnable playbook. Compile targets (n8n / Temporal / LangGraph)
  are responsible for execution; this is the portable content.
- Not a normative source for upstream IDs (Sigma rule, OSCAL catalog,
  OCSF class, D3FEND / ATT&CK technique). Upstream sources are pinned
  by URL + commit / version; the example follows upstream renames by
  republishing the pointer, never by vendoring rule bodies.
- Not an exhaustive metrics catalog. The four metrics here demonstrate
  one of each common shape (latency KPI, count KPI, coverage KPI,
  risk KRI). The full catalog lives elsewhere in the content tree.
