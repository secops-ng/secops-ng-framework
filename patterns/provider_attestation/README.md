# `provider_attestation` — periodic sovereign-provider re-verification

A durable Temporal workflow that periodically re-checks whether a declared
sovereign provider still satisfies a set of criteria, writes one attestation
record per cycle, and raises a structured regression event when a criterion
that previously passed starts failing.

## When to use it

You have a sovereign provider (compute, storage, identity, ...) declared in a
knowledge base with a known set of criteria (residency, certifications,
encryption posture, contractual basis) and you want to:

* Re-verify those criteria on a fixed cadence, durably.
* Persist one attestation artifact per cycle for audit.
* Get a structured event the moment a criterion regresses from pass to fail,
  so an upstream router can fan it out to a ticket, a chat channel, or
  another workflow.

The pattern deliberately does **not** decide what evidence to use for each
criterion. Replace the body of `verify_criterion` to call your real check
(KB lookup, configuration probe, document existence check); the workflow
contract stays the same.

## Surface

### Input

```python
class ProviderAttestationInput(BaseModel):
    provider_id: str
    criteria: list[str]
    fixture_dir: str       # where load_provider_snapshot reads from
    attestation_dir: str   # where write_attestation writes to
    interval_seconds: int = 3600
    max_cycles: int = 1
```

### Signals

* `stop()` — request the workflow exit after the current cycle.

### Queries

* `attestations() -> list[AttestationRef]` — records produced so far.
* `regressions() -> list[RegressionEvent]` — regressions detected so far.

### Result

```python
class ProviderAttestationResult(BaseModel):
    attestations: list[AttestationRef]
    regressions: list[RegressionEvent]
```

### Activities

* `load_provider_snapshot(provider_id, fixture_dir) -> ProviderSnapshot` —
  reads `<provider_id>.yaml` from `fixture_dir`, falling back to
  `sample_provider.yaml`. Replace for a real KB lookup.
* `verify_criterion(criterion_id, snapshot) -> CriterionResult` — evaluates
  one criterion against the snapshot. The bundled implementation reads
  `snapshot.criteria[criterion_id]`; replace with your real check.
* `write_attestation(record, attestation_dir) -> AttestationRef` — persists
  one JSON record per cycle to `<provider_id>-<cycle>.json`. Idempotent.

## Durability notes

* Cadence is driven by `workflow.sleep` — the workflow is resilient to
  worker restarts and resumes on the same schedule.
* `_last_pass` records whether each criterion passed in the previous cycle.
  Replays reconstruct the same map from history, so regression detection
  is deterministic.
* `write_attestation` overwrites `<provider_id>-<cycle>.json` on retry,
  keeping the activity safe under Temporal's at-least-once delivery.
* `max_cycles` bounds the run so tests terminate cleanly. For long-lived
  production use, increase it or wrap in a continue-as-new caller.

## Fixtures

`fixtures/sample_provider.yaml` is a generic example
(`eu-provider-alpha`, `region-eu-west`, four placeholder criteria). Generated
attestation records live under `fixtures/attestations/` and are gitignored.

## Tests

`tests/` exercises the seeded-snapshot happy path, the regression-event
emission on a pass -> fail transition, the `stop` signal exit path, and a
replay test that proves the workflow body is deterministic.
