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

Files are read as UTF-8 with ``errors="replace"``; binary files are
skipped via a NUL-byte sniff on the first 4 KiB. This keeps the linter
fully offline and pure-Python with no third-party deps.
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

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


def _iter_files(
    roots: Sequence[Path],
    excludes: Sequence[str],
) -> Iterable[Path]:
    for root in roots:
        if root.is_file():
            yield root
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            # default-exclude directories
            if any(part in _DEFAULT_EXCLUDES for part in path.parts):
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
    return out


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
