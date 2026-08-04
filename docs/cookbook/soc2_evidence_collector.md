# soc2_evidence_collector — cookbook walkthrough

Companion to [`content/playbooks/soc2_evidence_collector/`](../../content/playbooks/soc2_evidence_collector/README.md).
The playbook README states the design and its boundaries; this walkthrough
is the connective tissue — how the four steps behave at runtime, what each
compile target emits, and what an operator has to wire before the artifact
means anything.

Read [`soc2_crosswalk.md`](soc2_crosswalk.md) first if you have not: it
covers the crosswalk this playbook scores against, including the fact that
SOC 2 is not an EU statutory instrument and never displaces the EU mappings.

## 1. Why this matters

A SOC 2 audit begins with a period during which the operator must show that
controls were operating. Most of the evidence for that period already exists
in the operator's stack — access reviews, vulnerability closure records,
onboarding and offboarding trails — but it exists scattered across the
systems that produced it, and assembling it by hand at audit time is where
readiness assessments go wrong. Evidence gets reconstructed from memory,
gaps get discovered late, and the assembled picture is not reproducible.

This playbook aggregates evidence other playbooks have **already emitted**
into one dated document, scored per criterion. It collects nothing new. If a
criterion has no evidence behind it, the answer is `uncovered`, not a fresh
scan — the point is to report the operator's evidentiary position honestly,
including where it is empty.

Two things it deliberately is not:

- **Not an audit opinion.** A SOC 2 report is issued by a licensed
  practitioner after their own testing. The emitted document carries an
  explicit `disclaimer` field and a `document_kind` of
  `soc2_readiness_input` so it cannot be mistaken for one out of context.
- **Not a compliance score.** There is no percentage anywhere in the
  output. Section 6 explains why that is a design constraint rather than an
  omission.

## 2. When to run it

On the operator's own assessment cadence — this playbook has no alert
trigger and no schedule baked in. Typical points:

- ahead of an audit window opening, to find gaps while there is still time
  to close them;
- at a fixed interval during the observation period, so slippage shows up
  as a trend rather than a surprise;
- after a material change to the control environment, where the question is
  which criteria lost their supporting evidence.

The run is pure and replayable, so re-running over the same inputs is free
and yields a byte-identical document. That is what makes a fixed cadence
practical rather than expensive.

## 3. Source of truth

| Concern | Lives at |
|---|---|
| The criteria set | `content/mappings/soc2/` — passed in at runtime, never hard-coded |
| Criterion ref vocabulary | `soc2:` prefix, e.g. `soc2:cc6-1-logical-access-controls` |
| The playbook artifact | `content/playbooks/soc2_evidence_collector/playbook.cacao.json` |
| Deterministic bodies | `content/playbooks/soc2_evidence_collector/primitives/` |
| Emitted examples | `examples/{n8n,temporal,langgraph}/soc2_evidence_collector/` |
| Indicators | `content/metrics/soc2_evidence_ref_resolution_rate.yaml`, `content/metrics/soc2_unsupported_criteria_count.yaml` |

The criteria are **data, not a constant**. Adding an entry to
`content/mappings/soc2/` means it is scored on the next run with no change
to this playbook — and equally, this playbook can never claim coverage of a
criterion the repo does not carry. Today that is **53 criteria** across all
five Trust Services categories: 33 security (CC1.1 through CC9.2), 10
privacy, 5 processing integrity, 3 availability, 2 confidentiality.

## 4. CACAO topology

Four action steps, all bound, in a straight line:

```
start
  → collect criteria atoms          (criteria.collect_criteria_atoms)
  → map evidence to criteria        (mapping.map_evidence_to_criteria)
  → score per-criterion coverage    (scoring.score_criterion_coverage)
  → report readiness attestation    (attestation.build_readiness_attestation)
end
```

No conditionals, no parallel branches, no human step. Each step's verdict is
the next step's input, and every one of them is a frozen dataclass — so the
whole run is a pure function of `__crosswalk_entries__`, `__evidence_refs__`
and the window. `compile_targets` declares all three targets.

## 5. Playbook variables

Operator-supplied (`external: true`):

