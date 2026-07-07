# business_continuity — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on
the `business_continuity` CACAO playbook (NIS2 Art. 21(2)(c) business
continuity, backup management, disaster recovery, crisis management;
Art. 23 significant-incident notification to the competent authority).
It is aimed at an integrator who already runs n8n and wants to adopt a
portable SecOps-NG playbook without re-platforming: the example shows
exactly which workflow shape the compiler produces, how the CACAO
contract surfaces on each node, and where the integrator owns the
seams.

This worked example pins the n8n leg (target 1 of 3) of the
cross-target parity lane for the `business_continuity` playbook. The
Temporal and LangGraph siblings ship under
`../../temporal/business_continuity/` and
`../../langgraph/business_continuity/`; together the three folders
pin the full three-target contract for this playbook.

The `business_continuity` playbook is the plan-lifecycle sibling of
the `backup_recovery` exercise-lifecycle playbook: both co-anchor
NIS2 Art. 21(2)(c). This one runs when a business-continuity event is
declared against an in-scope service (detect → activate BCM plan →
isolate → switch to backup → notify competent authority → restore and
verify → post-incident review); its sibling runs on the periodic
restore-drill cadence that exercises the backup-and-recovery apparatus
before it is needed.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/business_continuity/playbook.cacao.yaml`.
Scenario, regulatory anchors (NIS2 Art. 21(2)(c), Art. 23), control /
telemetry bindings, and the operator-supplied variable set are
documented in that folder's `README.md`. This folder holds the emitted
artifact, a co-located mirror of the CACAO source (JSON form for
parity with sibling targets), and the regeneration command.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads one node per CACAO step wired into the topology the
   canonical playbook describes. The workflow is **inactive** by
   default — review and bind it to your own connectors before
   activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. Set-node assignments carry the CACAO I/O contract as
editable rows; binding them to real connectors (BCM-plan store,
isolation surface, failover surface, competent-authority notification
transport, health-signal probe, evidence store) is the operator's
job.

## How to regenerate

After any change to the canonical playbook or to `compilers/n8n/*`,
refresh the committed artifacts from the repo root:

```sh
./examples/n8n/business_continuity/regenerate.sh
```

The script mirrors the canonical CACAO YAML into a byte-deterministic
JSON form and then emits `workflow.n8n.json` via the unified
`tools.compile` CLI. The byte-parity golden test under
`tests/examples/n8n/business_continuity/test_golden.py` reruns the
same pipeline and fails if the committed artifact drifts.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
The Art. 23 notification transport, in particular, is operator-bound:
the competent authority varies by Member State of establishment and
the delivery surface (portal, S/MIME email, API) is the operator's
choice — the framework ships the envelope shape, the operator owns
the wire.
