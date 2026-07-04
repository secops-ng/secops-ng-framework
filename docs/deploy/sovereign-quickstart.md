# Sovereign quickstart — Temporal on EU-resident infrastructure

Take one SecOps-NG playbook end-to-end on infrastructure you operate
under EU jurisdiction. This guide picks the Temporal reference target
because durable-code execution has the strongest alignment with the
audit-trail and evidence-retention posture EU regulation asks for
(NIS2, DORA, GDPR): workflow history is deterministic, replayable, and
lives in a database you control.

Audience: a security engineer who reads Terraform and Docker Compose
without help, has never operated an agentic stack before, and wants
the smallest thing that proves the stack works on EU-sovereign
infrastructure. Hardening for high-assurance environments (key
management, network segmentation, evidence retention, multi-region
failover) is out of scope here — pick this guide up, then grow it
into your own runbook.

If you have not yet read [`docs/quickstart/README.md`](../quickstart/README.md),
start there for a local, target-agnostic tour of the framework. This
guide assumes you already know what "compile a CACAO playbook into an
orchestrator artifact" means.

## 1. What you are deploying

Three layers, all under your operational control:

```
┌──────────────────────────────────────────────────────────────┐
│  Playbook plane     content/playbooks/<workflow>/             │
│                     CACAO v2 source of truth                  │
├──────────────────────────────────────────────────────────────┤
│  Compile plane      compilers/temporal (deterministic emit)   │
│                     examples/temporal/<workflow>/ (mirror)    │
├──────────────────────────────────────────────────────────────┤
│  Runtime plane      Temporal cluster + Python worker          │
│                     (workflow history, retries, replay)       │
├──────────────────────────────────────────────────────────────┤
│  Inference plane    Mistral (EU-resident endpoint) OR         │
│                     local open-weight model on your VM        │
├──────────────────────────────────────────────────────────────┤
│  Compute plane      Sovereign cloud (Nebul / OVHcloud /       │
│                     Scaleway / Hetzner / …)                   │
└──────────────────────────────────────────────────────────────┘
```

The framework code is provider-agnostic. Sovereignty is enforced by
*where you run the Temporal cluster, where you host the model, and
which regions you pin* — not by anything inside the framework itself.
The commons ships portable structure; the runtime is yours.

## 2. Prerequisites

### 2.1 Local

