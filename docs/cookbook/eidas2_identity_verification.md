# eidas2_identity_verification — practitioner cookbook

Practitioner-facing walkthrough of the eIDAS 2.0 European Digital
Identity Wallet (EUDIW) identity-verification workflow: how the five
CACAO action steps in `playbook.eidas2_identity_verification@v1` land
in the operator's chosen compile target, what artifact each step
produces, and where the regulatory anchor lives in EU instruments.

The workflow is the eIDAS-2.0-native materialisation of the access-
management leg of NIS2 Article 21(2)(i) and the digital-identity-
governance leg of DORA Article 5(2)(a). On each onboarding event
against an EUDIW-enabled principal the workflow requests an EUDIW
presentation, cryptographically verifies the returned Person
Identification Data (PID) credential against the operator's declared
EU trust-anchor registry, maps the returned Level of Assurance to the
operator-side access tier, publishes a dated Account Change
(OCSF 3001) audit-evidence record, and hands off to the downstream
access-provisioning workflow.

> Framework-agnostic by construction. n8n, Temporal, and LangGraph
> are three reference compile targets; the same CACAO source compiles
> into all three. Practitioners run whichever target already lives in
> their stack.

## 1. Regulatory anchors

The workflow discharges obligations against three EU instruments.
Each anchor is pinned in the mapping graph so a change on the
content layer surfaces as a graph-visible edge on the regulatory
side.

- **eIDAS 2.0 — Regulation (EU) 2024/1183** amending Regulation (EU)
  No 910/2014 (European Digital Identity Framework). Article 5c pins
  the EUDIW presentation-request surface the
  `request_eudiw_presentation` step exercises. Full text on
  EUR-Lex: https://eur-lex.europa.eu/eli/reg/2024/1183/oj.
- **NIS2 — Directive (EU) 2022/2555**, Article 21(2)(i) (human
  resources security, access-control policies, and asset management).
  Inbound mapping entry: [`content/mappings/nis2/article-21-2-i.yaml`](../../content/mappings/nis2/article-21-2-i.yaml)
  (`nis2:art-21-2-i`).
- **DORA — Regulation (EU) 2022/2554**, Article 5(2)(a) (governance
  and organisation, digital-identity governance under the ICT
  risk-management framework). Inbound mapping entry:
  [`content/mappings/dora/article-5.yaml`](../../content/mappings/dora/article-5.yaml)
  (`dora:art-5-governance`).

The GDPR overlap lands on Article 32(1)(b) (ongoing confidentiality
and integrity of processing) via the access-management surface;
inbound anchor at
[`content/mappings/gdpr/article-32-security-of-processing.yaml`](../../content/mappings/gdpr/article-32-security-of-processing.yaml)
and the per-workflow data-flow at
[`content/mappings/gdpr/data-flow-eidas2_identity_verification.md`](../../content/mappings/gdpr/data-flow-eidas2_identity_verification.md).

## 2. Sovereign-stack note

The trust-anchor probe in `verify_pid_credential` resolves against
Member-State Trusted Lists and the List of Trusted Lists (LOTL)
aggregator per Commission Implementing Decision (EU) 2015/1505 as
maintained under eIDAS 2.0. **No non-EU trust anchor is assumed and
no Microsoft or Google EUDIW proxy surface is modelled** — the
wallet-side protocol is OpenID4VP / Architecture and Reference
Framework (ARF) v2 against the operator's own verifier. Downstream
provisioning routes into `playbook.onboarding_offboarding_tracker@v1`,
itself framed against EU-hostable orchestrators.

Compile targets in the reference set (n8n, Temporal, LangGraph) all
run on EU-resident compute (Nebul, OVHcloud, Scaleway, Hetzner).
Choice of compile target is orthogonal to the sovereign-stack
posture; a practitioner who runs a hosted commercial n8n or Temporal
Cloud instance shifts the sovereignty boundary and should record
that in their own data-flow entry.

## 3. Source of truth

```
content/playbooks/eidas2_identity_verification/
├── README.md                    # workflow-local module tree and status
├── playbook.cacao.json          # canonical CACAO v2 source
├── mappings.yaml                # outbound overlay (OSCAL, D3FEND, OCSF, NIS2, DORA)
└── cookbook.md                  # this file

examples/n8n/eidas2_identity_verification/
├── README.md
├── playbook.cacao.json          # byte-identical mirror of the canonical
├── workflow.n8n.json            # importable n8n workflow
└── regenerate.sh

examples/temporal/eidas2_identity_verification/
├── README.md
├── playbook.cacao.json          # byte-identical mirror
├── workflow.temporal.py         # @workflow.defn + one @activity.defn per action
└── regenerate.sh

examples/langgraph/eidas2_identity_verification/
├── README.md
├── playbook.cacao.json          # byte-identical mirror
├── graph_spec.json              # target-neutral node + edge description
├── state_bindings.py            # TypedDict state schema + @tool stubs
├── _audit_mirror.py             # per-step audit-mirror shim
└── regenerate.sh
```

