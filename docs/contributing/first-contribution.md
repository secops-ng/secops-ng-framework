# Your first contribution

Welcome. This walkthrough takes you from a fresh clone to an open pull
request. It is deliberately short and concrete. If you have already read
`CONTRIBUTING.md` at the repository root, this page is the operational
companion — the exact commands, in order.

Every commit in this repository is public the moment it lands. The
project is a Digital Commons for sovereign security operations in the
EU. That framing sets the voice; the hygiene linter enforces a floor.
Neither is a hazing ritual — both exist because the git history is
permanent and searchable.

## 1. Pick an issue

Open the [issue tracker][issues] and filter to
[`good first issue`][lbl-gfi] or [`contributor:welcome`][lbl-cw]. Those
are scoped to a single sitting and self-contained enough that you do not
need to coordinate with anyone before starting. [`help wanted`][lbl-hw]
is the next step up once you have landed one.

Comment on the issue saying you would like to take it, so two people do
not unknowingly do the same work. A single comment is enough — there is
no formal assignment step.

[`ROADMAP.md`](../../ROADMAP.md) is worth reading for context on why a
piece of work matters, but it is a registry of shipped and proposed
features rather than a list of open tasks — take the issue, not the
roadmap entry.

[issues]: https://github.com/secops-ng/secops-ng-framework/issues
[lbl-gfi]: https://github.com/secops-ng/secops-ng-framework/labels/good%20first%20issue
[lbl-cw]: https://github.com/secops-ng/secops-ng-framework/labels/contributor%3Awelcome
[lbl-hw]: https://github.com/secops-ng/secops-ng-framework/labels/help%20wanted

If nothing open fits your interest, opening a
[Playbook request](../../.github/ISSUE_TEMPLATE/playbook-request.yml)
or a
[Good first issue](../../.github/ISSUE_TEMPLATE/good-first-issue.yml)
of your own is equally welcome. Smaller, sharper proposals merge faster
than large undirected ones.

## 2. Fork and clone

Fork [`secops-ng/secops-ng-framework`](https://github.com/secops-ng/secops-ng-framework)
on GitHub, then clone your fork locally:

```bash
git clone git@github.com:<your-username>/secops-ng-framework.git
cd secops-ng-framework
git remote add upstream https://github.com/secops-ng/secops-ng-framework.git
```

Keep `main` on your fork tracking upstream:

```bash
git fetch upstream
git checkout main
git merge --ff-only upstream/main
```

## 3. Set up the toolchain

The repository uses a plain Python virtualenv plus the project's own
dev extras. Any modern Python 3.11+ interpreter works.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # local only; never commit .env
```

Sanity-check that the toolchain works before you write anything:

```bash
python -m pytest
python -m tools.hygiene_linter --min-severity LOW
```

Green locally is the baseline. CI runs the same checks on every pull
request.

## 4. Branch from `main`

Branch naming is `<area>/<short-description>`. Examples:

- `docs/foundation-clarifications`
- `content/dora-notification-playbook`
- `compilers/n8n-array-handling`
- `tests/posture-audit-golden`

```bash
git checkout -b docs/your-short-description
```

Keep the branch focused. One card, one branch, one pull request. If you
discover a second unrelated fix while working, hold it for a follow-up
branch — smaller PRs merge faster and are easier to review.

## 5. Do the work

Two rules apply to every file you touch:

- **Voice.** Read [`SOUL.md`](../../SOUL.md) once before writing anything
  that will be public-facing (documentation, playbook prose, comments
  in content files). Community and commons framing, calm and technical,
  no vendor or services-firm language.
- **Hygiene.** No credentials, internal hostnames, contact names, or
  named organisations described as prospects or partners. The linter
  in the next step enforces a floor.

For content changes, the source of truth for shape and structure is the
existing cookbook under `docs/cookbook/`. Mirror the tone and heading
depth of a page you like.

For code changes, keep the diff scoped: honest types, `ToolIO` at
workflow and tool boundaries, and tests that fail before your change
and pass after it.

## 6. Run tests and the hygiene linter locally

Before you push:

```bash
python -m pytest
python -m tools.hygiene_linter --min-severity LOW
```

Both must pass. The hygiene linter has two severity gates:

- `HIGH` findings (credential-shaped strings) block merge outright.
- `MEDIUM` findings (commercial language) are reviewed by a maintainer
  and usually mean a phrasing rewrite.

If the linter flags something you believe is a false positive, leave
the finding in place and mention it in the pull request description —
do not silence rules to make CI happy.

There is an inline `hygiene-linter: allow <rule-id>` pragma, but it
exists for a narrow case that is unlikely to be yours: a file that must
contain the vocabulary a rule detects, such as a rule definition or
`SOUL.md` quoting the phrasing it warns against. It cannot suppress a
`HIGH` credential finding at all. Reach for a rewrite first and the
pragma essentially never — see
[`hygiene-linter.md`](./hygiene-linter.md) for when it is legitimate.

## 7. Commit with sign-off

Every commit needs a
[DCO](https://developercertificate.org/) sign-off:

```bash
git add <files>
git commit -s -m "docs(contributing): add first-contribution walkthrough"
```

The `-s` flag appends `Signed-off-by: Your Name <you@example.org>` to
the commit message. That line certifies you wrote the change, or have
the right to submit it, under the licence that applies to the path.
Pull requests without sign-off cannot be merged.

Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org/):
`docs(...)`, `feat(...)`, `fix(...)`, `chore(...)`. The parenthesised
scope names the surface you touched.

## 8. Push and open a pull request

Push the branch to your fork:

```bash
git push -u origin docs/your-short-description
```

Then open a pull request against `secops-ng/secops-ng-framework:main`.
The PR template will ask you to pick a type — `bug-fix`, `new-content`,
`new-feature`, or `documentation` — and to acknowledge the hygiene
bar. Both are required. Fill in the description with a one-paragraph
summary and a link to the issue you took.

CI will run the test suite and the hygiene linter. Fix any failures
locally and push follow-up commits to the same branch; no need to open
a new PR.

## 9. What review looks like

A reviewer in the Custodian role reads every PR before it can merge.
The checks are documented in
[`CONTRIBUTING.md` §6](../../CONTRIBUTING.md); in plain terms:
forward-public hygiene, voice, code quality, and Conventional Commits
plus DCO on every commit.

Expect at least one round of phrasing or hygiene notes on your first
PR. That is normal, not a signal that something is wrong. Push
follow-up commits to the same branch as you address feedback; a
maintainer squashes on merge.

When your change is approved and merged, you will see your name in the
commit history and, if the change is user-visible, in the release notes
for the next version. Welcome to the commons.

## Where to go next

- [`CONTRIBUTING.md`](../../CONTRIBUTING.md) — the full contributor guide.
- [`SOUL.md`](../../SOUL.md) — voice reference.
- [`docs/FOUNDATION.md`](../FOUNDATION.md) — the four non-negotiable properties.
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — the four-layer runtime.
- [`docs/contributing/hygiene-linter.md`](./hygiene-linter.md) — how the linter works.
- [`docs/contributing/byte-parity-testing.md`](./byte-parity-testing.md) — golden-test conventions for compiler changes.
