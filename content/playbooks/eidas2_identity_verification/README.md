# eidas2_identity_verification

CACAO v2 SKELETON playbook for the eIDAS 2.0 European Digital Identity
Wallet (EUDIW) identity-verification lifecycle a regulated operator
runs when onboarding a new EUDIW-enabled principal to a protected
access surface: request an EUDIW presentation → cryptographically
verify the PID credential against the EU trust-anchor registry →
assess the returned Level of Assurance and map it to the operator-side
access tier → emit the dated identity-verification audit-evidence
artifact (OCSF Account Change 3001) → hand off to the downstream
access-provisioning workflow. Read-only against the wallet surface
and against the trust-anchor registry; no attribute is asserted back,
no trust-list entry is mutated. The regulatory anchor set is eIDAS 2.0
(Regulation (EU) 2024/1183) as read through NIS2 Art. 21(2)(i) access
management and DORA Art. 5 digital-identity governance.

## Status

SKELETON. The playbook artifact and the outbound overlay
(OSCAL AC-2 + IA-8, D3FEND D3-OAM, OCSF Account Change 3001, NIS2
Art. 21(2)(i), DORA Art. 5) land here. CORE-layer cards add the
per-target compiler emissions (n8n / Temporal / LangGraph goldens)
and the primitive bodies (presentation-request adapter, trust-anchor
probe, LoA-to-tier mapping); an EXTEND card wires the OCSF Compliance
Finding (2003) emission for the verification-failure branch and the
LoA-tier-drift KRI.

## Regulatory anchors

- **eIDAS 2.0** — Regulation (EU) 2024/1183 amending Regulation (EU)
  No 910/2014 (European Digital Identity Framework). Art. 5c pins the
  EUDIW presentation-request surface the request_eudiw_presentation
  step exercises.
- **NIS2** — Directive (EU) 2022/2555, Art. 21(2)(i) (human resources
  security, access-control policies, asset management). Inbound
  mapping id `nis2:art-21-2-i`.
- **DORA** — Regulation (EU) 2022/2554, Art. 5 (governance and
  organisation, ICT risk-management framework, digital-identity
  governance). Inbound mapping id `dora:art-5-governance`.

## EU-hosting note

The trust-anchor probe in verify_pid_credential resolves against
Member-State Trusted Lists and the LOTL aggregator per Commission
Implementing Decision (EU) 2015/1505 as maintained under eIDAS 2.0.
No non-EU trust anchor is assumed. No Microsoft / Google EUDIW proxy
surface is modelled: the wallet-side protocol is OpenID4VP / ARF v2
against the operator's own verifier. Downstream access-provisioning
hand-off routes into `playbook.onboarding_offboarding_tracker@v1`
which is itself framed against EU-hostable orchestrators (n8n,
Temporal, LangGraph on Nebul / OVHcloud / Scaleway / Hetzner).

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.eidas2_identity_verification@v1`).
- `mappings.yaml` — outbound overlay (OSCAL controls, D3FEND
  technique, OCSF telemetry class, NIS2 + DORA cross-references).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`.
Emitted artifacts and golden tests are owned by CORE-layer sibling
cards; this directory ships the portable content only.

## Companion pattern

The `patterns/eidas2_wallet/` typed-input pattern (F-SV-02) models the
already-verified wallet artifact a workflow *accepts*. This playbook
is the content-layer complement: the operational discipline that
*produces* that verified artifact. The two are deliberately distinct
— the pattern is a compile-layer concern; the playbook is a
content-layer concern — and the CACAO artifact does not directly
reference the Pydantic input type.
