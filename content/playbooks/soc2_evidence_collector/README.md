# soc2_evidence_collector

## Overview

CACAO v2 playbook that aggregates the evidence an operator's other playbooks
already emit into a dated **SOC 2 readiness attestation**, scored against the
AICPA Trust Services Criteria crosswalk under
[`content/mappings/soc2/`](../../mappings/soc2/README.md). It is triggered on the
operator's own assessment cadence — not by an alert — and takes two inputs: the
crosswalk entries to score against (`__crosswalk_entries__`) and the evidence
references other playbooks have already produced (`__evidence_refs__`) for a
stated `__assessment_window__`. It produces one artifact: a
`soc2_readiness_input` document carrying a per-criterion coverage verdict, counts
rolled up per Trust Services category, and the ids of every evidence artifact it
aggregated.

Four steps: collect criteria atoms → map evidence to criteria → score
per-criterion coverage → report readiness attestation. It is the same shape as
[`nis2_self_assessment`](../nis2_self_assessment/README.md), the framework's
other per-clause evidence aggregator, pointed at a different criteria set.

## What it does not do

Three boundaries, stated here because each is the kind a reader might otherwise
assume the other way:

- **It collects no new telemetry.** Every input is an evidence reference another
  playbook already produced. If a criterion has no evidence, the answer is
  "uncovered", not a new scan.
- **It asserts no audit opinion.** A SOC 2 report is issued by a licensed
  practitioner after their own testing. The emitted document carries an explicit
  `disclaimer` field and a `document_kind` of `soc2_readiness_input` so it cannot
  be mistaken for one out of context.
- **It emits no new evidence stream.** The seven streams under
  `content/evidence/` are each an F-CP ROADMAP card with a typed schema; minting
  an eighth here would pre-empt that epic. The attestation is a *report over*
  those streams, citing the artifact ids it aggregated. Promotion to a stream is
  additive EXTEND work — the document already carries `schema_version`, a
  deterministic `attestation_id` and a `provenance` block in the house shape.

## Why coverage is three-valued, not a percentage

Every SOC 2 entry in the crosswalk is currently `status: draft` (see
[`content/mappings/soc2/README.md`](../../mappings/soc2/README.md)). A draft
crosswalk entry is a stated intent to map, not an audit trail. So a criterion
scores one of:

| State | Meaning |
|---|---|
| `covered` | supporting evidence exists **and** the crosswalk entry is not draft |
| `draft_backed` | supporting evidence exists, crosswalk entry still draft |
| `uncovered` | no supporting evidence |

Collapsing `draft_backed` into `covered` would be the single most misleading
thing this playbook could do, and a percentage invites exactly that misreading:
*"87% SOC 2 compliant"* is not defensible, whereas *"41 of 53 criteria have
evidence, all of it against draft mappings"* is. The rollup therefore carries
counts per Trust Services category and never a score.

`readiness` summarises honestly — `not_ready` whenever anything is uncovered or
any support is draft-backed, because an auditor asks about the gap, not the
average.

## Criteria are data, not a constant

The crosswalk entries are passed in rather than hard-coded, so a criterion added
to `content/mappings/soc2/` is scored on the next run with no change here — and
this playbook can never claim coverage of a criterion the repo does not carry.
Today that is **53 criteria** across all five categories: 33 security (CC1.1
through CC9.2), 10 privacy, 5 processing integrity, 3 availability, 2
confidentiality.

An evidence reference naming a criterion the crosswalk does not carry is
reported as `unmatched` rather than dropped — the likely cause is a stale or
typo'd criterion ref in a producing playbook, and silently discarding it would
hide that behind an apparently clean run.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.soc2_evidence_collector@v1`).
- `mappings.yaml` — outbound cross-references. The `soc2` block pins the
  criteria this playbook's own operation discharges (CC4.1 / CC4.2 monitoring);
  the criteria it *scores* are runtime data, not declared here.
- `primitives/` — the four deterministic bodies. Pure, offline, replay-safe: no
  clock reads, no network, no LLM.

## Regulatory anchors

- **AICPA Trust Services Criteria (2017, as revised)** — the criteria set scored
  against, via `content/mappings/soc2/`.
- **CC4.1 / CC4.2** — monitoring of controls and evaluation/communication of
  deficiencies. This playbook's own operation is a monitoring activity, which is
  why those are the criteria it declares outbound.

Note per [`docs/cookbook/soc2_crosswalk.md`](../../../docs/cookbook/soc2_crosswalk.md):
SOC 2 is **not** an EU statutory instrument. The EU mappings remain the
authoritative pointer for the statutory surface, and a `soc2` mapping block never
replaces one.

## How to compile

`x_secops_ng.compile_targets` declares all three targets. Emitted artifacts:

- n8n — [`examples/n8n/soc2_evidence_collector/`](../../../examples/n8n/soc2_evidence_collector/)
- Temporal — [`examples/temporal/soc2_evidence_collector/`](../../../examples/temporal/soc2_evidence_collector/)
- LangGraph — [`examples/langgraph/soc2_evidence_collector/`](../../../examples/langgraph/soc2_evidence_collector/)

Each directory carries a `regenerate.sh` that re-emits from the canonical
artifact; the goldens are byte-parity checked in CI, so a change here must be
followed by a regenerate in the same commit.

## Operator customisation

Everything an operator supplies is a CACAO variable marked `external: true` —
there are no thresholds or channel names baked into the primitives:

| Variable | What the operator supplies |
|---|---|
| `__crosswalk_entries__` | the criteria set to score against. Passed in, so a criterion added to `content/mappings/soc2/` is scored on the next run with no change here |
| `__evidence_refs__` | the evidence references to aggregate, as emitted by the operator's other playbooks |
| `__assessment_window__` | the period the attestation covers |
| `__owner_role__` | the role accountable for the assessment, recorded in `provenance` |
| `__captured_at__` | the collection instant. Supplied rather than read from a clock, which is what makes a run replayable |
| `__workflow_id__`, `__execution_id__` | the runtime's own identifiers, recorded in `provenance` |

The remaining variables (`__criteria_atoms__`, `__criteria_mapping__`,
`__coverage_scoring__`, `__attestation_id__`) are internal — each step's verdict,
written by a primitive and read by the next. `__attestation_id__` is derived
deterministically from the window and the aggregated artifact ids, so re-running
over identical inputs yields an identical id rather than a fresh document.

There is deliberately **no** knob for collapsing `draft_backed` into `covered`,
and no percentage output to configure. See the section above for why.

## Sources

- OASIS CACAO v2.0 specification
- AICPA Trust Services Criteria (2017, as revised)
- `content/mappings/soc2/` — the crosswalk, including its draft status
- `docs/cookbook/soc2_crosswalk.md` — the practitioner walkthrough and the
  EU-primacy note
