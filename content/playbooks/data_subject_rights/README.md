# data_subject_rights

CACAO v2 playbook operationalising the operator-side
**data subject rights (DSR) intake and fulfilment lifecycle** a
controller runs when a data subject exercises one of the GDPR
Chapter III rights against personal data the controller holds.
Covers the receive-to-record chain across the six operational
rights plus the Article 22 classifier axis:

- **Article 15** — right of access.
- **Article 16** — right to rectification.
- **Article 17** — right to erasure / right to be forgotten.
- **Article 18** — right to restriction of processing.
- **Article 20** — right to data portability.
- **Article 21** — right to object.
- **Article 22** — automated individual decision-making concerns
  are classified at `classify_request` and routed to the
  controller's human-in-the-loop review surface as part of the
  objection lane. The workflow does not itself review the
  underlying automated decision.

Distinct from the Article 33 / Article 34 personal-data-breach
notification lifecycle (owned by the sibling `incident_management`
and `data_exfil` playbooks): this lifecycle is subject-initiated
against already-collected data; the breach-notification lifecycle
is controller-initiated on a personal-data-breach event.

Status: **stable** — `content_version` 1.0.0 under the Maturity
ladder. All seven action steps carry `x_secops_ng.core_body`
bindings into the deterministic primitives under `primitives/`
(`intake.open_dsr_case`, `verification.record_identity_verification`,
`classification.classify_request`, `routing.resolve_data_owner_manifest`,
`fulfilment.compile_fulfilment_pack`,
`response.compose_controller_response`, `outcome.record_case_outcome`),
each executed directly by the unit suite under
`tests/playbooks/data_subject_rights/`. One `if-condition` on
`__identity_verified__` after classification makes the Article 12(6)
short-circuit real topology: an unverified requester never reaches
data-owner routing; the case goes straight to the additional-
information response and closes as `unverified_subject`. The three
worked examples under `examples/{n8n,temporal,langgraph}/data_subject_rights/`
are regenerated from the bound source (n8n: seven Code nodes and one
If node; Temporal activities and LangGraph tools import their
primitives, with `NotImplementedError` marking only the operator-
integration seams). The sovereign IdP verification surface, the
data-inventory join, owner transport, secure delivery and the
evidence store remain adapter-bound operator surfaces — the framework
ships the deterministic contract, not a connector.

## Contents

- `playbook.cacao.yaml` — the CACAO v2 artifact
  (`playbook.data_subject_rights@v1`), authored as YAML per the
  finalisation-marker convention (`.cacao.json` or `.cacao.yaml`
  both counted as finalised).
- `mappings.yaml` — outbound cross-references to the OSCAL controls,
  MITRE D3FEND techniques, OCSF event classes, and EU regulatory
  clauses this playbook operationalises. The overlay pins the GDPR
  Articles 15-22 clause anchors, the OSCAL AC-2(11) and AU-9
  anchors, and the D3FEND D3-IAA Identity Access Assurance anchor
  on the `verify_identity` step.
- `primitives/` — the seven deterministic primitives the action
  steps bind: pure, offline, LLM-free. The Article 12(3) clock is
  anchored on the supplied receipt instant (never a clock read),
  deadlines use calendar-month arithmetic with the end-of-month
  clamp, an extension is representable only with its justification,
  a refusal always carries the Article 77 / 79 remedies, and the
  verification record stores no subject-supplied attribute.

## Compile targets

`compile_targets` declares `["n8n", "temporal", "langgraph"]`. The
emitted artifacts live under
`examples/{n8n,temporal,langgraph}/data_subject_rights/` with
byte-parity goldens under `tests/examples/`, regenerated from the
bound canonical YAML via each directory's `regenerate.sh` (which
mirrors the YAML into a byte-deterministic JSON form first).

## Step outline

1. **receive_request** — DSR intake surface (privacy-policy
   address, subject-facing portal, paper channel). Stamps
   `__case_id__` and `__request_received_ts__`.
2. **verify_identity** — sovereign IdP integration point on the
   SecOps-NG substrate (IdP-bound assertion for account-holders;
   out-of-band verification playbook for non-account subjects).
   Sets `__identity_verified__`.
3. **classify_request** — resolves `__request_type__` (access /
   rectification / erasure / restriction / portability / objection
   / Article 22 concern). Computes `__response_deadline__` as
   `__request_received_ts__` + 1 calendar month per Article 12(3),
   end-of-month clamped; records the justified extension where
   invoked. Runs before the gate so both branches carry a deadline.
4. **identity verified?** — the `if-condition` on
   `__identity_verified__`: true continues to routing; false
   short-circuits to `send_controller_response` for the Article
   12(6) additional-information request.
5. **route_to_data_owners** — resolves the per-owner manifest
   against the controller's declared data-inventory surface.
6. **compile_fulfilment_evidence** — assembles the per-request
   fulfilment pack (subject-copy assembly, applied-correction
   attestation, deletion attestation, restriction-marker set,
   structured data package, cessation record, or overriding-
   legitimate-interest determination).
7. **send_controller_response** — composes the response envelope on
   or before `__response_deadline__` under the Article 12
   modalities: fulfilment pack, refusal with remedies, or the
   Article 12(6) additional-information request — exactly one.
8. **record_outcome** — closes the case with `__outcome_code__`
   for the operator's Article 5(2) accountability posture.

## Regulatory anchors

| Right (playbook axis)         | Clause                       |
| ----------------------------- | ---------------------------- |
| Access                        | GDPR Article 15              |
| Rectification                 | GDPR Article 16              |
| Erasure                       | GDPR Article 17              |
| Restriction                   | GDPR Article 18              |
| Portability                   | GDPR Article 20              |
| Objection                     | GDPR Article 21              |
| Automated-decision review     | GDPR Article 22 (classifier) |
| Response-window modalities    | GDPR Article 12(3)           |
| Accountability                | GDPR Article 5(2)            |

Inbound mappings live at
[`content/mappings/gdpr/article-15-22-data-subject-rights.yaml`](../../mappings/gdpr/article-15-22-data-subject-rights.yaml).

## Operator integration notes

The playbook declares the following adapter-bound surfaces the
operator wires; the deterministic halves are bound under
`primitives/`, and the wired variables name each seam:

- **DSR intake surface** — the privacy-policy contact channel,
  the subject-facing in-app portal, and the paper-channel intake
  the controller's DSR policy admits. `receive_request` consumes it
  as `__raw_request__` + `__intake_channel__`.
- **Sovereign IdP integration point** — the operator's declared
  subject-verification surface for account-holders. On the
  SecOps-NG substrate the default binding is an EU-resident IdP
  under the sovereignty-first foundation
  (see [`docs/FOUNDATION.md`](../../../docs/FOUNDATION.md)).
- **Out-of-band verification playbook** — the fallback for
  non-account subjects (recognised identity-document check,
  shared-secret verification, call-back to a channel of record).
- **Data-inventory surface** — the controller's canonical data-
  inventory join key that `route_to_data_owners` resolves the
  per-owner manifest against.
- **Response-envelope templates** — the portability data-package
  format (structured, commonly-used, machine-readable per
  Article 20(1)), the erasure-attestation letter, the
  rectification confirmation, the access-copy assembly, and the
  refusal-with-remedy template.

## Sources

- OASIS CACAO v2.0 specification.
- General Data Protection Regulation (EU) 2016/679 —
  Chapter III (Articles 12-22).
- EDPB Guidelines 01/2022 on data subject rights — right of
  access.
- OCSF v1.3.0 — Compliance Finding (class_uid 2003) event class.
