# SecOps-NG Vulnscan — Deployment Notes

Status: draft (community review)
Target deployment: Nebul sovereign cloud (EU-hosted) hosting the
Controller stack; small-office or home-office estate as the Contained
network reachable via site-to-site VPN.

This is a working deployment shape, not a hard recipe. Operators on
other EU-hosted infrastructure (Hetzner, Exoscale, OVHcloud, Scaleway,
IONOS, or self-hosted) can substitute equivalents; the design has no
Nebul-specific dependency.

---

## 1. Layout

```
+-----------------------------------------------------+
|                  Nebul (EU region)                  |
|                                                     |
|  +------------------+      +---------------------+  |
|  |   Controller VM  |      | Scan Engine subnet  |  |
|  |  Temporal worker |      |  (private, no IGW)  |  |
|  |  DefectDojo      |<----->                     |  |
|  |  reportgen       | mTLS |  ephemeral engines  |  |
|  +--------+---------+      +----------+----------+  |
|           |                           |             |
|           | mgmt VPC                  | scan VPC    |
+-----------|---------------------------|-------------+
            |                           |
            | site-to-site VPN          | site-to-site VPN
            |                           |
+-----------v---------------------------v-------------+
|                Operator small-office                |
|                                                     |
|  +------------------+      +---------------------+  |
|  | Operator jump    |      | Contained VLAN      |  |
|  | host (SSH)       |      | 10.10.10.0/24       |  |
|  +------------------+      |  cameras, printers, |  |
|                            |  NAS, IoT           |  |
|                            +---------------------+  |
+-----------------------------------------------------+
```

Two VPN tunnels, one VPC per role:

- mgmt tunnel: operator → Controller, for orchestration and dashboard.
- scan tunnel: Scan Engine subnet → Contained VLAN, for probes.

Neither VPC has an internet gateway during scan windows. Feed updates
and image pulls happen outside the scan window via a maintenance
gateway that is detached when scans run.

---

## 2. Nebul resource shape

A reference layout for a single-tenant Controller plus an elastic Scan
Engine subnet. Values are starting points, not requirements.

| Component        | Resource              | Notes                                     |
|------------------|-----------------------|-------------------------------------------|
| Controller VM    | 4 vCPU, 8 GiB, 100 GB | Hosts Temporal, DefectDojo, reportgen     |
| Scan Engine pool | 2 vCPU, 4 GiB each    | Ephemeral; one per active engine activity |
| mgmt VPC         | /28                   | Controller + operator jump endpoint       |
| scan VPC         | /27                   | Scan engines; no shared subnet with mgmt  |
| Object storage   | EU region, encrypted  | PDF report retention + DefectDojo backups |
| Secrets          | Nebul secrets manager | Scan credentials, mTLS keys               |

The Controller is the only durable VM. Scan engines come up per
activity and are destroyed at end of run.

---

## 3. Firewall rules

### 3.1 At the Nebul layer

| From                | To                       | Ports                        | Direction | Notes                  |
|---------------------|--------------------------|------------------------------|-----------|------------------------|
| Operator jump       | Controller               | 22, 8080 (DefectDojo)        | inbound   | mgmt tunnel only       |
| Controller          | Scan Engine subnet       | 7233 (Temporal), per-engine  | inbound   | mTLS                   |
| Scan Engine subnet  | Controller (DefectDojo)  | 443 (ingest)                 | inbound   | one-way findings push  |
| Scan Engine subnet  | Internet                 | anything                     | DENY      | default-deny outbound  |
| Scan Engine subnet  | Scan Engine subnet       | anything                     | DENY      | intra-subnet isolation |
| Scan Engine subnet  | Contained VLAN (per IP)  | per-engine port set          | outbound  | scan tunnel            |
| Contained VLAN      | Anywhere                 | anything                     | DENY      | targets cannot egress  |

Intra-subnet deny on the Scan Engine subnet is the most often missed
rule. Without it, a compromised engine has a populated neighbourhood
of other attack tools to pivot through.

### 3.2 At the operator small-office gateway

| From                  | To                  | Ports             | Direction | Notes                                  |
|-----------------------|---------------------|-------------------|-----------|----------------------------------------|
| Scan tunnel endpoint  | Contained VLAN      | per-engine ports  | inbound   | rule is destination-IP specific        |
| Contained VLAN        | LAN / internet      | anything          | DENY      | enforce that targets cannot phone home |
| Contained VLAN        | Contained VLAN      | anything          | DENY      | optional but recommended               |

The Contained VLAN should be a dedicated broadcast domain. Putting
the printer that everyone in the office prints to in the Contained
VLAN during a scan is a fine way to learn about office politics.
Either accept that scans run after-hours, or move the scope to a
mirror VLAN.

---

## 4. Concurrency limits

The default profile keeps the scan polite enough to run against a
small-office estate without taking it down. Tune in the Temporal
worker config:

```yaml
workflow: VulnscanWorkflow
concurrency:
  max_parallel_engines: 3        # at most 3 engines running at once
  max_parallel_targets: 8        # per engine, across the scope
  per_target_rate_qps: 25        # per engine, against one target
  thorough_profile_multiplier: 0.5  # halve all the above on `thorough`
```

Rules of thumb:

- A /24 of office equipment tolerates `balanced` end-to-end in roughly
  45 minutes; `thorough` in 2-4 hours. Cameras and consumer IoT are
  the long tail.
- One engine per host is fine for `balanced`. `thorough` plus more
  than one ZAP active scan against the same target is overkill and
  often falls over the target.
- If targets include anything safety-critical (industrial controls,
  medical devices), do not use this workflow. It is not designed for
  that risk profile.

---

## 5. Sovereignty and data residency

- All durable storage (DefectDojo Postgres, object storage for
  reports, Temporal event log) is in an EU Nebul region.
- Scan engine images are pulled from EU-hosted mirrors where
  available; where the upstream is non-EU, the operator caches to an
  EU-hosted registry and points the worker at the mirror.
- No telemetry from engines or the orchestrator leaves the operator
  estate. Engines with phone-home defaults (typically commercial
  scanners) are configured offline or replaced with their
  community equivalent.

---

## 6. Operational runtime checklist

Before the first scan against a new estate:

- [ ] Both VPN tunnels up; route tables confirm Controller cannot
      reach Contained VLAN directly, only via the Scan Engine subnet.
- [ ] Scan Engine subnet egress default-deny verified by attempting
      `curl https://example.com` from a scratch container.
- [ ] DefectDojo reachable from operator jump host; not reachable
      from anywhere else.
- [ ] Engine image digests pinned in the worker config match what is
      in the registry.
- [ ] Feed snapshot timestamp within operator's freshness policy.
- [ ] Scope file in the deployment repo committed and tagged for the
      run.

If any of those fail, the worker's fail-closed checks will refuse to
start the scan. That is the intended behaviour.

---

## 7. See also

- `ARCHITECTURE.md` — design rationale.
- `RUNBOOK.md` — operator steps.
- `THREAT-MODEL.md` — what the design defends against.
