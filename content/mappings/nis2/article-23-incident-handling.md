# NIS2 Article 23(4) — Incidents evidence schema

Companion narrative to the structural mapping in
[`article-23.yaml`](./article-23.yaml). This document explains how the
**incidents evidence stream** under
[`content/evidence/incidents/`](../../evidence/incidents/README.md)
discharges the NIS2 Article 23(4) regulator-notification timeline —
the three-milestone reporting chain (early-warning ≤24h,
incident-notification ≤72h, final-report ≤1 month) — how the schema is
referenced (not duplicated) here, and how the three reference compile
targets emit conformant artifacts.

This file is contributor-facing prose. The structural crosswalk
(`obligation`, `control_refs`, `metric_refs`, `evidence_stream_refs`)
remains the single source of truth in
[`article-23.yaml`](./article-23.yaml); change that file when the
mapping itself changes.

## Scope

- **In:** how the incidents evidence stream's artifact shape satisfies
  the three Article 23(4) regulator-notification milestones; pointers
  to the typed schema, to the per-target reference emitters, and to
  the existing cross-regime crosswalk anchors.
- **Out:** legal interpretation of Article 23(4); duplication of the
  schema body (the JSON Schema is canonical and must not be mirrored
  here); the Article 21(2)(b) incident-handling-capability half — that
  is the companion narrative under the Art. 21(2)(b) atom; the
  drift-detection surface for this stream — that ships in a separate
  sibling card mirroring the F-CP-01 drift hook; KPI/KRI emission
  wiring beyond the milestone KPIs already on the crosswalk.

## Schema — pointer, not copy

The incidents evidence artifact shape is declared once, in the typed
JSON Schema:

- **Authoritative schema:**
  [`schemas/evidence/incidents.schema.json`](../../../schemas/evidence/incidents.schema.json)
- **Contributor narrative (at-a-glance field summary):**
  [`content/evidence/incidents/README.md`](../../evidence/incidents/README.md)

The stream README is the human-facing entry point; the JSON Schema is
the machine-checkable contract. **Do not duplicate the schema body in
this file.** If a field name, type, or constraint changes, the schema
file is the source of truth and the stream README's at-a-glance summary
is updated alongside it; this mapping document only changes when the
*mapping* between the stream and the regulatory clause changes.

Shared vocabularies the schema imports:

- `nis2_incident_notification_milestone` enum —
  [`schemas/nis2_incident_notification_milestone.json`](../../../schemas/nis2_incident_notification_milestone.json) —
  the three Article 23(4) milestone names with their duration suffix
  (`early_warning_24h`, `incident_notification_72h`,
  `final_report_1mo`). The workflow-internal `StageName` alphabet in
  [`primitives/stage_clock.py`](../../playbooks/incident-management/primitives/stage_clock.py)
  (`early_warning` / `notification` / `final_report`) maps onto this
  enum 1:1 via the duration suffix.
- `provenance` shape — `{ source_url, captured_at, commit_sha }`,
  mirrored from `content/controls/`.

## §23(4) mapping — milestone → schema fields → workflow signals

NIS2 Article 23(4) requires entities in scope of Article 23 to submit,
to the CSIRT or competent authority, a three-step regulator-notification
chain on every significant incident: an **early-warning** without undue
delay and in any event within 24h of operator awareness; an **incident
notification** within 72h with an initial severity / impact / IoC
assessment; and a **final report** no later than one month after the
incident notification with the detailed description, root-cause
analysis, and applied mitigation. The wording of Article 23(4) itself
is in Directive (EU) 2022/2555 (CELEX 32022L2555); see
[`article-23.yaml`](./article-23.yaml) for the citation records on
each of the three atoms (`nis2:art-23-early-warning`,
`nis2:art-23-notification-72h`, `nis2:art-23-final-report`). Source
language is not copied into this repository.

The incidents evidence stream discharges the operational half of that
obligation by emitting, per execution of the `incident-management`
playbook (F-WF-05), a per-execution artifact that records *which
incident the operator is handling*, *what significance verdict fired
under what rule-ids*, *what point on the detect-to-recover lifecycle
the execution sits at*, and *which Article 23(4) milestones the
operator has reached, when each clock started, when the submission
went out, and whether it landed inside the regulator window*.

### Milestone → schema-field → workflow-signal crosswalk

The schema's `notification_timeline[]` is the carrier for every
Article 23(4) milestone the artifact attests. Each entry is
`{ milestone, clock_started_at, submitted_at, submission_ref,
on_time }`. The same three fields recur per milestone; what changes is
the regulator clock and the upstream workflow signal that pins
`clock_started_at`.

