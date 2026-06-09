# content/evidence/incidents/

Incidents evidence stream — the third stream in the SecOps-NG
**evidence** layer (after `risk-analysis/` and `vulns/`).

## What this stream is

An operator handling a significant incident under NIS2 Article 21(2)(b)
(incident-handling capability) and Article 23 (incident-notification
timeline) has to demonstrate, per incident, that detection-to-respond
arithmetic stays inside the catalog targets, that the
NIS2 Article 23(3) significance classification was decided
deterministically, and that the three Article 23(4) regulator-
notification milestones (early-warning 24h, incident-notification 72h,
final-report 1 month) were submitted on time. That demonstration takes
the shape of one per-execution artifact emitted every time the
`incident-management` playbook (F-WF-05) runs.

This directory is the contributor home for that stream. The artifact
shape is declared in
[`schemas/evidence/incidents.schema.json`](../../../schemas/evidence/incidents.schema.json);
the upstream workflow is
[`content/playbooks/incident-management/`](../../playbooks/incident-management/);
the indicators it feeds live under
[`content/metrics/`](../../metrics/) — `kpi.mttd@v1`, `kpi.mttr@v1`,
`kpi.mttr_critical@v1`, `kpi.mttr_containment@v1`,
`kpi.timeline_completeness@v1`, `kpi.notification_sla_compliance@v1`,
`kri.regulator_notification_overrun@v1`, plus the NIS2 Article 23
milestone KPIs (`kpi.early_warning_on_time@v1`,
`kpi.notification_72h_on_time@v1`, `kpi.final_report_on_time@v1`) once
they land in `content/metrics/`.

The stream is framework-agnostic. A reference emitter for each of the
three compile targets (n8n, Temporal, LangGraph) lands under
`compilers/` in the sibling CORE / SKELETON cards.

## Regulator hooks

| Regulation | Article          | Obligation paraphrase                                                                                                                | Mapping file                                                                       |
|------------|------------------|--------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| NIS2       | Art. 21(2)(b)    | Operate an incident-handling capability: detect, triage, contain, remediate, capture lessons learned.                                | [`content/mappings/nis2/article-21-2-b.yaml`](../../mappings/nis2/article-21-2-b.yaml) |
| NIS2       | Art. 23(4)(a)    | Early-warning notification within 24h of awareness of a significant incident.                                                        | [`content/mappings/nis2/article-23.yaml`](../../mappings/nis2/article-23.yaml)       |
| NIS2       | Art. 23(4)(b)    | Incident notification within 72h of awareness, with initial severity / impact / IoC assessment.                                      | [`content/mappings/nis2/article-23.yaml`](../../mappings/nis2/article-23.yaml)       |
| NIS2       | Art. 23(4)(d)    | Final report no later than one month after the incident notification.                                                                | [`content/mappings/nis2/article-23.yaml`](../../mappings/nis2/article-23.yaml)       |

## Artifact shape — pointer

Authoritative shape:
[`schemas/evidence/incidents.schema.json`](../../../schemas/evidence/incidents.schema.json).

At a glance, each artifact carries:

- `artifact_id` — deterministic SHA-256 of `<incident_id>|<execution_id>`.
- `incident_id` — UUID issued upstream by the F-WF-05 `timeline_open`
  primitive (`primitives/timeline_binding.open_timeline`). Groups every
  re-execution of the same incident across the lifecycle.
- `execution_id` — per-execution id issued by the compile target's
  runtime. Re-runs of the same incident_id produce distinct executions.
- `regulation_refs[]` — pin to every regulatory obligation the artifact
  satisfies (typically the NIS2 Article 21(2)(b) atom and the three
  Article 23 milestone atoms above).
- `control_refs[]` — control stable-ids attested by this artifact
  (typically `control.incident_handling_capability@v1` and/or
  `control.incident_timeline_signals@v1`).
