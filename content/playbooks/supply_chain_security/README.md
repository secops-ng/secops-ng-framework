# supply_chain_security

Supply-chain-security playbook scaffold for NIS2-regulated operators.
Detects and responds to supply-chain compromises that reach the
operator through a direct supplier, service provider, or upstream
software component — the operational object of NIS2 Directive (EU)
2022/2555, Article 21(2)(d) (supply-chain security, including the
security characteristics of direct suppliers and service providers).

## Maturity

`SKELETON` — this card ships the workflow topology and the CACAO
artifact only. The action bodies are placeholders that pin the
contract, not real action logic. The following surfaces are explicit
out-of-scope siblings that will land in dedicated follow-on cards:

- **CORE** — real action logic for `assess-supplier-signal`
  (signal-source ingestion, SBOM correlation, supplier-attestation
  lookup, verdict scoring) and `emit-supply-chain-evidence` (the
  F-CP-03 supply-chain evidence artifact emission); compile-target
  fan-out to `examples/{n8n,temporal,langgraph}/supply_chain_security/`
  and the per-target binding tests.
- **EXTEND** — regulatory cross-references (OSCAL controls beyond the
  inline `control_refs`, MITRE D3FEND defensive techniques, OCSF
  telemetry classes, NIS2 / DORA / CRA inbound + outbound mappings),
  metric refs (KPI / KRI catalogue entries for supplier-attestation
  freshness and supply-chain-compromise dwell), and byte-parity
  golden tests against the three reference compile targets.

The SKELETON layer is intentionally scoped to one deliverable per
forward-public-hygiene convention: shape the contract, defer the
content. Operators reading this directory at the SKELETON layer get
the workflow shape but no runnable artifact.

## Files

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.supply_chain_security@v1`). Pins the topology
  (workflow_start → assess-supplier-signal →
  emit-supply-chain-evidence → workflow_end) and the per-step
  `x_secops_ng.control_refs` joins into the SecOps-NG content
  model. `compile_targets` is empty at this layer; the CORE
  sibling adds the three reference targets.
- `mappings.yaml` — outbound playbook-mappings overlay. Ships as a
  schema-valid placeholder with empty `oscal` / `d3fend` / `ocsf` /
  `nis2` / `dora` / `cra` blocks so the G-02 finalized-playbook
  coverage guard accepts the new directory without trapping it as
  an orphan. The full cross-reference graph is the explicit
  EXTEND sibling.

## Upstream regulatory anchors

- **NIS2 (EU) 2022/2555, Article 21(2)(d)** — supply-chain security,
  including the security characteristics of direct suppliers and
  service providers, with periodic re-attestation. The inbound
  cross-reference at
  `content/mappings/nis2/article-21-2-d.yaml` (id `nis2:art-21-2-d`)
  currently backlinks `playbook.threat_intel_ingest@v1` and
  `playbook.contractual_obligations_tracker@v1`; closure of the
  inbound + outbound link against this playbook is EXTEND-sibling
  work.

## Sources

- OASIS CACAO v2.0 specification
- NIS2 Directive (EU) 2022/2555 — Article 21(2)(d)
- Community input — supply-chain security workflow scaffold
