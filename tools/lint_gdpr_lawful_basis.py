"""GDPR data-flow lawful-basis CI guard.

For every cookbook playbook present under ``content/playbooks/``, this
linter asserts two things about its sibling GDPR data-flow document
under ``content/mappings/gdpr/``:

1. The document ``content/mappings/gdpr/data-flow-<workflow>.md`` exists.
2. Its ``## 2. Lawful basis`` section is non-empty — the heading is
   present and at least one non-whitespace content line appears before
   the next ``## `` heading.

This is the F-GD-02 SKELETON enforcement: it closes the
regulatory-mapping coverage criterion established by F-GD-01 so the
coverage cannot silently regress. Per-section semantic validation of
the remaining six template sections (purpose, categories, recipients,
retention, cross-border, data-subject-rights) is deliberately out of
scope here — that's F-GD-02 CORE / EXTEND.

# TODO(F-GD-02 CORE): extend to enforce non-empty bodies for the other
# six canonical sections of ``_data-flow-template.md`` (purpose,
# categories, recipients, retention, cross-border transfers, data
# subject rights), and add per-section semantic checks (e.g. score
# the cross-border section against a fixed vocabulary).

A "cookbook playbook" for the purpose of this check is any directory
directly under ``content/playbooks/`` that:

- does not start with an underscore (the underscore directories are
  Python-package shims for legacy import paths, not playbooks); and
- contains a ``README.md`` file.

Usage:

    python -m tools.lint_gdpr_lawful_basis            # walk default tree
    python -m tools.lint_gdpr_lawful_basis --json     # machine-readable
    python -m tools.lint_gdpr_lawful_basis --root /path/to/repo

Exit code is non-zero iff at least one finding is emitted.

Pure stdlib. No network, no extra dependencies.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

#: Repository root resolved from this file's location (``<root>/tools/<file>``).
DEFAULT_ROOT = Path(__file__).resolve().parents[1]

#: Subdirectory under the repo root that holds the cookbook playbooks.
PLAYBOOKS_SUBDIR = Path("content") / "playbooks"

#: Subdirectory under the repo root that holds the GDPR data-flow docs.
GDPR_MAPPINGS_SUBDIR = Path("content") / "mappings" / "gdpr"

#: Heading text of the lawful-basis section as written in the template.
LAWFUL_BASIS_HEADING = "## 2. Lawful basis"


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """A single CI-guard finding.

    ``workflow`` is the cookbook playbook directory name.
    ``kind`` is one of ``missing_doc`` or ``empty_lawful_basis``.
    ``path`` is the GDPR data-flow file path (relative to ``root``)
    that the check expected to find or evaluate.
    ``message`` is a contributor-facing one-line explanation.
    """

    workflow: str
    kind: str
    path: str
    message: str


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_playbooks(root: Path) -> list[str]:
    """Return cookbook-playbook directory names under ``content/playbooks/``.

    A cookbook playbook is a non-underscore-prefixed directory that
    carries a ``README.md`` file. The underscore-prefixed directories
    (``alert_triage`` etc.) are Python-package shims used by the
    compilers for legacy import paths — they are not playbooks.

    The returned list is sorted for deterministic CI output.
    """
    playbooks_dir = root / PLAYBOOKS_SUBDIR
    if not playbooks_dir.is_dir():
        return []
    out: list[str] = []
    for entry in playbooks_dir.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("_"):
            continue
        if not (entry / "README.md").is_file():
            continue
        out.append(entry.name)
    return sorted(out)


# ---------------------------------------------------------------------------
# Section parsing
# ---------------------------------------------------------------------------


def lawful_basis_is_non_empty(markdown_text: str) -> bool:
    """Return True iff the ``## 2. Lawful basis`` section has content.

    Content is "at least one non-whitespace line that is not a
    blockquote-prefix-only line, between the lawful-basis heading and
    the next ``## `` heading". The blockquote rule is what keeps the
    raw template (whose body is just a ``> ...`` cite of the GDPR
    article and a ``<fill in>`` placeholder) from counting as filled.

    Specifically, a content line counts if, after stripping, it:

    - is non-empty, and
    - is not the literal placeholder ``\`<fill in>\``` (the template's
      unfilled marker, with or without surrounding whitespace), and
    - does not start with ``>`` (block-quoted template guidance).

    Lines that are pure blockquote guidance and the bare ``<fill in>``
    marker therefore do not satisfy the check — only a contributor's
    actual prose does.
    """
    lines = markdown_text.splitlines()
    in_section = False
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped == LAWFUL_BASIS_HEADING:
            in_section = True
            continue
        if not in_section:
            continue
        # Next top-level subsection terminates the lawful-basis section.
        if stripped.startswith("## "):
            return False
        if not stripped:
            continue
        if stripped.startswith(">"):
            continue
        if stripped in ("`<fill in>`", "<fill in>"):
            continue
        return True
    return False


# ---------------------------------------------------------------------------
# Core check
# ---------------------------------------------------------------------------


def check(root: Path) -> list[Finding]:
    """Run the CI guard against ``root`` and return findings.

    An empty list means the guard passes.
    """
    findings: list[Finding] = []
    gdpr_dir = root / GDPR_MAPPINGS_SUBDIR
    for workflow in discover_playbooks(root):
        rel_path = GDPR_MAPPINGS_SUBDIR / f"data-flow-{workflow}.md"
        abs_path = root / rel_path
        if not abs_path.is_file():
            findings.append(
                Finding(
                    workflow=workflow,
                    kind="missing_doc",
                    path=str(rel_path),
                    message=(
                        f"playbook '{workflow}' has no GDPR data-flow doc at "
                        f"{rel_path} — create one from "
                        f"{GDPR_MAPPINGS_SUBDIR / '_data-flow-template.md'}"
                    ),
                )
            )
            continue
        text = abs_path.read_text(encoding="utf-8")
        if not lawful_basis_is_non_empty(text):
            findings.append(
                Finding(
                    workflow=workflow,
                    kind="empty_lawful_basis",
                    path=str(rel_path),
                    message=(
                        f"GDPR data-flow doc for '{workflow}' has an empty "
                        f"'## 2. Lawful basis' section at {rel_path} — fill "
                        f"in the lawful basis per GDPR Art. 6(1)"
                    ),
                )
            )
    return sorted(findings, key=lambda f: (f.workflow, f.kind))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_text(findings: Iterable[Finding]) -> str:
    lines = []
    for f in findings:
        lines.append(f"{f.path}: [{f.kind}] {f.message}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "F-GD-02 SKELETON: assert every cookbook playbook has a GDPR "
            "data-flow doc with a non-empty lawful-basis section."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Repository root (default: the secops-ng-framework checkout).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of one finding per line.",
    )
    args = parser.parse_args(argv)

    findings = check(args.root.resolve())

    if args.json:
        payload = {
            "ok": not findings,
            "findings": [asdict(f) for f in findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        if findings:
            print(_format_text(findings))
            print(
                f"\n{len(findings)} finding(s). "
                f"F-GD-02 SKELETON guard failed.",
                file=sys.stderr,
            )
        else:
            print("F-GD-02 SKELETON: lawful-basis guard passed.")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
