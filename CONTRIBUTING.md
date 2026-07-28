# Contributing to SecOps-NG

Welcome. SecOps-NG is a Digital Commons for sovereign security operations
in the EU. The work here belongs to the people doing it and to the
community that relies on it — not to any one organisation. If you have
made it this far, you already belong here.

This document walks you through your first contribution end-to-end:
from cloning the repository to seeing your change reviewed and merged.
Read it once before you start. It is short on purpose.

## Your first contribution

If this is your first time contributing here, the operational
companion to this document —
[`docs/contributing/first-contribution.md`](docs/contributing/first-contribution.md)
— walks through fork, branch, tests, hygiene linter, and pull request
as a sequence of exact commands. Read it alongside the sections below.

## 1. Clone the repository

```bash
git clone https://github.com/secops-ng/secops-ng-framework.git
cd secops-ng-framework
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # local only; never commit this file
```

Sanity-check that the toolchain works on your machine:

```bash
pytest            # unit + smoke tests
ruff check .      # lint
ruff format .     # auto-format
mypy src          # type-check
```

CI runs the same set on every pull request. Green locally is the
baseline; green in CI is the contract.

## 2. Read SOUL.md before you write anything public-facing

Open `SOUL.md` and read it through. It is a single page. It defines the
voice of the project: how we talk about sovereignty, regulation, and the
commons in any file that will one day be public.

This is not branding. It is a guardrail against drift. Code comments,
commit messages, documentation, issue titles, PR descriptions — anything
that lands in a public repository carries the same standard.
The shortest summary: we are a commons, not a vendor; sovereignty is a
public good, not a selling point; "we" for the project, "you" for the
reader, never "I" or "the company."

If a phrasing question comes up while you work, `SOUL.md` is the
reference. When in doubt, ask in the pull request — that conversation
itself is part of how the commons learns its own voice.

## 3. Licensing in plain terms

SecOps-NG separates the licence on *code* from the licence on *content*,
the same split the [secops-ng-website][website-repo] uses. In practice
that means:

- **Code** — compilers, schemas-as-code, primitives, tests, CLI tooling
  — is licensed under **Apache-2.0**. See [LICENSE](LICENSE).
- **Content** — playbooks, control mappings, telemetry shapes, the
  KPI/KRI catalogue, documentation — is intended to ship under
  **CC BY-SA 4.0** once the split lands on this repository as a
  cross-cutting change of its own. Until then, the whole tree is
  Apache-2.0; nothing you contribute now becomes harder to relicense
  later because Apache-2.0 → CC BY-SA 4.0 only requires forward consent,
  not retroactive rewriting.

Contributions are **inbound under the same licence as outbound** for
the path they touch: a change to code paths is offered under
Apache-2.0; a change to content paths is offered under the content
licence as it stands when the change is merged. Your DCO sign-off
(see §5) is your affirmation that you have the right to make that
offer.

If you are unsure which licence applies to a path you are editing,
ask in the pull request before you do the work — that conversation
is cheap and the answer is durable.

[website-repo]: https://github.com/secops-ng/secops-ng-website

## 4. Find something to work on

Open work lives in the [issue tracker][issues], sorted by label:

| Label | What it means |
|---|---|
| [`good first issue`][lbl-gfi] | Scoped for a single sitting, self-contained, no coordination needed. Start here. |
| [`contributor:welcome`][lbl-cw] | Held open for newcomers. A maintainer will walk you through the round-trip. |
| [`help wanted`][lbl-hw] | Larger than a first issue — a few hours to half a day — and usually has a committed precedent in the tree to follow. |
| [`arch`][lbl-arch] | Design decisions. Discussion is welcome; these are usually resolved by maintainers. |

Pick one and comment on it saying you would like to take it, so two
people do not unknowingly do the same work. There is no formal
assignment dance — a comment is enough.

If nothing open fits, opening an issue to propose your own change is
equally welcome. Smaller, sharper proposals merge faster than large
undirected ones.

For a curated menu of contribution *vectors* rather than specific
issues, [`docs/contributing/good-first-issues.md`](docs/contributing/good-first-issues.md)
lists four concrete starting points — a new CACAO playbook, a compiled
example for an existing playbook, a translation, or a walkthrough
improvement — each with the directory to work in, the standards to
satisfy, and the issue template to open.

`ROADMAP.md` is **not** a task board: it is the reviewed registry of
what the framework has shipped and what is proposed next, and every
entry links the goals it moves. Read it to understand why a piece of
work matters, then take the corresponding issue. A roadmap entry marked
`Proposed` is an invitation to discuss, not an unclaimed ticket.

[issues]: https://github.com/secops-ng/secops-ng-framework/issues
[lbl-gfi]: https://github.com/secops-ng/secops-ng-framework/labels/good%20first%20issue
[lbl-cw]: https://github.com/secops-ng/secops-ng-framework/labels/contributor%3Awelcome
[lbl-hw]: https://github.com/secops-ng/secops-ng-framework/labels/help%20wanted
[lbl-arch]: https://github.com/secops-ng/secops-ng-framework/labels/arch

