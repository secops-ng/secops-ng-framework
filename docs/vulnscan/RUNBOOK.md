# SecOps-NG Vulnscan — Operator Runbook

Status: draft (community review)
Audience: operator running a scan against a small-office or home-office
estate.

This runbook covers the end-to-end happy path: bring up the stack,
dispatch a scan, view results, retrieve the PDF report. Failure modes
and recovery live in `THREAT-MODEL.md` and `DEPLOYMENT.md`.

---

## 0. Prerequisites

- Docker Engine 24+ with Compose v2 on the Controller host.
- Network access from Controller into the Scan Engine network, and
  from Scan Engine into the Contained network, configured per
  `DEPLOYMENT.md`.
- Temporal CLI (`temporal`) installed locally, or a reachable
  Temporal frontend on the Controller.
- The operator's `.env` file populated; no credentials in shell
  history.

---

## 1. Bring up the stack

```bash
cd deploy/vulnscan
docker compose pull
docker compose up -d
```

This starts:

- `temporal` — workflow engine.
- `temporal-worker-vulnscan` — registers the `VulnscanWorkflow` and
  its activities.
- `defectdojo` + `defectdojo-postgres` — findings DB and UI.
- `reportgen` — PDF renderer.

Engine containers (Nessus, OpenVAS, Nikto, Wapiti, ZAP) are NOT
started by `up`. They are built in the Controller image and spawned
per-activity by the Temporal worker. This is intentional: an idle
engine should not exist.

Verify:

```bash
docker compose ps
temporal workflow list --address $TEMPORAL_ADDRESS
curl -sf http://localhost:8080/health      # defectdojo
```

---

## 2. Configure the target scope

Targets live in `deploy/vulnscan/scopes/<name>.yaml` on the operator's
deployment host (operational data — do not commit scope files into
this framework repo; they belong in the operator's private deployment
checkout):

```yaml
name: small-office-001
cidr: 10.10.10.0/24
include:
  - 10.10.10.21       # camera
  - 10.10.10.22       # printer
  - 10.10.10.40       # NAS
profile: balanced     # one of: light | balanced | thorough
http_endpoints:
  - https://10.10.10.40/
```

Commit scope files in your private deployment repository — never in
this framework repo. Target IPs are operational data.

---

## 3. Dispatch a scan

### Via Temporal CLI

```bash
temporal workflow start \
  --task-queue vulnscan \
  --type VulnscanWorkflow \
  --workflow-id "scan-$(date -u +%Y%m%dT%H%M%SZ)-small-office-001" \
  --input "$(jq -c . deploy/vulnscan/scopes/small-office-001.yaml)"
```

### Via REST

```bash
curl -sS -X POST "http://$TEMPORAL_ADDRESS/api/v1/namespaces/default/workflows" \
  -H "Content-Type: application/json" \
  --data @- <<'JSON'
{
  "workflow_id": "scan-<ts>-small-office-001",
  "workflow_type": "VulnscanWorkflow",
  "task_queue": "vulnscan",
  "input": { "scope_ref": "small-office-001" }
}
JSON
```

The workflow returns immediately; execution is durable. The
operator can disconnect.

---

## 4. Watch progress

```bash
temporal workflow describe --workflow-id <id>
temporal workflow show --workflow-id <id> --follow
```

Each activity emits a heartbeat. A long-running engine (Nessus on a
thorough profile against a /24 can take an hour or more) is healthy
as long as heartbeats arrive.

If an engine fails, the activity is retried per the workflow's
retry policy. The whole scan does not fail because one engine
crashed.

---

## 5. View findings in DefectDojo

Open the DefectDojo UI:

```
http://<controller>:8080/
```

Findings are grouped under an Engagement named after the workflow
ID. The dashboard shows per-engine breakdown, severity counts, and
de-duplicated finding clusters.

Suggested operator triage path:

1. Filter to severity High and Critical, regardless of engine.
2. Cross-reference Medium findings that two or more engines agree on
   — agreement is a stronger signal than a single engine's verdict.
3. Tag false positives; the next scan against the same scope will
   inherit those tags.

---

## 6. Retrieve the PDF report

When `VulnscanWorkflow` completes, the final activity writes the PDF
to a path emitted in the workflow result:

```bash
temporal workflow result --workflow-id <id>
```

Expected shape:

```json
{
  "status": "OK",
  "summary": "scan complete — 27 findings, 0 critical",
  "artifacts": ["/var/vulnscan/reports/scan-<id>.pdf"]
}
```

Retrieve it from the Controller:

```bash
scp controller:/var/vulnscan/reports/scan-<id>.pdf ./
```

Reports are retained on the Controller per the operator's retention
policy. Default is 90 days; tune in `reportgen` env vars.

---

## 7. Tear down

Between scan runs the stack can stay up — it costs little when idle
because engine containers are not running. To stop fully:

```bash
docker compose down
```

To stop AND remove findings history:

```bash
docker compose down -v   # destroys defectdojo postgres volume
```

The destructive form is irreversible and should not be the default.

---

## 8. See also

- `ARCHITECTURE.md` — what the stack actually is.
- `THREAT-MODEL.md` — what could go wrong and what the design assumes.
- `DEPLOYMENT.md` — putting this on Nebul against a real small-office
  estate.
