# What to tell the operator, and where the numbers come from

The compilers already write the honest remaining-work list. This file says how to
read it, so the hand-off reports the compiler's own output instead of asserting a
claim that has to be kept in sync by hand.

## The frame, stated once, before the interview

> This repo ships portable content and reference compilers — no runtime. The
> compilers emit topology, typed I/O contracts, regulatory references and
> observability wiring; you write the step bodies. Nothing in the catalog is
> `maturity: stable` yet: `content-model/playbook.schema.json` says of the enum
> that `draft` and `experimental` "are not compiled by default in production
> targets."

Say this **before** the operator spends five answers, not after. It costs three
lines and it is the difference between honesty and a bait-and-switch.

## Six statements that must survive into the hand-off

1. **Nothing is `stable`.** 10 `experimental`, 2 `draft` (`identity-compromise`,
   `alert_triage`), 1 invalid `skeleton`. `catalog.py` reports
   `counts.stable` — it is 0.
2. **9 of the 12 compilable playbooks are topology only** — zero bindings, every
   action body a stub or an empty `set` node.
3. **`incident_management`'s 4 bindings come from a per-example overlay, not the
   canonical playbook.** `examples/<target>/incident_management/core_body.overlay.json`
   is the documented seam; its `_meta` states the canonical "intentionally carries
   no core_body blocks yet". Compiling straight from `content/playbooks/` yields
   **9** remaining items; with the overlay applied, **5**. `catalog.py` reports
   both as `predicted_n8n_todos` and `predicted_n8n_todos_with_overlay`.
4. **Temporal does not give you control flow** — say it *before* recommending it.
5. **LangGraph does not give you a runnable graph** —
   `examples/langgraph/vuln_intake/assemble.py` is 184 hand-written lines that no
   compiler emits.
6. **Running a bound artifact needs `pydantic` and `PYTHONPATH=<repo>/content/playbooks`.**
   Emitted code imports `vuln_intake.primitives.…`, which resolves only with
   `content/playbooks/` on `sys.path`; `pydantic` is imported by the primitive
   modules and is declared in neither `pyproject.toml` nor `uv.lock`. Both are
   undocumented, so the hand-off must supply them.

## Deriving `gaps.json` per target

**n8n — read it directly.** `meta.secops_ng_notes` is a list of per-step strings
already written for an operator:

> `step 'action--01a17a01-…-0004': action with no commands — emitted Set node
> carrying the CACAO I/O contract (in_args / out_args / x_secops_ng refs).
> Operator fills the values in n8n.`
> `step 'switch-condition--01a17a01-…-0007' (switch-condition): no cases parsed …`

Quote these **verbatim** in the hand-off table. Do not paraphrase and do not
re-derive. `meta.secops_ng` alongside carries `stable_id`, `content_version`,
`maturity` for the decision header.

**Temporal / LangGraph — count the walls.** They are loud and *addressed*, which
is a design feature worth naming:

```bash
grep -c NotImplementedError <artifact>          # remaining bodies (+1 for Temporal's workflow lowering)
grep -c 'primitives\.'      <artifact>          # bodies the binding already wrote for you
```

For `vuln_intake` both `workflow.temporal.py` and `state_bindings.py` report 8.

**Blank branch predicates — the dangerous class, list them separately.** Every
branch step in every playbook lacks a parseable predicate. `catalog.py` returns
`blank_predicates` with each `step_id`, its `type`, and any `raw_expression`.

These matter more than stub bodies and deserve their own short list, because the
failure mode is different: an unimplemented body **fails loudly**; a blank
predicate **takes the wrong path silently**. A raw expression is not sufficient —
`vuln_intake`'s switch carries `switch: '__severity__'` and the emitter still
records "no cases parsed".

## Quantify what the compiler *did* do

This is what keeps the honesty from reading as discouragement. For each step the
emitted artifact already carries the `in_args`/`out_args` contract, the
`control_refs` / `telemetry_refs` / `metric_refs`, the retry policy, and the OTel +
`AuditTrail` wiring. **The operator writes the body; they do not design the
interface, the audit trail, or the regulatory mapping.** State it once with the
counts — `vuln_intake` carries 5 control refs, 1 telemetry ref and 9 metric refs
at playbook level plus per-step refs. A quantified gift lands; a vague reassurance
does not.

## Tone rules

- Counts first, in the order **what you have** → **what's left**. Copy the *shape*
  of `docs/deploy/sovereign-quickstart.md` §7 ("What you have, what you do not") —
  the shape only; that doc is stale and references deleted trees.
- Never "just", "simply", "should work".
- **Never "runnable" or "production"** about compiler output. (The public site
  calls the vuln-triage playbook "runnable" — do not repeat that word here.)
- No hour estimates. If an effort unit is needed: "one step body ≈ one connector
  call plus a shape assertion."
- Always say "the operator". Buyer nouns and commercial register are the wrong
  voice per `SOUL.md`, and `tools/hygiene_linter/rules/commercial.py` flags them.

## Hand off, don't restate

| Topic | Owning doc |
|---|---|
| per-target emit semantics, lossy translation table | `docs/compilers/{n8n,temporal,langgraph}.md` |
| full narrative for a Tier A playbook | `docs/cookbook/{alert_triage,vuln_intake,incident_management}.md` |
| audit trail, JSONL replay, no-OTLP posture | `docs/observability/audit-mirror.md` |
| adding bindings without forking the canonical | `examples/*/incident_management/apply_overlay.py` |
| LangGraph runtime assembly | `examples/langgraph/<slug>/assemble.py` |
| why stubs are the design | `docs/FOUNDATION.md` |

**Do not link** `docs/quickstart/README.md` (4-line dead end),
`docs/ARCHITECTURE.md` (stale notice), or `docs/deploy/sovereign-quickstart.md` as
a walkthrough (references deleted `src/secops_ng/`, `workflows/`).

Hosting, provider choice, LM residency and compliance scoping are **out of scope**
— name them as out of scope once, point at `docs/sovereignty/`, and stop.
