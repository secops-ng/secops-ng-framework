# GDPR data flow — codebase_vuln_management

Per-workflow GDPR data-flow entry for the
`codebase_vuln_management` cookbook playbook
(`playbook.codebase_vuln_management@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/codebase_vuln_management/`](../../playbooks/codebase_vuln_management/).

---

## 1. Purpose

The workflow exists to walk a freshly produced or refreshed software
bill of materials (SBOM) for a release the operator builds or
distributes, score each top-level dependency against a vulnerability
database (NVD, OSV, GHSA), assess each finding against the operator's
coordinated-vulnerability-disclosure (CVD) policy, and emit one
disclosure-timeline record per finding so downstream metrics streams
pick the case up. The purpose is bounded to that codebase-side
dependency-review decision chain and the per-finding record it
produces — the workflow does not retain reporter identifiers, contact
data, or any other personal-data attribute beyond the SBOM and
advisory metadata it walks.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

The workflow processes only dependency / SBOM metadata: package URLs
(PURL), package versions, advisory identifiers (CVE / GHSA / OSV),
severity scores, CVD-policy deadlines, and content-addressable hashes
of the SBOM artefact. None of these fields carry personal data
within the meaning of GDPR Art. 4(1): SBOMs and advisory feeds
identify software components and software vulnerabilities, not
natural persons.

Where an upstream advisory feed or SBOM-generation toolchain
incidentally includes a maintainer email address or other
personal-data attribute, that attribute is filtered at ingest and
not carried into the disclosure-timeline record — the
`schemas/evidence/codebase_vuln_management/disclosure-timeline-record.schema.json`
boundary rejects credential-shaped strings and personal-name fields
at the schema level per AGENTS.md §3.

If a future revision of this workflow extends scope to handle
reporter-supplied disclosure intake (currently handled by the
sibling `vuln_intake` workflow under
[`data-flow-vuln_intake.md`](./data-flow-vuln_intake.md)), this
section MUST be revisited and a real lawful basis declared before
that extension ships.

## 3. Categories of data subjects and personal data

Not applicable — no personal data processed. The workflow walks
software components (PURL + version) and software vulnerabilities
(CVE / GHSA / OSV advisory identifiers). No category of natural
person is the subject of the processing.

## 4. Recipients

Not applicable for personal data. For completeness, the recipients
of the non-personal codebase-finding data the workflow emits are:

- the operator's internal vulnerability-management surface
  (ticketing, dashboards, downstream evidence streams);
- the operator's external coordinated-disclosure surface
  (advisory publication, security-update dissemination per CRA
  Annex I §2(7)) — handled out-of-band by the operator's CVD
  policy, not directly by this workflow;
- the regulator-notification chain owned by the sibling
  `vuln_intake` workflow when (and only when) the codebase finding
  crosses into reporter-disclosed actively-exploited territory; that
  handover is a workflow-to-workflow event, not a
  data-subject-recipient relationship.

## 5. Retention

Not applicable for personal data. For completeness, the per-finding
disclosure-timeline records are retained for the support period of
the affected release (CRA Annex I §2(2): "throughout the support
period") plus the operator's regulatory retention overlay for NIS2
Art. 21 evidence. The retention mechanism is the evidence-bundle
expiry rule shared with the other evidence streams under
`schemas/evidence/bundle.schema.json`; this workflow does not
maintain its own retention schedule.

## 6. Cross-border transfers

**No transfer.** The default scanner is a CLI installable from an
EU-hosted package index — no hosted scanner SaaS dependency, no
non-EU default endpoint. The SBOM artefact, the advisory database
mirror, and the per-finding records all stay within the operator's
EU-hosted runtime by configuration. Operators MAY swap in a
non-EU-hosted scanner; doing so is visible in this section on a
fork of the data-flow doc, but is not the default and is not the
configuration the framework ships.

Advisory feeds (NVD, OSV, GHSA) are public information published
by their respective maintainers; fetching them does not constitute
a transfer of personal data within Chapter V because the fetched
content is non-personal vulnerability metadata.

## 7. Data subject rights

Not applicable — no personal data processed, no data subject to
exercise a right against this workflow. Subject Access Requests, if
any, reach the operator through the sibling `vuln_intake` workflow
(reporter-disclosed intake) rather than this codebase-side
dependency-review chain.
