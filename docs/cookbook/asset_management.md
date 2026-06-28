# asset_management — cookbook walkthrough

Per-window asset and configuration inventory-delta capture workflow.
The `playbook.asset_management@v1` CACAO playbook fires on a scheduled
reconciliation cadence: it ingests the operator's documented
inventory-source set, reconciles the per-source observations into the
operator-authoritative snapshot for the current window, computes the
per-asset delta against the previous documented snapshot, classifies
each delta against the closed delta taxonomy, captures the dated
asset-inventory-delta evidence record, and notifies the documented
inventory owner. The workflow operationalises a reconciliation
posture against pre-bound inventory sources; it does not author the
operator's inventory-source architecture itself.

The regulatory anchor is NIS2 Article 21(2)(i) — human resources
security, access-control policies, and asset management — pinned by
the `nis2:art-21-2-i` mapping entry in
[`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml).
DORA Article 8 (identification function — asset / configuration
register, exercised under the JC RTS on ICT risk management framework
Commission Delegated Regulation (EU) 2024/1774) is the co-anchored
inbound entry at
[`content/mappings/dora/article-8.yaml`](../../content/mappings/dora/article-8.yaml)
(`dora:art-8-identification`). The artifact shape is
[`schemas/evidence/inventory.schema.json`](../../schemas/evidence/inventory.schema.json)
(stream: `inventory`).

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the deterministic
primitives package and the per-target adapter live in each.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/asset_management/
├── README.md                    # workflow-local module tree
├── mappings.yaml                # outbound playbook-mappings overlay
├── playbook.cacao.json          # canonical CACAO v2 source (playbook.asset_management@v1)
└── primitives/
    ├── reconcile.py             # reconcile_inventory_snapshot — reconcile-authoritative-inventory
    ├── classify.py              # classify_inventory_delta — classify-delta
    └── artifact.py              # build_asset_inventory_delta_evidence_artifact — capture-evidence

schemas/evidence/inventory.schema.json
                                  # per-execution asset-inventory-delta evidence artifact schema (stream: inventory)

compilers/n8n/evidence/inventory_node.py
compilers/temporal/evidence/inventory_activity.py
compilers/langgraph/evidence/inventory_node.py
                                  # per-target adapters that marshal the JSON-native payload into the primitive
                                  # and persist the artifact atomically (no shared emitter — record assembly is
                                  # owned by the workflow-local primitive; see § 3).
```

The CACAO source is canonical. The primitives package is the
deterministic policy the playbook *means*. The three worked examples
are the same playbook compiled into three orchestrator idioms.
Everything else — runtime, inventory-source endpoints (CMDB,
declarative IaC state backend, cloud-provider asset APIs,
endpoint-management agent control plane), evidence sink, and the
inventory-owner notification channel — is the operator's data plane.

The CACAO source ships as JSON
(`content/playbooks/asset_management/playbook.cacao.json`); the three
worked examples each carry a mirror copy at
`examples/{n8n,temporal,langgraph}/asset_management/playbook.cacao.json`
that is byte-identical to the canonical and refreshed by the
per-target `regenerate.sh`.

## 2. CACAO topology and primitives binding

The playbook ships eight steps: one `start`, six `action`, one `end`.
The three core-bound action steps declare an `x_secops_ng.core_body`
reference into the deterministic primitives package. The ingest,
delta-computation, and notification steps are operator-bound runtime
seams (read calls against the documented inventory-source set; the
previous documented snapshot lookup; the inventory-owner notification
channel) and carry no `core_body` binding — the framework does not
ship a default endpoint for any of them.

| Step suffix | Step                                       | `core_body` binding                                                                  | Status         |
|-------------|--------------------------------------------|--------------------------------------------------------------------------------------|----------------|
| `…000001`   | start                                      | edge wiring only — no body                                                           | n/a            |
| `…000002`   | ingest-inventory-sources                   | operator-bound runtime seam — reads against the documented inventory-source set      | operator-bound |
| `…000003`   | reconcile-authoritative-inventory          | `primitives.reconcile.reconcile_inventory_snapshot`                                  | bound          |
| `…000004`   | compute-delta-against-previous-snapshot    | operator-bound runtime seam — read against the previous documented snapshot          | operator-bound |
| `…000005`   | classify-delta                             | `primitives.classify.classify_inventory_delta`                                       | bound          |
| `…000006`   | capture-evidence                           | `primitives.artifact.build_asset_inventory_delta_evidence_artifact`                  | bound          |
| `…000007`   | notify-inventory-owner                     | operator-bound runtime seam — dispatch on the documented owner channel               | operator-bound |
| `…000008`   | end                                        | edge wiring only — no body                                                           | n/a            |

Transitions are deterministic — each state declares exactly one
`on_completion` successor, no conditional branching at this layer.
One scheduled reconciliation execution emits exactly one
asset-inventory-delta evidence record; the per-asset delta entries are
folded into the artifact's `delta_set[]` block, not emitted as
independent records.

## 3. Deterministic primitives — the contract

The per-source asset-observation normalisation, the source-precedence
merge that composes the operator-authoritative snapshot, the
deterministic `snapshot_id` / `source_set_id` derivations, the closed
per-delta classification taxonomy, the closed `asset-inventory-delta`
evidence shape the schema pins, and the `artifact_id` recipe are
**code, not configuration**. They live in
`content/playbooks/asset_management/primitives/`. Operators who need
to diverge fork the primitive module; they do not override it via
runtime config.

Unlike the F-CP-02 incidents and F-CP-07 access streams, the
asset-inventory-delta record assembly is **not** delegated through a
shared `compilers/_shared/evidence/` helper. The delta-set,
source-set, and snapshot identifiers are purpose-shaped for the
reconciliation workflow and are not reusable on other streams; the
per-target adapters under `compilers/{n8n,temporal,langgraph}/evidence/`
are glue only — payload in, primitive call, atomic write out.

The three bindings exercised today:

`reconcile_inventory_snapshot(per_source_observations, source_precedence) -> InventorySnapshot`
:   The `reconcile-authoritative-inventory` step merges the operator-
    supplied per-source asset observations under the operator's
    documented source-precedence ordering. Asset records are
    NFKC-normalised, sorted on `asset_id`, exact-match duplicates
    collapse, and `source_attribution` carries the consulted sources
    in operator-documented precedence order. The canonical asset
    record list is SHA-256-hashed into `snapshot_id`; the canonical
    sorted `(source_id, source_kind)` pair list is SHA-256-hashed
    into `source_set_id` so the audit-evident chain pins both the
    surface and the snapshot. Two replays of the same window over
    the same sources produce byte-identical ids. The reconciliation
    is read-only against the source set — it does not write back into
    the operator's CMDB or IaC declarations; correcting drift is the
    operator's downstream lever. No network, no clock, no vendor
    SDK.

`classify_inventory_delta(delta_set, ownership_declarations, decommissioning_records, *, deadline_missed=False) -> Sequence[str]`
:   The `classify-delta` step resolves each entry in the asset-
    inventory delta set against the operator's documented delta
    taxonomy. The closed vocabulary is `new-managed`,
    `unmanaged-discovered`, `decommissioned`, and `baseline-drift`:

    - `new-managed` — asset appeared in the current snapshot and a
      documented owner / declaration covers it (the `asset_id`
      appears in `ownership_declarations`).
    - `unmanaged-discovered` — asset appeared without a documented
      owner, OR asset disappeared without a documented
      decommissioning record. The exception bucket NIS2 Art. 21(2)(i)
      reviewers consume; the per-execution
      `unmanaged_discovered_count` is the cardinality the artifact
      pins.
    - `decommissioned` — asset disappeared per a documented
      decommissioning record (`asset_id` in
      `decommissioning_records`).
    - `baseline-drift` — `baseline_diverged` change-kind: the asset
      is still present but the observed baseline differs from the
      documented baseline; the operator's downstream lever is to
      either refresh the baseline or correct the observed
      configuration.

    Per-delta consistency invariants (change-kind vs. state
    transition) are enforced at the primitive boundary. When the
    classification step short-circuits under the documented
    reconciliation deadline (`deadline_missed=True`), the primitive
    emits the single sentinel entry `["unclassified"]`; downstream
    reviewers treat the delta set as unmanaged-discovered for
    notification urgency. Output is sorted so two replays of the
    same inputs collapse to byte-identical bytes.

`build_asset_inventory_delta_evidence_artifact(workflow_id, execution_id, regulation_refs, control_refs, snapshot_window, snapshot_id, source_set_id, delta_set, delta_classification, captured_at, source_url, ...) -> InventoryEvidenceArtifact`
:   The `capture-evidence` step shapes the JSON-native asset-
    inventory-delta evidence record against
    [`schemas/evidence/inventory.schema.json`](../../schemas/evidence/inventory.schema.json).
    The deterministic `artifact_id` derives from
    `SHA-256(<workflow_id>|<execution_id>|<captured_at>)` (UTF-8, no
    separators around the pipes). `compile_target` is intentionally
    **not** part of the id — the three reference compilers (n8n,
    Temporal, LangGraph) re-derive byte-identical bytes from the same
    primitive output, and the G-03 byte-parity contract the
    CORE-FANOUT siblings assert against holds across targets. The
    primitive re-validates the snapshot block, delta block, and
    classification list shape so a direct caller cannot bypass the
    per-step guards. The `unmanaged_discovered_count` is computed
    from the classification list rather than supplied externally.

The `artifact_id` derivation deliberately omits `compile_target` —
this is the inverse of the posture-evidence and incidents streams,
which key on `compile_target` so each target produces its own artifact
under its own id. For asset_management, an operator running the same
reconciliation window under more than one target emits the **same**
artifact bytes at the **same** path; cross-target duplication is
treated as redundant emission, not as a discriminator. Downstream
consumers join on `(workflow_id, execution_id)` and dedupe on
`artifact_id`.

> **LM determinism.** Per-source reconciliation, per-delta
> classification, and evidence shaping are code, not LM. The
> asset_management playbook does not bind any DSPy signature — there
> is no free-text step at this layer. The inventory-source reads, the
> previous-snapshot lookup, and the inventory-owner notification are
> mechanical walks of the operator's documented surfaces, not LM
> judgements. See `docs/FOUNDATION.md` § LLM determinism.

## 4. Per-target hand-off

### 4.1 n8n — operator-edited Set rows + Code-node bindings

`examples/n8n/asset_management/workflow.n8n.json` carries the CACAO
topology as n8n nodes (`manualTrigger`, `set`, `noOp`), with node ids
preserving the CACAO step ids verbatim. The six action steps emit
`n8n-nodes-base.set` nodes carrying the CACAO I/O contract as
editable assignment rows — the n8n target ships as a **snapshot of
intent**, and the operator binds the Set rows to their own connectors
in their n8n instance:

- `ingest-inventory-sources` → CMDB endpoint, declarative IaC state
  backend, cloud-provider asset APIs, endpoint-management agent
  control plane (HTTP / database / executeCommand nodes per source).
- `reconcile-authoritative-inventory` → Python-runner Code node
  invoking `content.playbooks.asset_management.primitives.reconcile.reconcile_inventory_snapshot`
  on the canonicalised per-source observations.
- `compute-delta-against-previous-snapshot` → previous-snapshot read
  (object-store / filesystem / database lookup) + per-asset delta
  computation against the reconciled snapshot.
- `classify-delta` → Python-runner Code node invoking
  `content.playbooks.asset_management.primitives.classify.classify_inventory_delta`.
- `capture-evidence` → `executeCommand` node calling
  `python -m compilers.n8n.evidence.inventory_node` (or a Code node
  embedding the equivalent call), which routes the typed payload
  through the per-target adapter at
  [`compilers/n8n/evidence/inventory_node.py`](../../compilers/n8n/evidence/inventory_node.py).
- `notify-inventory-owner` → operator's inventory-owner notification
  channel (HTTP webhook / mail / chat connector).

The Code-node body for the bound steps assumes `PYTHONPATH` on the
n8n host resolves `content.playbooks.asset_management.primitives`;
operators who run n8n in a Python-free container drop a
Python-runner Code node ahead of the Set node (the
[`examples/n8n/asset_management/regenerate.py`](../../examples/n8n/asset_management/regenerate.py)
script documents the per-action wiring of the CORE bodies on the n8n
side end-to-end). The capture-evidence adapter is a pure function:
`payload (mapping) + output_dir` in, `{artifact_id, artifact_path}`
out. Persistence is atomic (`os.replace` through a sibling `.tmp`)
so a concurrent reader never observes a partial write.

n8n is the **no-code** target; the scheduled reconciliation cadence is
the operator's cron / schedule trigger at the front of the imported
workflow. The compiled artefact is a snapshot of intent — the operator
wires the schedule, the credential bindings on the inventory-source
reads, the previous-snapshot read path, the evidence directory, and
the inventory-owner notification channel in their own n8n instance.

### 4.2 Temporal — `@activity.defn` bodies with retry policy

`examples/temporal/asset_management/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action. Each activity docstring
names the primitive (or operator-bound seam) the activity discharges;
the bodies of the committed stub raise `NotImplementedError` pending
the worker-translator slice, so the operator wires the activity
implementations in their own assembly. The three core-bound
activities (`reconcile-authoritative-inventory`, `classify-delta`,
`capture-evidence`) document the primitive call against the
deterministic body under
`content.playbooks.asset_management.primitives.{reconcile,classify,artifact}`;
the ingest / compute-delta / notify activities document the
operator-bound seam (no default endpoint).

The sibling `_audit_mirror.py` carries the `AuditRecord` /
`AuditTrail` types — no `compilers.*` import in the emitted artifact,
so the worker module is a self-contained drop-in. The
`capture-evidence` activity at
[`compilers/temporal/evidence/inventory_activity.py`](../../compilers/temporal/evidence/inventory_activity.py)
delegates record assembly to the workflow-local primitive (rather than
through `compilers/_shared/evidence/`) and writes the artifact bytes
through the same atomic-write helper the n8n adapter uses. Replay
against the same Temporal event history re-derives the same
`artifact_id`. Temporal is the natural fit for the per-window
reconciliation shape: the scheduled cadence becomes a Temporal
Schedule, and the per-tick workflow is the unit a regulator-facing
reviewer reads the artifact series back against.

### 4.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/asset_management/state_bindings.py` carries the
`TypedDict` state and the `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes, edges).
The committed `state_bindings.py` is a generated stub: each tool's
docstring names the primitive (or operator-bound seam) it discharges
and the body raises `NotImplementedError` until a human integrator
wires it to the operator's runtime — the three core-bound tools
(`reconcile-authoritative-inventory`, `classify-delta`,
`capture-evidence`) document the primitive call against
`content.playbooks.asset_management.primitives.{reconcile,classify,artifact}`,
and the ingest / compute-delta / notify tools document the
operator-bound seam. The `capture-evidence` node at
[`compilers/langgraph/evidence/inventory_node.py`](../../compilers/langgraph/evidence/inventory_node.py)
is a plain `state -> state` function the integrator wires with
`graph.add_node("emit_asset_inventory_delta",
emit_asset_inventory_delta_artifact_node)`; no LangGraph or LangChain
import is required at the compiler layer.

LangGraph is the agentic target — the natural seam an operator extends
with an LLM-driven node is *out of band* for this workflow. Per-source
reconciliation, per-delta classification, and evidence shaping are
mechanical walks of the operator's documented surfaces, not free-text
reasoning steps; adding an agentic hook here would defeat the
determinism the asset-inventory-delta record relies on. The compiler
never embeds an LLM SDK; the framework-wide EU-resident LM endpoint
guard re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 5. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the primitive
call. The mirror runs unconditionally, ahead of any OTLP exporter, so
the audit property holds even when the operator has not configured a
collector — typical for disconnected, sovereign, or air-gapped
deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`).          |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default and
never imports a vendor SDK; pointing the exporter at a managed APM is
a downstream choice the operator owns end-to-end. The sovereignty
posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 6. Replay and audit story

