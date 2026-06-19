# Temporal compiler

Compile a SecOps-NG CACAO v2 playbook into a Temporal workflow stub
(Python). The stub is the durable, restartable skeleton an integrator
fills in against their own runtime.

This is one of three reference compile targets — Temporal sits next to
n8n (no-code) and LangGraph (agentic). The framework itself is
runtime-agnostic; the compiler is here so operators who already run
Temporal can adopt SecOps-NG playbooks without re-platforming.

## Quickstart

From the repository root:

```bash
python -m compilers.temporal \
  content/playbooks/vuln_intake/playbook.cacao.json \
  > vuln_intake.py
```

Or, programmatically:

```python
from pathlib import Path
from compilers.temporal import emit_file

source = emit_file(Path("content/playbooks/vuln_intake/playbook.cacao.json"))
Path("vuln_intake.py").write_text(source, encoding="utf-8")
```

The generated module exposes two registry symbols:

- `WORKFLOW` — the single `@workflow.defn` class.
- `ACTIVITIES` — a tuple of every `@activity.defn` async function.

A worker bootstrap can import them directly, no module scanning:

```python
from temporalio.client import Client
from temporalio.worker import Worker

from vuln_intake import WORKFLOW, ACTIVITIES

async def main() -> None:
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="secops-ng",
        workflows=[WORKFLOW],
        activities=list(ACTIVITIES),
    )
    await worker.run()
```

## What's in the stub

| Element | Source | Body |
|---|---|---|
| `@workflow.defn` class | one per playbook | `run()` raises `NotImplementedError` carrying the playbook `stable_id` |
| `@activity.defn` function | one per CACAO `action` / `playbook-action` step | raises `NotImplementedError` carrying the CACAO `step_id` |

Control-flow step types (`start`, `end`, `if-condition`,
`while-condition`, `switch-condition`, `parallel`) do **not** produce
activities. Lowering them into workflow code is a follow-up card.

Output is deterministic: the same AST yields byte-identical source.
A golden test (`tests/compilers/temporal/test_golden.py`) locks the
`vuln_intake` worked example, so any emitter change has to update the
golden in the same commit and a reviewer sees the full diff.

Regenerate the golden when an intentional emitter change lands:

```bash
python -m compilers.temporal \
  tests/compilers/_shared/fixtures/vuln_intake.cacao.json \
  > tests/compilers/temporal/golden/vuln_intake.expected.py
```

## Sovereignty

Temporal is a durable execution engine, not a hosting decision. The
compile target is portable; where you run the resulting workflows is up
to the operator. Two paths fit the EU sovereign-cloud posture this
project favours (see [docs/sovereignty/](../sovereignty/)):

- **Temporal Cloud, EU region.** Temporal Cloud offers an EU-hosted
  control plane. Suitable for teams that want a managed service without
  taking the engine on-prem, accepting the standard managed-SaaS
  trade-offs (data residency follows the region you provision in;
  control-plane telemetry follows Temporal's terms).
- **Self-hosted Temporal on a sovereign EU runtime.** Temporal is
  open source (MIT) and runs on any Kubernetes cluster. Hosting it on
  an EU sovereign provider such as Nebul, OVHcloud, Scaleway, or
  Hetzner keeps both the data plane and the control plane inside an
  EU jurisdiction. This is the recommended posture for operators with
  strict residency or processor-chain constraints (GDPR Art. 28,
  NIS2 Art. 21, DORA Ch. V).

The compiler does not encode either choice. It emits portable Python
that targets the upstream `temporalio` SDK; deployment is the operator's
prerogative.

## Limits of this release

- Workflow `run()` body is a stub. Wiring activities into ordered /
  branched / parallel execution is a follow-up.
- Activity signatures are typed from CACAO step variables, but bodies
  are unimplemented by design.
- Retry policy, timeout, and task-queue routing are not yet surfaced
  into the emitted module — these are configuration concerns the
  follow-up cards will lower into the generated code.

See `compilers/temporal/README.md` for module-level engineering notes.
