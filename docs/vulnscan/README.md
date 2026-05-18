# Vulnscan documentation

Documentation for the SecOps-NG multi-engine dynamic vulnerability
scanning workflow.

- `ARCHITECTURE.md` — what the system is and how it is wired.
- `RUNBOOK.md` — operator steps to bring it up, dispatch a scan, and
  retrieve the report.
- `THREAT-MODEL.md` — STRIDE on the Scan Engine network and the
  containment guarantees.
- `DEPLOYMENT.md` — Nebul (or other EU-hosted) deployment notes for a
  small-office estate.

Status: draft, community review pending. The corresponding
implementation lives in this repo alongside the docs:

- `src/secops_ng/workflows/vulnscan.py` — `VulnscanWorkflow` definition
  and activity signatures (library code).
- `workflows/vulnscan.py` — runnable end-user template (cookbook).
- `deploy/vulnscan/` — `docker-compose.yml`, scope file examples, and
  worker config for operators bringing the stack up.

The docs describe the target shape; implementation lands incrementally
and references back to these documents.
