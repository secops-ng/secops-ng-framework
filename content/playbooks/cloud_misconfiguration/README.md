# cloud_misconfiguration

CACAO v2 starter playbook for responding to a cloud-posture (CSPM)
finding: ingest → enrich resource and owner → notify owner → guided
remediation → re-scan, with escalation if the re-scan fails.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact (`playbook.cloud_misconfiguration@v1`).
- `primitives/` — one deterministic primitive per action step (see Status).

## Worked example

The cross-layer worked example — controls, telemetry, metrics, and
regulatory cross-references that bind to this playbook — lives at
`../../../content-model/examples/cloud_misconfiguration/`. Start with
the README there for the cross-reference graph and per-artifact stable
IDs:

- `control.cspm_baseline@v1`, `control.iac_policy_guardrail@v1`,
  `control.cloud_identity_least_privilege@v1`
- `telemetry.ocsf.compliance_finding@v1`,
  `telemetry.ocsf.cloud_resources_inventory_info@v1`
- `kpi.mttd_cloud_misconfig@v1`, `kpi.mttr_cloud_misconfig@v1`,
  `kpi.cloud_posture_coverage@v1`, `kri.recurring_cloud_misconfig@v1`

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
shared CACAO fixture lives at
`tests/compilers/_shared/fixtures/cloud_misconfiguration.cacao.json`.
Emitted artifacts and golden tests landed across the three CORE cards:

- n8n: `tests/compilers/n8n/test_cloud_misconfiguration.py`
- Temporal: `tests/compilers/temporal/test_cloud_misconfiguration.py` (PR #73)
- LangGraph: `examples/langgraph/cloud_misconfiguration/` plus
  `tests/compilers/langgraph/test_cloud_misconfiguration.py` (PR #85)

This directory ships the portable content only.

## Status

`maturity: stable`, `content_version` 1.0.0. All seven action steps
bind a deterministic primitive under `primitives/` through `core_body`,
each executed directly by
`tests/playbooks/cloud_misconfiguration/test_primitives.py`, and the
three reference targets emit those calls. The graduation checklist
recomputes green: tier A, 7 of 7 real bindings, zero placeholder
bodies, zero blank predicates, zero schema errors, zero predicted n8n
TODOs.

| Step | Primitive |
|---|---|
| ingest finding | `finding.normalise_posture_finding` |
| enrich resource and owner | `context.resolve_resource_context` |
| suppress and close | `suppression.compose_suppression_closure` |
| notify owner | `notification.compose_owner_notification` |
| guided remediation | `remediation.record_remediation_attempt` |
| re-scan | `verification.verify_remediation` |
| escalate | `escalation.compose_escalation` |

Decisions the primitives fix:

- **One deviation, one fingerprint.** The case fingerprint is the
  baseline rule and the resource, so the same deviation reported by a
  CSPM scan and by an IaC guardrail is the same deviation.
- **Detection latency only when it can be measured.** The MTTD KPI is
  stamped only when the adapter names the control-plane change that
  introduced the deviation; the KPI excludes the rest.
- **The owner fallback is recorded.** With no owner, or an inactive one,
  in the ownership graph, the case goes to the operator's default pool
  and every later record says so.
- **Severity moves by the operator's policy.** The upstream severity is
  shifted by the operator's per-classification table (-2 to +2 bands)
  and clamped. A resource the inventory does not know is an inventory
  gap and keeps its upstream severity; it is never lowered.
- **Only a live, exact, time-boxed entry suppresses.** The ledger entry
  must name this rule and this resource, be valid now and carry an
  expiry; a compensating control must also be attested. Matching entries
  that fail are listed with the reason. The closure is refused if the
  entry has lapsed since the gate read it, and it never extends the
  entry.
- **Recurrence as the KRI defines it.** A finding recurs when a verified
  remediation closed the same rule on the same cloud container before it
  was first observed. A suppressed closure does not count, and without
  an inventory record recurrence is unknown rather than false.
- **Every remediation is attested.** The attempt cites its change
  record; an automated hand-off (IaC change or runbook) also names the
  operator's approver. The record carries the NIST SP 800-53 anchors of
  the remediation branch.
- **Verified means a fresh pass under the same baseline.** The re-scan
  must target the same rule and resource. A result that is missing, that
  predates the change, that was taken under another baseline version, or
  that fails leaves the remediation unverified with that reason, and the
  case escalates.
- **Escalation is for unverified remediations only.** The payload
  carries the attempted change and the failing evidence for the
  security-engineering on-call.

- **The contract grows from 6 to 32 variables.** There are 19 adapter
  inputs: the finding, the inventory and ownership records, the default
  pool, the severity policy, the exception ledger, the prior closures,
  the routing table, the runbook, the remediation attempt, the re-scan
  result, the paging channel and the step instants. The ledger and the
  prior closures ride as JSON strings, because CACAO has no list type.
  There is one envelope per step. The five existing names are now
  fields extracted from those envelopes at the adapter seam, and
  `__finding_id__` stays the trigger input.
- **Both gates read real booleans.** `__known_false_positive__` comes
  from the enrichment envelope and `__remediation_verified__` from the
  re-scan envelope. Each gate compares its boolean to true, so the
  string `false`, which is truthy in most runtimes, never reaches it.

## Regulatory cross-references

The playbook is named in the regulatory mapping packs under
`content/mappings/`:

| Regime | Article  | Mapping entry                       |
|--------|----------|-------------------------------------|
| NIS2   | 21(2)(e) | `nis2:art-21-2-e`                   |
| NIS2   | 21(2)(i) | `nis2:art-21-2-i`                   |
| DORA   | 9(4)(a)  | `dora:art-9-vuln-mgmt` (companion)  |
| DORA   | 19(4)(a) | `dora:art-19-initial-4h` (escalation gate) |

## Sources

- OASIS CACAO v2.0 specification
- ENISA — Cloud Security: posture-management and misconfiguration guidance
- NIS2 Directive (EU) 2022/2555, Article 21(2)(e) and (i)
- DORA Regulation (EU) 2022/2554, Articles 9 and 19
- OCSF — Compliance Finding (2003) and Cloud Resources Inventory Info (5023)
- NIST SP 800-53 Rev. 5 — CM-2/CM-6/CM-8, AC-3/AC-6, SC-7/SC-8/SC-28
- MITRE D3FEND — System Configuration Permissions (D3-SCP),
  Resource Access Pattern Analysis (D3-RAPA)
- SigmaHQ — upstream rule IDs referenced via the playbook's
  `external_references`
