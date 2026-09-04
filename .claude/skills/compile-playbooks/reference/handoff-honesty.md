# What to tell the operator, and where the numbers come from

The compilers already write the honest remaining-work list. This file says how to
read it, so the hand-off reports the compiler's own output instead of asserting a
claim that has to be kept in sync by hand.

## The frame, stated once, before the interview

> This repo ships portable content and reference compilers — no runtime. The
> compilers emit topology, typed I/O contracts, regulatory references and
> observability wiring; for a `stable` playbook every action body already
> invokes a deterministic primitive, and what remains is connector wiring —
> for the `experimental` tail you also write the step bodies. `stable` is the
> Maturity ladder's deployment-ready bar (ROADMAP § Maturity ladder);
> `content-model/playbook.schema.json` says of the non-stable tiers that they
> "are not compiled by default in production targets."

Say this **before** the operator spends five answers, not after. It costs three
lines and it is the difference between honesty and a bait-and-switch.

## Six statements that must survive into the hand-off

1. **Which maturity tier the playbook sits on, with the tier's meaning.** Read
   the tally and the per-playbook tier from `catalog.py` (or the generated
   table at `content/playbooks/README.md` — CI keeps it honest); never quote a
   count from this file. A `stable` recommendation and an `experimental` one
   are different conversations, and the operator must know which they are in.
2. **The `experimental` tail is topology plus contract, not bodies** — its
   action steps are unbound (`catalog.py`'s `real_bindings` column), and the
   remaining work is `predicted_n8n_todos`.
3. **Bindings live on the canonical playbook — the single source of truth.**
   The early per-example overlay seam (`core_body.overlay.json`) is closed:
   the files remain on disk but are empty, and a seam-closure test pins them
   empty with each mirror byte-identical to its canonical source. If a fork
   between canonical and example ever reappears, that test — not this doc —
   is the alarm.
4. **Temporal does not give you control flow** — say it *before* recommending it.
5. **LangGraph does not give you a runnable graph** — the `assemble.py`
   reference assembly that wires `graph_spec.json` into a `StateGraph` is
   hand-written; no compiler emits it, and many examples ship only the spec
   and bindings without one.
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

For a `stable` playbook the count is small and names operator seams (connector
wiring), not missing logic; for the `experimental` tail it approximates the
unbound step count. Read it fresh — it changes as binds land.

**Blank branch predicates — the dangerous class, list them separately.** A
minority of playbooks still carry branch steps without a parseable predicate;
`catalog.py` returns `blank_predicates` with each `step_id`, its `type`, and any
`raw_expression` — read it per playbook rather than assuming either way.

These matter more than stub bodies and deserve their own short list, because the
failure mode is different: an unimplemented body **fails loudly**; a blank
predicate **takes the wrong path silently**. A raw expression is not sufficient
on its own — the emitter must actually parse cases from it, and `catalog.py`'s
column is the arbiter.

## Quantify what the compiler *did* do

This is what keeps the honesty from reading as discouragement. For each step the
emitted artifact already carries the `in_args`/`out_args` contract, the
`control_refs` / `telemetry_refs` / `metric_refs`, the retry policy, and the OTel +
`AuditTrail` wiring. **The operator writes the body; they do not design the
interface, the audit trail, or the regulatory mapping.** State it once with the
counts read from the artifact's own `meta` / refs blocks. A quantified gift
lands; a vague reassurance does not.

## Tone rules

- Counts first, in the order **what you have** → **what's left**. Copy the *shape*
  of `docs/deploy/sovereign-quickstart.md` § "What you have, what you do not".
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
| how bindings reach the canonical source | any `WIRE` / `CORE-WIRE` PR in the history; the overlay seam is closed |
| LangGraph runtime assembly | `examples/langgraph/<slug>/assemble.py` |
| why stubs are the design | `docs/FOUNDATION.md` |

**Do link** `docs/quickstart/README.md` — it is a real end-to-end walkthrough
now (the funnel dry-run exercised it verbatim). **Do not link**
`docs/ARCHITECTURE.md` while its stale notice stands.

Hosting, provider choice, LM residency and compliance scoping are **out of scope**
— name them as out of scope once, point at `docs/sovereignty/`, and stop.