| Variable | Supplies |
|---|---|
| `__crosswalk_entries__` | the criteria set to score against |
| `__evidence_refs__` | the evidence references to aggregate, as emitted by other playbooks |
| `__assessment_window__` | the period the attestation covers |
| `__owner_role__` | the role accountable for the assessment, recorded in `provenance` |
| `__captured_at__` | the collection instant |
| `__workflow_id__`, `__execution_id__` | the runtime's own identifiers |

Internal (`external: false`) — each step's verdict: `__criteria_atoms__`,
`__criteria_mapping__`, `__coverage_scoring__`, `__attestation_id__`.

`__captured_at__` is **supplied, not read from a clock**. That is the single
decision that makes a run replayable: a primitive that called
`datetime.now()` would produce a different document on every invocation and
the byte-parity tests in section 10 could not exist. `__attestation_id__` is
derived from the window and the aggregated artifact ids by
`attestation.derive_attestation_id`, so re-running over identical inputs
yields an identical id rather than a fresh document each time.

## 6. Why coverage is three-valued

Every SOC 2 entry in the crosswalk currently carries `status: draft`. A
draft crosswalk entry is a stated intent to map, not an audit trail. So
`scoring.score_criterion_coverage` scores each criterion as one of:

| State | Meaning |
|---|---|
| `covered` | supporting evidence exists **and** the crosswalk entry is not draft |
| `draft_backed` | supporting evidence exists, crosswalk entry still draft |
| `uncovered` | no supporting evidence |

Collapsing `draft_backed` into `covered` would be the single most misleading
thing this playbook could do, and a percentage invites exactly that
collapse. *"87% SOC 2 compliant"* is not defensible; *"41 of 53 criteria
have evidence, all of it against draft mappings"* is. So the rollup carries
counts per Trust Services category and never a score, and `readiness`
reports `not_ready` whenever anything is uncovered **or** draft-backed —
because an auditor asks about the gap, not the average.

There is deliberately no configuration knob to change any of this. If you
are looking for the setting, the absence is the answer.

## 7. Adapter-bound surfaces

Four things the framework will not decide for you.

### 7.1 Evidence source

`__evidence_refs__` is a mapping of criterion ref to the evidence artifacts
supporting it. Where those artifacts come from is the operator's wiring:
`iam_auditor`, `onboarding_offboarding_tracker` and
`it_security_support_agent` already emit artifacts whose ref regex accepts
`soc2:`, so the common case is routing their output here.

A reference naming a criterion the crosswalk does not carry is reported as
`unmatched` rather than dropped. The likely cause is a stale or mistyped
criterion ref in a producing playbook, and discarding it silently would hide
a broken evidence path behind an apparently clean run. That population is
what `kpi.soc2_evidence_ref_resolution_rate@v1` measures.

### 7.2 Crosswalk revision

Passed in, so the operator controls which revision a given assessment is
scored against. Pin it per assessment window and record it — the
unsupported-criteria count is only comparable across windows when the
denominator is held fixed.

### 7.3 Attestation sink

The playbook emits a document; it does not store one. There is no WORM store
in the framework, by design — the framework ships portable content, not a
runtime. Where the document lands, and whether that location is
append-only, is a deployment decision. If your audit programme needs
tamper-evidence, that is a property of the sink you choose, and
`content/metrics/audit_log_tamper_evidence_coverage.yaml` is the indicator
for it.

### 7.4 Accountable role

`__owner_role__` is recorded in `provenance` and validated against
`^[a-z][a-z0-9_-]{0,63}$`. The framework does not know your org chart; it
only insists that a named role is attached to the assessment.

## 8. Regulatory anchors

- **AICPA Trust Services Criteria (2017, as revised)** — the criteria set
  scored against, via `content/mappings/soc2/`.
- **CC4.1 / CC4.2** — monitoring of controls, and evaluation and
  communication of deficiencies. This playbook's own operation *is* a
  monitoring activity, which is why those are the criteria its
  `mappings.yaml` declares outbound. The criteria it *scores* are runtime
  data and are deliberately not declared there.

SOC 2 is **not** an EU statutory instrument. The EU mappings remain the
authoritative pointer for the statutory surface, and a `soc2` mapping block
never replaces one. See [`soc2_crosswalk.md`](soc2_crosswalk.md).

## 9. Per-target hand-off

