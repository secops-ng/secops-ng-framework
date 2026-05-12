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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions require a DCO
sign-off (`git commit -s`). We follow conventional commits.

Security issues: see [SECURITY.md](SECURITY.md). Please do **not** open public
issues for vulnerabilities.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

SecOps-NG is open core. The framework, contracts, and reference workflows are
and will remain Apache-2.0. The project has no commercial offering and is not
operated as a business.
