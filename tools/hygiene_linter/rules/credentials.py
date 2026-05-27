"""Credential-shape detection rules.

Catches the common syntactic credential leaks: AWS access keys, GitHub
tokens, PEM private-key blocks, ``KEY=value`` assignments where the
value looks high-entropy, and generic high-entropy tokens on a line.

All severities are HIGH because a single committed credential cannot
be un-leaked from git history once pushed to a public remote.

The detectors are deliberately conservative on the high-entropy path —
real secrets are dense and at least 20 chars; shorter or low-entropy
strings are skipped to keep false-positive noise off the contributor's
plate. The Custodian baseline workflow handles the remaining noise.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable

from tools.hygiene_linter.findings import Finding, Severity, redact

# --- Specific credential shapes ---------------------------------------------

# AWS access key id: AKIA / ASIA / AGPA + 16 alnum. Strict literal prefix
# avoids false positives on random 20-char tokens.
_AWS_ACCESS_KEY = re.compile(r"\b(AKIA|ASIA|AGPA|AIDA|AROA)[0-9A-Z]{16}\b")

# GitHub fine-grained / classic / OAuth tokens. Length lower-bounded
# defensively; the real shapes are 40+ chars.
_GH_TOKEN = re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,255})\b")

# PEM private-key block opener — any variant.
_PEM_HEADER = re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----")

# Slack tokens.
_SLACK_TOKEN = re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")

# Generic .env-style assignment: KEY=value with NO spaces around `=` —
# this is the canonical .env / shell-export shape. Python constants use
# spaces around `=` by PEP 8, so requiring no-spaces strips the bulk of
# the false positives without missing real .env leaks.
_ENV_ASSIGN_TIGHT = re.compile(
    r"""
    (?:^|[\s;])                      # line/separator boundary
    (?:export\s+)?                   # optional `export ` prefix
    ([A-Z][A-Z0-9_]{2,})             # KEY (>=3 chars, allcaps_snake)
    =                                # =, no surrounding whitespace
    ["']?                            # optional opening quote
    ([A-Za-z0-9+/=_\-./~]{12,})      # value (12+ chars, secret-shaped)
    ["']?                            # optional closing quote
    \s*$                             # to end of line
    """,
    re.VERBOSE,
)

# Python-style constant assignment with spaces — only flagged when the
# KEY is in the secret-named list. Slug-shaped values (containing `-`
# or `/`) are skipped because they're identifiers, not secrets.
_PY_ASSIGN_LOOSE = re.compile(
    r"""
    ^\s*                             # leading indent ok
    ([A-Z][A-Z0-9_]{2,})             # KEY (>=3 chars, allcaps_snake)
    \s+=\s+                          # = with surrounding whitespace
    ["']                             # require opening quote (string literal)
    ([^"'\n]{8,})                    # value (8+ chars)
    ["']                             # closing quote
    """,
    re.VERBOSE,
)


def _is_slug_shaped(value: str) -> bool:
    """Slug-shaped values (`my-task-queue`, `openai/gpt-4o`) are
    identifiers, not secrets. Hyphens and slashes are the giveaway."""
    return "-" in value or "/" in value

# Keys whose values being committed is a leak regardless of entropy.
_SECRET_KEYS = re.compile(
    r"^(?:.*_)?(?:"
    r"SECRET|TOKEN|PASSWORD|PASSWD|API_KEY|APIKEY|PRIVATE_KEY|"
    r"ACCESS_KEY|CLIENT_SECRET|AUTH_TOKEN|BEARER"
    r")(?:_.*)?$",
    re.IGNORECASE,
)


def _shannon_entropy(s: str) -> float:
    """Shannon entropy in bits per char for a string."""
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _looks_like_secret_value(value: str) -> bool:
    """Heuristic: long-ish, high-entropy, not an obvious placeholder."""
    if len(value) < 20:
        return False
    if _is_obvious_placeholder(value):
        return False
    # require mixed character classes — pure words are not secret-shaped
    if value.isalpha() or value.isdigit():
        return False
    return _shannon_entropy(value) >= 3.5


def _is_obvious_placeholder(value: str) -> bool:
    """Heuristic: value is clearly a documentation placeholder, not a
    real secret. Used to suppress findings on doc-example lines."""
    lowered = value.lower()
    placeholders = (
        "changeme", "example", "your-", "your_", "xxxxxxxx",
        "placeholder", "fixme", "todo", "redacted", "dummy",
        "local-", "<", ">",
    )
    return any(p in lowered for p in placeholders)


def scan(path: str, lines: list[str]) -> Iterable[Finding]:
    for i, line in enumerate(lines, start=1):
        # AWS access key id
        m = _AWS_ACCESS_KEY.search(line)
        if m:
            yield Finding(
                path=path, line=i,
                rule="credentials.aws_access_key",
                severity=Severity.HIGH,
                message="AWS access key id literal — never commit",
                snippet=redact(m.group(0)),
            )

        # GitHub tokens
        m = _GH_TOKEN.search(line)
        if m:
            yield Finding(
                path=path, line=i,
                rule="credentials.github_token",
                severity=Severity.HIGH,
                message="GitHub token literal — never commit",
                snippet=redact(m.group(0)),
            )

        # Slack tokens
        m = _SLACK_TOKEN.search(line)
        if m:
            yield Finding(
                path=path, line=i,
                rule="credentials.slack_token",
                severity=Severity.HIGH,
                message="Slack token literal — never commit",
                snippet=redact(m.group(0)),
            )

        # PEM private key
        if _PEM_HEADER.search(line):
            yield Finding(
                path=path, line=i,
                rule="credentials.private_key_pem",
                severity=Severity.HIGH,
                message="PEM PRIVATE KEY block header — never commit",
                snippet="-----BEGIN ... PRIVATE KEY-----",
            )

        # .env-style assignment (no spaces around `=`)
        m = _ENV_ASSIGN_TIGHT.search(line)
        if m:
            key, value = m.group(1), m.group(2)
            # Slug-shaped values are identifiers (model names, slugs),
            # not secrets — skip regardless of key shape.
            if _is_slug_shaped(value) or _is_obvious_placeholder(value):
                continue
            is_secret_named = bool(_SECRET_KEYS.match(key))
            if is_secret_named or _looks_like_secret_value(value):
                yield Finding(
                    path=path, line=i,
                    rule="credentials.env_assignment",
                    severity=Severity.HIGH,
                    message=(
                        f"`{key}=...` (.env style) looks like a committed "
                        "secret value (secret-named key)" if is_secret_named
                        else f"`{key}=...` (.env style) value is high-entropy "
                             "and secret-shaped"
                    ),
                    snippet=redact(value),
                )
            continue

        # Python-style constant: only flag when key is secret-named
        # AND value is not slug-shaped.
        m = _PY_ASSIGN_LOOSE.search(line)
        if m:
            key, value = m.group(1), m.group(2)
            if (
                _SECRET_KEYS.match(key)
                and not _is_slug_shaped(value)
                and _looks_like_secret_value(value)
            ):
                yield Finding(
                    path=path, line=i,
                    rule="credentials.py_constant",
                    severity=Severity.HIGH,
                    message=(
                        f"`{key} = \"...\"` Python constant has a "
                        "secret-named key and a secret-shaped value"
                    ),
                    snippet=redact(value),
                )
