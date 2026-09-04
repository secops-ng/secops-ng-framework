# it_security_support_agent — cookbook walkthrough

NIS2 Article 21(2)(b) front-line support-to-incident handoff. The
`playbook.it_security_support_agent@v1` CACAO playbook takes one
ticket-shaped IT/security support request per execution, classifies
it against the operator's policy, walks the declared automated-
resolution path against the operator's self-service surface, and
then materialises an **explicit** handoff envelope: every support
interaction MUST end with either an automated-resolution closure or
a confirmed handoff to a human responder — never a silent auto-close.
The per-execution interaction-evidence artifact is emitted against
the reused F-CP-02 incidents stream so the incident-handling KPI
surface counts handoffs exactly once on the same regulatory anchor
the F-WF-05 incident-management lifecycle discharges.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the
deterministic primitives package, the OpenTelemetry signal layer,
and the context-local `AuditTrail` mirror live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/it_security_support_agent/
├── README.md                    # workflow-local module tree
├── mappings.yaml                # OSCAL / D3FEND / OCSF / regulatory outbound refs
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.it_security_support_agent@v1)
└── primitives/
    ├── ingest.py                # ingest_support_request — canonicalise the inbound support-request record
    ├── classify.py              # classify_request — validate the closed classification verdict envelope
    ├── resolution.py            # attempt_automated_resolution — closed automated-resolution observation envelope
    ├── handoff.py               # escalate_with_human_handoff — first-class handoff envelope (fired or not)
    └── artifact.py              # emit_interaction_evidence — closed interaction-evidence record (F-CP-02 shape)
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, connectors, credentials, ticketing
sources, responder-queue endpoints — is the operator's data plane.

The CACAO source ships as JSON
(`content/playbooks/it_security_support_agent/playbook.cacao.json`);
both JSON and YAML are first-class inputs to the per-target
compilers. The JSON is the single source of truth, and each worked
example carries a byte-identical mirror at
`examples/{n8n,temporal,langgraph}/it_security_support_agent/playbook.cacao.json`.

## 2. CACAO topology and primitives binding

The playbook ships seven steps: one `start`, five `action`, one
`end`. Transitions are deterministic — every state has exactly one
`on_completion` successor, no conditional branching at this layer.
The handoff decision is encoded **inside** the
`escalate-with-human-handoff` step (the step ALWAYS runs and
materialises a closed handoff envelope carrying `handoff_fired`
accordingly) so the downstream interaction-evidence artifact can pin
the path taken explicitly, rather than as a conditional edge that
would erase the decision from the trace.

| Step suffix | Step                              | `core_body` binding                                                                  | Status |
|-------------|-----------------------------------|--------------------------------------------------------------------------------------|--------|
| `…00000002` | ingest-support-request            | `primitives.ingest.ingest_support_request`                                           | bound  |
| `…00000003` | classify-request                  | `primitives.classify.classify_request`                                               | bound  |
| `…00000004` | attempt-automated-resolution      | `primitives.resolution.attempt_automated_resolution`                                 | bound  |
| `…00000005` | escalate-with-human-handoff       | `primitives.handoff.escalate_with_human_handoff`                                     | bound  |
| `…00000006` | emit-interaction-evidence         | `compilers.<target>.evidence.emit_interaction_evidence_artifact_<target>` (adapter)  | bound  |

The five action steps are all bound; there are no absent-body seams
— the playbook is `stable` at `content_version` 1.0.0, the F-WF-12
ladder's first graduation. The interaction-evidence emitter is
a per-target adapter (n8n Code node, Temporal activity, LangGraph
node) that reuses the F-CP-02 incidents-schema
(`schemas/evidence/incidents.schema.json`) — the same shape
`playbook.incident_management@v1` writes against — with the
support-only closure branch carrying `classification.significant=false`
and the handoff branch carrying `classification.significant=true`.
No new evidence schema is introduced.

### 2.1 The classification verdict is operator policy

The classification-policy rule table this playbook validates against
is operator-supplied at runtime; the primitive re-validates the
closed verdict shape (`category` in {`informational`, `actionable`,
`incident-shaped`}, severity band, ordered `rule_ids`, opaque
`policy_version`) but does not carry a shipped policy YAML. This is
deliberate: the classification alphabet is fixed by the CACAO
playbook, but the policy that maps a given support-request record
into a verdict is a per-operator concern (the operator's ITSM
categories, escalation criteria, and responder-team topology).

## 3. Deterministic primitives — the contract

