# dora_tpr_management

CACAO v2 SKELETON playbook operationalising **DORA Chapter V ICT
third-party risk management** for an EU financial entity. Anchored on
Regulation (EU) 2022/2554 **Article 28** (general principles for the
use of ICT third-party service providers — the register of
information, pre-contractual risk assessment, criticality
determination, sub-outsourcing surface, and exit-strategy discipline)
and **Article 30** (key contractual provisions — the closed clause set
every ICT third-party contract must carry).

Status: **SKELETON**. Action steps are scaffolded as CACAO v2 actions
with `control_refs` / `telemetry_refs` stubs; the per-step primitive
bodies (deterministic pre-contractual risk-assessment rubric, Article
30 clause-presence check, Article 28 register-row composition,
periodic-review drift detection, and Article 28(8) exit-assessment
attestation emission) are placeholders that a sibling CORE-PRIM card
lands.

## Scope boundary

This playbook is the **contract-lifecycle third-party governance
spine** the DORA register anchors. It composes against the following
sibling playbooks without absorbing their scope:

- **`playbook.supply_chain_security@v1`** — the runtime
  supply-chain-signal spine (SBOM correlation, supplier-attestation
  lookup, per-execution supply-chain-evidence emission). Anchors on
  NIS2 Article 21(2)(d), not DORA. The `periodic_review` step of this
  playbook reads the runtime supply-chain-evidence stream on the
  provider handle so a `watch` or `confirmed_compromise` verdict from
  the runtime workflow re-enters the DORA register.
- **`playbook.contractual_obligations_tracker@v1`** — the per-obligation
  clause-attestation cadence across every declared contractual
  obligation regardless of counterparty type. The `contractual_provisions_check`
  step of this playbook is the DORA-specific Article 30(2)/(3)
  clause-presence check at the contract-onboarding boundary; the
  ongoing per-obligation re-attestation cadence is delegated to the
  contractual_obligations_tracker playbook.
- **`playbook.dora_ict_risk_selfassess@v1`** — the whole-Chapter II
  ICT risk management self-assessment roll-up (Articles 6/7/8/10/11).
  DORA Chapter V (third-party risk) is out of scope for that roll-up
  by construction; this playbook is the dedicated Chapter V discharge.

## Contents

- `playbook.cacao.json` — the CACAO v2 artifact
  (`playbook.dora_tpr_management@v1`). Pins the five-step topology
  (`workflow_start → onboarding_risk_assessment →
  contractual_provisions_check → register_entry → periodic_review →
  exit_assessment → workflow_end`) plus the per-step
  `x_secops_ng.control_refs` joins into the SecOps-NG content model.
  `regulatory_anchors` declares `dora:art-28` and `dora:art-30`;
  `evidence_streams` declares the `vendor_assessment` stream stub the
  CORE-PRIM primitive body wires.
- `mappings.yaml` — outbound playbook-mappings overlay. Ships with the
  OSCAL `SR-3` (Supply Chain Controls and Processes) and `SR-6`
  (Supplier Assessments and Reviews) anchors, an OCSF API-Activity
  stub for the register-emission surface, and a `dora: []` placeholder
  block deferring the inbound wiring to the CORE-EXTEND sibling under
  `content/mappings/dora/`.

## Compile targets

`compile_targets` declares `[n8n, temporal, langgraph]`. Emitted
artifacts under `examples/{n8n,temporal,langgraph}/dora_tpr_management/`
land in a follow-on CORE-FANOUT card once the per-step primitives are
populated. The `SKELETON` layer is intentionally scoped to one
deliverable per forward-public-hygiene convention: shape the contract,
defer the content.

## Step outline

1. **onboarding_risk_assessment** — score a candidate ICT third-party
   service provider against the operator's documented pre-contractual
   risk-assessment rubric (function criticality, sub-outsourcing chain,
   data-location, concentration exposure — the axes Article 28(4)
   names). Sets `__criticality_determination__` and
   `__risk_assessment_ref__`.
2. **contractual_provisions_check** — verify the negotiated contract
   carries the Article 30(2) and 30(3) closed clause set (service
   description, data-processing locations, exit-strategy obligations,
   audit rights, termination rights, sub-contracting conditions,
   service-level descriptions, insolvency and resolution provisions).
   Records `__clause_check_ref__` with per-clause status
   present / present_with_deviation / absent.
