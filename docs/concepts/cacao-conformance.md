# CACAO 2.0 conformance

The playbooks under `content/playbooks/` are published as CACAO v2 documents.
That claim is checked mechanically against the JSON Schema files the OASIS
CACAO Technical Committee publishes, vendored unmodified under
[`schemas/vendor/cacao-2.0/`](../../schemas/vendor/cacao-2.0/README.md).

```bash
python -m tools.cacao_conformance --show 3
python -m tools.cacao_conformance --baseline tests/content/cacao_conformance_baseline.json
```

## The ratchet

`tests/content/cacao_conformance_baseline.json` records, per document, how
many errors the official schema set reports. CI fails when any count changes:

- **more errors** is a regression and blocks the change;
- **fewer errors** is progress, recorded by re-writing the baseline in the same
  pull request (`--write-baseline`), so the floor only moves down.

A new playbook is expected to arrive with zero errors. The
[`_template`](../../content/playbooks/_template/) scaffold is excluded from the
walk; it has its own conformance lane.

## Two readings of the same schema

The upstream files declare JSON Schema Draft-07 and also use the
`unevaluatedProperties` keyword, which Draft-07 validators ignore. The default
reading (`--dialect declared`) is Draft-07: what the files say they are, and
what downstream CACAO tooling applies. `--dialect 2020-12` evaluates the root
document under the newer dialect so non-standard top-level properties are also
reported; it is informational and reports a superset.

## What conformance does not mean

Passing the schema does not make a playbook executable by a given
orchestrator; each compile target documents what it consumes. Conformance
means any CACAO-aware tool can parse, validate, visualise and exchange the
document as the standard intends.
