# network_security — cookbook walkthrough

Operator-side per-window reconciliation of a declared network-
segmentation policy against the observed network posture on the
operator's own deployed estate. The
`playbook.network_security@v1` CACAO playbook operates the five-step
reconciliation cycle NIS2 Article 21(2)(e) requires against the
network-boundary limb of the clause: enumerate the documented network
segments, evaluate the segmentation-policy allowances against the
observed reachability, detect and classify policy violations against
the declared zone-transit matrix, engage remediation on the operator's
pre-bound remediation surface, and publish the dated
network-security-posture evidence artifact for the reconciliation
window.

The playbook is the **portable description of the segmentation-
reconciliation spine**. It does not author the operator's segmentation
architecture, does not enumerate the operator's zone-transit matrix,
does not embed the operator's CIDR / IP-plan allocation, does not
choose the operator's remediation surface, and does not ship the
evidence-store schema. It describes the workflow shape the operator's
stack should run so the per-window reconciliation is auditable,
replayable, and restart-safe — as a shipped Digital Commons artifact
for the EU sovereign-security community.

This walkthrough wires the shipped playbook through all three
reference compile targets (n8n, Temporal, LangGraph) and shows where
each reconciliation stage — inventory, evaluate, detect, remediate,
generate-evidence — lands in each. Adapter bodies (network-inventory
source set, segmentation-policy source, reachability-observation
source, remediation surface, evidence store) are declared as
adapter-bound surfaces the operator wires; the shipped CORE artifact
lands the byte-parity emitter fan-out under
`examples/{n8n,temporal,langgraph}/network_security/` and the
cross-target parity test.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

## 1. Why this matters

NIS2 Article 21(2)(e) places **security in network and information
systems acquisition, development, and maintenance** under the essential
and important entities' technical-measures envelope. The
network-boundary / segmentation limb is the operator obligation to
maintain a documented segmentation architecture and to demonstrate
that the deployed estate stays in agreement with it — not once at
audit time, but continuously across every reconciliation window the
operator declares. DORA Article 9 (read against the JC RTS on ICT risk
management framework, Commission Delegated Regulation (EU) 2024/1774
Art. 12) places the same obligation on financial entities under a
DORA-flavoured framing: ICT-security tools, policies and procedures
covering the network layer.

The four state atoms every reconciliation window has to close over
are:

- **The declared segmentation architecture.** Which segments exist,
  what tenancy each carries, and which segment-pair transits the
  operator's zone-transit matrix allows, denies, or makes conditional
  on a documented predicate.
- **The deployed inventory.** Which segments actually exist on the
  operator's estate right now — from the declarative
  infrastructure-as-code records, the cloud-provider network APIs,
  and the on-premise network-controller inventories, composed under a
  documented source-precedence order so the answer is reproducible.
- **The observed reachability.** Which segment-pair transits are
  actually happening — from the operator's flow-log stream (OCSF
  Network Activity), the firewall / security-group inventory state,
  and any active reachability probes the operator's documented probe
  surface exposes.
- **The remediation posture.** When the observed reachability
  diverges from the declared allowance, which of the operator's
  pre-bound remediation surfaces engages — the ACL / firewall-rule
  change track, the boundary-control posture-change ticket, or the
  short-circuit isolation of the offending path.

An operator that maintains a segmentation policy document in one
place, a firewall-rule set in another, a flow-log dashboard in a
third, and a ticket tracker in a fourth still owes a coherent, dated,
replayable answer when the competent authority asks *what was your
declared segmentation policy on this date, what did your deployed
estate actually look like, which transits diverged, what did you
engage to bring them back, and what is the dated evidence record
joining all of them?* This playbook is that answer. Wiring the five
steps into an orchestration surface that survives worker restart,
records each step as durable evidence, and closes on a dated posture
artifact is the audit-evident discharge of the Art. 21(2)(e)
network-boundary obligation; assembling the answer from four
consoles and a screenshot folder on the review clock is not.

## 2. When to run each step

The reconciliation cycle is not a single-shot workflow: the five steps
land on different clocks and different operator triggers, but the
whole ring closes per reconciliation window before the next one
opens.

