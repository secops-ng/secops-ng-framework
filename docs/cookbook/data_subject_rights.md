# data_subject_rights — cookbook walkthrough

Operator-side intake and fulfilment lifecycle a controller runs when
a data subject exercises one of the GDPR Chapter III rights against
personal data the controller holds. The
`playbook.data_subject_rights@v1` CACAO playbook operates the
receive-to-record chain across the six operational rights (access,
rectification, erasure, restriction, portability, objection) plus
the Article 22 automated-decision classifier axis. The workflow is
anchored on the Article 12(3) one-month response window, extendable
by two further months where necessary, and closes with a durable
per-case record for the controller's Article 5(2) accountability
posture.

The playbook is the **portable description of the DSR discharge**.
It does not choose the intake surface (privacy-policy contact,
in-app portal, paper channel), does not embed subject-verification
credentials, and does not decide the controller's data-inventory
join key. It describes the workflow shape the controller's stack
should run so the seven-step lifecycle is auditable, replayable, and
restart-safe — as a shipped Digital Commons artifact.

Distinct from the Article 33 / Article 34 personal-data-breach
notification lifecycle (owned by the sibling `incident_management`
and `data_exfil` playbooks): this lifecycle is subject-initiated
against already-collected data; the breach-notification lifecycle
is controller-initiated on a personal-data-breach event.

This walkthrough wires the SKELETON playbook through all three
reference compile targets (n8n, Temporal, LangGraph) and shows
where the intake, sovereign-IdP verification, classification,
owner routing, evidence assembly, response emission, and outcome
record land in each. Adapter bodies (subject-verification against
the sovereign IdP, per-data-store owner-routing catalogue, response
templates) are declared as adapter-bound surfaces the operator
wires; a sibling CORE card lands the reference bindings.

> The framework is framework-agnostic by construction. n8n /
> Temporal / LangGraph are *three of three* reference targets;
> the same CACAO source compiles into all of them. Operators
> run whichever target already lives in their stack.

## 1. Why this matters

GDPR Chapter III grants data subjects a set of rights against
personal data a controller holds. Articles 15–22 name the
operational rights the workflow discharges; Article 12(3) fixes
the response window:

- **Art. 15** — right of access (incl. Art. 15(1)(a)–(h)
  meta-information and Art. 15(3) subject-copy provision).
- **Art. 16** — right to rectification.
- **Art. 17** — right to erasure / right to be forgotten, with
  Art. 17(3) retention-exemption carve-outs.
- **Art. 18** — right to restriction of processing, with
  Art. 18(3) subsequent-lifting notification.
- **Art. 20** — right to data portability, structured
  commonly-used machine-readable format.
- **Art. 21** — right to object.
- **Art. 22** — automated individual decision-making; treated on
  this workflow as a classifier axis on `receive_request` and
  routed to the controller's human-in-the-loop review surface
  as part of the objection lane. The workflow does not itself
  review the underlying automated decision.
- **Art. 12(3)** — the controller replies without undue delay
  and in any event within **one month** of receipt of the
  request, extendable by two further months where necessary
  taking into account the complexity and number of requests.

Missing the Art. 12(3) deadline is a supervisory-authority-visible
event under Art. 58(1)(a). Wiring the deadline into an
orchestration surface that survives worker restart is the
audit-evident discharge of the obligation; wiring it into the
controller's incident-tracker "on best effort" is not.

## 2. Source of truth

```
content/playbooks/data_subject_rights/
├── README.md                    # workflow-local overview and status
├── mappings.yaml                # outbound OSCAL / D3FEND / OCSF / GDPR overlay
└── playbook.cacao.yaml          # canonical CACAO v2 source (playbook.data_subject_rights@v1)

content/mappings/gdpr/article-15-22-data-subject-rights.yaml
                                  # GDPR Chapter III inbound anchors —
                                  # gdpr:art-15-access,
                                  # gdpr:art-16-rectification,
                                  # gdpr:art-17-erasure,
                                  # gdpr:art-18-restriction,
                                  # gdpr:art-20-portability,
                                  # gdpr:art-21-objection
                                  # (Art. 22 folded into the objection
                                  # entry per the classifier axis)
```