- `classification` — F-WF-05 classify-significance verdict:
  `{ significant, cross_border, reasons[], rule_ids[], severity, summary }`.
  `rule_ids` pins behaviour against
  `content/playbooks/incident-management/primitives/classification_policy.yaml`
  so a replay-vs-original diff is a single-string check.
- `lifecycle` — `{ first_observation_at, detected_at, triaged_at,
  contained_at, eradicated_at, recovered_at, closed_at }`. Catalog KPIs
  read the interval pairs they need (MTTD = detected_at -
  first_observation_at; MTTR = contained_at - detected_at;
  containment_window = eradicated_at - contained_at;
  eradication_window = recovered_at - eradicated_at).
- `kpi_windows` — optional pre-computed minute counts the emitter may
  carry so downstream rollups skip re-derivation.
- `notification_timeline[]` — append-only list of NIS2 Article 23(4)
  milestones reached, each with `{ milestone, clock_started_at,
  submitted_at, submission_ref, on_time }`. Read by the per-milestone
  KPIs.
- `owner` — role-shaped ownership pointer with `assigned_at` date. No
  individual personal names.
- `captured_at` — ISO-8601 UTC timestamp.
- `provenance` — `{ source_url, captured_at, commit_sha }` mirror of
  the pattern used in `content/controls/`.
- `retention` — optional ISO-8601 duration retention pointer; the
  community-default value is an open question to be settled with the
  EXTEND-NIS2-MAPPING card.

## Promoted enums

The schema imports one shared vocabulary promoted alongside this
stream:

- [`schemas/nis2_incident_notification_milestone.json`](../../../schemas/nis2_incident_notification_milestone.json)
  — the three NIS2 Article 23(4) regulator-notification milestones
  (`early_warning_24h`, `incident_notification_72h`,
  `final_report_1mo`) the F-WF-05 regulator-submission stages run on.

The workflow-internal `StageName` alphabet
(`early_warning` / `notification` / `final_report`) maps onto this
schema-side enum 1:1 via the duration suffix; the schema carries the
duration so a regulator consuming an artifact sees the deadline
explicitly without having to cross-reference the stage table.

## Contributor checklist

If you are proposing a change that touches this stream:

1. The JSON Schema is the source of truth — change
   `schemas/evidence/incidents.schema.json` first, then update this
   README's at-a-glance summary if a field is added or removed.
2. The promoted enum above is intentionally small; extending it is a
   discussion, not a drive-by change.
3. The MTTD / MTTR / containment-window / eradication-window KPIs and
   the NIS2 Article 23 milestone KPIs live in `content/metrics/`; the
   stream wires emission, it does not re-declare the catalog entries
   here.
4. Run the content-model tests:

   ```sh
   python -m pytest tests/content_model/
   ```

5. Run the forward-public hygiene linter:

   ```sh
   python -m tools.hygiene_linter --min-severity LOW
   ```

6. Follow the
   [`AGENTS.md` §3 public-bar rules](../../../AGENTS.md): no commercial
   framing, no credentials, no internal infrastructure references, no
   individual lead names.

## Status

The stream's schema, the promoted NIS2 incident-notification milestone
enum, and the mapping-atom wires landed in F-CP-02 SCHEMA. The EMITTER
SKELETON card adds the framework-agnostic emitter
([`compilers/_shared/evidence/incidents.py`](../../../compilers/_shared/evidence/incidents.py))
and one wired compile target — the Temporal-side activity
([`compilers/temporal/evidence/incidents_activity.py`](../../../compilers/temporal/evidence/incidents_activity.py)) —
with an activity-level happy-path test
([`tests/content_model/test_incidents_evidence_emitter.py`](../../../tests/content_model/test_incidents_evidence_emitter.py)).
The per-target CORE-FANOUT (n8n / LangGraph), the byte-parity
goldens, the NIS2 Art. 21(2)(b) + Art. 23 mapping doc, and the
ROADMAP flip fan out into the remaining siblings of the F-CP-02 wave;
the pattern mirrors F-CP-01 and F-CP-04.
