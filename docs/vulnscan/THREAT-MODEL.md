# SecOps-NG Vulnscan — Threat Model

Status: draft (community review)
Method: STRIDE applied to the Scan Engine network and its boundary
with the Controller and Contained networks.

The premise of this document is that the act of scanning is itself a
risk. A vulnerability scanner is, by design, an attack tool with
restraint. The threat model below states what restraints the design
enforces, what it relies on the operator to enforce, and what it
considers out of scope.

---

## 1. Assets

| Asset                          | Sensitivity | Notes                                  |
|--------------------------------|-------------|----------------------------------------|
| Scan engines (running)         | High        | Attack tooling on a privileged subnet  |
| Scanning credentials           | High        | Used for authenticated probes          |
| Findings database (DefectDojo) | High        | Inventory of weaknesses on the estate  |
| Generated reports (PDF)        | High        | Same inventory in transportable form   |
| Engine images / feed snapshots | Medium      | Tampering would skew findings          |
| Temporal workflow history      | Medium      | Records what was scanned, when, by whom|

---

## 2. Trust boundaries

```
+-------------------+         +-------------------+         +-------------------+
|   Operator host   |  ssh    |    Controller     |   no    |  Public internet  |
|                   |-------->|                   |  route  |                   |
+-------------------+         +---------+---------+         +-------------------+
                                        |
                                        | Temporal task dispatch (mTLS)
                                        v
                              +---------+---------+
                              |   Scan Engine     |
                              |     network       |
                              +---------+---------+
                                        |
                                        | per-IP allow, no egress
                                        v
                              +-------------------+
                              | Contained network |
                              +-------------------+
```

Three boundaries:

- B1: Operator → Controller. Out of scope for this design beyond
  "use SSH key auth, no shared shells, no credentials in env on the
  bastion".
- B2: Controller → Scan Engine network. The only trusted inbound
  channel into the Scan Engine network. Carries Temporal activity
  dispatch and findings exfiltration to DefectDojo.
- B3: Scan Engine → Contained network. The blast-radius boundary the
  rest of this document is concerned with.

---

## 3. STRIDE on the Scan Engine network

### Spoofing

| Threat                                                      | Mitigation                                                                                                         |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| Rogue target in Contained network impersonates another IP   | Static leases or DHCP reservation; scan output records MAC alongside IP; firewall ACL is keyed on the assigned IP. |
| Attacker on Controller submits a fake scan workflow         | Temporal frontend requires mTLS; operator identity is bound to workflow input via a signed scope reference.        |
| Engine container impersonates DefectDojo to siphon findings | Findings ingress to DefectDojo is one-way and over a fixed listener; engines do not initiate sessions elsewhere.   |

### Tampering

| Threat                                                  | Mitigation                                                                                                |
|---------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| Compromised engine container alters scan output         | Engines are stateless and rebuilt per run from pinned image digests; findings are written, not edited.    |
| Compromised target alters its responses to evade        | Out of scope — accepted residual risk; partially mitigated by multi-engine cross-check.                   |
| Feed snapshot is poisoned upstream                      | Feeds are pulled before the scan window from a known mirror; snapshot hash recorded in workflow history.  |
| Findings DB tampering                                   | DefectDojo is on the Controller side of B2; ingress port is the only attack surface; volumes backed up.   |

### Repudiation

| Threat                                              | Mitigation                                                                                                          |
|-----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| Operator claims a scan never happened or vice versa | Every scan is a Temporal workflow with a durable history including operator identity, scope, profile, and timings.  |
| Engine output cannot be tied to engine version      | Activity inputs include engine image digest and feed hash; recorded in workflow event log.                          |

### Information disclosure

| Threat                                                     | Mitigation                                                                                                  |
|------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| Findings DB read by an unauthorised party                  | DefectDojo on the Controller, reachable only via the operator jump host; no public ingress.                 |
| Compromised engine exfiltrates findings to the internet    | Scan Engine network has no internet route during the scan window; outbound default-deny at the gateway.     |
| Scanning credentials leak from an engine container         | Credentials are injected per activity, never baked into the image; engine container is destroyed after run. |
| PDF reports retained beyond need                           | Retention policy in `reportgen`; default 90 days; off-host backup of reports is operator decision.          |

### Denial of service

| Threat                                              | Mitigation                                                                                                   |
|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| Scan saturates the Contained network                | Concurrency limit on activity dispatch; per-engine pacing; "light" profile available for fragile estates.    |
| Scan crashes a fragile target (camera, printer)     | Profile selection is the operator's choice; intrusive checks gated behind `thorough`; documented in runbook. |
| An engine OOMs and takes down its host              | Engines are containerised with memory limits; Temporal restarts the activity.                                |

### Elevation of privilege

| Threat                                                     | Mitigation                                                                                                          |
|------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| Engine container escapes to the host                       | Engines run as non-root, no `--privileged`, no host bind mounts other than read-only image content, seccomp default.|
| Compromised engine pivots through Scan Engine network      | Engines cannot reach each other (intra-subnet deny); only outbound rule is to specific Contained IPs.               |
| Compromised engine reaches the Controller                  | Reverse path closed at the gateway; only the Controller initiates connections into the Scan Engine network.         |

---

## 4. Containment guarantees (the short version)

If a scan-engine container is compromised mid-scan, the design
promises:

1. The compromised engine cannot reach the public internet.
2. The compromised engine cannot reach the Controller, the findings
   DB, or any other engine.
3. The compromised engine can only reach the Contained-network IPs it
   was already authorised to probe, on the ports it was already
   authorised to probe — there is no additional lateral surface
   because compromise happened mid-run.
4. The compromised engine is destroyed at end of activity, regardless
   of whether the workflow succeeds.

What the design does NOT promise:

1. That the compromised engine could not corrupt its own findings
   within the run. Mitigation is multi-engine cross-check, not
   per-engine integrity.
2. That a target in the Contained network is unaffected. Targets
   that are themselves trivially exploitable are out of scope —
   that is, after all, what the scan is meant to surface.

---

## 5. Scanning credentials

When the operator chooses authenticated scanning:

- Credentials are stored as Temporal-injected secrets and unsealed
  only into the activity that uses them.
- The credential's scope is documented per-target. The expectation
  is read-only and audit-only; if the credential set includes
  write-capable accounts, the operator has explicitly opted in.
- Credentials are rotated after every scan run by the operator's
  IAM, not by this workflow. The workflow refuses to start if a
  credential is older than the operator's configured max age.

---

## 6. Fail-closed posture

The Temporal worker treats the following as scan-fatal and aborts
without writing findings:

- Inability to verify the Scan Engine network has no default route.
- Inability to verify the Contained-network firewall ACL matches
  the scope file.
- Engine image digest mismatch versus the pinned manifest.
- Feed snapshot hash mismatch versus the pinned manifest.

A scan that cannot prove its own containment does not run.

---

## 7. See also

- `ARCHITECTURE.md` — what the system is.
- `RUNBOOK.md` — how to operate it.
- `DEPLOYMENT.md` — how to put it where it has to live.