The CACAO source is canonical. The seven-step lifecycle (one
`start`, seven `action` steps, one `end`) is the deterministic
policy the playbook *means*. The three worked examples under
`examples/{n8n,temporal,langgraph}/data_subject_rights/` are the
same playbook compiled into three orchestrator idioms.

## 3. CACAO topology

The workflow is a linear seven-step lifecycle. Each action step
carries the CACAO I/O contract (`in_args` / `out_args`) plus
`x_secops_ng` reference bundles pinning the OSCAL control anchor,
D3FEND technique, and OCSF telemetry class the step emits.

| Step suffix | Step                          | Discipline                                                                                                                        | Status         |
|-------------|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|----------------|
| `…000001`   | dsr_start                     | edge wiring only — no body                                                                                                        | n/a            |
| `…000002`   | receive_request               | receive the DSR through the controller's intake surface; stamp `__case_id__`, `__request_received_ts__`, `__subject_contact__`    | adapter-bound  |
| `…000003`   | verify_identity               | verify the requesting party is the data subject; sovereign IdP integration point; sets `__identity_verified__`                    | adapter-bound  |
| `…000004`   | classify_request              | resolve `__request_type__` (access / rectification / erasure / restriction / portability / objection / Art. 22 concern); compute `__response_deadline__` from `__request_received_ts__ + 1 month` (Art. 12(3)); record any two-month extension | adapter-bound  |
| `…000005`   | route_to_data_owners          | resolve the per-owner manifest against the controller's declared data inventory; sets `__data_owner_manifest__`                   | adapter-bound  |
| `…000006`   | compile_fulfilment_evidence   | assemble the per-request fulfilment pack (subject-copy, rectification attestation, deletion attestation, restriction markers, structured data package, objection cessation record); sets `__fulfilment_pack_ref__` | adapter-bound  |
| `…000007`   | send_controller_response      | emit the response envelope on or before `__response_deadline__` under the Art. 12 modalities                                      | adapter-bound  |
| `…000008`   | record_outcome                | close the case with `__outcome_code__` for the Art. 5(2) accountability posture                                                   | adapter-bound  |
| `…00000a`   | dsr_end                       | edge wiring only — no body                                                                                                        | n/a            |

> The playbook maturity is `experimental` on the workflow-local
> content marker. This is a SKELETON: the topology, the variable
> contract, and the Article 12(3) response-window anchor are
> landed; the subject-verification adapter, the per-data-store
> owner-routing catalogue, and the outbound response templates
> are placeholders that a sibling CORE card lands.

## 4. Playbook variables

The playbook operates on a small set of workflow-scope variables.
Three are stamped by intake; the rest are set by the downstream
steps as the case progresses:

| Variable                       | External? | Set by                          | Purpose                                                                                                     |
|--------------------------------|-----------|---------------------------------|-------------------------------------------------------------------------------------------------------------|
| `__case_id__`                  | yes       | `receive_request`               | correlation key across the seven steps and against the operator's evidence store                            |
| `__request_received_ts__`      | yes       | `receive_request`               | ISO 8601 timestamp of intake — the **anchor** for the Article 12(3) response-deadline clock                 |
| `__subject_contact__`          | yes       | `receive_request`               | subject-facing envelope destination (`send_controller_response` reads this)                                 |
| `__identity_verified__`        | no        | `verify_identity`               | pass / fail on the sovereign IdP assertion (or on the out-of-band verification playbook for non-account subjects) |
| `__request_type__`             | no        | `classify_request`              | one of `access` / `rectification` / `erasure` / `restriction` / `portability` / `objection` / `art22_concern` |
| `__response_deadline__`        | no        | `classify_request`              | `__request_received_ts__ + 1 month` (Art. 12(3)), extendable by two months on complexity                    |
| `__data_owner_manifest__`      | no        | `route_to_data_owners`          | per-owner envelope catalogue resolved against the controller's data-inventory surface                       |
| `__fulfilment_pack_ref__`      | no        | `compile_fulfilment_evidence`   | opaque reference to the assembled fulfilment pack in the operator's evidence store                          |
| `__outcome_code__`             | no        | `record_outcome`                | closed-set outcome (`fulfilled` / `partially_fulfilled` / `refused_with_remedy` / `withdrawn`) for the Art. 5(2) posture |