Two replay properties are pinned for asset_management.

**Per-execution deterministic replay** — the workflow-local primitive
at `content.playbooks.asset_management.primitives.artifact` produces a
byte-identical record on every re-emission against the same execution
context. The record `artifact_id` is
`SHA-256(workflow_id|execution_id|captured_at)`; the snapshot block
re-derives the same `snapshot_id` over the same per-source
observations under the same precedence ordering, the same
`source_set_id` over the same source list, and the same sorted
`delta_classification` list over the same delta inputs.

**Per-target byte-stable goldens, cross-target byte-parity** — the
three committed worked-example records under
`examples/{n8n,temporal,langgraph}/asset_management/evidence/asset-inventory-delta-record.json`
are pinned byte-for-byte by the per-target byte-parity goldens at
`tests/examples/asset_management/test_{n8n,temporal,langgraph}_workflow_golden.py`
and
`tests/examples/asset_management/test_{n8n,temporal,langgraph}_asset_inventory_delta_evidence.py`.
Each test pins (a) the per-target workflow artefact
(`workflow.n8n.json` / `workflow.temporal.py` / `graph_spec.json` +
`state_bindings.py`), (b) the per-target asset-inventory-delta
record, and (c) the byte-equality of the co-located CACAO mirror
against the canonical source under
`content/playbooks/asset_management/`. Because `artifact_id` is **not**
keyed on `compile_target`, the three per-target records resolve to the
same `artifact_id` for the same execution context — cross-target
byte-parity is asserted on the bytes of the record themselves, not on
the path discriminator. If a primitive or any per-target adapter
changes, regenerate the worked example via the per-target
`regenerate.sh` and commit the diff intentionally; the drift guard
flips green again.

