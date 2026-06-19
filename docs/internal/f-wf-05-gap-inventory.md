# F-WF-05 — Incident management — gap inventory

> Contributor-facing planning document. Snapshots what is on `main`
> today versus what `ROADMAP.md` requires for F-WF-05 to flip from
> **In Progress** to **Shipped**, and how the work is sliced into
> independently dispatchable contributor tasks.
>
> Mirrors the structure of
> [`f-wf-03-gap-inventory.md`](f-wf-03-gap-inventory.md) and
> [`f-wf-01-gap-inventory.md`](f-wf-01-gap-inventory.md) so future
> readers can diff the three cookbook entries directly.
>
> See [`ROADMAP.md`](../../ROADMAP.md#f-wf-05--incident-management) for
> the acceptance criteria this inventory closes against, and
> [`AGENTS.md`](../../AGENTS.md) for repository conventions.

---

## 0. Layout note

ROADMAP F-WF-05 talks about an incident_management workflow. F-WF-05 is
**greenfield** — unlike F-WF-01 (vuln_intake) and F-WF-03 (alert_triage),
the canonical CACAO source does not yet exist on `main`. There is no
`content/playbooks/incident_management/`, no
`examples/{n8n,temporal,langgraph}/incident_management/`, and no
per-workflow tests. The expected on-disk layout, mirroring every other
cookbook workflow, is

```
content/playbooks/incident_management/                  # canonical CACAO source + primitives + payloads
examples/{n8n,temporal,langgraph}/incident_management/  # compiled worked examples
tests/examples/incident_management/                     # per-target byte-parity guards
tests/examples/test_{n8n,langgraph}_incident_management.py
tests/content_model/test_incident_management_source.py
```

A ROADMAP wording fix (`workflows/incident_management/` →
`incident_management`) is out of scope and will be picked up when
F-WF-05 flips to Shipped. This inventory treats `incident_management` as
the canonical name throughout.

The two named upstream dependencies are both Shipped: F-CR-04 supplies
the `AuditTrail` mirror contract that every CORE action will bind
against, and F-PT-02 supplies the `incident_timeline` pattern that the
three-stage state machine will consume to produce the regulator-shaped
JSON artefact. See § 4 for an open question on the on-disk presence of
the F-PT-02 pattern module.

## 1. Acceptance criteria → coverage matrix

| ROADMAP requirement | Status | Where |
|---|---|---|
| **Canonical CACAO source for the workflow** | ❌ missing | No `content/playbooks/incident_management/playbook.cacao.json` (or `.cacao.yaml`) exists. The three-stage NIS2 Art-23 state machine has not been sketched as a CACAO playbook yet. |
| **Worked example — n8n** | ❌ missing | No `examples/n8n/incident_management/`. |
| **Worked example — Temporal** | ❌ missing | No `examples/temporal/incident_management/`. Temporal is the natural primary target for this workflow because the three-stage timeline is a long-running durable state machine with timer-driven escalations — see § 4. |
| **Worked example — LangGraph** | ❌ missing | No `examples/langgraph/incident_management/`. |
| **Byte-parity golden tests (drift guards)** | ❌ missing | No `tests/examples/incident_management/`, no source-shape guard. |
| **OTel spans on every node** | ❌ missing | Inherits the same per-target story as F-WF-01 / F-WF-03 once SKELETON stubs land. |
| **`AuditTrail` mirror integration** | ❌ missing | F-CR-04 contract is Shipped and stable; SKELETON stubs will bind against it the same way the alert_triage SKELETON does. |
| **NIS2 Art. 23 three-stage timeline: 24h early warning → 72h notification → 1 month final report** | ❌ missing | No state machine, no clock-tracking primitive, no per-stage submission action. The regulated clock signals are already declared by `content/controls/control.incident_timeline_signals@v1.yaml` and the obligation text per stage already lives in `content/mappings/nis2/article-23.yaml` — both are inputs to CORE-PRIM, not gaps in their own right. |
| **State transitions are deterministic and replay-tested** | ❌ missing | Requires (a) the state machine encoded in the CACAO source, (b) a deterministic transition primitive, (c) a replay test in `tests/examples/incident_management/`. |
| **Machine-readable timeline JSON consumable by F-CP-02** | ❌ missing | F-PT-02 produces a NIS2-Art-23-shaped JSON timeline; the workflow needs to wire its three submission actions through the pattern so the emitted artefact lands at a configurable `content/evidence/incidents/<workflow-id>/timeline.json` location (consumed by F-CP-02). |
| **Library code / primitives directory** | ❌ missing | No `content/playbooks/incident_management/primitives/`. Stage-clock arithmetic, the regulator-submission contract, the typed early-warning / notification / final-report payload shapes, and the DSPy signature for free-text fields all need a home. |
| **Typed payload shapes** | ❌ missing | The three regulator submissions each have a distinct typed shape (early-warning ≠ 72h notification ≠ final report). Two placement readings — see § 4. |
| **DSPy signature for free-text fields only** | ❌ missing | No DSPy import or `dspy.Signature` exists for this workflow. Free-text fields cluster on the final report (narrative, root cause, applied mitigations); the regulated decisions (stage clock, classification, cross-border flag) are deterministic code. |
| **Notification-destination configuration is operator-supplied** | ❌ missing | Sovereign-stack constraint: the framework ships no default endpoint. The destination contract belongs in the operator-facing config (CACAO `playbook_variables` vs separate YAML — see § 4) and the action body must read it through that contract. |
| **CORE action bodies** (intake, classify, early-warning submit, 72h notification submit, final-report submit, plus stage-transition actions) | ❌ missing | No action stubs exist yet because no CACAO source exists yet. SKELETON shape lands once the CACAO source is sketched. |
| **Tests — happy path** | ❌ missing | Needs golden replay test across all three targets in `tests/examples/incident_management/`. |
| **Tests — late-arrival / re-classification** | ❌ missing | Needs a test that exercises (a) a late event arriving inside an already-open stage, (b) a re-classification that promotes / demotes the incident across the 24h boundary. Both must replay byte-identical against the timeline JSON. |
| **Tests — replay** | ❌ missing | Needs the deterministic-replay test (same incident event stream twice → byte-identical timeline JSON + AuditTrail). |
| **Tests — F-CP-02 consumability** | ❌ missing | The emitted timeline JSON must validate against whatever shape F-CP-02 declares. F-CP-02 status (see § 4) determines whether this lands inside F-WF-05 or moves to F-CP-02's closeout. |
| **GDPR data-flow `data-flow-incident_management.md`** | ❌ missing | `content/mappings/gdpr/` today carries only a `README.md` placeholder. The structural decision raised by F-WF-03 (per-workflow doc vs single per-mapping schema) is still open; F-WF-05 inherits it. See § 4. |
| **Cookbook entry + walkthrough docs** | ❌ missing | No `docs/cookbook/incident_management.md`. |
| **`config.yaml`** | ⚠️ pending decision | Same open question as F-WF-01 and F-WF-03: is the CACAO `playbook_variables` block the operator-facing config, or is a separate YAML expected? F-WF-02 (Shipped) does not ship a per-workflow YAML; precedent points at the CACAO block. The operator-supplied notification destination contract sharpens the question for F-WF-05. See § 4. |
| **F-CR-04 dependency** | ✅ unblocked | Shipped. The `AuditTrail` mirror contract that CORE actions will bind against is stable. |
| **F-PT-02 dependency** | ⚠️ flagged | ROADMAP marks F-PT-02 Shipped. The `incident_timeline` pattern is not currently present under `patterns/` on `main`; the whole `patterns/` tree is absent on disk despite multiple shipped pattern entries (F-PT-01..F-PT-03+) in the ROADMAP. CORE-PRIM cannot bind to a module that is not on disk. See § 4 — this is a maintainer call to make before card 1 starts. |

## 2. Proposed CACAO step shape

No source playbook exists yet, so the per-(action × target) matrix used
by F-WF-01 / F-WF-03 does not apply at kickoff time. The shape the
SKELETON card will encode mirrors the NIS2 Art-23 three-stage timeline
plus the deterministic transitions between stages.

| # | CACAO step | Notes |
|---|---|---|
| 1 | `start` — `incident-mgmt-start` | trigger / entry binding per target |
| 2 | `action` — intake significant-incident signal | typed payload boundary; consumes the F-PT-02 timeline-event shape |
| 3 | `action` — classify significance (NIS2 Art. 23(3): significant?) + cross-border flag | deterministic policy; no DSPy reach |
| 4 | `if-condition` — significant? | non-significant branch → audit-only close |
| 5 | `action` — open the incident timeline (signal F-PT-02 pattern `start`) | stage clock 0 begins |
| 6 | `action` — submit 24h early warning | reads operator-configured destination; emits timeline event |
| 7 | `action` — submit 72h notification | reads operator-configured destination; emits timeline event |
| 8 | `if-condition` — final-report material complete? | branches on whether root-cause + applied mitigations are ready before 1mo |
| 9 | `action` — submit 1-month final report (DSPy free-text only for narrative / root cause / mitigations) | reads operator-configured destination; emits timeline event |
| 10 | `action` — close incident timeline (signal F-PT-02 pattern `close`) | canonical timeline JSON persisted at `content/evidence/incidents/<workflow-id>/timeline.json` |
| 11 | `end` — `incident-mgmt-end` | exit |

CACAO step IDs and exact action names are CORE-SKEL's call; the table
above documents the shape, not the wire format. The three regulator
submissions in 6 / 7 / 9 share a single regulator-submission primitive
that takes a stage-shaped payload and a destination from operator
config; the typed shape per stage is what differs.

That is **7 action bodies × 3 targets = 21 CORE bodies** for the
SKELETON → CORE wave, plus the shared primitives module and the F-PT-02
binding layer that all three targets call into.

## 3. Decomposition strategy

Two-phase wave. Phase A lands the SKELETON across all three targets so
the byte-parity drift guards are in place before any CORE body work
begins; phase B lands CORE-PRIM and the per-target wiring on top, the
same shape F-WF-03 used. Grouping per-target rather than per-(action ×
target) for the same reasons F-WF-01 and F-WF-03 documented: 21
trivially-coupled per-(action × target) PRs would be 21 review cycles
for what is one mechanical sweep per target.

The F-PT-02 binding question (see § 4) gates CORE-PRIM but not the
SKELETON: SKELETON stubs can `raise NotImplementedError(...)` against a
named contract without that contract being on disk yet.

### 3.1 Sibling cards to spawn

All cards land as **siblings** of this gap-inventory card (no parent
edge back to it) so they sit flat on the board. Cross-card dependencies
are expressed via `parents=[…]` between siblings so the dispatcher only
promotes cards whose upstreams are done.

| # | Card | Parents (other siblings) | Public-bar |
|---|---|---|---|
| 1 | F-WF-05 CORE-SKEL-SRC — sketch the canonical CACAO source under `content/playbooks/incident_management/playbook.cacao.json` per the step shape in § 2; add `README.md`; add `content/playbooks/incident_management/__init__.py`; source-shape guard under `tests/content_model/test_incident_management_source.py` | — | yes |
| 2 | F-WF-05 CORE-SKEL-N8N — SKELETON `examples/n8n/incident_management/workflow.n8n.json` (8 stub action bodies + 1 if-condition cell + the trigger / end cells); regen via `regenerate.sh`; byte-parity drift guard under `tests/examples/test_n8n_incident_management.py` | 1 | yes |
| 3 | F-WF-05 CORE-SKEL-TMPRL — SKELETON `examples/temporal/incident_management/workflow.temporal.py` (span + AuditTrail mirror + NotImplementedError per action); regen; byte-parity drift guard under `tests/examples/incident_management/test_temporal_workflow.py` | 1 | yes |
| 4 | F-WF-05 CORE-SKEL-LG — SKELETON `examples/langgraph/incident_management/{graph_spec.json,state_bindings.py}` (span + AuditTrail mirror + NotImplementedError per action); regen; byte-parity drift guard under `tests/examples/test_langgraph_incident_management.py` | 1 | yes |
| 5 | F-WF-05 CORE-PRIM — shared primitives under `content/playbooks/incident_management/primitives/` (stage-clock arithmetic, deterministic significance + cross-border classification policy, regulator-submission contract with operator-configured destination, F-PT-02 binding layer, DSPy signature for free-text fields on the final report) | 1 | yes |
| 6 | F-WF-05 CORE-WIRE-N8N — wire 7 CORE action bodies in `examples/n8n/incident_management/workflow.n8n.json` against the primitives contract; regen; golden byte-parity green; bring the n8n audit-mirror node uplift to parity with the F-CR-04 cookbook | 2, 5 | yes |
| 7 | F-WF-05 CORE-WIRE-TMPRL — wire 7 CORE action bodies in `examples/temporal/incident_management/workflow.temporal.py` against the primitives contract; regen; golden byte-parity green | 3, 5 | yes |
| 8 | F-WF-05 CORE-WIRE-LG — wire 7 CORE action bodies in `examples/langgraph/incident_management/state_bindings.py` against the primitives contract; regen; golden byte-parity green | 4, 5 | yes |
| 9 | F-WF-05 CORE-MECH-GDPR — ship `content/mappings/gdpr/data-flow-incident_management.md` to satisfy the sovereign-stack constraint, plus a content-model test that pins the incident_management payload shapes against that doc | 5 | yes |
| 10 | F-WF-05 EXTEND-tests-happy — happy-path golden replay test across all three targets in `tests/examples/incident_management/` | 6, 7, 8 | yes |
| 11 | F-WF-05 EXTEND-tests-late-arrival — late-event / re-classification test across all three targets | 6, 7, 8 | yes |
| 12 | F-WF-05 EXTEND-tests-replay — deterministic-replay test (same event stream twice → byte-identical timeline JSON + AuditTrail) across all three targets | 6, 7, 8 | yes |
| 13 | F-WF-05 EXTEND-docs-cookbook — cookbook walkthrough under `docs/cookbook/incident_management.md` + worked-example README polish across all three targets | 6, 7, 8 | yes |
| 14 | F-WF-05 EXTEND-config — answer the `config.yaml` question (CACAO `playbook_variables` vs separate operator YAML, sharpened by the operator-supplied notification destination contract) and ship whichever is approved | 5 | yes |
| 15 | F-WF-05 CLOSEOUT — ROADMAP.md status flip In Progress → Shipped + decisions log update | 1–14 | yes |

Cards 2/3/4 fan out from card 1; CORE-PRIM (5) fans out from 1; CORE-WIRE
cards (6/7/8) fan in on the matching SKELETON card and on CORE-PRIM;
tests/docs fan in on 6/7/8; the closeout card fans in on everything.
Each PR is reviewed against the public-bar before merge, following the
same cadence used for F-WF-01 and F-WF-03.

## 4. Open questions for maintainers

1. **F-PT-02 on-disk presence.** ROADMAP F-PT-02 is marked Shipped but
   the `patterns/` tree is absent on `main` today (no
   `patterns/incident_timeline/`, no `patterns/evidence_collector/`,
   no `patterns/README.md`). Two readings: (a) the pattern modules were
   shipped under a different path that this inventory has not located
   and CORE-PRIM binds to that path; (b) the pattern modules are not on
   disk and the F-PT-02 binding becomes a precondition card before
   CORE-PRIM can start. Card 5 needs a one-line direction. This is the
   single largest unknown gating phase B.
2. **F-CP-02 readiness.** ROADMAP F-WF-05 acceptance says the timeline
   JSON is consumable by F-CP-02. F-CP-02's status and shape determine
   whether the consumability test lands inside F-WF-05 (card 10/12) or
   sits behind F-CP-02. Recommendation is the test lands here with a
   `pytest.mark.skipif` if F-CP-02 has not pinned its shape yet, so the
   harness is in place when F-CP-02 lands.
3. **Primitives directory location.** Mirror of the F-WF-03 open
   question. F-WF-05 is greenfield, so the subdirectory layout
   (`content/playbooks/incident_management/primitives/`) is the
   uncontested default — but the same call about whether the source
   playbook lives flat (`incident_management.cacao.yaml`) or under a
   subdirectory (`incident_management/playbook.cacao.json`) needs a
   one-line direction for card 1. Recommendation: subdirectory, both
   because every other multi-artifact playbook
   (ransomware_containment, post_incident_review, …) ships that way
   and because the workflow needs the subdirectory anyway for
   primitives, payloads, and the regulator-submission contract.
4. **GDPR data-flow doc as a workflow-local artifact.** Mirror of the
   F-WF-03 open question — the structural decision (per-workflow doc
   vs single per-mapping schema) is still open. Card 9 owns shipping
   the first one if (a) is chosen; under (b) card 9 instead extends
   the per-mapping schema. Decision affects future workflows.
5. **`config.yaml` semantics + notification destinations.** Mirror of
   the F-WF-01 / F-WF-03 open question, sharpened. F-WF-05 ships no
   default notification endpoint (sovereign-stack constraint); the
   operator-supplied destination contract has to live somewhere. The
   cleanest reading is: CACAO `playbook_variables` declares the
   destination contract surface (key shape, required vs optional, env
   indirection), and the operator wires concrete endpoints at the
   compile target's config layer (n8n credential, Temporal worker env,
   LangGraph runtime config). Card 14 needs that confirmed.
