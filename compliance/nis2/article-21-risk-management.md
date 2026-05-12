# NIS2 Article 21 — Cybersecurity Risk-Management Measures

**Directive (EU) 2022/2555, Article 21 — Cybersecurity risk-management measures**

Article 21 is the operational heart of NIS2. Article 21(1) requires essential
and important entities to take **appropriate and proportionate technical,
operational and organisational measures** to manage the risks posed to the
security of network and information systems which those entities use for
their operations or for the provision of their services, and to prevent or
minimise the impact of incidents on recipients of their services and on
other services.

Article 21(2) lists **ten categories** of measures (a–j) that must be
included, based on an all-hazards approach. Each subsection below maps one
of those categories to the SecOps-NG framework.

The mapping is honest about scope: SecOps-NG is a **toolkit for agentic
security workflows**. It is not a full cybersecurity programme. Several of
the Article 21(2) categories are organisational or physical in nature and
the framework can only contribute partially. Where that is the case the
mapping says so plainly.

---

## 21(2)(a) — Policies on risk analysis and information system security

**Obligation:** policies on risk analysis and information system security.

**SecOps-NG contribution:**

- Pydantic-typed contracts at every tool boundary make the *information
  security posture of each workflow* machine-readable, which is a
  prerequisite for any meaningful policy enforcement.
- Workflow definitions live in version control, so policies-as-code is the
  default rather than an aspiration.

**Evidence stream:** `../evidence/risk-analysis/` — policy versions and
risk-analysis outputs.
<!-- coder:wire -->

**Gaps:** the framework does not author policies; it executes them.

---

## 21(2)(b) — Incident handling

**Obligation:** incident handling.

**SecOps-NG contribution:**

- The `workflows/` directory is built around incident-handling primitives:
  triage, enrichment, deduplication, response orchestration.
- Temporal durability ensures an incident workflow survives a responder
  going offline mid-incident.

**Evidence stream:** every incident workflow emits a deterministic timeline
to `../evidence/incidents/<workflow-id>/`.
<!-- coder:wire -->

**Gaps:** none structural; depth depends on which incident workflows the
operator adopts.

---

## 21(2)(c) — Business continuity, such as backup management and disaster recovery, and crisis management

**Obligation:** business continuity, including backup management, disaster
recovery, and crisis management.

**SecOps-NG contribution:**

- Temporal's durable execution model is itself a continuity property: a
  workflow does not lose state when a worker dies.
- The framework does **not** provide backup management; that is an
  infrastructure concern.

**Evidence stream:** workflow durability records (Temporal-native).

**Gaps:** backup management, DR drills, crisis-management exercises are out
of scope.

---

## 21(2)(d) — Supply chain security

**Obligation:** supply chain security, including security-related aspects
concerning the relationships between each entity and its direct suppliers
or service providers.

**SecOps-NG contribution:**

- The Sovereign Provider KB (`secops-ng-deployment` repository) is the
  community's structured record of which European providers it considers
  fit for purpose, with verifiable claims.
- Workflows that call external providers (LLM backends, threat-intel feeds)
  declare those dependencies in their Pydantic contracts, making the
  supply-chain surface machine-inspectable.

**Evidence stream:** `../evidence/supply-chain/dependencies-snapshot.json`
emitted per workflow execution.
<!-- coder:wire -->

**Gaps:** supplier contractual obligations are out of scope.

---

## 21(2)(e) — Security in network and information systems acquisition, development and maintenance, including vulnerability handling and disclosure

**Obligation:** security across the acquire-develop-maintain lifecycle,
including vulnerability handling and disclosure.

**SecOps-NG contribution:**

- The framework itself follows coordinated vulnerability disclosure
  (see `SECURITY.md` in the repository root).
- The reference `vulnerability_triage` workflow is purpose-built for the
  *consumption* side of this obligation.

**Evidence stream:** `../evidence/vulns/` — triage decisions and disclosure
timelines.
<!-- coder:wire -->

**Gaps:** SDLC controls for the operator's own code are out of scope.

---

## 21(2)(f) — Policies and procedures to assess the effectiveness of cybersecurity risk-management measures

**Obligation:** policies and procedures to assess the effectiveness of the
measures.

**SecOps-NG contribution:**

- DSPy-based optimisation gives the framework a native vocabulary for
  *measuring* whether a policy or prompt is working: every learnable policy
  is paired with a metric.
- Workflow replays make before/after comparisons trivially possible.

**Evidence stream:** `../evidence/effectiveness/` — metric snapshots per
policy version.
<!-- coder:wire -->

**Gaps:** the operator must define what "effective" means for their context.

---

## 21(2)(g) — Basic cyber hygiene practices and cybersecurity training

**Obligation:** basic cyber hygiene and cybersecurity training.

**SecOps-NG contribution:** out of technical scope. The framework provides
workflow walkthroughs that can be used as training material.

**Evidence stream:** none from the framework directly.

**Gaps:** hygiene programmes and training delivery are operator
responsibilities.

---

## 21(2)(h) — Policies and procedures regarding the use of cryptography and, where appropriate, encryption

**Obligation:** policies and procedures on the use of cryptography and,
where appropriate, encryption.

**SecOps-NG contribution:**

- Credentials are **never** baked into workflow definitions; all secrets are
  runtime-injected via environment variables or the operator's secret
  manager. See `.env.example` for the canonical pattern.
- Workflow-to-worker and worker-to-Temporal-cluster transport is operator
  configurable; the framework is opinionated that TLS termination must be
  under operator control on sovereign infrastructure.

**Evidence stream:** `../evidence/crypto/secret-handling-attestation.json`
per workflow execution.
<!-- coder:wire -->

**Gaps:** key-management lifecycle is the operator's responsibility.

---

## 21(2)(i) — Human resources security, access control policies and asset management

**Obligation:** human resources security, access control policies, asset
management.

**SecOps-NG contribution:**

- Per-tool Pydantic contracts make it explicit which capabilities a
  workflow exercises, which is a prerequisite for least-privilege
  enforcement.
- Workflow audit trails record who initiated each execution.

**Evidence stream:** `../evidence/access/` — per-execution caller identity
and capability list.
<!-- coder:wire -->

**Gaps:** HR processes and asset inventories are out of scope.

---

## 21(2)(j) — Use of multi-factor authentication or continuous authentication solutions, secured voice, video and text communications and secured emergency communication systems within the entity, where appropriate

**Obligation:** MFA / continuous auth, secured comms (voice/video/text),
secured emergency comms.

**SecOps-NG contribution:** out of direct technical scope. Workflows that
*orchestrate* MFA challenges or secure-comms invocations can be built on
the framework, but the framework does not provide MFA primitives itself.

**Evidence stream:** none from the framework directly.

**Gaps:** MFA, comms security, emergency-comms infrastructure are the
operator's responsibility.

---

## References

- Directive (EU) 2022/2555, Article 21(1)–(5).
- ENISA implementation guidance (where available) is consulted but not
  authoritative.
