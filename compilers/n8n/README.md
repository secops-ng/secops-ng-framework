# compilers/n8n/

CACAO v2 playbook → n8n workflow JSON emitter.

Reference compiler #1 in the SecOps-NG project. Reads a parsed
[CACAO v2](https://www.oasis-open.org/standard/cacao-v2-0/) playbook
(via `compilers._shared.cacao_parser`) and emits an n8n workflow JSON
object suitable for `n8n import:workflow` or the n8n REST API.

## Quickstart

```bash
python -m tools.compile content/playbooks/vuln_intake/playbook.cacao.json \
    --target n8n --out /tmp/vuln_intake.n8n.json
```

Or programmatically:

```python
from compilers._shared.cacao_parser import parse_file
from compilers.n8n import emit

playbook = parse_file("path/to/playbook.cacao.json")
workflow = emit(playbook)  # dict ready for json.dumps
```

## Translation table

| CACAO step type     | n8n node                                   | Notes |
| ------------------- | ------------------------------------------ | ----- |
| `start`             | `n8n-nodes-base.manualTrigger`             | Playbook variables become initial values on the trigger. |
| `end`               | `n8n-nodes-base.noOp`                      | Terminal marker; no execution side effect. |
| `action` (http-api / openc2-http) | `n8n-nodes-base.httpRequest`     | `url`, `method`, `headers`, `body` mapped. |
| `action` (bash / sh) | `n8n-nodes-base.executeCommand`           | `command` interpolated for `__var__` tokens. |
| `action` (other / none) | `n8n-nodes-base.noOp`                  | Placeholder; lossy note recorded. |
| `playbook-action`   | `n8n-nodes-base.executeWorkflow`           | Sub-playbook target is operator-managed. |
| `if-condition`      | `n8n-nodes-base.if`                        | `on_success` = true branch, `on_failure` = false branch. |
| `while-condition`   | `n8n-nodes-base.if` + back-edge            | Lossy; n8n has no native while. |
| `switch-condition`  | `n8n-nodes-base.switch`                    | CACAO's `cases` mapping (case value → step ids) compiles to one rule + one output port per case, comparing the interpolated `switch` variable against the case value; the legacy `{when, label}` list shape is still accepted. A switch with neither shape emits an empty rule set plus a lossy note. |
| `parallel`          | `n8n-nodes-base.merge`                     | n8n parallelism is implicit (multi-edge fan-out). |

## Variables

CACAO `playbook_variables` are surfaced on the manual trigger as initial
values and references inside command bodies (`__finding_id__`) are
rewritten to n8n expressions (`{{$workflow.variables.finding_id}}`) so the
operator can edit them from the n8n UI without re-importing.

## Determinism

Same AST in → byte-identical JSON out (serialised with `json.dumps(..., indent=2)`,
no `sort_keys`). The golden test on the sibling card pins this.

## Known gaps (lossy)

The emitter records lossy translations on `workflow.meta.secops_ng_notes`
so the reviewer sees the gaps without diffing the source playbook.

Known gaps that hit every playbook:

- **If/while expressions.** CACAO v2 does not require a machine-readable
  expression on condition steps. The emitter inserts a placeholder
  comparator the operator fills in n8n. Authors who want round-trip
  fidelity can put a string under `extra.condition` and the emitter will
  carry it through.
- **Parallel fan-in.** A `parallel` step compiles to a `merge` node
  downstream of the fan-out. Verify the merge mode (combine / append /
  passthrough) suits your data shape.
- **Multi-command actions.** Only the first command on an `action` step
  is mapped. Split multi-command actions into separate steps.
- **Unknown command types.** Anything outside `{http-api, openc2-http,
  bash, sh, shell}` is emitted as a no-op placeholder. The note tells
  the operator which command type was skipped.

## Node version pins

The emitter pins `typeVersion` per node type to the versions stable since
n8n 1.0. Operators on older n8n lines may need to re-pin. The pins are
constants at the top of `emit.py`; a future n8n version bump is a
one-line change.

## CLI

`secops-ng compile <playbook> --target n8n [--out PATH]` is implemented
as `python -m tools.compile`. The packaging stub that wires
`secops-ng compile` as a console script lands when the framework reaches
its first installable version.