- **Inventory network segments.** Fires once per reconciliation
  window on the operator's declared cadence trigger (nightly /
  quarterly / on-demand against a change-management edge). Reads the
  operator's declared network-inventory sources under the documented
  source-precedence order, composes the operator-authoritative
  segment record list, and pins `__segment_inventory_id__` against
  the composed snapshot. The composition is deterministic — a replay
  of the same reconciliation window against the same source state
  recovers the same inventory identifier without re-hitting the
  upstream sources.
- **Evaluate segmentation policy.** Fires once per reconciliation
  window, downstream of the inventory. Reads the current
  segmentation-policy snapshot from the operator's documented policy
  source (declared zone-transit matrix, per-segment allowance set,
  OSCAL SC-7 / SC-3 anchor binding), normalises it against the
  segment inventory, and pins `__policy_snapshot_id__`. The
  three-value allowance algebra (allowed / denied / conditional)
  names, for every segment-pair, what the operator's declared policy
  says the transit should be. An empty allowance set is still emitted
  explicitly — a policy-missing window closes with an audit-evident
  artifact rather than short-circuiting the chain silently.
- **Detect policy violations.** Fires once per reconciliation
  window, downstream of inventory and policy. Compares the observed
  reachability posture against the policy-snapshot allowance state,
  classifies each divergence against the documented taxonomy
  (undocumented-transit, unauthorised-egress, boundary-control-drift),
  and pins `__violation_set_id__`. The set may be empty (no
  violation against the current window) — the empty case is emitted
  explicitly so a clean window is distinguishable from a skipped step
  on replay.
- **Enforce remediation.** Fires against `__violation_set_id__`.
  Engages the operator's pre-bound remediation surface per the
  operator's documented per-classification remediation binding —
  ACL / firewall-rule change track, boundary-control posture-change
  ticket, or short-circuit isolation on the active-abuse edge. Each
  engaged action returns a persistent identifier the evidence record
  binds. Empty when the violation set is empty; the closure record
  still names the empty set so the audit-evident chain remains
  complete.
- **Generate posture evidence artifact.** Fires last, unconditional.
  Publishes the dated network-security-posture evidence artifact to
  the operator's evidence store — an OSCAL-shaped Assessment-Result
  stub naming the reconciled inventory, the policy snapshot, the
  violation set (or explicit no-findings marker), and the engaged
  remediation actions. Pins `__posture_evidence_id__`. Always
  emitted — the closure record is the primary audit-evident output
  of the window regardless of whether any violation was surfaced.

## 3. Source of truth

```
content/playbooks/network_security/
├── README.md              # workflow-local overview and status
├── mappings.yaml          # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA overlay
└── playbook.cacao.yaml    # canonical CACAO v2 source
                           # (playbook.network_security@v1)

content/mappings/nis2/article-21-2-e.yaml
                           # NIS2 Art. 21(2)(e) inbound anchor —
                           # network-boundary / segmentation limb
                           # (co-anchored with the vulnerability-
                           # handling and codebase dependency-review
                           # limbs of the same clause)
content/mappings/dora/article-9-network-security.yaml
                           # DORA Art. 9 inbound anchor —
                           # network-security atom of the ICT
                           # protection and prevention obligation
content/mappings/cra/_orphan_skip.yaml
                           # CRA orphan-skip entry — estate-wide
                           # segmentation reconciliation is an
                           # operator obligation surface, not a
                           # product obligation (asset_management
                           # precedent)
content/mappings/gdpr/data-flow-network_security.md
                           # GDPR no-personal-data data-flow doc —
                           # segment identifiers, policy-snapshot
                           # identifiers, and evidence-record
                           # identifiers only; no personal data is
                           # processed by the reconciliation
```

The CACAO source is canonical. The five action steps plus one `start`
and one `end` node are the deterministic reconciliation-cycle policy
the playbook *means* — a linear
inventory → evaluate → detect → remediate → generate-evidence chain
with no conditional branching at the workflow layer. Classification
of an individual violation (undocumented-transit vs unauthorised-
egress vs boundary-control-drift) lives inside the detect step's
output artifact; the empty-violation-set branch is expressed by
`__remediation_action_id__` resolving empty while the evidence step
still fires unconditionally.

