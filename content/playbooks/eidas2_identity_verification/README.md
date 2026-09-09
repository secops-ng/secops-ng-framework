# eidas2_identity_verification

CACAO v2 playbook for the eIDAS 2.0 European Digital Identity
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

Stable — `content_version` 1.0.0 under the Maturity ladder. All five
action steps carry `x_secops_ng.core_body` bindings into the
deterministic primitives under `primitives/`
(`presentation.compose_presentation_request`,
`verification.record_pid_verification`,
`assurance.assess_assurance_level`,
`evidence.compose_identity_evidence_record`,
`provisioning.compose_provisioning_handoff`), each executed directly
by the unit suite under
`tests/playbooks/eidas2_identity_verification/`. The outbound overlay
(OSCAL AC-2 + IA-8, D3FEND D3-OAM, OCSF Account Change 3001, NIS2
Art. 21(2)(i), DORA Art. 5) and the three worked examples under
`examples/{n8n,temporal,langgraph}/eidas2_identity_verification/` ship
alongside, regenerated from the bound source: n8n emits five Code
nodes, and the Temporal activities and LangGraph tools import their
primitives, with `NotImplementedError` marking only the
operator-integration seams (the OpenID4VP verifier transport, the
trust-anchor probe and status-list read, the evidence sink, the
provisioning dispatch).

Two sovereignty properties are enforced rather than described: the
verification record retains the outcome and its provenance and
**actively refuses** a report carrying attested attributes, and there
is no partial-trust state — every check must hold and the revocation
status must be active, with suspended and unknown failing closed.

Still owed, and recorded as such: the OCSF Compliance Finding (2003)
emission for the verification-failure branch and the LoA-tier-drift
KRI remain a metrics-layer card; the steps carry no `metric_refs`
until it lands.

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
- `primitives/` — the five deterministic primitives the action steps
  bind: pure, offline, LLM-free. The presentation request names
  credential types only; the verification record keeps outcome plus
  provenance and no attested attribute; the assurance assessment
  refuses below-minimum rather than downgrading; the evidence record
  is emitted on every terminal path with the prescribed id
  derivation; the provisioning hand-off is a reasoned no-op on both
  refusal branches.
- `cookbook.md` — the practitioner walkthrough (mirrored at
  [`docs/cookbook/eidas2_identity_verification.md`](../../../docs/cookbook/eidas2_identity_verification.md)).

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
emitted artifacts live under
`examples/{n8n,temporal,langgraph}/eidas2_identity_verification/`
with byte-parity goldens under `tests/examples/`, regenerated from
the bound canonical source via each directory's `regenerate.sh`.

## Companion pattern

The `patterns/eidas2_wallet/` typed-input pattern (F-SV-02) models the
already-verified wallet artifact a workflow *accepts*. This playbook
is the content-layer complement: the operational discipline that
*produces* that verified artifact. The two are deliberately distinct
— the pattern is a compile-layer concern; the playbook is a
content-layer concern — and the CACAO artifact does not directly
reference the Pydantic input type.
