# Workflow Templates

This directory holds **end-user workflow examples** — concrete, runnable
templates that illustrate how to compose `secops_ng` primitives into useful
SecOps automation.

These files are deliberately separate from the library code under
`src/secops_ng/`:

- `src/secops_ng/` is the framework (imported as a library).
- `workflows/` is the cookbook (copied, adapted, and operated by you).

Each template here should be:

1. Self-contained and runnable (after configuring `.env`).
2. Heavily commented — assume the reader is learning LangGraph, DSPy, and
   SecOps-NG at the same time.
3. Safe by default — no destructive actions without explicit confirmation.
4. Sovereignty-aware — no hardcoded calls to non-EU endpoints; everything
   pluggable through `secops_ng.config`.

## Current templates

| File | Status | Purpose |
|------|--------|---------|
| `vulnerability_triage.py` | example | LangGraph triage of a single finding, with DSPy severity classification |

Contributions of new templates are very welcome — see `../CONTRIBUTING.md`.
