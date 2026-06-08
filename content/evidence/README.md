# content/evidence/

Evidence layer. Per-stream directories under `content/evidence/<stream>/`
hold the contributor home for each compliance-evidence stream the
framework emits. Each stream is paired with a typed schema under
`schemas/evidence/`, walked under a control-declared `review_cadence`,
and consumed by the corresponding regulatory crosswalks under
`content/mappings/`.

Streams are framework-agnostic. The shared emitter helpers live under
[`compilers/_shared/evidence/`](../../compilers/_shared/evidence/) and
each compile target wraps the same helper in a thin adapter:

| Target | Adapter | Surface |
|--------|---------|---------|
| Temporal | [`compilers/temporal/evidence/`](../../compilers/temporal/evidence/) | `@activity.defn` async activity |
| n8n | [`compilers/n8n/evidence/`](../../compilers/n8n/evidence/) | Python helper called from an `executeCommand` / `Code` node |
| LangGraph | [`compilers/langgraph/evidence/`](../../compilers/langgraph/evidence/) | Plain `state → state` node function |

Record assembly, deterministic `artifact_id` derivation, schema
validation, and the atomic write live on the shared helper — adapters
are glue only and never fork record shape per target.

## Cross-stream index

The seven streams correspond to the F-CP epic in
[`ROADMAP.md`](../../ROADMAP.md) (Epic CP — Compliance Evidence
Pipeline). Each row is the contributor home for one stream; the schema
column points to the typed shape the stream emits.

| Stream | Card | Directory | Status | One-line summary |
|--------|------|-----------|--------|------------------|
| Risk-analysis | F-CP-01 | [`risk-analysis/`](risk-analysis/README.md) | In Progress | Per-control attestation that the operator's risk-management policy is adopted, owned by a named role, and re-assessed on its declared cadence (NIS2 Art. 21(2)(a), DORA Art. 5–6). |
| Incidents | F-CP-02 | _pending_ | Proposed | Per-incident artifact emitted by the incident-management workflow, scoped to NIS2 reporting windows (NIS2 Art. 21(2)(b), Art. 23). |
| Supply-chain | F-CP-03 | _pending_ | Proposed | Dependencies snapshot per workflow execution that calls an external provider, including provider sovereignty classification (NIS2 Art. 21(2)(d), Art. 22). |
| Vulnerabilities | F-CP-04 | _pending_ | In Progress | Triage decisions and disclosure timelines emitted by `vulnerability_triage`, wired to the CVD-timing KPI family (NIS2 Art. 21(2)(e), CRA Art. 11). |
| Crypto attestation | F-CP-05 | _pending_ | Proposed | Per-execution attestation that no secret was baked into workflow code — env-only injection, hard-failed at boot otherwise (NIS2 Art. 21(2)(h), Core Directive #6). |
| Effectiveness | F-CP-06 | _pending_ | Proposed | Metric snapshots per policy / prompt version, DSPy-evaluatable, consumed by the NIS2 Art. 21(2)(f) effectiveness loop. |
| Access | F-CP-07 | _pending_ | Proposed | Per-execution caller identity and capability list (NIS2 Art. 21(2)(i)). |

Status values mirror the ROADMAP entry for each card. A `_pending_`
directory means the stream's schema and contributor README have not
landed yet; the row is named here so cross-stream references resolve
once the sibling card opens.

## Contributor checklist

Before opening a PR that touches an evidence stream:

1. **Provenance.** Every artifact carries a `provenance` block of the
   shape `{ source_url, captured_at, commit_sha }` — the same shape
   used in `content/controls/`. New streams reuse this block verbatim.
2. **Schema home.** The typed shape lives in
   `schemas/evidence/<stream>.schema.json`. The schema is the source of
   truth; the stream's `README.md` only carries the at-a-glance
   summary. Change the schema first, then update the README.
3. **Evidence-artifact contract.** Every artifact is deterministically
   addressable: `artifact_id` is a SHA-256 over a stable key (typically
   `<primary_ref>|<captured_at>`). The `attestation_state` vocabulary
   is shared across streams via
   [`schemas/attestation_state.json`](../../schemas/attestation_state.json) —
   do not fork it per stream.
4. **KRI / KPI wiring.** Every stream feeds at least one indicator in
   `content/metrics/`. Name the indicator(s) in the stream README's
   regulator-hooks table. A stream that does not feed a KRI or KPI is
   not yet a stream.
5. **Hygiene-linter clean.** Run the forward-public hygiene linter
   locally:

   ```sh
   python -m tools.hygiene_linter --min-severity LOW
   ```

   HIGH findings block merge; MEDIUM findings (commercial language)
   trigger maintainer review.
6. **Tests-schema present.** Add a test under `tests/content_model/`
   (or extend an existing one) that asserts the stream's schema loads,
   that any shipped fixtures validate, and that the stream's
   `attestation_state` values are drawn from the shared enum.
7. **Public-bar.** Follow
   [`AGENTS.md` §3](../../AGENTS.md): no commercial framing, no
   credentials, no internal infrastructure references, no individual
   lead names. The evidence layer is read by operators, regulators,
   and reviewers — write for that audience.

## Status

Cards 1–3 of the F-CP-01 wave shipped the SCHEMA, the STREAM-ROOT, and
the EMITTER SKELETON (Temporal-only activity wrapper). The CORE-FANOUT
card extends the SKELETON to the remaining two compile targets — n8n
and LangGraph — sharing the same emitter helper end-to-end. The
drift-detection hook, KPI/KRI wiring, and per-target byte-parity golden
tests fan out into the remaining sibling cards of the F-CP-01 wave;
the F-CP-02..F-CP-07 streams each open their own SCHEMA → STREAM-ROOT →
EMITTER decomposition as they land.
