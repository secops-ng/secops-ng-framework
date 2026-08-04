"""CLI entrypoint for the hygiene linter.

Usage::

    python -m tools.hygiene_linter [PATH ...] [--format text|json]
                                   [--severity HIGH|MEDIUM|LOW]
                                   [--exclude GLOB ...]

Exit codes:
    0 — no findings at-or-above the gating severity (default: HIGH).
    1 — at least one gating-severity finding.
    2 — CLI usage error.

Default scan target is the current working directory.

Honoured exclusions (regardless of ``--exclude``):
    .git/, .venv/, venv/, node_modules/, __pycache__/, .mypy_cache/,
    .ruff_cache/, dist/, build/, *.egg-info/
    tests/hygiene_linter/ — this linter's own test corpus, which exists to
        hold deliberate positives for the rules under test
    any nested checkout — a subdirectory carrying its own ``.git`` marker
        (a clone, a submodule, or a git worktree) is pruned with its subtree

The last two exist because a scan that reports its own fixtures, or a
worktree's copy of them, buries the real signal: before this, a bare run
at the repo root reported 24 HIGH credential findings and exited 1, every
one of them a planted test value. A gate that fails on a clean tree is a
gate people stop reading, and this one guards the public bar.

Individual findings may also be exempted inline with a
``hygiene-linter: allow <rule-id>`` pragma, for the narrow case of a file
that must contain the vocabulary a rule detects. HIGH findings are never
suppressible that way. See ``tools/hygiene_linter/pragma.py``.

Files are read as UTF-8 with ``errors="replace"``; binary files are
skipped via a NUL-byte sniff on the first 4 KiB. This keeps the linter
fully offline and pure-Python with no third-party deps.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from tools.hygiene_linter import pragma
from tools.hygiene_linter.findings import (
    Finding,
    Severity,
    render_json,
    render_text,
)
from tools.hygiene_linter.rules import RULES

_DEFAULT_EXCLUDES = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".mypy_cache", ".ruff_cache", "dist", "build",
}

# Directory paths, relative to a scan root, that are always pruned. Unlike
# ``_DEFAULT_EXCLUDES`` these are multi-segment, so they cannot be expressed
# as a bare directory name without over-matching (excluding every ``tests``
# or every ``hygiene_linter`` directory would be far too broad).
_DEFAULT_EXCLUDE_PATHS = frozenset({
    ("tests", "hygiene_linter"),
})

_SKIP_SUFFIXES = {
    ".pyc", ".pyo", ".so", ".o", ".a", ".dylib", ".dll", ".exe",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp3", ".mp4", ".mov", ".wav", ".ogg",
}

_SEVERITY_ORDER = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2}


def _is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            chunk = fh.read(4096)
    except OSError:
        return True
    return b"\x00" in chunk


def _is_nested_checkout(directory: Path, root: Path) -> bool:
    """True when ``directory`` is a checkout in its own right, not the root.

    A clone has a ``.git`` directory; a submodule and a git worktree have a
    ``.git`` *file* pointing at the parent repository. Either way the subtree
    below it belongs to a different checkout and scanning it double-reports
    whatever the outer tree already contains.
    """
    return directory != root and (directory / ".git").exists()


def _iter_files(
    roots: Sequence[Path],
    excludes: Sequence[str],
) -> Iterable[Path]:
    for root in roots:
        if root.is_file():
            yield root
            continue
        # os.walk (rather than rglob) so an excluded directory is pruned with
        # its whole subtree instead of being re-tested at every leaf.
        for dirpath, dirnames, filenames in os.walk(root):
            here = Path(dirpath)
            dirnames.sort()
            keep: list[str] = []
            for name in dirnames:
                child = here / name
                # ``*.egg-info`` is a pattern rather than a fixed name, so it
                # cannot live in the set above — the module docstring has
                # always promised it is honoured, so honour it.
                if name in _DEFAULT_EXCLUDES or name.endswith(".egg-info"):
                    continue
                try:
                    rel_parts = child.relative_to(root).parts
                except ValueError:
                    rel_parts = child.parts
                if rel_parts in _DEFAULT_EXCLUDE_PATHS:
                    continue
                if _is_nested_checkout(child, root):
                    continue
                keep.append(name)
            dirnames[:] = keep

            for name in sorted(filenames):
                path = here / name
                if not path.is_file():
                    continue
                # suffix skip
                if path.suffix.lower() in _SKIP_SUFFIXES:
                    continue
                # user-supplied glob excludes (matched against path-from-root)
                try:
                    rel = str(path.relative_to(root))
                except ValueError:
                    rel = str(path)
                if any(fnmatch.fnmatch(rel, g) for g in excludes):
                    continue
                yield path


def _scan_file(path: Path, display: str) -> list[Finding]:
    if _is_binary(path):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    out: list[Finding] = []
    for rule in RULES:
        out.extend(rule(display, lines))
    # Suppression is applied here rather than inside the rules: the rule
    # design conventions require scanners to stay pure functions of
    # (path, lines), and a rule that had to know about pragmas would not be.
    # HIGH findings survive this regardless of any pragma — see pragma.py.
    return pragma.apply(out, lines)


def _filter_severity(
    findings: Iterable[Finding], minimum: Severity
) -> list[Finding]:
    floor = _SEVERITY_ORDER[minimum]
    return [f for f in findings if _SEVERITY_ORDER[f.severity] >= floor]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="hygiene-linter",
        description="Forward-public hygiene linter — scans for credential "
                    "leakage and commercial-intent language before content "
                    "reaches will-be-public repos.",
    )
    p.add_argument(
        "paths", nargs="*", default=["."],
        help="Files or directories to scan (default: current directory).",
    )
    p.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--min-severity",
        choices=[s.value for s in Severity], default=Severity.LOW.value,
        help="Hide findings below this severity (default: LOW = show all).",
    )
    p.add_argument(
        "--gate-severity",
        choices=[s.value for s in Severity], default=Severity.HIGH.value,
        help="Exit non-zero if any finding is at-or-above this severity "
             "(default: HIGH).",
    )
    p.add_argument(
        "--exclude", action="append", default=[],
        help="Glob pattern (relative to each root) to exclude. Repeatable.",
    )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    roots = [Path(p) for p in args.paths]
    for r in roots:
        if not r.exists():
            print(f"hygiene-linter: path does not exist: {r}", file=sys.stderr)
            return 2

    all_findings: list[Finding] = []
    for fpath in _iter_files(roots, args.exclude):
        # Display path: relative to cwd when possible, else absolute.
        try:
            display = str(fpath.relative_to(Path.cwd()))
        except ValueError:
            display = str(fpath)
        all_findings.extend(_scan_file(fpath, display))

    visible = _filter_severity(all_findings, Severity(args.min_severity))

    if args.format == "json":
        print(render_json(visible))
    else:
        if visible:
            print(render_text(visible))
        else:
            print("hygiene-linter: no findings.")

    gate = Severity(args.gate_severity)
    gating = _filter_severity(all_findings, gate)
    return 1 if gating else 0


if __name__ == "__main__":
    sys.exit(main())
