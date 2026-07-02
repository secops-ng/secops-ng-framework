# cloud_misconfiguration — cookbook walkthrough

Cloud-posture (CSPM) remediation workflow under NIS2 Article 21(2)(e),
NIS2 Article 21(2)(i), DORA Article 9(4)(a) as operationalised by the
JC RTS on the ICT risk management framework (Commission Delegated
Regulation (EU) 2024/1774), CRA Annex I §1(b) secure-by-default and
Annex I §1(j) minimal-attack-surface essential-cybersecurity
requirements, and GDPR Article 30 Record of Processing Activity for
the resource-ownership enrichment and owner-notification processing.
The `playbook.cloud_misconfiguration@v1` CACAO playbook ingests a
posture finding from the operator's CSPM / posture-management layer,
enriches it with the affected resource's ownership context, suppresses
known-benign or already-exception'd deviations, notifies the resource
owner along the operator's pre-bound channel, drives an attested
guided remediation (an IaC pull request or a runbook execution), and
re-scans the same baseline rule against the resource to verify the
fix actually stuck. A failing re-scan escalates and is tracked
against the recurring-misconfiguration KRI so chronic deviation
surfaces in the metrics layer rather than quietly closing on an
unverified remediation attempt.

This playbook is a **companion** to `infra_posture_management` rather
than a duplicate: infra_posture_management is the *scheduled*
posture-evidence-emitting cadence over the operator's in-scope
manifest (audit-facing continuous re-execution against the policy
version in force); cloud_misconfiguration is the *per-finding*
remediation cadence that reacts to a single deviation the CSPM layer
has surfaced. The two lanes share the CSPM baseline surface and the
Compliance Finding telemetry shape; they differ in trigger (schedule
vs. finding) and in output (posture-evidence artifact series vs.
per-case remediation trail).

This walkthrough wires the playbook through all three reference
compilers (n8n, Temporal, LangGraph) and shows where the ingest, the
enrichment, the false-positive gate, the owner notification, the
guided remediation, the re-scan, and the escalation land in each
target.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are *three of three* reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 1. Source of truth

```
content/playbooks/cloud_misconfiguration/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay
└── playbook.cacao.json          # canonical CACAO v2 source (playbook.cloud_misconfiguration@v1)

content/mappings/nis2/article-21-2-e.yaml
                                  # NIS2 Art. 21(2)(e) inbound anchor —
                                  # security in network and information
                                  # systems acquisition, development
                                  # and maintenance; backlinks
                                  # playbook.cloud_misconfiguration@v1
                                  # as the operational discharge of
                                  # baseline-deviation and attested
                                  # remediation
content/mappings/nis2/article-21-2-i.yaml
                                  # NIS2 Art. 21(2)(i) inbound anchor —
                                  # HR security, access control and
                                  # asset management; backlinks the
                                  # enrich (asset management) and the
                                  # guided-remediation (least-privilege
                                  # tightening) steps
content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml
                                  # DORA Art. 9(4)(a) inbound anchor
                                  # operationalised by the JC RTS on
                                  # ICT risk management framework
                                  # (Commission Delegated Regulation
                                  # (EU) 2024/1774, Art. 10) —
                                  # documented vulnerability and
                                  # patch management procedures;
                                  # backlinks playbook.cloud_misconfiguration@v1
                                  # for the cloud-baseline-deviation
                                  # slice of the vulnerability-management
                                  # discipline
content/mappings/cra/annex-i-1-essential-cybersecurity.yaml
                                  # CRA Annex I §1(b) secure-by-default
                                  # and Annex I §1(j) minimal-attack-
                                  # surface essential-cybersecurity
                                  # requirements — playbook.cloud_misconfiguration@v1
                                  # is the operational trail that
                                  # keeps deployed cloud resources
                                  # against the secure-by-default
                                  # posture and the minimal-attack-
                                  # surface envelope after a deviation
                                  # is observed
content/mappings/gdpr/data-flow-cloud_misconfiguration.md
                                  # GDPR Art. 30 Record of Processing
                                  # Activity for the resource-ownership
                                  # enrichment and owner-notification
                                  # processing this playbook operates
                                  # on
```

The CACAO source is canonical. The two `if-condition` branches
(known-false-positive gate; remediation-verified gate), the six
`action` steps, and the one `start` / one `end` wiring nodes are the
deterministic policy the playbook *means* — an ingest step feeding an
enrichment feeding a false-positive gate that either short-circuits
via the suppression branch or drives the linear notification →
remediation → re-scan chain to the verified-fix terminal, with the
failing re-scan routing into escalation before terminating on the
same terminal end. The three worked examples under
`examples/{n8n,temporal,langgraph}/cloud_misconfiguration/` are the
same playbook compiled into three orchestrator idioms. Everything
else — the CSPM layer the ingest step consumes, the ownership graph
the enrichment step reads, the suppression-list store, the
notification channel per severity, the IaC pull-request or runbook
surface the guided remediation acts through, and the escalation
paging channel — is the operator's data plane.

## 2. CACAO topology and lifecycle binding

The playbook ships eleven steps: one `start`, six `action`, two
`if-condition`, and one terminal `end` reached from three inbound
edges (suppression-close, verified-fix, and escalate-then-close). The
first `if-condition` (`known false positive?`) fires on
`__is_known_false_positive__`; `on_success` routes into the
suppression close, `on_failure` routes into the linear remediation
chain. The second `if-condition` (`remediation verified?`) fires on
`__remediation_verified__`; `on_success` routes directly to the end,
`on_failure` routes into the escalation step which then terminates on
the same end so the case is closed under both branches with an
audit-evident trail.

