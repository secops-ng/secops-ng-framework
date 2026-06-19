# Byte-parity testing for the three reference compilers

> Audience: contributors changing a compiler under `compilers/{n8n,temporal,langgraph}/`
> or the canonical CACAO content under `content/playbooks/`.

The repository ships a worked example for every cookbook workflow under
`examples/{n8n,temporal,langgraph}/<workflow>/`. The committed bytes are
guaranteed to be the **byte-for-byte output** of the reference compilers
applied to the canonical CACAO playbook. This is what we mean by
*byte-parity*.

There are two complementary gates that enforce this property.

## 1. pytest — fast local gate

`tests/examples/<workflow>/test_golden.py` re-runs the parser + emitter
in-process and asserts the rendered string equals the committed example
file. This is what you run locally:

```sh
python -m pytest tests/examples/
```

A failure prints the exact regenerate command for that workflow in the
assertion message.

## 2. `regenerate.sh --check` — CI gate

The top-level `regenerate.sh` orchestrates the per-example regeneration
scripts that live next to each worked example. It has three forms:

```sh
./regenerate.sh                          # regenerate every example
./regenerate.sh <target>                 # regenerate one whole target
./regenerate.sh <target> <workflow>      # regenerate one example
./regenerate.sh --check [<target> [<workflow>]]
```

The `--check` form is what CI uses. It:

1. Runs each per-example `regenerate.sh` into the worktree.
2. Diffs the result against the committed bytes (`git diff`).
3. Restores the committed bytes (`git checkout --`), so the worktree
   is left clean either way.
4. On any drift, prints a contributor-friendly line and exits non-zero:

```
BYTE-PARITY DRIFT in temporal/vuln_intake — run: ./regenerate.sh temporal vuln_intake
```

The CI lane (`.github/workflows/three-target-parity.yml`) fan-outs this
check across the M0 cookbook set × the three targets.

## Workflow: making a compiler change

1. Edit the compiler.
2. Run `python -m pytest tests/examples/` — it will fail on the
   workflows whose output changed.
3. Run `./regenerate.sh <target> <workflow>` for each affected pair
   (or just `./regenerate.sh` to regenerate everything).
4. `git add` the regenerated example files alongside your compiler
   change. Both belong in the same commit so the byte-parity guarantee
   is preserved at every point on `main`.
5. Re-run pytest. It should be green.
6. Open the PR. CI will re-run `regenerate.sh --check` across the
   matrix; if you missed a target/workflow pair it will be named
   explicitly in the failure.

## Workflow: making a CACAO content change

Same five steps as above — a content change can cascade into every
target's worked example. The `regenerate.sh` orchestrator without
arguments is the simplest sweep.

## Pitfalls

- **Forgetting to commit the regenerated example.** The committed
  example *is* the contract; the test asserts byte equality. If you
  change a compiler without regenerating, CI will fail and tell you so.
- **Hand-editing a worked example.** Don't. Edit the compiler or the
  canonical playbook. The example is generated, not authored.
- **OpenTelemetry dependency.** The Temporal and LangGraph emitters
  import the `opentelemetry` API namespace at module load. The CI lane
  installs it; if you're regenerating locally and hit `ModuleNotFoundError`,
  `python -m pip install opentelemetry-api opentelemetry-sdk` in the
  environment you run regenerate from.
