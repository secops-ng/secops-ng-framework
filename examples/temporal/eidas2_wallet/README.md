# examples/temporal/eidas2_wallet/ — F-SV-02 typed-input worked example (Temporal)

ROADMAP feature **F-SV-02** (CORE-FANOUT-TEMPORAL). This is the
Temporal compile target's worked example for the
[`patterns/eidas2_wallet/`](../../../patterns/eidas2_wallet/) typed
input: a Pydantic v2 model a workflow accepts when its caller has
already resolved an EU Digital Identity Wallet (EUDIW) attestation
into a verified, normalised record.

## What this example pins

The committed `typed_input/wallet-attestation-input.json` is one
representative materialised bundle the Temporal activity under
`compilers.temporal.patterns.materialise_wallet_attestation_input_activity`
produces for the payload pinned in [`regenerate.py`](regenerate.py).
The byte-parity test under
`tests/examples/temporal/eidas2_wallet/test_temporal_typed_input.py`
re-drives the activity from that payload and pins both the
worked-example bytes and an immutable Temporal-side fixture so a
refactor of the canonical pattern model or the Temporal activity that
silently changes serialisation is caught at the byte level.

The same test also pins the **cross-target byte-parity invariant**:
the bytes the Temporal activity writes for this payload must equal
the bytes the n8n sibling adapter writes for the byte-identical
payload at `examples/n8n/eidas2_wallet/regenerate.py`. Same canonical
payload ⇒ same `input_id` ⇒ byte-identical materialised bundle across
compile targets, which is what makes the pattern a portable typed
input rather than a per-target shape.

The LangGraph sibling of this fan-out lands on a separate card (F-SV-02
CORE-FANOUT-LANGGRAPH), mirroring the F-WF-12 per-target split.

## Pattern surface, not a workflow graph

Unlike the per-workflow examples under
`examples/temporal/<workflow>/`, this directory does **not** ship a
`workflow.temporal.py` or a CACAO mirror. The F-SV-02 pattern is
input-only: it describes the bundle a workflow ACCEPTS, not the
graph it runs. The worked example covers the input-side
materialisation only — a Temporal workflow that consumes this
pattern calls the activity before its own state machine runs.

## Regenerating

After any change to `patterns/eidas2_wallet/` or
`compilers/temporal/patterns/`:

```sh
./examples/temporal/eidas2_wallet/regenerate.sh
```

Copy the new bytes into the immutable fixture at
`tests/fixtures/eidas2_wallet/temporal.wallet-attestation-input.json`
alongside the change. If the change is intentional and the canonical
serialisation moved, the n8n sibling's worked example and fixture
must move in the same PR — otherwise the cross-target byte-parity
test fails.

## Sovereign-stack constraints

The example writes to a local directory; an operator's Temporal
worker is expected to point the activity's `output_dir` at the volume
their chosen EU-hosted input store ingests from. The framework ships
no hosted-SaaS default endpoint, no vendor SDK, and no non-EU host —
the upstream verifier is the operator's, run on the operator's
sovereign stack.
