# examples/n8n/threat_intel_ingest

Worked example: the `playbook.threat_intel_ingest@v1` CACAO v2 playbook
compiled by the n8n reference compiler. Operators can import
`workflow.n8n.json` directly into an n8n instance to see the topology
the emitter produces; binding the placeholder Set-node steps to real
connectors (TAXII / STIX feed endpoint, SIEM, perimeter / DNS / EDR
blocklist gateway, ticketing system) is the operator's job.

## Source

Canonical CACAO playbook:

    ../../../content/playbooks/threat_intel_ingest/playbook.cacao.json

Scenario, workflow, regulatory anchors (NIS2 Article 21(2)(d), DORA
Article 19(2)), and the operator-supplied bindings are documented in
that folder's `README.md`. This folder holds the emitted artifact, a
co-located byte-identical copy of the CACAO source for easy diff
inspection, and the regeneration script.

## Layout

| Path                  | Source compiler | Format            |
|-----------------------|-----------------|-------------------|
| `playbook.cacao.json` | (input mirror)  | CACAO v2 JSON     |
| `workflow.n8n.json`   | `compilers.n8n` | n8n workflow JSON |
| `regenerate.sh`       | (tooling)       | bash script       |

## How to import

1. In your own n8n instance, open the workflows list and choose
   **Import from File**.
2. Select `workflow.n8n.json` from this directory.
3. n8n loads the nodes wired into the topology described in the
   canonical playbook. The workflow is **inactive** by default —
   review and bind it to your own connectors before activating.

The emitted workflow is a *snapshot of intent*, not a runnable
playbook. The Set nodes carry the CACAO I/O contract (`in_args` /
`out_args`) plus the `x_secops_ng` reference bundles (control,
detection, telemetry, metric) as editable assignments; binding those
rows to real connectors is the operator's job.

## Regeneration

The n8n emitter is deterministic: same input bytes in, same output
bytes out. From the repo root:

    ./examples/n8n/threat_intel_ingest/regenerate.sh

The script mirrors the canonical CACAO source into this folder and
re-emits `workflow.n8n.json` via `tools.compile --target n8n`.
Equivalent direct invocation:

    PYTHONPATH=. python -m tools.compile \
        content/playbooks/threat_intel_ingest/playbook.cacao.json \
        --target n8n \
        --out examples/n8n/threat_intel_ingest/workflow.n8n.json

The canonical playbook under
`content/playbooks/threat_intel_ingest/playbook.cacao.json` is the
single source. The `tests/compilers/n8n/test_threat_intel_ingest.py`
suite pins the byte-identical drift guard between the committed worked
example and the checked-in golden under
`tests/compilers/n8n/golden/threat_intel_ingest.n8n.json`.

## Mirroring policy

The mapping from CACAO to n8n is the same one the compiler implements:

| CACAO step type    | n8n node type                                       |
|--------------------|-----------------------------------------------------|
| `start`            | `n8n-nodes-base.manualTrigger`                      |
| `action` (no cmds) | `n8n-nodes-base.set` (carries CACAO I/O + refs)     |
| `if-condition`     | `n8n-nodes-base.if`                                 |
| `switch-condition` | `n8n-nodes-base.switch`                             |
| `end`              | `n8n-nodes-base.noOp`                               |

Node ids preserve the CACAO step id verbatim so the two artifacts can
be cross-referenced by id alone. Node labels mirror the CACAO step
`name`. Sequencing (`on_completion` / `on_success` / `on_failure`)
becomes n8n `connections` edges.

## What this example does not do

The n8n reference compiler translates **structure** and the
**CACAO I/O contract**, not **business logic**. The emitted workflow
carries the topology of the playbook (steps, transitions, conditional
routing), the per-step `in_args` / `out_args` and the `x_secops_ng`
reference bundles as Set rows, plus the lossy-translation notes
recorded under `meta.secops_ng_notes`. It does not carry:

- Operator-bound bindings (TAXII / STIX feed endpoint, SIEM, perimeter
  / DNS / EDR blocklist gateway, ticketing system).
- Credentials, secrets, or environment-specific endpoints.
- Detection logic — Sigma rule references are pinned upstream at
  SigmaHQ; no Sigma rules are authored in this repo.
- Confidence thresholds or indicator scoring rules — these are
  intent-bearing values the operator sets when binding the workflow
  to their environment.

Where a CACAO step expresses intent the target runtime cannot encode
(an `action` with no machine-readable `commands`, a switch with no
machine-readable `cases` expression, etc.), the emitter inserts an
explicit placeholder node and records the gap in
`meta.secops_ng_notes` so a human integrator sees exactly what they
still need to wire.

## Common pitfalls when binding activity bodies

The emitted `workflow.n8n.json` gives you topology and the CACAO I/O
contract; the Set-node placeholders are where operator judgement
lands. A short checklist of the pitfalls a maintainer already knows
but a first-time integrator does not:

- **Upstream rate-limiting and backpressure.** TAXII collections and
  STIX bundle endpoints publish on their own cadence and often cap
  poll frequency. n8n's HTTP Request node has no built-in
  backpressure — schedule the trigger conservatively (a Cron or
  Schedule Trigger at the feed's documented poll interval), and set
  the node's *Retry On Fail* + *Wait Between Tries* under **Settings**
  so a `429` or `503` from the feed does not cascade into the
  downstream Set nodes. If the feed publishes an `X-RateLimit-*` or
  `Retry-After` header, honour it explicitly in a downstream IF /
  Wait pair rather than tuning the retry blindly.
- **Deduplication and idempotency keys.** The CACAO playbook exposes
  the STIX object `id` (a UUID pinned by the producer) as the stable
  key. Bind that field — not `created`, not `modified`, not the
  local ingest timestamp — as the idempotency key when persisting or
  forwarding indicators. In n8n this typically means an *Item Lists*
  node (Deduplicate) keyed on `{{$json["id"]}}` before the SIEM /
  blocklist Set rows fire.
- **Credentials and sovereign hosting.** Feed endpoints, SIEM API
  keys, and blocklist-gateway tokens belong in n8n Credentials, not
  in the exported workflow JSON. The repo's [`.env.example`](../../../.env.example)
  documents the variable names the reference examples expect; the
  sovereignty posture (which EU host runs n8n, which egress domain
  the feed uses) is discussed in
  [`docs/FOUNDATION.md`](../../../docs/FOUNDATION.md). Exported
  `workflow.n8n.json` files are safe to commit only because the Set
  nodes carry placeholders — do not check in workflows exported
  after credentials have been bound.
- **n8n gotcha — Set node coercion.** n8n's Set node stringifies
  numeric and boolean values by default. CACAO `in_args` /
  `out_args` such as `confidence` (integer 0–100) or
  `high_confidence` (boolean) will arrive downstream as `"75"` and
  `"true"` unless the *Keep Only Set* toggle is off and the value
  type is set explicitly (Number, Boolean) on each row. A confidence
  threshold IF node comparing `{{$json["confidence"]}} > 70` will
  silently short-circuit on string comparison; verify the row type
  before wiring the branch.

## Sovereignty note

The artifact emitted here is a description of what the operator's own
n8n instance should do. No telemetry, no execution traces, no
indicator data, no identifying flows reach this repository or the
SecOps-NG project. The operator runs n8n on infrastructure they
control — we ship the structure, they own the data plane.
