# content/evidence/sovereignty/

Sovereignty posture evidence stream (F-SV-04) — the eleventh stream in
the SecOps-NG **evidence** layer.

## What this stream is

The catalogue measures the sovereign posture from twenty-one angles —
the sovereignty cluster under `content/metrics/` (fifteen KPIs, six
KRIs, every one carrying `foundation_property: sovereignty`) — but
until this stream it emitted nothing. An operator could observe that
they are EU-resident and still be unable to hand a reviewer a dated
artifact saying so, which is the difference between claiming the
property and evidencing it.

This stream closes that gap with one artifact per attestation exercise:
the assessment window, **one observation per sovereignty-cluster
indicator** (its observed value, the threshold band it fell in against
the indicator's own catalogue thresholds, and when it was sampled), and
an attestation state drawn from the shared four-state vocabulary in
[`schemas/attestation_state.json`](../../../schemas/attestation_state.json).

The artifact shape is declared in
[`schemas/evidence/sovereignty.schema.json`](../../../schemas/evidence/sovereignty.schema.json);
the indicator definitions and their thresholds remain owned by the
catalogue entries under [`content/metrics/`](../../metrics/). This
stream never re-declares either.

## The two disciplines the schema enforces

**Completeness is mechanical, not aspirational.** The `observations`
object requires every sovereignty-cluster indicator and accepts no
other key. A record that omits an indicator fails validation, so the
stream cannot silently under-report the posture it attests to — an
operator who cannot observe an indicator records it with its
`overdue`-shaped truth rather than dropping it. When a new
sovereignty-tagged metric lands in the catalogue,
`tests/content_model/test_sovereignty_evidence_schema.py` fails naming
the metric and this schema as the file to edit — the same
force-a-classification shape as the playbook family map.

**No numeric aggregate, deliberately.** The record carries
per-indicator observations and never a single sovereignty score. A
ratio invites "N% sovereign", which is not a defensible claim — the
same reasoning that keeps a percentage out of the SOC 2 readiness
attestation. The `attestation_state` field is a categorical state about
the attestation exercise itself, not a verdict; evaluating the
observations against a declared baseline is the job of the F-SV-05
conformance profile, which consumes this artifact.

## Sovereign-stack constraints

No default sink and no network call: the stream is composed from
observations the operator supplies. The emitted artifact carries no
endpoint literal, so it cannot itself become a non-EU reference that
`kri.hardcoded_non_eu_endpoint_reference_count@v1` would count.

## Status

Shipped. SKELETON (#898): stream layout, artifact schema, and the
validation guards above. CORE (#899): the shared emitter at
[`compilers/_shared/evidence/sovereignty.py`](../../../compilers/_shared/evidence/sovereignty.py)
— which enforces the all-indicators completeness contract and the
window-containment rule *before* any file is written, so a gapped
attestation is refused rather than fabricated — plus the three thin
target adapters (n8n node, Temporal activity, LangGraph node) and
byte-parity worked examples anchored on `infra_posture_management`
under `examples/<target>/infra_posture_management/evidence/sovereignty/`.

## Consumers

- **F-SV-05 — Declared sovereignty conformance profile** (Proposed):
  evaluates a record from this stream against a declared indicator
  baseline, deterministically — same record plus same profile yields
  the same per-indicator verdict.
- Reviewer/auditor surfaces that today receive the claim without the
  artifact.
