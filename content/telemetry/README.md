# content/telemetry/

OCSF event schema bindings and sample payloads. Every playbook expects its
input events to conform to one of the bindings defined here.

Each binding is a JSON document validated by
`content-model/telemetry.schema.json`. Files are named
`<stable_id>.json` (the `@` in `stable_id` is preserved in the filename).

## Bindings

| Stable ID                              | OCSF version | Class UID | Class name           | Consumers                              |
|----------------------------------------|--------------|-----------|----------------------|----------------------------------------|
| `telemetry.ocsf.account_change@v1`     | 1.4.0        | 3001      | Account Change       | `playbook.identity_compromise@v1`      |
| `telemetry.ocsf.api_activity@v1`       | 1.4.0        | 6003      | API Activity         | `playbook.identity_compromise@v1`      |
| `telemetry.ocsf.authentication@v1`     | 1.4.0        | 3002      | Authentication       | `playbook.identity_compromise@v1`      |
| `telemetry.ocsf.email_activity@v1`     | 1.4.0        | 4009      | Email Activity       | `playbook.phishing_triage@v1`          |
| `telemetry.ocsf.email_url_activity@v1` | 1.4.0        | 4012      | Email URL Activity   | `playbook.phishing_triage@v1`          |
| `telemetry.ocsf.file_activity@v1`      | 1.4.0        | 1001      | File System Activity | `playbook.phishing_triage@v1`          |
| `telemetry.ocsf.detection_finding@v1`  | 1.4.0        | 2004      | Detection Finding    | `playbook.detection_engineering@v1`, `playbook.threat_intel_ingest@v1` |
| `telemetry.ocsf.incident_finding@v1`   | 1.4.0        | 2005      | Incident Finding     | `playbook.incident_management@v1`      |

Class UIDs are pinned to OCSF v1.4.0; do not introduce a binding without
verifying its class UID against the upstream schema at
<https://schema.ocsf.io/1.4.0/>.
