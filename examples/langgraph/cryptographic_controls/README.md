# cryptographic_controls — LangGraph worked example

End-to-end demonstration of the SecOps-NG LangGraph reference compiler
on the `cryptographic_controls` CACAO playbook. This is the write-side
lifecycle counterpart to `crypto_posture_management`: it operates the
key-generate / key-rotate / key-revoke branch, the encryption-
enforcement gate against declared at-rest and in-transit floors, the
certificate issue / renew / revoke branch, and the dated lifecycle
attestation NIS2 Art. 21(2)(h) and DORA Art. 9(2)/(3) anchor on.

This worked example closes the cross-target parity ring (target 3 of 3)
for the `cryptographic_controls` playbook. The Temporal and n8n
siblings already ship under `../../temporal/cryptographic_controls/`
and `../../n8n/cryptographic_controls/`; together the three folders
pin the full three-target contract for this playbook.

## Files in this directory

| File | Role |
|------|------|
| `playbook.cacao.json` | Portable CACAO v2 playbook — byte-identical mirror of `content/playbooks/cryptographic_controls/playbook.cacao.json`, the input to the compiler. |
| `graph_spec.json` | Target-neutral GraphSpec (nodes, edges, conditional edges) emitted by `compilers.langgraph.emit`. |
| `state_bindings.py` | Generated `TypedDict` state + `@tool`-decorated action wrappers + agentic-extension hook, emitted by `compilers.langgraph.state`. |
| `assemble.py` | Hand-written reference assembly that wires the GraphSpec + bindings into a `langgraph.graph.StateGraph`. |
| `_audit_mirror.py` | Dependency-free audit-mirror sibling; see docs/observability/audit-mirror.md. |
| `regenerate.sh` | Re-runs both emitters from the canonical playbook and overwrites the mirrored CACAO + the generated artifacts. |

## How to regenerate

After any change to the canonical playbook or to `compilers/langgraph/*`,
refresh the committed artifacts from the repo root:

```bash
./examples/langgraph/cryptographic_controls/regenerate.sh
```

The script mirrors the canonical CACAO source into this folder and
re-emits `graph_spec.json` and `state_bindings.py` from it using
`compilers.langgraph.emit` and `compilers.langgraph.state`. A drift
test in `tests/examples/langgraph/cryptographic_controls/` fails the
suite if the committed artifacts diverge from a fresh regeneration.

## Cross-target pointers

The same canonical playbook ships under the other two reference compile
targets so an integrator can compare lowerings side by side:

- [`examples/n8n/cryptographic_controls/`](../../n8n/cryptographic_controls/) — n8n no-code workflow.
- [`examples/temporal/cryptographic_controls/`](../../temporal/cryptographic_controls/) — Temporal durable workflow stub.

## Topology

The cryptographic_controls playbook is a linear resolve-policy /
key-lifecycle / enforce-encryption / certificate-lifecycle /
record-evidence / notify chain with no conditional branching at the
workflow layer. Six GraphSpec action nodes, one per CACAO action step:

1. `resolve policy inventory` — resolve the operator's declared
   cryptography policy at the start of the lifecycle event.
2. `key lifecycle` — discharge the generate / rotate / revoke branch
   against the operator's KMS backend.
3. `enforce encryption` — evaluate the encryption-enforcement gate on
   the pair of at-rest and in-transit conditions the policy names.
4. `certificate lifecycle` — discharge the issue / renew / revoke
   branch against the operator's CA backend.
5. `record lifecycle evidence` — persist the dated lifecycle-
   attestation record to the operator's evidence store.
6. `notify crypto owner` — surface the attestation to the cryptography
   owner via the operator's notification channel.

Because the playbook is linear, the emitted GraphSpec has no
`conditional_edges`; every edge is an unconditional `on_completion`
hand-off. The conditional-edge router pattern documented in
`assemble.py` is still imported and exercised for parity with the
other LangGraph worked examples — it is a no-op for this playbook but
makes the assembly file copy-paste-ready for playbooks that do branch.

## What this example deliberately doesn't do

- It does not execute the graph. The `@tool` bodies raise
  `NotImplementedError`; integrators wire them to their own runtime
  (KMS backend, CA backend, storage-encryption backend, TLS-endpoint
  backend, evidence store, notification channel).
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