| Step suffix    | Step                          | Discipline                                                                                                                                                                                                                                        | Status         |
|----------------|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000000001`   | cloud-misconfig-start         | edge wiring only — no body                                                                                                                                                                                                                        | n/a            |
| `…000000002`   | ingest finding                | receive the Compliance Finding from the operator's CSPM / posture-management layer (rule fingerprint, affected resource, evaluated baseline, first-observed timestamp) and normalise it into the case shape the rest of the workflow reads       | operator-bound |
| `…000000003`   | enrich resource and owner     | resolve tenant, account, region, resource type, tags, and accountable owner against the operator's cloud-inventory and ownership graph; annotate the case with the routing context the notification and escalation steps read against            | operator-bound |
| `…000000004`   | known false positive?         | `if-condition` — branches on `__is_known_false_positive__` (true → suppress and close; false → notify owner)                                                                                                                                       | n/a            |
| `…000000005`   | suppress and close            | record the suppression against the operator's exception ledger (rule fingerprint, resource id, exception owner, expiry) and close the case without a remediation attempt so an already-triaged benign deviation stops re-paging owners           | operator-bound |
| `…000000006`   | notify owner                  | hand off along the operator's pre-bound channel per `__severity__` (ticketing / chat / paging) carrying the finding, the affected resource, the violated baseline, and a pointer to the guided-remediation runbook the next step references     | operator-bound |
| `…000000007`   | guided remediation            | apply the remediation bound to the violated baseline rule via an attested change — an IaC pull request against the operator's declarative-infrastructure repository or a runbook execution the operator's platform automates                    | operator-bound |
| `…000000008`   | re-scan                       | targeted re-evaluation of the same baseline rule against the affected resource; writes `__remediation_verified__` for the next gate                                                                                                               | operator-bound |
| `…000000009`   | remediation verified?         | `if-condition` — branches on `__remediation_verified__` (true → cloud-misconfig-end; false → escalate)                                                                                                                                             | n/a            |
| `…00000000b`   | escalate                      | compose the escalation payload (finding, attempted remediation, failing re-scan evidence) and hand off along the operator's pre-bound paging channel; the case is tracked against the recurring-misconfiguration KRI                              | operator-bound |
| `…00000000a`   | cloud-misconfig-end           | edge wiring only — no body (closure, from any of: suppression, verified-fix, escalate-then-close)                                                                                                                                                 | n/a            |

All six action steps carry the CACAO I/O contract (`in_args` /
`out_args`) plus `x_secops_ng` reference bundles (detection, control,
telemetry, metric). One execution short-circuits through the
suppression branch when the deviation is known-benign, or runs the
linear four-step remediation chain (notify → remediate → re-scan →
close) exactly once and — if the re-scan does not verify — takes the
escalation branch before closure. Per-case metric accounting into
the MTTD / MTTR / cloud-posture-coverage KPI catalogue and the
recurring-misconfig KRI is unambiguous.

> The playbook maturity is `Shipped` across all three compile
> targets: the n8n, Temporal, and LangGraph worked examples all ship
> committed emitter output today, and cross-target byte-parity
> goldens live under `tests/examples/cloud_misconfiguration/` (see
> § 5).

## 3. Lifecycle contract — the six action states

The per-case payload — finding, affected resource, ownership context,
suppression decision, notification stamp, remediation attempt, and
re-scan verdict — is remediation-oriented content that carries
operator-side identifiers (account labels, resource ids, tenant
markers, owner tags). The inbound GDPR Art. 30 Record of Processing
Activity at
[`content/mappings/gdpr/data-flow-cloud_misconfiguration.md`](../../content/mappings/gdpr/data-flow-cloud_misconfiguration.md)
covers the resource-ownership enrichment and owner-notification
processing the six steps below operate on; lawful-basis-grounded in
GDPR Art. 6(1)(f) legitimate interests with Art. 6(1)(c) legal
obligation as the secondary basis where NIS2 Art. 21(2)(e) / (2)(i)
transposition applies. Personal data does not sit on the finding
payload itself — the resource configuration is what the workflow
reads — but the owner-notification leg dereferences a natural
person's contact identifier via the ownership graph, and the RoPA
covers that processing per AGENTS.md §3.

**ingest finding** (`…000000002`)
:   Ingest step. Consumes the Compliance Finding the operator's CSPM
    / posture-management layer emits (rule fingerprint, affected
    resource, evaluated baseline, first-observed timestamp) and
    normalises it into the case shape the rest of the workflow reads
    against. Anchored on MITRE D3FEND v1.0.0 `D3-RAPA` (Resource
    Access Pattern Analysis) — the CSPM / posture-management layer's
    continuous evaluation of cloud resources against a documented
    baseline is the Detect-tactic resource-access-pattern-analysis
    this step's input is sourced from. Anchored on OSCAL CM-2
    (Baseline Configuration) and SI-4 (System Monitoring) —
    documented baseline the CSPM rule fingerprint is evaluated
    against, and the system-monitoring layer that emits the
    originating finding. Consumes OCSF **Compliance Finding** (class
    2003) as the primary shape; when the originating signal is an
    upstream Sigma match against cloud audit logs the operator's
    posture-management layer normalises the OCSF **Detection
    Finding** (class 2004) shape into a Compliance Finding before
    this step sees it. Feeds `kpi.mttd_cloud_misconfig@v1`.

**enrich resource and owner** (`…000000003`)
:   Enrichment step. Resolves the affected resource against the
    operator's cloud-inventory and ownership graph (tenant, account,
    region, resource type, tags, accountable owner, data
    classification) and annotates the case with the routing context
    the notification and escalation steps read against. Anchored on
    MITRE D3FEND v1.0.0 `D3-AI` (Asset Inventory) — the Harden-tactic
    asset-inventory discipline the rest of the playbook depends on
    for routing and severity resolution. Anchored on OSCAL CM-8
    (System Component Inventory) — the system-component-inventory
    discipline is the operator's evidence trail that resource
    resolution is trustworthy. The downstream owner-notification
    routing depends on this enrichment being trustworthy; a missing
    or stale owner reference falls back to the operator's declared
    default ownership pool.

**known false positive?** (`…000000004`, `if-condition`)
:   Deterministic branch on `__is_known_false_positive__`. The gate
    reads the operator's suppression / exception ledger for a
    live-and-in-scope exception matching the finding's rule
    fingerprint against the affected resource; a match short-circuits
    to the suppression close, a miss routes into the notification
    leg. The false-positive branch is a distinct action step (rather
    than a straight-to-end shortcut) so the suppression close is
    audit-evident on the CACAO trail. Anchored on OSCAL IR-4
    (Incident Handling) for the triage-decision leg.

**suppress and close** (`…000000005`)
:   Suppression step. Records the suppression against the operator's
    exception ledger (rule fingerprint, resource id, exception owner,
    expiry) and closes the case without a remediation attempt. The
    step is deliberately narrow — it does not extend or expand the
    exception, only stamps the closure against the pre-existing
    ledger entry so an already-triaged benign deviation stops
    re-paging owners. Emits OCSF **Compliance Finding** (class 2003)
    keyed to the case so timeline-signal controls audit the
    suppression closure alongside the standard remediation trail.

**notify owner** (`…000000006`)
:   Notification step. Hand-off along the operator's pre-bound
    channel per `__severity__` (ticketing / chat / paging) carrying
    the finding, the affected resource, the violated baseline, and a
    pointer to the guided-remediation runbook the next step
    references. Anchored on MITRE D3FEND v1.0.0 `D3-IRA` (Incident
    Response Analysis) — the incident-response-analysis discipline
    that pages the accountable owner with the routed evidence.
    Anchored on OSCAL IR-4 (Incident Handling). Emits OCSF
    **Compliance Finding** (class 2003) per notification so the
    timeline-signal controls can audit on-time notification cadence.

**guided remediation** (`…000000007`)
:   Remediation step. Applies the remediation bound to the violated
    baseline rule via an attested change — an IaC pull request
    against the operator's declarative-infrastructure repository or
    a runbook execution the operator's platform automates. Anchored
    on MITRE D3FEND v1.0.0 `D3-SCP` (System Configuration
    Permissions) — the Harden-tactic system-configuration-permissions
    control the remediation lands through. Anchored on OSCAL CM-6
    (Configuration Settings) for the baseline-conformance leg, plus
    per-branch anchors: AC-3 (Access Enforcement) and AC-6 (Least
    Privilege) on the over-permissive-identity branch (public
    storage exposure, world-readable object stores, over-broad IAM
    policies, wildcard actions bound to workload identities); SC-7
    (Boundary Protection) on the over-permissive-baseline network
    branch (0.0.0.0/0 on sensitive ports, missing private-endpoint
    enforcement); SC-28 (Protection of Information at Rest) on the
    missing-encryption branch (unencrypted storage volume, bucket
    without server-side encryption, key-vault with deletion-protection
    disabled). The attested-change discipline is the audit property
    the CRA Annex I §1(b) secure-by-default anchor discharges here.

**re-scan** (`…000000008`)
:   Verification step. Targeted re-evaluation of the same baseline
    rule against the affected resource. Writes
    `__remediation_verified__` for the next gate. Anchored on MITRE
    D3FEND v1.0.0 `D3-RAPA` (Resource Access Pattern Analysis) — the
    same Detect-tactic technique the ingest step consumes, applied
    here as a targeted re-evaluation rather than a continuous walk.
    Anchored on OSCAL CM-2 (Baseline Configuration) and SI-4 (System
    Monitoring). Emits OCSF **Compliance Finding** (class 2003)
    carrying the verified-or-refuted verdict. Stamps
    `kpi.mttr_cloud_misconfig@v1` on the verified branch.

**remediation verified?** (`…000000009`, `if-condition`)
:   Deterministic branch on `__remediation_verified__`. `on_success`
    (verified) routes directly to the terminal end; `on_failure`
    (still deviant) routes into escalation. Anchored on OSCAL IR-4
    (Incident Handling) for the case-closure leg.

**escalate** (`…00000000b`)
:   Escalation step. Composes the escalation payload (finding,
    attempted remediation, failing re-scan evidence) and hands off
    along the operator's pre-bound paging channel — the security-
    engineering on-call so the case is not closed on an unverified
    remediation. Anchored on MITRE D3FEND v1.0.0 `D3-IRA` (Incident
    Response Analysis) and OSCAL IR-4 (Incident Handling) plus IR-5
    (Incident Monitoring) — the incident-monitoring discipline is
    the audit property this step discharges by ensuring chronic
    unremediated deviations surface in the metrics layer rather than
    quietly closing on the case. Emits OCSF **Compliance Finding**
    (class 2003) keyed to the case and stamps
    `kri.recurring_cloud_misconfig@v1` so chronic deviation surfaces
    in the metrics layer.

The six action steps are operator-bound runtime seams: the framework
ships neither the CSPM layer, the ownership graph, the suppression
ledger, the notification-channel binding, the IaC pull-request
surface, nor the runbook registry. The playbook is the portable
description of *what* the operator's stack should do per case;
binding those seams to real endpoints is the operator's job.

> **LM determinism.** Ingest, enrichment, suppression, notification,
> guided remediation, re-scan, and escalation are structured reads
> and writes against operator-owned surfaces, not free-text
> reasoning steps. The playbook binds no DSPy signature — there is
> no LM-driven step at this layer. See
> [`docs/FOUNDATION.md`](../FOUNDATION.md) § LLM determinism. If an
> operator wires an LM-driven remediation-suggestion aide on top of
> the guided-remediation step (a private, forward-looking extension
> that composes a candidate IaC diff for review), the framework-wide
> EU-resident LM endpoint guard re-applies the check at process
> startup (`compilers/_shared/lm_endpoint_guard.py`), with the
> `SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
> [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).