Ingest canonicalisation, classification-verdict shape, automated-
resolution envelope, handoff envelope, and the interaction-evidence
adapter contract are **code, not configuration**. They live in
`content/playbooks/it_security_support_agent/primitives/`. Operators
who need to diverge fork the primitive module; they do not override
it via runtime config.

`ingest_support_request(record) -> dict`
:   The intake step canonicalises the inbound support-request record
    read from the operator-supplied ticketing source: NFKC-normalises
    the free-text fields, validates the closed request-kind alphabet
    (`informational` / `actionable` / `incident-shaped`), and binds
    the requester handle plus policy-version anchor into a normalised
    in-workflow record. Read-only by contract — the ticketing source
    is never mutated.

`classify_request(record, verdict) -> dict`
:   The classify step re-validates the operator-supplied classification
    verdict against the closed alphabet: `category` matches the
    ingest record's `request_kind`; `severity` is one of
    {`Informational`, `Low`, `Medium`, `High`, `Critical`}; `rule_ids`
    are ordered and shape-checked; `policy_version` is a bounded
    opaque string. The verdict is the anchor a replay-vs-original
    diff string-equals against.

`attempt_automated_resolution(request, action_set) -> dict`
:   The automated-resolution step attempts the declared action path
    against the operator's self-service surface, bounded by the
    operator-supplied action set. It emits a closed observation
    envelope on every outcome — success, no-op, refused, or errored
    — with the fired-rule id and the terminal state pinned; the
    handoff step downstream reads this envelope, it does not re-run
    the action.

`escalate_with_human_handoff(request, resolution, handoff_inputs) -> dict`
:   **First-class explicit handoff step.** The step ALWAYS runs and
    ALWAYS materialises a closed handoff envelope carrying
    `handoff_fired` (boolean), the responder-queue handle
    (role-shaped by contract — responder rota, automation responder
    role, on-call shift handle; personal-user handles are rejected
    at the primitive boundary), and the handoff timestamp. A support
    interaction MUST end with either an automated-resolution closure
    or a confirmed handoff to a human responder — the closed envelope
    is what makes the "never silently auto-close" property auditable.

`emit_interaction_evidence(...)` — per-target adapter
:   The evidence step invokes the per-target interaction-evidence
    adapter
    (`compilers.n8n.evidence.emit_interaction_evidence_artifact_n8n`,
    `compilers.temporal.evidence.emit_interaction_evidence_artifact_activity`,
    or `compilers.langgraph.evidence.emit_interaction_evidence_artifact_node`),
    which combines the closed ingest / classification / resolution /
    handoff envelopes into one interaction-evidence artifact against
    `schemas/evidence/incidents.schema.json`. The
    interaction-evidence record is target-agnostic on the wire (the
    schema carries no `compile_target` field), so the three adapters
    emit byte-identical records for the same canonical payload.

Determinism is the property a regulator can replay against. The
closed envelopes on ingest / classify / resolution / handoff are
what a replay diff string-equals against; because the primitives
are the same Python functions called through three different
orchestrator idioms, the interaction-evidence record is byte-
identical across the three targets.

## 4. Per-target hand-off

### 4.1 n8n — Code-node bodies bound to primitives

`examples/n8n/it_security_support_agent/workflow.n8n.json` carries
the CACAO topology as n8n nodes (`manualTrigger`, `code`), with node
ids preserving the CACAO step ids verbatim. The five bound action
steps emit `n8n-nodes-base.code` nodes whose `pythonCode` imports
the primitive (e.g.
`from content.playbooks.it_security_support_agent.primitives.classify import classify_request`)
and produces the closed envelope for the next step. The
interaction-evidence step binds to the n8n adapter at
`compilers.n8n.evidence.emit_interaction_evidence_artifact_n8n`.

Operators bind the Set / Code-node inputs to their connectors:

- ingest → ticketing source (helpdesk / ITSM / support mailbox)
- classify → operator's classification-policy rule table
- automated-resolution → self-service surface (operator-declared
  action set)
- handoff → responder-queue handle (responder rota / automation
  responder role / on-call shift)
- interaction-evidence → operator's evidence store rooted at
  `content/evidence/incidents/` (see § 5)

The Code-node body assumes `PYTHONPATH` on the n8n host resolves
`content.playbooks.it_security_support_agent.primitives`. Operators
who run n8n in a Python-free container drop a single Python-runner
Code node between nodes; the wiring is documented in
[`examples/n8n/it_security_support_agent/README.md`](../../examples/n8n/it_security_support_agent/README.md)
under *Per-action wiring notes — CORE bodies*.