## 7. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys. The CMDB
  read endpoint, the declarative IaC state backend, the cloud-provider
  asset APIs, the endpoint-management agent control plane, the
  previous-snapshot store, the asset-inventory-delta evidence sink,
  and the inventory-owner notification channel are all operator-bound
  at runtime against environment variables documented per target; the
  framework ships no default endpoint and bundles no hosted
  CMDB-correlation SaaS per the sovereign-stack posture.
- **Inventory-source architecture.** This playbook consumes the
  documented inventory-source set the operator already maintains — it
  does not author that set. Which CMDB the operator runs, which IaC
  state backend they treat as authoritative, which cloud-provider
  asset APIs they consume, and the precedence ordering between them
  are upstream operator concerns out of scope for this workflow. The
  framework commits to the reconciliation contract, not the
  source-set composition.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting, the
  scheduler driving the reconciliation cadence, LangGraph host
  process model — those are runtime concerns the operator applies in
  their own assembly.
- **Personal data in asset records.** Operator-side asset records may
  carry asset identifiers, account labels, owner role names, and
  tenancy markers; per AGENTS.md §3 they MUST stay role-shaped or
  opaque. Individual personal names, credential-shaped strings, and
  raw configuration secret material are out of scope and rejected at
  the schema boundary. The GDPR Records of Processing Activity entry
  accompanying this overlay
  ([`content/mappings/gdpr/data-flow-asset_management.md`](../../content/mappings/gdpr/data-flow-asset_management.md))
  pins the no-personal-data posture explicitly.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 8. References