## 4. CACAO topology and control binding

The playbook ships seven steps: one `start`, five `action`, and one
`end`. The topology is a linear
inventory → evaluate → detect → remediate → generate-evidence chain.
Each action step carries a CACAO I/O contract (`in_args` /
`out_args`) and an `x_secops_ng.control_refs` binding. The
step-to-control map is:

| Step suffix | Step | I/O contract | `x_secops_ng.control_refs` | OSCAL anchor | Regulatory anchor |
|---|---|---|---|---|---|
| `…000001` | `netsec_posture_start` | — | — | — | — |
| `…000002` | inventory network segments | `__reconciliation_window__` → `__segment_inventory_id__` | `control.network_boundary_protection@v1` | NIST SP 800-53 Rev. 5 **CA-9** — Internal System Connections | NIS2 Art. 21(2)(e); DORA Art. 9 |
| `…000003` | evaluate segmentation policy | `__reconciliation_window__` + `__segment_inventory_id__` → `__policy_snapshot_id__` | `control.network_boundary_protection@v1` | NIST SP 800-53 Rev. 5 **SC-7** — Boundary Protection; **SC-3** — Security Function Isolation | NIS2 Art. 21(2)(e); DORA Art. 9 |
| `…000004` | detect policy violations | `__segment_inventory_id__` + `__policy_snapshot_id__` → `__violation_set_id__` | `control.network_boundary_protection@v1` | NIST SP 800-53 Rev. 5 **SC-7** — Boundary Protection | NIS2 Art. 21(2)(e); DORA Art. 9 |
| `…000005` | enforce remediation | `__violation_set_id__` → `__remediation_action_id__` | `control.network_boundary_protection@v1` | NIST SP 800-53 Rev. 5 **SC-7** — Boundary Protection | NIS2 Art. 21(2)(e); DORA Art. 9 |
| `…000006` | generate posture evidence artifact | `__reconciliation_window__` + `__segment_inventory_id__` + `__policy_snapshot_id__` + `__violation_set_id__` + `__remediation_action_id__` → `__posture_evidence_id__` | `control.network_boundary_protection@v1` | NIST SP 800-53 Rev. 5 **CA-9** / OSCAL Assessment Result stub | NIS2 Art. 21(2)(e); DORA Art. 9 |
| `…000007` | `netsec_posture_end` | — | — | — | — |

The `control.network_boundary_protection@v1` placeholder control
lives at `content/controls/control.network_boundary_protection@v1.yaml`
and carries the SC-7 / SC-3 / CA-9 catalog rows the mappings overlay
resolves against. Placeholder catalog rows are flagged `todo: true`
until the OSCAL upstream binding fully lands — see the `todo` markers
on
[`mappings.yaml`](../../content/playbooks/network_security/mappings.yaml).

**D3FEND binding.** The detect step is the operator-side
network-traffic analysis primitive: it carries the **D3-NTA** (network
traffic analysis) technique anchor plus **D3-ISVA** (inbound session
volume analysis) on the reachability-observation surface. The other
four steps carry per-step gap notes in the mappings overlay — an
inventory-composition primitive, a policy-evaluation algebra
primitive, a remediation-dispatch adapter, and an evidence-artifact
composer are not native D3FEND techniques and are called out as
such rather than force-fitted.

**OCSF binding.** The reconciliation ring emits **Network Activity**
(class_uid 4001) events at each pinning point — an inventory-composed
event at snapshot pinning, a policy-snapshot event at policy pinning,
per-violation events at detection pinning, per-remediation events at
remediation pinning, and a window-closure event at evidence pinning.
Each event names the reconciliation window and the pinned artifact
identifier so the audit-evident chain is emitter-side reconstructable
from telemetry alone if the evidence store is subsequently unavailable.

The playbook maturity is `experimental` on the workflow-local content
marker. The mappings overlay pins the outbound surface (OSCAL SC-7 /
SC-3 / CA-9, D3FEND D3-NTA + D3-ISVA on detect, OCSF Network Activity
4001) and the inbound regulatory closure (NIS2 Art. 21(2)(e), DORA
Art. 9; CRA and GDPR are recorded as orphan-skip entries per the
asset_management precedent).

