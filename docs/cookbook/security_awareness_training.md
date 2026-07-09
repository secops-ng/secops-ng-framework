# security_awareness_training — cookbook walkthrough

Programme-lifecycle governance for the structured security-awareness
training required by NIS2 Article 21(2)(g), with GDPR Article 32(1)(b)
staff-training organisational-measures and ISO/IEC 27001 Annex A.6.3
information-security awareness, education, and training as sibling
anchors. The `playbook.security_awareness_training@v1` CACAO playbook
operates the annual and quarterly programme-authoring cycle upstream of
the reactive phishing and per-cohort hygiene disciplines: it schedules
the training-needs assessment against the in-scope programme scope,
authors or updates the per-track curriculum, publishes delivery-intent
records to the operator's learning-management surface, reads per-staff
completion state and rolls up to per-cohort aggregate, composes the
residual-gap report for the programme owner, and closes the cycle with
a dated cycle-review artifact that references the assessment,
curriculum, delivery, completion, and gap-report records.

## 1. When to use `security_awareness_training` vs `cyber_hygiene_training`

Both playbooks sit under NIS2 Art. 21(2)(g). They discharge distinct
halves of the clause and are meant to be run together:

| Concern | `security_awareness_training` (this playbook) | `cyber_hygiene_training` |
|---|---|---|
| Cadence | Annual / quarterly programme cycle | Per-cohort operational cycle |
| Question answered | *What* training must the programme require? | *Who* got trained this cycle, and did they finish? |
| Surface | Assessment, curriculum authoring, delivery-intent, cycle-review governance | Roster inventory, cycle assignment, phishing simulation, completion tracking, dated attestation |
| Layer | Programme governance | Per-cycle operational execution |
| Audit reader | Programme owner / NIS2 competent-authority reviewer looking for the *documented programme* | Programme owner / auditor looking for per-cycle *evidence of discharge* |
| Personal-data surface | Cohort aggregates + curriculum metadata | Per-staff identifiers, per-recipient simulation click / report |
| GDPR data-flow companion | Read-only against HR / identity / LMS aggregates | `content/mappings/gdpr/data-flow-cyber_hygiene_training.md` (full ROPA) |

The two playbooks are complementary siblings under the same clause:
this one authors the training programme the operator's programme owner
declares; `cyber_hygiene_training` discharges the operational per-cycle
execution against that programme. `phishing_triage` is the third
sibling — the reactive incident-response lane when a real phishing
attempt lands on live mailflow.

```
security_awareness_training  (annual / quarterly programme governance)
   └── schedule assessment ─► design content ─► deliver training
       ─► record completion ─► report gaps ─► review cycle
                                │
                                ▼
cyber_hygiene_training       (per-cohort operational execution)
   └── inventory roster ─► schedule cycle ─► run simulation
       ─► track completion ─► attest ─► notify gaps
                                │
                                ▼
phishing_triage              (reactive on live incident)
   └── triage suspicious email ─► contain ─► notify affected users
```

Cookbook cross-reference:
[`cyber_hygiene_training.md`](cyber_hygiene_training.md).

## 2. Source of truth

```
content/playbooks/security_awareness_training/
├── README.md              # workflow-local overview and status
├── mappings.yaml          # outbound OSCAL / OCSF / NIS2 / GDPR overlay
└── playbook.cacao.json    # canonical CACAO v2 source
                           # (playbook.security_awareness_training@v1)

content/mappings/nis2/article-21-2-g.yaml
                           # NIS2 Art. 21(2)(g) inbound anchor —
                           # basic cyber-hygiene practices and
                           # cybersecurity training for staff
content/mappings/gdpr/article-32-security-of-processing.yaml
                           # GDPR Art. 32(1)(b) inbound anchor —
                           # organisational measures for security
                           # of processing (staff-training limb)
```

The CACAO source is canonical. The six action steps plus one `start`
and one `end` node are the deterministic programme-governance policy
the playbook *means* — a linear
assessment → curriculum → delivery → completion → gap-report →
cycle-review chain with no conditional branching at the workflow
layer.

The compile-target worked examples for the per-cohort operational
delivery live under
[`examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`](../../examples).
This is intentional: the programme-governance scope
(`security_awareness_training`) and the operational-delivery scope
(`cyber_hygiene_training`) share compile examples so the same NIS2
Art. 21(2)(g) surface is not forked across two synonymous rings. § 4
below shows how to wire the programme-governance layer to those
examples for end-to-end coverage.

