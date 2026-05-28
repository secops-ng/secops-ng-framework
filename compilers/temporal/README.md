# compilers/temporal/

Emits Temporal workflow stubs (Python) from a CACAO v2 playbook.

## What it produces

One generated module per playbook, containing:

- One `@workflow.defn` class — `run()` raises `NotImplementedError` carrying
  the playbook `stable_id`. Control-flow lowering (transitions, branches,
  parallel) is intentionally deferred to a follow-up card.
- One `@activity.defn` async function per CACAO `action` /
  `playbook-action` step. Each body raises `NotImplementedError` carrying
  the CACAO `step_id` so a runtime worker fails loudly with a deterministic
  message pointing at the source step.
- `WORKFLOW` and `ACTIVITIES` registry symbols a worker bootstrap can import
  without re-scanning the module.

Control-flow step types (`start`, `end`, `if-condition`, `while-condition`,
`switch-condition`, `parallel`) do **not** produce activities — they become
workflow code when lowering lands.

## Usage

```python
from compilers.temporal import emit_file

source = emit_file("content/playbooks/vuln-intake/playbook.cacao.json")
```

Output is deterministic: the same AST always yields byte-identical source.

## Scope

This module is **stub-only**. It does not import `temporalio` itself, makes
no I/O beyond reading the input file, and emits no business logic. An
integrator fills the activity bodies and the `run()` orchestration against
their own runtime.
