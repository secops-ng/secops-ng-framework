# backup_recovery — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the backup_recovery CACAO playbook. It is aimed at an
integrator who already runs LangGraph and wants to adopt a portable
SecOps-NG playbook without re-platforming: the example shows exactly
which artifacts the compiler produces, how they fit together, and where
the integrator owns the seams.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/backup_recovery/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the two generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/backup_recovery/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A drift
test in `tests/examples/backup_recovery/` fails the suite if the
committed artifacts diverge from a fresh regeneration, so the worked
example stays honest as the compiler evolves.

## Cross-target pointers

The same canonical playbook ships under the other two reference compile
targets so an integrator can compare lowerings side by side:

- [`examples/n8n/backup_recovery/`](../../n8n/backup_recovery/) — n8n no-code workflow.
- [`examples/temporal/backup_recovery/`](../../temporal/backup_recovery/) — Temporal durable workflow stub.

## Topology

The backup_recovery playbook branches twice: once on triage
outcome, then on detection-capability availability before fanning into
the linear containment chain.

1. `triage signal` — collect ransomware indicators from the EDR, SIEM,
   and any anomaly-detection feed the operator already runs.
2. `ransomware confirmed?` — an `if-condition` step. The triage step
   writes a status into `state["step_status"][src]`; the router maps
   `success` (confirmed) to the `EDR available?` capability check and
   `failure` (false positive) to the end sentinel.
3. `EDR available?` — second `if-condition`. `success` routes to
   `endpoint isolation — EDR isolate` (the preferred path);
   `failure` routes to `endpoint isolation — network ACL deny
   (fallback)` so the playbook still completes when the EDR is
   unavailable.
4. Both isolation branches converge on the linear containment chain:
   `identity revocation` → `backup verification` → `comms plan` →
   end sentinel.

The conditional-edge router pattern is identical to vuln_intake and
identity_compromise; see `assemble.py` for the ~10-line wiring.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (EDR, IdP, backup platform, ticketing, SIEM, comms channel).
- It does not ship operator credentials, endpoints, or environment.
  Secrets stay with the operator.
- It does not pick an LLM provider for the agentic-extension hook.
  `AGENTIC_HOOK` is a documented placeholder; the operator chooses a
  provider that matches their sovereignty posture at integration time.
- It does not bind a specific runtime topology (retry policy,
  concurrency, persistence backend). Those are runtime concerns the
  integrator applies in their own assembly.

## Sovereignty note

LangGraph is open source (MIT) and runs as a Python process: hosting
it on EU sovereign infrastructure (Nebul, OVHcloud, Scaleway, Hetzner)
is a deployment choice, not a vendor decision. The agentic-extension
hook is provider-neutral by design — the compiler never embeds an LLM
SDK, so the operator can wire it to self-hosted open-weights inference
or to an EU-hosted managed endpoint without regenerating the artifact.
See [docs/compilers/langgraph.md](../../../docs/compilers/langgraph.md)
and [docs/sovereignty/](../../../docs/sovereignty/) for the full
posture.
