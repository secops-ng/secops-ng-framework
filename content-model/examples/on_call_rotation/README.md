# Worked example: `playbook.on_call_rotation@v1`

End-to-end worked example for the SecOps-NG content model, following
the same shape as `content-model/examples/vuln_intake/`,
`content-model/examples/data_exfil/`, and
`content-model/examples/post_incident_review/`. Ties together every
layer that applies (playbook → control → telemetry → metrics) plus
regulatory overlays (NIS2, DORA) and external catalog references
(OSCAL, MITRE D3FEND, OCSF) around a single scenario: operating the
on-call rotation so the operator has a bound primary responder and a
bound escalation chain before any shift window opens, with a
structured handoff brief delivered at the boundary.

## Why on-call rotation

Detection, triage, containment, and post_incident_review playbooks
all assume *somebody is going to be paged when an incident fires*. On-
call rotation is the readiness slice that makes that assumption hold:
who is primary / secondary / manager for the next shift window, what
escalation chain the paging system reads at page time, and how the
incoming responder inherits open risk from the prior shift. It is the
smallest realistic workflow that anchors NIS2 Article 21(2)(b)
incident-handling capability and DORA Article 6 ICT risk-management
responder readiness without crossing into detection or response.

## Scenario narrative

1. Scheduler kicks the playbook on each evaluated shift window with
   `__shift_window__` pinned (cron, Temporal schedule, or n8n trigger).
2. `load rotation roster` reads the operator's roster source of truth
   (paging system schedule, calendar feed, or roster file) and resolves
   `__current_on_call__` (primary slot for the window) and
   `__next_on_call__` (responder receiving the next shift).
3. `bind escalation tiers` composes the ordered chain (primary,
   secondary, manager) and publishes the binding the operator's paging
   system will fan out through at page time. The bound chain is the
   only durable side-effect during steady-state shifts.
4. `shift handoff window?` branches on `__handoff_window__`. False ends
   the run; true continues into handoff-brief generation.
5. `generate handoff brief` composes a structured artifact (markdown +
   JSON payload) covering open incidents, recent alerts within lookback,
   outstanding escalations, and an ack-latency snapshot for the prior
   shift.
6. `notify incoming on-call` delivers the brief along the pre-bound
   channel (paging-system DM, chat thread, email). Generation and
   delivery are deliberately adjacent-but-separate steps so the
   delivery KPI can report compose-time and deliver-time independently.

## Files

| Layer        | File                                                  | Stable ID                                       |
|--------------|-------------------------------------------------------|-------------------------------------------------|
| Playbook     | `../../../content/playbooks/on_call_rotation/playbook.cacao.json` | `playbook.on_call_rotation@v1`                  |
| Control      | `control.json`                                        | `control.on_call_roster_governance@v1`          |
| Telemetry    | `telemetry.account_change.json`                       | `telemetry.ocsf.account_change@v1`              |
| Telemetry    | `telemetry.api_activity.json`                         | `telemetry.ocsf.api_activity@v1`                |
| Metric (KPI) | `metrics/kpi.coverage_on_call_schedule.json`          | `kpi.coverage_on_call_schedule@v1`              |
| Metric (KPI) | `metrics/kpi.mttr_on_call_ack.json`                   | `kpi.mttr_on_call_ack@v1`                       |
| Metric (KPI) | `metrics/kpi.handoff_brief_delivery_sla.json`         | `kpi.handoff_brief_delivery_sla@v1`             |
| Metric (KRI) | `metrics/kri.escalation_tier_breach.json`             | `kri.escalation_tier_breach@v1`                 |

The portable CACAO v2 fixture the compilers consume is also published
at `tests/compilers/_shared/fixtures/on_call_rotation.cacao.json` so
the shared parser and per-target compiler suites pick it up without
reaching into `content/`.

Compile-target outputs landed across the three CORE cards:

- n8n: `tests/compilers/n8n/test_on_call_rotation.py`
- Temporal: `tests/compilers/temporal/test_on_call_rotation.py`
- LangGraph: `examples/langgraph/on_call_rotation/` plus
  `tests/compilers/langgraph/test_on_call_rotation.py`

The detection layer is intentionally **not** authored here. The
playbook references upstream SigmaHQ rule names for off-hours
authentication anomaly and privileged-account modification via
`external_references` only; rule IDs are pinned at the CORE-layer
detection mapping rather than fabricated here, and SecOps-NG does not
re-author Sigma.

Note on metric set: vuln_intake and data_exfil carry detection-shaped
MTTD / MTTR metrics because they are detection-and-response workflows.
On-call rotation is not. It is a readiness workflow that runs on a
shift-window clock, and the four metrics shipped here — schedule-
coverage KPI, page-to-ack MTTR-ack KPI, handoff-brief delivery-SLA
KPI, and escalation-tier-breach KRI — are exactly the set the
SKELETON playbook pins in its `x_secops_ng.metric_refs`. Inventing
detection-shaped identifiers for this workflow would violate the
no-invented-IDs bar.

## Cross-reference graph