| Article 23(4) milestone | Schema enum value (`notification_timeline[].milestone`) | `clock_started_at` is pinned by | `submitted_at` is pinned by | `on_time` semantics | Downstream KPI / KRI |
|-------------------------|---------------------------------------------------------|---------------------------------|------------------------------|---------------------|----------------------|
| §23(4)(a) — early-warning, ≤24h from operator awareness | `early_warning_24h` | F-WF-05 `classify-significance` verdict on `lifecycle.detected_at` (operator-awareness anchor); rule-ids pinned in `classification.rule_ids[]`. | F-WF-05 `regulator-submission(early_warning)` stage success, recorded by [`primitives/regulator_submission.py`](../../playbooks/incident-management/primitives/regulator_submission.py). | `submitted_at − clock_started_at ≤ 24h`, evaluated by [`primitives/stage_clock.py`](../../playbooks/incident-management/primitives/stage_clock.py) on the `early_warning` stage. | `kpi.early_warning_on_time@v1`, `kri.early_warning_missed@v1`. |
| §23(4)(b) — incident notification, ≤72h from awareness | `incident_notification_72h` | Same operator-awareness anchor (`lifecycle.detected_at`); the 72h clock runs from the same `t0` as the 24h clock, not from the early-warning submission. | F-WF-05 `regulator-submission(notification)` stage success. | `submitted_at − clock_started_at ≤ 72h`, evaluated by `stage_clock.py` on the `notification` stage. | `kpi.notification_72h_on_time@v1`, `kpi.notification_sla_compliance@v1`, `kri.regulator_notification_overrun@v1`. |
| §23(4)(d) — final report, ≤1 month after the incident notification | `final_report_1mo` | The incident-notification submission timestamp on the prior `incident_notification_72h` entry (`submitted_at`); the 1-month clock runs from notification, not from awareness. | F-WF-05 `regulator-submission(final_report)` stage success. | `submitted_at − clock_started_at ≤ 30d`, evaluated by `stage_clock.py` on the `final_report` stage. An operator who prefers calendar-month arithmetic swaps the helper in their compile target's adapter; the schema carries the timestamps, not the interpretation. | `kpi.final_report_on_time@v1`, `kpi.review_completion_sla@v1`. |

The shared significance precondition — Article 23(4) only fires once
the incident has been classified `significant` under Article 23(3) —
is carried on the same artifact by `classification.significant` and
`classification.rule_ids[]`, so a reviewer follows the audit trail
from milestone-missed back to the rule-id that fired the clock, on
one artifact, without leaving the evidence stream.

The `submission_ref` field on each `notification_timeline[]` entry is
the operator-side regulator handle (the receipt-id the CSIRT or
competent authority returned). The framework does not prescribe its
shape — different national CSIRTs return different identifiers; the
schema pins the field as opaque-string so the audit trail survives
without forcing a vocabulary.

## How this is emitted

The shared emitter under
[`compilers/_shared/evidence/incidents.py`](../../../compilers/_shared/evidence/incidents.py)
assembles the artifact; each of the three reference compile targets
calls into the shared emitter and writes the same on-disk bytes.
Byte-parity is pinned per target by an immutable golden:

- **n8n** — adapter under
  [`compilers/n8n/evidence/incidents_node.py`](../../../compilers/n8n/evidence/incidents_node.py);
  per-target byte-parity golden at
  [`tests/examples/incidents_evidence/`](../../../tests/examples/incidents_evidence/)
  pinned against
  [`tests/fixtures/incidents_evidence/n8n.json`](../../../tests/fixtures/incidents_evidence/).
- **Temporal** — activity under
  [`compilers/temporal/evidence/incidents_activity.py`](../../../compilers/temporal/evidence/incidents_activity.py);
  same per-target test directory, pinned against
  [`tests/fixtures/incidents_evidence/temporal.json`](../../../tests/fixtures/incidents_evidence/).
- **LangGraph** — node wiring under
  [`compilers/langgraph/evidence/incidents_node.py`](../../../compilers/langgraph/evidence/incidents_node.py);
  same per-target test directory, pinned against
  [`tests/fixtures/incidents_evidence/langgraph.json`](../../../tests/fixtures/incidents_evidence/).

Cross-target round-trip equivalence (all three targets agree
byte-for-byte under one execution) is pinned by
[`tests/content_model/test_incidents_evidence_emitter.py`](../../../tests/content_model/test_incidents_evidence_emitter.py).
The per-target goldens are the EXTEND complement: a refactor of the
shared emitter that silently changes serialisation fails the test for
the specific target whose bytes drifted.

The targets are framework-agnostic by construction — each is one of
three, not the engine. An operator running a fourth compile target
implements the same shared-emitter interface and lands their own
per-target golden.

## Cross-regime alignment

The incidents evidence stream sits at the centre of the EU incident-
reporting cluster and the structural crosswalk already records the
anchors. **This mapping document does not extend the crosswalk** — it
only references what is already on disk:

- **NIS2 Article 21(2)(b)** — the incident-handling capability the
  Article 23(4) timeline runs on top of — is anchored at
  [`article-21-2-b.yaml`](./article-21-2-b.yaml); the companion
  narrative for that obligation is its own sibling mapping doc and
  shares this stream.
- **DORA Article 19** — major-ICT-related-incident reporting on
  financial entities — and the corresponding ITS reporting templates
  share the same three-milestone shape (initial / intermediate /
  final). The crosswalk anchor is on the DORA mapping side; the
  promoted milestone enum is reused without modification.
- **CRA Article 14** — manufacturer reporting on actively exploited
  vulnerabilities and severe incidents — runs its own clock vocabulary
  on the vulnerabilities evidence stream (`cra_timing_milestone`); the
  incidents stream does not carry CRA timings, and the two streams
  remain separate by design.

Extending the crosswalk — promoting per-field equivalence between
NIS2 Article 23(4) and DORA Article 19 into a typed overlap matrix —
is a follow-on sibling, not this card.

## See also

- [`article-23.yaml`](./article-23.yaml) — the structural mapping
  entries this document narrates.
- [`content/evidence/incidents/README.md`](../../evidence/incidents/README.md) —
  contributor home for the stream, with the at-a-glance field summary.
- [`schemas/evidence/incidents.schema.json`](../../../schemas/evidence/incidents.schema.json) —
  authoritative artifact shape.
- [`schemas/nis2_incident_notification_milestone.json`](../../../schemas/nis2_incident_notification_milestone.json) —
  the promoted three-milestone enum.
- [`ROADMAP.md` §F-CP-02](../../../ROADMAP.md) — feature definition and
  acceptance criteria.