- A workstation with `git`, `python>=3.11`, and `docker` (or `podman`).
- The `temporal` CLI. Install per the upstream [CLI docs](https://docs.temporal.io/cli#install)
  — the CLI doubles as a one-process dev server, useful for smoke
  tests before you provision a durable cluster.
- An SSH key registered with whichever sovereign provider you choose.

### 2.2 Sovereign compute

Pick one EU-resident compute provider. The community
sovereign-providers KB (maintained in the deployment repository) is
the source of truth for jurisdictional anchor, ownership chain, DPA
status, and evidence provenance — re-read the entry before commitment
because posture moves as evidence refreshes. The canonical EU options
tracked in the KB today:

- **Nebul** — NL-anchored, GPU/AI positioning; suitable for a single
  host carrying both Temporal and a local inference model.
- **OVHcloud** — FR-domiciled; pin to FR/DE/PL regions in the DPA.
- **Scaleway** — FR-anchored; HDS and ISO 27001:2022 certifications.
- **Hetzner** — DE GmbH; pin to Nuremberg / Falkenstein / Helsinki.

The KB carries the current sovereign-score floor and jurisdictional
notes per entry. Do not hardcode vendor cost, SLA numbers, or marketing
claims here or in your runbook — link to the KB entry and re-verify before you
commit real workloads. This guide uses the shape of the deployment,
not a specific vendor decision; substitute the provider block in
your Terraform / cloud-init as needed.

### 2.3 EU-resident inference

Two paths. Both keep inference inside EU jurisdiction.

**Path A — Mistral on an EU-resident managed endpoint.** Any endpoint
exposing the OpenAI chat-completions wire shape from an EU-domiciled
provider works. You give the framework `LLM_BASE_URL`, `LLM_REGION`,
and an API key supplied at runtime through your secret store.

**Path B — Local open-weight model on your sovereign VM.** Run an
open-weight model (Mistral, Llama, Qwen, or similar) directly on the
GPU you provisioned. The framework talks to it over the same
OpenAI-compatible wire shape (vLLM, text-generation-inference, or
`llama.cpp` server mode all expose this). Zero cross-border traffic
for inference; you pin GPU choice to whatever the sovereign provider
rents you.

OpenAI, Anthropic, or any US-hosted managed endpoint is **not** a
sovereign default. Do not wire one into a runbook that claims EU
sovereignty posture.

## 3. Provision

Bring up one VM. Replace the provider block with whichever sovereign
cloud you chose; the shape stays the same.

```hcl
# infra/main.tf
terraform {
  required_version = ">= 1.6"
  required_providers {
    # Example: a generic OpenStack-compatible provider. Several
    # sovereign clouds expose OpenStack APIs. For a provider without
    # an OpenStack surface, swap in the provider your account team
    # publishes.
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = "~> 1.54"
    }
  }
}

variable "region"         { type = string }     # e.g. "fr-par-1"
variable "ssh_public_key" { type = string }

resource "openstack_compute_keypair_v2" "operator" {
  name       = "secops-ng-operator"
  public_key = var.ssh_public_key
}

resource "openstack_compute_instance_v2" "worker" {
  name        = "secops-ng-worker-01"
  image_name  = "Ubuntu 24.04 LTS"
  flavor_name = "gpu.l40s-1"      # or any sovereign GPU flavour
  key_pair    = openstack_compute_keypair_v2.operator.name

  network { name = "default" }

  tags = [
    "project=secops-ng",
    "sovereignty=eu",
    "workload=temporal+inference",
  ]
}

output "worker_ip" {
  value = openstack_compute_instance_v2.worker.access_ip_v4
}
```

```bash
terraform init
terraform apply -auto-approve
ssh ubuntu@$(terraform output -raw worker_ip)
```

Right-sizing: 16 GB / 4 vCPU is enough if you use Mistral via an
EU-resident managed endpoint (Path A). For a local model on the same
host (Path B), give yourself a single L40S / L4 / equivalent —
anything that runs a 7-8B model at acceptable latency.

## 4. Clone the framework

```bash
sudo apt update && sudo apt install -y python3.12-venv git
git clone https://github.com/secops-ng/secops-ng-framework.git ~/secops-ng
cd ~/secops-ng
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env         # local only; never commit this file
```

Sanity-check:

```bash
python -m pytest -q
python -m tools.hygiene_linter --min-severity LOW
```

Green on both means the framework and the forward-public hygiene
floor are healthy on this VM.

## 5. Pick a playbook

Every portable playbook lives under `content/playbooks/<workflow>/` as
a CACAO v2 document alongside its mappings and README. The simplest
entry points for a first sovereign deployment:

- `content/playbooks/phishing_triage/` — inbound suspicious-email
  triage. Full compile artifacts under `examples/{n8n,temporal,langgraph}/phishing_triage/`
  and a golden-parity test suite under `tests/examples/phishing_triage/`.
- `content/playbooks/vuln_intake/` — vulnerability intake and
  classification. Same three-target coverage.

This guide uses `phishing_triage` because it exercises the full
framework: CACAO source, three compile targets, a cookbook narrative,
and byte-parity goldens.

## 6. Compile

The Temporal emitter is deterministic — same input bytes in, same
output bytes out. The committed worked example under
`examples/temporal/phishing_triage/` is a mirror of what a fresh
compile produces. To regenerate from the canonical playbook:

```bash
cd ~/secops-ng
. .venv/bin/activate

PYTHONPATH=. python -m tools.compile \
  content/playbooks/phishing_triage/playbook.cacao.json \
  --target temporal \
  --out /tmp/phishing_triage.temporal.py
```

Or just re-run the committed regeneration script and confirm the
output is byte-identical:

```bash
./examples/temporal/phishing_triage/regenerate.sh
git diff --exit-code examples/temporal/phishing_triage/workflow.temporal.py
```

The emitted `workflow.temporal.py` is a stub: activity signatures,
CACAO step topology, retry policies, OpenTelemetry spans carrying the
`secops_ng.step.*` attributes, and an audit-trail mirror. Activity
bodies raise `NotImplementedError` on purpose — an unbound artifact
fails loudly rather than silently doing nothing.

## 7. Wire it to a Temporal server

### 7.1 Smoke test (dev server)

For the first end-to-end pass, use the single-binary dev server. It
loses history on restart but proves the topology is live:

```bash
temporal server start-dev --ui-port 8233 &
```

Visit `http://<worker_ip>:8233` — the Temporal UI should be up.
Tunnel over SSH if the worker has no public web port.

### 7.2 Configure the framework

Edit `~/secops-ng/.env`:

```ini
# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=secops-ng

# Observability
LOG_LEVEL=INFO

# Inference — choose ONE path, leave the others empty.

# Path A: Mistral on an EU-resident managed endpoint.
SECOPS_NG_DSPY_MODEL=openai/mistral-small-latest
LLM_BASE_URL=https://<eu-resident-endpoint>/v1
LLM_REGION=fr-par
OPENAI_API_KEY=                # injected at runtime, never committed

# Path B: Local open-weight model via vLLM / TGI / llama.cpp server.
# SECOPS_NG_DSPY_MODEL=openai/mistral-7b-instruct
# LLM_BASE_URL=http://127.0.0.1:8000/v1
# LLM_REGION=on-host
# OPENAI_API_KEY=local-placeholder
```

Secret hygiene: `OPENAI_API_KEY` is the variable name the OpenAI-wire
client stack expects for any endpoint speaking that wire shape,
including an EU-resident Mistral one. It is **not** a key for OpenAI.
Inject it from your secret store (cloud-init `runcmd`, systemd
`EnvironmentFile=`, HashiCorp Vault agent, the provider's secret
manager) — never commit a populated `.env`.

### 7.3 Bind the activities

The stub `examples/temporal/phishing_triage/workflow.temporal.py`
carries one activity per CACAO step. Copy the file into your own
worker module (do not edit the mirror in the repo — it is regenerated
byte-for-byte from the CACAO source) and replace each `raise
NotImplementedError` body with a call into your operator runtime:

- `ingest_report` — fetch the reported email envelope from your email
  security platform (user-reported or mailbox-sweep).
- `enrich_headers_urls_attachments` — sender authentication (SPF /
  DKIM / DMARC), URL reputation against your posture, attachment
  static analysis.
- `classify_intent` — the DSPy signature that consults your
  EU-resident inference endpoint; classifies suspected phishing
  intent and preserves the model's rationale in the audit trail.
- `suppress_and_close` / `respond_*` — the response-branch actions
  keyed on intent.

Read `content/playbooks/phishing_triage/README.md` and the
co-located `mappings.yaml` for the OCSF telemetry shape, Sigma rule
references, and NIS2 / DORA / GDPR anchors each step should honour.
The cookbook walkthrough at `docs/cookbook/phishing_triage.md`
(if present) narrates the same topology target-by-target.

### 7.4 Run the worker

In one terminal on the VM:

```bash
cd ~/secops-ng
. .venv/bin/activate
python -m <your_module>.worker    # your worker registers the bound activities
```

You should see the worker connect to Temporal and register on
`secops-ng` task queue. Drive one report through the workflow from a
second terminal (either via the Temporal CLI or a small client
script) and confirm it runs to completion.

## 8. Verify the audit trail

The property that matters for the regulatory baseline is that every
workflow execution leaves a deterministic, replayable audit trail —
the LLM call is one step in a graph, not a black box.

Two places to look:

1. **Temporal UI** — `http://<worker_ip>:8233` → **Workflows** → your
   run. Each activity execution is a history event with input,
   output, retries, and elapsed time. Replay this history at any
   point and Temporal produces the same downstream events.
2. **OpenTelemetry spans** — the emitted stub wraps each activity in
   a span carrying `secops_ng.playbook.id`, `secops_ng.step.id`,
   `secops_ng.step.name`, and `secops_ng.compile.target`. Wire your
   worker to an EU-resident OpenTelemetry collector (Grafana Cloud
   EU, Aiven, self-hosted Tempo) and your evidence pipeline gets the
   same trace stream your reviewers can inspect later.

That is what the framework exists to give you. A reviewer can read
the CACAO playbook, the emitted stub, and the workflow history side
by side, and confirm the runtime did what the playbook said it would
do.

## 9. Durable cluster (production)

The dev server is fine for the smoke test; swap it for a durable
cluster before you route real reports. Two shapes work:

- **Self-hosted on the same sovereign VM.** Temporal publishes a
  Docker Compose layout at
  <https://github.com/temporalio/docker-compose>. Pin the
  Postgres-backed variant, use the sovereign provider's managed
  Postgres service for history + visibility, and supervise the worker
  process with `systemd`. Read the upstream README first — the
  configuration matters more than the install command.
- **Managed Temporal Cloud in EU.** Temporal Cloud offers EU-resident
  regions; check the current DPA and sub-processor list against your
  posture before committing. This shifts the durability plane to the
  provider but keeps the inference plane and the worker under your
  control.

Either way, the framework does not change — same emitted stub, same
task queue, same audit trail.

## 10. What you have, what you do not

You have:

- A worker process on EU-sovereign compute, talking to a Temporal
  durability plane and an EU-resident inference endpoint.
- One phishing-triage workflow that runs end-to-end with a
  deterministic audit trail per report.
- An `.env` shape, a Terraform skeleton, and a compile / regenerate
  pattern you can copy into your own runbook.

You do not yet have:

- Network policy, key management, or evidence retention configured.
- A history / visibility store that survives a database restart —
  the smoke-test path uses the ephemeral dev server.
- A real ingestion path — the emitted stub raises
  `NotImplementedError` until you wire it. Binding the SIEM / email
  security platform / ticketing connectors is the next step.
- Multi-region failover. Sovereignty pinning makes that more
  interesting; pick your jurisdiction set first, then design the
  topology across it.

Each of those is a separate playbook. Track them in the framework
issues and bring patterns back into the commons when they generalise.

## 11. Where to next

- [`docs/quickstart/README.md`](../quickstart/README.md) — the
  target-agnostic quickstart if you want to see the n8n or LangGraph
  paths before committing to Temporal.
- [`docs/cookbook/`](../cookbook/) — per-workflow walkthroughs that
  narrate the CACAO topology, the emitted artifact, and the
  operator-supplied bindings.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — the four-layer
  runtime the emitted artifacts compile into.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — the four non-negotiable
  properties (auditability, determinism, sovereignty, operability).
- [`docs/contributing/`](../contributing/) — if you find something
  the guide could do better, open a PR. Sovereignty notes that
  contradict the KB should land in the KB first and propagate here
  second.

## Sovereignty note

The framework ships portable structure, not runtime state. No
telemetry, no execution traces, no email content, and no identifying
flows reach this repository or the SecOps-NG project from your
compiled artifacts. The orchestrator you run is yours; the
infrastructure it runs on is yours. The commons ships the structure,
you own the data plane.