All four steps are bound, so every target emits executable bodies rather
than stubs — the differences are in idiom, not in coverage.

### 9.1 n8n

Four Code nodes in sequence, each importing its primitive and passing the
prior verdict forward. The three-valued coverage state travels as a plain
string in the node's JSON output, so an operator adding a Switch node
downstream branches on `covered` / `draft_backed` / `uncovered` without
re-deriving anything.

### 9.2 Temporal

Four activities on one workflow. The frozen dataclasses serialise cleanly
through the data converter, and because `__captured_at__` is an input rather
than a clock read, a replayed workflow history produces the identical
attestation — the property Temporal's determinism requirement demands
anyway, satisfied here by construction rather than by a side-effect wrapper.

### 9.3 LangGraph

Four nodes over a typed state object, plus the emitted `_audit_mirror.py`
that appends one record per node transition. No LLM participates in any
step: this playbook is deterministic end to end, which is the bottom rung of
the determinism ladder and the correct rung for an evidence artifact. A
model in this path would make the document unreproducible for no gain.

## 10. Byte-parity across compile targets — the G-03 invariant

Each `examples/<target>/soc2_evidence_collector/` directory carries a
`regenerate.sh` that re-emits from the canonical artifact, and CI asserts
the committed output is byte-identical to a fresh run. So a change to
`playbook.cacao.json` that is not accompanied by a regenerate fails the
build.

This is what makes the three targets substitutable rather than merely
similar: the same four primitives, the same three-valued scoring, the same
derived attestation id. An operator can move from n8n to Temporal and
produce the same document for the same window, which is the only basis on
which a reviewer can trust either.

## 11. Indicators

Two catalogue entries, both `foundation_property: auditability`:

| Metric | Reads |
|---|---|
| `kpi.soc2_evidence_ref_resolution_rate@v1` | whether supplied evidence refs resolve to criteria the crosswalk carries — the operator's own wiring health |
| `kri.soc2_unsupported_criteria_count@v1` | how many criteria have no non-draft support — the audit gap |

They are a pair by necessity. The KPI is bounded above by wiring, not by the
control environment: a stack where every reference resolves and no evidence
sits behind any of them scores 1.00. Only the KRI makes it interpretable.
Both carry mandatory slices — unmatched refs by criterion, unsupported
criteria by state *and* by category — because in each case the scalar cannot
distinguish situations with entirely different remediation. The reasoning is
in each metric's `measurement.formula` and its committed `.viz.md`.

## 12. Playbook chain — where this sits

Downstream of everything that emits evidence. It is a **reader**: it has no
write surface, mutates nothing, and cannot affect the systems whose evidence
it aggregates. Natural producers today are `iam_auditor`,
`onboarding_offboarding_tracker` and `it_security_support_agent`.

It is a sibling of [`nis2_self_assessment`](nis2_self_assessment.md) — the
same per-clause evidence-aggregator shape pointed at a different criteria
set. If you are extending either, read both: a change to the aggregation
pattern should land in both or be justified as deliberately divergent.

## 13. What this cookbook deliberately does not cover

- **Credentials and connectivity** for the systems that produce evidence.
  Those belong to the deployment, not the content.
- **Which criteria your service organisation is in scope for.** That is a
  scoping decision made with your auditor; the playbook scores whatever
  crosswalk you hand it.
- **Whether your evidence is sufficient.** The playbook reads whether
  evidence *exists* and whether the crosswalk entry behind it is draft. Only
  a practitioner can say whether an artifact actually demonstrates the
  control operated.
- **Graduating crosswalk entries out of `draft`.** That is repo maturity
  work, tracked against the crosswalk, and no operator can close it from
  their own deployment.

## 14. References

- OASIS CACAO Security Playbooks v2.0
- AICPA Trust Services Criteria (2017, as revised)
- [`content/mappings/soc2/`](../../content/mappings/soc2/README.md) — the crosswalk, including its draft status
- [`soc2_crosswalk.md`](soc2_crosswalk.md) — the practitioner walkthrough and the EU-primacy note
- [`nis2_self_assessment.md`](nis2_self_assessment.md) — the sibling aggregator
- [`content/playbooks/soc2_evidence_collector/README.md`](../../content/playbooks/soc2_evidence_collector/README.md) — design and boundaries
