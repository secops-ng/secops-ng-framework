# Forward-public hygiene linter

The hygiene linter is the cheap first gate for content shipping to a
public repo. It scans staged files for the syntactic class of
leaks — credential shapes, `.env`-style assignments, high-entropy
tokens — and a defensive subset of commercial-intent / strategy
language patterns. Semantic and tone review remains with the human
reviewer (AGENTS.md §5 directive 7).

Scope is explicitly MVP. The linter does **not** replace gitleaks /
detect-secrets / Custodian review; it lives in-repo so it has zero
install footprint and can be invoked from any contributor laptop
without a network round-trip.

## Running locally

From the repo root:

```bash
# Scan the whole working tree (default):
python -m tools.hygiene_linter

# Scan a specific path:
python -m tools.hygiene_linter docs/

# JSON output (for tooling integration):
python -m tools.hygiene_linter --format json

# Treat MEDIUM findings as build-blocking too:
python -m tools.hygiene_linter --gate-severity MEDIUM

# Hide MEDIUM and LOW from the report:
python -m tools.hygiene_linter --min-severity HIGH

# Exclude a path glob (repeatable):
python -m tools.hygiene_linter --exclude 'docs/legacy/*'
```

Exit codes:

- `0` — no findings at or above the gating severity (default: `HIGH`).
- `1` — at least one gating-severity finding.
- `2` — CLI usage error.

The linter is pure-stdlib Python; no install step is required beyond
the Python interpreter the framework already targets.

## Severity model

| Severity | Meaning | Default gating? |
|----------|---------|-----------------|
| `HIGH`   | Credential-shape match. Committing this is a hard leak that git history will preserve forever. | Yes — non-zero exit. |
| `MEDIUM` | Commercial / strategy language patterns. Strong signal of content that belongs in the private repo, but context-dependent. | No — warning only. |
| `LOW`    | Reserved for future use. | No. |

The asymmetry is deliberate: credential leaks are irreversible on a
public repo, so we accept some false-positive cost. Commercial-language
matches are context-dependent, so they surface as warnings the
reviewer should resolve before merge but do not block the build on
their own.

## CI integration

The repo runs `python -m tools.hygiene_linter` on every PR and every
push to `main` via `.github/workflows/hygiene-lint.yml`. The job
excludes `tests/hygiene_linter/*` because those files contain
intentional positive fixtures and literal test inputs for the rules
under test.

## Adding a new rule

Rules live under `tools/hygiene_linter/rules/`. Each rule is a single
Python module exposing a `scan(path, lines) -> Iterable[Finding]`
function:

```python
# tools/hygiene_linter/rules/my_rule.py
from __future__ import annotations
import re
from typing import Iterable, List
from tools.hygiene_linter.findings import Finding, Severity

_PATTERN = re.compile(r"\\bforbidden-pattern\\b")

def scan(path: str, lines: List[str]) -> Iterable[Finding]:
    for i, line in enumerate(lines, start=1):
        m = _PATTERN.search(line)
        if m:
            yield Finding(
                path=path, line=i,
                rule="my_rule.example",
                severity=Severity.HIGH,
                message="forbidden-pattern appeared in a public file",
                snippet=m.group(0),
            )
```

To activate the rule:

1. Add a positive fixture under
   `tests/hygiene_linter/fixtures/` that the rule should fire on.
2. Add a negative fixture that the rule should ignore (to guard
   against regex over-matching).
3. Register the module in `tools/hygiene_linter/rules/__init__.py`:

```python
from tools.hygiene_linter.rules import my_rule  # noqa: F401, E402

RULES: list[RuleFn] = [
    credentials.scan,
    commercial.scan,
    my_rule.scan,
]
```

4. Add a positive and a negative unit test alongside the others in
   `tests/hygiene_linter/test_hygiene_linter.py`.

## Rule design conventions

- **Use word boundaries.** Bare-substring matches generate false
  positives in code comments and unrelated prose.
- **Redact match snippets.** Never log a candidate secret in full —
  use `tools.hygiene_linter.findings.redact` so the linter does not
  itself become a leak channel.
- **Reserve HIGH for irreversible leaks.** Anything context-dependent
  belongs at MEDIUM. Reviewers will tune out a noisy gate.
- **Stay offline.** No network calls, no third-party deps — pure
  Python standard library. Sovereignty posture requires this.
- **Pure functions.** Rule scanners are side-effect-free; they take
  inputs and yield findings. No global state, no file I/O.

## Relationship to gitleaks / detect-secrets

Per the forward-public hygiene linter brief, the steady-state stack
will eventually be `gitleaks` (primary) + `detect-secrets`
(secondary) with project-specific rule packs. This in-repo Python
linter is the **bootstrap** layer: it lands the policy gate
immediately without depending on contributor-side binary installs or
on the eventual CI provider ruling. The Python linter and gitleaks
are complementary — the Python linter owns project-specific patterns
(commercial language, future house-style rules) while gitleaks will
own the broad credential pattern catalogue and entropy analysis.

The two layers can co-exist; nothing in the design requires choosing
one or the other.
