# Workflow Templates

This directory holds **end-user workflow examples** — concrete,
runnable templates that show how to compose `secops_ng` primitives
into useful SecOps automation.

These files are deliberately separate from the library code under
`src/secops_ng/`:

- `src/secops_ng/` is the framework (imported as a library).
- `workflows/` is the cookbook (copied, adapted, and operated by you).

## Every workflow is a directory

Every workflow under `workflows/` is its own directory. Single-file
templates are not accepted. The canonical layout, mirrored by
`_template/`, is:

```
workflows/<workflow-name>/
  README.md           purpose, inputs/outputs, full config table, integration notes
  PROMPT.md           single-shot prompt to rebuild this workflow from scratch
  primitives.py       graph nodes, DSPy signatures, state types (or re-exports from the library)
  example.py          runnable cookbook example
  config.example.yaml annotated configuration surface, every knob with default
```

Each template should be:

1. Self-contained and runnable (after configuring `.env`).
2. Heavily commented — assume the reader is learning LangGraph, DSPy,
   and SecOps-NG at the same time.
3. Safe by default — no destructive actions without explicit
   confirmation.
4. Sovereignty-aware — no hardcoded calls to non-EU endpoints;
   everything pluggable through `secops_ng.config`.

## Starting a new workflow

New workflows MUST start by copying `_template/`:

```bash
cp -r workflows/_template workflows/<new-workflow-name>
```

A pull request that adds a workflow is rejected if any required file
(`README.md`, `PROMPT.md`, `primitives.py`, `example.py`,
`config.example.yaml`) is missing or left as a `TODO` stub.

## Why PROMPT.md

Each workflow ships a `PROMPT.md` that is a single-shot reproduction
prompt: a fresh agent (or contributor) handed *only* that file with
no other context should be able to produce a functionally-equivalent
workflow. This is a deliberate guardrail — it forces every workflow
to have a complete, externalised specification, separate from the
code that happens to implement it.

## Index

| Workflow | One-liner |
|----------|-----------|
| [`vulnerability_triage/`](vulnerability_triage/README.md) | LangGraph triage of a single finding with DSPy severity classification and a NIS2-aligned audit trail. |
| `vulnscan/` (planned) | End-user template for the multi-engine dynamic scan workflow — see [`../docs/vulnscan/README.md`](../docs/vulnscan/README.md). |

Contributions of new templates are very welcome — see
[`../CONTRIBUTING.md`](../CONTRIBUTING.md).
