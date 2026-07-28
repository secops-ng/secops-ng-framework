# Playbook quickstart

A short, opinionated path from empty checkout to a first playbook PR.
This is the fast lane; for the exhaustive rules read
[`playbook-authoring.md`](playbook-authoring.md) and the top-level
[`CONTRIBUTING.md`](../../CONTRIBUTING.md).

The steps below assume you have a green checkout, a Python environment
that can run the test suite, and a workflow you want to contribute as
portable CACAO v2 content.

## 1. Pick a slug

The slug is the directory name under `content/playbooks/` and the
segment inside the playbook's `x_secops_ng.stable_id`
(`playbook.<slug>@v1`). Rules:

- `snake_case`, ASCII, no digits at the start.
- Names the workflow, not the technology (`vulnerability_intake` yes,
  `n8n_vuln_flow` no).
- Stable forever — renaming a landed slug is a breaking change.

Check it does not already exist:

```bash
ls content/playbooks/ | grep -i <candidate>
grep -r "playbook.<candidate>@" content/
```

If either returns a hit, pick a different slug. Composing with an
existing playbook (see `cra_cvd` and `cra_srp_notify`) is welcome;
overlapping with one is not.

## 2. Scaffold from the template

Copy the reference scaffold and rename:

```bash
cp -r content/playbooks/_template content/playbooks/<slug>
```

You now have:

```
content/playbooks/<slug>/
├── playbook.cacao.yaml    # commented skeleton — fill it in, then convert to JSON
├── README.md              # human-readable overview
└── examples/              # sample input / output fixtures
    └── .gitkeep
```

Open `playbook.cacao.yaml` and replace every `TODO_*` placeholder. The
inline comments explain what each field is for and which values the
schema accepts.

Replace the guidance in `README.md` while preserving these canonical
second-level headings, which the strict template check requires for
every new playbook:

- `## Overview`
- `## Regulatory anchors`
- `## How to compile`
- `## Operator customisation`

## 3. Convert the artifact to JSON

Canonical playbooks ship JSON, not YAML. The template ships YAML so it
can carry inline comments; convert once your fields are correct:

```bash
python -c 'import sys, json, yaml; \
  json.dump(yaml.safe_load(open("content/playbooks/<slug>/playbook.cacao.yaml")), \
            open("content/playbooks/<slug>/playbook.cacao.json","w"), indent=2)'
rm content/playbooks/<slug>/playbook.cacao.yaml
```

For the reasoning behind JSON-only see `playbook-authoring.md` § 2.

## 4. Add at least one mapping entry

Every playbook that lands on `main` needs an inbound citation from at
least one regulatory YAML — otherwise orphan-CI holds it. Add a line
under the appropriate framework:

```
content/mappings/nis2/article-XX.yaml
content/mappings/dora/article-XX.yaml
content/mappings/cra/article-XX.yaml
content/mappings/gdpr/article-XX.yaml
```

Open the clause file that most naturally cites the workflow, find the
entry, and append `playbook.<slug>@v1` to its `playbook_refs:` list.
`playbook-authoring.md` § 4 has a worked example.

If the mappings closure will land in a follow-on PR (SKELETON pattern),
add the slug to the framework's `_orphan_skip.yaml` with a rationale
and a target CORE card reference. Temporary only — a permanent skip is
a design mistake.

## 5. Run the linter and tests locally

Two commands, in this order:

```bash
python -m tools.hygiene_linter --min-severity LOW content/playbooks/<slug>/
python -m pytest tests/
```

The hygiene linter enforces the public-bar rules (no credentials, no
commercial framing). HIGH findings block merge, MEDIUM findings need
reviewer sign-off, LOW findings are advisory. The full test suite
covers schema validation, mapping-shape lint, and per-framework
orphan-CI.

If the linter fires on something you believe is legitimate, see
[`hygiene-linter.md`](hygiene-linter.md) for the escalation path.

## 6. Open the pull request

Branch naming: `content/<framework>-<slug>` for regulatory-anchored
playbooks, `content/playbook-<slug>` for cross-cutting workflows.

Commit-message and PR-title convention:

```
content(playbooks): add <slug> — <one-line description>
```

The PR body should:

- Name the regulatory or operational anchor (CRA / NIS2 / DORA / GDPR
  clause, OSCAL control, D3FEND technique, or OCSF event class).
- Link to the mapping YAML lines that cite the new slug (or the
  `_orphan_skip` entry and its target CORE card).
- Acknowledge the DCO sign-off and the hygiene-linter run.

A maintainer will review against the voice guardrails in
[`SOUL.md`](../../SOUL.md) and the four foundation properties in
[`FOUNDATION.md`](../FOUNDATION.md). Expect questions about
sovereignty-stack alignment for anything that touches the compilers.

## 7. What lands after merge

The playbook becomes part of the commons. If you declared
`compile_targets`, the follow-on cookbook lands the compiled examples
under `examples/{n8n,temporal,langgraph}/<slug>/` in a sibling PR;
byte-parity golden tests catch drift from there on.

If you need to iterate on the playbook after merge, treat it as
append-only — bump `x_secops_ng.content_version`, keep `stable_id`
frozen, and open a follow-up PR.

## Where to go next

- [`playbook-authoring.md`](playbook-authoring.md) — full field
  reference, schema notes, and worked mapping example.
- [`hygiene-linter.md`](hygiene-linter.md) — public-bar rules the
  linter enforces.
- [`compiler-walkthrough.md`](compiler-walkthrough.md) — landing a
  compiled example alongside the portable playbook.
- [`review-process.md`](review-process.md) — what to expect from a
  maintainer once the PR is open.
