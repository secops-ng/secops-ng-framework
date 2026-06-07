# content/evidence/risk-analysis/

Risk-analysis evidence stream — the first stream in the SecOps-NG
**evidence** layer.

## What this stream is

An operator working under NIS2 or DORA scope has to demonstrate, on a
cadence, that their risk-management policy is adopted, periodically
re-assessed, and owned by a named role. That demonstration takes the
shape of a per-control artifact emitted every time the cadence walker
runs.

This directory is the contributor home for that stream. The artifact
shape is declared in
[`schemas/evidence/risk-analysis.schema.json`](../../../schemas/evidence/risk-analysis.schema.json);
the cadence it is walked under is declared on each control
(`review_cadence` on
[`content/controls/control.risk_management_policy@v1.yaml`](../../controls/control.risk_management_policy@v1.yaml));
the residual-exposure indicator it feeds is
[`kri.control_effectiveness@v1`](../../metrics/control_effectiveness.yaml).

The stream is framework-agnostic. A reference emitter for each of the
three compile targets (n8n, Temporal, LangGraph) lands under
`examples/` once the F-CP-01 EMITTER card ships.

## Regulator hooks

| Regulation            | Article                          | Obligation paraphrase                                                                                                                  | Mapping file                                                                       |
|-----------------------|----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| NIS2                  | Art. 21(2)(a)                    | Adopt and maintain policies on risk analysis and information-system security, including periodic re-assessment with dated ownership.   | [`content/mappings/nis2/article-21-2-a.yaml`](../../mappings/nis2/article-21-2-a.yaml) |
| DORA                  | Art. 5 (Governance)              | Internal governance and control framework for ICT risk, with annual review and management-body approval.                              | [`content/mappings/dora/article-5.yaml`](../../mappings/dora/article-5.yaml)         |
| DORA                  | Art. 6 (ICT risk-management framework) | Establish, document and maintain a sound ICT risk-management framework, reviewed at least annually and after major ICT incidents.    | [`content/mappings/dora/article-6.yaml`](../../mappings/dora/article-6.yaml)         |

NIS2 Art. 21(2)(f) (effectiveness assessment) consumes the artifacts
this stream emits via the F-CP-06 effectiveness loop; the wiring lands
when F-CP-06 opens.

## Artifact shape — pointer

Authoritative shape: [`schemas/evidence/risk-analysis.schema.json`](../../../schemas/evidence/risk-analysis.schema.json).

At a glance, each artifact carries:

- `artifact_id` — deterministic SHA-256 of `<control_ref>|<captured_at>`.
- `control_ref` — the control attested by this artifact.
- `regulation_refs[]` — pin to every regulatory obligation the artifact
  satisfies (typically the NIS2 + DORA entries above).
- `policy_version` — SemVer or content hash of the operator's policy
  document.
- `attestation_state` — one of `effective`, `partially_effective`,
  `ineffective`, `overdue`. Imported from the shared
  [`schemas/attestation_state.json`](../../../schemas/attestation_state.json)
  vocabulary.
- `attestation_state_delta` — transition from the previous artifact in
  the same `control_ref` series (omitted on first emission).
- `risk_analysis_output` — operator-side narrative: residual-exposure
  summary, scoped scenarios, deviations from baseline, compensating
  controls.
- `owner` — role-shaped ownership pointer with `assigned_at` date. No
  individual personal names.
- `review_cadence` — ISO-8601 duration the artifact was produced
  under; normally copied from the control.
- `captured_at` — ISO-8601 UTC timestamp.
- `provenance` — `{ source_url, captured_at, commit_sha }` mirror of
  the pattern used in `content/controls/`.
- `baseline_drift` — optional drift signal set when the upstream
  regulation version or OSCAL catalog version has changed since the
  previous artifact.

## Contributor checklist

If you are proposing a change that touches this stream:

1. The schema is the source of truth — change
   `schemas/evidence/risk-analysis.schema.json` first, then update
   this README's at-a-glance summary if a field is added or removed.
2. The `attestation_state` vocabulary lives in
   `schemas/attestation_state.json` — extending the state set is a
   discussion, not a drive-by change.
3. The `review_cadence` field on a control is operator-overridable; do
   not hard-code an operator's stricter cadence into the community
   default.
4. Run the content-model tests:

   ```sh
   python -m pytest tests/content_model/
   ```

5. Run the forward-public hygiene linter:

   ```sh
   python -m tools.hygiene_linter --min-severity LOW
   ```

6. Follow the
   [`AGENTS.md` §3 public-bar rules](../../../AGENTS.md): no commercial
   framing, no credentials, no internal infrastructure references, no
   individual lead names.

## Status

The stream's schema, enum promotion, and control cadence land in this
card (F-CP-01 SCHEMA). The cross-stream evidence index
(`content/evidence/README.md`), the workflow emitter, the drift-detection
hook, KPI/KRI wiring, and the per-target byte-parity golden tests fan
out into sibling cards 2–10 of the F-CP-01 wave.
