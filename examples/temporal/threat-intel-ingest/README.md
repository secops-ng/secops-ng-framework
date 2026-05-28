# threat-intel-ingest — Temporal worked example

Emitted from `content/playbooks/threat-intel-ingest/playbook.cacao.json`
via `python -m compilers.temporal`.

- `playbook.cacao.json` — source CACAO playbook (copy of the canonical
  authored file under `content/`).
- `workflow.py` — generated Temporal stub: one `@workflow.defn` class
  with an `async def run` entry point, one `@activity.defn` per CACAO
  action step, and a module-level `RetryPolicy` template per activity.

Activity bodies raise `NotImplementedError` by design — the CACAO
playbook is the source of truth; integrators wire activities into the
operator's runtime without round-tripping back through the content
model. Workflow control-flow lowering (branching, parallel) is tracked
on a separate card.

The emitter is deterministic: regenerating produces byte-identical
source.