```
                    playbook.on_call_rotation@v1
                    (CACAO v2 + x_secops_ng)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
  upstream Sigma          control.              telemetry.ocsf.
  off-hours-auth /        on_call_roster_       account_change@v1
  privileged-account-     governance@v1         telemetry.ocsf.
  modification refs              │              api_activity@v1
  (external_references)          │                     │
                                 ▼                     ▼
                kpi.coverage_on_call_schedule@v1
                kpi.mttr_on_call_ack@v1
                kpi.handoff_brief_delivery_sla@v1
                kri.escalation_tier_breach@v1
                (measurement.inputs[].{control,telemetry,playbook}_ref +
                 playbook_refs[].step_id)
```

Every metric pins which CACAO step it measures
(`playbook_refs[].step_id`) so a dashboard compiler can render the
metric beside the step it observes without inferring topology.

## OSCAL / D3FEND / OCSF references

External catalog citations live in the layer files; this section is
the cross-layer pointer table.

| Catalog     | Identifier                                  | Cited by                              |
|-------------|---------------------------------------------|---------------------------------------|
| OSCAL       | NIST SP 800-53 Rev. 5 — IR-4                | `control.json` (incident handling)    |
| OSCAL       | NIST SP 800-53 Rev. 5 — IR-7                | `control.json` (response assistance)  |
| OSCAL       | NIST SP 800-53 Rev. 5 — AC-2                | `control.json` (account management of rotation handoffs) |
| MITRE D3FEND| D3-AM Account Monitoring                    | `control.json`                        |
| OCSF        | class_uid 3001 — Account Change             | `telemetry.account_change.json`       |
| OCSF        | class_uid 6003 — API Activity               | `telemetry.api_activity.json` (metrics: handoff-delivery, ack) |

D3FEND is cited for the rotation-handoff monitoring side; ATT&CK
counter-techniques are intentionally empty on `control.on_call_roster_governance@v1`
because the control is a programme-level readiness control, not a
technique-level countermeasure.

## Regulatory cross-references

The on-call rotation playbook is wired into the regulatory mapping
packs under `content/mappings/` against the obligations its readiness
slice supports. This EXTEND card additionally registers the four
metrics above on the same obligations, so the obligation → playbook →
metric chain resolves end-to-end:

| Regime | Article         | Mapping entry                  | What this playbook + metrics evidence                                 |
|--------|-----------------|--------------------------------|-----------------------------------------------------------------------|
| NIS2   | 21(2)(b)        | `nis2:art-21-2-b`              | Incident handling: bound responder readiness per shift window         |
| NIS2   | 23(4)(a)        | `nis2:art-23-early-warning`    | 24h early warning: page-to-ack latency is the head of the clock       |
| DORA   | 6               | (programme-level; see playbook external_references) | ICT risk-management framework — responder readiness role |
| DORA   | 19(4)(a)        | `dora:art-19-initial-4h`       | 4h-post-classification clock: ack latency + coverage are upstream     |

Article texts are quoted verbatim in the mapping packs; this table is
a pointer table only. Rotation coverage gaps that the schedule-
coverage KPI catches in advance are the operational condition that
prevents notification-window breaches downstream — the dependency runs
upstream of the notification step, not parallel to it.

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
temporal,langgraph}/test_on_call_rotation.py` exercise the shared
CACAO fixture against each compile target and pin the byte-for-byte
goldens against drift.

## Sovereignty note

The roster source itself, the paging system the bound escalation
chain is read by, and the handoff-brief delivery channel are all
operator-owned. There is no SecOps-NG-hosted plane that sees an
operator's roster, escalation chain, or handoff brief. The same
sovereignty boundary holds for the OCSF Account Change events the
playbook reads — they live in the operator's identity-and-access
data plane and are consumed by the operator's compile target inside
the operator's environment.

EU-hostable runtimes (Nebul, OVHcloud, Scaleway, Hetzner) are first-
class for the three reference compile targets; AI-provider neutrality
is enforced at the artifact layer so a switch between providers does
not require re-authoring the playbook or its bindings.

## What this example is NOT

- Not a runnable playbook. Compile targets (n8n / Temporal / LangGraph)
  are the SKELETON's downstream consumers; runnable artifacts are
  authored by the CORE cards.
- Not authoritative for upstream IDs. Sigma rule IDs (off-hours auth,
  privileged-account modification), OSCAL catalog control-ids, OCSF
  class UIDs, and MITRE D3FEND technique IDs are pinned by URL plus a
  commit / version where one exists; this example follows upstream
  renames by republishing the pointer, never by vendoring rule or
  catalog bodies.
- Not the place where roster source bindings, paging-system bindings,
  or delivery channels are encoded. Those are operator-specific
  bindings supplied at compile time; the framework's templates ship
  the contract, not the integration.

## Out of scope here

- Compiler outputs (`examples/{n8n,temporal,langgraph}/on_call_rotation/`)
  and their golden tests. Owned by the three CORE cards.
- Roster source-of-truth integrations. Operator-owned.
- Re-authoring of upstream off-hours-auth or privileged-account-
  modification Sigma rules. SecOps-NG does not re-author Sigma; the
  playbook references upstream rule names only until the CORE-layer
  detection mapping pins the rule IDs.