The CACAO source is canonical. Each example directory carries a
byte-identical mirror of `playbook.cacao.json`; byte-parity is
enforced by golden tests under `tests/examples/`. If the canonical
source moves, `regenerate.sh` inside each example re-emits the
compiled artifact and the goldens re-lock.

## 4. Step-by-step walkthrough

The workflow ships seven steps: one `start`, five `action`, one
`end`. Deterministic transitions — each state has exactly one
`on_completion` successor. One onboarding event emits exactly one
identity-verification evidence record.

### Step 1 — `request_eudiw_presentation`

**What the operator does.** The workflow issues an EUDIW presentation
request to the principal identified by `__principal_id__` for the PID
credential set required by `__auth_scope__`. The request is scoped
against eIDAS 2.0 Art. 5c (presentation of electronic attestations
of attributes).

**Compile-target view.**

- *n8n* — the step maps to an HTTP Request node emitting the
  OpenID4VP presentation request against the verifier endpoint the
  practitioner has bound to `presentation_endpoint`. Import
  `examples/n8n/eidas2_identity_verification/workflow.n8n.json` into
  a running n8n and wire the credentials the node references.
- *Temporal* — the step compiles to
  `activity.request_eudiw_presentation` in
  `examples/temporal/eidas2_identity_verification/workflow.temporal.py`.
  The activity raises `NotImplementedError` at the SKELETON layer;
  the practitioner supplies the verifier-adapter body when wiring
  their own verifier deployment.
- *LangGraph* — the step is a `@tool`-decorated node in
  `state_bindings.py` with the same NotImplementedError contract;
  the graph spec in `graph_spec.json` records the immutable topology.

**Regulatory anchor.** eIDAS 2.0 Art. 5c (wallet presentation).

### Step 2 — `verify_pid_credential`

**What the operator does.** The workflow cryptographically verifies
the PID credential returned by the wallet: resolves the issuer to a
Member-State Trusted List entry (or to the LOTL aggregator per
Commission Implementing Decision (EU) 2015/1505), performs the
holder-binding check (`cnf` claim for SD-JWT VC, device binding for
mDoc per ARF v2), and resolves the credential status list. The step
is read-only against the wallet surface and against the trust-anchor
registry.

**Compile-target view.**

- *n8n* — HTTP Request node against the operator's declared trust-
  anchor probe, followed by a Code node that runs the holder-binding
  and status-list checks against the returned credential envelope.
- *Temporal* — `activity.verify_pid_credential`. The activity is the
  natural home for the trust-anchor cache (with a documented TTL)
  so repeat verifications against the same issuer inside a
  restart-window do not re-hit the trust-list endpoint.
- *LangGraph* — `@tool` node; the state schema carries the returned
  credential envelope on the input edge and the verification verdict
  on the output edge.

**Regulatory anchor.** eIDAS 2.0 Art. 5c and the Member-State
Trusted List surface maintained under Commission Implementing
Decision (EU) 2015/1505.

### Step 3 — `assess_assurance_level`

**What the operator does.** The workflow reads the Level of
Assurance (LoA) attribute on the verified PID credential — one of
`high`, `substantial`, or `low` per the eIDAS 2.0 assurance-level
matrix — and maps it to the operator-side access tier for
`__auth_scope__` per the operator's documented assurance-tier
mapping. An LoA the operator does not accept for the requested
scope is a terminal negative verdict at this step.

**Compile-target view.**

- *n8n* — a Switch node against the `loa_verdict` field routing
  onto the accept / reject branches.
- *Temporal* — `activity.assess_assurance_level` returning the
  mapped access tier or a documented `LoARejection` signal.
- *LangGraph* — `@tool` node returning the mapped tier on the state
  edge.

**Regulatory anchor.** eIDAS 2.0 Art. 8 (assurance levels) as read
through the operator's own access-tier mapping under NIS2
Art. 21(2)(i).

### Step 4 — `emit_identity_audit_evidence`

**What the operator does.** The workflow publishes the dated
identity-verification audit-evidence artifact to the operator's
evidence store as an OCSF Account Change (`class_uid 3001`) record.
The record pins `__principal_id__`, `__auth_scope__`,
`__presentation_request_id__`, `__pid_credential_id__`,
`__loa_verdict__`, `__access_tier__`, `__verification_verdict__`,
and `__captured_at__` so the NIS2 Art. 21(2)(i) auditable-lifecycle
obligation is discharged on every terminal path (including the
verification-failed branch).

**Compile-target view.** All three targets project the record into
the same shape; the difference is only in how the emitter is
invoked.

- *n8n* — HTTP Request node against the operator's evidence sink,
  carrying the JSON body below.
- *Temporal* — `activity.emit_identity_audit_evidence` invoking the
  shared emitter under `compilers/_shared/evidence/`.
- *LangGraph* — `@tool` node calling the same shared emitter.

**Regulatory anchor.** OCSF Account Change (`class_uid 3001`)
telemetry class carries the record; the audit-evident obligation is
NIS2 Art. 21(2)(i) and DORA Art. 5(2)(a).

