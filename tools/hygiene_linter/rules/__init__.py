"""Rule modules for the hygiene linter.

Each rule module exposes a single ``scan(path, lines)`` callable that
takes a file path (for reporting only) and the file content split into
lines, and yields :class:`Finding` objects.

Adding a rule:

1. Create ``tools/hygiene_linter/rules/<name>.py`` with a ``scan``
   function matching the ``RuleFn`` protocol below.
2. Append the module to :data:`RULES`.
3. Add a positive and a negative fixture under
   ``tests/hygiene_linter/fixtures/``.

Rules MUST be pure-Python, fully offline, and side-effect-free.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from tools.hygiene_linter.findings import Finding

RuleFn = Callable[[str, list[str]], Iterable[Finding]]

from tools.hygiene_linter.rules import commercial, credentials  # noqa: E402

RULES: list[RuleFn] = [
    credentials.scan,
    commercial.scan,
]

__all__ = ["RULES", "RuleFn"]
