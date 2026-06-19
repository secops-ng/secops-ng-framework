# content/evidence/vulns/

Vulnerabilities evidence stream — the second stream in the SecOps-NG
**evidence** layer (after `risk-analysis/`).

## What this stream is

An operator handling vulnerability disclosures under NIS2 Art. 21(2)(e),
DORA Art. 9(4)(a), or the CRA Article 14 reporting chain has to
demonstrate, per case, that the triage decision was made, the
coordinated-disclosure SLA was held, security updates were disseminated
on time, and the regulator-notification milestones (24h / 72h / 14d)
were submitted on time. That demonstration takes the shape of one
per-execution artifact emitted every time the `vuln_intake` playbook
runs.

This directory is the contributor home for that stream. The artifact
shape is declared in
[`schemas/evidence/vulns.schema.json`](../../../schemas/evidence/vulns.schema.json);
the upstream workflow is
[`content/playbooks/vuln_intake/`](../../playbooks/vuln_intake/);
the indicators it feeds live under
[`content/metrics/`](../../metrics/) — `kpi.vuln_disclosure_sla@v1`,
`kri.cvd_intake_aging@v1`, `kpi.patch_disseminated_on_time@v1`, and
the four CRA-timing KPIs.

The stream is framework-agnostic. A reference emitter for each of the
three compile targets (n8n, Temporal, LangGraph) lands under
`compilers/` once the F-CP-04 CORE-EMITTER-CONTRACT card ships.

## Regulator hooks

| Regulation | Article                | Obligation paraphrase                                                                                  | Mapping file                                                                       |
|------------|------------------------|--------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| NIS2       | Art. 21(2)(e)          | Vulnerability handling and disclosure; SBOM production for releases.                                   | [`content/mappings/nis2/article-21-2-e.yaml`](../../mappings/nis2/article-21-2-e.yaml) |
| DORA       | Art. 9(4)(a)           | Vulnerability and patch management procedures (operationalised by JC RTS Reg. (EU) 2024/1774 Art. 10). | [`content/mappings/dora/article-9-and-rts-vuln-mgmt.yaml`](../../mappings/dora/article-9-and-rts-vuln-mgmt.yaml) |
| CRA        | Annex I §2(2)          | Address and remediate vulnerabilities without delay; document the vulnerability-handling process.     | [`content/mappings/cra/article-14-and-annex-i.yaml`](../../mappings/cra/article-14-and-annex-i.yaml) |
| CRA        | Annex I §2(5)          | Coordinated vulnerability disclosure policy with single point of contact.                              | [`content/mappings/cra/article-14-and-annex-i.yaml`](../../mappings/cra/article-14-and-annex-i.yaml) |
| CRA        | Annex I §2(7)          | Disseminate security updates without undue delay, with advisory messages.                              | [`content/mappings/cra/article-14-and-annex-i.yaml`](../../mappings/cra/article-14-and-annex-i.yaml) |
| CRA        | Art. 14(1) / (2) / (3) | Early-warning (24h), incident-notification (72h), final-report (14d), severe-incident (24h) clocks.    | [`content/mappings/cra/article-14-and-annex-i.yaml`](../../mappings/cra/article-14-and-annex-i.yaml) |

## Artifact shape — pointer

Authoritative shape: [`schemas/evidence/vulns.schema.json`](../../../schemas/evidence/vulns.schema.json).

At a glance, each artifact carries:

- `artifact_id` — deterministic SHA-256 of `<case_ref>|<execution_id>`.
- `case_ref` — SHA-256 of `<cve_id>|<asset_ref>`, set upstream by the
  F-WF-01 dedup primitive. Groups every re-execution of the same
  disclosure across the lifecycle.
- `execution_id` — per-execution id issued by the compile target's
  runtime. Re-runs of the same case_ref produce distinct executions.
- `regulation_refs[]` — pin to every regulatory obligation the artifact
  satisfies (typically the NIS2 / DORA / CRA entries above).
