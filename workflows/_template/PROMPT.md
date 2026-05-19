# PROMPT — rebuild <workflow-name> from scratch

> This file is a single-shot prompt. Hand it to a fresh agent (or
> human contributor) with no other context and they should be able to
> produce a functionally-equivalent workflow.

## 1. Goal

TODO: one sentence stating what the workflow accomplishes.

## 2. Inputs / Outputs

**Inputs** — explicit schema:

TODO: each field, type, semantics.

**Outputs** — explicit schema:

TODO: each field the workflow guarantees on success, plus the audit
trail.

## 3. Required primitives

TODO: list each graph node, DSPy signature, and state type by name and
signature.

- `node_name(state: <StateType>) -> <StateType>` — TODO intent.
- `<SignatureClass>(dspy.Signature)` — TODO inputs/outputs/constraints.
- `<StateType>(ToolIO)` — TODO field list.

## 4. Workflow shape

TODO: high-level state machine in prose. Describe the states, the
edges, durability requirements (which transitions must survive a
restart), and any conditional routing.

## 5. Configuration surface

TODO: every config option, type, default, semantics. Should match the
table in `README.md` and the keys in `config.example.yaml`.

| Key | Type | Default | Semantics |
|-----|------|---------|-----------|
| TODO | TODO | TODO | TODO |

## 6. Acceptance criteria

- TODO: tests under `tests/test_<workflow-name>_*.py` pass.
- TODO: `python workflows/<workflow-name>/example.py` runs to
  completion against a `DummyLM`.
- TODO: `ruff check`, `ruff format --check`, `mypy src` all green.
- TODO: any workflow-specific behavioural checks.

## 7. Anti-goals

- Do not call external services from the graph-node functions
  directly; isolate side effects behind explicit tools / adapters.
- Do not duplicate state mutation — every node returns a fresh
  `ToolIO` instance via `model_copy`.
- Do not hardcode endpoints or credentials. Read from environment via
  `configure_default_lm` or an equivalent.
- Do not embed strategy, internal infrastructure, or contact names
  anywhere in this directory — it is forward-public.
