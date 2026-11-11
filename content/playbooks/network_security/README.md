# network_security — NIS2 Art. 21(2)(e) / DORA Art. 9 network-boundary reconciliation

`stable` playbook of the F-WF-NETWORK-SECURITY trilogy. It is the
operator-side per-window reconciliation of the declared
segmentation policy against the observed network posture on the
operator's own deployed estate: enumerate the documented network
segments, evaluate the segmentation-policy allowances against the
observed reachability, detect and classify policy violations against
the declared zone-transit matrix, engage remediation on the
operator's pre-bound remediation surface, and publish the dated
network-security-posture evidence artifact for the reconciliation
window.

## Regulatory anchors

- **NIS2 Art. 21(2)(e)** — security in network and information
  systems. The network-boundary / segmentation limb of the clause;
  co-anchored with the existing vulnerability-handling limb
  (`nis2:art-21-2-e`) and the codebase-side dependency-review limb
  (`nis2:art-21-2-e-codebase`).
- **DORA Art. 9** — protection and prevention (ICT security tools,
  policies and procedures), read against the JC RTS on ICT risk
  management framework (Commission Delegated Regulation (EU)
  2024/1774) Art. 13 network security management.
- **CRA** — no direct inbound. Estate-wide network-segmentation
  reconciliation is an operator obligation surface; the CRA
  clause-by-clause review is recorded in
  `content/mappings/cra/_orphan_skip.yaml` (asset_management
  precedent).
- **GDPR** — no direct inbound. The reconciliation operates on
  segment identifiers, policy-snapshot identifiers, and evidence-
  record identifiers only; no personal data is processed. A
  no-personal-data data-flow doc lands at
  `content/mappings/gdpr/data-flow-network_security.md`
  (ddos_response / patch_management / asset_management precedent).

## Files

- `playbook.cacao.yaml` — the CACAO v2 workflow (5 steps:
  inventory-network-segments → evaluate-segmentation-policy →
  detect-policy-violations → enforce-remediation →
  generate-posture-evidence-artifact), each step bound to its
  primitive through `core_body`.
- `mappings.yaml` — outbound view of the content model: OSCAL
  (SC-7 / SC-3 / CA-9), D3FEND (D3-NTA + D3-ISVA on the detect step
  with per-step gap notes), OCSF (Network Activity 4001), and the
  inbound regulatory anchors (`nis2:art-21-2-e-network-security`,
  `dora:art-9-network-security`; CRA and GDPR deliberately excluded
  with orphan-skip entries).
- `primitives/` — one deterministic primitive per action step (see
  Status).

## Status

`maturity: stable`, `content_version` 1.0.0. All five action steps
bind a deterministic primitive under `primitives/` through `core_body`,
each executed directly by
`tests/playbooks/network_security/test_primitives.py`, and the three
reference targets emit those calls. The graduation checklist
recomputes green: tier A, 5 of 5 real bindings, zero placeholder
bodies, zero blank predicates, zero schema errors, zero predicted n8n
TODOs.

| Step | Primitive |
|---|---|
| inventory_network_segments | `inventory.compose_segment_inventory` |
| evaluate_segmentation_policy | `policy.evaluate_segmentation_policy` |
| detect_policy_violations | `detection.detect_policy_violations` |
| enforce_remediation | `remediation.dispatch_remediation` |
| generate_posture_evidence_artifact | `evidence.compose_posture_evidence` |

Decisions the primitives fix:

- **Precedence decides, disagreement is recorded.** Inventory sources
  are read highest precedence first; the higher source's record wins
  and every field a lower source disagrees on is recorded.
- **Documented means declared.** A segment only a provider API or a
  network controller reports is listed as undocumented (Commission
  Implementing Regulation (EU) 2024/2690, Annex point 6.7.2(a);
  Delegated Regulation (EU) 2024/1774, Art. 13(b)).
