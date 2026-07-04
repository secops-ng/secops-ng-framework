# docs/deploy

Deployment guides for running SecOps-NG on infrastructure you operate.

The framework itself is portable structure — CACAO playbooks under
`content/`, deterministic compilers under `compilers/`, worked
examples under `examples/`. The guides in this directory cover how
to take those emitted artifacts and run them on real infrastructure
under real regulatory posture.

## Guides

- [`sovereign-quickstart.md`](sovereign-quickstart.md) — end-to-end
  path for running one playbook on EU-sovereign infrastructure using
  the Temporal reference target. Provisioning, EU-resident inference,
  compile, wire, verify the audit trail.

## Where else to look

- [`../quickstart/README.md`](../quickstart/README.md) — target-agnostic
  local quickstart (n8n, Temporal, LangGraph).
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — the four-layer runtime
  the emitted artifacts compile into.
- [`../sovereignty/`](../sovereignty/) — the sovereignty posture the
  deployment guides enforce.

Contributions welcome — see [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md).