## 5. Operator-supplied bindings

The playbook operationalises a documented posture; it does not
author the segmentation architecture. Operators wire five adapter
surfaces at the compile-target config layer:

| Binding | Sourced from |
|---|---|
| Network-inventory source set | Operator's declarative infrastructure-as-code records, cloud-provider network APIs (VPC / subnet describe endpoints), on-premise network-controller inventories |
| Segmentation-policy source | Operator's declared zone-transit matrix / per-segment allowance set, OSCAL SC-7 / SC-3 anchor binding |
| Reachability-observation source | Operator's documented network-telemetry surface — flow-log stream (OCSF Network Activity), firewall / security-group inventory state, active reachability probes |
| Remediation surface | Operator's pre-bound remediation channels — per-segment ACL / firewall-rule change tickets, boundary-control posture-change tickets, short-circuit isolation records |
| Evidence store | Operator's documented evidence-store surface for the dated posture record |

The playbook is silent on *which* IaC tool, *which* cloud-provider
vendor, *which* firewall product, and *which* evidence store the
operator runs. The interoperability surface is the CACAO I/O contract
and the OSCAL / OCSF / D3FEND overlays; the runtime binding is the
operator's declaration.

## 6. Three-target hand-off

The shipped worked examples under
`examples/{n8n,temporal,langgraph}/network_security/` compile the same
CACAO source into three reference orchestrator idioms. The
`tests/examples/{n8n,temporal,langgraph}/network_security/test_golden.py`
byte-parity goldens guard the ring across all three targets on every
PR — a compiler change that would drift any target from the committed
example fails CI.

### 6.1 n8n

The n8n emitter under `compilers/n8n/emit.py` lands the CACAO chain
as a linear n8n workflow: one Set-node per action step carrying the
`x_secops_ng.<key>` bundle as node assignments, connected in the
inventory → evaluate → detect → remediate → generate-evidence order
the CACAO `on_completion` links declare. Each n8n node id is the
CACAO step id verbatim — the node-id parity test in the golden pins
the invariant.

The Set-node surface is the operator-facing wiring point in n8n:
each `x_secops_ng.<key>` assignment names one of the operator-bound
surfaces (`x_secops_ng.control_refs`, `x_secops_ng.telemetry_refs`)
and stays visible in the n8n canvas as a first-class node parameter
rather than getting collapsed into an opaque script body. Operators
wire the adapter surfaces upstream and downstream of the Set-node
ring — a Function-node or HTTP-node reads the operator's
network-inventory source and lands `__segment_inventory_id__` on
the inventory step; a Function-node or HTTP-node reads the
segmentation-policy source and lands `__policy_snapshot_id__` on
the evaluate step; and so on across the ring.

### 6.2 Temporal

The Temporal emitter under `compilers/temporal/emit.py` lands the
CACAO chain as a workflow-and-activity fan-out: a
`NetworkSecurityWorkflow` orchestrator plus one activity per action
step (`inventory_network_segments`, `evaluate_segmentation_policy`,
`detect_policy_violations`, `enforce_remediation`,
`generate_posture_evidence_artifact`). The workflow signature declares
`__reconciliation_window__` as the input and returns
`__posture_evidence_id__` — the closure record identifier — as the
output. Intermediate identifiers flow through workflow-scoped state
so a worker restart mid-window replays against the same pinned
identifiers rather than re-hitting the upstream sources.

The Temporal target is the durable-code emission of the same CACAO
source. The workflow-level history is the audit-evident replay
surface: an auditor reading the Temporal history sees each activity
input and output pinned to the same identifiers the evidence artifact
carries. Retries live inside each activity (idempotent against the
upstream source) rather than at the workflow layer — the reconciliation
ring itself is a straight-line workflow.

### 6.3 LangGraph

The LangGraph emitter under `compilers/langgraph/emit.py` lands the
CACAO chain as a `StateGraph` with one node per action step, sharing
a Pydantic v2 state model whose fields are the CACAO variables:
`reconciliation_window`, `segment_inventory_id`, `policy_snapshot_id`,
`violation_set_id`, `remediation_action_id`, `posture_evidence_id`.
Node functions are pure state-transitions — each reads the fields it
declares in `in_args`, writes the fields it declares in `out_args`,
and returns the state delta the graph merges.