Regenerate from the repo root:

```sh
examples/n8n/it_security_support_agent/regenerate.sh
```

Key files: `workflow.n8n.json` (compiled workflow), `regenerate.py`
(interaction-evidence artefact driver), `evidence/interaction-evidence.json`
(representative artefact).

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/it_security_support_agent/workflow.temporal.py`
is a standard Temporal worker module: one `@workflow.defn` class
and one `@activity.defn` function per CACAO action. All five bound
activities import the primitive and produce the closed envelope;
the interaction-evidence activity binds to
`compilers.temporal.evidence.emit_interaction_evidence_artifact_activity`.

Operators drop `workflow.temporal.py` next to their worker, register
the activities, and run the worker against their Temporal cluster.
The sibling `_audit_mirror.py` carries the `AuditRecord` /
`AuditTrail` types — no `compilers.*` import in the emitted artifact,
so the worker module is a self-contained drop-in. Per-activity
retry policies are emitted alongside the activities
(`<ACTIVITY>_RETRY_POLICY`) so the operator can pin them on the
`workflow.execute_activity` call sites in their worker assembly.

Regenerate:

```sh
examples/temporal/it_security_support_agent/regenerate.sh
```

Key files: `workflow.temporal.py` (compiled workflow stub),
`regenerate.py` (interaction-evidence artefact driver),
`evidence/interaction-evidence.json`.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/it_security_support_agent/state_bindings.py`
carries the `TypedDict` state and `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes,
edges). All five bound tools import the primitive and update the
typed state. The interaction-evidence node binds to
`compilers.langgraph.evidence.emit_interaction_evidence_artifact_node`.

The agentic-extension slot is provider-neutral by construction: the
compiler never embeds an LLM SDK, so an operator wiring an LLM-driven
callable in place of one of the deterministic nodes points the hook
at self-hosted open-weights inference or an EU-hosted managed
endpoint without regenerating the artifact. The framework-wide
EU-resident LM endpoint guard re-applies the check at process
startup (`_lm_endpoint_guard.py`); see
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
for the documented `SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out.

Regenerate:

```sh
examples/langgraph/it_security_support_agent/regenerate.sh
```

Key files: `graph_spec.json` (topology), `state_bindings.py`
(TypedDict state + `@tool` bodies), `_audit_mirror.py`
(dependency-free audit-mirror sibling), `regenerate.py`
(interaction-evidence artefact driver),
`evidence/interaction-evidence.json`.

## 5. Where evidence artefacts land

The per-execution interaction-evidence artefact is emitted against
[`schemas/evidence/incidents.schema.json`](../../schemas/evidence/incidents.schema.json)
(the reused F-CP-02 incidents-stream shape) and lands under
[`content/evidence/incidents/`](../../content/evidence/incidents/) —
the same directory `playbook.incident_management@v1` writes against.
The schema's closed `classification` envelope (with the `significant`
and `cross_border` flags) and the `lifecycle` envelope together
carry the support-interaction shape without schema extension:

- **automated-resolution closure** — the record emits on the
  intake-only audit-close branch with `classification.significant=false`
  so the F-CP-02 incident KPI surface counts the interaction but
  does not double-count it as an incident.
- **human-handoff fired** — the record emits with
  `classification.significant=true` so the incident-handling KPI
  surface picks it up exactly once on the same NIS2 Article 21(2)(b)
  anchor F-WF-05 discharges when the handoff opens the downstream
  lifecycle.

The interaction-evidence record is target-agnostic on the wire —
the schema carries no `compile_target` field — so the three
per-target adapters emit byte-identical records. The byte-parity
ring is closed by `test_n8n_fixture_matches_temporal_fixture` and
`test_langgraph_fixture_matches_n8n_fixture` under
`tests/examples/it_security_support_agent/`; the immutable fixture
lives under `tests/fixtures/it_security_support_agent/`.

## 6. Relationship to sibling playbooks

**F-WF-05 `incident_management` — the handoff target.**
`playbook.incident_management@v1` is the lifecycle owner for an
incident that has already been opened: classify-significance,
open-timeline, submit the NIS2 Article 23 three-stage reports (24h /
72h / one-month), close the timeline. This playbook is the
**interaction front-line**: one support request per execution,
classified, attempted-automatically, and either closed or explicitly
handed off. The handoff envelope this playbook emits is the entry
point into the F-WF-05 lifecycle. Both anchor onto the same F-CP-02
incidents evidence stream and the same
`schemas/evidence/incidents.schema.json` artefact shape — the
schema's closed `classification` block (with `significant` and
`cross_border` flags) suffices for both surfaces, so no new evidence
schema is introduced.

