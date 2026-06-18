# content/evidence/effectiveness/

Effectiveness evidence stream — the sixth stream in the SecOps-NG
**evidence** layer (after `risk-analysis/`, `incidents/`,
`supply-chain/`, `vulns/`, and `crypto/`).

## What this stream is

An operator running framework-compiled workflows under NIS2 Article
21(2)(f) (effectiveness assessment of risk-management measures) has to
demonstrate that the risk-management measures the organisation has
adopted are not just on paper — that they are being *assessed* for
effectiveness on a declared cadence, that the results are archived,
and that the indicators feeding the assessment are pinned to the
specific policy version or prompt version that was in force at
evaluation time.

That demonstration takes the shape of one snapshot per (metric,
policy-or-prompt-version, evaluation-window). The snapshot is
mechanical: a numeric value with its unit and direction, the indicator
stable-id it measures, the subject version it was evaluated against,
a pointer to the source-data shape (typically an OCSF event class)
the indicator was derived from, and the usual provenance and
captured-at envelope.

The reference indicator the F-CP-06 stream reads against is the
catalogue's
[`kri.control_effectiveness@v1`](../../metrics/control_effectiveness.yaml).
The snapshot artifact does **not** duplicate the metric definition —
the catalogue entry remains the source of truth for the unit, the
direction, the thresholds, and the measurement formula. The snapshot
is the per-evaluation pin: which version of the policy or prompt the
indicator was measured against, and what value it took at that point.

This directory is the contributor home for that stream. The artifact
shape is declared in
[`schemas/evidence/effectiveness.schema.json`](../../../schemas/evidence/effectiveness.schema.json);
the regulatory anchor is
[`content/mappings/nis2/article-21-2-f.yaml`](../../mappings/nis2/article-21-2-f.yaml),
with the contributor-facing companion narrative under
[`article-21-2-f-effectiveness.md`](../../mappings/nis2/article-21-2-f-effectiveness.md).

The stream is framework-agnostic. Reference emitters for each of the
three compile targets (n8n, Temporal, LangGraph) land under
`compilers/` in the sibling CORE-FANOUT card; this SKELETON card
deliberately ships schema + stream-root + mapping stub only.

## Regulator hooks

| Regulation | Article          | Obligation paraphrase                                                                                                                | Mapping file                                                                       |
|------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| NIS2       | Art. 21(2)(f)    | Policies and procedures to assess the effectiveness of cybersecurity risk-management measures, with results archived.                | [`content/mappings/nis2/article-21-2-f.yaml`](../../mappings/nis2/article-21-2-f.yaml) |

The stream feeds three indicators in `content/metrics/`:

- [`kri.control_effectiveness@v1`](../../metrics/control_effectiveness.yaml) —
  share of in-scope controls NOT in the `effective` state.
- `kpi.control_effectiveness_coverage@v1` — coverage of the in-scope
  control set by an in-cadence effectiveness test.
- `kri.overdue_effectiveness_tests@v1` — count of controls whose most
  recent effectiveness test predates the declared review cadence.

The KPI/KRI promotions and the wiring of those indicators into the
snapshot's `metric_ref` field are decided per-emitter in the
CORE-FANOUT sibling; the schema floor accepts any stable-id in the
`kpi.<slug>@v<semver>` / `kri.<slug>@v<semver>` namespace.

## Artifact shape — pointer

Authoritative shape:
[`schemas/evidence/effectiveness.schema.json`](../../../schemas/evidence/effectiveness.schema.json).

At a glance, each snapshot carries:

- `artifact_id` — deterministic SHA-256 of
  `<workflow_id>|<execution_id>|<compile_target>|<metric_ref>|<subject_version.value>`.
- `workflow_id` — lower-snake-case workflow stable-id from
  `content/playbooks/<workflow>/`.
- `execution_id` — per-execution id issued by the compile target's
  runtime.
- `compile_target` — one of `n8n`, `temporal`, `langgraph`.
- `regulation_refs[]` — pin to every regulatory obligation the
  snapshot satisfies (typically the NIS2 Article 21(2)(f) atom).
