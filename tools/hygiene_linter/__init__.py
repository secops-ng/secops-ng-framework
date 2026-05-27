"""Forward-public hygiene linter.

A repo-native, fully-offline scanner that checks staged content against
the public-release bar (AGENTS.md directive 7) before it ships to the
will-be-public repos. Catches the syntactic class of leaks — credential
shapes, .env fragments, high-entropy secrets — and a defensive subset
of commercial-intent / strategy language patterns. Semantic and tone
review remains with human reviewers; this tool is the cheap first gate.

The CLI entrypoint is :mod:`tools.hygiene_linter.cli`. Each detection
rule is a standalone module under :mod:`tools.hygiene_linter.rules`;
adding a rule is a single file plus an entry in the registry.
"""

from __future__ import annotations

from tools.hygiene_linter.findings import Finding, Severity

__all__ = ["Finding", "Severity"]