- [`content/playbooks/asset_management/playbook.cacao.json`](../../content/playbooks/asset_management/playbook.cacao.json)
  — canonical CACAO source.
- [`content/playbooks/asset_management/README.md`](../../content/playbooks/asset_management/README.md)
  — workflow-local module tree.
- [`content/playbooks/asset_management/mappings.yaml`](../../content/playbooks/asset_management/mappings.yaml)
  — outbound playbook-mappings overlay (OSCAL CM-8 / CM-8(2), OCSF
  API Activity, NIS2 Art. 21(2)(i) and DORA Art. 8 inbound closures).
- [`schemas/evidence/inventory.schema.json`](../../schemas/evidence/inventory.schema.json)
  — per-execution asset-inventory-delta evidence artifact schema
  (stream: `inventory`).
- [`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml)
  — NIS2 Art. 21(2)(i) mapping; entry `nis2:art-21-2-i` is the
  human-resources-security / access-control / asset-management
  anchor.
- [`content/mappings/dora/article-8.yaml`](../../content/mappings/dora/article-8.yaml)
  — DORA Art. 8 mapping; entry `dora:art-8-identification` is the
  identification-function (asset / configuration register) anchor.
- [`compilers/n8n/evidence/inventory_node.py`](../../compilers/n8n/evidence/inventory_node.py)
- [`compilers/temporal/evidence/inventory_activity.py`](../../compilers/temporal/evidence/inventory_activity.py)
- [`compilers/langgraph/evidence/inventory_node.py`](../../compilers/langgraph/evidence/inventory_node.py)
- [`examples/n8n/asset_management/regenerate.py`](../../examples/n8n/asset_management/regenerate.py)
- [`examples/temporal/asset_management/regenerate.py`](../../examples/temporal/asset_management/regenerate.py)
- [`examples/langgraph/asset_management/regenerate.py`](../../examples/langgraph/asset_management/regenerate.py)
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
