# examples/langgraph/eidas2_wallet/ — F-SV-02 typed-input worked example (LangGraph)

ROADMAP feature **F-SV-02** (CORE-FANOUT-LANGGRAPH). This is the
LangGraph compile target's worked example for the
[`patterns/eidas2_wallet/`](../../../patterns/eidas2_wallet/) typed
input: a Pydantic v2 model a workflow accepts when its caller has
already resolved an EU Digital Identity Wallet (EUDIW) attestation
into a verified, normalised record.

## What this example pins

The committed `typed_input/wallet-attestation-input.json` is one
representative materialised bundle the LangGraph node under
`compilers.langgraph.patterns.materialise_wallet_attestation_input_node`
produces for the payload pinned in [`regenerate.py`](regenerate.py).
The byte-parity test under
`tests/examples/langgraph/eidas2_wallet/test_langgraph_typed_input.py`
re-drives the node from that payload and pins both the worked-example
bytes and an immutable LangGraph-side fixture so a refactor of the
canonical pattern model or the LangGraph node that silently changes
serialisation is caught at the byte level.

The same test also pins the **cross-target byte-parity invariant**:
the bytes the LangGraph node writes for this payload must equal the
bytes the n8n adapter and the Temporal activity write for the
byte-identical payloads at `examples/n8n/eidas2_wallet/regenerate.py`
and `examples/temporal/eidas2_wallet/regenerate.py`. Same canonical
payload ⇒ same `input_id` ⇒ byte-identical materialised bundle across
all three compile targets, which is what makes the pattern a portable
typed input rather than a per-target shape. With this card landed the
F-SV-02 three-target fan-out is complete.

## Pattern surface, not a workflow graph

Unlike the per-workflow examples under
`examples/langgraph/<workflow>/`, this directory does **not** ship a
`workflow.langgraph.py` or a CACAO mirror. The F-SV-02 pattern is
input-only: it describes the bundle a workflow ACCEPTS, not the
graph it runs. The worked example covers the input-side
materialisation only — a LangGraph composition that consumes this
pattern registers the node on its `StateGraph` and runs it before
its own graph executes:

```python
from langgraph.graph import StateGraph
from compilers.langgraph.patterns import (
    materialise_wallet_attestation_input_node,
)

graph = StateGraph(MyState)
graph.add_node(
    "materialise_wallet_attestation_input",
    materialise_wallet_attestation_input_node,
)
```

The compiler ships no `langgraph` import; the integrator wires the
node themselves (the runtime-free convention documented in
`compilers/langgraph/__init__.py`).

## Regenerating

After any change to `patterns/eidas2_wallet/` or
`compilers/langgraph/patterns/`:

```sh
./examples/langgraph/eidas2_wallet/regenerate.sh
```

Copy the new bytes into the immutable fixture at
`tests/fixtures/eidas2_wallet/langgraph.wallet-attestation-input.json`
alongside the change. Cross-target byte-parity means the n8n and
Temporal fixtures move in lockstep — if you change one, all three
worked examples and all three fixtures must be refreshed together.

## Sovereign-stack constraints

The example writes to a local directory; an operator's LangGraph
runtime is expected to point the node's `wallet_input_output_dir`
state key at the volume their chosen EU-hosted input store ingests
from. The framework ships no hosted-SaaS default endpoint, no vendor
SDK, and no non-EU host — the upstream verifier is the operator's,
run on the operator's sovereign stack.
