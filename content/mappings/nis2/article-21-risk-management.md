# NIS2 Article 21(2)(a) — Risk-analysis evidence schema

Companion narrative to the structural mapping in
[`article-21-2-a.yaml`](./article-21-2-a.yaml). This document explains
how the **risk-analysis evidence stream** under
[`content/evidence/risk-analysis/`](../../evidence/risk-analysis/README.md)
discharges the NIS2 Article 21(2)(a) risk-management policy/procedure
obligation, how the schema is referenced (not duplicated) here, how
the three reference compile targets emit conformant artifacts, and how
drift between cadence walks is surfaced.

This file is contributor-facing prose. The structural crosswalk
(`obligation`, `control_refs`, `metric_refs`, `evidence_stream_refs`)
remains the single source of truth in
[`article-21-2-a.yaml`](./article-21-2-a.yaml); change that file when
the mapping itself changes.

## Scope

- **In:** how the risk-analysis evidence stream's artifact shape and
  cadence satisfy the policy/procedure obligation in NIS2 Article
  21(2)(a); pointers to the typed schema, to the reference emitters
  for each compile target, and to the drift-detection surface.
- **Out:** legal interpretation of Article 21(2)(a); duplication of
  the schema body (the JSON Schema is canonical and must not be
  mirrored here); the effectiveness-assessment slice — that lives
  under Article 21(2)(f) and feeds back via the F-CP-06 wave.

## Schema — pointer, not copy

The risk-analysis evidence artifact shape is declared once, in the
typed JSON Schema:

- **Authoritative schema:**
  [`schemas/evidence/risk-analysis.schema.json`](../../../schemas/evidence/risk-analysis.schema.json)
- **Contributor narrative (at-a-glance field summary):**
  [`content/evidence/risk-analysis/README.md`](../../evidence/risk-analysis/README.md)

The stream README is the human-facing entry point; the JSON Schema is
the machine-checkable contract. **Do not duplicate the schema body in
this file.** If a field name, type, or constraint changes, the schema
file is the source of truth and the stream README's at-a-glance summary
is updated alongside it; this mapping document only changes when the
*mapping* between the stream and the regulatory clause changes.

Shared vocabularies the schema imports:

- `attestation_state` enum —
  [`schemas/attestation_state.json`](../../../schemas/attestation_state.json)
  (`effective`, `partially_effective`, `ineffective`, `overdue`).
- `provenance` shape — `{ source_url, captured_at, commit_sha }`,
  mirrored from `content/controls/`.

## §21(2)(a) mapping — risk-analysis fields → policy/procedure obligation

NIS2 Article 21(2)(a) requires entities in scope to adopt and maintain
policies on risk analysis and information-system security, with
periodic re-assessment and dated, role-shaped ownership. The risk-
analysis evidence stream satisfies that obligation by emitting, on a
cadence declared on the attested control, a per-control artifact that
records *which policy is in force*, *what the operator's current
risk-analysis output is*, *who owns it as a role*, and *when it was
last re-assessed*. The wording of Article 21(2)(a) itself is in
Directive (EU) 2022/2555 (CELEX 32022L2555); see
[`article-21-2-a.yaml`](./article-21-2-a.yaml) for the citation
record. Source language is not copied into this repository.

Field-level mapping:

| Schema field                        | What it pins for §21(2)(a)                                                                                                  |
|-------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| `artifact_id`                       | Deterministic, content-addressable identity for this attestation event; lets a regulator follow the audit trail without relying on operator-side numbering.|
| `control_ref`                       | The control the artifact attests — for §21(2)(a) this is `control.risk_management_policy@v1`, the policy/procedure carrier. |
| `regulation_refs[]`                 | Pins every regulatory obligation the artifact discharges; the §21(2)(a) entry resolves to `nis2:art-21-2-a` in `article-21-2-a.yaml`. |
| `policy_version`                    | The version (SemVer or content hash) of the operator's policy text in force at capture time; this is the "adopted policy" half of the obligation. |
| `attestation_state`                 | Drawn from the four-state shared vocabulary; states the operator's current judgement on whether the policy is being maintained. |
| `attestation_state_delta`           | Transition from the previous artifact in the same `control_ref` series; lets a reviewer see *maintenance*, not just adoption. |
| `risk_analysis_output`              | The narrative half of the obligation — residual-exposure summary, scoped scenarios, deviations from baseline, compensating controls. |
| `owner`                             | Role-shaped ownership with `assigned_at`; this discharges the "dated ownership" requirement without putting an individual's name in a public-bar artifact. |
| `review_cadence`                    | ISO-8601 duration the artifact was produced under, normally copied from the control's `review_cadence`; this discharges the "periodic re-assessment" requirement. |
| `captured_at`                       | UTC capture timestamp; combined with `review_cadence`, lets a downstream consumer detect overdue re-assessment. |
| `provenance`                        | `{ source_url, captured_at, commit_sha }` — pins the provenance trail mirrored from `content/controls/`. |
| `baseline_drift`                    | Optional signal that the upstream regulation version or OSCAL catalog version has changed since the previous artifact (see §"Drift detection" below). |

