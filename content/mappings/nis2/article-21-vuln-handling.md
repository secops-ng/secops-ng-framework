# NIS2 Article 21(2)(e) — Vulnerabilities evidence schema

Companion narrative to the structural mapping in
[`article-21-2-e.yaml`](./article-21-2-e.yaml). This document explains
how the **vulnerabilities evidence stream** under
[`content/evidence/vulns/`](../../evidence/vulns/README.md) discharges
the NIS2 Article 21(2)(e) obligation on security in acquisition,
development and maintenance — specifically the vulnerability-handling
and coordinated-disclosure half plus the SBOM-production half — how
the schema is referenced (not duplicated) here, and how the three
reference compile targets emit conformant artifacts.

This file is contributor-facing prose. The structural crosswalk
(`obligation`, `control_refs`, `metric_refs`, `evidence_stream_refs`)
remains the single source of truth in
[`article-21-2-e.yaml`](./article-21-2-e.yaml); change that file when
the mapping itself changes.

## Scope

- **In:** how the vulnerabilities evidence stream's artifact shape
  satisfies the vulnerability-handling-and-disclosure obligation in
  NIS2 Article 21(2)(e); pointers to the typed schema, to the per-
  target reference emitters, and to the existing cross-regime
  crosswalk anchors.
- **Out:** legal interpretation of Article 21(2)(e); duplication of
  the schema body (the JSON Schema is canonical and must not be
  mirrored here); the drift-detection surface for this stream — that
  ships in a separate sibling card mirroring the F-CP-01 drift hook;
  KPI/KRI emission wiring from the stream — that is a separate
  follow-on as well.

## Schema — pointer, not copy

The vulnerabilities evidence artifact shape is declared once, in the
typed JSON Schema:

- **Authoritative schema:**
  [`schemas/evidence/vulns.schema.json`](../../../schemas/evidence/vulns.schema.json)
- **Contributor narrative (at-a-glance field summary):**
  [`content/evidence/vulns/README.md`](../../evidence/vulns/README.md)

The stream README is the human-facing entry point; the JSON Schema is
the machine-checkable contract. **Do not duplicate the schema body in
this file.** If a field name, type, or constraint changes, the schema
file is the source of truth and the stream README's at-a-glance summary
is updated alongside it; this mapping document only changes when the
*mapping* between the stream and the regulatory clause changes.

Shared vocabularies the schema imports:

- `cra_clock` kind — [`schemas/cra_clock_kind.json`](../../../schemas/cra_clock_kind.json).
- `cra_timing_milestone` — [`schemas/cra_timing_milestone.json`](../../../schemas/cra_timing_milestone.json).
- `vuln_response_band` — [`schemas/vuln_response_band.json`](../../../schemas/vuln_response_band.json).
- `provenance` shape — `{ source_url, captured_at, commit_sha }`,
  mirrored from `content/controls/`.

## §21(2)(e) mapping — vulnerabilities fields → vulnerability-handling obligation

NIS2 Article 21(2)(e) requires entities in scope to adopt measures
covering security in network and information systems acquisition,
development, and maintenance, including a vulnerability-handling and
coordinated-disclosure capability and SBOM production for releases.
The vulnerabilities evidence stream discharges the operational
half of that obligation by emitting, per inbound disclosure cycle,
a per-execution artifact that records *which case the operator
triaged*, *what severity policy fired*, *what response branch was
chosen*, *what regulator-notification milestones the case has
reached*, *who owns the case as a role*, and *what disclosure-SLA
the operator is held against*. The wording of Article 21(2)(e)
itself is in Directive (EU) 2022/2555 (CELEX 32022L2555); see
[`article-21-2-e.yaml`](./article-21-2-e.yaml) for the citation
record. Source language is not copied into this repository.

Field-level mapping:

| Schema field                              | What it pins for §21(2)(e)                                                                                                  |
|-------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| `artifact_id`                             | Deterministic, content-addressable identity for one triage / response cycle; lets a reviewer follow the audit trail without relying on operator-side numbering. |
| `case_ref`                                | Stable per-disclosure case identity (SHA-256 of CVE + asset); groups every re-execution of the same disclosure across its lifecycle. |
| `execution_id`                            | Per-execution identity issued by the compile target; re-emissions are evidentiary, not deduplicated away. |
| `control_refs[]`                          | The controls the artifact attests — for §21(2)(e) the carriers are `control.vuln_disclosure_intake@v1` and `control.sbom_capture@v1`. |
| `regulation_refs[]`                       | Pins every regulatory obligation the artifact discharges; the §21(2)(e) entry resolves to `nis2:art-21-2-e` in `article-21-2-e.yaml`. |
| `triage_decision.severity` / `cvss_severity` / `cvss_base_score` / `cvss_vector` / `epss_probability` / `actively_exploited` | Typed triage outputs; this is the "vulnerability handling" half — the operator must demonstrate a triage policy fired and which inputs drove it. |
| `triage_decision.cra_clock`               | Which CRA Article 14 reporting clock triage started; the §21(2)(e) duty composes with the CRA notification chain on covered products. |
| `triage_decision.dedup_outcome` / `dedup_collided_with` | Pins whether the case is new or folded into an open case; lets a reviewer see disclosure-volume accounting without re-running the dedup primitive. |
| `triage_decision.risk_summary`            | One-paragraph residual-exposure narrative; the qualitative half of the triage record, role-shaped per public-bar discipline. |
| `response.band`                           | Response branch chosen (patch / mitigate / accept / schedule); discharges the "handle the vulnerability" branching the obligation expects. |
| `response.case_opened_at` / `patch_disseminated_at` / `advisory_ref` | The dissemination half — when the patch or advisory shipped to affected users, and under what identifier; downstream KPI `kpi.patch_disseminated_on_time@v1` reads these. |
| `response.accept_rationale` / `compensating_controls`                | When the operator accepts residual exposure, the rationale and any compensating controls; lets a reviewer audit the residual-risk path under §21(2)(e). |
| `disclosure_timeline[]`                   | Ordered regulator-notification milestones (early-warning / 72h / final-report); the coordinated-disclosure-toward-authorities half of the obligation. |
| `reporter_acknowledgement.disclosure_received_at` / `acknowledged_at` / `sla_duration` | The reporter-acknowledgement half — pins that an inbound disclosure was received and acknowledged inside the operator's documented CVD SLA. Feeds `kpi.vuln_disclosure_sla@v1`. |
| `owner`                                   | Role-shaped ownership with `assigned_at`; discharges the "dated ownership" requirement without putting an individual's name in a public-bar artifact. |
| `captured_at`                             | UTC capture timestamp for the per-execution record. |
| `provenance`                              | `{ source_url, captured_at, commit_sha }` — pins the provenance trail mirrored from `content/controls/`. |
| `retention`                               | Optional retention pointer; reserves the field for operator-declared evidentiary retention. |

