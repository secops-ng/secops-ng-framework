# Contributing to SecOps-NG

Welcome. SecOps-NG is a Digital Commons for sovereign security operations
in the EU. The work here belongs to the people doing it and to the
community that relies on it — not to any one organisation. If you have
made it this far, you already belong here.

This document walks you through your first contribution end-to-end:
from cloning the repository to seeing your change reviewed and merged.
Read it once before you start. It is short on purpose.

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
that lands in a will-be-public repository carries the same standard.
The shortest summary: we are a commons, not a vendor; sovereignty is a
public good, not a selling point; "we" for the project, "you" for the
reader, never "I" or "the company."

If a phrasing question comes up while you work, `SOUL.md` is the
reference. When in doubt, ask in the pull request — that conversation
itself is part of how the commons learns its own voice.

## 3. Find a good-first card on the public roadmap

The public roadmap is rendered from the open kanban board and lives in
the repository as `ROADMAP.md`. Cards tagged `good-first` are scoped to
be approachable in a single sitting and self-contained enough that you
do not need to coordinate with anyone before starting.

Pick one. Comment on the linked issue saying you would like to take it
so two people do not unknowingly do the same work. There is no formal
assignment dance — a comment is enough.

If nothing on the board fits, opening an issue to propose your own
change is equally welcome. Smaller, sharper proposals merge faster than
large undirected ones.

## 4. Open a pull request

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
  wrote the contribution, or have the right to submit it, under
  Apache-2.0. Pull requests without sign-off cannot be merged.
- **Squash noisy fix-up commits** before requesting review.
- **Type hints on all public functions and methods.** `ToolIO` (strict
  Pydantic) is the canonical I/O type at every workflow, activity, and
  tool boundary.

In the pull request description, link the issue you are closing and say
in two or three sentences what changed and why. If you are uncertain
about an approach, mark the PR as draft and ask — early questions are
cheaper than late rewrites.

## 5. What review looks like

Every pull request to this repository is read by a reviewer in the
**Custodian** role before it can merge. The Custodian is not a
gatekeeper-by-attitude; the role exists because the project's history
is permanent and will one day be public. Once a commit lands on `main`,
it lives there forever — searchable, quotable, attributable. The
Custodian's job is to make sure nothing lands that we will regret later.

In plain terms, the Custodian checks:

- **Forward-public hygiene.** No credentials, secrets, internal
  hostnames, or contact names. No commercial or consulting framing. No
  named organisations described as prospects or partners. If something
  reads like it belongs in a private operational note, it goes there
  instead.
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
release notes for the next version.

## Reporting security issues

Please do **not** open public issues for vulnerabilities. See
`SECURITY.md` for the disclosure process.

## Code of conduct and governance

Participation in this project is governed by `CODE_OF_CONDUCT.md`. How
decisions are made — proposals, consent, escalation — is documented in
`GOVERNANCE.md`. Both are short. Reading them now means you will not be
surprised later.

Welcome to the commons. We are glad you are here.