The response-deadline handling is the invariant that pins
correctness of the whole lifecycle: **`__response_deadline__` is
derived from `__request_received_ts__`, not from any
emitter-clock or worker-local wall-clock read**. See § 8.

## 5. Sovereign IdP integration point

The `verify_identity` step is the framework's authoritative
integration point for the operator's sovereign identity substrate.
The step exists to bind the DSR request to the identity of the
requesting subject on a surface that discharges the OSCAL
AC-2(11) usage-conditions anchor (see § 6) *before* any personal
data flows out of `compile_fulfilment_evidence`.

Two verification lanes ship as adapter-bound surfaces:

- **IdP-bound assertion (account-holders).** The operator's
  declared subject-verification surface is a sovereign IdP under
  the sovereignty-first foundation (see
  [`docs/FOUNDATION.md`](../FOUNDATION.md)). The default binding
  on the SecOps-NG substrate is an EU-resident IdP the operator
  runs on their own sovereign cloud, EU-region KMS, and EU-issued
  identity assertions. The `verify_identity` adapter accepts an
  IdP-bound assertion (SAML / OIDC as the operator's substrate
  admits) and writes `__identity_verified__ = pass` on a valid
  assertion whose subject claim matches the DSR request's
  `__subject_contact__`.

- **Out-of-band verification playbook (non-account subjects).**
  For DSR requests from subjects who do not hold an account with
  the controller (marketing-list subject, contract-processor
  case, historic-collection subject), the adapter delegates to
  the operator's out-of-band verification playbook (recognised
  identity-document check, shared-secret against the channel of
  record, call-back to a channel of record). The out-of-band
  lane is symmetric to the IdP lane on the CACAO contract — it
  returns `__identity_verified__ = pass` or `= fail` — but its
  concrete steps sit with the operator.

The framework ships **no default identity substrate**, no
default credential material, and no substitute for a failed
verification. Failed verification exits the workflow on
`send_controller_response` with a refusal-with-remedy envelope
per Article 12(6) — the request is registered, the refusal is
audit-evident on `record_outcome`, and the subject is directed
to the operator's supervisory-authority complaint address
(Article 77) and judicial-remedy address (Article 79).

## 6. Regulatory anchors

**GDPR Chapter III — Articles 15–22 and Article 12(3).** The
regulation prescribes the seven operational rights the workflow
discharges and the response window that anchors the deadline.
Inbound anchors live at
[`content/mappings/gdpr/article-15-22-data-subject-rights.yaml`](../../content/mappings/gdpr/article-15-22-data-subject-rights.yaml)
under the mapping ids `gdpr:art-15-access`, `gdpr:art-16-rectification`,
`gdpr:art-17-erasure`, `gdpr:art-18-restriction`,
`gdpr:art-20-portability`, and `gdpr:art-21-objection`. Article 22
folds into the objection entry per the workflow's classifier axis.
Each backlinks `playbook.data_subject_rights@v1`.

**EDPB Guidelines 01/2022 on data subject rights — right of
access.** The guidelines frame the operator-facing expectations
for Article 15 (subject-copy assembly modalities, information
requirements under Art. 15(1)(a)–(h), and the interaction with
Art. 15(3) provision-of-copy). The `compile_fulfilment_evidence`
adapter for the access lane pins the guidelines as the reference
shape for the assembled subject-copy pack.