- **Every unlisted zone pair is denied**, within a zone as well as
  between zones (Annex points 6.7.2(c) and 6.8.2(e)). A conditional
  allowance names services, a time-boxed authorisation with both
  bounds (Annex point 6.7.2(h)), or both.
- **The policy's own gaps are recorded, not fatal:** zones of
  inventoried segments it does not declare, no dedicated
  administration zone (Art. 13(c); Annex point 6.8.2(f)), an
  administration zone reachable from outside, no allowance at all.
- **Two kinds of violation.** An observed transit the matrix does not
  permit is unauthorised egress when it leaves the estate and
  undocumented transit otherwise. A boundary rule that permits what
  the matrix denies, or denies what it plainly allows, is drift,
  whether or not traffic was seen.
- **Isolation only for active abuse, with the operator's consent.**
  Every violation is dispatched to the surface the operator binds to
  its classification; it is isolated instead (Art. 13(j)) only when it
  carries an active-abuse fingerprint and automated isolation is
  allowed. The step does not close until every dispatch has returned
  a persistent identifier.
- **One checked chain per window.** The evidence refuses records from
  another inventory, snapshot or violation set, gives every finding
  its action, and carries undocumented segments, source disagreements
  and policy gaps as open items, so a clean violation set over an
  incomplete inventory does not read as a clean window.
- **Replays recover the same identifiers.** Inventory, snapshot,
  violation and evidence identifiers are digests of content, never of
  the clock.

The wire binds them:

- **The topology stays linear.** `enforce_remediation` runs on every
  window. With an empty violation set it dispatches nothing and leaves
  `__remediation_action_id__` unset, and the evidence step records
  `no_findings`.
- **The contract grows from 6 to 23 variables.** There are 13 adapter
  inputs: the reconciliation window, the inventory sources in
  precedence order, the segmentation policy, the observed transits and
  the boundary rules, the remediation binding, whether automated
  isolation is allowed, the dispatch receipts, and the five step
  instants. There is one envelope per step. The five identifiers the
  SKELETON declared are now fields extracted from those envelopes at
  the adapter seam; `__reconciliation_window__` stays the trigger
  input.
- **Lists ride as JSON strings**, because CACAO has no list type: the
  inventory sources, the observed transits, the boundary rules and the
  dispatches. `__remediation_binding__` defaults to `DEFAULT_BINDING`,
  carried as JSON text in the variable's `value`, which the adapter
  decodes like the lists.
- **Isolation needs a real boolean.** `__automated_isolation_allowed__`
  has no default, so the operator states its isolation posture
  explicitly every run.

## Operator-supplied bindings

The playbook operationalises a documented posture; it does not
author the segmentation architecture. These operator surfaces feed
the adapter inputs above:

| Binding | Sourced from |
|---------|--------------|
| Network-inventory source set | Operator's declarative IaC records, cloud-provider network APIs, on-premise network-controller inventories |
| Segmentation-policy source  | Operator's declared zone-transit matrix / per-segment allowance set |
| Reachability-observation source | Operator's documented network-telemetry surface (traffic observations, boundary-control state, reachability probes) |
| Remediation surface | Operator's pre-bound remediation channels (per-segment ACL / firewall-rule change tickets, boundary-control posture-change tickets, short-circuit isolation) |
| Evidence store | Operator's documented evidence-store surface for the dated posture record |

## Trilogy

- **SKELETON:** scaffold + mappings + inbound wires.
- **CORE (CORE-PRIM #1063, CORE-WIRE + GRADUATE this change):** full workflow logic — deterministic per-step
  primitives (segment-inventory reconciliation, policy-evaluation
  algebra, violation-classification, remediation-dispatch adapter
  Protocols), per-target compiler emissions (n8n / Temporal /
  LangGraph), and the deterministic control-side overlay under
  `content/controls/control.network_boundary_protection@v1.yaml`.
- **EXTEND:** cookbook walkthrough + advanced features
  (segmentation-drift and unauthorised-egress-cardinality metric
  emitters, boundary-control-drift detection bindings).
