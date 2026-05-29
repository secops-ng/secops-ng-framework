# Content model — mid layer (detection / control / telemetry)

This directory holds the **mid-layer schemas** of the SecOps-NG content model. The upper layer is the playbook schema (sibling branch `coder/content-model-playbook-v2`); the lower layer is the metrics catalog plus an end-to-end worked example (sibling branch `coder/content-model-metrics`). This branch lands the three middle layers and the way they join.

## Stable ID model

Every layer of the content model addresses every other layer with the **same lexical stable_id shape** that the playbook schema defines:

```
<namespace>.<slug>@v<semver>
```

Pattern (shared by all five layers):

```
^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$
```

| Layer       | Namespace prefix     | Schema                                  | Example                                  |
|-------------|----------------------|------------------------------------------|------------------------------------------|
| Playbook    | `playbook.`          | `playbook.schema.json` *(sibling)*      | `playbook.vuln_intake@v1`                |
| Detection   | `detection.`         | `detection.schema.json`                  | `detection.powershell_encoded_cmd@v1`    |
| Control     | `control.`           | `control.schema.json`                    | `control.edr_script_block_logging@v1`    |
| Telemetry   | `telemetry.`         | `telemetry.schema.json`                  | `telemetry.host_process_create@v1`       |
| Metric      | `kpi.` / `kri.`      | `metrics.schema.json` *(sibling)*       | `kpi.mttd_critical@v1`                   |

A SecOps-NG playbook step (CACAO `workflow.step.x_secops_ng`) references mid-layer artifacts via:

```yaml
detection_refs:  [detection.powershell_encoded_cmd@v1]
control_refs:    [control.edr_script_block_logging@v1]
telemetry_refs:  [telemetry.host_process_create@v1]
```

…and each mid-layer artifact lists which playbooks (and optionally which CACAO steps) it belongs to via `playbook_refs[].playbook_id` plus optional `playbook_refs[].step_id`. The graph is **bidirectional by construction**, so any layer can serve as the entry point for review.

> Cross-layer referential integrity (target stable_id actually exists) is **not** enforced by JSON Schema. That belongs in the compiler / linter — see the forward-public hygiene linter and the upcoming content-model linter for where this lands.

## What each schema is — and explicitly is not

### `detection.schema.json` — Sigma rule POINTERS

* Captures `sigma.rule_id`, `sigma.repo`, optional `sigma.path` and `sigma.commit` pin.
* Carries an operator-facing overlay: stable_id, severity, content_version, maturity, logsource summary, cross-refs.
* **We never fork Sigma rule bodies.** Consumers MUST resolve the rule from the upstream repository at the pinned commit. If the rule is renamed or removed upstream, our pointer becomes invalid — that is the correct failure mode, not a reason to vendor the rule.

### `control.schema.json` — OSCAL component + D3FEND technique

* `oscal.component` is a faithful fragment of a NIST OSCAL component-definition (component → control-implementations → implemented-requirements). Consumers can lift this into a full component-definition without translation.
* `d3fend.technique_id` ties the control to a MITRE D3FEND defensive technique (the "how"), while `attack_counters[]` lists the MITRE ATT&CK techniques the control is designed to counter.
* **We do not invent control catalogs.** Catalog references (`control-id`, `source`) point at upstream sources (NIST 800-53, ISO 27001, NIS2 articles, community profiles).

### `telemetry.schema.json` — OCSF class binding + sample payload pointer

* Binds the content layer to an OCSF event class (`version`, `category_uid`, `class_uid`, optional `activity_id`, `profiles`).
* `fields_used[]` lists the dot-paths into the OCSF event our content actually reads or writes — a thin contract so reviewers can reason about compatibility without diffing the full OCSF schema.
* `sample.path` points to a canonical sample payload kept beside the binding (out-of-line to keep schema files reviewable). Optional `sha256` pins payload integrity.
* **We do not fork OCSF.** The schema bound here is the upstream OCSF schema at `ocsf.version`.

## Examples

`examples/` ships one valid instance per mid-layer schema, all wired to each other and to the same playbook (`playbook.vuln_intake@v1`):

* `examples/detection.example.json` — `detection.powershell_encoded_cmd@v1`
* `examples/control.example.json` — `control.edr_script_block_logging@v1`
* `examples/telemetry.example.json` — `telemetry.host_process_create@v1` plus `examples/telemetry.sample.json` (OCSF Process Activity payload)

The end-to-end worked example that ties all five layers — playbook + detection + control + telemetry + metrics — together lives in `content-model/examples/vuln-intake/`. See its README for the cross-reference graph and the contract the tests enforce. Sibling worked examples follow the same shape: `content-model/examples/data-exfil/` (regulator-notification half), `content-model/examples/identity-compromise/` (IAM-containment half), and `content-model/examples/phishing-triage/`.

## Metrics layer

`metrics.schema.json` defines the KPI/KRI catalog entry shape. Each entry names one operator metric (MTTD, MTTR, coverage, control-effectiveness), declares its unit / direction / window, and pins the lower-layer artifacts (playbook step, detection rule, control, telemetry class) it measures via the shared `stable_id`. SecOps-NG does not define a new metrics standard; the catalog is a thin overlay over the upstream content layers.

| Layer       | Namespace prefix     | Example                                  |
|-------------|----------------------|------------------------------------------|
| Metric      | `kpi.` / `kri.`      | `kpi.mttd_critical@v1`                   |

A playbook step references the metrics it contributes a measurement to via:

```yaml
metric_refs: [kpi.mttd_critical@v1, kri.control_effectiveness@v1]
```

…and each metric pins back at the playbook step it observes through `playbook_refs[].step_id`, so any dashboard compiler can render a metric beside the step it measures without inferring topology.

## Validation

Each schema is JSON Schema 2020-12. `tests/content_model/test_schemas.py` covers the mid-layer schemas and their bundled examples; `tests/content_model/test_metrics_schema.py` covers the metrics schema in isolation; `tests/content_model/test_vuln_intake_example.py` validates every artifact in the worked example, asserts the five-layer cross-reference graph is closed, and checks that each metric input resolves to a sibling artifact.

## Out of scope

* Building our own runtime, agent framework, or SOAR.
* Re-implementing Sigma / OSCAL / D3FEND / OCSF — we reference and compose.
* Cross-layer referential integrity at the JSON Schema layer — that belongs in the compiler / linter.
