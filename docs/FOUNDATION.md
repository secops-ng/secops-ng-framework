# Foundation — the four non-negotiable properties

SecOps-NG ships portable content (CACAO playbooks, OSCAL/D3FEND control
mappings, OCSF data shapes, KPI/KRI catalogue) plus reference compilers
that emit that content into the orchestrator an operator already runs.
The project is framework-agnostic by design — n8n, Temporal, and
LangGraph are reference targets, not the engine.

Across every artifact, every compiler, and every workflow this
repository ships, four properties are non-negotiable. A change that
relaxes any of them is out of scope for this repository, regardless of
how small the diff looks.

## 1. Auditability

A regulator, an operator, or a community reviewer must be able to
reconstruct what a workflow did, why it did it, and from which artifact,
without privileged access to the maintainers' infrastructure.

Concretely:

- Portable artifacts (CACAO playbooks, OSCAL controls, OCSF shapes) are
  the source of truth. Compiled orchestrator definitions are build
  outputs and must be reproducible from the artifact.
- Every boundary value crossing a node, tool, or agent is a typed
  contract — unknown fields fail loudly rather than degrade silently.
- Mappings to regulatory regimes (NIS2, DORA, CRA, GDPR, ISO 27001,
  SOC 2) cite the control they implement, not the other way around.

Auditability is the property NIS2 Article 21 expects of the data plane
and what makes the project usable inside a regulated environment.

## 2. Determinism

The same artifact compiled with the same compiler version produces the
same orchestrator definition, byte for byte. The same workflow executed
against the same inputs produces the same control flow and the same
telemetry shape.

Concretely:

- Per-example byte-parity golden tests under `tests/examples/` are not
  optional. A compiler change that moves golden output is intentional
  and lands in the same PR as the test update.
- Random ordering, wall-clock drift, and uncaptured environment
  configuration are bugs.
- LLM-facing steps go through a versioned, diff-reviewable signature
  (the prompt is code), and tests pin the LM to a deterministic stub.

Determinism is what makes a workflow reviewable as text, replayable
under audit, and safe to ship as a Digital Commons artifact.

## 3. Sovereignty

The project favours EU-hostable runtimes and EU-resident inference
endpoints. Sovereignty is encoded in the artifacts the project ships,
not as a deployment-time afterthought.

Concretely:

- Reference deployment paths target sovereign-cloud runtimes (e.g.
  Nebul, OVHcloud, Scaleway, Hetzner). Vendor lock-in to a
  non-EU-resident control plane is a design defect, not a trade-off.
- LM backends are pluggable and the default configuration assumes the
  operator pins inference to an EU-resident endpoint.
- AI-provider neutrality is enforced at the artifact layer — a CACAO
  playbook does not name a non-EU model in its body.

See [`docs/sovereignty/`](sovereignty/README.md) for the current
sovereign-runtime guidance.

## 4. Operability

The output of this project is something an operator can adopt without
adopting the maintainers' stack. That is the whole point of being
framework-agnostic.

Concretely:

- Three reference compile targets — n8n (no-code), Temporal (durable
  code), LangGraph (agentic) — each one of three, not the engine.
- The portable artifact remains the source of truth; the emitted
  orchestrator definition is a build output an operator can regenerate
  at any time.
- Documentation is read-first: the same contributor who finds this
  document via `AGENTS.md` should be able to follow
  [`docs/quickstart/`](quickstart/README.md) without needing to ask
  the maintainers anything.

Operability is what keeps the project useful as a Digital Commons —
adoption does not require buying anything, replacing the operator's
stack, or trusting the maintainers' infrastructure.

## See also

- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — historical four-layer
  runtime context (carries a stale notice; superseded by the
  content-first model).
- [`docs/concepts/content-model.md`](concepts/content-model.md) — the
  current shape of what this repository ships.
- [`ROADMAP.md`](../ROADMAP.md) — feature definitions and status.
- [`GOVERNANCE.md`](../GOVERNANCE.md) — maintainer roles and decision
  process.
