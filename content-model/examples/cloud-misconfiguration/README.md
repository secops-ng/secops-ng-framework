# Worked example: `playbook.cloud_misconfiguration@v1`

End-to-end worked example for the SecOps-NG content model, following
the same shape as `content-model/examples/vuln-intake/`,
`content-model/examples/data-exfil/`, and
`content-model/examples/post-incident-review/`. Ties together every
layer (playbook → controls → telemetry → metrics) plus regulatory
overlays (NIS2, DORA) and external catalog references (OSCAL, MITRE
D3FEND, OCSF) around a single scenario: a cloud-posture (CSPM) finding
arrives, is enriched with resource ownership, false-positive-screened,
guided to remediation, re-scanned, and escalated if verification fails.

The playbook anchors NIS2 Article 21(2)(e) (security in acquisition,
development and maintenance) and Article 21(2)(i) (asset management and
access control), and DORA Article 9 (ICT systems hygiene) and Article 19
(escalation when a posture exception becomes incident-grade), without
prescribing a specific cloud provider — those are operator-specific and
live in the operator's compile target.

## Why cloud misconfiguration

Cloud-posture deviations are the smallest realistic workflow that
exercises the *control-plane-as-telemetry* half of the content model.
A CSPM emits an OCSF Compliance Finding (2003), the playbook enriches
the affected resource against the cloud inventory (OCSF Cloud Resource
Inventory Info, 5001), false-positive-screens it, notifies the owner,
guides remediation, re-scans, and escalates if the re-scan still
reports the deviation. The metrics layer reports ingest latency,
end-to-end remediation latency, posture coverage, and the
recurring-deviation risk indicator over a rolling window.

## Scenario narrative

1. CSPM emits a posture finding (OCSF Compliance Finding 2003) on a
   resource that violates the operator's baseline.
2. `ingest finding` lifts the finding into the playbook state.
3. `enrich resource and owner` joins against OCSF Cloud Resource
   Inventory Info (5001) to attach owner, tags, and account context.
4. `known false positive?` checks the operator's suppression list;
   true → `suppress and close` (terminal).
5. `notify owner` opens the remediation handoff to the resource owner.
6. `guided remediation` runs the operator-chosen remediation action
   (provider console, IaC pull request, OPA-gated change).
7. `re-scan` re-evaluates the resource against the CSPM baseline.
8. `remediation verified?` checks the re-scan result; true → end,
   false → `escalate` (sub-threshold incident).

## Files

| Layer        | File                                                      | Stable ID                                          |
|--------------|-----------------------------------------------------------|----------------------------------------------------|
| Playbook     | `../../../content/playbooks/cloud-misconfiguration/playbook.cacao.json` | `playbook.cloud_misconfiguration@v1`               |
| Control      | `control.json`                                            | `control.cspm_baseline@v1`                         |
| Control      | `control.iac_policy_guardrail.json`                       | `control.iac_policy_guardrail@v1`                  |
| Control      | `control.cloud_identity_least_privilege.json`             | `control.cloud_identity_least_privilege@v1`        |
| Telemetry    | `telemetry.json`                                          | `telemetry.ocsf.compliance_finding@v1`             |
| Telemetry    | `telemetry.cloud_resource_inventory.json`                 | `telemetry.ocsf.cloud_resource_inventory@v1`       |
| Metric (KPI) | `metrics/kpi.mttd_cloud_misconfig.json`                   | `kpi.mttd_cloud_misconfig@v1`                      |
| Metric (KPI) | `metrics/kpi.mttr_cloud_misconfig.json`                   | `kpi.mttr_cloud_misconfig@v1`                      |
| Metric (KPI) | `metrics/kpi.cloud_posture_coverage.json`                 | `kpi.cloud_posture_coverage@v1`                    |
| Metric (KRI) | `metrics/kri.recurring_cloud_misconfig.json`              | `kri.recurring_cloud_misconfig@v1`                 |

The portable CACAO v2 fixture the compilers consume is also published
at `tests/compilers/_shared/fixtures/cloud_misconfiguration.cacao.json`
so the shared parser and per-target compiler suites can pick it up
without reaching into `content/`.

Compile-target outputs landed across the three CORE cards:

- n8n: `tests/compilers/n8n/test_cloud_misconfiguration.py`
- Temporal: `tests/compilers/temporal/test_cloud_misconfiguration.py` (PR #73)
- LangGraph: `examples/langgraph/cloud-misconfiguration/` plus
  `tests/compilers/langgraph/test_cloud_misconfiguration.py` (PR #85)

The detection layer is intentionally **not** authored here. The CSPM
finding and public-storage-bucket pointers used by this scenario are
already published via the playbook's `external_references` block; this
example layers controls, telemetry, and metrics around them.

## Cross-reference graph

```
                playbook.cloud_misconfiguration@v1
                (CACAO v2 + x_secops_ng)
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
  control.cspm_         control.iac_           control.cloud_
  baseline@v1           policy_guardrail@v1    identity_least_
                                               privilege@v1
        │                     │                      │
        ▼                     ▼                      ▼
  telemetry.ocsf.compliance_finding@v1
  telemetry.ocsf.cloud_resource_inventory@v1
                              │
                              ▼
                kpi.mttd_cloud_misconfig@v1
                kpi.mttr_cloud_misconfig@v1
                kpi.cloud_posture_coverage@v1
                kri.recurring_cloud_misconfig@v1
                (measurement.inputs[].{control,telemetry,playbook}_ref +
                 playbook_refs[].step_id)
```

Every metric pins which CACAO step it measures
(`playbook_refs[].step_id`) so a dashboard compiler can render the
metric beside the step it observes without inferring topology.

## Regulatory cross-references

The cloud-misconfiguration playbook is named in the NIS2 and DORA
mapping packs under `content/mappings/`. The four metrics above wire
onto the obligations they support, so the obligation → playbook →
metric chain resolves end-to-end:

| Regime | Article  | Mapping entry                       | What this playbook + metrics evidence                 |
|--------|----------|-------------------------------------|-------------------------------------------------------|
| NIS2   | 21(2)(e) | `nis2:art-21-2-e`                   | Security in acquisition, development and maintenance — cloud posture baseline, IaC guardrail, vulnerability handling on cloud resources |
| NIS2   | 21(2)(i) | `nis2:art-21-2-i`                   | Asset management — cloud-resource inventory delta and ownership enrichment |
| DORA   | 9        | `dora:art-9-vuln-mgmt` (companion)  | ICT systems hygiene — documented vulnerability-handling surface applied to cloud posture |
| DORA   | 19       | `dora:art-19-initial-4h` (escalation gate) | Escalation path when a posture exception becomes incident-grade |

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
the whole tree. The compiler suites under
`tests/compilers/{n8n,temporal,langgraph}/test_cloud_misconfiguration.py`
exercise the shared CACAO fixture against each compile target and pin
the byte-for-byte goldens against drift.

## Sovereignty note

The remediation action, the resource-owner notification, and the
re-scan artifact are emitted by the operator's compile target into the
operator's data plane. There is no SecOps-NG-hosted plane that sees an
operator's cloud-control-plane events. The same sovereignty boundary
holds for the OCSF Compliance Finding and Cloud Resource Inventory
events consumed at ingest — both are read from the operator's cloud
provider, into the operator's environment, by the operator's compile
target.

EU-hostable runtimes (Nebul, OVHcloud, Scaleway, Hetzner) are
first-class for the three reference compile targets; AI-provider
neutrality is enforced at the artifact layer so a switch between
providers does not require re-authoring the playbook or its bindings.

## What this example is NOT

- Not a runnable playbook. Compile targets (n8n / Temporal / LangGraph)
  are the SKELETON's downstream consumers; runnable artifacts are
  authored by the CORE cards (PRs #73, #85, and the n8n CORE).
- Not authoritative for upstream IDs. OSCAL catalog control-ids, OCSF
  class UIDs, and MITRE D3FEND technique IDs are pinned by URL plus a
  commit / version where one exists; this example follows upstream
  renames by republishing the pointer, never by vendoring rule or
  catalog bodies.
- Not the place where provider-specific remediation runbooks are
  encoded. The guided-remediation step delegates to the operator's
  compile target and the operator's provider tooling; this example
  ships the portable content shape only.

## Out of scope here

- Compiler outputs (`examples/{n8n,temporal,langgraph}/cloud-misconfiguration/`)
  and their golden tests. Owned by the three CORE cards.
- Cloud-provider-specific remediation playbooks. Operator-owned.
- Re-authoring of upstream CSPM rules. SecOps-NG does not re-author
  CSPM content; the playbook references upstream IDs only.