## 4. Regulatory anchors

**NIS2 Article 21(2)(e)** — security in network and information
systems acquisition, development and maintenance. The clause requires
essential and important entities to secure their information systems
across acquisition, development, and maintenance, which covers the
continuous-baseline-conformance discipline for deployed cloud
resources. The cloud_misconfiguration playbook is the **operational
discharge of the baseline-deviation, IaC guardrail, and remediation
surface** this obligation demands: continuous evaluation of
cloud-baseline rules via the CSPM layer, attested remediation through
an IaC pull request or runbook execution, and re-scan-driven
verification so a deviation cannot quietly persist. Inbound anchor at
[`content/mappings/nis2/article-21-2-e.yaml`](../../content/mappings/nis2/article-21-2-e.yaml)
(`nis2:art-21-2-e`) backlinks `playbook.cloud_misconfiguration@v1`.

**NIS2 Article 21(2)(i)** — HR security, access control and asset
management. The clause requires operators to run access-control and
asset-management processes with joiner-mover-leaver evidence and
least-privilege enforcement. The cloud_misconfiguration playbook
discharges the **asset-management and least-privilege surface for
cloud resources**: the enrichment step resolves the affected resource
against the cloud inventory and ownership graph (asset management),
and the guided-remediation step reduces over-permissive identity
bindings to the documented minimum on the over-permissive-identity
branch (least privilege). Inbound anchor at
[`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml)
(`nis2:art-21-2-i`).

**DORA Article 9(4)(a)** — protection and prevention, operationalised
by the JC RTS on the ICT risk management framework (Commission
Delegated Regulation (EU) 2024/1774) Article 10. The clause requires
documented vulnerability and patch management procedures covering
identification, risk-based prioritisation, and tracking of
remediation to closure. The cloud_misconfiguration playbook
discharges the **cloud-baseline-deviation slice** of that obligation:
ingest a posture finding, enrich it with ownership, drive guided
remediation, re-scan to verify closure, and escalate when remediation
does not stick so the recurring-misconfig KRI catches chronic
exceptions. Inbound anchor at
[`content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml`](../../content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml)
(`dora:art-9-vuln-mgmt`).

**CRA Annex I §1(b)** — secure-by-default configuration. The clause
requires products with digital elements to be delivered with a
secure-by-default configuration. The cloud_misconfiguration playbook
is the **operational trail that keeps deployed cloud resources
against the secure-by-default posture after a deviation is observed**:
a posture finding is by construction a deviation from a documented
secure baseline, and the attested remediation restores conformance.
Inbound anchor at
[`content/mappings/cra/annex-i-1-essential-cybersecurity.yaml`](../../content/mappings/cra/annex-i-1-essential-cybersecurity.yaml)
(`cra:annex-i-1-secure-by-default`).

**CRA Annex I §1(j)** — minimal attack surface. The clause requires
manufacturers to design products with a minimal attack surface. The
cloud_misconfiguration playbook is the **operational trail that keeps
deployed cloud resources against the minimal-attack-surface envelope
after a deviation is observed**: the over-permissive-baseline branch
(public storage exposure, world-readable object stores, 0.0.0.0/0 on
sensitive ports) is the class of finding this control is scoped to,
and the attested remediation tightens the exposed surface back to the
declared envelope. Inbound anchor at
[`content/mappings/cra/annex-i-1-essential-cybersecurity.yaml`](../../content/mappings/cra/annex-i-1-essential-cybersecurity.yaml)
(`cra:annex-i-1-attack-surface`). No outbound CRA Art. 14
incident-reporting closure is asserted here — a posture finding only
becomes Art. 14 reportable when it rises to incident-grade and is
dispatched via `playbook.incident_management@v1`.

**GDPR Article 30 Record of Processing Activity.** The per-workflow
RoPA at
[`content/mappings/gdpr/data-flow-cloud_misconfiguration.md`](../../content/mappings/gdpr/data-flow-cloud_misconfiguration.md)
covers the resource-ownership enrichment and owner-notification
processing this playbook operates on. Lawful basis is GDPR Art.
6(1)(f) legitimate interests, with Art. 6(1)(c) legal obligation as
the secondary basis where NIS2 Art. 21(2)(e) / (2)(i) transposition
applies. Where the misconfiguration itself concerns a resource that
holds personal data (an unencrypted bucket, a publicly exposed
database), GDPR Art. 32 (security of processing — appropriate
technical and organisational measures) is the substantive anchor;
the playbook's re-scan-verified remediation is the operational trail
that appropriate measures were restored. The framework treats owner
identifiers as operator-scoped opaque references under the operator's
own naming convention and does not re-derive subject identifiers
outside the operator's own directory surface.

**OSCAL controls** exercised by the workflow (from
[`content/playbooks/cloud_misconfiguration/mappings.yaml`](../../content/playbooks/cloud_misconfiguration/mappings.yaml)):
CM-2 (Baseline Configuration — anchors the ingest and re-scan
steps), CM-6 (Configuration Settings — anchors the guided-remediation
step), CM-8 (System Component Inventory — anchors the enrichment
step), AC-3 (Access Enforcement — anchors the guided-remediation
step for the over-permissive-identity branch), AC-6 (Least Privilege
— anchors the guided-remediation step for the privilege-escalation-
pattern sub-branch), SC-7 (Boundary Protection — anchors the
guided-remediation step for the over-permissive-baseline network
branch), SC-28 (Protection of Information at Rest — anchors the
guided-remediation step for the missing-encryption branch), SI-4
(System Monitoring — anchors the ingest step's input surface and the
re-scan step's verification surface), IR-4 (Incident Handling —
anchors the notify-owner, gate, and escalate steps), IR-5 (Incident
Monitoring — anchors the per-case KPI / KRI accounting).

**MITRE D3FEND v1.0.0** — `D3-RAPA` (Resource Access Pattern
Analysis) at `ingest finding` and at `re-scan`; `D3-AI` (Asset
Inventory) at `enrich resource and owner`; `D3-IRA` (Incident
Response Analysis) at `notify owner` and at `escalate`; `D3-SCP`
(System Configuration Permissions) at `guided remediation`. The
Detect-tactic (`D3-RAPA`), Harden-tactic (`D3-AI`, `D3-SCP`), and
incident-response (`D3-IRA`) techniques together describe the
detect-through-harden discipline the playbook discharges.

**OCSF v1.3.0** — `Compliance Finding` (class_uid 2003, category
Findings), direction `consumes`. Consumed at the ingest step as the
originating CSPM / posture finding (rule fingerprint, affected
resource, evaluated baseline, first-observed timestamp).
`Detection Finding` (class_uid 2004, category Findings), direction
`consumes`. Consumed at the ingest step alongside the Compliance
Finding when the originating signal is an upstream Sigma match
against cloud audit logs (`cspm_finding_critical`,
`public_storage_bucket` referenced on the CACAO
`x_secops_ng.detection_refs`); the operator's posture-management
layer normalises both shapes into the Compliance Finding the rest of
the playbook branches on. `Compliance Finding` (class_uid 2003),
direction `emits`. Emitted by the suppression, notification,
re-scan, and escalation steps: each milestone (suppression record,
owner-notification stamp, re-scan verdict, escalation submission) is
recorded as a Compliance Finding keyed to the originating case so
the MTTD / MTTR / cloud-posture-coverage KPIs and the recurring-
misconfig KRI can audit on-time progression and chronic deviation.

The CACAO playbook's external references additionally cite the OCSF
**Cloud Resources Inventory Info** class (class_uid 5023 under OCSF
v1.4.0) as the upstream class feeding the resource-and-owner
enrichment step. A telemetry binding for that class is omitted from
the overlay today because sibling overlays standardise on OCSF
v1.3.0, and 5023 is documented in 1.4.0; once a
`telemetry.ocsf.cloud_resource_inventory@v1` file lands under
`content/telemetry/` and the operator's OCSF baseline lifts to
1.4.0, a CORE follow-up card can pin it without a schema change.

## 5. Per-target hand-off

### 5.1 n8n — operator-edited Set rows over the cloud-misconfig topology

`examples/n8n/cloud_misconfiguration/workflow.json` carries the CACAO
topology as eleven n8n nodes (`manualTrigger`, six `set` nodes, two
`if`, one `noOp` terminal), with node ids preserving the CACAO step
ids verbatim. The six action steps emit `n8n-nodes-base.set` nodes
carrying the CACAO I/O contract as editable assignment rows plus the
`x_secops_ng` reference bundles (detection, control, telemetry,
metric). The two `if-condition` nodes (`known false positive?`,
`remediation verified?`) emit `n8n-nodes-base.if` nodes with
placeholder conditions the operator wires to the upstream
`out.is_known_false_positive` and `out.remediation_verified` fields.
The lossy translations are recorded in `meta.secops_ng_notes` so the
integrator sees exactly which seams need attention.

Operators bind the Set rows to their connectors:

- `ingest finding` → the operator's CSPM / posture-management layer's
  finding-fetch or webhook surface; writes the normalised case
  shape.
- `enrich resource and owner` → the operator's cloud-inventory and
  ownership-graph read APIs; writes ownership context onto the case.
- `suppress and close` → the operator's suppression / exception
  ledger (SCIM-driven store, ticketing-system tag, or purpose-built
  exception service).
- `notify owner` → the operator's pre-bound notification channel per
  `__severity__` (ticketing / chat / paging).
- `guided remediation` → the operator's IaC pull-request surface
  (GitLab / GitHub / a hosted Git provider) or the runbook-execution
  surface for the automated branches (a hosted automation service, a
  self-hosted runner).
- `re-scan` → the operator's CSPM layer's targeted-rescan API
  against the affected resource.
- `escalate` → the operator's paging surface for the security-
  engineering on-call.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/cloud_misconfiguration/regenerate.sh
```

To import into an n8n instance: open the workflows list, choose
**Import from File**, and select
`examples/n8n/cloud_misconfiguration/workflow.json`. The workflow is
inactive by default — review and bind the Set rows to your own
connectors before activating. The emitted workflow is a *snapshot of
intent*, not a runnable playbook.

### 5.2 Temporal — `@activity.defn` bodies

`examples/temporal/cloud_misconfiguration/workflow.temporal.py` is a
standard Temporal worker module: one `@workflow.defn` class and one
`@activity.defn` function per CACAO action, with the six action
activities documenting their operator-bound seam (ingest, enrichment,
suppression, notification, guided remediation, re-scan, escalation).
Per-activity retry policies are emitted alongside the activities so
the operator can pin them on the `workflow.execute_activity` call
sites; the workflow lowering itself is the standard target-neutral
lowering the compiler emits.

Temporal is a natural fit for the cloud-misconfiguration discipline:
each finding becomes one workflow run; the two conditional branches
become Temporal conditionals; retries against transient failures on
the CSPM layer / ownership graph / IaC surface / paging channel get
first-class Temporal semantics (activity retry policy per seam);
replay against the same Temporal event history re-derives the same
suppression / remediation / re-scan record when the activity bodies
are wired against the same operator seams.

The sibling `_audit_mirror.py` carries the `AuditRecord` /
`AuditTrail` types — no `compilers.*` import in the emitted artifact,
so the worker module is a self-contained drop-in.

### 5.3 LangGraph — `@tool` wrappers + agentic-extension hook

`examples/langgraph/cloud_misconfiguration/state_bindings.py` carries
the `TypedDict` state and the six `@tool`-decorated action wrappers.
`graph_spec.json` carries the target-neutral topology (nodes,
conditional edges on `__is_known_false_positive__` and
`__remediation_verified__`, linear edges through the remediation
chain to the terminal end, and the direct edge from the suppression
branch to the same end); `assemble.py` is the hand-written
reference assembly that wires the GraphSpec + bindings into a
`langgraph.graph.StateGraph`.

LangGraph is the agentic target — an operator who wants to layer an
LM-driven remediation-suggestion aide on top of the guided-remediation
step (reading the enriched finding and emitting a candidate IaC diff
or a runbook selection for reviewer approval) fills that as a
private extension. The framework-wide EU-resident LM endpoint guard
re-applies the check at process startup
(`compilers/_shared/lm_endpoint_guard.py`), with the
`SECOPS_NG_LM_ENDPOINT_NON_EU_ACK` opt-out documented in
[`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md).
The compiler never embeds an LLM SDK.

### 5.4 Cross-target parity

All three reference targets are present in the tree today with
committed emitter output — `examples/n8n/cloud_misconfiguration/`,
`examples/temporal/cloud_misconfiguration/`, and
`examples/langgraph/cloud_misconfiguration/`. Cross-target byte-
parity goldens under `tests/examples/cloud_misconfiguration/` pin the
committed worked-example artifacts against fresh emitter runs from
the canonical CACAO source; if the compiler changes, regenerate the
worked examples via the per-target `regenerate.sh` and commit the
diff intentionally.

## 6. Observability — OTel + AuditTrail in every target

Every emitted action opens an OpenTelemetry span and appends an
`AuditRecord` to a context-local `AuditTrail` *before* the operator-
bound seam call. The mirror runs unconditionally, ahead of any OTLP
exporter, so the audit property holds even when the operator has not
configured a collector — typical for disconnected, sovereign, or
air-gapped deployments.

Span attributes use the shared `secops_ng.*` keyspace and are stable
across the three targets:

| Attribute key                | Carries                                              |
|------------------------------|------------------------------------------------------|
| `secops_ng.playbook.id`      | CACAO playbook id (`playbook--…`).                   |
| `secops_ng.playbook.version` | Content version pinned in the playbook.              |
| `secops_ng.step.id`          | CACAO step id (`action--…`).                         |
| `secops_ng.step.name`        | Human-readable step label.                           |
| `secops_ng.step.type`        | CACAO step type (`action`, `start`, `end`, `if-condition`). |
| `secops_ng.tool.name`        | Emitted tool / activity / Code-node function name.   |
| `secops_ng.compile.target`   | `n8n` / `temporal` / `langgraph` discriminator.      |

Span boundaries per target:

- **n8n** — the compiled workflow is a snapshot of intent; OTel
  instrumentation is a per-node operator concern documented per
  node-id, not a runtime guarantee of the emitted JSON.
- **Temporal** — workflow span (`workflow.<stable_id>`) at workflow
  entry; activity span (`activity.<step_id>`) on every activity body,
  with retries opening a fresh child span per Temporal attempt.
- **LangGraph** — node span (`node.<step_id>`) wrapping every node
  assembled from `graph_spec.json`; tool span (`tool.<step_id>`)
  inside the `@tool` wrapper.

The OTLP exporter endpoint is operator-supplied
(`OTEL_EXPORTER_OTLP_ENDPOINT`). The compiler never sets a default
and never imports a vendor SDK; pointing the exporter at a managed
APM is a downstream choice the operator owns end-to-end. The
sovereignty posture asks for an EU-resident collector — see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
for the JSONL replay envelope and the snapshot API used to drain a
trail offline.

## 7. Metrics — what the cloud-misconfiguration response exposes

Four indicator catalogue entries surface the cloud_misconfiguration
posture to the operator's metrics dashboard. The catalogue entries
live under `content/metrics/`.

- **`kpi.mttd_cloud_misconfig@v1`** — time from earliest telemetry
  evidence to the first authoritative Compliance Finding firing on
  the cloud-misconfiguration case. Rising values indicate the CSPM
  layer is drifting behind the operational objective.
- **`kpi.mttr_cloud_misconfig@v1`** — median time from ingest to
  re-scan-verified remediation. Stamped by the re-scan step on the
  verified branch; audits on-time closure of the remediation chain.
- **`kpi.cloud_posture_coverage@v1`** — share of the in-scope cloud
  resource inventory covered by an active CSPM baseline rule per
  operator policy version. Coverage below the operator-configured
  floor indicates the CSPM layer is running against an incomplete
  surface and the ingest step may be under-observing deviation.
- **`kri.recurring_cloud_misconfig@v1`** — count of resource /
  rule-fingerprint pairs that trip the same finding across
  consecutive re-scan windows. Stamped by the escalate step; a
  non-zero value indicates the guided-remediation surface is
  addressing symptoms rather than root causes on the flagged
  resource.

The catalogue entries pin the field-level read contract; the
framework does not ship a hosted dashboard. Operators dashboard the
KPI / KRI series against their own metrics backend.

## 8. Detection references — the upstream signal shapes

The playbook cites the upstream **CSPM / Sigma signal shapes** on
its `external_references`:

- **CSPM finding — critical severity.** Attaches at the ingest step
  as the primary shape the workflow branches on. The rule
  fingerprint is provider-native and pinned by the operator's CSPM
  layer.
- **Public storage bucket exposure.** Attaches at the ingest step
  for the public-storage-exposure sub-branch (world-readable object
  store, missing bucket-policy deny). MITRE ATT&CK T1580 (Cloud
  Infrastructure Discovery) is the case-shape taxonomy the enrichment
  and remediation steps read against.

See
[`content/playbooks/cloud_misconfiguration/README.md`](../../content/playbooks/cloud_misconfiguration/README.md)
for the rule-reference discipline (SecOps-NG does not re-author
Sigma or CSPM rules; upstream rule ids are pinned by the CORE-layer
detection mapping).

## 9. Operator customisation points

The playbook is a cloud-misconfiguration-remediation machine; the
*policy* it exercises is the operator's. The customisation seams:

- **CSPM provider binding.** The `ingest finding` step reads the
  operator's CSPM / posture-management layer — a hosted provider, a
  self-hosted open-source CSPM, or an in-house rules pipeline. The
  framework binds the finding shape (Compliance Finding), not the
  vendor; operators wire the step to whichever CSPM their
  environment runs on.
- **Ownership-graph source.** The `enrich resource and owner` step
  reads the operator's cloud-inventory and ownership-graph
  surface — a tag-based ownership scheme, a CMDB, a self-service
  ownership catalogue, or an internal directory join. The
  framework does not prescribe the source; a stale or missing owner
  reference falls back to the operator's declared default ownership
  pool.
- **Suppression-list management.** The `known false positive?` gate
  reads the operator's suppression / exception ledger — a ticketing-
  system tag, a purpose-built exception service, or a SCIM-driven
  store. Exception lifecycle (creation, expiry, review cadence) is
  the operator's discipline; the playbook only reads a live-and-in-
  scope match, it does not extend or create exceptions.
- **Notification channel per severity.** The `notify owner` step
  reads the operator's `__severity__`-conditioned channel binding —
  chat for low, ticketing for medium, paging for high / critical, or
  whatever the operator's routing policy dictates. The framework
  documents the seam but does not prescribe the mapping.
- **IaC pull-request surface / runbook registry.** The `guided
  remediation` step branches on the remediation binding on the
  violated baseline rule — an IaC pull request against the operator's
  declarative-infrastructure repository or a runbook execution
  through the operator's platform. The remediation binding itself
  (which rule remediates through IaC vs. runbook) is operator-owned
  and lives on the operator's rule-registry side.
- **Significance threshold for incident escalation.** A posture
  finding that lifts to incident-grade — impact on essential
  services, personal-data exposure confirmed, active exploitation
  observed — is routed off this playbook onto
  `playbook.incident_management@v1`. The numeric cut-offs and the
  qualitative predicates for the lift are the operator's; the
  framework binds the seam, not the threshold.
- **Recurring-misconfig KRI threshold.** The
  `kri.recurring_cloud_misconfig@v1` catalogue entry pins the
  field-level shape but not the numeric alerting threshold — the
  operator dashboards the series and sets the alert cut-off in their
  own metrics backend.

## 10. Replay and audit story

The byte-parity drift guards under
`tests/examples/cloud_misconfiguration/` pin the committed worked-
example artifacts against fresh emitter runs from the canonical
CACAO source; if the compiler or the playbook changes, regenerate
via the per-target `regenerate.sh` and commit the diff
intentionally.

The cross-target replay property is the harder one: the same
finding, fed through n8n / Temporal / LangGraph, produces byte-
identical suppression / notification / remediation / re-scan records
when each target's activity or tool bodies are wired against the same
operator seams and the same OSCAL / OCSF / D3FEND reference bundles.
The `(finding_id, resource_id, is_known_false_positive,
suppression_stamped_at, notification_stamped_at,
remediation_applied_at, remediation_verified, rescan_verdict)` key is
the string a regulator can diff to confirm the property holds across
targets. Where personal data lives on the affected resource
configuration itself, the framework treats owner and account
identifiers as operator-scoped opaque references and does not
re-derive subject identifiers outside the operator's own directory
surface.

## 11. Relationship to other playbooks

The cloud_misconfiguration playbook sits at a specific point in the
posture-and-response lane set:

- **Alongside `infra_posture_management`.** infra_posture_management
  is the scheduled continuous-audit lane — it walks the operator's
  in-scope manifest on a cadence, evaluates each declared control
  against the resulting posture-state snapshot, and emits a
  posture-evidence artifact series the auditor bundle folds into a
  handover. cloud_misconfiguration is the per-finding response lane —
  it reacts to a single deviation the CSPM layer has surfaced and
  drives it to a re-scan-verified fix. Both lanes share the CSPM
  baseline surface and the Compliance Finding telemetry shape; they
  differ in trigger (schedule vs. finding) and in output (evidence
  artifact series vs. per-case remediation trail). See
  [`docs/cookbook/infra_posture_management.md`](./infra_posture_management.md).
- **Feeds `incident_management` when the case lifts to
  incident-grade.** cloud_misconfiguration is content-model
  independent of the regulator-notification chain — a posture finding
  that escalates on the recurring-misconfig KRI stays inside the
  CSPM remediation surface and does not auto-route into
  `playbook.incident_management@v1` under NIS2 Art. 23 / DORA Art.
  19 / GDPR Art. 33. When the operator's classification does lift the
  case to incident-grade (impact on essential services confirmed,
  personal-data exposure verified, active exploitation observed), the
  case envelope is handed off to
  `playbook.incident_management@v1` the same way the detection-chain
  playbooks do. See
  [`docs/cookbook/incident_management.md`](./incident_management.md).
- **Distinct from `patch_management` and `vuln_intake`.**
  patch_management drives OS- and package-level patch cadence;
  vuln_intake drives CRA Art. 14 product-side vulnerability
  notification and CVE-scoped remediation. cloud_misconfiguration is
  the *configuration-deviation* lane — a resource's declarative
  configuration has drifted from a documented baseline, not a package
  version behind on a CVE.

## 12. What this cookbook does not cover

- **Credentials.** No API keys, no tokens, no private keys for the
  CSPM layer, the ownership graph, the suppression ledger, the
  notification channel, the IaC pull-request surface, the runbook
  registry, the re-scan API, or the escalation paging channel.
  Connectors are operator-bound at runtime against environment
  variables documented per target; the framework ships no default
  endpoint per the sovereign-stack posture.
- **Deployment topology.** Worker concurrency, retry policies beyond
  the per-activity defaults, persistence backends, n8n hosting, the
  scheduler driving any operator-side re-scan cadence, LangGraph
  host process model — those are runtime concerns the operator
  applies in their own assembly.
- **CSPM rule authoring.** This playbook consumes a Compliance
  Finding the operator's CSPM layer has already emitted against a
  documented baseline rule; authoring the baseline rules, tuning
  their severity, and pinning their fingerprints are upstream
  disciplines the framework does not carry. The playbook binds the
  finding shape and the remediation-verification loop, not the
  rule catalogue.
- **Incident-grade escalation and regulator notification.** A
  posture finding only becomes NIS2 Art. 23 / DORA Art. 19 / GDPR
  Art. 33 reportable when the operator's classification lifts the
  case to incident-grade. The regulator-notification chain runs on
  `playbook.incident_management@v1`; this playbook produces the
  remediation-history evidence a downstream lift would feed on, not
  the submission envelope.
- **Personal data in resource configurations.** Operator-side
  configurations may carry resource ids, account labels, owner tags,
  and tenancy markers; per AGENTS.md §3 they MUST stay role-shaped
  or opaque. Personal localparts, credential-shaped strings, and raw
  cloud-account secret material are out of scope and rejected at the
  schema boundary.
- **Per-deployment YAML.** This playbook ships no separate
  operator-facing `config.yaml`; per-case inputs are the CACAO
  `playbook_variables` block bound at compile time via the standard
  `__double_underscore__` substitution.

## 13. References

- [`content/playbooks/cloud_misconfiguration/README.md`](../../content/playbooks/cloud_misconfiguration/README.md)
  — canonical CACAO source overview and status.
- [`content/playbooks/cloud_misconfiguration/mappings.yaml`](../../content/playbooks/cloud_misconfiguration/mappings.yaml)
  — outbound OSCAL / D3FEND / OCSF / NIS2 / DORA / CRA overlay with
  per-step control anchors.
- [`content/mappings/nis2/article-21-2-e.yaml`](../../content/mappings/nis2/article-21-2-e.yaml)
  — NIS2 Article 21(2)(e) inbound anchor (security in acquisition,
  development, and maintenance).
- [`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml)
  — NIS2 Article 21(2)(i) inbound anchor (HR security, access
  control, asset management).
- [`content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml`](../../content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml)
  — DORA Article 9(4)(a) inbound anchor operationalised by the JC
  RTS on the ICT risk management framework (Commission Delegated
  Regulation (EU) 2024/1774, Art. 10).
- [`content/mappings/cra/annex-i-1-essential-cybersecurity.yaml`](../../content/mappings/cra/annex-i-1-essential-cybersecurity.yaml)
  — CRA Annex I §1(b) secure-by-default and §1(j) minimal-attack-
  surface inbound anchors.
- [`content/mappings/gdpr/data-flow-cloud_misconfiguration.md`](../../content/mappings/gdpr/data-flow-cloud_misconfiguration.md)
  — GDPR Article 30 Record of Processing Activity.
- [`examples/n8n/cloud_misconfiguration/README.md`](../../examples/n8n/cloud_misconfiguration/README.md)
  — n8n worked-example walkthrough and import instructions.
- [`examples/temporal/cloud_misconfiguration/README.md`](../../examples/temporal/cloud_misconfiguration/README.md)
  — Temporal worked-example walkthrough.
- [`examples/langgraph/cloud_misconfiguration/README.md`](../../examples/langgraph/cloud_misconfiguration/README.md)
  — LangGraph worked-example walkthrough.
- [`docs/cookbook/infra_posture_management.md`](./infra_posture_management.md)
  — companion cookbook (scheduled posture-evidence lane).
- [`docs/cookbook/incident_management.md`](./incident_management.md)
  — downstream cookbook (regulator-submission engine when a case
  lifts to incident-grade).
- [`docs/observability/audit-mirror.md`](../observability/audit-mirror.md)
  — `AuditTrail` / `AuditRecord` envelope and offline replay shape.
- [`docs/sovereignty/eu-resident-lm-guard.md`](../sovereignty/eu-resident-lm-guard.md)
  — EU-resident LM endpoint check and the documented opt-out.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — four-layer runtime.