- `control_refs[]` — control stable-ids attested by this artifact
  (typically `control.vuln_disclosure_intake@v1` and/or
  `control.sbom_capture@v1`).
- `triage_decision` — severity, CVSS qualitative + score + vector, EPSS
  probability, `actively_exploited` flag, `cra_clock` (none /
  article_14_1 / article_14_3), `dedup_outcome`, and a free-text
  `risk_summary`.
- `response` — `{ band, case_opened_at, patch_disseminated_at,
  advisory_ref, accept_rationale, compensating_controls }`. `band` is
  one of `critical` / `high` / `scheduled` / `accept`.
- `disclosure_timeline[]` — append-only list of CRA Article 14
  milestones reached, each with `{ milestone, clock_started_at,
  submitted_at, submission_ref, on_time }`. Read by the four CRA-timing
  KPIs.
- `reporter_acknowledgement` — CVD intake acknowledgement event with
  the operator's documented SLA. Read by `kpi.vuln_disclosure_sla@v1`
  and `kri.cvd_intake_aging@v1`.
- `owner` — role-shaped ownership pointer with `assigned_at` date. No
  individual personal names.
- `captured_at` — ISO-8601 UTC timestamp.
- `provenance` — `{ source_url, captured_at, commit_sha }` mirror of
  the pattern used in `content/controls/`.
- `retention` — optional ISO-8601 duration retention pointer; the
  community-default value is an open question (see the F-CP-04 gap
  inventory).

## Promoted enums

The schema imports three small shared vocabularies promoted alongside
this stream:

- [`schemas/vuln_response_band.json`](../../../schemas/vuln_response_band.json)
  — the four response branches (`critical`, `high`, `scheduled`,
  `accept`) the F-WF-01 switch step routes onto.
- [`schemas/cra_clock_kind.json`](../../../schemas/cra_clock_kind.json)
  — which CRA Article 14 clock was started (`none`, `article_14_1`,
  `article_14_3`).
- [`schemas/cra_timing_milestone.json`](../../../schemas/cra_timing_milestone.json)
  — the four CRA Article 14 timing milestones the four CRA-timing KPIs
  read.

## Contributor checklist

If you are proposing a change that touches this stream:

1. The JSON Schema is the source of truth — change
   `schemas/evidence/vulns.schema.json` first, then update this
   README's at-a-glance summary if a field is added or removed.
2. The promoted enums above are intentionally small; extending any of
   them is a discussion, not a drive-by change.
3. The four CRA-timing KPIs and the CVD-intake SLA KPI / KRI live in
   `content/metrics/`; the stream wires emission, it does not
   re-declare the catalog entries here.
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

The stream's schema, the three promoted enums, the mapping-atom wires,
and the Pydantic v2 model + byte-stable JSON Schema export helper
landed in F-CP-04 SCHEMA. The EMITTER SKELETON card added the
framework-agnostic emitter
([`compilers/_shared/evidence/vulns.py`](../../../compilers/_shared/evidence/vulns.py))
and one wired compile target — the Temporal-side activity
([`compilers/temporal/evidence/vulns_activity.py`](../../../compilers/temporal/evidence/vulns_activity.py)) —
mirroring the F-CP-01 SKELETON pattern. CORE-FANOUT now extends the
SKELETON to n8n
([`compilers/n8n/evidence/vulns_node.py`](../../../compilers/n8n/evidence/vulns_node.py))
and LangGraph
([`compilers/langgraph/evidence/vulns_node.py`](../../../compilers/langgraph/evidence/vulns_node.py)),
sharing the same emitter helper end-to-end. Byte-parity goldens, the
drift-detection hook surface, the NIS2 Art. 21(2)(e) mapping doc, and
the ROADMAP flip fan out into the remaining siblings of the F-CP-04
wave; see
[`docs/internal/f-cp-04-gap-inventory.md`](../../../docs/internal/f-cp-04-gap-inventory.md).
