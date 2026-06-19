# F-WF-03 — Alert triage — gap inventory

> Contributor-facing planning document. Snapshots what is on `main`
> today versus what `ROADMAP.md` requires for F-WF-03 to flip from
> **In Progress** to **Shipped**, and how the remaining work is sliced
> into independently dispatchable contributor tasks.
>
> Mirrors the structure of
> [`f-wf-01-gap-inventory.md`](f-wf-01-gap-inventory.md) so future
> readers can diff the two cookbook entries directly.
>
> See [`ROADMAP.md`](../../ROADMAP.md#f-wf-03--alert-triage) for the
> acceptance criteria this inventory closes against, and
> [`AGENTS.md`](../../AGENTS.md) for repository conventions.

---

## 0. Layout note

ROADMAP F-WF-03 talks about `workflows/alert_triage/`. The on-disk
layout that has actually emerged in this repository is

```
content/playbooks/alert_triage.cacao.yaml              # CACAO source of truth (flat YAML)
examples/{n8n,temporal,langgraph}/alert_triage/        # compiled worked examples
tests/examples/alert_triage/                           # per-target byte-parity guards
tests/examples/test_{n8n,langgraph}_alert_triage.py    # mirror + node-uplift guards
tests/content_model/test_alert_triage_source.py        # source-shape guard
```

The source playbook ships as a flat YAML file rather than under a
`content/playbooks/alert_triage/` subdirectory. That divergence
pre-dates this card; it is not the layout vuln_intake settled on, and
where primitives should live is one of the open questions for
maintainers (see § 4). This inventory treats `alert_triage` as the
canonical name; a ROADMAP wording fix is out of scope and will be
picked up when F-WF-03 flips to Shipped.

## 1. Acceptance criteria → coverage matrix

| ROADMAP requirement | Status | Where |
|---|---|---|
| Canonical CACAO source for the workflow | ✅ done | `content/playbooks/alert_triage.cacao.yaml` (12 steps: 1 start, 8 action, 1 if-condition, 1 switch-condition, 1 end) |
| Worked example — n8n | ✅ SKELETON | `examples/n8n/alert_triage/workflow.n8n.json` |
| Worked example — Temporal | ✅ SKELETON | `examples/temporal/alert_triage/workflow.temporal.py` |
| Worked example — LangGraph | ✅ SKELETON | `examples/langgraph/alert_triage/{graph_spec.json,state_bindings.py}` |
| Byte-parity golden tests (drift guards) | ✅ done | `tests/examples/alert_triage/test_temporal_workflow.py`, `tests/examples/test_n8n_alert_triage.py`, `tests/examples/test_langgraph_alert_triage.py`, `tests/content_model/test_alert_triage_source.py` |
| OTel spans on every node | ⚠️ partial | Temporal + LangGraph emit `_TRACER.start_as_current_span(...)` per action; n8n is a node-graph format so OTel is a runtime concern documented per node-id, not a per-node instruction in the JSON. |
| `AuditTrail` mirror integration | ⚠️ partial | Temporal + LangGraph call `AuditTrail.current().append(...)` per action (delivered by the F-CR-04 wave). n8n parity with the F-CR-04 audit-mirror node uplift is not present in the alert_triage example yet. |
| **Ingestion of typed alert payloads from at least two source shapes** | ❌ missing | The CACAO source carries `__alert_source_shape__` and the ingest action documents two shapes (push from detection pipeline, pull from a shared alert store), but no typed shape lives under `content/telemetry/` and the ingest action body is a stub in all three targets. |
| **Library code / primitives directory** | ❌ missing | No `content/playbooks/alert_triage/primitives/` (or peer location) exists. The deterministic prioritisation policy, the suppression-window helper, and the DSPy signature for free-text fields have nowhere to live yet. See § 4 for the layout question. |
| **Deterministic prioritisation policy (code)** | ❌ missing | The `classify and prioritise` action stub in all three targets `raise NotImplementedError(...)`; the policy itself has not been written. |
| **DSPy signature for free-text fields only** | ❌ missing | No `DSPy` import or `dspy.Signature` exists in the alert_triage tree. ROADMAP and FOUNDATION read together as: priority decision is code, DSPy is used only for free-text fields (analyst summary, narrative). |
| **Suppression / already-seen helper** | ❌ missing | The `if-condition` step branches on `__benign_or_seen__` and the `suppress and close` action stub references the suppression-window contract, but no helper, no canonical seen-key, and no benign-rule table exist. |
| **CORE action bodies** (ingest, enrich, suppress, classify, 4× response) | ❌ missing | All 8 action stubs in all three targets `raise NotImplementedError(...)`. |
| **Tests — happy path** | ❌ missing | The only alert_triage tests today are byte-parity drift guards plus the source-shape guard. |
| **Tests — suppression-collision** | ❌ missing | No suppression test exists because no suppression helper exists. |
| **Tests — replay** | ❌ missing | No replay test (golden replay across all three targets). |
| **Cookbook entry + walkthrough docs** | ❌ missing | No `docs/cookbook/alert_triage.md`; only `docs/cookbook/vuln_intake.md` exists today. |
| **GDPR data-flow `data-flow-alert_triage.md`** | ❌ missing | ROADMAP F-WF-03 sovereign-stack constraint: payload shapes validate as `content/mappings/gdpr/data-flow-alert_triage.md`. `content/mappings/gdpr/` today contains only a `README.md` placeholder — no per-workflow data-flow doc exists for any workflow. See § 4. |
| **`config.yaml`** | ⚠️ pending decision | Same question as F-WF-01: is the existing CACAO `playbook_variables` block the operator-facing config, or is a separate YAML expected? F-WF-02 (Shipped) does not ship a per-workflow YAML; precedent points at the CACAO block. See § 4. |
| **F-WF-01 dependency** | ✅ unblocked | ROADMAP F-WF-03 lists `Depends on: F-WF-01`. F-WF-01 shipped via the CLOSEOUT wave; the dedup primitive shape and the AuditTrail mirror contract that the alert_triage suppression and response actions inherit are now stable. |

## 2. Per-target action × body inventory

Every CACAO step shipped per target today; ✅ = SKELETON stub present
(span + AuditTrail mirror + `NotImplementedError`), ❌ = CORE body
required. n8n cells are marked ✅ where the node + Set-node uplift is
present in the workflow JSON; CORE bodies on the n8n side land as
Function-node expression bodies wired off the Set-node fields.

| CACAO step | n8n | Temporal | LangGraph |
|---|---|---|---|
| `start` — `triage-start` | ✅ trigger node | ✅ workflow entry | ✅ entry binding |
| `action--…000002` — ingest typed alert payload | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…000003` — enrich with telemetry context | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `if-condition--…000004` — already-seen or known-benign? | ✅ edge wiring only — no body required | ✅ edge wiring only | ✅ edge wiring only |
| `action--…000005` — suppress and close | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…000006` — classify and prioritise (deterministic policy) | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `switch-condition--…000007` — route on priority | ✅ edge wiring only | ✅ edge wiring only | ✅ edge wiring only |
| `action--…000008` — response: p1 severe — page and escalate | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…000009` — response: p2 high — queue for primary analyst | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…00000a` — response: p3 routine — queue for review | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…00000b` — response: p4 informational — log and close | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `end` — `triage-end` | ✅ | ✅ | ✅ |

That is **8 actions × 3 targets = 24 CORE bodies missing**, plus the
shared primitives module they will all call into.

## 3. Decomposition strategy

Grouping per-target rather than per-(action × target), matching the
shape F-CR-04 and F-WF-01 used. The eight action bodies in a single
target share the same imports, the same prioritisation-policy contract,
and one golden-regen cadence — splitting them eight ways per target
would create 24 trivially-coupled PRs and 24 review cycles for work
that is one mechanical sweep per target.

Cross-target consistency of action *semantics* (the prioritisation
policy, the suppression-window contract, the typed-payload boundary)
is enforced once in the shared primitives module (`CORE-PRIM`);
per-target cards then bind their framework idioms to those primitives.
Shared helper first, per-target wiring after.

### 3.1 Sibling cards to spawn

All cards land as **siblings** of this gap-inventory card (no parent
edge back to it) so they sit flat on the board. Cross-card
dependencies are expressed via `parents=[…]` between siblings so the
dispatcher only promotes cards whose upstreams are done.

| # | Card | Parents (other siblings) | Public-bar |
|---|---|---|---|
| 1 | F-WF-03 CORE-PRIM — shared primitives (deterministic prioritisation policy, suppression-window helper with canonical seen-key, typed-payload validators for the two source shapes, DSPy signature for free-text fields) under the agreed primitives location (see § 4) | — | yes |
| 2 | F-WF-03 CORE-N8N — wire 8 CORE action bodies in `examples/n8n/alert_triage/workflow.n8n.json` against the primitives contract; regen via `regenerate.sh`; golden byte-parity green; bring the n8n audit-mirror node uplift to parity with the F-CR-04 cookbook | 1 | yes |
| 3 | F-WF-03 CORE-TMPRL — wire 8 CORE action bodies in `examples/temporal/alert_triage/workflow.temporal.py` against the primitives contract; regen; golden byte-parity green | 1 | yes |
| 4 | F-WF-03 CORE-LG — wire 8 CORE action bodies in `examples/langgraph/alert_triage/state_bindings.py` against the primitives contract; regen; golden byte-parity green | 1 | yes |
| 5 | F-WF-03 CORE-MECH-GDPR — ship `content/mappings/gdpr/data-flow-alert_triage.md` to satisfy the sovereign-stack constraint, plus a content-model test that pins the alert_triage payload shapes against that doc | 1 | yes |
| 6 | F-WF-03 EXTEND-tests-happy — happy-path golden replay test across all three targets in `tests/examples/alert_triage/` | 2, 3, 4 | yes |
| 7 | F-WF-03 EXTEND-tests-suppress — suppression-collision test (same seen-key inside the window → single closed case across all three targets) | 2, 3, 4 | yes |
| 8 | F-WF-03 EXTEND-tests-replay — deterministic-replay test (same input twice → byte-identical AuditTrail) across all three targets | 2, 3, 4 | yes |
| 9 | F-WF-03 EXTEND-docs-cookbook — cookbook walkthrough under `docs/cookbook/alert_triage.md` + worked-example README polish across all three targets | 2, 3, 4 | yes |
| 10 | F-WF-03 EXTEND-config — answer the `config.yaml` question (CACAO `playbook_variables` vs separate operator YAML) and ship whichever is approved | 1 | yes |
| 11 | F-WF-03 CLOSEOUT — ROADMAP.md status flip In Progress → Shipped + decisions log update | 1–10 | yes |

Cards 2/3/4/5 fan out from card 1; tests/docs fan in on 2/3/4; the
closeout card fans in on everything. Each PR is reviewed against the
public-bar before merge, following the same cadence used for F-WF-01.

## 4. Open questions for maintainers

1. **Primitives directory location.** F-WF-01 ships its primitives
   under `content/playbooks/vuln_intake/primitives/` because the source
   playbook lives in a `content/playbooks/vuln_intake/` directory.
   F-WF-03's canonical source is a flat YAML at
   `content/playbooks/alert_triage.cacao.yaml`. Two readings: (a)
   introduce `content/playbooks/alert_triage/primitives/` and let the
   flat YAML and the subdirectory coexist (the YAML keeps its current
   path; primitives live alongside it under the subdirectory name);
   (b) restructure to mirror vuln_intake — move the YAML under
   `content/playbooks/alert_triage/` first, then add `primitives/`.
   Card 1 needs a one-line direction. Recommendation is (a): the
   restructure is a separate refactor and dragging it into CORE-PRIM
   inflates the diff and the review surface.
2. **GDPR data-flow doc as a workflow-local artifact.** ROADMAP F-WF-03
   pins payload validation against
   `content/mappings/gdpr/data-flow-alert_triage.md`. That directory
   today only carries a `README.md`; no per-workflow data-flow doc
   exists for any workflow yet. Card 5 owns shipping the first one,
   but the structural decision — does every workflow get a peer doc,
   or does a single per-mapping schema cover all workflows? — is a
   maintainer call that affects future workflows too.
3. **`config.yaml` semantics.** Mirror of the F-WF-01 open question.
   The CACAO `playbook_variables` block already declares the
   `__alert_id__`, `__alert_source_shape__`, `__benign_or_seen__`,
   `__priority__` contract. Is that the answer, or does the
   operator-facing YAML live separately? F-WF-02 (Shipped) does not
   ship a per-workflow YAML; precedent points at the CACAO block being
   authoritative.
4. **DSPy reach.** ROADMAP says "DSPy module only used for free-text
   fields" and FOUNDATION §LLM determinism reinforces it. Card 1 reads
   those together as: the priority decision is deterministic code, the
   DSPy signature covers free-text fields on the case (analyst
   summary, narrative). Confirm before card 1 starts; this is the same
   question F-WF-01 raised and the answer should be consistent.
5. **Typed payload shapes — placement.** The two source shapes (push
   from detection pipeline, pull from a shared alert store) need a
   typed home. Two readings: (a) under `content/telemetry/` as OCSF
   bindings (matches F-WF-01's `__report_source__` evolution); (b)
   under `content/playbooks/alert_triage/payloads/` as
   workflow-local types. Card 1 needs a one-line direction.

## 5. Out of scope for this card

- ROADMAP.md acceptance-criteria edits (the status flip flows from
  card 11 when the wave is shipped). The `Proposed → In Progress`
  flip on the status field itself ships in this PR.
- Any actual CORE body work — that is cards 2–4.
- Restructuring the canonical source from flat YAML to a subdirectory
  layout — separate refactor, see § 4 question 1.
- GDPR data-flow doc design — card 5.
