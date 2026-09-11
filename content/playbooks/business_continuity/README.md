# business_continuity — NIS2 Art. 21(2)(c) plan-lifecycle

Plan-lifecycle playbook of the F-NIS2-BCP trilogy — `stable` under
the Maturity ladder (`content_version` 1.0.0). This playbook is the
operator-side plan-lifecycle materialisation of the NIS2 Art. 21(2)(c)
business-continuity obligation: detect and declare a business-
continuity event, activate the documented BCM plan artifact, isolate
affected systems where applicable, failover to the documented backup
capacity, notify the competent authority on the NIS2 Art. 23 path
where the event crosses the significant-incident threshold, restore
and verify the primary service against the documented recovery
objectives (RTO / RPO), and persist the post-incident-review record.

Sibling `backup_recovery` playbook pins the periodic non-destructive
restore-drill lane on the same clause — both overlays anchor
`nis2:art-21-2-c`, plan-lifecycle vs exercise-lifecycle.

## Files

- `playbook.cacao.yaml` — CACAO v2 workflow (7 action steps:
  detect / activate / isolate / switch-to-backup / notify /
  restore-and-verify / PIR), every step bound through
  `x_secops_ng.core_body` to a deterministic primitive under
  `primitives/`.
- `primitives/` — the seven step primitives plus the two OCSF
  milestone composers: pure, offline, LLM-free. The declaration
  anchors the Art. 23 clock on the supplied instant; a continuity
  event with no plan on file is reported as such rather than
  blocking (skips and non-engagement are data); the Art. 23
  notification and the no-notification determination are exclusive
  dispositions; recovery is verified against observed RTO / RPO,
  never asserted; a review without a lesson is not a review. The
  milestone composers (`compose_milestone_record`,
  `compose_incident_finding_record`) are the telemetry-seam
  contract for the per-milestone records the mappings declare as
  emitted, keyed to the event id — they are called at the seam, not
  bound as step bodies.
- `mappings.yaml` — outbound view of the content model: OSCAL
  (CP-2 / CP-10 / IR-6), D3FEND (D3-SRA on the recovery step),
  OCSF (API Activity 6003 at the five operational milestones,
  Incident Finding 2005 at notification and review — the house
  binding for workflow-emitted milestones per #877),
  and the inbound regulatory anchors (nis2:art-21-2-c,
  dora:art-11-response-recovery, gdpr:art-32-1-c-restore-availability;
  CRA deliberately excluded — the drill-lane CRA anchor is on the
  sibling `backup_recovery` overlay).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
emitted artifacts live under
`examples/{n8n,temporal,langgraph}/business_continuity/` with
byte-parity goldens under `tests/examples/`, regenerated from the
bound canonical YAML via each directory's `regenerate.sh` (which
mirrors the YAML into a byte-deterministic JSON form first). n8n
emits seven Code nodes; the Temporal activities and LangGraph tools
import their primitives, with `NotImplementedError` marking only the
operator-integration seams (the declaring surface, the plan store,
the isolation and failover surfaces, competent-authority delivery,
the health-signal probe, the evidence store).

## Trilogy

- **SKELETON:** scaffold + mappings (#707).
- **CORE:** the seven deterministic primitives and the milestone
  composers (CORE-PRIM), bound to the action steps with the three
  worked examples regenerated and the playbook graduated to `stable`
  (CORE-WIRE). The adapter-bound seams — plan store, isolation and
  failover surfaces, competent-authority delivery, evidence store —
  are the operator's, as on every bound playbook.
- **EXTEND:** the cookbook walkthrough (`docs/cookbook/business_continuity.md`).
  Per-Member-State competent-authority delivery adapters and cutback
  misconfiguration detection bindings remain operator-side and are
  recorded as not covered in the cookbook, not as framework debt.
