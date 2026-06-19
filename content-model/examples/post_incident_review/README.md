# Worked example: `playbook.post_incident_review@v1`

End-to-end worked example for the SecOps-NG content model, following
the same shape as `content-model/examples/vuln_intake/` and
`content-model/examples/data_exfil/`. Ties together every layer that
applies (playbook \u2192 controls \u2192 telemetry \u2192 metrics) plus regulatory
overlays (NIS2, DORA, CRA) and external catalog references (OSCAL,
MITRE D3FEND, OCSF) around a single scenario: a structured, blameless
post-incident review that turns each closed incident into auditable,
restartable state for the operator's lessons-learned programme.

The review anchors NIS2 Article 23(4)(d) (final report one month after
notification) and DORA Article 19(4)(c) (final report one month after
the intermediate report) without prescribing a specific reporting
template \u2014 those are jurisdiction- and operator-specific and live in
the regulatory mapping packs.

## Why post-incident review

Detection, control, telemetry, and response playbooks all produce
per-event evidence. NIS2 and DORA additionally require a structured,
defensible learning record after every closed incident, with a final
report submitted on a one-month clock. Post-incident review is the
smallest realistic workflow that closes the loop: it consumes the
incident's evidence record (including upstream anti-forensics /
audit-tampering Sigma references when they fired in the incident
window), produces a blameless review artifact, and registers the
resulting corrective actions for follow-through. Distribution, signing,
and archival of the regulator-facing report are operator-owned.

## Scenario narrative

1. Scheduler kicks the playbook on incident close with `__incident_id__`
   pinned.
2. `timeline collation` builds the chronology, flags evidence gaps via
   the bound anti-forensics / audit-tampering Sigma references, and
   sets `__evidence_gaps_present__`.
3. `blameless review template` records decisions taken (including
   decisions made under partial evidence), contributing factors, and
   learnings. Output is the review artifact at `__review_artifact__`.
4. `corrective action tracking` registers each raised action on the
   corrective-action register (owner, due date, status) bound to
   `control.corrective_action_register@v1`. Output is the register
   handle at `__corrective_action_register__`.
5. An OCSF Incident Finding is emitted at completion so downstream
   control-effectiveness rollups, board-pack pipelines, and
   regulator-facing final-report compilers consume a single shape.

## Files

| Layer        | File                                                  | Stable ID                                       |
|--------------|-------------------------------------------------------|-------------------------------------------------|
| Playbook     | `../../../content/playbooks/post_incident_review/playbook.cacao.json` | `playbook.post_incident_review@v1`              |
| Control      | `control.json`                                        | `control.blameless_review@v1`                   |
| Control      | `control.corrective_action_register.json`             | `control.corrective_action_register@v1`         |
| Telemetry    | `telemetry.json`                                      | `telemetry.ocsf.incident_finding@v1`            |
| Metric (KPI) | `metrics/kpi.timeline_completeness.json`              | `kpi.timeline_completeness@v1`                  |
| Metric (KPI) | `metrics/kpi.review_completion_sla.json`              | `kpi.review_completion_sla@v1`                  |
| Metric (KPI) | `metrics/kpi.corrective_action_close_rate.json`       | `kpi.corrective_action_close_rate@v1`           |
| Metric (KRI) | `metrics/kri.corrective_action_overdue.json`          | `kri.corrective_action_overdue@v1`              |

The portable CACAO v2 fixture the compilers consume is also published
at `tests/compilers/_shared/fixtures/post_incident_review.cacao.json`
so the shared parser and per-target compiler suites can pick it up
without reaching into `content/`.

Compile-target outputs landed across the three CORE cards:

