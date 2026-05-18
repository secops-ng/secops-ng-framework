# SecOps-NG

**Durable, auditable, sovereignty-respecting security operations agents.**

SecOps-NG is a community-driven framework for building next-generation security
operations workflows on top of open, durable execution primitives. It is
maintained as a digital commons — built in the open, owned by no single vendor,
and designed for organisations that need to operate security workflows under
European data sovereignty and regulatory constraints.

## What is SecOps-NG

SecOps-NG provides reusable building blocks for *agentic* security workflows
(vulnerability triage, incident enrichment, evidence collection, alert
deduplication, response orchestration) that survive process restarts, host
failures, and partial cloud outages.

Where traditional SOAR platforms encode workflows as fragile, vendor-specific
playbooks, SecOps-NG treats each workflow as a **durable state machine** —
deterministic, replayable, and inspectable end-to-end.

## Why Sovereignty

The EU NIS2 Directive raises the bar on incident reporting, supply-chain
hygiene, and operational resilience for essential and important entities.
Meeting that bar means knowing — and being able to prove — where your security
telemetry lives, which models touched it, and what an agent decided on your
behalf.

SecOps-NG is designed from day one to run on **sovereign infrastructure**:

- On-premises or EU-resident clouds (e.g. Nebul, OVHcloud, Scaleway, Hetzner)
- Self-hosted Temporal clusters — no managed-SaaS lock-in required
- Pluggable LLM backends (local, EU-hosted, or hyperscaler) selected at
  runtime, never baked into the workflow definition
- All credentials injected at runtime via environment variables or vault —
  never committed, never embedded

This is not a compliance product. It is a toolkit that makes compliant
architectures cheaper to build.

## Architecture

Four pillars, each chosen for a specific reason:

| Layer        | Tool          | Why                                                  |
|--------------|---------------|------------------------------------------------------|
| Durability   | Temporal.io   | Workflows survive restarts, replays are deterministic|
| Reasoning    | LangGraph     | Explicit graph state — auditable agent transitions   |
| Contracts    | Pydantic v2   | Strict, typed I/O at every tool boundary             |
| Optimisation | DSPy          | Prompts and policies are *programs*, not strings     |

The split is deliberate: **Temporal owns time and state**, **LangGraph owns
control flow**, **Pydantic owns the type system**, and **DSPy owns the
learnable bits**. None of them is forced to do another's job.

## Status

**Early. Community-driven. Pre-1.0.**

The scaffold is in place; the interesting workflow templates are landing
incrementally. We are deliberately holding off on a stable API until the
durable-execution patterns have been validated against real NIS2-relevant use
cases by more than one operator. If you are running security operations under
NIS2 and want to help shape this, please open a discussion.

## Running the skeleton

The canonical durable workflow lives at
`src/secops_ng/workflows/skeleton.py`. It is the template every future
agentic workflow descends from: signal-driven, deterministic body,
side effects pushed into activities, replay-clean.

To run it against a local Temporal dev server:

```bash
# Terminal 1 — start a local Temporal server (install the CLI from
# https://docs.temporal.io/cli once; nothing else is required).
temporal server start-dev

# Terminal 2 — run the worker. TEMPORAL_ADDRESS and TEMPORAL_TASK_QUEUE
# are both optional; defaults are localhost:7233 and secops-ng-default.
python -m secops_ng.worker
```

Drive the workflow with the `temporal` CLI (or the Python client):

```bash
temporal workflow start \
  --task-queue secops-ng-default \
  --type SkeletonWorkflow \
  --workflow-id demo-run-1

temporal workflow signal --workflow-id demo-run-1 --name add_item --input '"alpha"'
temporal workflow signal --workflow-id demo-run-1 --name add_item --input '"bravo"'
temporal workflow signal --workflow-id demo-run-1 --name finish
temporal workflow result --workflow-id demo-run-1
```

The replay-based tests in `tests/test_skeleton_replay.py` exercise the
same workflow without needing a live server — they use Temporal's
time-skipping test environment.

## Running the sovereign posture audit

The posture audit (`src/secops_ng/workflows/posture_audit.py`) is the
first non-skeleton workflow. It cross-references a declared cloud
footprint manifest against a sovereign-provider knowledge base and
emits a markdown report. The worker opts into serving it when
`POSTURE_AUDIT_KB_PATH` points at a KB JSON file — when the variable is
unset, the worker behaves exactly as before. A thin operator client at
`scripts/submit_audit.py` loads a manifest, signals each workload to a
`PostureAuditWorkflow`, finalizes the run, and prints the rendered
report to stdout. End-to-end with the committed sample fixtures:

```bash
# Terminal 1 — Temporal dev server.
temporal server start-dev

# Terminal 2 — worker with the audit surface enabled.
POSTURE_AUDIT_KB_PATH=tests/fixtures/audit_kb.json python -m secops_ng.worker

# Terminal 3 — submit the sample manifest, render the report.
python scripts/submit_audit.py tests/fixtures/sample_manifest.yaml
```

## Quickstart

> Full docs are pending. Expect rough edges.

```bash
git clone https://github.com/secops-ng/secops-ng-framework.git
cd secops-ng-framework
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # then edit
pytest
```

Documentation will live at `docs/` (TBD) and at the project site once the
community settles on hosting. Until then, the source — particularly the
`workflows/` examples — is the documentation.

## Contributing & governance

This is a community project. Four documents describe how to take part:

- [CONTRIBUTING.md](CONTRIBUTING.md) — dev setup, commit style, DCO
  sign-off, and the PR process.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — what we expect of one
  another, adapted from the Contributor Covenant 2.1.
- [GOVERNANCE.md](GOVERNANCE.md) — how decisions get made, who has
  merge rights, and how that will evolve as the project grows.
- [SECURITY.md](SECURITY.md) — vulnerability disclosure policy and
  contact.

All contributions require a DCO sign-off (`git commit -s`). We follow
conventional commits.

Security issues: see [SECURITY.md](SECURITY.md). Please do **not** open
public issues for vulnerabilities.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

SecOps-NG is open core. The framework, contracts, and reference workflows are
and will remain Apache-2.0. The project has no commercial offering and is not
operated as a business.
