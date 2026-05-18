# Posture Audit Walkthrough

A single-page walkthrough for running the sovereign Posture Audit end to end
against the committed sample fixtures. By the end of it you will have a
Temporal dev server running, a worker serving the audit surface, and a
rendered markdown report on your terminal that matches the committed golden
output.

The Posture Audit is the first non-skeleton workflow in the framework. It
takes a declared cloud-footprint manifest, cross-references each workload
against a sovereign-provider knowledge base, and emits a markdown verdict.
The walkthrough below uses the sample manifest and sample KB that ship in
`tests/fixtures/`; swap them for your own once the round-trip works.

## Prerequisites

- Python 3.11+ on the path.
- The Temporal CLI. Install it once from
  [temporal.download/cli.sh](https://temporal.download/cli.sh) or follow
  [docs.temporal.io/cli](https://docs.temporal.io/cli). Nothing else is
  required — `temporal server start-dev` runs an in-process server with no
  external dependencies.
- A POSIX shell. Three terminals or three `tmux` panes.

## 1. Clone and install

```bash
git clone https://github.com/secops-ng/secops-ng-framework.git
cd secops-ng-framework
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

The editable install puts the `secops_ng` package, the worker entrypoint,
and the `scripts/submit_audit.py` operator client on your path.

## 2. Start the Temporal dev server

In your first terminal:

```bash
temporal server start-dev
```

This binds `localhost:7233` (the frontend the worker and client connect to)
and serves the Temporal Web UI at <http://localhost:8233>. Leave it
running.

## 3. Run the worker with the audit surface enabled

In a second terminal, point `POSTURE_AUDIT_KB_PATH` at the sample KB and
start the worker:

```bash
POSTURE_AUDIT_KB_PATH=tests/fixtures/audit_kb.json python -m secops_ng.worker
```

`POSTURE_AUDIT_KB_PATH` is the opt-in switch. When it is set, the worker
registers `PostureAuditWorkflow` alongside the skeleton workflow and serves
the two audit activities (`evaluate_workload`, `render_report`) backed by a
file-backed adapter over the KB you point it at. When the variable is
unset the worker behaves exactly as before — only the skeleton surface is
served. The opt-in keeps the audit's dependency graph (the manifest model,
the KB adapter, YAML) out of the hot path for workers that only need the
skeleton.

The worker logs `worker listening on task queue 'secops-ng-default'` once
it is connected and ready to take work.

## 4. Submit the sample manifest

In a third terminal, submit the manifest:

```bash
python scripts/submit_audit.py tests/fixtures/sample_manifest.yaml
```

The submission client loads the manifest from disk, connects to the same
Temporal frontend, starts a `PostureAuditWorkflow`, signals each workload
in declaration order via `add_workload`, signals `finalize`, waits for the
workflow to complete, and writes the rendered markdown report to stdout.

## 5. View the rendered report

The report appears on stdout immediately after the workflow completes. For
the committed sample fixtures it matches
[`tests/fixtures/sample_report.md`](../tests/fixtures/sample_report.md)
byte for byte — three workloads, one Sovereign, one Partial, one
Non-sovereign — and you can diff against it to confirm the round-trip:

```bash
python scripts/submit_audit.py tests/fixtures/sample_manifest.yaml \
    | diff - tests/fixtures/sample_report.md
```

Empty diff output means the workflow, the activities, the KB adapter, and
the renderer all agree on what a sovereign verdict looks like for the
sample workloads.

You can also follow the run in the Temporal Web UI at
<http://localhost:8233> — pick the workflow you just started and inspect
the signal history, the activity timeline, and the result. The audit is a
durable state machine: if you kill the worker mid-run and restart it, the
workflow resumes from the last signal.

## Configuration reference

The worker and the submission client both honour the same two environment
variables, and they must agree:

| Variable               | Default              | Used by         |
|------------------------|----------------------|-----------------|
| `TEMPORAL_ADDRESS`     | `localhost:7233`     | worker + client |
| `TEMPORAL_TASK_QUEUE`  | `secops-ng-default`  | worker + client |

Only the worker reads `POSTURE_AUDIT_KB_PATH`. The submission client does
not need a KB — it only sends signals and reads the report from the
workflow result.

## Going further

- Edit `tests/fixtures/sample_manifest.yaml` to declare your own workloads
  (kind, declared provider, region, data classification) and re-submit.
  The KB at `tests/fixtures/audit_kb.json` decides the verdict for each
  declared provider; extend that file to teach the audit about additional
  sovereign and non-sovereign providers.
- The replay tests in `tests/test_posture_audit_e2e.py` exercise the same
  workflow without needing a live server — they use Temporal's
  time-skipping test environment. Run them with `pytest -k posture_audit`.
- The audit's pieces are reusable. The KB adapter is a `Protocol`; the
  renderer is a pure function; the workflow body is signal-driven and
  deterministic. Compose them into the next sovereignty-aware workflow
  rather than starting from scratch.

## Troubleshooting

- *Worker logs `connecting to Temporal at localhost:7233` and then hangs.*
  The dev server is not up yet, or the addresses do not match. Confirm
  `temporal server start-dev` is running and that `TEMPORAL_ADDRESS` is
  the same in both terminals.
- *The submission client prints nothing and the run is stuck.* The worker
  is up but the audit surface is not registered. Confirm
  `POSTURE_AUDIT_KB_PATH` is set in the worker's environment and that the
  file exists.
- *The report differs from `tests/fixtures/sample_report.md`.* The
  committed fixture is the contract. A diff means the workflow, the
  activities, the KB, or the renderer drifted — open an issue with the
  diff attached so the regression gets a test before a fix.
