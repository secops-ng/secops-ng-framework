# F-WF-01 — Vulnerability triage — gap inventory

> Contributor-facing planning document. Snapshots what is on `main`
> today versus what `ROADMAP.md` requires for F-WF-01 to flip from
> **In Progress** to **Shipped**, and how the remaining work is sliced
> into independently dispatchable contributor tasks.
>
> See [`ROADMAP.md`](../../ROADMAP.md#f-wf-01--vulnerability-triage)
> for the acceptance criteria this inventory closes against, and
> [`AGENTS.md`](../../AGENTS.md) for repository conventions.

---

## 0. Naming note

ROADMAP F-WF-01 talks about `workflows/vulnerability_triage/`. The
on-disk layout that has actually emerged in this repository is

```
content/playbooks/vuln-intake/            # CACAO source of truth
examples/{n8n,temporal,langgraph}/vuln-intake/   # compiled worked examples
```

That divergence pre-dates this card and matches the layout for every
other shipped workflow (posture-audit, phishing-triage, …). This
inventory treats `vuln-intake` as the canonical name; a ROADMAP wording
fix is out of scope here and will be picked up when F-WF-01 flips to
Shipped.

## 1. Acceptance criteria → coverage matrix

| ROADMAP requirement | Status | Where |
|---|---|---|
| Canonical CACAO source for the workflow | ✅ done | `content/playbooks/vuln-intake/playbook.cacao.json` (11 steps: 1 start, 7 action, 1 if-condition, 1 switch-condition, 1 end) |
| Worked example — n8n | ✅ SKELETON | `examples/n8n/vuln-intake/workflow.n8n.json` |
| Worked example — Temporal | ✅ SKELETON | `examples/temporal/vuln-intake/workflow.temporal.py` |
| Worked example — LangGraph | ✅ SKELETON | `examples/langgraph/vuln-intake/{graph_spec.json,state_bindings.py}` |
| Byte-parity golden tests (drift guards) | ✅ done | `tests/examples/vuln_intake/` + `tests/examples/test_langgraph_vuln_intake.py` |
| OTel spans on every node | ⚠️ partial | Temporal + LangGraph emit `_TRACER.start_as_current_span(...)` per action; n8n is a node-graph format so OTel is a runtime concern documented per node-id, not a per-node instruction in the JSON. |
| `AuditTrail` mirror integration | ✅ done | All three targets call `AuditTrail.current().append(...)` per action (delivered by the F-CR-04 wave). |
| **Library code / primitives directory** | ❌ missing | No `content/playbooks/vuln-intake/primitives/` exists. Severity policy, CVSS+EPSS scoring helpers, and the deterministic dedup function have nowhere to live. |
| **DSPy signature for severity rating (free-text fields only)** | ❌ missing | No `DSPy` import or `dspy.Signature` exists in the vuln-intake tree. |
| **Deterministic dedup** | ❌ missing | No dedup helper, no canonicalisation of `__cve_id__ + __asset_ref__`, no idempotency key. |
| **CORE action bodies** (intake, triage, assess, regulator, 4× response) | ❌ missing | All 7 action stubs in all three targets `raise NotImplementedError(...)`. |
| **Tests — happy path** | ❌ missing | The only vuln-intake tests today are byte-parity drift guards. |
| **Tests — dedup-collision** | ❌ missing | No dedup test exists because no dedup helper exists. |
| **Tests — replay** | ❌ missing | No replay test (golden replay across all three targets). |
| **Cookbook entry + walkthrough docs** | ❌ missing | `content/playbooks/vuln-intake/README.md` exists but only describes the playbook shape; there is no cookbook walkthrough doc under `docs/cookbook/` (the directory does not yet exist for vuln-intake). |
| **`config.yaml`** | ❌ missing | F-WF-02 (Posture audit, Shipped) ships its own scaffolding without a per-workflow `config.yaml`. F-WF-01 needs a clear answer on whether the ROADMAP `config.yaml` requirement is satisfied by the CACAO `playbook_variables` block or whether a separate operator-facing YAML is expected. See § 4 — flagged for maintainer review. |
| **Threat-intel feeds as Pydantic-typed supplier deps (F-CP-04)** | ❌ blocked | F-CP-04 is Status: Proposed. The intake step today carries `__report_source__` as a free string; the supplier-dependency contract cannot land until F-CP-04 ships a Pydantic shape. Tracked but not blocking F-WF-01 closeout — see § 4. |

## 2. Per-target action × body inventory

Every CACAO step shipped per target today; ✅ = SKELETON stub present
(span + AuditTrail mirror + `NotImplementedError`), ❌ = CORE body
required.

| CACAO step | n8n | Temporal | LangGraph |
|---|---|---|---|
| `start` — `vuln-intake-start` | ✅ trigger node | ✅ workflow entry | ✅ entry binding |
| `action--…000002` — intake disclosure | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…000003` — triage and asset correlation (CVSS+EPSS+severity+dedup) | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…000004` — assess CRA reporting trigger | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `if-condition--…000005` — actively exploited? | ✅ edge wiring only — no body required | ✅ edge wiring only | ✅ edge wiring only |
| `action--…000006` — regulator-notification chain (CRA Art. 14) | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `switch-condition--…000007` — route on severity | ✅ edge wiring only | ✅ edge wiring only | ✅ edge wiring only |
| `action--…000008` — response: critical | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…000009` — response: high | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…00000a` — response: scheduled remediation | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `action--…00000b` — response: accept risk | ❌ CORE body | ❌ CORE body | ❌ CORE body |
| `end` — `vuln-intake-end` | ✅ | ✅ | ✅ |

That is **7 actions × 3 targets = 21 CORE bodies missing**, plus the
shared primitives module they will all call into.

## 3. Decomposition strategy

Grouping per-target rather than per-(action × target). Precedent: the
F-CR-04 wave landed CORE work as per-target cards (CORE-LG, CORE-TMPRL,
CORE-C-AUDIT-SKEL …), not per-(action × target) cards, because the
seven action bodies in a single target share the same imports, helper
contract, and golden-regen cadence — splitting them three ways per
action would create 21 trivially-coupled PRs and 21 review cycles for
work that is one mechanical sweep per target.

Cross-target consistency of the action *semantics* (e.g. the severity
policy, the dedup key, the regulator-notification contract) is enforced
once in the shared primitives module (`CORE-PRIM`); per-target cards
then bind their framework idioms to those primitives. This is the same
shape F-CR-04 used: shared helper first (`AuditTrail`), per-target
wiring after.

### 3.1 Sibling cards to spawn

All cards land as **siblings** of this gap-inventory card (no parent
edge back to it) so they sit flat on the board. Cross-card
dependencies are expressed via `parents=[…]` between siblings so the
dispatcher only promotes cards whose upstreams are done.

| # | Card | Parents (other siblings) | Public-bar |
|---|---|---|---|
| 1 | F-WF-01 CORE-PRIM — shared primitives (severity policy, CVSS+EPSS helpers, deterministic dedup, DSPy signature for free-text fields) under `content/playbooks/vuln-intake/primitives/` | — | yes |
| 2 | F-WF-01 CORE-N8N — wire 7 CORE action bodies in `examples/n8n/vuln-intake/workflow.n8n.json` against the primitives contract; regen via `regenerate.sh`; golden byte-parity green | 1 | yes |
| 3 | F-WF-01 CORE-TMPRL — wire 7 CORE action bodies in `examples/temporal/vuln-intake/workflow.temporal.py` against the primitives contract; regen; golden byte-parity green | 1 | yes |
| 4 | F-WF-01 CORE-LG — wire 7 CORE action bodies in `examples/langgraph/vuln-intake/state_bindings.py` against the primitives contract; regen; golden byte-parity green | 1 | yes |
| 5 | F-WF-01 EXTEND-tests-happy — happy-path golden replay test across all three targets in `tests/examples/vuln_intake/` | 2, 3, 4 | yes |
| 6 | F-WF-01 EXTEND-tests-dedup — dedup-collision test (same CVE × same asset_ref → single case) across all three targets | 2, 3, 4 | yes |
| 7 | F-WF-01 EXTEND-tests-replay — deterministic-replay test (same input twice → byte-identical AuditTrail) across all three targets | 2, 3, 4 | yes |
| 8 | F-WF-01 EXTEND-docs-cookbook — cookbook walkthrough under `docs/cookbook/vuln-intake.md` + worked-example README polish across all three targets | 2, 3, 4 | yes |
| 9 | F-WF-01 EXTEND-config — answer the `config.yaml` question (CACAO `playbook_variables` vs separate operator YAML) and ship whichever is approved | 1 | yes |
| 10 | F-WF-01 CLOSEOUT — ROADMAP.md status flip In Progress → Shipped + decisions log update | 1–9 | yes |

Cards 2/3/4 fan out from card 1; tests/docs fan in on 2/3/4; the
closeout card fans in on everything. Each PR is reviewed against the
public-bar before merge, following the same cadence used for F-CR-04.

## 4. Open questions for maintainers

1. **`config.yaml` semantics.** ROADMAP F-WF-01 asks for a per-workflow
   `config.yaml`. The CACAO playbook already declares
   `playbook_variables` (the `__cve_id__`, `__severity__`, … contract).
   Card 9 needs a one-line direction: is the existing
   `playbook_variables` block the answer, or does the operator-facing
   YAML live separately? F-WF-02 (Shipped) does not ship a per-workflow
   YAML, so precedent points at the CACAO block being authoritative.
2. **F-CP-04 (vulnerabilities stream) coupling.** ROADMAP F-WF-01's
   sovereign-stack constraint says threat-intel feeds are
   Pydantic-typed supplier dependencies under F-CP-04. F-CP-04 is
   Status: Proposed. Two readings: (a) F-WF-01 can flip to Shipped
   with the current free-string `__report_source__` and the supplier
   shape lands later as part of F-CP-04; (b) F-WF-01 cannot flip until
   F-CP-04 lands. Flag for maintainers — recommendation is (a), with the
   note in `__report_source__`'s description pointing forward to
   F-CP-04.
3. **DSPy reach.** ROADMAP says "DSPy signature for severity rating"
   but FOUNDATION.md §LLM determinism says "deterministic
   prioritisation policy expressed as code; DSPy module only used for
   free-text fields." Card 1 reads those together as: severity is
   deterministic code, DSPy is used only for free-text fields on the
   case (reporter narrative, advisory body). Confirm before card 1
   starts.

## 5. Out of scope for this card

- ROADMAP.md edits (the status flip flows from card 10 when the wave
  is shipped).
- Any actual CORE body work — that is cards 2–4.
- F-CP-04 design — separate roadmap item.
