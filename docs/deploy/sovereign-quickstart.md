# Sovereign Quickstart — Nebul + Mistral + Temporal

> **Stale notice (restructure landing):** This guide assumes the previous
> runtime-shipping layout (the `src/secops_ng/` package, `workflows/`,
> `patterns/`). After the content-first restructure the repo no longer
> ships those trees. A content-aware sovereign-deployment guide is
> queued; until it lands, treat this document as historical reference
> for sovereign-hosting topology only.

> **Audience.** Security engineers who already read Terraform and Docker
> Compose without help, but who have not yet operated an agentic stack
> in production. The goal of this guide is to get a single
> SecOps-NG worker running end-to-end on EU-sovereign infrastructure —
> sovereign compute, a sovereign-hosted language model, a durable
> Temporal cluster — and to take one posture-audit workflow from
> input to recommended action, with the full audit trail intact.

> **Scope.** A reference deployment, not a production blueprint.
> Hardening for high-assurance environments (key management, network
> segmentation, evidence retention, redundancy across regions) is out
> of scope for this document. Treat the output of this guide as the
> "smallest thing that proves the stack works on sovereign infra,"
> and grow it from there.

> **Sovereignty stance.** Every component here is selectable from the
> community sovereign-providers KB. The defaults below favour
> EU-resident hosting and EU-domiciled legal entities. You are
> expected to re-evaluate the providers against your own regulatory
> posture before you put real findings through this pipeline.

---

## 1. What you are deploying

Three layers, all under your operational control:

```
┌──────────────────────────────────────────────────────────────┐
│  Workflow plane     LangGraph + DSPy (Python, in-process)    │
│                     posture-audit / vulnerability-triage     │
├──────────────────────────────────────────────────────────────┤
│  Durability plane   Temporal cluster                         │
│                     (workflow history, retries, replay)      │
├──────────────────────────────────────────────────────────────┤
│  Inference plane    Mistral (sovereign-hosted) OR            │
│                     local Llama on sovereign GPU             │
├──────────────────────────────────────────────────────────────┤
│  Compute plane      Sovereign cloud (Nebul / Scaleway /      │
│                     OVHcloud / Hetzner / Exoscale)           │
└──────────────────────────────────────────────────────────────┘
```

The framework code is provider-agnostic. Sovereignty is enforced by
*where you run the VMs and which inference endpoint you wire up* —
not by anything inside the Python package.

---

## 2. Prerequisites

### 2.1 Operator side

- A workstation with `git`, `python>=3.11`, `docker` (or `podman`),
  and `terraform>=1.6`.
- An SSH key registered with whichever sovereign provider you choose.
- The `temporal` CLI (`brew install temporal` / `apt install temporal`
  / GitHub release). The CLI doubles as a one-process dev server,
  which we use later for smoke-testing before deploying the cluster.

### 2.2 Cloud side

Pick exactly one compute provider from the community KB
(`secops-ng-deployment/sovereign-providers-kb/providers/`). The
short table below summarises the current sovereign-score floor; full
provenance, ownership chain, and DPA notes live in the KB entries
themselves. Re-read those entries before commitment — scores move as
the Researcher refreshes evidence.

| Provider   | Score | Sovereignty notes                                           |
|------------|------:|-------------------------------------------------------------|
| Scaleway   |  100  | FR-anchor; HDS, ISO 27001:2022; SecNumCloud in-process.     |
| OVHcloud   |   —   | FR-domiciled; pin to FR/DE/PL/GB regions in the DPA.        |
| Hetzner    |   —   | DE GmbH; pin to Nuremberg / Falkenstein / Helsinki.         |
| Exoscale   |   —   | CH-anchor (GDPR-adequate); zones in AT/DE/BG/HR available.  |
| Nebul      |   25  | NL; AI/GPU positioning. STUB — DPA + subprocessors pending. |
| IONOS      |   —   | DE-parent but US subsidiary exists; explicit down-rank.     |

> Reading the KB. Each provider file carries a `sovereign_score`,
> a `last_verified` date, and a `notes` block describing the
> jurisdictional anchor. Treat the score as a floor under active
> research, never as a verdict. The KB lives in the deployment
> repo because it is operational knowledge, not a public claim.

For the rest of this guide we use **Nebul** as the compute anchor
(its public positioning is EU-sovereign GPU/AI compute, suitable for
the same machine carrying both Temporal and a local Mistral / Llama
runtime). If you pick a different provider, the shape is identical —
substitute the Terraform provider block and the SSH user.

### 2.3 Inference side

You have two paths. Both are sovereign-resident.

**Path A — Mistral on a sovereign endpoint.** Use a Mistral model
served from an EU-hosted inference platform (the Scaleway Generative
APIs surface or an equivalent EU-resident managed endpoint exposing
the OpenAI chat-completions wire shape). You provide the framework
with `LLM_BASE_URL`, `LLM_REGION`, and an API key supplied at
runtime through your platform's secret manager.

