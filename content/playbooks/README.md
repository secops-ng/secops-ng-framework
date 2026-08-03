# content/playbooks/

CACAO v2 response playbooks — the portable content this framework exists to
ship. **One directory per playbook, named by its slug.**

## The layout is flat on purpose

A playbook's directory name is its slug, and the slug is its permanent
identity: `x_secops_ng.stable_id` is always `playbook.<slug>@v1`, and that
handle is what compilers, tests, cross-playbook handoffs and downstream
deployments reference. Renaming or moving a playbook breaks real consumers,
so the filesystem carries exactly one stable name per playbook and nothing
else.

There is no category nesting (`incident/`, `compliance/`, `vuln/`) because
most playbooks belong to several categories at once — ransomware containment
is incident response *and* malware handling *and* backup recovery.
Classification lives in metadata, where an artifact can carry many tags:
`playbook_types` and `labels` inside the CACAO document, and the regulatory
anchors in each playbook's `mappings.yaml`. Tooling discovers content by
globbing this directory, not by knowing a taxonomy.

The families are still visible in the names themselves: lifecycle chains
(`alert_triage` → `incident_management` → `post_incident_review`;
`vuln_intake` → `vulnerability_management` → `patch_management`),
regulation-anchored playbooks prefixed by the law they serve (`dora_*`,
`nis2_*`, `cra_*`, `eu_ai_act_*`, `eidas2_*`), identity
(`iam_auditor`, `identity_compromise`, `onboarding_offboarding_tracker`),
scenario response (`phishing_triage`, `ransomware_containment`,
`ddos_response`, `data_exfil`), and posture / programme playbooks.

## What a playbook directory contains

| Entry | Purpose |
|---|---|
| `playbook.cacao.json` | the canonical artifact (CACAO v2 + `x_secops_ng` superset). Some playbooks keep the canonical as `playbook.cacao.yaml` — same schema, YAML serialization. |
| `README.md` | scenario, prerequisites, regulatory anchors, and the bindings an operator supplies |
| `mappings.yaml` | OSCAL / D3FEND / OCSF / KPI wiring into `../mappings/`, `../controls/`, `../metrics/` |
| `primitives/` | where CORE work has landed: deterministic, replay-safe Python bodies that `core_body` bindings reference. Importable as `content.playbooks.<slug>.primitives` — which is why this directory tree is a Python package. |
| `payloads/` | (some playbooks) typed payload models for the shapes the playbook ingests |

Playbooks grow in stages — SKELETON (workflow graph + mappings + README, the
committed contract) → CORE (primitives written and bound, three-target
compiled examples with byte-parity goldens) → EXTEND (cookbook walkthrough,
metric pairs). An action step without a `{primitive, in, out}` binding is an
honest TODO, and the tooling counts it rather than hiding it.

## Entries that are not playbooks

- `_template/` — the contributor scaffold for a new playbook. The underscore
  prefix means "not content"; tooling skips `_*` directories.
- `__init__.py`, `__pycache__/` — package plumbing and build residue of the
  importable primitives. Not content.
- `alert_triage.cacao.yaml` — the one layout exception: a directory-level
  YAML canonical whose semantically identical JSON twin lives at
  `alert_triage/playbook.cacao.json`. Edit both or neither;
  `tests/content/test_playbook_mirror_parity.py` guards the pair against
  drift.

## Counting and cataloguing

Do not hand-count this directory, and do not maintain a playbook table in
this file — both drift (an earlier version of this README listed six
playbooks while the tree held dozens). A naive `content/playbooks/*/` glob
also counts `_template` and `__pycache__`. The catalogue script computes the
truth, including per-playbook readiness and which sources cannot compile:

```sh
python .claude/skills/compile-playbooks/scripts/catalog.py --table
```

To choose a playbook and a compile target, start at
[`docs/quickstart/README.md`](../../docs/quickstart/README.md).
