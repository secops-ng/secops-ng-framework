# cra_cvd — n8n worked example

End-to-end demonstration of the SecOps-NG n8n reference compiler on the
`cra_cvd` CACAO playbook. Aimed at an integrator who already runs n8n
and wants to adopt the CRA Article 14 coordinated vulnerability
disclosure (CVD) lifecycle without re-platforming: the example shows
the workflow shape the compiler produces, how the CACAO acknowledgement
and disclosure-coordination contracts surface on each node, and where
the integrator owns the seams (reporter-communications channel, CVE
request adapter, CSIRT-coordination adapter, PGP-signed delivery, and
the evidence store).

This worked example is the n8n leg of the three-target parity lane for
the `cra_cvd` playbook. Sibling Temporal and LangGraph examples ship
alongside under `../../temporal/cra_cvd/` and
`../../langgraph/cra_cvd/`.

## Files in this directory

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |
| `README.md`           | —               | This file.        |

The canonical input is the CACAO v2 playbook at
`../../../content/playbooks/cra_cvd/playbook.cacao.json`. Regulatory
anchors (CRA Article 14 §1 CVD policy and §6 acknowledgement window),
control / metric / telemetry bindings, and the reporter-side contracts
are documented on that canonical source. This folder holds the emitted
artifact, a co-located byte-identical copy of the CACAO source for easy
diff inspection, and the regeneration script.

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads the nine-node topology described below. The workflow is
   **inactive** by default — bind the reporter channel, CVE-request,
   CSIRT-coordination, PGP delivery, and evidence-store connectors
   before activating.

The emitted workflow is a *snapshot of intent*, not a runnable playbook.
The Set nodes carry the CACAO I/O contract (case id, reporter contact,
triage verdict, fix reference, actively-exploited flag, disclosure
target date, advisory id) as editable assignments; the integrator binds
them to their own reporter-facing surface and downstream adapters.

## How to regenerate

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/cra_cvd/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

```bash
PYTHONPATH=. python -m tools.compile \
    content/playbooks/cra_cvd/playbook.cacao.json \
    --target n8n \
    --out examples/n8n/cra_cvd/workflow.n8n.json
```

The drift guard in `tests/examples/cra_cvd/test_golden.py` fails the
suite if the committed `workflow.n8n.json` diverges from a fresh
regeneration, so the worked example stays honest as the compiler
evolves.

## Topology

The cra_cvd lifecycle is a linear seven-step disclosure chain — every
step's status feeds the next, so an integrator can follow the CACAO
Article 14 §6 acknowledgement clock and the disclosure target date
through the same audit trail. Nine n8n nodes, one per CACAO step:

1. `cra_cvd_start` (`manualTrigger`) — entry point; carries the
   workflow-scope variables (`__case_id__`, `__reporter_contact__`,
   `__reporter_ack_ts__`, `__triage_verdict__`, `__fix_ref__`,
   `__actively_exploited__`, `__disclosure_target_date__`,
   `__advisory_id__`, `__reporter_credit_display__`) that the upstream
   intake surface supplies.
2. `intake` (`set`) — receive the reporter's submission; write the
   durable receipt used by the Art. 14 §6 acknowledgement-SLA clock.
3. `ack_to_reporter` (`set`) — dispatch the acknowledgement letter
   (see `content/playbooks/cra_cvd/templates/ack_letter.j2`) via the
   operator-bound reporter channel (email, PGP-signed if the reporter
   supplied a key id). Records `__reporter_ack_ts__`.
4. `triage` (`set`) — evaluate reproducibility, severity, and
   actively-exploited status. Emits `__triage_verdict__` and
   `__actively_exploited__` (the latter is the join key against a
   sibling `cra_srp_notify` run if the case trips CRA Art. 14(2)).
5. `develop_fix` (`set`) — capture the internal fix reference. Emits
   `__fix_ref__`.
6. `validate_fix` (`set`) — validate the fix against the reporter's
   reproduction (with reporter cooperation where consented).
7. `coordinate_disclosure` (`set`) — set the disclosure target date,
   request a CVE (CVE-request adapter), and — where a national CSIRT
   is co-coordinating — open the CSIRT-coordination hold. Emits
   `__disclosure_target_date__`.
8. `publish_advisory` (`set`) — publish the CSAF 2.0 advisory (see
   `content/playbooks/cra_cvd/templates/advisory.csaf2.json.j2`) and
   the human-readable advisory (`advisory.md.j2`). Emits
   `__advisory_id__`.
9. `cra_cvd_end` (`noOp`) — end sentinel.

## Where the reporter-communications and adapter TODOs live

The three adapter-bound steps (`ack_to_reporter`, `coordinate_disclosure`,
`publish_advisory`) compile through as `set` nodes whose assignments
carry the CACAO contract but leave the values blank. The integrator
wires:

- **Reporter channel** — outbound mail or PGP-signed delivery
  (`patterns.cra_cvd.PGPDeliveryRequest`).
- **CVE-request adapter** — CNA request; the reference contract lives
  at `patterns.cra_cvd.CVERequest` / `CVERequestResponse`.
- **CSIRT-coordination adapter** — for cases requiring national CSIRT
  coordination; contract at `patterns.cra_cvd.CSIRTCoordinationRequest`.

The CSAF 2.0 advisory template is deterministic; the operator supplies
the vulnerability metadata (CWE, CVSS, affected versions, fix ref) at
the `publish_advisory` node's assignments.

## CACAO contract surfaces on Set nodes

Every `action`-without-commands step in the CACAO source emits an n8n
`set` node whose **assignments** carry the CACAO contract one row per
field:

- `in.<name>` rows for each entry in the step's `in_args`.
- `out.<name>` rows for each entry in the step's `out_args`.
- `x_secops_ng.<key>` rows for each key under the step's `x_secops_ng`
  block (`control_refs`, `telemetry_refs`, `metric_refs`).

The values are left blank (or pre-seeded with the reference-id list, for
`x_secops_ng` rows) so the integrator can wire them to expressions that
pull from upstream nodes, n8n variables, or operator-bound connectors.

The lossy translations the emitter notes (workflow-scope variables
flattened onto the trigger, CACAO contract rows surfaced as blank Set
assignments) are recorded in `meta.secops_ng_notes` so the integrator
sees exactly which seams need attention.

## What this example deliberately doesn't do

- It does not execute the workflow. The Set nodes carry the CACAO I/O
  contract but the right-hand values are blank until the integrator
  binds the reporter channel, CVE-request adapter, CSIRT-coordination
  adapter, and the operator's evidence store.
- It does not ship CNA API tokens, CSIRT-coordination endpoints, or
  PGP secret keys. Secrets stay with the operator.
- It does not select a CVE numbering authority — that is an operator
  policy decision. The `patterns.cra_cvd.CNARole` enum documents the
  EU-preferred default (`eu_preferred`).

## Status

CORE-PRIM — the n8n artifact ships byte-deterministic from the
canonical CACAO source. Adapter wiring stays operator-owned; the CORE
siblings (ack/advisory templates, adapter stubs, orphan-CI + D3FEND +
OSCAL + Art.14 §6 KPI mapping) have all landed and this three-target
example closes the G-03 byte-parity gap.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
identifying data flows to this repository or to the SecOps-NG project.
n8n runs as a Node.js process; hosting it on EU sovereign
infrastructure (Nebul, OVHcloud, Scaleway, Hetzner) is a deployment
choice, not a vendor decision. The operator runs n8n on infrastructure
they control — we ship the structure, they own the data plane.
