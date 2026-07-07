# dora_tlpt_programme

CACAO v2 SKELETON playbook operationalising the operator-side **DORA
Chapter IV digital operational resilience testing (DORT) programme** a
financial entity discharges against its ICT risk-management framework
— Article 24 (general requirements for the testing of digital
operational resilience) and Article 26 (advanced testing of ICT
tools, systems and processes based on threat-led penetration testing,
anchored on the ECB TIBER-EU framework as the implementation
reference).

Distinct from the `dora_ict_risk_selfassess` playbook (whole-Chapter II
roll-up on the Art. 6(5) annual-review cadence) and from the per-section
posture playbooks (`crypto_posture_management`, `detection_engineering`,
etc. — the per-section producing surfaces that roll-up aggregates):
this playbook is the Chapter IV testing-programme discipline, keyed on
the four programme-lifecycle atoms the operator discharges on the
mandatory-TLPT cadence prescribed by the competent authority against
the operator's designated critical-or-important functions.

Status: **EXTEND** (cookbook walkthrough shipped at
[`docs/cookbook/dora_tlpt_programme.md`](../../../docs/cookbook/dora_tlpt_programme.md)).
Action steps are scaffolded as CACAO v2 actions with `control_refs` /
`telemetry_refs` bound; the compile-target parity lane is
materialised as three worked examples under
`examples/{n8n,temporal,langgraph}/dora_tlpt_programme/` with
byte-parity goldens under
`tests/examples/{n8n,temporal,langgraph}/dora_tlpt_programme/`. The
per-step primitives (scope-catalogue composition, TLPT
trigger-and-planning gate, competent-authority notification adapter,
red-team scoping-submission adapter, findings-register schema,
remediation-attestation emitter) remain adapter-bound placeholders
that a sibling EXTEND card lands alongside the TIBER-EU red-team
choreography, the threat-intelligence-source binding, and the
purple-team lessons-learned loop into `detection_engineering`.

## Trilogy

