"""Structured finding type for the hygiene linter."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from enum import Enum


class Severity(str, Enum):  # noqa: UP042 — str+Enum kept for JSON-shape stability
    """Severity classes — HIGH causes non-zero CLI exit."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class Finding:
    """A single hygiene-rule hit.

    Attributes
    ----------
    path:
        File path, relative to the scan root.
    line:
        1-indexed line number of the match.
    rule:
        Stable rule id (e.g. ``credentials.aws_access_key``).
    severity:
        ``HIGH`` / ``MEDIUM`` / ``LOW``. HIGH gates the build.
    message:
        Human-readable explanation, suitable for terminal output.
    snippet:
        The matched text, truncated to ``snippet_max`` chars. Never
        printed in full to avoid leaking the secret further into logs.
    """

    path: str
    line: int
    rule: str
    severity: Severity
    message: str
    snippet: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


def render_text(findings: Iterable[Finding]) -> str:
    """Human-readable single-line-per-finding output."""
    out = []
    for f in findings:
        out.append(
            f"{f.severity.value:6}  {f.path}:{f.line}  [{f.rule}]  {f.message}"
        )
    return "\n".join(out)


def render_json(findings: Iterable[Finding]) -> str:
    """JSON-array output for downstream tooling."""
    return json.dumps([f.to_dict() for f in findings], indent=2, sort_keys=True)


def redact(text: str, max_visible: int = 4) -> str:
    """Return a short fingerprint of a candidate secret string.

    Never log the full match — show first ``max_visible`` chars plus a
    length marker so a reviewer can identify the hit without the tool
    becoming a second leak vector.
    """
    text = text.strip()
    if len(text) <= max_visible:
        return "*" * len(text)
    return f"{text[:max_visible]}…[{len(text)} chars]"
