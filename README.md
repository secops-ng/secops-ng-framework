# SecOps-NG

**Portable SecOps content, structure, and metrics — compile to the
orchestrator you already run.**

SecOps-NG is a community-driven project that publishes the *content* layer
of security operations — playbooks, detections, control mappings, telemetry
shapes, and operational metrics — as portable, vendor-neutral artifacts.
Reference compilers translate those artifacts into runnable form for the
orchestrators teams already operate.

It is maintained as a digital commons: built in the open, owned by no single
vendor, and designed for organisations that need to meet European
regulatory baselines without locking their playbooks to one runtime.

## What is SecOps-NG

SecOps-NG is **not** a SOAR, not a workflow runtime, and not an agent
framework. It is a **content and structure layer that sits above the
existing open standards**, plus reference compilers that emit ready-to-run
definitions for three launch orchestrator targets.

The content model is built on standards that already exist:

| Layer        | Standard                | What we contribute                                  |
|--------------|-------------------------|-----------------------------------------------------|
| Response     | CACAO v2 (OASIS)        | A growing library of portable response playbooks    |
| Detection    | Sigma                   | Curated references — we author no detection rules   |
| Controls     | OSCAL + D3FEND          | Control mappings to NIS2 / GDPR / ISO 27001         |
| Telemetry    | OCSF                    | The canonical event shape every playbook expects in |
| Measurement  | KPI / KRI catalog       | Operational and risk metrics, defined once          |

Every artifact in this repository is plain YAML / JSON / Markdown. The
primary output of SecOps-NG is **content**, not a runtime.

## Compile targets

A response playbook should be writeable once and runnable wherever the
operator already runs workflows. SecOps-NG ships reference compilers for
three launch targets:

- **n8n** — for teams that already run n8n for automation.
- **Temporal** — for teams that need durable, replayable, deterministic
  execution.
- **LangGraph** — for teams building agentic response loops with explicit
  graph state.

Compilers for **MindStudio, Make, Zapier, StackAI, and CrewAI** are out of
launch scope and expected to land as community contributions over time.

The compilers consume the same canonical artifact and emit
orchestrator-native definitions. The artifact is the source of truth; the
emitted definition is the build output.

## Why this shape

Security operations content has been trapped in vendor playbook formats
for two decades. Every migration between SOAR vendors, every move from
on-prem to cloud, every rebuild after an acquisition rewrites the same
playbooks in a new dialect.

SecOps-NG bets on the standards that already exist (CACAO for response,
Sigma for detection, OSCAL/D3FEND for controls, OCSF for telemetry) and
fills the gap above them with a coherent content library plus the
glue to compile that content into whatever runtime an operator chose for
unrelated reasons.

The split is deliberate:

- **Sigma** is detection only. We *reference* Sigma rules; we do not
  rewrite detection logic.
- **CACAO** is the portable response standard. Playbooks live here.
- **OSCAL + D3FEND** carry the control and technique mappings.
- **OCSF** is the telemetry shape every playbook reads.

## Sovereign deployment

The content layer is runtime-neutral, but most operators reading this work
under European regulatory baselines (NIS2, GDPR, DORA). The deployment
guidance section is therefore opinionated:

- The reference compile targets all have EU-hostable runtimes:
  self-hosted n8n, self-hosted Temporal clusters, and LangGraph executed
  inside any EU-resident process.
- The content artifacts are AI-provider neutral — model choice belongs at
  the runtime layer, never baked into a playbook.
- All credentials are injected at runtime by the executing orchestrator —
  never embedded in a published playbook, never committed.
- Recommended hosting bias: on-premises or EU-resident clouds
  (e.g. Nebul, OVHcloud, Scaleway, Hetzner).

This is not a compliance product. It is a content commons that makes
compliant architectures cheaper to build.

## Repository layout

| Path             | What lives there                                                       |
|------------------|------------------------------------------------------------------------|
| `content/`       | Canonical artifacts — playbooks, detections, controls, telemetry, metrics, mappings |
| `compilers/`     | Reference compilers that emit orchestrator-native definitions          |
| `schemas/`       | JSON Schema for every portable artifact shape                          |
| `tools/`         | CLI helpers (hygiene linter, validate, compile wrapper)                |
| `docs/`          | Long-form documentation (quickstart, concepts, compilers, sovereignty) |
| `examples/`      | End-to-end demos: one playbook compiled to all three reference targets |
| `tests/`         | Schema validation, compiler tests, hygiene-linter tests                |

## Status

**Early. Community-driven. Pre-1.0.**

The content scaffold is in place; the compile targets are landing
incrementally. We are deliberately holding the API stable only at the
artifact layer (YAML/JSON shapes) and treating the compilers as evolving
until each target has been validated against real operator use.

If you are running security operations and want to help shape this, open
a discussion.

## Quickstart

```bash
git clone https://github.com/secops-ng/secops-ng-framework.git
cd secops-ng-framework
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # then edit
pytest
```

See `docs/quickstart/` once the launch compilers land for the
end-to-end walkthrough ("clone, pick orchestrator, ship in days").

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

SecOps-NG is open core. The content artifacts, control mappings, and
reference compilers are and will remain Apache-2.0. The project has no
commercial offering and is not operated as a business.
