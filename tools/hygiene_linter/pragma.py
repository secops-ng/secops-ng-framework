# hygiene-linter: allow-file commercial.sales_language,commercial.pricing_language
"""Inline suppression pragmas for the hygiene linter.

Some files must contain the vocabulary the linter detects. A
``commercial.*`` rule definition necessarily spells out the sales and
pricing terms it matches, and ``SOUL.md`` quotes the phrasing it instructs
against. Before this, those files stood as 15 permanent MEDIUM findings —
a floor a reviewer had to remember was "normal", which is exactly the sort
of floor that hides the sixteenth finding.

The alternative was excluding both paths wholesale, and that was rejected
in #892: ``rules/`` is production code where a genuine leak would matter,
and a path exclusion is invisible at the point it applies. A pragma sits
next to the thing it exempts, names the rule it exempts, and shows up in
review as part of the diff.

Two forms, both matched anywhere in a line so every comment style works.

**Line-scoped** — for a one-off legitimate use inside otherwise ordinary
prose or code::

    # hygiene-linter: allow commercial.sales_language           (Python)
    <!-- hygiene-linter: allow commercial.pricing_language -->  (Markdown)

It suppresses matching findings on **its own line** and on the **line
immediately after**, so it can sit inline or on the line above when the
target line has no room.

**File-scoped** — for a file that contains the vocabulary *by
construction*, where a per-line pragma would mean the same redundant
comment a dozen times::

    # hygiene-linter: allow-file commercial.sales_language,commercial.gtm_language

The rule-definition modules are the motivating case: a ``sales_language``
pattern cannot avoid spelling out the sales vocabulary. A file-scoped
pragma must appear within the first ``_HEADER_LINES`` lines, so it lives
in the header where a reader meets it rather than buried mid-file.

Both forms require **exact rule ids**. There is no wildcard and no
whole-file amnesty: a pragma names the rules it exempts and nothing else,
so adding a new rule cannot be silenced by an existing pragma, and a
reviewer can see precisely what was waived.

**HIGH findings are never suppressible, by either form.** Credential leaks
are irreversible on a public repo — the severity model accepts
false-positive cost for exactly that reason — so a pragma naming a
credentials rule is inert. Test corpora that must hold real-shaped
credentials are handled by path exclusion instead (see
``_DEFAULT_EXCLUDE_PATHS`` in ``cli``).
"""

from __future__ import annotations

import re

from tools.hygiene_linter.findings import Finding, Severity

# Rule ids are ``<module>.<suffix>`` — lowercase, underscores, one dot.
_IDS = r"[a-z0-9_]+\.[a-z0-9_]+(?:\s*,\s*[a-z0-9_]+\.[a-z0-9_]+)*"
_LINE_RE = re.compile(rf"hygiene-linter:\s*allow\s+({_IDS})")
_FILE_RE = re.compile(rf"hygiene-linter:\s*allow-file\s+({_IDS})")

# A file-scoped pragma is only honoured inside the file header, so it cannot
# be buried somewhere a reader will not meet it.
_HEADER_LINES = 20

# A pragma may never suppress these severities, whatever it names.
_UNSUPPRESSABLE = frozenset({Severity.HIGH})


def _ids(raw: str) -> set[str]:
    return {part.strip() for part in raw.split(",") if part.strip()}


def parse_pragmas(lines: list[str]) -> tuple[dict[int, frozenset[str]], frozenset[str]]:
    """Return (line-scoped allowances, file-scoped allowances).

    A line-scoped pragma on line *n* registers its rule ids for line *n*
    and line *n + 1*, so it works inline or on the line above. A
    file-scoped pragma registers for the whole file, but only when it
    appears within the first ``_HEADER_LINES`` lines.
    """
    per_line: dict[int, set[str]] = {}
    whole_file: set[str] = set()
    for i, line in enumerate(lines, start=1):
        if (m := _FILE_RE.search(line)) is not None:
            if i <= _HEADER_LINES:
                whole_file.update(_ids(m.group(1)))
            # A file-scoped pragma below the header is ignored rather than
            # downgraded to line scope — silently narrowing it would leave
            # the author believing the whole file was covered.
            continue
        if (m := _LINE_RE.search(line)) is not None:
            ids = _ids(m.group(1))
            for target in (i, i + 1):
                per_line.setdefault(target, set()).update(ids)
    return {k: frozenset(v) for k, v in per_line.items()}, frozenset(whole_file)


def is_suppressed(
    finding: Finding,
    per_line: dict[int, frozenset[str]],
    whole_file: frozenset[str] = frozenset(),
) -> bool:
    """True when a pragma exempts this finding.

    HIGH findings are never suppressed, so a mis-scoped or over-broad
    pragma cannot hide a credential leak.
    """
    if finding.severity in _UNSUPPRESSABLE:
        return False
    if finding.rule in whole_file:
        return True
    return finding.rule in per_line.get(finding.line, frozenset())


def apply(findings: list[Finding], lines: list[str]) -> list[Finding]:
    """Drop findings a pragma in the same file exempts."""
    per_line, whole_file = parse_pragmas(lines)
    if not per_line and not whole_file:
        return findings
    return [f for f in findings if not is_suppressed(f, per_line, whole_file)]
