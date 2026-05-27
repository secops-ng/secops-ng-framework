# Content model

SecOps-NG ships **content**, **structure**, and **metrics**. It does not
ship a runtime, an agent framework, or a SOAR.

## The five content tracks

| Track       | Standard           | Where it lives                      |
|-------------|--------------------|-------------------------------------|
| Response    | CACAO v2 (OASIS)   | `content/playbooks/`                |
| Detection   | Sigma              | `content/detections/` (references)  |
| Controls    | OSCAL + D3FEND     | `content/controls/`                 |
| Telemetry   | OCSF               | `content/telemetry/`                |
| Measurement | KPI / KRI catalog  | `content/metrics/`                  |

## Structure

- `schemas/` defines every portable artifact shape as JSON Schema.
- `content/mappings/` carries regulatory crosswalks (NIS2, DORA, CRA,
  GDPR, ISO 27001, SOC 2). Mappings cite controls and playbooks; they
  are not themselves controls.

## Compilation

`compilers/` consume content and emit orchestrator-native definitions.
The artifact is the source of truth; the emitted definition is a build
output that can be regenerated at any time.

## What this layer is not

- Not a SOAR. Operators bring their own.
- Not a runtime. Compile to n8n, Temporal, or LangGraph and run there.
- Not a detection-rule fork. We reference Sigma; we do not maintain rules.
- Not a control authority. We map to OSCAL / D3FEND and to regulatory
  regimes; we do not invent new controls.