**OSCAL controls** — from
[`content/playbooks/data_subject_rights/mappings.yaml`](../../content/playbooks/data_subject_rights/mappings.yaml):

- **AC-2(11)** — *Account Management — Usage Conditions*, anchored
  on `verify_identity`. Binding the DSR request to the requesting
  subject on the operator's declared subject-verification surface
  (sovereign IdP for account-holders; out-of-band playbook for
  non-account subjects) is the access-enforcement leg the workflow
  discharges before any personal data is compiled into the
  response envelope.
- **AU-9** — *Protection of Audit Information*, anchored on
  `record_outcome`. The per-case correlation record the workflow
  persists (case id, response-deadline delta, per-owner
  fulfilment audit trail, outcome code) is the audit-information
  surface that discharges the operator's Article 5(2)
  accountability posture and any downstream Article 58(1)(a)
  supervisory-authority information order.

**MITRE D3FEND v1.0.0** — `D3-IAA` *Identity Access Assurance* is
selected on `verify_identity` as the closest-fitting defensive
technique for the sovereign-IdP assertion. The remaining six
steps carry no D3FEND technique: the workflow is a discharge
discipline for a subject-initiated obligation, not a runtime
countermeasure against an adversary behaviour, and the closest
fit is the identity-access assurance at the gate.

**OCSF v1.3.0** — one class binding.
`Compliance Finding` (class_uid 2003, category Findings),
direction `emits`, is emitted by `send_controller_response` and
`record_outcome` as the structured per-case record the
compliance layer routes on. One Compliance Finding per emitted
response envelope, keyed to `__case_id__`, so the
incident-timeline-signals control can audit on-time delivery
against the Article 12(3) response deadline.

## 7. Per-target hand-off

### 7.1 n8n — Set nodes over the seven-step lifecycle

`examples/n8n/data_subject_rights/workflow.n8n.json` carries the
CACAO topology as n8n nodes (one `manualTrigger`, one `set` node
per action, one `noOp` terminal). Node ids preserve the CACAO
step ids verbatim. Each action node emits a `n8n-nodes-base.set`
carrying the CACAO I/O contract as editable assignment rows plus
the `x_secops_ng` reference bundles.

Operators bind the Set rows to their connectors:

- `receive_request` → the controller's intake surface (webhook
  from the subject-facing portal, IMAP node against the privacy
  address, paper-channel scanner ingest); writes `__case_id__`,
  `__request_received_ts__`, `__subject_contact__`.
- `verify_identity` → the sovereign IdP integration point (HTTP
  Request node against the operator's IdP substrate; or a Subflow
  invocation of the out-of-band verification playbook); writes
  `__identity_verified__`.
- `classify_request` → the classifier surface (Function node with
  the closed request-type set, or a Set node when classification
  is exposed on the intake surface); writes `__request_type__`
  and `__response_deadline__`.
- `route_to_data_owners` → the operator's data-inventory
  connector (HTTP Request against the inventory API, or a
  Postgres node against the data-inventory table); writes
  `__data_owner_manifest__`.
- `compile_fulfilment_evidence` → the evidence-pack assembler
  (Function node materialising the per-lane pack against
  operator-owned templates); writes `__fulfilment_pack_ref__`.
- `send_controller_response` → the outbound-envelope connector
  (Send Email node, subject-portal HTTP Request, or paper-mail
  print-and-mail queue). Reads `__response_deadline__` and
  refuses to emit past-deadline without an audit-evident
  extension record.
- `record_outcome` → the evidence-store connector (Postgres,
  S3-compatible object store, or evidence-ledger HTTP Request);
  writes `__outcome_code__`.

To regenerate the compiled workflow artifact from the repo root:

```sh
./examples/n8n/data_subject_rights/regenerate.sh
```

The script mirrors the canonical CACAO YAML into a
byte-deterministic JSON form and then emits `workflow.n8n.json`
via the unified `tools.compile` CLI. The byte-parity golden test
under `tests/examples/n8n/data_subject_rights/test_golden.py`
reruns the same pipeline and fails if the committed artifact
drifts.