**F-WF-04 `alert_triage` — a parallel upstream.**
`playbook.alert_triage@v1` is the detection-signal front-line: one
typed alert payload per execution, enriched, suppressed-or-prioritised,
routed to the appropriate response branch. `alert_triage` closes on a
p1 escalation, a p2 on-call notify, a p3 review-queue route, or a
p4 log-and-close; the handoff envelope is not first-class there
because the branching is switch-shaped. This playbook is
`alert_triage`'s ticket-shaped sibling: the same regulatory anchor
(NIS2 Article 21(2)(b) incident-handling capability), the same
downstream F-WF-05 handoff surface, and the same F-CP-02 evidence
stream — but the input is a support-request record (ticket-shaped),
not a detection alert (event-shaped).

**Regulatory mapping.**
[`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
(`nis2:art-21-2-b`) backlinks this playbook alongside
`incident_management`, `alert_triage`, and the per-incident playbooks
(`phishing_triage`, `identity_compromise`, `ransomware_containment`,
`data_exfil`, `post_incident_review`) and the responder-readiness
surface (`on_call_rotation`), closing the mapping graph in both
directions.

## 7. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the primitive
call. The mirror runs unconditionally, ahead of any OTLP exporter,
so the audit property holds even when the operator has not
configured a collector — typical for disconnected, sovereign, or
air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, …).                       |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
endpoint and never imports a vendor SDK. See
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain
a trail offline.

## 8. Sovereign-stack default

The ticketing source that `ingest-support-request` reads, the
self-service surface that `attempt-automated-resolution` walks, the
responder-queue surface that `escalate-with-human-handoff`
acknowledges against, and the evidence store that
`emit-interaction-evidence` writes to are all operator-configured.
No default hosted helpdesk, no ITSM-SaaS dependency, no default
non-EU endpoint, no vendor SDK bundled. The reference compile
targets ship bodies that import from
`content.playbooks.it_security_support_agent.primitives`; the
operator's runtime is expected to make that package importable
alongside the target's runtime. The responder-queue handle is
role-shaped by contract (responder rota, automation responder role,
on-call shift handle) — personal-user responder handles are rejected
at the primitive boundary.

## 9. What this cookbook does not cover

- **Credentials.** No API keys, tokens, private keys, ticketing-
  system credentials, or responder-queue endpoints. Connectors are
  operator-bound at runtime against environment variables documented
  per target; the framework ships no default endpoint per the
  sovereign-stack constraint.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting,
  LangGraph host process model — those are runtime concerns the
  operator applies in their own assembly.
- **Classification-policy content.** The rule table this playbook
  validates against is operator-supplied and out of scope at the
  primitive layer. The primitive re-validates the closed verdict
  shape only; the policy that produces the verdict is the operator's.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 10. References

- [`content/playbooks/it_security_support_agent/README.md`](../../content/playbooks/it_security_support_agent/README.md)
  — workflow-local module tree, state machine, and regulatory anchor.
- [`content/playbooks/it_security_support_agent/playbook.cacao.json`](../../content/playbooks/it_security_support_agent/playbook.cacao.json)
  — canonical CACAO source.
- [`content/mappings/nis2/article-21-2-b.yaml`](../../content/mappings/nis2/article-21-2-b.yaml)
  — NIS2 Article 21(2)(b) incident-handling anchor.
- [`schemas/evidence/incidents.schema.json`](../../schemas/evidence/incidents.schema.json)
  — reused F-CP-02 incidents-stream evidence schema.
- [`examples/n8n/it_security_support_agent/README.md`](../../examples/n8n/it_security_support_agent/README.md)
- [`examples/temporal/it_security_support_agent/README.md`](../../examples/temporal/it_security_support_agent/README.md)
- [`examples/langgraph/it_security_support_agent/README.md`](../../examples/langgraph/it_security_support_agent/README.md)
- [`docs/cookbook/incident_management.md`](incident_management.md)
  — F-WF-05 lifecycle, the handoff target for this workflow.
- [`docs/cookbook/alert_triage.md`](alert_triage.md)
  — F-WF-04 event-shaped sibling front-line.
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
