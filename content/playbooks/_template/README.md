# Playbook template

This directory is a **scaffold**, not a playbook. It is the starting
point a new contributor copies to
`content/playbooks/<slug>/` when adding a workflow to the commons. The
underscore prefix keeps it out of the finalized-playbook set that
orphan-CI and the schema lint walk.

For the short path from empty scaffold to open PR, read
[`docs/contributing/playbook-quickstart.md`](../../../docs/contributing/playbook-quickstart.md).
For the exhaustive field reference, read
[`docs/contributing/playbook-authoring.md`](../../../docs/contributing/playbook-authoring.md).

## Contents

- `playbook.cacao.yaml` — CACAO v2 skeleton with inline comments on
  every required field, action steps in the house shape (`in_args` /
  `out_args` / per-step `x_secops_ng`, optional `core_body` binding).
  YAML is used here only because it supports comments; canonical
  playbooks ship JSON, so convert this file to `playbook.cacao.json`
  before opening the PR (quickstart § 3).
- `mappings.yaml.example` — schema-minimum outbound mapping overlay.
  Rename to `mappings.yaml` in your copy and fill the seven keys; the
  `.example` suffix keeps the structural-tier NO_MAPPING_EDGE signal
  armed until you do (quickstart § 5).
- `README.md` — this file. When you copy the template, replace it with
  a per-playbook README following the section headings below.
- `examples/` — placeholder for sample input / output fixtures the
  compiler tests read.

## Overview

*(Replace this section in your copy.)*

One paragraph naming the workflow, its trigger, its inputs, and the
artifact it produces. Keep it factual — this is the first thing an
operator or reviewer reads.

## Regulatory anchors

*(Replace this section in your copy.)*

Bullet the specific clauses this playbook operationalises. Cite the
official source, not a secondary summary. Example shapes:

- **Cyber Resilience Act (EU) 2024/2847, Article 14 §6** —
  acknowledgement of received reports to the reporter within a
  policy-declared window.
- **NIS2 Article 23(1) (overlap)** — when the workflow produces a
  severe incident, the operator's NIS2 notification chain runs in
  parallel.

If the playbook is SKELETON and the outbound mappings will land in a
sibling CORE PR, say so here and reference the target card by title
(not by internal id).

## How to compile

*(Replace this section in your copy.)*

Name the compile targets you declared in
`x_secops_ng.compile_targets`, if any. Point to the emitted example
directories once the CORE cookbook lands:

- n8n — `examples/n8n/<slug>/`
- Temporal — `examples/temporal/<slug>/`
- LangGraph — `examples/langgraph/<slug>/`

If the playbook is portable content only for now
(`compile_targets: []`), say so and reference the follow-up card that
will add a compile target.

## Operator customisation

*(Replace this section in your copy.)*

Name the CACAO variables the playbook exposes and the operator-side
knobs (thresholds, notification channels, retention windows) the
compilers surface. Point to the templates directory if the playbook
renders human-facing artifacts.

## Sources

*(Replace this section in your copy.)*

List the primary upstream specifications and clauses the playbook is
grounded in. One line per source. Match what you put under
`x_secops_ng.sources` in the artifact.