6. **DSPy reach.** Mirror of the F-WF-01 / F-WF-03 open question.
   F-WF-05 reads as: regulated decisions (stage clock arithmetic,
   significance / cross-border classification, submission dispatch)
   are deterministic code. DSPy covers free-text fields on the final
   report only (narrative, root cause text, applied mitigations
   summary). Confirm before card 5 starts; answer should be consistent
   across all three workflow gap inventories.
7. **Typed payload shapes — placement.** Three regulator submissions
   have three distinct typed shapes plus the event-intake shape.
   Mirror of the F-WF-03 open question about placement under
   `content/telemetry/` vs `content/playbooks/incident_management/payloads/`.
   Card 1 / card 5 need a one-line direction.

## 5. Out of scope for this card

- ROADMAP.md acceptance-criteria edits (the status flip flows from card
  15 when the wave is shipped). The `Proposed → In Progress` flip on
  the status field itself ships in this PR.
- Any actual SKELETON or CORE body work — that is cards 1–8.
- F-PT-02 pattern module rehydration / relocation — depends on the
  answer to § 4 question 1; if it lands, it ships as a precondition
  card before phase B, not inside this kickoff.
- F-CP-02 design — separate roadmap item.
- GDPR data-flow doc design — card 9, gated on § 4 question 4.