## 5. Open a pull request

Branch from `main`, keep the scope tight, and commit with sign-off:

```bash
git checkout -b feat/short-descriptive-slug
# ... do the work ...
git commit -s -m "feat(workflows): add incident enrichment template"
git push -u origin feat/short-descriptive-slug
```

Conventions worth knowing:

- **Conventional Commits** for the message subject:
  `feat(...)`, `fix(...)`, `docs(...)`, `chore(...)`. The scope in
  parentheses names the surface you touched.
- **DCO sign-off (`-s`) is required on every commit.** It appends
  `Signed-off-by: Your Name <you@example.org>` and certifies that you
  wrote the contribution, or have the right to submit it, under the
  licence that applies to the path. Pull requests without sign-off
  cannot be merged. There is no exception for AI-assisted commits:
  the human committer's sign-off is what counts.
- **Signed commits** (`git commit -S`, GPG/SSH) are required only on
  pull requests that touch a *security-critical surface*. The current
  enumeration of those surfaces lives in [SECURITY.md](SECURITY.md);
  if a CI check rejects your push, that is what it is checking for.
- **Squash noisy fix-up commits** before requesting review.
- **Type hints on all public functions and methods.** `ToolIO` (strict
  Pydantic) is the canonical I/O type at every workflow, activity, and
  tool boundary.

### 5.1 Typed pull-request templates

The PR template asks you to pick a type. Picking the right one sets the
reviewer's expectations and shortens the round-trip:

| Type | When to use it | What the template asks |
|---|---|---|
| **bug-fix** | A behaviour does not match a documented contract, a test catches it, the fix is local. | Failing test or repro; smallest possible diff. |
| **new-content** | A new playbook, control mapping, telemetry shape, KPI/KRI entry, or any other content artifact. | Schema validates; standards lineage cited; example included. |
| **new-feature** | A new primitive, compiler emitter, or public API surface. | Design motivation; alternatives considered; backward-compatibility note. |
| **documentation** | Prose-only changes: clarifications, examples, fixed links. | One-line rationale; affected pages listed. |

If your change does not fit cleanly into one type, that is usually a
sign it should be split into separate PRs.

### 5.2 Conflict-of-interest and funded-contribution disclosure

If a person or organisation paying you would materially benefit from
the change being merged, the PR description must include:

- **`Funded by:`** a one-line note when the contribution originates
  from grant or contract work. The line is informational — funded
  work does not get accelerated review and does not enter a separate
  tree.
- **A COI flag.** If your employer or a client has a material interest
  in the change (a feature they need, a competitor they want
  disadvantaged), say so in two sentences in the PR description. A
  flagged change is reviewed the same way as any other change; the
  flag is for the public record, not for gatekeeping.

A funded contributor may not be the sole approver of a deliverable they
were funded to produce. Routine for grant-supported work; uncommon for
contract work.

## 6. Community norms

SecOps-NG is a **Digital Commons**, not a company and not a product.
The norms below are how the project stays that way in practice.

- **Community language.** The voice on every public surface is
  community, commons, and practitioners — not vendor, services firm,
  or advisory. Avoid buyer vocabulary (leads, prospects, deals,
  pipeline, funnel, price points, market-segment acronyms) and avoid
  money-in framing. [`SOUL.md`](SOUL.md) is the reference; the
  hygiene linter (§4 in [AGENTS.md](AGENTS.md)) encodes the mechanical
  floor.
- **No named organisations as prospects or partners.** Do not attach
  the name of an organisation the maintainers are talking to, or the
  name of an individual at such an organisation, to any file, commit,
  issue, or PR comment. This applies whether the reference is
  flattering or critical — the public history is permanent, and
  attribution creates pressure the project's governance model is
  designed to avoid.