- **SKELETON:** scaffold + mappings + compile-target declaration (PR #714).
- **CORE:** three-target compiled examples + byte-parity goldens,
  full mappings closure (D3-OAM D3FEND selection, NIS2 Art. 21(2)(f) +
  GDPR Art. 32(1)(d) inbound edges, CRA + EU AI Act reviewed skips)
  (PR #715).
- **EXTEND (this card):** cookbook walkthrough at
  [`docs/cookbook/dora_tlpt_programme.md`](../../../docs/cookbook/dora_tlpt_programme.md).
  Adapter Protocols under `patterns.dora_tlpt_programme`, the
  TIBER-EU red-team choreography, threat-intelligence-source
  binding, and the purple-team lessons-learned loop into
  `detection_engineering` land on a sibling EXTEND card.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.dora_tlpt_programme@v1`), authored as JSON per the
  finalisation-marker convention (`.cacao.json` or `.cacao.yaml` both
  counted as finalised).
- `mappings.yaml` — outbound cross-references to the OSCAL controls,
  MITRE D3FEND techniques, OCSF event classes, and EU regulatory
  clauses this playbook operationalises. The CORE overlay pins the
  DORA Chapter IV testing-programme atom
  (`dora:art-24-26-dort-tlpt-programme`), the OSCAL CA-2 (Control
  Assessments) anchor with CA-8 (Penetration Testing) absorbed into
  the effectiveness-testing slice, the D3-OAM (Operational Activity
  Mapping) technique on the remediation-tracking step, the OCSF API
  Activity binding, and the NIS2 Art. 21(2)(f) +
  GDPR Art. 32(1)(d) effectiveness-testing cross-references.

## Compile targets

`compile_targets` declares `[n8n, temporal, langgraph]`. Emitted
artifacts ship at CORE under
`examples/{n8n,temporal,langgraph}/dora_tlpt_programme/`, each with
its own regenerate script, mirrored CACAO source, and byte-parity
drift guards under
`tests/examples/{n8n,temporal,langgraph}/dora_tlpt_programme/`.

## Step outline

1. **define_dort_scope** — read the operator's business-service register,
   ICT-asset register, and ICT third-party service-provider register to
   compose the DORT-scope catalogue for the current testing-programme
   window per Art. 24: the ICT-supported critical or important
   functions in scope, the supporting ICT assets, and the ICT
   third-party service providers whose services are in scope. Sets
   `__dort_scope_catalogue__`.
2. **tlpt_trigger_and_planning_gate** — evaluate whether TLPT is
   mandatory in the window against the JC Joint Guidelines on TLPT
   (JC 2022 03) criteria and the operator's declared
   `__entity_significance_tier__` per Art. 26(1); notify the competent
   authority; record the declared programme cadence, threat-intelligence
   source, and internal-versus-external tester posture. Sets
   `__tlpt_trigger_decision__`.
3. **red_team_scoping_approval** — package the red-team scoping
   submission per Art. 26(3) against the operator's declared providers
   (internal or external, with the certification / independence
   criteria the JC RTS names), dispatch to the competent authority,
   and bind the approval or deferral outcome. Sets
   `__red_team_scoping_id__`.
4. **remediation_tracking** — compose the findings register from the
   red-team engagement, bind each finding to a remediation timeline
   against the operator's declared severity rubric, and emit the
   dated competent-authority remediation attestation per Art. 26(8).
   Sets `__findings_register_id__` and
   `__remediation_attestation_id__`.

## Regulatory anchors

| Step (playbook axis)                | Clause                                                  |
| ----------------------------------- | ------------------------------------------------------- |
| DORT scope definition               | DORA Art. 24; JC RTS Art. 25                            |
| TLPT trigger and planning gate      | DORA Art. 26(1); ESAs JC 2022 03; TIBER-EU              |
| Red-team scoping approval           | DORA Art. 26(3); JC RTS Art. 26                         |
| Remediation tracking + attestation  | DORA Art. 26(8)                                         |

Inbound mapping lives at
[`content/mappings/dora/article-24-26.yaml`](../../mappings/dora/article-24-26.yaml)
(`dora:art-24-26-dort-tlpt-programme`) for the primary DORA anchor,
with CORE-added cross-regime edges under
[`content/mappings/nis2/article-21-2-f.yaml`](../../mappings/nis2/article-21-2-f.yaml)
(NIS2 effectiveness-assessment adjacent anchor) and
[`content/mappings/gdpr/article-32-security-of-processing.yaml`](../../mappings/gdpr/article-32-security-of-processing.yaml)
(GDPR Art. 32(1)(d) regular-testing lane). CRA and EU AI Act axes
are recorded as reviewed skips in the respective
`_orphan_skip.yaml` files (see `mappings.yaml` header notes).

## Operator integration notes

The CORE tier declares the following adapter-bound surfaces the operator
wires; the sibling EXTEND card lands the reference bindings under
`patterns.dora_tlpt_programme`:

- **Business-service register** — the operator's declared register of
  ICT-supported critical or important functions per Art. 8
  identification. The scope-definition step reads this register to
  compose the DORT-scope catalogue.
- **ICT-asset register** — the operator's declared register of ICT
  assets and their pinning to the business-service register (each
  critical or important function must resolve to the supporting ICT
  assets in scope).
- **ICT third-party register** — the operator's declared register of
  ICT third-party service providers per Art. 28 third-party risk
  (used here only for scope composition, not for third-party risk
  discharge — that is the `supply_chain_security` playbook's surface).
- **Entity significance tier** — the operator's declared tier under
  the JC 2022 03 identification criteria. Read-only against the
  operator's declared tier at the trigger gate; the primitive does
  not itself judge the tier.
- **Threat-intelligence source** — the declared source the TLPT
  engagement's threat-intelligence provider reads against (per Art.
  26(2) the threat-intelligence must reflect the operator's threat
  landscape). Binding lands in the sibling EXTEND card.
- **Competent-authority notification / approval channel** — the
  declared adapter binding for the Art. 26(1) notification and the
  Art. 26(3) scoping-approval submission. Binding lands in the
  sibling EXTEND card under `patterns.dora_tlpt_programme`.
- **Evidence store** — the operator's declared evidence store the
  dated remediation attestation is published to at the
  remediation-tracking step, with the content-addressed filename
  derived from the artifact_id `SHA-256(workflow_id|execution_id|captured_at)`.

## Sources

- OASIS CACAO v2.0 specification.
- DORA — Regulation (EU) 2022/2554, Chapter IV (Articles 24–27)
  digital operational resilience testing.
- ESAs Joint Committee — Joint Guidelines on the criteria for the
  identification of financial entities required to perform threat-led
  penetration testing (JC 2022 03).
- Commission Delegated Regulation (EU) 2024/1774 — JC RTS on ICT
  risk-management framework (Articles 25–26 testing scope).
- NIST SP 800-53 Rev. 5 — CA-2 (Control Assessments), CA-8
  (Penetration Testing).
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
- ECB — TIBER-EU framework (threat-intelligence-based ethical red
  teaming).
