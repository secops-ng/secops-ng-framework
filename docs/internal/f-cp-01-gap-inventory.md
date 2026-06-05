# F-CP-01 — Risk-analysis stream — gap inventory

> Contributor-facing planning document. Snapshots what is on `main`
> today versus what `ROADMAP.md` requires for F-CP-01 to flip from
> **In Progress** to **Shipped**, and how the remaining work is sliced
> into independently dispatchable contributor tasks.
>
> Mirrors the structure of
> [`f-wf-01-gap-inventory.md`](f-wf-01-gap-inventory.md) and
> [`f-wf-03-gap-inventory.md`](f-wf-03-gap-inventory.md) so future
> readers can diff the cookbook entries directly.
>
> See [`ROADMAP.md`](../../ROADMAP.md#f-cp-01--risk-analysis-stream) for
> the acceptance criteria this inventory closes against, and
> [`AGENTS.md`](../../AGENTS.md) for repository conventions.

---

## 0. Layout note

ROADMAP F-CP-01 talks about `content/evidence/risk-analysis/` populated
by "at least one workflow" with policy versions and risk-analysis
outputs, and a schema documented in
`content/mappings/nis2/article-21-risk-management.md` §21(2)(a).

The on-disk layout that has actually emerged in this repository is:

```
content/mappings/nis2/article-21-2-a.yaml   # crosswalk atom (Art. 21(2)(a))
content/controls/control.risk_management_policy@v1.yaml  # OSCAL+D3FEND crosswalk
content/metrics/control_effectiveness.yaml  # KRI (residual exposure)
```

Two divergences from the ROADMAP wording:

1. The Article-21 mapping is sharded one file per sub-point
   (`article-21-2-a.yaml` … `article-21-2-j.yaml`) rather than a single
   `article-21-risk-management.md` markdown doc. The schema-documentation
   slice of F-CP-01 has to choose between (a) adopting the existing
   sharded YAML as the schema home and adding the risk-analysis-stream
   schema block to `article-21-2-a.yaml`, or (b) introducing a new
   markdown peer at the path the ROADMAP names. See § 4.
2. `content/evidence/` does not exist yet on `main`. F-CP-01 is the
   first card in the Epic CP wave, so it ships the directory plus the
   first stream's schema and contributor README. The other six CP
   streams (F-CP-02 … F-CP-07) will land sibling subdirectories under
   the same root once their own cards open.

This inventory treats `content/evidence/risk-analysis/` as the canonical
stream path and `article-21-2-a.yaml` as the schema home; a ROADMAP
wording fix is out of scope and will be picked up when F-CP-01 flips to
Shipped.

## 0.1 Dependency note — F-PT-01 status

ROADMAP marks F-PT-01 (Evidence collector) **Shipped** and F-CP-01 lists
it as a dependency. F-PT-01 originally shipped as a Temporal-Python
pattern at `patterns/evidence_collector/`; that tree was removed in the
content-first restructure (commit `a78ea7f`) when the repo dropped its
runtime layers. The artifact F-CP-01 inherits from F-PT-01 today is
therefore the **contract**, not a runtime: a declared control set
walked once per cadence, one evidence artifact per control, dedup
invariant on `control_id`, add-control mid-run extensibility,
deterministic replay. That contract is what the risk-analysis stream
schema has to express in content-model terms — typed evidence-artifact
shape, stream-level cadence metadata, per-control idempotency key.

The F-PT-01 status itself (whether to re-instate a pattern shell under
the new content model, or treat the contract as fully content-resident)
is flagged in § 4 for maintainer review; F-CP-01 work proceeds against
the contract regardless of where F-PT-01 lands.

## 1. Acceptance criteria → coverage matrix

| ROADMAP requirement | Status | Where |
|---|---|---|
| `content/evidence/risk-analysis/` populated by at least one workflow with policy versions and risk-analysis outputs | ❌ missing | Directory does not exist on `main`. No workflow on `main` writes risk-analysis evidence today. |
| Schema documented in `content/mappings/nis2/article-21-risk-management.md` §21(2)(a) | ⚠️ partial | `content/mappings/nis2/article-21-2-a.yaml` exists and links to `control.risk_management_policy@v1` + `kri.risk_register_staleness@v1`, but the evidence-stream **schema** (typed evidence-artifact shape, required fields, cadence metadata) is not declared anywhere. |
| **Evidence-artifact typed shape** | ❌ missing | No Pydantic/JSON-schema type for a risk-analysis evidence artifact. Needs: policy version (semver or content hash), risk-assessment output (residual exposure summary keyed off `kri.control_effectiveness@v1`), dated ownership, attestation cadence, captured-at timestamp, stable artifact id. |
| **Stream contributor README** | ❌ missing | No `content/evidence/risk-analysis/README.md`. The cross-stream `content/evidence/README.md` does not exist yet either (F-CP-01 ships it). |
| **OSCAL+D3FEND control crosswalk integration** | ⚠️ partial | `control.risk_management_policy@v1.yaml` ships the OSCAL (NIST 800-53 PM-9, RA-3; ISO/IEC 27001 A.5.1; NIS2 Art. 21(2)(a)) + D3FEND (D3-OAM) crosswalks. The risk-analysis stream consumes these as the control set walked per cadence, but no `evidence_collector` contract block in the control file declares the artifact shape this stream expects. |
| **KRI/KPI catalog integration** | ⚠️ partial | `kri.control_effectiveness@v1` ships the residual-exposure indicator the stream should embed in each cadence's risk-analysis output, and `kri.risk_register_staleness@v1` is referenced by `article-21-2-a.yaml` (file not present in this audit pass — needs verification or creation). No `evidence_source` field on the KRIs ties them back to the stream. |
| **NIS2 Art. 21(2)(a) crosswalk** | ✅ done | `content/mappings/nis2/article-21-2-a.yaml` shipped. |
| **NIS2 Art. 21(2)(f) effectiveness loop** | ✅ done | `content/mappings/nis2/article-21-2-f.yaml` shipped — F-CP-01 is the upstream feeder for the F-CP-06 effectiveness stream that closes this loop. |
| **DORA Art. 5–6 ICT-risk-framework crosswalk** | ⚠️ unverified | `content/mappings/dora/article-5.yaml` and `article-6.yaml` exist; whether they reference the same `control.risk_management_policy@v1` + `kri.control_effectiveness@v1` artifacts (so DORA scope reuses the NIS2 stream) needs a one-pass audit in card 1. |
| **CRA scope** | ✅ out of scope | CRA applies to product-lifecycle obligations (Annex I §1 + SBOM Annex I §2(1)); risk-analysis stream is operator-side, not product-side. Card 1 confirms no CRA mapping change is required. |
| **Continuous read cadence — periodic risk-posture re-assessment** | ❌ missing | No content-resident declaration of cadence for `control.risk_management_policy@v1`. The ROADMAP describes F-CP-01 as a **continuous** stream; the contract needs an explicit `review_cadence` field on the control (or a stream-level default with per-control override) so an operator's compile target knows when to walk. |
| **Control-effectiveness signals — per-cadence delta** | ❌ missing | Stream artifacts need to carry the delta from the previous attestation (state transitions: effective → partially_effective → ineffective → overdue) so downstream consumers (F-CP-06, executive-metrics) can compute drift without re-deriving from the artifact archive. |
| **Regulatory-baseline drift detection** | ❌ missing | No mechanism today to detect that the upstream regulatory text (NIS2 Art. 21(2)(a)) has been re-issued or that an OSCAL catalog version has bumped. Card 4 owns the drift-detection contract; the stream itself ships the metadata fields it needs (regulation version pin, captured-at, source URL hash). |
| **Workflow emitter — at least one** | ❌ missing | Which workflow emits the risk-analysis stream is undecided. Two readings: (a) the `executive-metrics` playbook (already exists, already consumes KRIs) takes on the cadence walker; (b) a new dedicated `risk-posture-review` playbook is added under `content/playbooks/`. See § 4. |
| **Tests — stream schema guard** | ❌ missing | No content-model test guards the risk-analysis-stream evidence-artifact shape today. |
| **Tests — crosswalk integrity** | ❌ missing | No test asserts that every control referenced by the stream is reachable from the NIS2 + DORA mappings (and vice-versa). |
| **Hygiene linter clean on all artifacts** | ⚠️ pending | New files in this PR must pass `python -m tools.hygiene_linter --min-severity LOW`. |
| **Cookbook entry / contributor doc** | ❌ missing | No `docs/cookbook/risk-analysis-stream.md`; only workflow cookbooks exist under `docs/cookbook/`. May or may not be required for an Epic CP stream — see § 4. |
| **F-PT-01 dependency** | ⚠️ contract-only | Evidence-collector **pattern** was removed in the content-first restructure (commit `a78ea7f`). F-CP-01 inherits the F-PT-01 **contract** (cadence walk, per-control artifact, dedup invariant, add-control extensibility, deterministic replay) and expresses it in content-model terms. See § 0.1 and § 4. |

## 2. Stream schema × artifact inventory

The risk-analysis stream emits one evidence artifact per `(control, cadence)`
pair. Every artifact is identified by a stable id derived from
`(control_stable_id, captured_at_iso8601)`. Per-artifact field coverage:

| Field | Required | Status | Source / contract |
|---|---|---|---|
| `artifact_id` | yes | ❌ missing | Deterministic hash of `(control_stable_id, captured_at)`. |
| `stream` | yes | ❌ missing | Literal `risk-analysis`. |
| `control_ref` | yes | ⚠️ shape only | Stable id reference to `content/controls/control.<name>@vN.yaml`. Today reachable as a string ref; the typed validator is not written. |
| `regulation_refs[]` | yes | ❌ missing | Pin to the upstream regulation entries (`nis2:art-21-2-a`, `dora:art-5`, …) so a regulator can re-derive the obligation chain from the artifact alone. |
| `policy_version` | yes | ❌ missing | Semver or content hash of the operator's policy document. |
| `attestation_state` | yes | ⚠️ partial | One of `effective / partially_effective / ineffective / overdue` — vocabulary already declared in `kri.control_effectiveness@v1`, but not promoted to a typed enum used by the stream. |
| `attestation_state_delta` | no | ❌ missing | Transition from previous artifact in the same `control_ref` series. Required by F-CP-06; optional on the very first emission. |
| `risk_analysis_output` | yes | ❌ missing | Free-form structured block — residual-exposure rationale, scoped scenarios, owner. Free-text fields use DSPy signatures per the F-WF-01/F-WF-03 precedent; the deterministic state fields stay code. |
| `owner` | yes | ❌ missing | Dated ownership pointer (NIS2 Art. 21(2)(a) explicit requirement: "dated ownership"). |
| `review_cadence` | yes | ❌ missing | Cadence the artifact was produced under (cron expression or ISO-8601 duration). |
| `captured_at` | yes | ❌ missing | ISO-8601 UTC timestamp. |
| `provenance` | yes | ❌ missing | `{ source_url, captured_at, commit_sha }` mirror of the pattern used in `content/controls/`. |
| `baseline_drift` | no | ❌ missing | Optional signal — set when the regulation version or OSCAL catalog version changed since the previous artifact. Consumed by card 4 (drift detection). |

That is 13 fields across the artifact contract, of which 0 are typed
today.

## 3. Decomposition strategy

Grouping per-deliverable rather than per-(field × consumer), matching
the shape F-WF-01 and F-WF-03 used. Schema first, then the workflow
emitter that produces conformant artifacts, then drift detection and
tests fan out from a stable schema.

### 3.1 Sibling cards to spawn

All cards land as **siblings** of this gap-inventory card (no parent
edge back to it) so they sit flat on the board. Cross-card
dependencies are expressed via `parents=[…]` between siblings so the
dispatcher only promotes cards whose upstreams are done.

| # | Card | Parents (other siblings) | Public-bar |
|---|---|---|---|
| 1 | F-CP-01 SCHEMA — ship `content/evidence/risk-analysis/README.md` + the typed evidence-artifact schema (JSON Schema or Pydantic source under `schemas/`), promote the `attestation_state` enum from `kri.control_effectiveness@v1`, declare `review_cadence` on `control.risk_management_policy@v1`, and add the schema-block / link from `content/mappings/nis2/article-21-2-a.yaml` (and the DORA peers) | — | yes |
| 2 | F-CP-01 STREAM-ROOT — ship the cross-stream `content/evidence/README.md` index that names all seven CP streams (F-CP-01..F-CP-07) with one-line summaries and the contributor-checklist that mirrors `patterns/README.md`'s shape | 1 | yes |
| 3 | F-CP-01 EMITTER — wire the chosen workflow (see § 4 q.1) to emit conformant risk-analysis artifacts: walk `control.risk_management_policy@v1`, write one artifact per cadence per target (n8n / Temporal / LangGraph), include `attestation_state_delta` once a prior artifact exists | 1 | yes |
| 4 | F-CP-01 DRIFT — regulatory-baseline drift-detection contract: store regulation-version + OSCAL-catalog-version pins on each artifact, set `baseline_drift` when either pin changes, document the operator-facing alert hook | 1 | yes |
| 5 | F-CP-01 KPI-WIRE — wire `kri.control_effectiveness@v1` + (if shipped) `kri.risk_register_staleness@v1` to declare the stream as their `evidence_source` so downstream metric dashboards know which stream to read | 1 | yes |
| 6 | F-CP-01 TESTS-SCHEMA — content-model test guarding the evidence-artifact shape (golden fixture + JSON Schema validation) | 1 | yes |
| 7 | F-CP-01 TESTS-CROSSWALK — integrity test asserting every control referenced by the stream is reachable from NIS2 Art. 21(2)(a) + DORA Art. 5–6, and vice-versa | 1, 5 | yes |
| 8 | F-CP-01 TESTS-EMITTER — per-target byte-parity golden test for the chosen emitter's risk-analysis output | 3 | yes |
| 9 | F-CP-01 DOCS — contributor walkthrough under `docs/cookbook/risk-analysis-stream.md` (if § 4 q.4 lands "yes"); else README polish on the stream + cross-stream READMEs | 1, 2, 3 | yes |
| 10 | F-CP-01 CLOSEOUT — ROADMAP.md status flip In Progress → Shipped + decisions log update | 1–9 | yes |

Cards 2/3/4/5 fan out from card 1; tests fan in on 1/3/5; the closeout
card fans in on everything. Each PR is reviewed against the public-bar
before merge, following the same cadence used for F-WF-01 and F-WF-03.

## 4. Open questions for maintainers

1. **Workflow emitter — which one.** F-CP-01 needs at least one
   workflow to walk `control.risk_management_policy@v1` on a cadence
   and emit conformant artifacts. Two readings: (a) extend the existing
   `content/playbooks/executive-metrics/` playbook, which already
   consumes KRIs and runs on a cadence; (b) add a dedicated
   `content/playbooks/risk-posture-review/` playbook. Card 3 needs a
   one-line direction. Recommendation is (a) for the v1 stream — the
   executive-metrics playbook is the natural cadence walker — with a
   note that a dedicated playbook is the right home if the stream
   expands to walk dozens of controls.
2. **Schema home — sharded YAML vs new markdown peer.** ROADMAP names
   `content/mappings/nis2/article-21-risk-management.md` as the schema
   doc. The actual on-disk layout is sharded
   `article-21-2-{a..j}.yaml`. Two readings: (a) adopt the sharded YAML
   as the schema home and add an `evidence_stream_schema:` block to
   `article-21-2-a.yaml`; (b) introduce a new markdown peer at the path
   ROADMAP names and link to it from the YAML. Recommendation is (a):
   single source of truth, no duplication, no parallel maintenance.
3. **`attestation_state` enum location.** The vocabulary lives in
   `kri.control_effectiveness@v1` today. Promote to a shared schema
   reference (e.g. `schemas/attestation_state.json`) so the stream
   artifact, the KRI, and the F-CP-06 effectiveness stream all import
   the same enum? Card 1 needs a one-line direction.
4. **Cookbook walkthrough — required for Epic CP streams?** F-WF
   workflows ship a cookbook walkthrough doc. Epic CP streams are
   structural, not workflow-shaped; whether they get their own
   cookbook entry, or document themselves through the cross-stream
   `content/evidence/README.md` + per-stream READMEs, is a maintainer
   call. Card 9 picks up whichever lands.
5. **F-PT-01 status reconciliation.** The original F-PT-01
   Temporal-Python pattern (`patterns/evidence_collector/`) was removed
   in the content-first restructure. ROADMAP still marks F-PT-01
   **Shipped** with `patterns/evidence_collector/` as the acceptance
   criterion. Options: (a) re-instate F-PT-01 as a content-model
   pattern (declared evidence-collector contract under
   `content/_shared/` or similar) and update ROADMAP accordingly; (b)
   amend the F-PT-01 acceptance criteria to say "contract resident in
   the CP stream schemas" and treat F-CP-01 as the first instantiation;
   (c) leave the ROADMAP wording as historical, on the understanding
   that all future F-PT cards land as content-model patterns. This is
   structural; flagged for maintainer review and does not block F-CP-01
   work, which proceeds against the contract regardless.
6. **DORA crosswalk reuse.** Card 1 audits whether
   `content/mappings/dora/article-5.yaml` and `article-6.yaml` already
   reference `control.risk_management_policy@v1` + `kri.control_effectiveness@v1`.
   If yes, the stream is shared across NIS2 + DORA scope and no new
   mapping work is required; if no, the audit produces a fixup line
   item that can either fold into card 1 or split off as card 5b.

## 5. Out of scope for this card

- ROADMAP.md acceptance-criteria edits (the status flip flows from
  card 10 when the wave is shipped). The `Proposed → In Progress` flip
  on the status field itself ships in this PR.
- Any actual schema / emitter / drift-detection work — that is cards
  1–4.
- The other six CP streams (F-CP-02 … F-CP-07). The cross-stream
  `content/evidence/README.md` index that card 2 ships names them but
  does not flesh them out.
- F-PT-01 status reconciliation — separate maintainer decision, see
  § 4 question 5.
