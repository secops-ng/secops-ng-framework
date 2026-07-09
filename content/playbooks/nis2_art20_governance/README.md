# nis2_art20_governance

CACAO v2 SKELETON playbook for the NIS2 Directive (EU) 2022/2555
Article 20 management-body cybersecurity governance lifecycle:
schedule management review → present risk posture (over the current
Art. 21(2)(a)–(j) coverage) → approve risk-management measures (with
the Art. 20(2) management-body training-completion attestation
carried on the approval record) → log the dated governance-record
evidence artifact. Read-only against the operator's evidence store
and governance-cadence catalogue; the four-step cycle records the
governance-decision outcome and does not mutate any operational
control surface.

This playbook is the governance-body approval companion to the
sibling `nis2_self_assessment` playbook (the whole-Article-21
evidence roll-up on the operator's declared self-assessment cadence)
and to the F-CP-06 effectiveness loop (per-metric snapshots on the
evaluation-window cadence): those two operate the evidence-side and
measurement-side surfaces of Article 21; this playbook operates the
governance-body approval surface Article 20(1) names.

## Status

SKELETON. The CACAO v2 artifact (`playbook.nis2_art20_governance@v1`),
the outbound overlay (OSCAL PM-2 + SA-2, D3FEND D3-PSEP on the
approve step, OCSF API Activity 6003 on the log step, NIS2 Art.
20(1) + 20(2) inbound anchors), and the inbound NIS2 Art. 20 mapping
entry at `content/mappings/nis2/article-20.yaml` land here. CORE-
layer cards add the per-target compiler emissions (n8n / Temporal /
LangGraph goldens) and the primitive bodies (governance-cadence-
catalogue probe, evidence-store posture-composition, governance-
decision record shape, deterministic evidence-record derivation).
An EXTEND card wires the practitioner cookbook and any KPI/KRI
emitters (e.g. a management-body training-overdue KRI) once the
metric shapes are ratified.

## Regulatory anchors

- **NIS2** — Directive (EU) 2022/2555, Article 20(1) (management-
  body approval of cybersecurity risk-management measures, oversight
  of their implementation, and liability for infringements) and
  Article 20(2) (cybersecurity training for members of the
  management body, and encouragement of similar training for all
  employees). Inbound mapping ids `nis2:art-20-1` and
  `nis2:art-20-2` under `content/mappings/nis2/article-20.yaml`.
- **NIS2** — Directive (EU) 2022/2555, Article 21(2)(a)–(j) is the
  downstream obligation surface Article 20(1) anchors on; the
  present_risk_posture step reads over the whole-Article-21
  coverage buckets composed by `playbook.nis2_self_assessment@v1`
  and any per-clause playbook evidence records that post-date the
  most recent self-assessment attestation.

## Sovereign-stack note

No proprietary governance-tooling surface is assumed. The
governance-cadence catalogue (which management-body forum, which
meeting cadence, which agenda-slot conventions) and the management-
body member roster live in the operator's own governance
documentation upstream of this playbook. The dated evidence
artifact this playbook emits is a plain JSON governance-record
shaped against a `schemas/evidence/governance.schema.json` envelope
landing in the sibling CORE card; the evidence-sink is whatever
EU-hostable object surface (Nebul, OVHcloud, Scaleway, Hetzner) the
operator already runs.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.nis2_art20_governance@v1`).
- `mappings.yaml` — outbound overlay (OSCAL PM-2 + SA-2, D3FEND
  D3-PSEP on the approve step, OCSF API Activity 6003, NIS2 Art.
  20(1) + 20(2)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`.
Emitted artifacts and golden tests are owned by CORE-layer sibling
cards; this directory ships the portable content only.
