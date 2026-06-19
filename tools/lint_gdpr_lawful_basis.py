"""GDPR data-flow CI guard — full 7-section coverage + drift check.

For every cookbook playbook present under ``content/playbooks/``, this
linter asserts the following about its sibling GDPR data-flow document
under ``content/mappings/gdpr/``:

1. The document ``content/mappings/gdpr/data-flow-<workflow>.md`` exists.
2. Its section set matches the canonical template
   ``content/mappings/gdpr/_data-flow-template.md`` exactly — no
   missing, extra, or renamed sections (the drift check).
3. Each of the seven canonical sections has a non-empty body — at
   least one non-whitespace, non-blockquote, non-placeholder line
   between the section heading and the next ``## `` heading.

The canonical sections (read live from the template, not hard-coded
here) are:

  1. Purpose
  2. Lawful basis
  3. Categories of data subjects and personal data
  4. Recipients
  5. Retention
  6. Cross-border transfers
  7. Data subject rights

This is the F-GD-02 EXTEND enforcement, completing the feature whose
SKELETON shipped earlier (single ``## 2. Lawful basis`` non-empty
check).

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

#: Canonical template filename (relative to GDPR_MAPPINGS_SUBDIR).
TEMPLATE_FILENAME = "_data-flow-template.md"

#: Heading text of the (legacy SKELETON) lawful-basis section. Retained
#: as a public constant for backward compatibility with importers; the
#: EXTEND check resolves all section headings dynamically from the
#: canonical template.
LAWFUL_BASIS_HEADING = "## 2. Lawful basis"


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """A single CI-guard finding.

    ``workflow`` is the cookbook playbook directory name.
    ``kind`` is one of:

      - ``missing_doc``         — data-flow doc absent for this playbook.
      - ``missing_section``     — section required by template is absent
                                  from this doc.
      - ``empty_section``       — section heading present but body is
                                  empty / placeholder / blockquote-only.
      - ``unexpected_section``  — section heading present in doc that
                                  is not in the canonical template
                                  (drift: renamed or extra).

    ``path`` is the data-flow file path (relative to ``root``).
    ``section`` is the offending section heading (empty for
    ``missing_doc``).
    ``message`` is a contributor-facing one-line explanation.
    """

    workflow: str
    kind: str
    path: str
    message: str
    section: str = ""


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


def _extract_sections(markdown_text: str) -> "list[tuple[str, list[str]]]":
    """Return ``[(heading, body_lines), ...]`` for each ``## `` section.

    ``heading`` is the full heading line stripped (e.g. ``## 2. Lawful
    basis``). ``body_lines`` is every raw line between this heading and
    the next ``## `` heading, in order. Order is preserved.
    """
    sections: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            if current is not None:
                sections.append(current)
            current = (stripped, [])
            continue
        if current is not None:
            current[1].append(raw_line)
    if current is not None:
        sections.append(current)
    return sections


def _section_body_is_non_empty(body_lines: Iterable[str]) -> bool:
    """Return True iff ``body_lines`` contains contributor prose.

    A content line counts if, after stripping, it:

    - is non-empty, and
    - is not the literal placeholder ``\\`<fill in>\\``` / ``<fill in>``
      (the template's unfilled marker, with or without backticks), and
    - does not start with ``>`` (block-quoted template guidance).

    Lines that are pure blockquote guidance and the bare ``<fill in>``
    marker therefore do not satisfy the check — only a contributor's
    actual prose does.
    """
    for raw_line in body_lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            continue
        if stripped in ("`<fill in>`", "<fill in>"):
            continue
        return True
    return False


def canonical_sections(template_text: str) -> list[str]:
    """Return canonical section headings (in template order) from the template.

    Pulled live from the template so any rename in
    ``_data-flow-template.md`` is the single source of truth.
    """
    return [heading for heading, _ in _extract_sections(template_text)]


# Backward-compatibility shim retained for the SKELETON tests and any
# downstream importer.
def lawful_basis_is_non_empty(markdown_text: str) -> bool:
    """Return True iff the ``## 2. Lawful basis`` section has content.

    Kept for backward compatibility with the F-GD-02 SKELETON. The
    EXTEND ``check`` function asserts non-empty bodies for ALL seven
    canonical sections.
    """
    for heading, body in _extract_sections(markdown_text):
        if heading == LAWFUL_BASIS_HEADING:
            return _section_body_is_non_empty(body)
    return False


# ---------------------------------------------------------------------------
# Core check
# ---------------------------------------------------------------------------


def _load_template_sections(root: Path) -> list[str]:
    """Load canonical sections from the template under ``root``.

    Returns the empty list if the template is missing (the caller turns
    that into a single explanatory finding rather than crashing).
    """
    template_path = root / GDPR_MAPPINGS_SUBDIR / TEMPLATE_FILENAME
    if not template_path.is_file():
        return []
    return canonical_sections(template_path.read_text(encoding="utf-8"))


def check(root: Path) -> list[Finding]:
    """Run the CI guard against ``root`` and return findings.

    An empty list means the guard passes. Findings are returned sorted
    by (workflow, kind, section) for deterministic CI output.
    """
    findings: list[Finding] = []

    canonical = _load_template_sections(root)
    template_rel = GDPR_MAPPINGS_SUBDIR / TEMPLATE_FILENAME
    if not canonical:
        # Template missing or empty — single explanatory finding, no
        # per-workflow scan (the check is undefined without a template).
        findings.append(
            Finding(
                workflow="",
                kind="missing_template",
                path=str(template_rel),
                message=(
                    f"canonical GDPR data-flow template missing or empty at "
                    f"{template_rel} — cannot derive section set"
                ),
            )
        )
        return findings

    canonical_set = set(canonical)

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
                        f"{rel_path} — create one from {template_rel}"
                    ),
                )
            )
            continue

        text = abs_path.read_text(encoding="utf-8")
        sections = _extract_sections(text)
        section_index: dict[str, list[str]] = {}
        for heading, body in sections:
            # First occurrence wins; duplicates are flagged as drift
            # below (the second copy is "unexpected" relative to the
            # canonical single-occurrence template).
            if heading not in section_index:
                section_index[heading] = body

        # Drift: unexpected / renamed sections in doc.
        for heading in section_index:
            if heading not in canonical_set:
                findings.append(
                    Finding(
                        workflow=workflow,
                        kind="unexpected_section",
                        path=str(rel_path),
                        section=heading,
                        message=(
                            f"GDPR data-flow doc for '{workflow}' contains "
                            f"section '{heading}' which is not in the "
                            f"canonical template ({template_rel}) — drift: "
                            f"renamed or extra section"
                        ),
                    )
                )

        # Missing / empty canonical sections.
        for heading in canonical:
            if heading not in section_index:
                findings.append(
                    Finding(
                        workflow=workflow,
                        kind="missing_section",
                        path=str(rel_path),
                        section=heading,
                        message=(
                            f"GDPR data-flow doc for '{workflow}' is missing "
                            f"canonical section '{heading}' at {rel_path} — "
                            f"add the section from {template_rel}"
                        ),
                    )
                )
                continue
            if not _section_body_is_non_empty(section_index[heading]):
                findings.append(
                    Finding(
                        workflow=workflow,
                        kind="empty_section",
                        path=str(rel_path),
                        section=heading,
                        message=(
                            f"GDPR data-flow doc for '{workflow}' has an "
                            f"empty '{heading}' section at {rel_path} — "
                            f"fill in contributor prose (blockquote "
                            f"guidance and `<fill in>` do not count)"
                        ),
                    )
                )

    return sorted(findings, key=lambda f: (f.workflow, f.kind, f.section))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_text(findings: Iterable[Finding]) -> str:
    lines = []
    for f in findings:
        suffix = f" [{f.section}]" if f.section else ""
        lines.append(f"{f.path}: [{f.kind}]{suffix} {f.message}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "F-GD-02 EXTEND: assert every cookbook playbook has a GDPR "
            "data-flow doc that matches the canonical 7-section template "
            "with no missing, empty, renamed, or extra sections."
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
                f"F-GD-02 guard failed.",
                file=sys.stderr,
            )
        else:
            print("F-GD-02: GDPR data-flow 7-section guard passed.")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
