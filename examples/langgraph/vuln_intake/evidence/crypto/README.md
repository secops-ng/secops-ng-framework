# examples/langgraph/vuln_intake/evidence/crypto

Worked example: one crypto-attestation evidence artifact for a
representative execution of the `playbook.vuln_intake@v1` playbook
compiled by the LangGraph reference compiler. The vuln_intake workflow
consumes a small set of provider secrets during triage (CVE / EPSS
data feed tokens, optional AI risk-summary generator key), so it is
the canonical F-CP-05 worked path on the LangGraph side and mirrors
the F-CP-03 supply-chain worked example under
`examples/langgraph/vuln_intake/evidence/supply-chain/`.

## Source

The artifact is produced by the LangGraph-side node adapter at
`compilers/langgraph/evidence/crypto_attestation_node.py`, which wraps
the shared emitter under
`compilers/_shared/evidence/crypto_attestation.py`. A preceding node —
the one that bootstraps the run and records which UPPER_SNAKE_CASE
environment-variable names the running graph reads for secret material
— assembles the typed `CryptoAttestationContext` and places it on the
running state under the `crypto_attestation_context` key together
with an `evidence_output_dir`; the node adapter then delegates record
assembly, env-only-injection enforcement, and the atomic write to the
shared helper. Only UPPER_SNAKE_CASE *names* travel through the
context — no values, no fragments — and the shared helper rejects
anything that does not match the schema's regex at the boundary.

## Layout

| Path                                 | Source compiler                                            | Format        |
|--------------------------------------|------------------------------------------------------------|---------------|
| `secret-handling-attestation.json`   | `compilers.langgraph.evidence.crypto_attestation_node`     | evidence JSON |
| `regenerate.py`                      | (tooling)                                                  | python script |

The committed snapshot is named with the human-friendly
`secret-handling-attestation.json` filename for diffing; the node
writes it to disk as `<artifact_id>.json` where `artifact_id` is
`SHA-256(<workflow_id>|<execution_id>|<compile_target>)`. The snapshot
validates against `schemas/evidence/crypto-attestation.schema.json`
and carries the three mechanical assertions the stream exists to
record: `secrets_baked_in: false`, `injection_mode: env`, and the list
of declared `env_var_refs`. The regulator hook anchors on NIS2
Art. 21(2)(h) and Core Directive #6 (Secret Management).

## Regenerate

From the repo root:

```sh
PYTHONPATH=. python examples/langgraph/vuln_intake/evidence/crypto/regenerate.py
```

Re-runs with the same `(workflow_id, execution_id, compile_target)`
tuple reproduce the same artifact byte-for-byte — the snapshot is
deterministic. `captured_at` is deliberately *not* part of
`artifact_id`, so re-emissions inside a single execution land on the
same path with byte-stable content.