3. **register_entry** — compose and publish the Article 28 register-of-
   information row for the provider, joined to the criticality
   determination and the accepted-clause set. Content-addressed
   against `SHA-256(workflow_id|execution_id|captured_at)`. Sets
   `__register_row_id__`.
4. **periodic_review** — re-read the register row on the operator's
   documented review cadence (`__review_window__`) and re-score
   criticality against the current runtime supply-chain-evidence
   stream (`__runtime_supply_chain_evidence_ref__`). Sets
   `__periodic_review_ref__`. Exit is never auto-invoked: when a
   re-scored criticality crosses an exit-decision threshold, the
   operator's governance surface consumes the review block to invoke
   exit_assessment.
5. **exit_assessment** — discharge the Article 28(8) exit-strategy
   discipline on a documented `__exit_trigger__` (operator election,
   periodic-review failure, contractual termination, provider
   insolvency, regulatory direction). Emits the dated exit-assessment
   attestation joined to the register row, the risk-assessment block,
   the clause-check block, and the periodic-review block. Sets
   `__exit_attestation_id__`.

## Regulatory anchors

| Step (playbook axis)              | Clause                                    |
| --------------------------------- | ----------------------------------------- |
| Pre-contractual risk assessment   | DORA Article 28(4)                        |
| Contractual provisions check      | DORA Article 30(2) and 30(3)              |
| Register-of-information entry     | DORA Article 28(3); Commission ITS 2024/2956 |
| Periodic review + drift detection | DORA Article 28(1)(a) monitoring cadence  |
| Exit-strategy attestation         | DORA Article 28(8)                        |

The inbound wiring at
[`content/mappings/dora/article-19-and-28.yaml`](../../mappings/dora/article-19-and-28.yaml)
already carries a `dora:art-28-third-party-register` atom that will
gain `playbook.dora_tpr_management@v1` in its `playbook_refs:` in the
CORE-EXTEND sibling; a new `content/mappings/dora/article-30.yaml`
entry lands in the same CORE-EXTEND sibling for the Article 30 axis.
The SKELETON is deliberately orphan-tolerant for the G-02 orphan-CI
7-day grace window.

## Operator integration notes

The SKELETON declares the following adapter-bound surfaces the
operator wires; the CORE-PRIM card lands the reference bindings:

- **Critical-or-important-function register** — the operator's
  declared register of the business or ICT functions that qualify as
  critical or important under DORA Article 3(22) and the operator's
  own governance documentation. Consumed by the onboarding-risk-
  assessment step to key the criticality determination against the
  supported function.
- **Pre-contractual risk-assessment rubric** — the operator's
  documented rubric with the four axes Article 28(4) names (function
  criticality, sub-outsourcing chain, data-location, concentration
  exposure) plus the operator's declared threshold set (typically
  `{non_critical, important, critical}` with a supporting-critical
  bucket).
- **Article 30 clause-shape rubric** — the operator's declared
  per-clause shape (service description, data-processing locations,
  exit-strategy obligations, audit rights, termination rights,
  sub-contracting conditions, service-level descriptions, insolvency
  and resolution provisions) the clause-presence check reads against.
- **Register sink** — the operator's evidence store the Article 28
  register row is published to, with the content-addressed filename
  derived from the artifact_id.
- **Exit-strategy discipline** — the operator's declared exit-strategy
  playbook for critical-or-important-function ICT third-party service
  providers; the exit-assessment step emits the attestation that
  discharges the Article 28(8) obligation on the operator side.

Third-party risk on the DORA Chapter V surface is a governance
infrastructure discipline for EU financial operators: the register,
the pre-contractual assessment, the clause set, the review cadence,
and the exit discipline form one closed lifecycle the regulator
audits end-to-end. This playbook is the operator's agentic spine
against that lifecycle, not a vendor-selection tool.

## Sources

- OASIS CACAO v2.0 specification.
- DORA — Regulation (EU) 2022/2554, Chapter V (Articles 28–44), ICT
  third-party risk management.
- DORA — Regulation (EU) 2022/2554, Article 28, general principles
  for the use of ICT third-party service providers.
- DORA — Regulation (EU) 2022/2554, Article 30, key contractual
  provisions.
- Commission Implementing Regulation (EU) 2024/2956 — ITS on the
  standard templates for the register of information.
- NIST SP 800-53 Rev. 5 — SR-3 (Supply Chain Controls and Processes),
  SR-6 (Supplier Assessments and Reviews).
- OCSF v1.3.0 — API Activity (class_uid 6003) event class.
