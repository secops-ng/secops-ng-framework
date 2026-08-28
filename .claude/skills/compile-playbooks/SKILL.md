---
name: compile-playbooks
description: Pick which playbooks to adopt and which compile target to use, then compile them. Use when asked which playbook to start with, which of them are actually ready to run, how much work a playbook still needs before it does anything, whether to use n8n or Temporal or LangGraph, or how to get this content into an existing automation stack. Reads the CACAO catalogue under content/playbooks/ and reports computed readiness per playbook — it advises and compiles, and never deploys.
---

# Choose playbooks and a compile target

`docs/quickstart/README.md` already walks through installing, compiling and running
one worked playbook end to end. **Send the operator there for the mechanics.** This
skill covers the two things the quickstart deliberately does not: with every
finalized playbook compilable, *which* to adopt, and which target to compile into.

Companion reference: `reference/target-tradeoffs.md` for the per-target matrix,
`reference/handoff-honesty.md` for how to report remaining work.

## Boundaries

Advise and compile. **Never deploy**, never run an orchestrator import, never
`terraform apply`.

Hosting, provider choice, LM residency and infra sizing are out of scope here —
name them as out of scope and point at `docs/sovereignty/`.

## Read the catalogue first

```bash
python .claude/skills/compile-playbooks/scripts/catalog.py --table   # humans
python .claude/skills/compile-playbooks/scripts/catalog.py           # JSON
```

Never hand-derive this. The script exists because the catalogue has traps that
reading by eye walks into:

- a slug can be reachable **twice** — `content/playbooks/<slug>/playbook.cacao.json`
  and a dir-level `<slug>.cacao.yaml`. It prefers the directory form and flags
  `yaml_mirror_exists`.
- `core_body` blocks shaped `{placeholder, note}` **look** like primitive bindings
  and are not; only `{primitive, in, out}` counts.
- it validates against `content-model/playbook.schema.json`, so a playbook that
  cannot compile is reported as such instead of being recommended.

`predicted_n8n_todos` is the remaining-work figure: unbound actions plus
control-flow steps (`if`/`switch`/`while`/`parallel`). Verified exact against every
committed n8n example when the column landed; it recomputes from source, so it
needs no compile.

## Choosing a playbook

Rank by `maturity` first. `stable` is the Maturity ladder's deployment-ready
designation (ROADMAP § Maturity ladder): every action step carries a real
primitive binding, three-target worked examples are golden-pinned, and the
primitives are unit-covered — graduation is a checklist `catalog.py` computes,
not a judgement call. **The `stable` set is the honest "start here" set**, and
it currently coincides exactly with `todo = 0`. Never quote a count from this
file: the generated table at `content/playbooks/README.md` carries the current
maturity tally and per-playbook tier, and CI fails when it is stale.

Within the non-stable tail, sort by the `todo` column — the figure that predicts
time-to-running. Two things to say out loud:

- The scenario names an operator often asks for first (`phishing_triage`,
  `ransomware_containment`, `cloud_misconfiguration`) currently sit in the
  unbound tail with the **most** remaining work — read their `todo` from the
  script and say so before they invest a sprint in one.
- Do not rank by step count — it measures scope, not readiness.

**Cap the first pass at one playbook.** The failure this prevents is an operator
compiling six, opening forty stub bodies, and concluding the framework is vapour.
One playbook, all the way to one step body actually running, then the next.

## Choosing a target

Five questions, stop at the first that decides it:

```
Q1 Already running n8n, Temporal or LangGraph in production?
   exactly one -> pin it; the decision is done. The compilers exist so an operator
   adopts without re-platforming, and that cost dominates every other factor.
Q2 Must a model CHOOSE what happens next (not merely write text in a fixed step)?
   yes -> LangGraph. If Q1 already pinned another runtime, do NOT add a second one:
   keep theirs and put the model behind one deterministic step.
Q3 Must a run survive process death and resume, against a regulator clock?
   yes -> Temporal, with the mandatory disclosure below.
Q4 Will a rotating analyst read and adjust it, rather than its author?     -> n8n
Q5 Reviewed in git, or edited in the orchestrator UI?              UI      -> n8n
default                                                                   -> n8n
```

**Before recommending Temporal, say this:** its emitter does not lower control flow
— the workflow body raises `NotImplementedError` and branch steps produce no
activities. You write the orchestration from the CACAO step graph. It is the only
target that does not preserve topology. If the goal is to *see the playbook run end
to end*, n8n is the better first target even for a Temporal shop.

The n8n default is a property of the compilers, not a judgement about the team: it
is the only target whose artifact preserves control flow *and* imports without
writing Python, and the only one that publishes its own remaining-work list
(`meta.secops_ng_notes`).

Report the outcome naming the question that decided it and the condition that would
flip it. Never a score the operator cannot audit.

## Compiling

Point at `docs/quickstart/README.md` for the walkthrough. Two things it does not
say that will cost time:

- **LangGraph is not in the unified CLI.** `tools/compile/cli.py` still has
  `_TARGETS = {"n8n", "temporal"}`. Use the module entrypoints directly, as the
  committed examples' `regenerate.sh` do:
  ```bash
  python -m compilers.langgraph.emit  <playbook> > graph_spec.json
  python -m compilers.langgraph.state <playbook> > state_bindings.py
  python -m compilers._shared.audit_mirror_cli --out _audit_mirror.py
  ```
  `emit` and `state` have no `--out`; redirect stdout. The `runpy` RuntimeWarning on
  stderr is benign.
- **Temporal's emitted module imports a sibling** (`from ._audit_mirror import …`),
  so it needs `audit_mirror_cli` run alongside plus an `__init__.py`, or it will not
  import.

Write compiled output somewhere ignored — never under `examples/`, where
`regenerate.sh --check` runs `git checkout --` and where files read as goldens to
the next contributor.

## Reporting remaining work

Derive it, never narrate it — see `reference/handoff-honesty.md`. For n8n quote
`meta.secops_ng_notes` verbatim; for the Python targets count `NotImplementedError`.

List blank branch predicates separately from stub bodies. They fail differently: a
stub body fails loudly, a blank predicate takes the wrong path silently.

And quantify what the compiler *did* do — the I/O contract, the control/telemetry/
metric refs, the retry policy and the audit wiring are all filled in. The operator
writes bodies; they do not design the interface or the regulatory mapping.

## Voice

Write for **the operator**. Commercial register belongs in the private strategy
repo; `tools/hygiene_linter/rules/commercial.py` holds the pattern list and
`SOUL.md` the rationale. Never call compiler output "runnable" or "production".
Check anything you write:

```bash
python -m tools.hygiene_linter <path> --min-severity LOW
```

`--min-severity` only filters display; `--gate-severity` (default HIGH) drives the
exit code, so read the findings rather than the exit status.