### 7.2 Temporal — activities over the seven-step lifecycle

`examples/temporal/data_subject_rights/workflow.temporal.py`
carries the CACAO topology as a Temporal workflow with one
activity per action step. The workflow signature threads
`request_received_ts` through as an argument — the Article 12(3)
deadline is derived from that external playbook-scoped input
rather than from `datetime.utcnow()` at the worker's current
wall-clock. A worker restart mid-workflow re-hydrates the same
deadline against Temporal's event-history replay contract.

Operators bind the activity bodies to real connectors:

- `receive_request` — the intake-surface activity; writes the
  three intake variables.
- `verify_identity` — the sovereign IdP activity; the reference
  binding is an HTTP call against the operator's EU-resident IdP.
  Non-account subjects trigger a nested workflow (the operator's
  out-of-band verification playbook), not a nested activity, so
  the out-of-band lane inherits Temporal's replay contract.
- `classify_request` — the classifier activity; the reference
  binding computes `__response_deadline__` as
  `__request_received_ts__ + 1 month` (Art. 12(3)) with
  `dateutil.relativedelta` so month-boundary arithmetic is
  calendar-correct.
- `route_to_data_owners` — the inventory-join activity.
- `compile_fulfilment_evidence` — the evidence-pack activity.
- `send_controller_response` — the outbound-envelope activity.
- `record_outcome` — the evidence-store activity.

To regenerate the compiled artifact from the repo root:

```sh
./examples/temporal/data_subject_rights/regenerate.sh
```

The byte-parity golden test under
`tests/examples/temporal/data_subject_rights/test_golden.py`
reruns the emitter and fails if the committed artifact drifts.

### 7.3 LangGraph — nodes and state over the seven-step lifecycle

`examples/langgraph/data_subject_rights/graph_spec.json` carries
the CACAO topology as a target-neutral GraphSpec (nodes, edges);
`state_bindings.py` emits the `TypedDict` state and the
`@tool`-decorated action wrappers plus the agentic-extension hook.
The Article 12(3) deadline is expressed as a node-local derivation
from `request_received_ts` threaded through state — never from
`time.time()` or `datetime.utcnow()` inside the node body.

The audit-mirror sibling `_audit_mirror.py` (see
[`docs/observability/audit-mirror.md`](../observability/audit-mirror.md))
carries the OTel-free durable audit trail on LangGraph runs where
the operator has not wired an OTLP collector.

Operators bind the tool bodies to real connectors:

- `receive_request` → intake surface tool.
- `verify_identity` → sovereign IdP tool + optional
  agentic-extension hook (the agentic-extension surface is where
  the operator's LangGraph agent can pause the graph on a
  non-account-holder subject and route to the out-of-band
  verification playbook).
- `classify_request`, `route_to_data_owners`,
  `compile_fulfilment_evidence`, `send_controller_response`,
  `record_outcome` — one tool per step against the operator's
  substrate.

To regenerate the compiled artifacts from the repo root:

```sh
./examples/langgraph/data_subject_rights/regenerate.sh
```

## 8. Response-deadline handling — the G-03 restart-drift invariant

The Article 12(3) one-month response window is the single
correctness-critical clock in the workflow, and it is
**derived from `__request_received_ts__` — never from any
emitter-side or worker-side clock read**.

Concretely, across the three targets:

- **n8n** — the `classify_request` Set node reads
  `__request_received_ts__` from the workflow state; downstream
  nodes MUST NOT reach for `$now` / `Date.now()` when computing
  the deadline.
- **Temporal** — the workflow signature threads
  `request_received_ts` through as an activity argument;
  activities MUST NOT read `datetime.utcnow()` for the deadline.
- **LangGraph** — the TypedDict state carries
  `request_received_ts`; node bodies MUST NOT read
  `time.time()` for the deadline.

