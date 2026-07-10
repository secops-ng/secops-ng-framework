# network_security — NIS2 Art. 21(2)(e) / DORA Art. 9 network-boundary reconciliation

SKELETON tier of the F-WF-NETWORK-SECURITY trilogy. This playbook is
the operator-side per-window reconciliation of the declared
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
  2024/1774) Art. 12 network-security controls.
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

- `playbook.cacao.yaml` — CACAO v2 workflow scaffold (5 steps:
  inventory-network-segments → evaluate-segmentation-policy →
  detect-policy-violations → enforce-remediation →
  generate-posture-evidence-artifact). SKELETON: action bodies are
  `TODO` markers a sibling CORE card lands.
- `mappings.yaml` — outbound view of the content model: OSCAL
  (SC-7 / SC-3 / CA-9), D3FEND (D3-NTA + D3-ISVA on the detect step
  with per-step gap notes), OCSF (Network Activity 4001), and the
  inbound regulatory anchors (`nis2:art-21-2-e-network-security`,
  `dora:art-9-network-security`; CRA and GDPR deliberately excluded
  with orphan-skip entries).

## Operator-supplied bindings

The playbook operationalises a documented posture; it does not
author the segmentation architecture. Operators supply the
following bindings at the CORE tier:

| Binding | Sourced from |
|---------|--------------|
| Network-inventory source set | Operator's declarative IaC records, cloud-provider network APIs, on-premise network-controller inventories |
| Segmentation-policy source  | Operator's declared zone-transit matrix / per-segment allowance set |
| Reachability-observation source | Operator's documented network-telemetry surface (traffic observations, boundary-control state, reachability probes) |
| Remediation surface | Operator's pre-bound remediation channels (per-segment ACL / firewall-rule change tickets, boundary-control posture-change tickets, short-circuit isolation) |
| Evidence store | Operator's documented evidence-store surface for the dated posture record |

## Trilogy

- **SKELETON (this card):** scaffold + mappings + inbound wires.
- **CORE:** full workflow logic — deterministic per-step
  primitives (segment-inventory reconciliation, policy-evaluation
  algebra, violation-classification, remediation-dispatch adapter
  Protocols), per-target compiler emissions (n8n / Temporal /
  LangGraph), and the deterministic control-side overlay under
  `content/controls/control.network_boundary_protection@v1.yaml`.
- **EXTEND:** cookbook walkthrough + advanced features
  (segmentation-drift and unauthorised-egress-cardinality metric
  emitters, boundary-control-drift detection bindings).
