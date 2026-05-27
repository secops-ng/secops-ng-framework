# compilers/_shared/cacao_parser

Shared CACAO v2 playbook parser used by every reference compiler in this
repository — `compilers/n8n`, `compilers/temporal`, and
`compilers/langgraph`. It accepts a SecOps-NG playbook JSON (the CACAO v2
superset defined in `content-model/playbook.schema.json`) and returns an
immutable in-memory AST. Emitters consume the AST; they never re-parse the
raw JSON.

This module is **parse + validate only**. It emits nothing.

## Usage

```python
from compilers._shared.cacao_parser import parse_file

pb = parse_file("path/to/playbook.cacao.json")

print(pb.x_secops_ng.stable_id)        # "playbook.vuln_intake@v1"
print(pb.start_step().name)            # "intake-start"

for step_id, step in pb.workflow.items():
    for target in step.next_step_ids():
        ...
```

## What the parser checks

1. **Schema.** The JSON is validated against
   `content-model/playbook.schema.json` (Draft 2020-12). Any schema failure
   raises `CacaoSchemaError` carrying the full list of validator messages.
2. **Cross-reference invariants.** After schema validation the parser
   additionally checks:
   - `workflow_start` resolves to an existing step of type `start`
   - exactly one `start` step is declared
   - at least one `end` step is declared
   - every `on_completion` / `on_success` / `on_failure` / `next_steps`
     transition target exists in `workflow`
   - `workflow_exception`, if present, resolves to an existing step
   - `end` steps carry no outgoing transitions
   
   Violations raise `CacaoSemanticError`.

Both error classes derive from `CacaoParseError` so callers can catch the
family in one place.

## AST shape

```
Playbook
├── (CACAO root fields: type, spec_version, id, name, created_by, ...)
├── workflow: Mapping[str, WorkflowStep]   (read-only)
├── playbook_variables: Mapping[str, Variable]
└── x_secops_ng: SecOpsExtensions
    ├── stable_id, content_version, maturity
    ├── compile_targets
    └── detection_refs / control_refs / telemetry_refs / metric_refs / sources

WorkflowStep
├── step_id, type (StepType enum), name, description
├── on_completion / on_success / on_failure / next_steps
├── commands (raw CACAO command dicts — emitter-specialised)
├── agent, targets, in_args, out_args
├── step_variables
├── x_secops_ng: StepSecOpsExtensions
└── extra: any CACAO step fields the AST doesn't model — preserved verbatim
```

Every node is a frozen dataclass and every nested mapping is wrapped in
`MappingProxyType`, so an emitter cannot accidentally mutate a playbook
another emitter is reading concurrently.

CACAO step fields that aren't modelled explicitly land in
`WorkflowStep.extra`, so an emitter that wants richer translation can opt
in without forcing a parser change.

## What it does NOT do

- It does **not** emit any target-specific artefact. That is the job of
  `compilers/n8n/emit.py`, `compilers/temporal/emit.py`, and
  `compilers/langgraph/emit.py`.
- It does **not** resolve `x_secops_ng.*_refs` against the rest of the
  content model. Stable-ID joins are validated by the content linter,
  not the parser — keeping the parser free of file-system assumptions
  about the surrounding content tree.
- It does **not** load secrets, contact external services, or perform any
  I/O beyond reading the playbook file passed to `parse_file()` and the
  bundled schema.

## Tests

`tests/compilers/_shared/test_cacao_parser.py` exercises the parser against
the `vuln_intake.cacao.json` fixture and covers schema failures, semantic
invariants, frozen-ness, and `extra`-field preservation. Run with:

```
pytest tests/compilers/_shared -q
```
