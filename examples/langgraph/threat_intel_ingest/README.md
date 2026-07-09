# threat_intel_ingest — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the threat_intel_ingest CACAO playbook. It is aimed at an integrator
who already runs LangGraph and wants to adopt a portable SecOps-NG
playbook without re-platforming: the example shows exactly which
artifacts the compiler produces, how they fit together, and where the
integrator owns the seams.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `regenerate.sh` | Re-runs both emitters from the playbook and overwrites the two generated artifacts. |

## How to regenerate

After any change to the playbook or to `compilers/langgraph/*`, refresh
the committed artifacts from the repo root:

```bash
./examples/langgraph/threat_intel_ingest/regenerate.sh
```

The script re-emits `graph_spec.json` and `state_bindings.py` from
`playbook.cacao.json` using `compilers.langgraph.emit` and
`compilers.langgraph.state`. A drift test in `tests/examples/` fails
the suite if the committed artifacts diverge from a fresh regeneration,
so the worked example stays honest as the compiler evolves.

## Topology

The threat_intel_ingest playbook branches on indicator confidence:

1. `pull upstream feed` — poll the upstream TAXII collection or STIX
   bundle endpoint (sovereign / community feed of the operator's
   choosing — an ENISA CSIRTs-network feed, a national CSIRT
   bulletin, a community MISP instance).
2. `normalise STIX to OCSF` — flatten the bundle into the OCSF shape
   the rest of the framework already speaks.
3. `above confidence threshold?` — an `if-condition` step. The
   normalisation step writes a status into `state["step_status"][src]`;
   the router maps `success` (high-confidence indicators present) to
   the propagation branch and `failure` (detection-only) to the
   detection-rule activation.
4. Propagation branch — `propagate to blocklist` then chains into
   `activate detection rule`; the false-branch goes straight to
   `activate detection rule`. Both branches converge so detections are
   always armed.

The conditional-edge router pattern is identical to vuln_intake and
identity_compromise; see `assemble.py` for the ~10-line wiring.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (TAXII client, OCSF pipeline, SIEM, detection-rule manager).
- It does not ship operator credentials, feed endpoints, or
  environment. Secrets stay with the operator.
- It does not pick an LLM provider for the agentic-extension hook.
  `AGENTIC_HOOK` is a documented placeholder; the operator chooses a
  provider that matches their sovereignty posture at integration time.
- It does not bind a specific runtime topology (retry policy,
  concurrency, persistence backend). Those are runtime concerns the
  integrator applies in their own assembly.

## Common pitfalls when binding activity bodies

The emitted `state_bindings.py` gives you a `TypedDict` state schema
and `@tool`-decorated wrappers around each CACAO action; the tool
bodies raise `NotImplementedError` on purpose. Filling them in is
where operator judgement lands. A short checklist of the pitfalls a
maintainer already knows but a first-time integrator does not:

- **Upstream rate-limiting and backpressure.** TAXII collections and
  STIX bundle endpoints publish on their own cadence and typically
  cap poll frequency. The `pull upstream feed` tool body should
  surface `429` / `503` (and any `Retry-After` header) as a typed
  error the caller can route on, rather than sleeping inside the
  tool — a LangGraph node blocked on `time.sleep` blocks the whole
  graph tick. If the assembly is running under a checkpointer,
  prefer raising and letting the outer retry policy schedule the
  next tick; if you are running without a checkpointer, add an
  explicit `wait_node` between `pull` and `normalise` and route to
  it on the backpressure branch of the router.
- **Deduplication and idempotency keys.** The CACAO playbook exposes
  the STIX object `id` (a UUID pinned by the producer) as the stable
  key. Bind that field — not `created`, not `modified`, not the
  local ingest timestamp — as the idempotency key. The state schema's
  `step_status[src]` channel tracks branch outcome, but it does not
  dedup indicators; add a per-STIX-`id` set in a dedicated state
  channel and reduce it with a set-union reducer if you expect the
  graph to be re-entered from a checkpointer.
- **Credentials and sovereign hosting.** Feed endpoints, SIEM API
  keys, and blocklist-gateway tokens belong in the process
  environment — read them via `os.environ` in the tool bodies, not
  from graph state (state is checkpointed and may end up on disk or
  in a shared backend). The repo's [`.env.example`](../../../.env.example)
  documents the variable names the reference examples expect; the
  sovereignty posture (which EU host runs the LangGraph process,
  which provider hosts the agentic-extension hook) is discussed in
  [`docs/FOUNDATION.md`](../../../docs/FOUNDATION.md) and the
  provider-neutrality guidance in
  [`docs/sovereignty/`](../../../docs/sovereignty/).
- **LangGraph gotcha — state-channel reducer choice.** The generated
  `TypedDict` uses `Annotated[..., <reducer>]` for channels that
  merge across nodes. The default reducer replaces the previous
  value; that is correct for scalars like `step_status` but silently
  drops indicators when two branches both write to a `indicators`
  list. For collection-shaped channels (indicator batches, detection
  rule ids, blocklist entries), pick `operator.add` for lists or a
  custom set-union reducer for uniqued collections. Re-run
  `regenerate.sh` after changing the CACAO playbook to keep the
  state schema in sync; the drift test in `tests/examples/` catches
  the case where the committed `state_bindings.py` no longer matches
  the playbook.

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
