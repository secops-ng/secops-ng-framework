# content/mappings/gdpr/

GDPR crosswalk. Entries land here as control objectives are mapped.

## Per-workflow data-flow documents

The canonical template at
[`_data-flow-template.md`](./_data-flow-template.md) defines the
section set every per-workflow `data-flow-<workflow>.md` document
must satisfy.

### Required sections (§1–§7) — Art. 30 ROPA

Sections one through seven are the per-workflow Record of Processing
Activity entry under **GDPR Art. 30**:

1. Purpose (Art. 5(1)(b))
2. Lawful basis (Art. 6(1))
3. Categories of data subjects and personal data (Art. 30(1)(c))
4. Recipients (Art. 30(1)(d))
5. Retention (Art. 5(1)(e))
6. Cross-border transfers (Chapter V, Art. 44–50) — scored as a
   whole against the workflow's processing
7. Data subject rights (Art. 12–22)

These are enforced by
[`tools/lint_gdpr_lawful_basis.py`](../../../tools/lint_gdpr_lawful_basis.py)
(the F-GD-02 EXTEND CI guard): every cookbook playbook under
`content/playbooks/` must have a sibling `data-flow-<workflow>.md`
where all seven sections are present and filled with contributor
prose.

### Section §8 — Outbound personal-data transfer (Chapter V)

Section eight is the **outbound** view of GDPR Chapter V (Art. 44–49):
where the workflow SENDS personal data — regulator submissions,
peer-operator or cross-border notification, threat-intel sharing,
processor / sub-processor egress — and the Chapter V transfer
mechanism (adequacy, SCCs / BCRs, derogation) that authorises each
outbound leg. The section enumerates each leg, its destination class,
the transfer instrument, the EU-residency posture per Directive 1
(sovereignty-first), and the data-minimisation discipline on the
outbound payload.

§8 is **rollout-optional** today: the canonical template tags it with
an HTML-comment marker (`<!-- skeleton-pending -->`) and the F-GD-02
EXTEND CI guard accepts a missing or unfilled §8 on any data-flow
doc during the per-playbook EXTEND fan-out. The heading text itself
is still drift-checked — renaming §8 or inserting a non-canonical §8
is rejected as drift.

The worked exemplar is
[`data-flow-incident_management.md`](./data-flow-incident_management.md),
which scores three outbound legs (NIS2 Article 23 regulator
submissions, NIS2 cross-border cooperation notification, and
operator-bound processor egress) against Chapter V under the
default sovereign-stack posture.
