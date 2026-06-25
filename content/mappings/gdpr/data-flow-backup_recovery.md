# GDPR data flow — backup_recovery

Per-workflow GDPR data-flow entry for the `backup_recovery` cookbook
playbook (`playbook.backup_recovery@v1`). Filled in against
[`_data-flow-template.md`](./_data-flow-template.md). Together the
seven sections below form the Art. 30 Record of Processing Activity
entry for this workflow.

Workflow source of truth:
[`content/playbooks/backup_recovery/`](../../playbooks/backup_recovery/).

---

## 1. Purpose

The workflow exists to exercise the operator's business-continuity
surface on a scheduled or operator-initiated restore-drill window:
detect the drill trigger, validate the integrity of the most recent
in-scope backup artifact (checksum, manifest, decryption-key
availability), execute a non-destructive restore drill against the
operator's documented isolated drill target, capture the dated
attestation + drill-evidence record, and notify the continuity
owner. The purpose is bounded to that exercise decision and the
metric hook it produces (`kpi.backup_integrity_pass_rate@v1`); the
workflow does not author the operator's backup policy itself, does
not run against production state, and does not retain or inspect
the contents of the restored objects beyond the inventory and
RTO/RPO counters the drill produces.

## 2. Lawful basis

**Out of scope: no personal data processed in this workflow.**

The workflow operates on backup-artifact metadata, not on the
contents of the backups themselves. The fields it reads and writes
are: backup-artifact identifiers, backup-scope identifiers,
checksum / manifest values, decryption-key-availability booleans
against the operator's key-management surface, restored-object
inventories (object identifiers only), RTO/RPO counters, attestation
identifiers, and the continuity owner's pre-bound channel
identifier. None of these carry personal data within the meaning of
GDPR Art. 4(1): the workflow exercises the recovery capability of a
backup artifact, it does not process the personal-data payload that
artifact may contain.

The backup artifacts themselves may, depending on the operator's
documented backup scope, contain personal data — but the lawful
basis for the underlying processing (production-system processing
of subject data, with backup as a retention discipline under
GDPR Art. 5(1)(e) and a security-of-processing discipline under
Art. 32) lives on the operator's production-system data-flow
entries, not on this exercise playbook. This workflow is the
periodic-testing discipline that Art. 32(1)(d) and NIS2 Art.
21(2)(c) require operators to run against those backups; it does
not introduce a new processing purpose against the subject data.

If a future revision of this workflow extends scope to inspect the
restored object contents (for example, to validate per-record
fidelity against a production sample), this section MUST be
revisited and a real lawful basis declared before that extension
ships.

## 3. Categories of data subjects and personal data

Not applicable — no personal data processed. The workflow operates
on backup-artifact metadata, restore-target identifiers, RTO/RPO
counters, and attestation records. No category of natural person is
the subject of the processing.

For completeness: the continuity owner's pre-bound channel
identifier (ticketing system, chat thread, email) is a contact
endpoint, not a data-subject record — the notify-continuity-owner
step delivers an attestation reference along that channel and does
not introduce or retain a per-subject record beyond what the
operator's notification surface already holds independently.

## 4. Recipients

Not applicable for personal data. For completeness, the recipients
of the non-personal drill-evidence data the workflow emits are:

- the operator's **evidence store** — primary recipient of the
  dated attestation + drill-evidence record (the audit-evident
  artifact NIS2 Art. 21(2)(c) and DORA Art. 12 reviewers read);
- the operator's **continuity owner** along their pre-bound
  channel — receives the attestation reference via the
  notify-continuity-owner step;
- the **catalogue metric pipeline** that reads
  `kpi.backup_integrity_pass_rate@v1` from the emitted records for
  programme-level rollup (handled by the sibling `executive_metrics`
  workflow).

No external processor is invoked by the default configuration; the
backup store, the key-management surface, the isolated drill
target, and the evidence store are all operator-bound infrastructure.

## 5. Retention

Not applicable for personal data. For completeness, the dated
attestation + drill-evidence record is retained as the operator's
NIS2 Art. 21(2)(c) / DORA Art. 12 evidence under the operator's
regulatory-retention overlay; the retention mechanism is the
evidence-bundle expiry rule shared with the other evidence streams
under `schemas/evidence/bundle.schema.json`. This workflow does not
maintain its own retention schedule.

The candidate backup artifacts the workflow reads are governed by
the operator's backup-retention policy, which lives outside this
playbook. The workflow only resolves and reads them for the
duration of the drill; it does not extend or shorten their
retention.

## 6. Cross-border transfers

**No transfer.** The default configuration runs the validate-
integrity step, the restore-drill execution, the evidence-capture
emission, and the notify dispatch entirely against operator-bound,
EU-resident endpoints (the operator's backup store, key-management
surface, isolated drill target, and evidence store). No public-cloud-
AI dependency is wired on the workflow's hot path. Operators MAY
swap in a non-EU-hosted backup store or drill target; doing so is
visible on a fork of this data-flow doc, but is not the default and
is not the configuration the framework ships.

Even where the underlying backup artifacts contain personal data
governed by Chapter V on the production-side workflow, the exercise
discipline this playbook operates does not itself cross a Chapter V
boundary — the restore lands on the operator's isolated drill
target, not on a third-country endpoint.

## 7. Data subject rights

Not applicable — no personal data processed, no data subject to
exercise a right against this workflow. Subject Access Requests,
rectification requests, erasure requests, and objections that bear
on the underlying backup contents are answered against the
operator's production-side workflows that own the subject data; the
backup_recovery playbook neither creates a new subject record nor
holds a copy of one that a subject could exercise rights against
independently.

The dated attestation + drill-evidence record names the candidate
backup artifact by identifier, not by content; it carries no
subject-identifier fields.

## 8. Outbound personal-data transfer

**No outbound personal-data transfer — N/A.** Per §3, the workflow
processes backup-artifact metadata, restore-target identifiers,
RTO/RPO counters, and attestation records; no category of natural
person is the subject of the processing, so no Chapter V outbound
leg exists.

The non-personal-data outbound legs documented elsewhere (evidence-
store publication in §4, continuity-owner notification in §4, the
catalogue-metric pipeline rollup in §4) do not engage Chapter V
because their payloads carry no personal data: the attestation
record names the candidate backup artifact by identifier and the
notification carries the attestation reference along an
operator-bound channel.

Cross-reference §6: the workflow-as-a-whole cross-border scoring is
**no transfer** and this §8 carries no contradicting leg.

If a future binding wires a non-EU-hosted drill target, an attestation
field that captures a subject-identifier excerpt from the restored
inventory, or any other surface that introduces personal data into
the exercise discipline, this section MUST be re-scored against the
canonical four-axis shape (destination class, transfer mechanism,
EU-residency posture, data minimisation) and §3 amended in the same
change.