- **Code of conduct.** Participation is governed by
  [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Read it once. The short
  version: be calm, be technical, assume good faith, disagree in
  public, resolve in the thread.
- **Ask for help in public.** Questions about the framework, a
  playbook, a compile target, or a review note belong in **GitHub
  Discussions** or on the issue thread, not in DMs to individual
  maintainers. A public question benefits every future contributor
  who hits the same wall; a DM benefits one person once. If you have
  a genuinely private matter (a security report, a conduct concern,
  a licensing question that names third parties), the escalation
  paths in [`SECURITY.md`](SECURITY.md) and
  [`GOVERNANCE.md`](GOVERNANCE.md) are the way in.
- **DCO sign-off is not optional.** Every commit ships with
  `Signed-off-by:` (via `git commit -s`) per §5. This is the point at
  which you affirm you have the right to contribute the change under
  the licence that applies to the path. AI-assisted commits do not
  change the requirement — the human committer's sign-off is what
  counts.

Reading these once, at the start of your first contribution, makes
none of the later review notes feel personal. They are how the commons
converges.

## 7. The review process

Every pull request to this repository is read by a reviewer in the
**Custodian** role before it can merge. The Custodian is not a
gatekeeper-by-attitude; the role exists because the project's history
is permanent and will one day be public. Once a commit lands on `main`,
it lives there forever — searchable, quotable, attributable. The
Custodian's job is to make sure nothing lands that we will regret later.

In plain terms, the Custodian checks:

- **Forward-public hygiene.** No credentials, secrets, internal
  hostnames, or contact names. No commercial framing, no vendor or
  services-firm voice. No named organisations described as prospects
  or partners. If something reads like it belongs in a private
  operational note, it goes there instead.
- **Voice.** Consistent with `SOUL.md`. Community language, calm and
  technical, no marketing verbs.
- **Code quality.** Tests cover the change, types are honest,
  `ToolIO` boundaries are respected, the diff is focused.
- **Conventional Commits + DCO sign-off** on every commit.

Most reviews end in one of three places: an approval and a merge, a
small set of requested changes that you push as follow-up commits, or
a conversation about scope. None of those are failures — they are how
the commons converges. Expect the first round to surface at least one
phrasing or hygiene note; that is normal even for experienced
contributors, because the public-history bar is genuinely strict.

When the change is approved, a maintainer merges it. You will see your
name in the commit history and, if the change is user-visible, in the
release notes for the next version — cut per
[`docs/contributing/release-process.md`](docs/contributing/release-process.md).

The operational companion to this section —
[`docs/contributing/review-process.md`](docs/contributing/review-process.md)
— walks through what CI runs (the hygiene linter, the test suite),
what CODEOWNERS gates trigger, typical timelines and feedback style,
how to respond to requested changes, and the squash-merge + delete-branch
convention. Read it once before your first review round.

### 7.1 Writing a new playbook

If your contribution scaffolds a new CACAO v2 playbook under
`content/playbooks/`, the operational walkthrough —
[`docs/contributing/playbook-authoring.md`](docs/contributing/playbook-authoring.md)
— covers the directory scaffold, required CACAO fields, the
`mappings.yaml` overlay, what the orphan-CI gate checks, and how to
run the hygiene linter locally. Read it end-to-end before your first
playbook PR.

### 7.2 Adding a compiled example

If your contribution adds a runnable example under
`examples/{n8n,temporal,langgraph}/<playbook>/` for an existing
playbook, the compiler-path walkthrough —
[`docs/contributing/compiler-walkthrough.md`](docs/contributing/compiler-walkthrough.md)
— covers the three reference targets, the shared example directory
layout, the `regenerate.sh` pattern, and the byte-parity golden test
that anchors each example. Compiler-surface changes themselves (new
primitives, new emitters) still go through a scoping issue first.

## 8. Adding or editing a playbook

Playbooks live under `content/playbooks/<slug>/` and follow a fixed
per-directory layout:

| File | Required | Holds |
|------|----------|-------|
| `playbook.cacao.json` | yes | the canonical CACAO v2 source (a `playbook.cacao.yaml` source is also accepted — five shipped playbooks use it) |
| `mappings.yaml` | yes | the outbound OSCAL / D3FEND / OCSF / regulatory overlay |
| `README.md` | yes | workflow-local overview and status |
| `examples/` | no | worked-example material, where the playbook ships any |

New playbooks MUST start by copying the template, which carries every
required file with each field annotated:

```bash
cp -r content/playbooks/_template content/playbooks/<slug>
```

The step-by-step walkthrough — choosing a slug, converting the scaffold
to canonical JSON, adding your first mapping entry, and running the
linter and tests locally — is
[`docs/contributing/playbook-quickstart.md`](docs/contributing/playbook-quickstart.md).
Read it before your first content pull request.

Pull requests that are missing a required file, or that leave required
files as `TODO` stubs, are rejected. A `_template`-conformance linter
runs in CI, so a scaffold left half-filled fails before review.

## 9. Proposing larger changes

Most changes do not need a formal proposal — an issue plus a PR is
enough. When a change is *cross-cutting* — touching public APIs,
breaking artifact shapes, the sovereignty posture, the licence
structure, this document, `GOVERNANCE.md`, or `CODE_OF_CONDUCT.md` —
open an issue first that describes the motivation, alternatives
considered, and the impact on existing users. The pull request links
to that issue.

A heavyweight RFC document type may be introduced in `docs/rfcs/` once
the project's scale justifies the ceremony. It does not exist yet
because the project does not need it yet. The trigger for introducing
it is documented in [GOVERNANCE.md §4](GOVERNANCE.md).

## 10. Reporting security issues

Please do **not** open public issues for vulnerabilities. See
[SECURITY.md](SECURITY.md) for the disclosure process.

## 11. Code of conduct and governance

Participation in this project is governed by
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). How decisions are made —
proposals, consent, chapter leads, escalation, and the threshold at
which a steering group is constituted — is documented in
[GOVERNANCE.md](GOVERNANCE.md). Both are short. Reading them now
means you will not be surprised later.

Welcome to the commons. We are glad you are here.