The downstream KRI the stream feeds is
[`kri.risk_register_staleness@v1`](../../metrics/), referenced from
[`article-21-2-a.yaml`](./article-21-2-a.yaml) under `metric_refs`.

The board-approval / policy-text *governance* slice of §21(2)(a) (the
parts that live in document templates rather than workflow content)
is out of scope for this stream and stays in the docs templates per
the note in [`article-21-2-a.yaml`](./article-21-2-a.yaml). The
cadence-enforcement slice (effectiveness assessment) is mapped
under §21(2)(f) via the F-CP-06 effectiveness loop.

## How this is emitted

The shared emitter under `compilers/_shared/evidence/` assembles the
artifact; each of the three reference compile targets calls into the
shared emitter and writes the same on-disk bytes. Byte-parity is
pinned per target by an immutable golden:

- **n8n** — adapter under `compilers/n8n/`; per-target byte-parity
  golden at
  [`tests/examples/risk_analysis_evidence/`](../../../tests/examples/risk_analysis_evidence/)
  pinned against
  [`tests/fixtures/risk_analysis_evidence/n8n.json`](../../../tests/fixtures/risk_analysis_evidence/).
- **Temporal** — activity wiring under `compilers/temporal/`; same
  per-target test directory, pinned against
  [`tests/fixtures/risk_analysis_evidence/temporal.json`](../../../tests/fixtures/risk_analysis_evidence/).
- **LangGraph** — node wiring under `compilers/langgraph/`; same
  per-target test directory, pinned against
  [`tests/fixtures/risk_analysis_evidence/langgraph.json`](../../../tests/fixtures/risk_analysis_evidence/).

Cross-target round-trip equivalence (all three targets agree
byte-for-byte under one execution) is pinned by
[`tests/content_model/test_risk_analysis_evidence_emitter.py`](../../../tests/content_model/test_risk_analysis_evidence_emitter.py).
The per-target goldens are the EXTEND complement: a refactor of the
shared emitter that silently changes serialisation fails the test for
the specific target whose bytes drifted.

The targets are framework-agnostic by construction — each is one of
three, not the engine. An operator running a fourth compile target
implements the same shared-emitter interface and lands their own
per-target golden.

## Drift detection

Successive emissions on the same `control_ref` carry an
`attestation_state_delta.previous_state` that lets a downstream
consumer notice when a control's attestation has advanced between
cadence walks (e.g. `effective` → `partially_effective`, or `overdue`
→ `effective`).

The hook surface that exposes those transitions is in
[`compilers/_shared/evidence/drift_hook.py`](../../../compilers/_shared/evidence/drift_hook.py):

- `DriftEvent` — the dataclass naming the fields a downstream consumer
  receives for one observed transition.
- `DriftHook` — the callable type adapters thread through to the
  shared emitter.
- `noop_drift_hook` — the default the three target adapters register
  when an integrator does not supply one; a hook-less call is still a
  valid call.

The shared emitter invokes the supplied hook exactly when the record
under assembly carries an `attestation_state_delta` *and*
`previous_state` differs from the new `attestation_state` — i.e. a
real transition, not a re-emission at the same state. The surface
contract is pinned by
[`tests/content_model/test_risk_analysis_drift_hook.py`](../../../tests/content_model/test_risk_analysis_drift_hook.py).

This is intentionally a thin surface. Pinning the drift-event payload
contract per-target, promoting drift into the KPI/KRI catalog, and
durably persisting cross-run drift history are explicit follow-on
siblings of the F-CP-01 wave, not this card.

## See also

- [`article-21-2-a.yaml`](./article-21-2-a.yaml) — the structural
  mapping entry this document narrates.
- [`content/evidence/risk-analysis/README.md`](../../evidence/risk-analysis/README.md) —
  contributor home for the stream, with the at-a-glance field summary.
- [`schemas/evidence/risk-analysis.schema.json`](../../../schemas/evidence/risk-analysis.schema.json) —
  authoritative artifact shape.
- [`ROADMAP.md` §F-CP-01](../../../ROADMAP.md) — feature definition and
  acceptance criteria.