## 3. CACAO topology and control binding

The playbook ships eight steps: one `start`, six `action`, and one
`end`. The topology is a linear
assessment → curriculum → delivery → completion → report-gaps →
review-cycle chain. There is no conditional branching at the workflow
layer; residual-gap classification lives inside the report-gaps step's
output artifact.

Read-only and side-effect-free against operator infrastructure:
- assessment reads HR / identity / policy surfaces to resolve required
  tracks per cohort;
- delivery writes *delivery-intent* records to the learning-management
  surface — the LMS owns final scheduling and per-staff dispatch;
- completion reads per-staff state from the LMS and does not mark
  completion on the operator's behalf.

Each action step carries a CACAO I/O contract (`in_args` / `out_args`)
and an `x_secops_ng.control_refs` binding. The step-to-control map is:

| Step suffix | Step | `x_secops_ng.control_refs` | OSCAL anchor | Regulatory anchor |
|---|---|---|---|---|
| `…000001` | `security_awareness_training_start` | — | — | — |
| `…000002` | schedule assessment | `control.training_needs_assessment@v1` | NIST SP 800-53 Rev. 5 **AT-2** — Literacy Training and Awareness | NIS2 Art. 21(2)(g); GDPR Art. 32(1)(b) |
| `…000003` | design content | `control.training_curriculum@v1` | ISO/IEC 27001:2022 Annex **A.6.3** — Information security awareness, education and training | NIS2 Art. 21(2)(g); ISO 27001 A.6.3 |
| `…000004` | deliver training | `control.training_delivery@v1` | NIST SP 800-53 Rev. 5 **AT-3** — Role-based Training | NIS2 Art. 21(2)(g) |
| `…000005` | record completion | `control.training_records@v1` | NIST SP 800-53 Rev. 5 **AT-4** — Training Records | NIS2 Art. 21(2)(g); GDPR Art. 32(1)(b) |
| `…000006` | report gaps | `control.training_records@v1` | NIST SP 800-53 Rev. 5 **AT-4** — Training Records | NIS2 Art. 21(2)(g) |
| `…000007` | review cycle | `control.training_records@v1` | NIST SP 800-53 Rev. 5 **AT-4** — Training Records | NIS2 Art. 21(2)(g); ISO 27001 A.6.3 |
| `…000008` | `security_awareness_training_end` | — | — | — |

The AT-4 anchor is shared with `cyber_hygiene_training` — the two
playbooks discharge the programme and operational-execution halves of
the same training-records obligation.

The playbook maturity is `experimental` on the workflow-local content
marker. The mappings overlay pins the control surface (OSCAL AT-2 /
AT-3 / AT-4 plus ISO/IEC 27001 A.6.3) and holds a SKELETON placeholder
for the D3FEND and OCSF slices until the CORE-layer defensibility and
telemetry analyses land — see the `todo: true` markers on
[`mappings.yaml`](../../content/playbooks/security_awareness_training/mappings.yaml).

## 4. Wiring the programme-governance layer to per-cohort operational delivery

The programme-lifecycle cycle emits five internal artifact identifiers
plus one closing cycle-review record:

- `__assessment_id__` — per-cohort record of (cohort id, required
  tracks, identified gaps, regulatory drivers, priority).
- `__curriculum_id__` — per-track record of (track id, module ids,
  learning objectives, source citation, review date).
- `__delivery_id__` — per-cohort delivery-intent record (cohort id,
  delivery channel, delivered-at, target audience count).
- `__completion_id__` — per-staff record rolled up to per-cohort
  aggregate.
- `__gap_report_id__` — residual-gap summary the programme owner reads
  at cycle close.
- `__cycle_review_id__` — dated cycle-review record referencing the
  five upstream artifacts plus programme-level recommendations for the
  next cycle.

The two inputs to a cycle are `__training_window__` (ISO 8601
interval) and `__training_scope__` (identifier of the in-scope
programme surface).

End-to-end coverage is achieved by feeding the programme-governance
outputs into the per-cohort operational cycle:

```
security_awareness_training  (programme cycle: annual / quarterly)
   assessment ─► curriculum ─► delivery-intent (per cohort)
                                      │
                                      ▼           per-cohort operational cycle
                             cyber_hygiene_training
                             (roster inventory + cycle assignment
                              + phishing simulation + tracking
                              + attestation + notify)
                                      │
                                      ▼
   completion ◄── (LMS-of-record) ◄──┘
   ─► report gaps ─► review cycle
```

