# business_continuity — Temporal worked example

End-to-end demonstration of the SecOps-NG Temporal reference compiler
on the `business_continuity` CACAO playbook (NIS2 Art. 21(2)(c);
Art. 23 significant-incident notification). It is aimed at an
integrator who already runs Temporal and wants to adopt a portable
SecOps-NG playbook without re-platforming.

This worked example pins the Temporal leg (target 2 of 3) of the
cross-target parity lane for the `business_continuity` playbook. The
n8n and LangGraph siblings ship under `../../n8n/business_continuity/`
and `../../langgraph/business_continuity/`.

The `business_continuity` playbook is the plan-lifecycle sibling of
the `backup_recovery` exercise-lifecycle playbook (both anchor NIS2
Art. 21(2)(c)).

## Files in this directory

| Path                    | Source compiler      | Format             |
|-------------------------|----------------------|--------------------|
| `playbook.cacao.json`   | (input mirror)       | CACAO v2 JSON      |
| `workflow.temporal.py`  | `compilers.temporal` | Temporal workflow  |
| `regenerate.sh`         | (tooling)            | bash script        |
| `README.md`             | —                    | This file.         |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/business_continuity/playbook.cacao.yaml`.
The emitted `workflow.temporal.py` is a workflow stub: one
`@workflow.defn` class whose method calls one `@activity.defn`
coroutine per CACAO action step. Activity function names mirror CACAO
step ids so the two artifacts cross-reference by id alone; each
activity docstring records the originating `step_id` for auditability.

## Determinism boundary

Temporal workflow code must be deterministic across replay. Every
non-deterministic boundary the workflow crosses — BCM-plan store
reads, isolation-surface calls, failover-surface calls, competent-
authority notification transport, health-signal probes, evidence-store
writes — lives on the activity side of the `@activity.defn` line, not
inside the workflow. Integrators fill the activity bodies with their
runtime clients; the workflow code the compiler emits stays pure.

## How to regenerate

After any change to the canonical playbook or to
`compilers/temporal/*`, refresh the committed artifacts from the repo
root:

```sh
./examples/temporal/business_continuity/regenerate.sh
```

The byte-parity golden test under
`tests/examples/temporal/business_continuity/test_golden.py` reruns
the same pipeline and fails if the committed artifact drifts.

## Sovereignty note

Temporal is open source (MIT) and runs on infrastructure the operator
controls (Nebul, OVHcloud, Scaleway, Hetzner, self-hosted). The
Temporal Cloud SaaS is one deployment choice, not a vendor lock-in —
the workflow stub emitted here is a `temporalio.workflow.defn` that
runs against any Temporal server the operator brings.
