# dora_major_incident_reporting

CACAO v2 SKELETON playbook for the DORA Chapter III major-ICT-related
incident reporting lifecycle a financial entity discharges to its
competent authority per DORA Regulation (EU) 2022/2554 Article 19. The
playbook operates the three-milestone reporting cycle upstream anchored
on the Art. 18 classification decision: detect-and-classify (Art. 18
classifier gate) → notify-authority-initial (Art. 19(4)(a), 4h / 24h)
→ notify-authority-intermediate (Art. 19(4)(b), 72h) →
notify-authority-final (Art. 19(4)(c), one month after intermediate) →
close-and-archive.

## Timeline

DORA Art. 19 imposes a distinct three-milestone reporting cycle. All
clocks start from the point the incident is classified as **major**
under Art. 18 (which is itself operationalised by Commission Delegated
Regulation (EU) 2024/1772):

1. **Initial notification** — as soon as possible, within **4 hours**
   of classification as major, and no later than **24 hours** from
   awareness. ITS content shape per Commission Implementing Regulation
   (EU) 2024/2956.
2. **Intermediate report** — within **72 hours** of classification as
   major, or earlier if regular activities have recovered.
3. **Final report** — no later than **one month** after the
   intermediate report.

## Authority chain

The competent authority for DORA reporting is the operator's sectoral
supervisor — one of the three European Supervisory Authorities (EBA,
ESMA, EIOPA) via the national competent authority (NCA) chain
prescribed by the operator's sector. The operator's designated
authority chain is a compile-target configuration input, not a
hardcoded endpoint. The three ESAs receive aggregated reporting from
the NCAs; the operator files to its NCA.

## When to invoke this vs `playbook.incident_management@v1`

Both playbooks discharge regulator-notification chains against a
significant / major incident, but they target different regimes and
different authority chains:

- `playbook.dora_major_incident_reporting@v1` (this playbook) — the
  DORA-flavoured lane for financial entities in scope of DORA. Fires
  on the Art. 18 classification decision and drives the three DORA
  Art. 19 milestones (4h/24h, 72h, one month) to the ESA / NCA
  authority chain against the Commission ITS content shape.
- `playbook.incident_management@v1` — the NIS2-flavoured lane for
  essential and important entities in scope of NIS2. Fires on the
  NIS2 Art. 23 significant-incident threshold and drives the NIS2
  Art. 23 milestones (24h early warning, 72h notification, one-month
  final report) to the CSIRT / competent-authority chain.

A single operator may be in scope of **both regimes** simultaneously
(most large EU financial entities are). In that case the two
playbooks fire in parallel on the same underlying incident against
different authority chains, and the operator files separate
notifications to separate authorities. Where the incident also
involves personal data, the GDPR Art. 33 / 34 breach-notification
chain fires in parallel as a third lane, discharged by the existing
breach-notification cluster (`playbook.data_exfil@v1`,
`playbook.identity_compromise@v1`,
`playbook.ransomware_containment@v1`,
`playbook.incident_management@v1`).

## When to invoke this vs `playbook.dora_tlpt_programme@v1`

`playbook.dora_tlpt_programme@v1` is the DORA **Chapter IV**
testing-programme discipline (Art. 24 general testing requirements
+ Art. 26 threat-led penetration testing). This playbook is the
DORA **Chapter III** reporting discipline. The two are separate
Chapters covering separate obligation surfaces — one is a cadenced
testing programme, the other is an incident-driven reporting cycle.
They share no runtime touchpoint.

## Status

SKELETON. Only the CACAO v2 scaffold and the outbound overlay
(`mappings.yaml`) are populated. Per-target compile examples
(`examples/{n8n,temporal,langgraph}/dora_major_incident_reporting/`),
byte-parity goldens
(`tests/examples/{n8n,temporal,langgraph}/dora_major_incident_reporting/`),
per-milestone submission-adapter bindings, competent-authority
notification-channel bindings, and any per-cycle KPIs (missed-milestone
KRI, milestone-on-time KPI variants) are owned by CORE / EXTEND
sibling cards.

## Steps

1. **detect-and-classify** — evaluate the incident against the Art. 18
   classification criteria (Commission Delegated Regulation (EU)
   2024/1772). Emit the classification-decision record. On the
   not-major branch, short-circuit the notification chain but still
   emit the dated decision so the audit-evident chain is closed.
2. **notify-authority-initial** — package the initial notification
   against the ITS content shape (Commission Implementing Regulation
   (EU) 2024/2956) and dispatch to the competent authority. Fires
   within 4 hours of classification / 24 hours from awareness.
3. **notify-authority-intermediate** — package the intermediate report
   against the ITS content shape and dispatch. Fires within 72 hours
   of classification (or earlier if regular activities have
   recovered).
4. **notify-authority-final** — package the final report (root-cause
   analysis, final impact figures, remediation, lessons learned,
   action plan, residual-risk statement) and dispatch. Fires no later
   than one month after the intermediate report.
5. **close-and-archive** — compose the dated cycle-archival record
   referencing the classification decision, the three submissions,
   the authority acknowledgements, and any cross-regime notification
   chains (NIS2 Art. 23, GDPR Art. 33-34). The archival record is
   the audit-evident cycle closure.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.dora_major_incident_reporting@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, D3FEND stub,
  OCSF stub, DORA Art. 19 primary, NIS2 Art. 23 cross-regime sibling,
  GDPR Art. 33-34 cross-regime sibling).

## Goal links

- **G-01** — content coverage: dedicated DORA-flavoured major-ICT-
  related-incident reporting playbook closing the Chapter III surface
  upstream of the existing NIS2 Art. 23-flavoured
  `incident_management` playbook; advances the target of ≥ 25 CACAO
  v2 playbooks.
- **G-02** — regulatory-graph closure: DORA Art. 19 (4)(a)/(b)/(c)
  and Art. 18(1) primary anchors, with sibling references to NIS2
  Art. 23(4)(b) and GDPR Art. 33 for the cross-regime parallel-
  notification relationship.