Concretely:

1. **Programme cycle opens.** Operator scheduler triggers
   `playbook.security_awareness_training@v1` at the declared cadence
   (annual full-cycle, quarterly refresh). `__training_scope__`
   resolves the in-scope cohorts and mandatory / role-based tracks.
2. **Curriculum authored, delivery-intent published.** The
   `design content` step lands `__curriculum_id__`; the
   `deliver training` step writes delivery-intent records to the
   learning-management surface. Delivery-intent is the hand-off
   contract to the operational cycle — it declares *what* is due, not
   *when* individual staff are assigned.
3. **Per-cohort operational cycle runs.** For each declared cohort in
   the programme scope, the operator runs
   `playbook.cyber_hygiene_training@v1` — the per-cohort operational
   materialisation — against the LMS the delivery-intent record points
   at. That playbook is reference-compiled against three orchestrator
   idioms under
   `examples/{n8n,temporal,langgraph}/cyber_hygiene_training/` with
   byte-parity goldens under
   `tests/examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`.
   Walkthrough: [`cyber_hygiene_training.md`](cyber_hygiene_training.md).
4. **Programme cycle closes.** The programme playbook resumes on its
   `record completion` → `report gaps` → `review cycle` tail against
   the LMS aggregate the operational cycle produced. The cycle-review
   artifact is the audit-evident programme-governance record NIS2 Art.
   21(2)(g) reviewers read against the operator's declared training
   policy.

The compile-target byte-parity goldens under
`tests/examples/{n8n,temporal,langgraph}/cyber_hygiene_training/`
guard the operational-delivery ring on every PR. The programme
playbook itself is portable CACAO source with no operator-bound
runtime dependency — an operator can drive it from whichever
orchestrator (or manual programme calendar) already carries their
governance surface.

> The framework is framework-agnostic by construction. n8n / Temporal
> / LangGraph are three of three reference targets; the same CACAO
> source compiles into all of them. Operators run whichever target
> already lives in their stack.

## 5. Regulatory-graph closure

The programme-governance playbook contributes to NIS2 Art. 21(2)(g)
graph closure at the *programme* end of the clause. Companion inbound
anchors are wired in the mappings overlay:

- **NIS2 Art. 21(2)(g)** — primary anchor. The inbound entry at
  `content/mappings/nis2/article-21-2-g.yaml` backlinks
  `playbook.security_awareness_training@v1` (programme governance),
  `playbook.cyber_hygiene_training@v1` (operational per-cohort
  execution), and `playbook.phishing_triage@v1` (reactive lane).
- **GDPR Art. 32(1)(b)** — sibling anchor. The staff-training
  organisational-measures reading is a well-established EDPB / CJEU
  interpretation of Art. 32(1)(b); the cycle-review artifact carries
  the programme-effectiveness evidence a data protection reviewer
  would read against.
- **ISO/IEC 27001 Annex A.6.3** — companion anchor. The curriculum-
  authoring surface is the direct A.6.3 discharge point; the
  cycle-review artifact carries the programme-effectiveness evidence.

DORA Art. 13(6) and CRA Art. 13(6) staff-cyber-hygiene / awareness
touchpoints are carried on `cyber_hygiene_training` — see that
overlay. The programme-lifecycle overlay stays scoped to NIS2 / GDPR /
ISO to avoid forking the sibling references.

## 6. What this cookbook deliberately does not cover

- **Credentials.** No LMS, HR, identity-source, or evidence-store
  endpoint or token belongs in the playbook or its compiled
  orchestrator artifacts. The operator wires each at the compile-
  target config layer.
- **Per-deployment topology.** Cadence (annual vs quarterly refresh),
  cohort taxonomy, and role-based-track catalogue are operator
  declarations that live in the operator's programme-scope catalogue,
  not in the playbook.
- **LMS-of-record choice.** The playbook is deliberately silent on
  which LMS the operator runs; the delivery-intent contract is the
  interoperability surface.
- **Programme-scope authoring.** *Which* cohorts, tracks, and
  regulatory drivers are in scope is the programme owner's declaration
  — the playbook operates against the scope catalogue it is handed,
  not against a framework-declared taxonomy.
