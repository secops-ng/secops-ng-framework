# content/telemetry/

OCSF event schema bindings and sample payloads. Every playbook expects its
input events to conform to one of the bindings defined here.

Each binding is a JSON document validated by
`content-model/telemetry.schema.json`. Files are named
`<stable_id>.json` (the `@` in `stable_id` is preserved in the filename).

## Bindings

| Stable ID                                  | OCSF version | Class UID | Class name                     | Consumers                                                                                         |
|--------------------------------------------|--------------|-----------|--------------------------------|---------------------------------------------------------------------------------------------------|
| `telemetry.ocsf.account_change@v1`         | 1.4.0        | 3001      | Account Change                 | `playbook.identity_compromise@v1`                                                                 |
| `telemetry.ocsf.api_activity@v1`           | 1.4.0        | 6003      | API Activity                   | `playbook.identity_compromise@v1`                                                                 |
| `telemetry.ocsf.authentication@v1`         | 1.4.0        | 3002      | Authentication                 | `playbook.identity_compromise@v1`                                                                 |
| `telemetry.ocsf.cloud_resource_inventory@v1` | 1.4.0        | 5023      | Cloud Resources Inventory Info | `playbook.cloud_misconfiguration@v1`                                                              |
| `telemetry.ocsf.compliance_finding@v1`     | 1.4.0        | 2003      | Compliance Finding             | `playbook.vuln_intake@v1`, `playbook.ransomware_containment@v1`, `playbook.data_exfil@v1`         |
| `telemetry.ocsf.detection_finding@v1`      | 1.4.0        | 2004      | Detection Finding              | `playbook.detection_engineering@v1`, `playbook.threat_intel_ingest@v1`                            |
| `telemetry.ocsf.device_inventory_info@v1`  | 1.4.0        | 5001      | Device Inventory Info          | `playbook.asset_management@v1`                                                                    |
| `telemetry.ocsf.email_activity@v1`         | 1.4.0        | 4009      | Email Activity                 | `playbook.phishing_triage@v1`                                                                     |
| `telemetry.ocsf.email_url_activity@v1`     | 1.4.0        | 4012      | Email URL Activity             | `playbook.phishing_triage@v1`                                                                     |
| `telemetry.ocsf.file_activity@v1`          | 1.4.0        | 1001      | File System Activity           | `playbook.phishing_triage@v1`                                                                     |
| `telemetry.ocsf.incident_finding@v1`       | 1.4.0        | 2005      | Incident Finding               | `playbook.incident_management@v1`                                                                 |
| `telemetry.ocsf.network_activity@v1`       | 1.4.0        | 4001      | Network Activity               | `playbook.network_security@v1`, `playbook.ddos_response@v1`, `playbook.ransomware_containment@v1` |
| `telemetry.ocsf.patch_state@v1`            | 1.4.0        | 5004      | Operating System Patch State   | `playbook.patch_management@v1`                                                                    |
| `telemetry.ocsf.process_activity@v1`       | 1.4.0        | 1007      | Process Activity               | `playbook.ransomware_containment@v1`, `playbook.post_incident_review@v1`                          |
| `telemetry.ocsf.vulnerability_finding@v1`  | 1.4.0        | 2002      | Vulnerability Finding          | `playbook.vuln_intake@v1`                                                                         |

Class UIDs are pinned to OCSF v1.4.0; do not introduce a binding without
verifying its class UID against the upstream schema at
<https://schema.ocsf.io/1.4.0/>. The table above lists every artifact in
this directory — an earlier revision named 8 of the 12 then shipped, so keep
it complete or the catalogue looks smaller than it is.

A `stable_id` is a join key. Where the shorter form an asserting playbook
already uses differs from the upstream class name (for example
`cloud_resource_inventory` against *Cloud Resources Inventory Info*), the
`stable_id` keeps the form the refs use and `ocsf.class_name` carries the
exact upstream name — renaming the key would break the refs it exists to
resolve.
