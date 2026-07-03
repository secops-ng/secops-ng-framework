# Adding a compiled example

This guide walks through adding a new compiled example under
`examples/{n8n,temporal,langgraph}/<playbook>/` for an existing
playbook. It is the operational companion to
[`playbook-authoring.md`](playbook-authoring.md); read that first if
you are also adding the playbook itself.

**Scope note.** This guide is about *exercising* the existing
compilers. If you need a compiler feature that does not exist yet (a
new primitive, a new emitter for a new target), open an issue first —
compiler surface changes go through a design review before code.
Everything below assumes the primitives your playbook needs already
compile.

## 1. The three reference targets

SecOps-NG maintains three reference compile targets. Each is one of
three, not the engine. They exist to demonstrate that the portable
content is genuinely portable and to give operators a runnable starting
point in the orchestrator they already run.

| Target | Directory | Emits | Runtime story |
|---|---|---|---|
| **n8n** | `examples/n8n/<playbook>/` | `workflow.n8n.json` | Import into any n8n instance; no-code operator surface. |
| **Temporal** | `examples/temporal/<playbook>/` | `workflow.temporal.py` (+ activities) | Durable code; the workflow module runs under a Temporal worker. |
| **LangGraph** | `examples/langgraph/<playbook>/` | `graph_spec.json`, `state_bindings.py`, `assemble.py`, `_audit_mirror.py` | Agentic; assembles into a `StateGraph` at runtime. |

Every example directory carries three files in common — a `README.md`,
a mirrored `playbook.cacao.json` (byte-identical to the canonical), and
a `regenerate.sh` script that re-emits the target-specific artifacts
from that CACAO source.

## 2. Prerequisite: the playbook already exists

Adding an example only makes sense once
`content/playbooks/<playbook>/playbook.cacao.json` is present and the
canonical unit tests pass. If the playbook is still SKELETON (steps
are placeholders), the compiled example will inherit those placeholders
— that is fine, and is how we ship SKELETON + CORE in two PRs.

Confirm the playbook compiles at all before you start on the example
directory:

```bash
python -m tools.compile \
    content/playbooks/<playbook>/playbook.cacao.json \
    --target n8n \
    --out /tmp/probe.n8n.json
```

If that errors out, the fix belongs on the playbook, not the example.

## 3. Scaffold the example directory

Copy the layout from an existing example for the same target. `cra_cvd`
is the current reference and covers all three targets end-to-end:

```bash
# Pick your target and copy from cra_cvd as the model.
TARGET=n8n            # or temporal / langgraph
PLAYBOOK=<your-playbook>
mkdir -p examples/${TARGET}/${PLAYBOOK}
cp examples/${TARGET}/cra_cvd/regenerate.sh examples/${TARGET}/${PLAYBOOK}/
```

Then edit the copied `regenerate.sh` to point at your playbook's
canonical path. The three regenerate scripts have slightly different
shapes; the essentials are:

- **n8n:** mirror the canonical CACAO into the example directory, then
  run `python -m tools.compile <canon> --target n8n --out
  workflow.n8n.json`.
- **Temporal:** same mirror step, then `--target temporal --out
  workflow.temporal.py`.
- **LangGraph:** mirror the CACAO, then invoke
  `python -m compilers.langgraph.emit` to write `graph_spec.json`, run
  `python -m compilers.langgraph.state` to write `state_bindings.py`,
  and materialise `_audit_mirror.py` via
  `python -m compilers._shared.audit_mirror_cli`.

Copy the exact incantations from
`examples/{n8n,temporal,langgraph}/cra_cvd/regenerate.sh`; do not
re-derive them from memory.

## 4. Run regenerate and commit the outputs

`regenerate.sh` is idempotent and is committed alongside the artifacts
it emits. Run it once:

```bash
bash examples/${TARGET}/${PLAYBOOK}/regenerate.sh
```

The outputs — `workflow.n8n.json`, `workflow.temporal.py`,
`graph_spec.json`, `state_bindings.py`, `assemble.py`,
`_audit_mirror.py` (depending on target) — are committed. That is
deliberate: reviewers read the diff to catch emitter regressions, and
downstream users pull the emitted artifact directly without needing to
run a compiler.

The mirrored `playbook.cacao.json` in the example directory is
**byte-identical** to the canonical `content/playbooks/<playbook>/`
file. The regenerate script re-copies it every time; if the canonical
changes and you forget to re-run, the byte-parity test (§ 6) will fail.

## 5. Write the example README

Every example directory ships a short `README.md` that a first-time
user can follow. The template is:

```markdown
# <playbook> — <target> compiled example

The <target> materialisation of the `<playbook>` CACAO playbook. This
file exists to be imported into a running <target> instance; the
canonical playbook lives at `content/playbooks/<playbook>/`.

## Regenerating

Run `./regenerate.sh` from anywhere; paths are resolved relative to
the script.

## What is emitted

- `workflow.<ext>` — the target-specific artifact.
- `playbook.cacao.json` — mirror of the canonical CACAO source, kept
  byte-identical.

## Byte-parity

`tests/examples/test_<target>_<playbook>.py` asserts that
`regenerate.sh` produces exactly the committed files. If you change
the compiler or the canonical playbook, run regenerate and commit both
in the same PR.
```

Fill in the target and the playbook name; keep the file to one page.
The point is that a stranger can arrive, read it, and run the artifact.

## 6. The byte-parity golden test

Every example directory is anchored by a byte-parity test under
`tests/examples/`. The test does effectively:

```python
def test_<target>_<playbook>_bytes_match():
    expected = (EXAMPLES_DIR / "<target>" / "<playbook>" / "workflow.<ext>").read_bytes()
    actual   = compile_playbook(CANON_PATH, target="<target>")
    assert actual == expected
```

That test is what enforces the "the emitted artifact in the repo is
what the compiler produces today" contract. When you add a new example,
add the corresponding test file. See
[`byte-parity-testing.md`](byte-parity-testing.md) for the full pattern
and for how to update goldens intentionally when the compiler changes.

## 7. Local checks before opening the PR

```bash
# Regenerate everything you touched.
bash examples/${TARGET}/${PLAYBOOK}/regenerate.sh

# Byte-parity + wider test suite.
python -m pytest tests/examples/ tests/content/

# Hygiene linter.
python -m tools.hygiene_linter --min-severity LOW examples/${TARGET}/${PLAYBOOK}/
```

Green locally is the baseline; CI will run the same set plus the
per-target three-target-parity check under
`.github/workflows/three-target-parity.yml`.

## 8. Opening the PR

```bash
git checkout -b examples/<playbook>-<target>
git add examples/${TARGET}/${PLAYBOOK}/ tests/examples/
git commit -s -m "examples(<playbook>): <target> compiled example"
git push -u origin examples/<playbook>-<target>
```

PR template type: `new-content`. The reviewer looks at (in order) the
byte-parity test, the regenerate script for reproducibility, and the
README for a stranger's first-run experience. If you add all three
targets in one PR the review is proportionally longer; splitting per
target is welcome.

## 9. When something feels missing

If you hit a wall — a primitive you need that no target emits, an
emitter that produces incorrect output, an example that needs a
compiler feature that does not exist — that is a compiler surface issue,
not an example issue. Open a scoping issue against `compilers/` before
sinking hours into a workaround inside `examples/`. Compiler changes go
through a design conversation because they touch every downstream
consumer.

Welcome to the commons.