The downstream KPIs / KRIs the stream feeds — `kpi.vuln_disclosure_sla@v1`,
`kri.cvd_intake_aging@v1`, `kpi.patch_disseminated_on_time@v1`, and
the four CRA-timing KPIs (`kpi.cra_early_warning_on_time@v1`,
`kpi.cra_severe_incident_on_time@v1`, `kpi.cra_notification_72h_on_time@v1`,
`kpi.cra_final_report_on_time@v1`) — are referenced from
[`article-21-2-e.yaml`](./article-21-2-e.yaml) under `metric_refs`.

The **SBOM-production** half of §21(2)(e) is anchored on the same
mapping entry via `control.sbom_capture@v1` and the
`kri.releases_without_sbom@v1` indicator; the per-release SBOM
evidence shape itself is out of scope for this stream (vulnerabilities
is the response-side stream, not the release-side stream) and stays
its own follow-on under the SBOM control.

## How this is emitted

The shared emitter under
[`compilers/_shared/evidence/vulns.py`](../../../compilers/_shared/evidence/vulns.py)
assembles the artifact; each of the three reference compile targets
calls into the shared emitter and writes the same on-disk bytes.
Byte-parity is pinned per target by an immutable golden:

- **n8n** — adapter under
  [`compilers/n8n/evidence/vulns_node.py`](../../../compilers/n8n/evidence/vulns_node.py);
  per-target byte-parity golden at
  [`tests/examples/vulnerabilities_evidence/`](../../../tests/examples/vulnerabilities_evidence/)
  pinned against
  [`tests/fixtures/vulnerabilities_evidence/n8n.json`](../../../tests/fixtures/vulnerabilities_evidence/).
- **Temporal** — activity under
  [`compilers/temporal/evidence/vulns_activity.py`](../../../compilers/temporal/evidence/vulns_activity.py);
  same per-target test directory, pinned against
  [`tests/fixtures/vulnerabilities_evidence/temporal.json`](../../../tests/fixtures/vulnerabilities_evidence/).
- **LangGraph** — node wiring under
  [`compilers/langgraph/evidence/vulns_node.py`](../../../compilers/langgraph/evidence/vulns_node.py);
  same per-target test directory, pinned against
  [`tests/fixtures/vulnerabilities_evidence/langgraph.json`](../../../tests/fixtures/vulnerabilities_evidence/).

Cross-target round-trip equivalence (all three targets agree
byte-for-byte under one execution) is pinned by
[`tests/content_model/test_vulns_evidence_emitter.py`](../../../tests/content_model/test_vulns_evidence_emitter.py).
The per-target goldens are the EXTEND complement: a refactor of the
shared emitter that silently changes serialisation fails the test for
the specific target whose bytes drifted.

The targets are framework-agnostic by construction — each is one of
three, not the engine. An operator running a fourth compile target
implements the same shared-emitter interface and lands their own
per-target golden.

## Cross-regime alignment

The vulnerabilities evidence stream sits on a regulatory crossroad and
the structural crosswalk already records the anchors. **This mapping
document does not extend the crosswalk** — it only references what is
already on disk:

- **DORA Article 9(4)(a)** plus the JC RTS on ICT risk management
  framework (Commission Delegated Regulation (EU) 2024/1774) Art. 10 —
  the ICT-vulnerability-management duty on financial entities is
  anchored at
  [`content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml`](../dora/article-9-and-rts-vuln-mgmt.yaml)
  under the `dora:art-9-vuln-mgmt` entry, which pins the same
  `playbook.vuln_intake@v1` and the same `control.vuln_disclosure_intake@v1`.
- **CRA Article 14** (manufacturer reporting obligations on actively
  exploited vulnerabilities and severe incidents) — anchored at
  [`content/mappings/cra/article-14-and-annex-i.yaml`](../cra/article-14-and-annex-i.yaml);
  the four CRA-timing KPIs referenced above are the metric carriers
  on that side.

Extending the crosswalk — promoting per-field equivalence between
NIS2 §21(2)(e), DORA Art. 9(4)(a), and CRA Art. 14 into a typed
overlap matrix — is a follow-on sibling, not this card.

## See also

- [`article-21-2-e.yaml`](./article-21-2-e.yaml) — the structural
  mapping entry this document narrates.
- [`content/evidence/vulns/README.md`](../../evidence/vulns/README.md) —
  contributor home for the stream, with the at-a-glance field summary.
- [`schemas/evidence/vulns.schema.json`](../../../schemas/evidence/vulns.schema.json) —
  authoritative artifact shape.
- [`ROADMAP.md` §F-CP-04](../../../ROADMAP.md) — feature definition and
  acceptance criteria.
