# <workflow-name>

> Canonical empty skeleton. Copy this directory (`cp -r _template/ <name>/`)
> to start a new workflow. Every required file below must be present and
> non-stub before the workflow is merged.

## Purpose

TODO: one short paragraph — what this workflow does, who it is for, and
what regulatory or operational need it addresses.

## Inputs

TODO: explicit input schema. Reference the Pydantic `ToolIO` subclass
defined in `primitives.py`. List every field, its type, and whether it
is required.

## Outputs

TODO: explicit output schema. Same shape as inputs — list every field
the workflow guarantees to populate on success, plus the audit-trail
contract.

## Configuration

TODO: table of every configurable knob exposed by this workflow.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| TODO | TODO | TODO | TODO |

A full annotated example lives in `config.example.yaml`.

## Running the example

```bash
python workflows/<workflow-name>/example.py
```

Configure a real LM via environment variables before running — see
`src/secops_ng/workflows/<workflow-name>.py` (the library module) for
the `configure_default_lm` contract. Without credentials the script
will construct the graph but the LLM-facing step will fail; tests
inject a `DummyLM` to keep CI offline-safe.

## Integration notes

TODO: how this workflow plugs into a broader runner (LangGraph host,
durable scheduler, ingest pipeline). Reference the library module
under `src/secops_ng/workflows/` if the logic lives there.

## See also

- `PROMPT.md` — single-shot prompt to reconstruct this workflow from
  scratch.
- `primitives.py` — graph nodes, DSPy signatures, state types.
- `example.py` — runnable example.
- `config.example.yaml` — annotated configuration surface.
