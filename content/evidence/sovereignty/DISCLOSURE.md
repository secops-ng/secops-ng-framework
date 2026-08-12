# Sovereignty conformance disclosure pack

The disclosure pack is the redacted, self-contained artifact an
operator publishes to substantiate a sovereignty claim — typically as
the **Evidence link** of their [`USED-BY.md`](../../../USED-BY.md)
row. It is the public face of the Epic SV chain: the posture is
*measured* (the 26-indicator sovereignty cluster), *evidenced* (this
stream's F-SV-04 records), *judged* (the F-SV-05 profile evaluation),
and — with this pack — *disclosed*.

## What the pack carries

| Field | Content |
|---|---|
| `disclosure_pack` | Format discriminator: `sovereignty-conformance-disclosure/v1`. |
| `profile` | Stable id of the profile the record was judged against. |
| `record` | The evidence record's `artifact_id` (digest-shaped). |
| `record_sha256` | SHA-256 of the exact record bytes evaluated — a reviewer holding the record can verify which snapshot was disclosed. |
| `assessment_window` | The record's `from`/`to` window. |
| `indicators` | Every indicator in the verdict: `outcome` (`pass` / `fail` / `unobserved` / `unprofiled`), the `observed_band` / `required_band` pair, and `via_override` where a recorded relaxation applied. |
| `pass` | The boolean roll-up. |
| `provenance` | Renderer name and version, evaluator module. |

The pack validates against
[`schemas/sovereignty-disclosure-pack.schema.json`](../../../schemas/sovereignty-disclosure-pack.schema.json),
whose `additionalProperties: false` at every level makes the schema
the redaction contract in machine-readable form.

## The redaction contract

A pack MUST NOT carry:

- **Endpoint literals or URLs of any kind** — the same constraint the
  F-SV-04 stream places on itself: a sovereignty artifact cannot be
  the non-EU reference the catalogue would count.
- **Internal identifiers** — workflow ids, execution ids and compile
  targets stay in the record; the pack carries only the digest-shaped
  `artifact_id` and the byte digest.
- **Raw observed values** — per indicator the pack discloses the
  *band* the value fell in, never the value. The band is the posture;
  the value is telemetry, and telemetry stays with the operator.

The renderer enforces this by construction (the pack is assembled
from an explicit field allowlist) and backstops it with a scan of the
serialised output: a forbidden marker aborts rendering with exit
code 2 rather than producing a leaking artifact.

## The honesty contract

Every indicator in the verdict appears in the pack — including
`fail`, `unobserved` and `unprofiled` outcomes — and the roll-up is a
boolean, never a score. A pack that renders only its passing rows, or
compresses the posture to "94 % sovereign", is not a disclosure; the
schema rejects the second by construction and review rejects the
first. The committed worked example below fails its own baseline — the
failing rows are the work queue the profile names, and publishing
them is the point.

## Generating a pack

```bash
python -m tools.render_disclosure_pack \
    path/to/sovereignty-posture-attestation.json \
    --baseline content/profiles/sovereignty_conformance.yaml \
    --output disclosure-pack.json
```

Deterministic: the same record and profile bytes yield a
byte-identical pack — no clock read, no network access. When
`--baseline` is given, a profile that quietly relaxes below the
baseline without a recorded override is refused before rendering, so
a pack cannot be flattered by profile drift. Rendering succeeds
whether or not the posture holds: disclosure is not a gate.

## Worked example

[`examples/temporal/infra_posture_management/evidence/sovereignty/disclosure-pack.json`](../../../examples/temporal/infra_posture_management/evidence/sovereignty/disclosure-pack.json)
is rendered from the committed reference record against the shipped
baseline and regenerates byte-identically in CI. It carries the
reference posture's true verdict — `"pass": false`, with the
LM-endpoint coverage and non-EU critical-dependency rows failing —
exactly as the F-SV-05 tests pin it.
