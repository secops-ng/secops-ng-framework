# Quickstart

Clone the framework, compile the reference playbook into the orchestrator you
already run, and see the first operator-actionable output — inside thirty
minutes on a clean machine.

This guide is written for a practitioner who has never seen SecOps-NG before.
It picks `phishing_triage` as the worked example because it is the most
complete playbook shipped in `content/` — a CACAO v2 source, three
reference-compiled emissions (n8n, Temporal, LangGraph), and a cookbook entry
that ties the topology to the operator's own runtime.

If you get stuck, the [`docs/cookbook/`](../cookbook/) walkthroughs and the
[GitHub Discussions](https://github.com/secops-ng/secops-ng-framework/discussions)
board are the two places to look before opening an issue.

## 1. Prerequisites

The framework itself is Python; the orchestrator you compile *into* is your
choice. You need:

- **Python 3.11 or newer** and `git`.
- A working checkout of one of the three reference targets:
  - **n8n** — Docker is the simplest path: `docker run -it --rm --name n8n
    -p 5678:5678 docker.n8n.io/n8nio/n8n`. n8n is open source (Sustainable
    Use Licence); self-hosting on EU sovereign infrastructure (Hetzner,
    OVHcloud, Scaleway, Nebul) is a deployment choice you make at install
    time, not a vendor lock-in.
  - **Temporal** — the Temporal CLI ships a dev server:
    `brew install temporal` (macOS) or the [CLI install
    instructions](https://docs.temporal.io/cli#install) for Linux, then
    `temporal server start-dev`. Same sovereignty story: Temporal is MIT
    licensed and self-hostable.
  - **LangGraph** — a Python package installed alongside the framework's
    dev extras (see step 2). LangGraph runs as a Python process; hosting
    it on EU sovereign infrastructure is a deployment choice, not a
    provider decision.

You only need **one** of the three to complete the quickstart. Pick the one
closest to what you already run in production.

## 2. Clone and install

```bash
git clone https://github.com/secops-ng/secops-ng-framework.git
cd secops-ng-framework
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env               # local only; never commit this file
```

Sanity-check that the toolchain works:

```bash
python -m pytest -q                # unit + smoke tests, ~1000 pass
python -m tools.hygiene_linter --min-severity LOW
```

Green on both means the framework is installed and the forward-public hygiene
floor holds on your checkout. If either fails on a clean install, that is a
bug — open an issue with the failing output.

## 3. Pick a playbook

Every portable playbook lives under `content/playbooks/<workflow>/` as a
CACAO v2 JSON document alongside its mappings and README. We use
`phishing_triage` throughout the rest of this guide because it exercises the
full framework: CACAO source, three compile targets, a cookbook narrative,
and a golden-parity test suite under `tests/examples/phishing_triage/`.

The canonical source you will compile from:

```
content/playbooks/phishing_triage/playbook.cacao.json
```

Read the co-located `README.md` in that folder for the scenario, the
regulatory anchors (NIS2, DORA, GDPR), and the operator-supplied bindings
the emitted artifacts leave for you to wire.

## 4. Compile and run

The three reference compilers are deterministic: same input bytes in, same
output bytes out. Pre-emitted worked examples are committed under
`examples/{n8n,temporal,langgraph}/phishing_triage/` so you can inspect the
output without running the compiler. To regenerate from source, pick your
target below.

### n8n (no-code)

The n8n emitter produces a workflow JSON your n8n instance imports directly.

```bash
PYTHONPATH=. python -m tools.compile \
  content/playbooks/phishing_triage/playbook.cacao.json \
  --target n8n \
  --out /tmp/phishing_triage.n8n.json
```

Then in your n8n UI:

1. Open the workflows list and choose **Import from File**.
2. Select `/tmp/phishing_triage.n8n.json` (or the pre-emitted
   `examples/n8n/phishing_triage/workflow.n8n.json`).
3. n8n loads the phishing-triage topology as Set-node placeholders wired
   into the CACAO transitions. The workflow is **inactive** by default.

The first operator-actionable output is the workflow graph itself: nodes for
ingestion, enrichment (email security gateway, URL sandbox, attachment
sandbox), intent classification, and the response branches — each carrying
the CACAO `in_args`/`out_args` contract and the `x_secops_ng` reference
bundles (control, detection, telemetry, metric) as editable assignments.
Binding the Set nodes to your own connectors is the integration step you
own.

### Temporal (durable code)

The Temporal emitter produces a Python workflow module that runs against
`temporalio`.

```bash
temporal server start-dev &        # in a separate terminal
PYTHONPATH=. python -m compilers.temporal \
  content/playbooks/phishing_triage/playbook.cacao.json \
  --out /tmp/phishing_triage.temporal.py
```

Open `/tmp/phishing_triage.temporal.py` (or the committed
`examples/temporal/phishing_triage/workflow.temporal.py`). The first
operator-actionable output is the Python workflow class itself: a
deterministic activity DAG mirroring the CACAO topology, with activity
placeholders for each step. Register those activities against your own
worker to run it end-to-end; the placeholder bodies raise
`NotImplementedError` on purpose so an unbound artifact fails loudly rather
than silently doing nothing.

### LangGraph (agentic)

The LangGraph emitter produces a target-neutral GraphSpec plus a typed
state-bindings module. A hand-written `assemble.py` shows how the two combine
into a runnable `StateGraph`.

```bash
PYTHONPATH=. python -m compilers.langgraph.emit \
  content/playbooks/phishing_triage/playbook.cacao.json \
  > /tmp/phishing_triage.graph_spec.json

# Or, to see the whole assembled example:
python examples/langgraph/phishing_triage/assemble.py
```

The first operator-actionable output is the compiled `StateGraph`: nodes
bound to `@tool`-decorated wrappers, conditional edges honouring the CACAO
branch labels, and an `AGENTIC_HOOK` slot where you plug an LLM provider that
matches your sovereignty posture. As with the other targets, the `@tool`
bodies raise `NotImplementedError` until you wire them to real connectors.

## 5. Verify

Run the phishing-triage golden and per-target parity suites:

```bash
python -m pytest tests/examples/ -k phishing_triage -q
```

Expected output ends with a green summary line, roughly:

```
25 passed in 0.9s
```

Twenty-five checks pass: CACAO schema validity, byte-parity between the
committed worked-example artifacts and a fresh regeneration, per-target
structural invariants (n8n node graph, Temporal DAG, LangGraph GraphSpec
edges), and the mappings alignment against NIS2 / DORA / GDPR anchors.

If any test fails on a clean checkout, that is a bug worth reporting.

## 6. Next steps

- Read [`docs/cookbook/`](../cookbook/) for end-to-end walkthroughs of the
  phishing-triage playbook per target — narrative that ties the emitted
  artifact to the operator hand-off contract.
- Read [`docs/contributing/`](../contributing/) if you want to add a
  playbook, a mapping, or a compiler improvement. First-time contributors
  should start at [`docs/contributing/first-contribution.md`](../contributing/first-contribution.md).
- If you are running the framework in your environment, add yourself to
  [`USED-BY.md`](../../USED-BY.md). The registry is community-owned,
  self-attested, and the shared public signal of adoption the commons runs
  on.
- Bring questions to
  [GitHub Discussions](https://github.com/secops-ng/secops-ng-framework/discussions).
  The **Deployments** category is the right place for stuck-on-integration
  questions; **Ideas** is where playbook proposals start their life.

## Sovereignty note

The framework ships portable structure, not runtime state. No telemetry, no
execution traces, and no identifying flows reach this repository or the
SecOps-NG project from your compiled artifacts. The orchestrator you run —
n8n, Temporal, LangGraph, or a community-contributed target — is yours; the
infrastructure it runs on is yours. The commons ships the structure, you own
the data plane.