- n8n: `tests/compilers/n8n/test_post_incident_review.py` (PR #79)
- Temporal: `tests/compilers/temporal/test_post_incident_review.py` (PR #74)
- LangGraph: `examples/langgraph/post_incident_review/` plus
  `tests/compilers/langgraph/test_post_incident_review.py` (PR #86)

The detection layer is intentionally **not** authored here. Detection
of anti-forensics / audit-tampering during the incident window is
covered by upstream SigmaHQ rules referenced via the playbook's
`external_references` block, not re-authored by SecOps-NG. The
playbook's README lists the seven spot-checkable rule IDs.

Note on metric set: vuln_intake and data_exfil carry detection-shaped
MTTD / MTTR metrics because they are detection-and-response workflows.
Post-incident review is not. It runs **after** incident close, on a
one-month clock anchored on NIS2 Art. 23(4)(d) and DORA Art. 19(4)(c).
The four metrics shipped here \u2014 timeline-completeness KPI, review-SLA
KPI, corrective-action close-rate KPI, and corrective-action overdue
KRI \u2014 are exactly the set the SKELETON playbook pins in its
`x_secops_ng.metric_refs`. Inventing detection-shaped identifiers for
this workflow would violate the no-invented-IDs bar.

## Cross-reference graph

```
                   playbook.post_incident_review@v1
                   (CACAO v2 + x_secops_ng)
                              \u2502
        \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
        \u2502                     \u2502                     \u2502
  upstream Sigma          control.                  telemetry.ocsf.
  anti-forensics /        blameless_review@v1       incident_finding@v1
  audit-tampering         control.corrective_              \u2502
  rule references         action_register@v1               \u2502
  (external_references)         \u2502                          \u2502
                                \u25bc                          \u25bc
                kpi.timeline_completeness@v1
                kpi.review_completion_sla@v1
                kpi.corrective_action_close_rate@v1
                kri.corrective_action_overdue@v1
                (measurement.inputs[].{control,telemetry,playbook}_ref +
                 playbook_refs[].step_id)
```

Every metric pins which CACAO step it measures
(`playbook_refs[].step_id`) so a dashboard compiler can render the
metric beside the step it observes without inferring topology.

## Regulatory cross-references

The post-incident review playbook is already named in the regulatory
mapping packs under `content/mappings/`. This EXTEND card additionally
wires the four metrics above onto the obligations they support, so the
obligation \u2192 playbook \u2192 metric chain resolves end-to-end:

| Regime | Article | Mapping entry                       | What this playbook + metrics evidence                 |
|--------|---------|-------------------------------------|-------------------------------------------------------|
| NIS2   | 21(2)(b)| `nis2:art-21-2-b`                   | Incident handling: capture lessons learned per incident |
| NIS2   | 23(4)(d)| `nis2:art-23-final-report`          | Final report no later than one month after notification |
| DORA   | 18(2)   | `dora:art-18-recurring-incident`    | Treat recurring incidents with the same root cause as major |
| DORA   | 19(4)(c)| `dora:art-19-final-one-month`       | Final report one month after intermediate report      |
| CRA    | 14(3)   | `cra:art-14-final-report`           | Final report on a severe incident                     |

Article texts are quoted verbatim in the mapping packs; this table is a
pointer table only.

## How to validate locally

```
cd secops-ng-framework
pytest tests/ -q
```

The content-model test suite parametrises the layer schemas against
every JSON file under `content-model/examples/` and asserts each
artifact validates against its schema. The mapping-pack test suite
under `tests/content/test_mappings.py` validates every regime YAML
against `schemas/mapping.schema.json` and enforces id uniqueness across
the whole tree. The compiler suites under `tests/compilers/{n8n,
temporal,langgraph}/test_post_incident_review.py` exercise the shared
CACAO fixture against each compile target and pin the byte-for-byte
goldens against drift.

## Sovereignty note

The post-incident review artifact is the operator's evidence record.
SecOps-NG ships the content shape and the bindings; the artifact
itself, the corrective-action register, and the regulator-facing final
report are emitted by the operator's compile target into the operator's
data plane. There is no SecOps-NG-hosted plane that sees an operator's
incident record. The same sovereignty boundary holds for the OCSF
Incident Finding emitted at completion \u2014 it is consumed by the
operator's dashboards, board-pack pipeline, and regulator-submission
compiler, all of which sit inside the operator's environment.

EU-hostable runtimes (Nebul, OVHcloud, Scaleway, Hetzner) are first-class
for the three reference compile targets; AI-provider neutrality is
enforced at the artifact layer so a switch between providers does not
require re-authoring the playbook or its bindings.

## What this example is NOT

- Not a runnable playbook. Compile targets (n8n / Temporal / LangGraph)
  are the SKELETON's downstream consumers; runnable artifacts are
  authored by the CORE cards (PRs #74, #79, #86).
- Not authoritative for upstream IDs. Sigma rule IDs (anti-forensics /
  audit-tampering), OSCAL catalog control-ids, OCSF class UIDs, and
  MITRE D3FEND technique IDs are pinned by URL plus a commit / version
  where one exists; this example follows upstream renames by
  republishing the pointer, never by vendoring rule or catalog bodies.
- Not the place where final-report submission templates are encoded.
  Submission content shape is jurisdiction-specific (NIS2 Art. 23 /
  DORA Art. 19 / CRA Art. 14) and bound at compile time by the mapping
  pack the operator selects; the framework's templates mirror the
  upstream ITS / RTS where one exists.

## Out of scope here

- Compiler outputs (`examples/{n8n,temporal,langgraph}/post_incident_review/`)
  and their golden tests. Owned by the three CORE cards.
- Regulator-facing final-report submission transport. Operator-owned.
- Re-authoring of upstream anti-forensics / audit-tampering Sigma
  rules. SecOps-NG does not re-author Sigma; the playbook references
  upstream IDs only.
