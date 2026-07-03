# The review process

This page walks through what happens after you open a pull request against
`secops-ng-framework`, from CI landing to merge. It is the operational
companion to §6 of [`CONTRIBUTING.md`](../../CONTRIBUTING.md) — that
section describes *what* the Custodian reviews for; this page describes
*how* the pipeline runs around it.

Read it before your first PR so nothing on the round-trip is a surprise.

## 1. What runs in CI

Every pull request against `main` triggers a small set of GitHub Actions
jobs. The two you will interact with most:

### 1.1 The forward-public hygiene linter

`.github/workflows/hygiene-lint.yml` runs
`python -m tools.hygiene_linter` against the whole tree. See
[`docs/contributing/hygiene-linter.md`](hygiene-linter.md) for the rule
catalogue.

Two severities matter for review flow:

- **HIGH** — credential-shaped strings (API keys, tokens, private-key
  blocks, secret-shaped patterns). HIGH findings fail the job and block
  merge. There is no exception path — rotate the secret if it was real,
  scrub the diff, force-push a clean history to your branch, and push
  again.
- **MEDIUM** — commercial-language hits (vendor / services-firm voice,
  buyer vocabulary, funnel/pipeline framing). MEDIUM findings do *not*
  block CI by default, but they are surfaced to the reviewer and almost
  always come back as requested changes. Rework them client-side before
  requesting review — a MEDIUM you land on the first pass shortens the
  round-trip.

Run the linter locally before you push:

```bash
python -m tools.hygiene_linter --min-severity LOW
```

`--min-severity LOW` shows everything the linter knows about, including
advisory notes that CI would not fail on. Fixing LOWs is optional but
it is the cheapest time to do it.

### 1.2 The test suite

`python -m pytest` from the repo root runs unit, integration, and
per-example byte-parity golden tests. Green locally is the baseline; the
CI lane runs the same set and any red job blocks merge.

Compiler changes almost always cascade into per-example golden updates
under `tests/examples/` — expect that, regenerate the affected examples
in the same PR, and note the regenerate step in your PR description so
the reviewer does not have to guess whether the golden churn is
intentional.

## 2. CODEOWNERS gates

`.github/CODEOWNERS` assigns default review to the
`@secops-ng/maintainers` GitHub team on every path, with two path-scoped
overrides that make the requirement explicit:

- `/content/playbooks/` — every CACAO playbook change lands on `main`
  forever and is compiled by all three reference targets, so a
  maintainer review is required.
- `/content/mappings/` — cross-framework regulatory mappings (CRA,
  DORA, GDPR, NIS2, OSCAL, D3FEND). Changes here shift the G-02 KRI
  and the orphan-CI graph, so a maintainer must be on the review.

GitHub auto-requests review from the maintainer team when your PR
touches a matching path. You do not have to tag anyone by hand. If
your change touches only documentation or tooling, the default rule
still requests the team — a maintainer will pick it up in the review
queue.

The file is a floor, not a ceiling: any maintainer may review any PR,
and any contributor may leave review comments. What CODEOWNERS
guarantees is that at least one maintainer sees a permanent-history
change before it merges.

## 3. Typical review timeline

There is no SLA on the maintainer team, and the project deliberately
does not run a triage rota. In practice:

- Small, well-scoped documentation and content PRs usually see a first
  review within a few days.
- Compiler or cross-cutting changes take longer, because the reviewer
  is checking sovereignty-stack alignment and byte-parity across three
  emitters.
- If a PR sits with no comment for over a week and CI is green, it is
  reasonable to leave a single follow-up comment asking whether
  anything is blocking review. One nudge is fine; repeated nudges are
  not.

Reviewers do not accelerate `Funded by:` or COI-flagged PRs. The
disclosure is for the public record, not for the queue order.

## 4. Feedback style

Reviews are calm, technical, and specific. Expect:

- **Inline comments on the diff** for concrete phrasing, code, or
  test issues. Each comment points at exactly one line or block.
- **A top-level review comment** summarising the round: what is good,
  what needs changes, what is optional.
- **Questions, not directives**, for anything that is a judgment call
  — sovereignty posture, voice, scope. The reviewer is not the
  gatekeeper of a house style; the reviewer is a peer flagging drift.

If you disagree with a review note, say so in the thread. A short,
specific disagreement ("this phrasing is intentional because …") is
part of how the commons converges. Reviewers back down when the
contributor has the better argument; the point is not to win the
review, it is to land the change well.

## 5. Responding to requested changes

Push follow-up commits to the same branch. Do not squash locally
between review rounds — reviewers navigate by the commit-level diff,
and squashing mid-review makes their re-read harder. The merge itself
squashes (see §6), so noisy fix-up commits are cheap on your branch
and cost nothing in `main`.

When you have addressed a batch of comments:

1. Mark each resolved comment thread resolved on GitHub.
2. Leave a one-line reply on any thread where you did something
   different from what was asked, explaining why.
3. Re-request review through the GitHub UI.

If a reviewer's request would materially change the scope of the PR,
raise that in the thread rather than doing the work silently. Scope
drift is one of the two most common reasons a PR stalls; the other is
CI red left unaddressed.

## 6. The merge path

When the review is complete and the CI lane is green, a maintainer
merges. The convention on this repository:

- **Squash merge.** The PR becomes a single commit on `main`. The
  squash commit message is the PR title plus the PR body summary —
  reviewers pay attention to both because that is what shows up in
  the public history and in release notes.
- **Delete the branch after merge.** GitHub is configured to prompt
  for branch deletion on merge; take the prompt. Long-lived branches
  on `origin` pile up quickly and hide which work is in flight.
- **No merge commits.** The `main` history is linear on purpose:
  every commit is a shipped change, one-to-one with a merged PR.

You will see the squash commit in the history under your name; if the
change is user-visible, you will see it in the release notes for the
next version.

## 7. If something goes wrong after merge

Regressions happen. The path is:

1. Open an issue naming the regression and linking the merged PR.
2. Open a follow-up PR that either forward-fixes the behaviour or
   reverts the offending commit. Reverts are commits like any other
   — they need sign-off and a normal review.
3. If the regression is a hygiene or credential leak on a public
   surface, follow [`SECURITY.md`](../../SECURITY.md) instead of
   opening a public issue.

`main` is never rewritten. History is permanent because that is the
promise a Digital Commons makes to the people who rely on it.
