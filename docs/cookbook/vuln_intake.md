# vuln_intake — cookbook walkthrough

Coordinated vulnerability disclosure (CVD) intake under the EU Cyber
Resilience Act. The `playbook.vuln_intake@v1` CACAO playbook receives
an inbound disclosure, acknowledges the reporter against the CRA
single-point-of-contact obligation (Annex I §2(5)), correlates the
affected component against the operator's SBOM and asset inventory
(Annex I §2(1)), scores the case with CVSS + EPSS, assesses whether
the disclosure trips the CRA Article 14 actively-exploited or
severe-incident clock, fires the regulator-notification chain when it
does, and routes the case to a per-severity response branch.

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package, the OpenTelemetry signal layer, and the
context-local `AuditTrail` mirror live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/vuln_intake/
├── README.md             # playbook overview, control / metric / OCSF refs
├── playbook.cacao.json   # the CACAO v2 artifact (playbook.vuln_intake@v1)
└── primitives/           # deterministic helpers the CACAO core_body refs bind to
    ├── cvss.py           # CVSS v3.1 parser + qualitative band
    ├── epss.py           # EPSS validator + freshness window
    ├── severity.py       # severity_policy(cvss, epss, context) → verdict
    ├── dedup.py          # case_idempotency_key + canonicalize_case_field
    └── signatures.py     # DSPy signature schema for free-text fields only
```

The CACAO playbook is the canonical source. The primitives package is
the deterministic policy the playbook *means*. The three worked
examples are the same playbook compiled into three orchestrator
idioms. Everything else — runtime, connectors, credentials — is the
operator's data plane.

## 2. CACAO topology and primitives binding

The playbook ships 12 steps: one `start`, eight `action`, one
`if-condition`, one `switch-condition`, one `end`. All eight action
steps declare an `x_secops_ng.core_body` reference into the
deterministic primitives package; the playbook is `stable` at
`content_version` 1.0.0 under the Maturity ladder.

| Step suffix       | Step                                          | `core_body` binding                                            | Status   |
|-------------------|-----------------------------------------------|----------------------------------------------------------------|----------|
| `…000002`         | intake disclosure                             | `primitives.dedup.canonicalize_case_field`                     | bound    |
| `…000003`         | triage and asset correlation                  | `primitives.severity.severity_policy`                          | bound    |
| `…000004`         | assess CRA reporting trigger                  | `primitives.cra_trigger.assess_cra_reporting_trigger`          | bound    |
| `…000005`         | actively exploited? (if-condition)            | edge wiring only — no body                                     | n/a      |
| `…000006`         | regulator-notification chain (CRA Art. 14)    | `primitives.cra_trigger.build_notification_chain`              | bound    |
| `…000007`         | route on severity (switch-condition)          | edge wiring only — no body                                     | n/a      |
| `…000008`         | response: critical — patch and advisory       | `primitives.remediation.patch_and_advisory_critical`           | bound    |
| `…000009`         | response: high — patch and advisory           | `primitives.remediation.patch_and_advisory_high`               | bound    |
| `…00000a`         | response: scheduled remediation               | `primitives.remediation.schedule_remediation`                  | bound    |
| `…00000b`         | response: accept risk                         | `primitives.remediation.accept_risk`                           | bound    |

The eight bindings are the byte-identical anchor the cross-target
replay property hangs off. The remaining `NotImplementedError` in the
emitted artifacts marks only operator-integration seams (KEV-feed
adapter, submission endpoint, advisory channel — the connectors the
operator wires), which is emitter-standard across every bound
playbook: span + AuditTrail mirror prologue first, so the seam is
identifiable at a glance.

## 3. Deterministic primitives — the contract

Severity bands, CVSS / EPSS thresholds, the dedup key shape, the
freshness window for EPSS, and the DSPy signature schema for free-text
fields are **code, not configuration**. They live in
`content/playbooks/vuln_intake/primitives/`. Operators who need to
diverge fork the primitive module; they do not override it via runtime
config.

The two bindings exercised today:

`canonicalize_case_field(value: str) -> str`
:   The intake step canonicalises the inbound CVE id (and other
    free-text case-key fields) before any downstream comparison so
    `CVE-2025-1234` and `cve-2025-1234` resolve to the same case. The
    full idempotency key (`case_idempotency_key(cve_id, asset_ref)`)
    is composed in the triage step once `__asset_ref__` is resolved.

`severity_policy(cvss, epss, context) -> SeverityVerdict`
:   The triage step produces a single normalised severity verdict so
    the downstream switch picks one of the four response branches
    without re-deriving the call in three different target idioms.
    The verdict carries the final band, the unmodified CVSS band, an
    ordered tuple of every reason that fired, and a digest of the
    canonical inputs so a replay-vs-original comparison is one
    string-equal check.

Determinism is the property a regulator can replay against. The
`SeverityVerdict.inputs_digest` is the same hex string on every target
because the policy is the same Python function; the digest is what
makes byte-parity meaningful at audit time.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + optional Code-node binding

`examples/n8n/vuln_intake/workflow.n8n.json` carries the CACAO
topology as n8n nodes (`manualTrigger`, `set`, `if`, `switch`, `noOp`),
with node ids preserving the CACAO step ids verbatim. The two bound
CORE steps emit `n8n-nodes-base.code` nodes whose `pythonCode` is the
exact primitive call (e.g. `from vuln_intake.primitives.severity import
severity_policy ; __severity_verdict__ = severity_policy(…)`); the
bound steps emit `n8n-nodes-base.code` nodes invoking their
primitives, and no Set-node placeholders remain, carrying
the CACAO I/O contract as editable assignment rows.

Operators bind the Set rows to their connectors:

- intake → CVD intake mailbox / advisory feed / CVE webhook
- triage → SBOM + asset-inventory connector, CVSS / EPSS scoring
- regulator chain → operator's CSIRT / ENISA submission endpoint and
  the CRA 24h / 72h / 14d clock from their incident_management system
- response branches → ticketing system + advisory distribution channel

The Code-node body for the two bound steps assumes `PYTHONPATH` on
the n8n host resolves `vuln_intake.primitives`. Operators who run n8n
in a Python-free container drop a single Python-runner Code node
between the Set node and the next step; the wiring is documented in
[`examples/n8n/vuln_intake/README.md`](../../examples/n8n/vuln_intake/README.md)
under *Per-action wiring notes — CORE bodies*.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/vuln_intake/workflow.temporal.py` is a standard
Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. The two bound activities
import the primitive and produce the canonical case field / severity
verdict; the only remaining `NotImplementedError` marks the
operator-integration seams (connector wiring) so an integrator
sees exactly which seam they still have to wire.

