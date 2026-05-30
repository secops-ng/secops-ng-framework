# threat-intel-ingest

CACAO v2 starter playbook for ingesting external cyber threat
intelligence: pull an upstream feed (STIX 2.1 / TAXII or OCSF Threat
Intelligence) → normalise indicators against the OCSF Threat
Intelligence Inference event class → propagate the result to detection
(Sigma rule activation) and blocking (network / EDR blocklist) controls.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.threat_intel_ingest@v1`).
- `mappings.yaml` — regulatory/metrics overlay (SKELETON: placeholder
  OSCAL / D3FEND / OCSF entries; NIS2 Art. 21(2)(d) and DORA Art. 19(2)
  cross-refs populated). Schema:
  `../../../schemas/playbook-mappings.schema.json`.

## Mappings

See [`mappings.yaml`](mappings.yaml) for the outbound view of the
content model: OSCAL controls exercised, MITRE D3FEND defensive
techniques per step, OCSF event classes consumed/emitted, and NIS2 /
DORA cross-references. SKELETON ships structural pointers only; the
sibling CORE card populates real catalog IDs and the EXTEND card adds
KPI metric files plus the hooks block in this README.

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
- OCSF v1.3 — Threat Intelligence Inference (5005) and Security Finding (2001)
- SigmaHQ — upstream rule IDs referenced above
- ENISA — EU CSIRTs network operational guidance