The invariant is asserted across all three targets by
`tests/patterns/data_subject_rights/test_response_deadline_restart_drift.py`.
The test injects a synthetic `__request_received_ts__`, restarts
the worker mid-workflow (simulated in n8n via re-execution from
the same trigger record; in Temporal via history replay; in
LangGraph via checkpoint reload), and asserts the recomputed
deadline is byte-identical to the pre-restart deadline.

The reason for the external anchor is regulatory, not stylistic.
Article 12(3) declares the response window from the moment the
request is *received*, not from the moment the workflow *reaches
the deadline computation*. A worker restart that shifts the
deadline is a compliance drift — the framework refuses that shape
by construction.

## 9. Playbook chain — where data_subject_rights sits

The DSR lifecycle interacts with three neighbouring playbooks on
the operator's substrate. The interactions are documented at the
CACAO source but are worth calling out in a cookbook context so a
reader can situate the workflow:

- **`incident_management` / `data_exfil`** — the personal-data-breach
  notification lifecycle (GDPR Art. 33 / Art. 34) is
  *controller-initiated* on a breach event. The DSR lifecycle is
  *subject-initiated* against already-collected data. A DSR
  request that surfaces a personal-data breach the controller
  had not yet detected triggers a lateral hand-off to
  `incident_management`; that hand-off is a controller-side
  decision documented in the operator's DSR policy, not a
  branch in the DSR workflow itself.
- **`iam_auditor`** — the DSR lifecycle reads the operator's
  declared subject-verification surface; `iam_auditor` audits
  the health of that surface on a periodic cadence. A failing
  `iam_auditor` posture is a leading indicator that
  `verify_identity` will refuse assertions across the fleet;
  the two playbooks share the sovereign IdP integration point
  by contract.
- **`contractual_obligations_tracker`** — DSR requests that
  fall on data held by a controller's processor (Art. 28) are
  routed to the processor via the DPA-obligation surface the
  `contractual_obligations_tracker` playbook maintains. The
  processor-side response feeds back into
  `compile_fulfilment_evidence` on the controller-side DSR
  workflow.

## 10. What this cookbook deliberately does not cover

- **The intake-surface UX.** The subject-facing portal shape, the
  privacy-policy contact address, and the paper-channel intake
  are operator decisions on the controller's user-facing
  substrate. The framework describes the CACAO contract the
  intake surface writes into; it does not ship the surface.
- **The subject-verification adapter body.** The SecOps-NG
  substrate defaults to a sovereign EU-resident IdP; the
  concrete IdP product, its EU-region KMS, its EU-issued
  assertions, and the out-of-band verification playbook for
  non-account subjects are operator-owned and sit behind the
  `verify_identity` adapter.
- **The data-inventory join key.** `route_to_data_owners`
  resolves against the controller's declared data-inventory
  surface; the join key, the inventory schema, and the per-owner
  routing catalogue are operator-owned.
- **The response-envelope templates.** The portability
  data-package format (structured, commonly-used,
  machine-readable per Art. 20(1)), the erasure-attestation
  letter, the rectification confirmation, the access-copy
  assembly, and the refusal-with-remedy template are
  operator-owned. A sibling CORE card lands reference templates
  a controller can adopt or override.
- **The Art. 22 automated-decision review itself.** Article 22
  concerns are classified at `classify_request` and routed to
  the controller's human-in-the-loop review surface as part of
  the objection lane. The review of the underlying automated
  decision sits with the controller, not with this workflow.

## 11. References

- OASIS CACAO v2.0 specification.
- General Data Protection Regulation (EU) 2016/679 —
  Chapter III (Articles 12–22) and Article 5(2).
- EDPB Guidelines 01/2022 on data subject rights — right of
  access.
- NIST SP 800-53 Rev. 5 — AC-2(11) Usage Conditions, AU-9
  Protection of Audit Information.
- MITRE D3FEND v1.0.0 — D3-IAA Identity Access Assurance.
- OCSF v1.3.0 — Compliance Finding (class_uid 2003) event class.
