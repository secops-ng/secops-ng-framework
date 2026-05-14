# Contributing to SecOps-NG

Thanks for considering a contribution. SecOps-NG is a digital commons —
community-driven, non-commercial, Apache-2.0. Patches, bug reports,
documentation, and discussion are all welcome.

## Development setup

```bash
git clone https://github.com/secops-ng/secops-ng-framework.git
cd secops-ng-framework
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # edit as needed; do NOT commit
```

## Running checks

```bash
pytest            # unit + smoke tests
ruff check .      # lint
ruff format .     # auto-format
mypy src          # type-check
```

CI runs the same set. Please make sure each is clean before opening a PR.

## Code style

- Ruff is the source of truth for formatting and lint rules
  (configured in `pyproject.toml`).
- Type hints are required on all public functions and methods.
- `secops_ng.tool_io.ToolIO` (strict Pydantic) is the canonical I/O type
  at every workflow / activity / tool boundary.

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(workflows): add incident enrichment template
fix(contracts): reject empty CVE strings
docs(readme): clarify sovereignty stance
chore: bump temporalio to 1.7.1
```

Keep commits focused. Squash noisy fix-up commits before requesting review.

## DCO sign-off (required)

Every commit must carry a Developer Certificate of Origin sign-off:

```bash
git commit -s -m "feat(activities): add CMDB lookup activity"
```

This appends `Signed-off-by: Your Name <you@example.org>` and certifies
that you wrote (or have the right to submit) the contribution under
Apache-2.0. PRs without DCO sign-off cannot be merged.

## Code of conduct

All participation is governed by the project
[Code of Conduct](CODE_OF_CONDUCT.md), adapted from the
[Contributor Covenant, version 2.1][cc-2.1]. Reports of unacceptable
behaviour go to the stewards at **conduct@secops-ng.com**.

[cc-2.1]: https://www.contributor-covenant.org/version/2/1/code_of_conduct.html

## Governance

How decisions get made, who has merge rights, and how that is expected
to evolve is documented in [GOVERNANCE.md](GOVERNANCE.md). The short
version: lazy consensus among maintainers, with the Code of Conduct
enforced by a steward group.

## Reporting security issues

Please do **not** open public issues for vulnerabilities. See
[SECURITY.md](SECURITY.md) for the disclosure process.