**Path B — Local Llama on the sovereign VM.** Run an open-weight
Llama model directly on the GPU you provisioned in §3. The framework
talks to it over the same OpenAI-compatible wire shape (vLLM /
text-generation-inference / llama.cpp's server mode all expose this).
This path requires zero cross-border traffic for inference but pins
GPU choice to whatever the sovereign provider rents you.

The framework does not care which one you pick. The choice is purely
a sovereignty / cost / latency trade-off, made in your runbook.

---

## 3. Provision

This section is intentionally minimal — enough Terraform to bring up
one VM. Replace the provider block with whichever sovereign cloud
you chose; the rest of the resource shape stays the same.

```hcl
# infra/main.tf
terraform {
  required_version = ">= 1.6"
  required_providers {
    # Example: a generic OpenStack-compatible provider. Several
    # sovereign clouds expose OpenStack APIs (Scaleway via Cloud
    # Native, OVHcloud Public Cloud). For Nebul, swap in the
    # provider published by your account team.
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

Apply, then wait for SSH:

```bash
terraform init
terraform apply -auto-approve
ssh ubuntu@$(terraform output -raw worker_ip)
```

> Right-sizing. For the smoke test in §5 a 16 GB / 4 vCPU VM is
> enough if you are using Mistral via a managed sovereign endpoint
> (Path A). For local Llama (Path B) on the same host, give yourself
> a single L40S / L4 / equivalent — anything that runs a 7-8B model
> at acceptable latency.

---

## 4. Configure

All configuration lives in `~/secops-ng/.env` on the worker. The
framework's `pydantic_settings` loader expects this file at the
working directory by default. **No secrets have committed defaults.**

### 4.1 Install the framework

```bash
sudo apt update && sudo apt install -y python3.12-venv git
git clone https://github.com/secops-ng/secops-ng-framework.git ~/secops-ng
cd ~/secops-ng
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

### 4.2 Bring up Temporal

For the smoke test we use the single-binary dev server; for the
durable cluster we use the published Temporal Docker Compose layout
(see §4.4).

```bash
# Smoke test only — ephemeral, in-memory.
temporal server start-dev --ui-port 8233 &
```

Visit `http://<worker_ip>:8233` to confirm the Temporal UI is up.
Tunnel over SSH if the worker has no public web port.

### 4.3 Wire up inference

Edit `.env`:

```ini
# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=secops-ng

# Observability
LOG_LEVEL=INFO

# Inference — choose ONE path, leave the others empty.

# Path A: Mistral on a sovereign managed endpoint (OpenAI-compatible).
SECOPS_NG_DSPY_MODEL=openai/mistral-small-latest
LLM_BASE_URL=https://<sovereign-endpoint>/v1
LLM_REGION=fr-par
OPENAI_API_KEY=                # injected at runtime, never committed

# Path B: Local Llama via vLLM / TGI / llama.cpp server on this host.
# SECOPS_NG_DSPY_MODEL=openai/llama-3.1-8b-instruct
# LLM_BASE_URL=http://127.0.0.1:8000/v1
# LLM_REGION=on-host
# OPENAI_API_KEY=local-placeholder
```

> Secret hygiene. `OPENAI_API_KEY` is the variable name DSPy /
> LiteLLM expect for any OpenAI-wire-shape endpoint, including a
> sovereign Mistral one. It is **not** a key for OpenAI. Inject it
> from your secret store (cloud-init `runcmd`, systemd
> `EnvironmentFile=`, HashiCorp Vault agent, the provider's secret
> manager) — never check the populated `.env` into git.

### 4.4 (Optional) Bring up the durable Temporal cluster

The dev server is fine for the smoke test, but it loses history on
restart. For anything you intend to operate, swap it for the
Compose stack published by Temporal. A minimal layout on the same
worker VM:

```bash
git clone https://github.com/temporalio/docker-compose.git ~/temporal-compose
cd ~/temporal-compose
# Pin to the docker-compose-postgres-12.yml layout for a single-node
# Postgres-backed history store. Read the upstream README first —
# the configuration matters more than the install command.
docker compose -f docker-compose-postgres-12.yml up -d
```

For real durability you want history + visibility on managed Postgres
(your sovereign cloud's managed-database service), and the worker
process supervised by `systemd` rather than left under `nohup`.
That progression belongs in a runbook, not this quickstart.

---

## 5. Smoke test — one posture-audit run

The framework ships with a cookbook example under `workflows/` that
exercises the full LangGraph + DSPy + Temporal-adjacent path on a
single finding. We use it here as the smoke test.

### 5.1 Run the worker

In one terminal on the VM:

```bash
cd ~/secops-ng
. .venv/bin/activate
python -m secops_ng.worker
```

You should see, in order:

```
connecting to Temporal at localhost:7233
worker listening on task queue 'secops-ng-default'
```

### 5.2 Drive a single triage through the graph

In a second terminal on the same VM:

```bash
cd ~/secops-ng
. .venv/bin/activate
python workflows/vulnerability_triage/example.py
```

A successful run prints something like:

```
finding_id          = VULN-DEMO-0001
severity_label      = critical
rationale           = Stack buffer overflow in X.509 verification on
                      an internet-facing gateway; pre-auth remote
                      reachability and known PoC make this critical.
recommended_action  = page-on-call
audit_trail         = ('ingest:VULN-DEMO-0001',
                       'classify:critical',
                       'recommend:page-on-call')
```

The `audit_trail` is the artifact that matters for the regulatory
baseline. Every state transition leaves a tuple entry; the DSPy
`rationale` field is preserved verbatim so a reviewer can read the
model's stated reasoning later. That property is what the framework
exists to give you — the LLM call is just one node in a deterministic
graph, and the graph is what your auditors get to inspect.

### 5.3 Confirm Temporal sees the worker

`http://<worker_ip>:8233` → *Task Queues* → `secops-ng-default`.
You should see one poller registered. The dev server will not yet
have history rows for the triage example (the cookbook example
invokes the graph directly), but the worker registration is
sufficient to confirm the Temporal side of the stack is live.

To exercise Temporal end-to-end, run the skeleton workflow client
included with the framework once it is wired (see
`src/secops_ng/workflows/skeleton.py` and the issues tracker for the
client harness). The skeleton path produces durable history rows
visible in the UI.

---

## 6. Troubleshoot

### 6.1 The worker cannot reach Temporal

```
temporalio.service.RPCError: failed to connect to all addresses
```

- The dev server is bound to `127.0.0.1:7233` by default. If the
  worker runs in Docker on the same host, point it at the host
  network or run Temporal on `0.0.0.0:7233` (dev server flag
  `--ip 0.0.0.0`).
- `TEMPORAL_HOST` in `.env` must match the address Temporal is
  actually listening on. Mismatches here are the single most common
  failure on first run.

### 6.2 DSPy raises `InvalidRequestError` on the classification call

- `LLM_BASE_URL` is missing or wrong — DSPy falls back to the public
  OpenAI endpoint, which (a) is not sovereign and (b) will reject
  your key.
- `SECOPS_NG_DSPY_MODEL` does not match a model the sovereign
  endpoint actually serves. Check the endpoint's `/v1/models` route.
- `OPENAI_API_KEY` is unset. Even for local Llama you must supply a
  non-empty placeholder so the OpenAI-wire client constructs.

### 6.3 `severity_label` round-trips as `(no rationale provided)`

The DSPy adapter sometimes serialises the prediction as a single
JSON blob into one output field. The library catches the common
shapes; if you see this regularly with your sovereign endpoint,
open an issue with one example payload and the model name — the
adapter list is small and explicit on purpose.

### 6.4 Local Llama is too slow for interactive use

- Move to a quantised build (`Q5_K_M` or `Q4_K_M` for 7-8B
  parameters is the sweet spot on a single L40S).
- Cache the model on a local volume — the cold-start cost from
  pulling weights over the network dwarfs everything else.
- For batch posture audits run the classifier with a higher
  concurrency under a Temporal activity, not from the cookbook
  script. The cookbook is single-shot by design.

### 6.5 The recommended action is wrong for your environment

`_ACTION_BY_SEVERITY` in `secops_ng.workflows.vulnerability_triage`
is deliberately plain Python (not a DSPy module) so that policy
review does not require LM expertise. Fork the action map, keep the
diff small, and route the new mapping through your own workflow
template under `workflows/`. Do not edit the library map in place —
it is the shared default the rest of the commons starts from.

---

## 7. What you have, what you do not

You have:

- A worker process on EU-sovereign compute, talking to a Temporal
  durability plane and a sovereign-resident inference endpoint.
- One posture-audit workflow that runs end-to-end with a complete
  audit trail per finding.
- An `.env` shape and a Terraform skeleton that you can copy into a
  real runbook.

You do not yet have:

- Network policy, key management, or evidence retention configured.
- A history / visibility store that survives a Postgres restart.
- A real ingestion path — the cookbook script feeds one synthetic
  finding. Wiring SIEM / scanner output is the next step.
- Multi-region failover. Sovereignty pinning makes that more
  interesting; pick your jurisdiction set first.

Each of those is a separate playbook. Track them in the issues on
this repository as you reach them, and bring patterns back into the
commons when they generalise.

---

## 8. References

- Framework architecture: `docs/ARCHITECTURE.md`
- Foundational design notes: `docs/FOUNDATION.md`
- Cookbook templates: `workflows/`
- Sovereign-providers KB: deployment repository,
  `sovereign-providers-kb/providers/`
- Temporal: <https://docs.temporal.io>
- LangGraph: <https://langchain-ai.github.io/langgraph/>
- DSPy: <https://dspy.ai>

Contributions improving this guide are welcome — see
`CONTRIBUTING.md`. Sovereignty notes that contradict the KB should
land in the KB first and propagate here second.