Operators drop `workflow.temporal.py` next to their worker, register
the activities, and run the worker against their Temporal cluster.
The sibling `_audit_mirror.py` carries the `AuditRecord` / `AuditTrail`
types — no `compilers.*` import in the emitted artifact, so the worker
module is a self-contained drop-in.

Per-activity retry policies are emitted alongside the activities
(`<ACTIVITY>_RETRY_POLICY`) so the operator can pin them on the
`workflow.execute_activity` call sites in their worker assembly.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/vuln_intake/state_bindings.py` carries the
`TypedDict` state, `@tool`-decorated action wrappers, and an
`AGENTIC_HOOK` slot for an LLM-driven node. `graph_spec.json` carries
the target-neutral topology (nodes, edges, conditional edges).
`assemble.py` is the canonical reference assembly that wires the spec
into a `StateGraph`.

The two bound tools import the primitive and update the typed state.
All eight tools import their primitive and update the typed state;
the operator-integration seams stay marked with `NotImplementedError`
after their span and audit record. Operators wire those seams to
their own runtime, or swap any node for an LLM-driven callable that
fills the agentic hook.

The agentic-extension slot is provider-neutral by construction: the
compiler never embeds an LLM SDK, so the operator wires the hook to
self-hosted open-weights inference or to an EU-hosted managed
endpoint without regenerating the artifact. The framework-wide
EU-resident LM endpoint guard re-applies the check at process startup
(`_lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 5. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry
span and appends an `AuditRecord` to a context-local `AuditTrail`
*before* the primitive call or the `NotImplementedError`. The mirror
runs unconditionally, ahead of any OTLP exporter, so the audit
property holds even when the operator has not configured a collector
— typical for disconnected, sovereign, or air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `if-condition`, …).       |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern, documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled in `assemble.py`; tool span (`tool.<step_id>`) inside the
  `@tool` wrapper. The node span is the parent of the tool span so a
  trace shows one `node.*` per step with the matching `tool.*` child.

The OTLP exporter endpoint is operator-supplied (`OTEL_EXPORTER_OTLP_ENDPOINT`).
The compiler never sets a default endpoint and never imports a vendor
SDK; pointing the exporter at a managed APM is a downstream choice
the operator owns end-to-end. The sovereignty posture asks for an
EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 6. Replay and audit story

The byte-parity drift guards under `tests/examples/vuln_intake/` and
`tests/examples/test_langgraph_vuln_intake.py` pin each committed
worked example to a fresh emitter run from the canonical CACAO source.
If the compiler or the playbook changes, regenerate via the per-target
`regenerate.sh` and commit the diff intentionally; the drift guard
flips green again.

The cross-target replay property is the harder one: the same
disclosure, fed through n8n / Temporal / LangGraph, produces a
byte-identical case because the bound CORE bodies are the same Python
functions called through three different idioms. The
`SeverityVerdict.inputs_digest` is the single string a regulator can
diff to confirm the property held.

## 7. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys.
  Connectors are operator-bound at runtime against environment
  variables documented per target.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting,
  LangGraph host process model — those are runtime concerns the
  operator applies in their own assembly.
- **KEV / threat-intel feed integration.** The CRA reporting-trigger
  step (`…000004`) is bound to
  `primitives.cra_trigger.assess_cra_reporting_trigger`; the KEV-feed
  *adapter* — where the exploited-in-the-wild signal comes from —
  remains the operator's connector seam by design.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution. See the canonical README's
  *Configuration contract* section.

## 8. References

- [`content/playbooks/vuln_intake/README.md`](../../content/playbooks/vuln_intake/README.md)
  — canonical CACAO source and per-step control / telemetry / metric
  refs.
- [`examples/n8n/vuln_intake/README.md`](../../examples/n8n/vuln_intake/README.md)
- [`examples/temporal/vuln_intake/README.md`](../../examples/temporal/vuln_intake/README.md)
- [`examples/langgraph/vuln_intake/README.md`](../../examples/langgraph/vuln_intake/README.md)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
