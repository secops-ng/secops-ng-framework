# examples/n8n/eidas2_wallet/ — F-SV-02 typed-input worked example (n8n)

ROADMAP feature **F-SV-02** (CORE-FANOUT-N8N). This is the n8n
compile target's worked example for the
[`patterns/eidas2_wallet/`](../../../patterns/eidas2_wallet/) typed
input: a Pydantic v2 model a workflow accepts when its caller has
already resolved an EU Digital Identity Wallet (EUDIW) attestation
into a verified, normalised record.

## What this example pins

The committed
`typed_input/wallet-attestation-input.json` is one representative
materialised bundle the n8n adapter under
`compilers.n8n.patterns.materialise_wallet_attestation_input_n8n`
produces for the payload pinned in [`regenerate.py`](regenerate.py).
The byte-parity test under
`tests/examples/n8n/eidas2_wallet/test_n8n_typed_input.py` re-drives
the adapter from that payload and pins both the worked-example bytes
and an immutable fixture so a refactor of the canonical pattern
model or the n8n adapter that silently changes serialisation is
caught at the byte level.

The Temporal and LangGraph siblings of this fan-out land on
separate cards (F-SV-02 CORE-FANOUT-TEMPORAL / -LANGGRAPH), mirroring
the F-WF-12 per-target split.

## Pattern surface, not a workflow graph

Unlike the per-workflow examples under
`examples/n8n/<workflow>/`, this directory does **not** ship a
`workflow.n8n.json` or a CACAO mirror. The F-SV-02 pattern is
input-only: it describes the bundle a workflow ACCEPTS, not the
graph it runs. The worked example covers the input-side
materialisation only — an n8n workflow that consumes this pattern
calls the adapter from an `executeCommand` or `Code` node before
its own graph runs.

## Regenerating

After any change to `patterns/eidas2_wallet/` or
`compilers/n8n/patterns/`:

```sh
./examples/n8n/eidas2_wallet/regenerate.sh
```

Copy the new bytes into the immutable fixture at
`tests/fixtures/eidas2_wallet/n8n.wallet-attestation-input.json`
alongside the change.

## Sovereign-stack constraints

The example writes to a local directory; an operator's n8n node is
expected to point the adapter's `output_dir` at the volume their
chosen EU-hosted input store ingests from. The framework ships no
hosted-SaaS default endpoint, no vendor SDK, and no non-EU host —
the upstream verifier is the operator's, run on the operator's
sovereign stack.
