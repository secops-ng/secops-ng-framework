# n8n compiler

Reference compiler #1 in the SecOps-NG framework. Compiles a parsed CACAO
v2 playbook into an [n8n](https://n8n.io/) workflow JSON document — the
same shape n8n produces when you export a workflow from its UI. The
output is import-ready: pipe it to `n8n import:workflow` or `POST` it to
the n8n REST API.

n8n is the no-code reference target. It's the most accessible of the
three (n8n / Temporal / LangGraph) and the right one to reach for when
the operator wants to **see, edit, and run** a playbook in a UI without
writing code.

## Quickstart

From the framework repo root:

```bash
python -m tools.compile \
    content/playbooks/vuln_intake/playbook.cacao.json \
    --target n8n \
    --out /tmp/vuln_intake.n8n.json
```

That produces a `.json` file you can import into n8n:

```bash
n8n import:workflow --input=/tmp/vuln_intake.n8n.json
```

…or upload via the REST API:

```bash
curl -X POST "$N8N_URL/rest/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "content-type: application/json" \
    --data @/tmp/vuln_intake.n8n.json
```

Credentials, schedules, and runtime secrets stay in n8n. The compiled
workflow is **content only** — connectivity is the operator's job.

### Programmatic use

```python
from compilers._shared.cacao_parser import parse_file
from compilers.n8n import emit

playbook = parse_file("path/to/playbook.cacao.json")
workflow = emit(playbook)  # plain dict, json-serialisable
```

`emit_file()` is the same with a `Path` sink:

```python
from compilers.n8n import emit_file
emit_file("path/to/playbook.cacao.json", "/tmp/out.n8n.json")
```

## Supported CACAO features

The emitter walks the AST returned by `compilers._shared.cacao_parser`
and maps each step type to an n8n node:

| CACAO step type           | n8n node                              | Notes |
| ------------------------- | ------------------------------------- | ----- |
| `start`                   | `n8n-nodes-base.manualTrigger`        | Playbook variables become initial values on the trigger. |
| `end`                     | `n8n-nodes-base.noOp`                 | Terminal marker; no execution side effect. |
| `action` (http-api / openc2-http) | `n8n-nodes-base.httpRequest`  | `url`, `method`, `headers`, `body` mapped. |
| `action` (bash / sh / shell) | `n8n-nodes-base.executeCommand`    | `command` interpolated for `__var__` tokens. |
| `action` (other / none)   | `n8n-nodes-base.noOp`                 | Placeholder; lossy note recorded. |
| `playbook-action`         | `n8n-nodes-base.executeWorkflow`      | Sub-playbook target is operator-managed. |
| `if-condition`            | `n8n-nodes-base.if`                   | `on_success` = true branch, `on_failure` = false branch. |
| `while-condition`         | `n8n-nodes-base.if` + back-edge       | Lossy: n8n has no native while loop. |
| `switch-condition`        | `n8n-nodes-base.switch`               | Cases sourced from `extra.cases` (best-effort). |
| `parallel`                | `n8n-nodes-base.merge`                | n8n parallelism is implicit (multi-edge fan-out); merge node handles fan-in. |

### Variables

CACAO `playbook_variables` are surfaced on the manual trigger as initial
values. References to `__variable__` in command bodies are rewritten to
n8n expressions (`{{$workflow.variables.variable}}`) so the operator can
edit them from the UI without re-importing the workflow.

### SecOps-NG metadata

Every compiled workflow carries content provenance on `meta.secops_ng`:

```json
{
  "secops_ng": {
    "stable_id": "playbook.vuln_intake@v1",
    "content_version": "0.1.0",
    "maturity": "draft",
    "source_playbook_id": "playbook--…"
  }
}
```

This is how a downstream registry or KPI dashboard knows which content
version a running workflow came from.

### Determinism

Same AST in → byte-identical JSON out. The output is serialised with
`json.dumps(..., indent=2)` and a single trailing newline. The golden
test under `tests/compilers/n8n/` pins this against the `vuln_intake`
fixture and fails on drift.

Re-generate the golden after an intentional emitter change:

```bash
python -m tools.compile \
    tests/compilers/_shared/fixtures/vuln_intake.cacao.json \
    --target n8n \
    --out tests/compilers/n8n/golden/vuln_intake.n8n.json
```

Commit the new golden alongside the emitter change so reviewers see
both diffs in the same PR.

## Known gaps

n8n cannot model every CACAO concept. Each lossy translation is logged
on `workflow.meta.secops_ng_notes` so a reviewer or operator sees the
gap without diffing the source playbook.

Gaps that hit every playbook of the affected shape:

- **If / while expressions.** CACAO v2 does not require a machine-readable
  expression on condition steps. The emitter inserts a placeholder
  comparator the operator fills in n8n. Authors who want round-trip
  fidelity can put a string under `extra.condition` and the emitter
  carries it through.
- **While loops.** n8n has no native while; the emitter emits an `if`
  node plus a back-edge to approximate it. Tight loops should be
  re-expressed as iterators driven by an upstream data source.
- **Parallel fan-in.** A `parallel` step compiles to a `merge` node
  downstream of the fan-out. Verify the merge mode (combine / append /
  passthrough) suits your data shape.
- **Multi-command actions.** Only the first `command` on an `action`
  step is mapped to a node. Split multi-command actions into separate
  steps for full fidelity.
- **Unknown command types.** Anything outside
  `{http-api, openc2-http, bash, sh, shell}` becomes a `noOp`
  placeholder. The lossy note tells the operator which command type
  was skipped.
- **Credentials.** The emitter never embeds secrets or credentials. HTTP
  nodes expect the operator to attach an n8n credential record in the
  UI after import.
- **Schedules.** CACAO playbooks describe content, not cadence. If a
  playbook should run on a schedule, the operator swaps the manual
  trigger for an n8n schedule trigger after import.
- **Switch cases.** CACAO has no first-class switch case shape yet, so
  the emitter pulls cases from `extra.cases` when present and emits a
  pass-through switch otherwise.

## Node version pins

The emitter pins `typeVersion` per node type to versions stable since
n8n 1.0. Operators running older n8n lines may need to re-pin. The pins
are constants at the top of `compilers/n8n/emit.py`; a future n8n
version bump is a one-line change.

## CLI surface

`secops-ng compile <playbook> --target n8n [--out PATH]` is implemented
as `python -m tools.compile`. The console-script entry point that wires
`secops-ng compile` directly lands when the framework reaches its first
installable version.

## See also

- `compilers/n8n/README.md` — the module-level reference (translation
  table, internals).
- `tests/compilers/n8n/` — golden test and regeneration recipe.
- `docs/compilers/README.md` — index of all reference compilers.
