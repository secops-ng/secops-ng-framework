# Pull request

Thanks for contributing to SecOps-NG. Before you open this PR, please skim
[`SOUL.md`](https://github.com/secops-ng/secops-ng-framework/blob/main/SOUL.md)
for project voice and tone, and walk the
[`CONTRIBUTING.md`](https://github.com/secops-ng/secops-ng-framework/blob/main/CONTRIBUTING.md)
guide for setup, checks, commit style, and DCO sign-off. (Full URLs on
purpose: relative links break once this template becomes a PR body.)

## Summary

<!-- One or two sentences: what does this change and why? -->

## Related issues

<!-- e.g. closes #123, refs #456 -->

## Pre-flight checklist

- [ ] Local verification passes: `python -m pytest` and
      `python -m tools.hygiene_linter --min-severity LOW`. For a docs-
      or content-only change, the linter plus pytest scoped to the
      touched surface is fine — CI runs the full suite regardless.
- [ ] No secrets, credentials, or `.env` files are committed.
- [ ] No third-party organisations or individuals are named as prospects,
      customers, or leads anywhere in the diff or PR description.
- [ ] Voice matches
      [`SOUL.md`](https://github.com/secops-ng/secops-ng-framework/blob/main/SOUL.md)
      — community-driven, sovereign, non-commercial.
- [ ] Commits are signed off with DCO (`git commit -s`).

## Notes for reviewers

<!-- Anything that needs context: design choices, follow-ups, open
     questions, areas you want extra eyes on. -->
