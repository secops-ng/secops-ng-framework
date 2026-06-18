# examples/temporal/vuln-intake/evidence/effectiveness

Worked example: one effectiveness evidence artifact for a
representative evaluation of the `playbook.vuln_intake@v1` playbook
compiled by the Temporal reference compiler. Mirrors the F-CP-03
supply-chain and F-CP-05 crypto-attestation Temporal worked examples
under `examples/temporal/vuln-intake/evidence/supply-chain/` and
`examples/temporal/vuln-intake/evidence/crypto/`.

## Source

The artifact is produced by the Temporal-side activity adapter at
`compilers/temporal/evidence/effectiveness_activity.py`, which wraps
the shared emitter under `compilers/_shared/evidence/effectiveness.py`.
A Temporal workflow assembles an `EffectivenessContext` from its own
state (the metric stable-id, the pinned subject version, the
pre-computed indicator value, the source-shape pointer) and invokes
the activity through the standard Temporal activity-execution path.

The pre-computed `measurement.value` is the snapshot — the underlying
sample (which may carry personal data) is deliberately out of scope
at this layer per AGENTS.md §3; the `measurement.source_shape` pointer
is the public-bar-safe surface a reviewer needs.

## Layout

| Path                                  | Source compiler                                       | Format        |
|---------------------------------------|-------------------------------------------------------|---------------|
| `control-effectiveness-snapshot.json` | `compilers.temporal.evidence.effectiveness_activity`  | evidence JSON |
| `regenerate.py`                       | (tooling)                                             | python script |

The committed snapshot is named with the human-friendly
`control-effectiveness-snapshot.json` filename for diffing; the
activity writes it to disk as `<artifact_id>.json` where
`artifact_id` is
`SHA-256(<workflow_id>|<execution_id>|<compile_target>|<metric_ref>|<subject_version.value>)`.
`captured_at` is deliberately *not* part of `artifact_id`, so
re-emissions inside a single evaluation land on the same path with
byte-stable content. The snapshot validates against
`schemas/evidence/effectiveness.schema.json` and anchors on
NIS2 Article 21(2)(f) (effectiveness measurement of cyber-risk
management measures).

## Regenerate

From the repo root:

```sh
PYTHONPATH=. python examples/temporal/vuln-intake/evidence/effectiveness/regenerate.py
```

Re-runs with the same `(workflow_id, execution_id, compile_target,
metric_ref, subject_version.value)` tuple reproduce the same artifact
byte-for-byte — the snapshot is deterministic.
