# threat-intel-ingest

CACAO v2 starter playbook for ingesting external cyber threat
intelligence: pull an upstream feed (STIX 2.1 / TAXII or OCSF Threat
Intelligence) → normalise indicators against the OCSF Threat
Intelligence Inference event class → propagate the result to detection
(Sigma rule activation) and blocking (network / EDR blocklist) controls.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.threat_intel_ingest@v1`).
- `mappings.yaml` — regulatory/metrics overlay (real OSCAL / D3FEND /
  OCSF IDs plus NIS2 Art. 21(2)(d) and DORA Art. 19(2) cross-refs).
  Schema: `../../../schemas/playbook-mappings.schema.json`.

## Mappings

See [`mappings.yaml`](mappings.yaml) for the full outbound view of
the content model: OSCAL controls exercised, MITRE D3FEND defensive
techniques per step, OCSF event classes consumed/emitted, and the
NIS2 / DORA cross-references summarised below. The sibling EXTEND
card adds KPI metric files and the hooks block in this README.

### OSCAL — NIST SP 800-53 Rev. 5

| Control | Title | Role in this playbook |
|---|---|---|
| PM-16 | Threat Awareness Program | Anchors the playbook in an ongoing threat-awareness programme. |
| PM-16(1) | Automated Means for Sharing Threat Intelligence | Covers automated STIX 2.1 / TAXII ingest, the playbook's input contract. |
| SI-5 | Security Alerts, Advisories, and Directives | Receipt of external alerts and onward dissemination to detection. |
| SI-4 | System Monitoring | Detection-rule activation so subsequent telemetry generates alerts. |
| SC-7 | Boundary Protection | Blocklist propagation to perimeter / DNS / EDR enforcement. |

### MITRE D3FEND v1.0.0

| Step | Technique | Identifier |
|---|---|---|
| pull upstream feed | Operational Activity Mapping | D3-OAM |
| normalise STIX to OCSF | Identifier Activity Analysis | D3-IAA |
| propagate to blocklist | Inbound Traffic Filtering | D3-ITF |
| propagate to blocklist | Outbound Traffic Filtering | D3-OTF |
| propagate to blocklist | DNS Denylisting | D3-DNSDL |
| activate detection rule | Network Traffic Analysis | D3-NTA |

### OCSF v1.3.0

The playbook's input contract is a STIX 2.1 bundle delivered over
TAXII (or an equivalent STIX 2.1 endpoint), not an OCSF event — the
released OCSF v1.3.0 catalogue does not contain a dedicated
threat-intel ingest class, so the consumed side is asserted in
STIX-native terms (Indicator, Malware, Threat-Actor SDOs) rather
than pinned to an OCSF class. The only OCSF binding this playbook
commits to is the Detection Finding emitted when the activated
upstream Sigma rule matches subsequent telemetry.

| Event class | class_uid | Direction |
|---|---|---|
| Detection Finding | 2004 | emits |

### NIS2 Art. 21(2)(d) — supply-chain security

NIS2 Article 21(2)(d) obliges essential and important entities to
address the security characteristics of direct suppliers and service
providers, including periodic re-attestation of those characteristics.
Threat-intel ingest contributes the IOC-driven signal that lets an
operator detect when a known-bad indicator touches a supplier-adjacent
surface — feeding the supplier-attestation and re-attestation cadence
captured at `content/mappings/nis2/article-21-2-d.yaml` under
`nis2:art-21-2-d`.

### DORA Art. 19(2) — voluntary cyber-threat notification

DORA Article 19(2) of Regulation (EU) 2022/2554 permits voluntary
notification of significant cyber threats to the competent authority,
on a lighter content schema than a major-incident notification and
with no mandatory clock. The normalised indicator records and
Detection Finding events emitted by this playbook are the artefacts
an operator lifts into a voluntary notification payload; the inbound
mapping at `content/mappings/dora/article-19-and-28.yaml` under
`dora:art-19-cyber-threat-voluntary` closes the graph in the
regulator-side direction.

## KPI hooks

The metric catalog entries below bind to this playbook and ship in
[`content-model/examples/threat-intel-ingest/metrics/`](../../../content-model/examples/threat-intel-ingest/metrics/).
The shapes are validated against `content-model/metrics.schema.json`
in `tests/content_model/test_threat_intel_ingest_metrics.py`.

| Stable ID | Kind | One-line definition | File |
|---|---|---|---|
| `kpi.mttd_threat_intel_indicator@v1` | KPI — MTTD | Time from upstream feed publish to the Sigma rule firing on a matching event — the intel-to-detection latency this playbook is built to compress. | [`metrics/kpi.mttd_threat_intel_indicator.json`](../../../content-model/examples/threat-intel-ingest/metrics/kpi.mttd_threat_intel_indicator.json) |
| `kpi.mttr_blocklist_propagation@v1` | KPI — MTTR | Time from confidence-gate pass to blocklist-propagation completion across the operator's enforcement points (network / DNS / EDR). | [`metrics/kpi.mttr_blocklist_propagation.json`](../../../content-model/examples/threat-intel-ingest/metrics/kpi.mttr_blocklist_propagation.json) |
| `kpi.coverage_threat_intel_feed@v1` | KPI — coverage | Share of scheduled upstream poll batches successfully ingested and normalised in the window. | [`metrics/kpi.coverage_threat_intel_feed.json`](../../../content-model/examples/threat-intel-ingest/metrics/kpi.coverage_threat_intel_feed.json) |

These bind back to the playbook stable ID `playbook.threat_intel_ingest@v1`
and pin the CACAO step IDs they measure. The regulatory hooks in
`mappings.yaml` (NIS2 Art. 21(2)(d), DORA Art. 19(2)) reference these
metric IDs as the catalog-side anchors for evidence collection.

## Worked example, mappings, and compile-target emissions

This directory ships the **portable response only**. Cross-layer
artifacts (detection / control / telemetry / metrics worked examples,
`mappings.yaml`, KPI hooks, NIS2 / DORA regulator cross-references) and
the per-target compiler emissions
(`examples/{n8n,temporal,langgraph}/threat-intel-ingest/`) are authored
on the sibling CORE and EXTEND cards. Until those land, the only
contract this directory commits to is the CACAO v2 source and the Sigma
rule ID list below.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. Emitted
artifacts under `examples/{n8n,temporal,langgraph}/threat-intel-ingest/`
will be authored by the CORE card; this directory ships the portable
content only.

## Sigma rule references (upstream — SigmaHQ)

The "activate detection rule" step does **not** ship new Sigma rule
bodies. It activates upstream SigmaHQ rules that already cover the
indicator types the normalisation step emits. Operators bring their own
rule pack and the runtime resolves the activation list against the
indicator types observed in the bundle.

The rules below are a representative starting set — each ID is
copy-pasted from upstream SigmaHQ master and resolvable via the linked
URL. The list is not exhaustive; the runtime iterates the normalised
indicator types and toggles whichever upstream rules the operator's
rule pack already contains.

| Indicator class | Sigma rule ID (upstream) | Title | Path on SigmaHQ |
|---|---|---|---|
| Malicious IP — sign-in failure | `a3f55ebd-0c01-4ed6-adc0-8fb76d8cd3cd` | Malicious IP Address Sign-In Failure Rate | [rules/cloud/azure/identity_protection/azure_identity_protection_malicious_ip_address.yml](https://github.com/SigmaHQ/sigma/blob/master/rules/cloud/azure/identity_protection/azure_identity_protection_malicious_ip_address.yml) |
| Malicious IP — sign-in success | `36440e1c-5c22-467a-889b-593e66498472` | Malicious IP Address Sign-In Suspicious | [rules/cloud/azure/identity_protection/azure_identity_protection_malicious_ip_address_suspicious.yml](https://github.com/SigmaHQ/sigma/blob/master/rules/cloud/azure/identity_protection/azure_identity_protection_malicious_ip_address_suspicious.yml) |
| Threat-intel sign-in correlation | `a2cb56ff-4f46-437a-a0fa-ffa4d1303cba` | Azure AD Threat Intelligence | [rules/cloud/azure/identity_protection/azure_identity_protection_threat_intel.yml](https://github.com/SigmaHQ/sigma/blob/master/rules/cloud/azure/identity_protection/azure_identity_protection_threat_intel.yml) |
| Anonymising-network domain (DNS) | `b55ca2a3-7cff-4dda-8bdd-c7bfa63bf544` | DNS Query Tor .Onion Address - Sysmon | [rules/windows/dns_query/dns_query_win_tor_onion_domain_query.yml](https://github.com/SigmaHQ/sigma/blob/master/rules/windows/dns_query/dns_query_win_tor_onion_domain_query.yml) |
| Anonymising-network domain (Zeek) | `a8322756-015c-42e7-afb1-436e85ed3ff5` | DNS TOR Proxies | [rules/network/zeek/zeek_dns_torproxy.yml](https://github.com/SigmaHQ/sigma/blob/master/rules/network/zeek/zeek_dns_torproxy.yml) |
| Threat-actor C2 domain | `4d16c9a6-4362-4863-9940-1dee35f1d70f` | DPRK Threat Actor — C2 Communication DNS Indicators | [rules-emerging-threats/2024/TA/DPRK/dns_query_win_apt_dprk_malicious_domains.yml](https://github.com/SigmaHQ/sigma/blob/master/rules-emerging-threats/2024/TA/DPRK/dns_query_win_apt_dprk_malicious_domains.yml) |
| Threat-actor host IOC | `440a56bf-7873-4439-940a-1c8a671073c2` | GALLIUM IOCs | [rules-emerging-threats/2020/TA/GALLIUM/proc_creation_win_apt_gallium_iocs.yml](https://github.com/SigmaHQ/sigma/blob/master/rules-emerging-threats/2020/TA/GALLIUM/proc_creation_win_apt_gallium_iocs.yml) |

Pointers are versioned by upstream commit; the regression test under
`tests/content/test_threat_intel_ingest_playbook.py` walks each ID and
verifies it resolves on `master` so silent upstream renames surface as
a CI failure.

## Sources

- OASIS CACAO v2.0 specification
- OASIS STIX 2.1 specification
- OCSF v1.3 — Detection Finding (2004)
- SigmaHQ — upstream rule IDs referenced above
- ENISA — EU CSIRTs network operational guidance