### Step 5 — `trigger_access_provisioning`

**What the operator does.** The workflow hands the verified identity
off to the downstream access-provisioning workflow
(`playbook.onboarding_offboarding_tracker@v1`) so the joiner-side
capability delta is applied against `__auth_scope__`. The hand-off
carries the `evidence_id` of the record emitted in step 4 so the
downstream workflow can trace back to the verification transaction.

**Compile-target view.**

- *n8n* — Execute Workflow node invoking the onboarding tracker's
  compiled n8n workflow.
- *Temporal* — a child-workflow invocation of
  `OnboardingOffboardingTracker` via
  `workflow.start_child_workflow`.
- *LangGraph* — a graph-boundary handoff carrying the state
  envelope to the onboarding-tracker graph; the LangGraph reference
  emitter records the boundary in `graph_spec.json` as a terminal
  node whose downstream is the sibling graph.

**Regulatory anchor.** NIS2 Art. 21(2)(i) access-control policies
close on the joiner-side capability provisioning the downstream
workflow discharges.

## 5. Example evidence artifact shape

The record emitted in step 4 lands as an OCSF Account Change (class
`3001`, category `Identity & Access Management`) event. A sample
record is shown below; field names and enumerations follow OCSF
v1.4.0. All principal identifiers are documented as bounded
identifiers, never raw PID attributes (name, national identifier,
date-of-birth) — the record is an audit-evidence artifact, not a
PID copy.

```json
{
  "class_uid": 3001,
  "class_name": "Account Change",
  "category_uid": 3,
  "category_name": "Identity & Access Management",
  "activity_id": 1,
  "activity_name": "Create",
  "type_uid": 300101,
  "time": 1783590000000,
  "status_id": 1,
  "status": "Success",
  "actor": {
    "process": {
      "name": "playbook.eidas2_identity_verification@v1"
    }
  },
  "user": {
    "uid": "principal:0f8c2a4e-onboarding-2026-07",
    "type_id": 1,
    "type": "User"
  },
  "src_endpoint": {
    "uid": "verifier:eu-central/OpenID4VP"
  },
  "metadata": {
    "version": "1.4.0",
    "product": {
      "name": "eidas2_identity_verification",
      "vendor_name": "secops-ng"
    },
    "profiles": ["cloud"],
    "labels": [
      "eidas2:art-5c",
      "nis2:art-21-2-i",
      "dora:art-5-2-a"
    ]
  },
  "unmapped": {
    "auth_scope": "workspace:admin",
    "presentation_request_id": "pr-01HXXK...",
    "pid_credential_id": "sd-jwt-vc:01HXXK...",
    "loa_verdict": "high",
    "access_tier": "tier-2",
    "verification_verdict": "verified",
    "evidence_id": "evi:01HXXK...",
    "captured_at": "2026-07-09T09:40:00Z",
    "trust_anchor": "lotl:eu/DE/BSI"
  }
}
```

The `unmapped` extension carries the eIDAS-2.0-native fields the
OCSF Account Change schema does not project natively; keeping them
under `unmapped` rather than co-opting existing OCSF fields
preserves cross-vendor readability of the record. The `labels`
array is the durable regulatory-anchor trail — a downstream evidence
reader can walk from the record back to the mapping YAMLs without
re-reading the CACAO source.

The `evidence_id` is the correlation handle the downstream
`onboarding_offboarding_tracker` hand-off in step 5 carries. On a
negative verdict (`verification_verdict: "rejected"` or
`status_id: 2 /* Failure */`) the record is still emitted — the
audit-evident discharge covers both terminal branches.

## 6. Running the worked examples

Each of the three example directories ships a `regenerate.sh` that
re-emits the compiled artifact from the canonical CACAO source. The
byte-parity golden tests under `tests/examples/` catch drift on
every PR.

- n8n: [`examples/n8n/eidas2_identity_verification/README.md`](../../examples/n8n/eidas2_identity_verification/README.md)
- Temporal: [`examples/temporal/eidas2_identity_verification/README.md`](../../examples/temporal/eidas2_identity_verification/README.md)
- LangGraph: [`examples/langgraph/eidas2_identity_verification/README.md`](../../examples/langgraph/eidas2_identity_verification/README.md)

The compiled artifacts are the starting point, not the finished
workflow: the primitive bodies (verifier adapter, trust-anchor
probe, LoA-to-tier mapping) are the practitioner's own to wire
against their identity plane. The framework holds the shape; the
practitioner holds the data plane.

## 7. Companion pattern

The [`patterns/eidas2_wallet/`](../../patterns/eidas2_wallet/)
typed-input pattern (F-SV-02) models the already-verified wallet
artifact a *downstream* workflow accepts as input. This playbook is
the content-layer complement: the operational discipline that
*produces* that verified artifact. The two are deliberately distinct
— the pattern is a compile-layer concern (a Pydantic input type),
the playbook is a content-layer concern (a CACAO workflow) — and the
CACAO artifact does not directly reference the Pydantic input type.