- `control_refs[]` — control stable-ids attested by this snapshot
  (typically `control.control_effectiveness_test@v1` plus the
  risk-management control under measurement).
- `metric_ref` — `kpi.<slug>@v<semver>` or `kri.<slug>@v<semver>` the
  snapshot measures.
- `subject_version` — `{ kind: policy_version | prompt_version,
  value }`. Semver-shaped or 64-hex content-hash.
- `measurement` — `{ value, unit, direction, source_shape,
  evaluation_window?, threshold_crossed? }`. The numeric value and
  its unit/direction/source-shape pointer. The source-shape pointer
  is the public-bar-safe surface — the underlying sample payload is
  deliberately not embedded.
- `captured_at` — ISO-8601 UTC timestamp.
- `provenance` — `{ source_url, captured_at, commit_sha? }`.
- `owner` — optional role-shaped ownership pointer.
- `retention` — optional ISO-8601 duration retention pointer.

## What this stream is NOT

To stay scoped and reviewable, this SKELETON card deliberately leaves
the following to sibling cards in the F-CP-06 wave:

- **Compiler emitters** — the shared framework-agnostic helper at
  `compilers/_shared/evidence/effectiveness.py` and the per-target
  adapters (n8n / Temporal / LangGraph) land in the CORE-FANOUT
  sibling.
- **Worked example** — an end-to-end snapshot for one shipped workflow
  lands in the EXAMPLE card; per-target byte-parity goldens land in
  the EXTEND-tests-goldens sibling.
- **Drift detection** — the drift-detection scaffolding (change in
  the indicator's value between successive evaluations on the same
  subject version) lands in the EXTEND-drift sibling, mirroring the
  shape used by the F-CP-01 risk-analysis drift hook.
- **Metric-catalogue promotions** — wiring
  `kri.control_effectiveness@v1` and its KPI-family siblings into a
  closed catalogue-side declaration of the F-CP-06 stream's
  consumers is its own follow-up; the schema floor here just pins the
  per-snapshot artifact shape.
- **F-WF-09 auditor-bundle slot** — the auditor-bundle manifest
  gains an `effectiveness` slot once the CORE-FANOUT lands a real
  emission on a shipped workflow; until then the slot resolves to
  `null` in the bundle.

## Contributor checklist

If you are proposing a change that touches this stream:

1. The JSON Schema is the source of truth — change
   `schemas/evidence/effectiveness.schema.json` first, then update
   this README's at-a-glance summary if a field is added or removed.
2. Reuse `content/metrics/control_effectiveness.yaml` as the
   reference shape for the indicator under measurement. Do not
   duplicate the catalogue body in the snapshot — the snapshot carries
   the stable-id, the value, and the unit/direction; the catalogue
   carries the formula, the thresholds, and the regulatory anchors.
3. The `subject_version.value` pattern accepts semver and 64-hex
   content-hash only. Free-text version strings are rejected by
   design — the deterministic-id derivation pins on this string
   verbatim, so emitter conventions are reviewable at the artifact
   level.
4. The `measurement.source_shape` pointer is the public-bar-safe
   surface. The underlying sample payload is **not** embedded —
   personal data in the sample is out of scope per AGENTS.md §3.
5. Run the content-model tests:

   ```sh
   python -m pytest tests/content_model/
   ```

6. Run the forward-public hygiene linter:

   ```sh
   python -m tools.hygiene_linter --min-severity LOW
   ```

7. Follow the
   [`AGENTS.md` §3 public-bar rules](../../../AGENTS.md): no
   commercial framing, no credentials, no internal infrastructure
   references, no individual lead names.

## Status

The stream's SKELETON card landed the typed artifact shape, this
contributor README, and the NIS2 Article 21(2)(f) mapping stub.
The CORE-FANOUT shared helper, the per-target adapters, the worked
example, the per-target byte-parity goldens, the drift hook, the
metric-catalogue promotions, and the F-WF-09 auditor-bundle slot fan
out into the remaining siblings of the F-CP-06 wave.
