"""Playbook _template conformance linter — F-CONTRIB-ONBOARD-01 EXTEND (G-06).

Mechanical feedback loop for external contributors who copy
``content/playbooks/_template/`` into ``content/playbooks/<slug>/``.

Two check tiers, sharing the same underlying inspection code:

* **Structural** (always applied). Enforces the invariants that a
  playbook directory ships *something* to compile against:
    - A CACAO artifact is present (``playbook.cacao.json`` or
      ``playbook.cacao.yaml``).
    - A ``README.md`` is present.
    - The playbook is reachable from the outbound mapping graph —
      either a local ``mappings.yaml`` exists, or at least one
      inbound ``playbook.<slug>`` citation exists under
      ``content/mappings/<framework>/``.
    - No verbatim ``TODO_`` placeholders from the template
      (``TODO_UUID``, ``TODO_SLUG``, ``TODO_HUMAN_READABLE_TITLE`` …)
      leak into the shipped CACAO artifact or the README.

* **Strict** (opt-in). Enforces the four canonical README section
  headings the template documents:
    - ``## Overview``
    - ``## Regulatory anchors``
    - ``## How to compile``
    - ``## Operator customisation``

  Strict checks apply to a new playbook directory the moment a
  contributor opens a PR that adds it. Existing shipped playbooks
  use varied heading styles (grown historically); the structural
  tier holds them accountable without a forced-migration churn PR.
  Two switches select strict targets:

    * ``--strict`` — apply strict checks to every canonical playbook
      the walk visits. Useful for local iteration on a single new
      playbook (paired with ``--slug``).
    * ``--baseline-ref <ref>`` — apply strict checks only to playbook
      directories that are *net-new* in HEAD vs the baseline ref
      (default: ``origin/main`` in CI). Mirrors the diff-mode pattern
      established by ``tools.lint_playbook_orphans``.

Excluded from the walk in all modes:
    - ``_template`` itself (it is a scaffold, not a playbook).
    - Legacy hyphenated redirect stubs (``alert-triage``,
      ``incident-management``, ``vuln-intake``). These are preserved
      compatibility shims for the original hyphenated slugs; the
      canonical underscored siblings carry the CACAO artifact.
    - Any directory without a CACAO artifact (treated as "not a
      playbook yet"; the structural CACAO check would flag it, but
      the walk skips it so drafts a contributor is preparing don't
      trip the linter until they add the artifact).

Output formats: ``text`` (default, human-readable), ``json``
(machine-readable finding list). No network. Pure stdlib + PyYAML.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

import yaml

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

DEFAULT_ROOT = Path(__file__).resolve().parents[1]

PLAYBOOKS_RELPATH = Path("content") / "playbooks"
MAPPINGS_RELPATH = Path("content") / "mappings"

CACAO_FILENAMES = ("playbook.cacao.json", "playbook.cacao.yaml")

# Directories that live under content/playbooks/ but are not canonical
# playbooks the linter should visit.
#
# ``_template`` — scaffold, not a playbook.
# ``alert-triage`` / ``incident-management`` / ``vuln-intake`` —
#     legacy hyphenated redirect stubs; the canonical underscored
#     siblings ship the CACAO artifact.
EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        "_template",
        "alert-triage",
        "incident-management",
        "vuln-intake",
    }
)

# Canonical README section headings the template documents.
STRICT_HEADINGS: tuple[str, ...] = (
    "## Overview",
    "## Regulatory anchors",
    "## How to compile",
    "## Operator customisation",
)

# Inbound citation regex — same shape as tools.lint_playbook_orphans.
PLAYBOOK_REF_RE = re.compile(
    r"^\s*-\s*playbook\.([A-Za-z0-9_]+)(?:@[A-Za-z0-9_.\-]+)?\s*$"
)

# Verbatim placeholders that come out of ``_template/`` and must not
# survive into a shipped playbook. Kept explicit rather than a bare
# ``TODO_`` prefix scan so free-form ``TODO:`` comments in author
# notes are not flagged.
TEMPLATE_PLACEHOLDERS: tuple[str, ...] = (
    "TODO_UUID",
    "TODO_SLUG",
    "TODO_HUMAN_READABLE_TITLE",
    "TODO_ONE_TO_FOUR_PARAGRAPHS",
    "TODO_TYPE",
    "TODO_ISO8601_UTC",
    "TODO_LOWERCASE_TAG",
    "TODO_REGULATORY_CITATION",
    "TODO_PUBLISHER",
    "TODO_UPSTREAM_SPEC_OR_CLAUSE_URL",
    "TODO_ACTION_STEP_NAME",
    "TODO_UUID_START",
    "TODO_UUID_ACTION",
    "TODO_UUID_END",
    "__TODO_INPUT__",
    "__TODO_OUTPUT__",
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    slug: str
    code: str
    tier: str  # "structural" | "strict"
    message: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Report:
    root: Path
    checked: list[str] = field(default_factory=list)
    strict_targets: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    @property
    def ok(self) -> bool:
        return not self.findings

    def as_dict(self) -> dict:
        return {
            "root": str(self.root),
            "checked": self.checked,
            "strict_targets": self.strict_targets,
            "findings": [f.as_dict() for f in self.findings],
            "ok": self.ok,
        }


# ---------------------------------------------------------------------------
# Playbook enumeration
# ---------------------------------------------------------------------------


def enumerate_playbooks(root: Path) -> list[Path]:
    """Return every canonical playbook directory under content/playbooks/."""
    base = root / PLAYBOOKS_RELPATH
    if not base.is_dir():
        return []
    out: list[Path] = []
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name in EXCLUDED_DIRS:
            continue
        if entry.name.startswith("__"):
            continue
        if not any((entry / fn).is_file() for fn in CACAO_FILENAMES):
            # Not a canonical playbook (draft directory without a
            # CACAO artifact yet). Not our target.
            continue
        out.append(entry)
    return out


# ---------------------------------------------------------------------------
# Inbound mapping index
# ---------------------------------------------------------------------------


def build_inbound_index(root: Path) -> set[str]:
    """Return the set of slugs that appear as inbound playbook_refs."""
    base = root / MAPPINGS_RELPATH
    if not base.is_dir():
        return set()
    inbound: set[str] = set()
    for yml in base.rglob("*.yaml"):
        try:
            for line in yml.read_text(encoding="utf-8").splitlines():
                m = PLAYBOOK_REF_RE.match(line)
                if m:
                    inbound.add(m.group(1))
        except (OSError, UnicodeDecodeError):
            continue
    return inbound


# ---------------------------------------------------------------------------
# Diff-mode: net-new playbook slugs
# ---------------------------------------------------------------------------


def new_playbook_slugs(root: Path, baseline_ref: str) -> set[str] | None:
    """Return slugs whose playbook directory is net-new vs baseline.

    Returns None if the baseline ref cannot be resolved (silent no-op,
    matching the tolerance pattern in lint_playbook_orphans).
    """
    # Confirm the ref exists.
    probe = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", baseline_ref],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        return None

    # List playbook directories at baseline.
    ls = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-tree",
            "-d",
            "--name-only",
            f"{baseline_ref}:content/playbooks",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    baseline_dirs: set[str] = set()
    if ls.returncode == 0:
        baseline_dirs = {
            line.strip() for line in ls.stdout.splitlines() if line.strip()
        }

    current_dirs: set[str] = {
        p.name for p in (root / PLAYBOOKS_RELPATH).iterdir() if p.is_dir()
    }
    new = current_dirs - baseline_dirs
    new -= EXCLUDED_DIRS
    return {slug for slug in new if not slug.startswith("__")}


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------


def _check_cacao(playbook_dir: Path, report: Report) -> Path | None:
    for fn in CACAO_FILENAMES:
        p = playbook_dir / fn
        if p.is_file():
            return p
    report.add(
        Finding(
            slug=playbook_dir.name,
            code="MISSING_CACAO",
            tier="structural",
            message=(
                "no CACAO artifact found (expected "
                "playbook.cacao.json or playbook.cacao.yaml)"
            ),
        )
    )
    return None


def _check_readme(playbook_dir: Path, report: Report) -> Path | None:
    p = playbook_dir / "README.md"
    if p.is_file():
        return p
    report.add(
        Finding(
            slug=playbook_dir.name,
            code="MISSING_README",
            tier="structural",
            message="no README.md",
        )
    )
    return None


def _check_mapping_presence(
    playbook_dir: Path, inbound: set[str], report: Report
) -> None:
    if (playbook_dir / "mappings.yaml").is_file():
        return
    if playbook_dir.name in inbound:
        return
    report.add(
        Finding(
            slug=playbook_dir.name,
            code="NO_MAPPING_EDGE",
            tier="structural",
            message=(
                "no local mappings.yaml and no inbound "
                "playbook_refs entry under content/mappings/<framework>/"
            ),
        )
    )


def _check_no_template_placeholders(
    playbook_dir: Path, report: Report
) -> None:
    for name in ("README.md", *CACAO_FILENAMES):
        p = playbook_dir / name
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits = sorted(
            {ph for ph in TEMPLATE_PLACEHOLDERS if ph in text}
        )
        if hits:
            report.add(
                Finding(
                    slug=playbook_dir.name,
                    code="TEMPLATE_PLACEHOLDER_LEAK",
                    tier="structural",
                    message=(
                        f"{name} contains verbatim _template placeholder(s): "
                        + ", ".join(hits)
                    ),
                )
            )


# ---------------------------------------------------------------------------
# Strict checks
# ---------------------------------------------------------------------------


def _check_strict_headings(readme_path: Path, slug: str, report: Report) -> None:
    try:
        text = readme_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return
    lines = text.splitlines()
    heading_set = {line.rstrip() for line in lines if line.startswith("## ")}
    missing = [h for h in STRICT_HEADINGS if h not in heading_set]
    if missing:
        report.add(
            Finding(
                slug=slug,
                code="MISSING_CANONICAL_HEADING",
                tier="strict",
                message=(
                    "README.md missing canonical heading(s): "
                    + ", ".join(missing)
                ),
            )
        )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def lint(
    root: Path,
    *,
    strict_all: bool = False,
    baseline_ref: str | None = None,
    slug_filter: str | None = None,
) -> Report:
    """Walk the playbook tree and produce a Report.

    Args:
        root: repository root.
        strict_all: apply strict checks to every visited playbook.
        baseline_ref: apply strict checks only to playbook directories
            that are net-new in HEAD vs this git ref.
        slug_filter: restrict the walk to a single slug (useful for
            local iteration on a new playbook).
    """
    report = Report(root=root)
    inbound = build_inbound_index(root)

    strict_targets: set[str] | None
    if strict_all:
        strict_targets = None  # sentinel: everything
    elif baseline_ref is not None:
        resolved = new_playbook_slugs(root, baseline_ref)
        if resolved is None:
            # Baseline ref unresolvable — no strict scope. Structural
            # tier still runs.
            strict_targets = set()
        else:
            strict_targets = resolved
    else:
        strict_targets = set()

    for playbook_dir in enumerate_playbooks(root):
        slug = playbook_dir.name
        if slug_filter and slug != slug_filter:
            continue
        report.checked.append(slug)

        _check_cacao(playbook_dir, report)
        readme = _check_readme(playbook_dir, report)
        _check_mapping_presence(playbook_dir, inbound, report)
        _check_no_template_placeholders(playbook_dir, report)

        if readme is not None:
            in_strict_scope = strict_targets is None or slug in strict_targets
            if in_strict_scope:
                report.strict_targets.append(slug)
                _check_strict_headings(readme, slug, report)

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_text(report: Report) -> str:
    lines: list[str] = []
    lines.append(
        f"playbook _template conformance — {len(report.checked)} playbook(s) "
        f"checked, {len(report.strict_targets)} in strict scope"
    )
    if report.ok:
        lines.append("OK — no violations.")
        return "\n".join(lines) + "\n"
    lines.append(f"FAIL — {len(report.findings)} violation(s):")
    for f in report.findings:
        lines.append(f"  [{f.tier}] {f.slug}: {f.code}: {f.message}")
    return "\n".join(lines) + "\n"


def _format_json(report: Report) -> str:
    return json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tools.lint_playbook_template",
        description=(
            "Playbook _template conformance linter — "
            "F-CONTRIB-ONBOARD-01 EXTEND (G-06)."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Repository root (default: repo containing this script).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Apply strict README-heading checks to every visited "
            "playbook (not just diff-new)."
        ),
    )
    parser.add_argument(
        "--baseline-ref",
        default=None,
        help=(
            "Apply strict checks only to playbook directories that are "
            "net-new in HEAD vs this git ref (e.g. origin/main)."
        ),
    )
    parser.add_argument(
        "--slug",
        default=None,
        help="Restrict the walk to a single playbook slug.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = lint(
        args.root.resolve(),
        strict_all=args.strict,
        baseline_ref=args.baseline_ref,
        slug_filter=args.slug,
    )
    if args.format == "json":
        sys.stdout.write(_format_json(report))
    else:
        sys.stdout.write(_format_text(report))
    return 0 if report.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
