# Content model — mid layer (detection / control / telemetry)

This directory holds the **mid-layer schemas** of the SecOps-NG content model. The upper layer is the playbook schema (sibling card `coder/content-model-playbook`); the lower layer is the metrics catalog + worked example (sibling card `coder/content-model-metrics`). This card lands the three middle layers and how they join.

## Stable ID model

Every layer addresses the others by a short, stable string with a prefix. Cross-references are validated at compile time by the consumers, not by these schemas (JSON Schema cannot do referential integrity across files).

| Layer       | Prefix | Schema                       | Example                          |
|-------------|--------|------------------------------|----------------------------------|
| Playbook    | `pb:`  | `playbook.schema.json` *(sibling)*  | `pb:vuln-intake`                 |
| Detection   | `det:` | `detection.schema.json`      | `det:powershell-encoded-cmd`     |
| Control     | `ctl:` | `control.schema.json`        | `ctl:edr-script-block-logging`   |
| Telemetry   | `tlm:` | `telemetry.schema.json`      | `tlm:host-process-create`        |
| Metric      | `kpi:` / `kri:` | `metrics.schema.json` *(sibling)* | `kpi:mttd-critical`         |

A SecOps-NG playbook step (CACAO `workflow.step`) references mid-layer artifacts via:

```yaml
detection_refs:  [det:powershell-encoded-cmd]
control_refs:    [ctl:edr-script-block-logging]
telemetry_refs:  [tlm:host-process-create]
```

…and each mid-layer artifact lists which playbooks and steps it belongs to via `playbook_refs[].playbook_id` + optional `playbook_refs[].step_id`. The graph is **bidirectional by construction** so any layer can serve as the entry point for review.

## What each schema is — and explicitly is not

### `detection.schema.json` — Sigma rule POINTERS

* Captures `sigma.rule_id`, `sigma.repo`, optional `sigma.path` and `sigma.commit` pin.
* Carries an operator-facing overlay: stable ID, severity, status, logsource summary, cross-refs.
* **We never fork Sigma rule bodies.** Consumers MUST resolve the rule from the upstream repository at the pinned commit. If the rule is renamed or removed upstream, our pointer becomes invalid — that is the correct failure mode, not a reason to vendor the rule.

### `control.schema.json` — OSCAL component + D3FEND technique

* `oscal.component` is a faithful fragment of a NIST OSCAL component-definition (component → control-implementations → implemented-requirements). Consumers can lift this into a full component-definition without translation.
* `d3fend.technique_id` ties the control to a MITRE D3FEND defensive technique (the "how"), while `attack_counters[]` lists the MITRE ATT&CK techniques the control is designed to counter.
* **We do not invent control catalogs.** Catalog references (`control-id`, `source`) point at upstream sources (NIST 800-53, ISO 27001, NIS2 articles, community profiles).

### `telemetry.schema.json` — OCSF class binding + sample payload pointer

* Binds the content layer to an OCSF event class (`version`, `category_uid`, `class_uid`, optional `activity_id`, `profiles`).
* `fields_used[]` lists the dot-paths into the OCSF event our content actually reads or writes — a thin contract so reviewers can reason about compatibility without diffing the full OCSF schema.
* `sample.path` points to a canonical sample payload kept beside the binding (kept out-of-line to keep schema files reviewable). Optional `sha256` pins payload integrity.
* **We do not fork OCSF.** The schema bound here is the upstream OCSF schema at `ocsf.version`.

## Examples

`examples/` ships one valid instance per mid-layer schema, all wired to each other and to the same playbook (`pb:vuln-intake`):

* `examples/detection.example.json` (`det:powershell-encoded-cmd`)
* `examples/control.example.json` (`ctl:edr-script-block-logging`)
* `examples/telemetry.example.json` (`tlm:host-process-create`) + `examples/telemetry.sample.json` (OCSF Process Activity payload)

The end-to-end worked example that ties all five layers together lands in the metrics card (`content-model/examples/vuln-intake/`).

## Validation

Each schema is JSON Schema 2020-12 and is checked by `tests/content_model/test_schemas.py` (added in this branch). The tests also assert the bundled examples validate against their schemas.

## Out of scope

* Building our own runtime, agent framework, or SOAR.
* Re-implementing Sigma / OSCAL / D3FEND / OCSF — we reference and compose.
* Cross-layer referential integrity at the JSON Schema layer — that belongs in the compiler / linter.
