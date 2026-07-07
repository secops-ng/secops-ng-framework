# business_continuity — NIS2 Art. 21(2)(c) plan-lifecycle

SKELETON tier of the F-NIS2-BCP trilogy. This playbook is the
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

- `playbook.cacao.yaml` — CACAO v2 workflow scaffold (7 steps:
  detect / activate / isolate / switch-to-backup / notify /
  restore-and-verify / PIR). SKELETON: adapter bindings are TODO
  markers a sibling CORE card lands.
- `mappings.yaml` — outbound view of the content model: OSCAL
  (CP-2 / CP-10 / IR-6), D3FEND (D3-SRA on the recovery step),
  OCSF (Availability Activity 4004, Incident Finding 2005),
  and the inbound regulatory anchors (nis2:art-21-2-c,
  dora:art-11-response-recovery, gdpr:art-32-1-c-restore-availability;
  CRA deliberately excluded — the drill-lane CRA anchor is on the
  sibling `backup_recovery` overlay).

## Compile targets

Stub modules for the three reference compile targets are present at
`compilers/{n8n,temporal,langgraph}/business_continuity/`. SKELETON:
dispatchers and adapter Protocols land at CORE.

## Trilogy

- **SKELETON (this card):** scaffold + mappings + compile stubs.
- **CORE:** full workflow logic — adapter Protocols under
  `patterns.business_continuity`, the three-target dispatch wrappers,
  the significance-threshold evaluator, and the Art. 23 envelope
  templates.
- **EXTEND:** cookbook walkthrough + advanced features (per-Member-
  State NCA delivery surface, cutback misconfiguration detection
  bindings).