The LangGraph target is the agentic-idiom emission of the same CACAO
source. The state model is the audit-evident replay surface: the
final `posture_evidence_id` value on the terminal state is the
closure identifier, and the intermediate identifiers stay reconstructable
from the state trajectory the graph runner logs.

### 6.4 Cross-target invariants

Two properties hold across all three targets and are pinned by the
byte-parity goldens:

- **Step-id parity.** Every CACAO step id (`action--7e750001-...-000000N`)
  appears once as an n8n node id, once as a Temporal activity name
  (via the CACAO `name` field), and once as a LangGraph node key —
  the reconciliation graph shape is the same across targets.
- **Variable parity.** The six playbook variables
  (`__reconciliation_window__`, `__segment_inventory_id__`,
  `__policy_snapshot_id__`, `__violation_set_id__`,
  `__remediation_action_id__`, `__posture_evidence_id__`) surface in
  each target under the target's idiomatic variable-passing surface —
  n8n Set-node assignments, Temporal activity arguments and returns,
  LangGraph state fields — and no additional target-local identifiers
  are introduced.

## 7. Regulatory-graph closure

The playbook contributes to the network-boundary limb of NIS2
Art. 21(2)(e) and to the network-security atom of DORA Art. 9.
Companion inbound anchors are wired in the mappings overlay:

- **NIS2 Art. 21(2)(e)** — primary anchor. The inbound entry at
  `content/mappings/nis2/article-21-2-e.yaml` co-anchors this
  playbook (network-boundary / segmentation limb) with
  `playbook.vulnerability_management@v1` (vulnerability-handling
  limb) and `playbook.codebase_vuln_management@v1` (codebase
  dependency-review limb). The three limbs discharge distinct
  slices of the same clause.
- **DORA Art. 9** — sibling anchor. The network-security atom of
  the ICT protection and prevention obligation reads against the
  JC RTS on ICT risk management framework (Commission Delegated
  Regulation (EU) 2024/1774) Art. 12 network-security controls.
  The inbound entry at
  `content/mappings/dora/article-9-network-security.yaml` backlinks
  `playbook.network_security@v1`.
- **CRA** — orphan-skip. Estate-wide segmentation reconciliation is
  an operator obligation surface, not a product obligation. The
  clause-by-clause review is recorded in
  `content/mappings/cra/_orphan_skip.yaml` (asset_management
  precedent).
- **GDPR** — orphan-skip. The reconciliation operates on segment
  identifiers, policy-snapshot identifiers, and evidence-record
  identifiers only; no personal data is processed. A
  no-personal-data data-flow doc lands at
  `content/mappings/gdpr/data-flow-network_security.md`
  (ddos_response / patch_management / asset_management precedent).

## 8. What this cookbook deliberately does not cover

- **Credentials.** No IaC-source, cloud-provider, network-controller,
  firewall, evidence-store, or ticketing endpoint or token belongs
  in the playbook or its compiled orchestrator artifacts. The
  operator wires each at the compile-target config layer.
- **Per-deployment topology.** Segment taxonomy, zone-transit
  matrix, CIDR / IP-plan allocation, per-classification remediation
  binding, and reconciliation-window cadence are operator
  declarations that live in the operator's segmentation-scope
  catalogue, not in the playbook.
- **Segmentation-architecture authoring.** *Which* zones exist,
  *which* transits are allowed, and *what* the conditional-transit
  predicates evaluate are the operator's programme-scope
  declarations — the playbook operates against the declared
  architecture it is handed, not against a framework-declared
  taxonomy.
- **Flow-log vendor choice.** The playbook is deliberately silent
  on which flow-log source the operator runs; the OCSF Network
  Activity (4001) shape is the interoperability surface, and the
  observation-source binding is the operator's declaration.
- **Remediation-surface choice.** *Which* change-management channel
  handles ACL edits, *which* ticketing surface holds boundary-control
  posture-change tickets, and *whether* automated short-circuit
  isolation is bound are operator posture decisions — the playbook
  dispatches against pre-bound surfaces the operator's
  change-management posture already documents.
