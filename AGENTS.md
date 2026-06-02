# AGENTS.md — SecOps-NG contributor guide

This file is for **humans and AI coding assistants** (Aider, Cursor,
Claude Code, Continue, Codex CLI, and similar) working in this
repository. It is the entrypoint a new contributor or an agent running
from outside the maintainer org should read first.

If you are looking for the project mission, the published narrative, or
the user-facing voice, start at [`SOUL.md`](SOUL.md) and the website
([secops-ng.com](https://secops-ng.com)). If you are looking for
governance, see [`GOVERNANCE.md`](GOVERNANCE.md). If you are looking for
the feature roadmap, see [`ROADMAP.md`](ROADMAP.md).

This document covers: what kind of repository this is, what the public
surface looks like, the conventions you should follow before opening a
PR, and the hygiene bar a PR is reviewed against.

---

## 1. What this repository is

SecOps-NG is the framework repository of a community-driven initiative
building **sovereign security for the EU** as a Digital Commons. The
output is portable content — CACAO playbooks, OSCAL/D3FEND control
mappings, OCSF data shapes, a KPI/KRI catalogue — plus reference
compilers that emit that content into the orchestrator an operator
already runs.

The project is **framework-agnostic**. It does not ship its own runtime,
agent framework, or SOAR. Three reference compile targets are
maintained: **n8n** (no-code), **Temporal** (durable code), and
**LangGraph** (agentic). Each is one of three, not the engine.

Read [`docs/FOUNDATION.md`](docs/FOUNDATION.md) for the four
non-negotiable properties (auditability, determinism, sovereignty,
operability) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for
the four-layer runtime that the content compiles into.

## 2. Repository layout

| Path | Purpose |
|------|---------|
| `content/` | Portable artifacts: CACAO playbooks, OSCAL/D3FEND mappings, KPIs. Framework-agnostic; this is the canonical source for everything that gets compiled. |
| `compilers/` | Reference compilers that read `content/` and emit n8n / Temporal / LangGraph artifacts. |
| `examples/` | Per-workflow compiled examples (`examples/{n8n,temporal,langgraph}/<workflow>/`) used by golden tests and as runnable starting points. |
| `tests/` | Unit, integration, and per-example byte-parity golden tests. |
| `tools/hygiene_linter/` | The forward-public hygiene linter. Runs in CI; you can run it locally too. |
| `docs/` | FOUNDATION, ARCHITECTURE, deployment guides, contributor references. |
| `ROADMAP.md` | Source-of-truth feature definitions, reviewed by the community. |
| `SECURITY.md` | Coordinated disclosure policy. |
| `CONTRIBUTING.md` | How to propose a change, sign-off conventions, review flow. |
| `GOVERNANCE.md` | Maintainer roles, decision process, conflict resolution. |
| `CODE_OF_CONDUCT.md` | Community standards. |

## 3. Public-bar hygiene (read before committing)

Every commit, comment, and file in this repository is treated as
already public. The project is currently developed in a private
mirror, but the working assumption — and the rule the linter and
reviewers enforce — is that anything you write here may be read by an
operator, a journalist, or a regulator tomorrow.

Concretely, **do not** include:

- **Commercial framing.** Avoid the vocabulary of selling: words for
  buyers, price points, market-segment acronyms, funnel/pipeline
  terms, money-in framing, advisory-services framing. The voice is
  community / commons / practitioners. The published pages on the
  website are the live exemplar; the hygiene linter (§ 4) encodes
  the explicit list.
- **Credentials.** No API keys, tokens, passwords, private keys, or
  anything secret-shaped. Use environment variables and document them
  in `.env.example`.
- **Internal infrastructure details.** No internal paths, internal
  tool names, internal task-tracking ids, or references to private
  sibling repositories or the maintainers' development harness.
- **Contact or lead names.** No individual names attached to
  organisations the maintainers are talking to.

If you are unsure whether something belongs in the public repository,
it does not. See [`SOUL.md`](SOUL.md) for the voice the project uses
in public surfaces.

## 4. The hygiene linter

A linter at `tools/hygiene_linter/` enforces a subset of the public-bar
rules mechanically. It runs in CI on every PR via
`.github/workflows/hygiene-lint.yml`. You can run it locally:

```sh
python -m tools.hygiene_linter --min-severity LOW
```

HIGH findings (credential-shaped strings) block merge. MEDIUM findings
(commercial-language hits) are reviewed by a maintainer. The linter is
a floor, not a ceiling — passing it does not guarantee the change is
acceptable; failing it almost always means rework.

## 5. Conventions for AI coding assistants

If you are an AI assistant operating from a user's machine against this
repository:

- **Default to small, scoped PRs.** One feature or one bugfix per
  branch. Cookbook changes that touch multiple workflows belong in
  multiple PRs.
- **Run the test suite locally before opening the PR.**
  `python -m pytest` from the repo root. Per-example byte-parity tests
  under `tests/examples/` matter — if you change a compiler, expect
  golden output to change and update both intentionally in the same
  PR.
- **Run the hygiene linter locally.** See § 4. The CI lane will run it
  anyway; failing it client-side wastes a review cycle.
- **Read `SOUL.md` once at the start of a session** to calibrate voice.
  The published Astro pages on the website are the live exemplar.
- **Do not invent kanban ids, ticket numbers, or maintainer initials.**
  If the user references a kanban id like `t_...`, that is internal to
  their working copy — do not write it into a commit message, PR body,
  or code comment.
- **Reference issues and PRs by number, not by author.** PRs are reviewed
  on content; attaching individual names to in-flight work creates
  pressure that the project's governance model is designed to avoid.

## 6. Conventions for human contributors

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first. The short version:

1. Open an issue or comment on an existing one before starting a large
   change. Small drive-by fixes (typos, broken links, obvious bugs) do
   not need pre-discussion.
2. Branch off `main`. Branch naming: `<area>/<short-description>` —
   `compilers/n8n-array-handling`, `docs/foundation-clarifications`,
   `tests/posture-audit-golden`.
3. Sign your commits per the DCO instructions in `CONTRIBUTING.md`.
4. Open the PR against `main`. Fill in the PR template — the linter
   acknowledgement is not optional.
5. A maintainer will review. Expect questions about
   sovereignty-stack alignment for changes that touch the compilers,
   and questions about voice for changes that touch published copy.

## 7. Coordinated disclosure

Do **not** open a public issue for a suspected vulnerability. See
[`SECURITY.md`](SECURITY.md) for the supported reporting flow.

## 8. Where to learn more

- [`SOUL.md`](SOUL.md) — voice, tone, and external-communications
  guardrails.
- [`ROADMAP.md`](ROADMAP.md) — feature definitions and status.
- [`GOVERNANCE.md`](GOVERNANCE.md) — maintainer roles and decision
  process.
- [`docs/FOUNDATION.md`](docs/FOUNDATION.md) — the four non-negotiable
  properties.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — the four-layer
  runtime.
- [secops-ng.com](https://secops-ng.com) — the project website.
