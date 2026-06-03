"""Module CLI: print the audit-mirror module source to stdout.

Usage:
    python -m compilers._shared.audit_mirror_cli > path/to/_audit_mirror.py

Co-location plumbing for :func:`render_audit_mirror_module`. Each
``regenerate.sh`` for a worked example invokes this entrypoint to
materialise ``_audit_mirror.py`` as a sibling of its emitted artifacts.
See :doc:`/docs/observability/audit-mirror` for the rationale.

Exit codes:
    0 — module source written to stdout (or to ``--out`` if given).
    2 — CLI usage error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from compilers._shared.observability import render_audit_mirror_module


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m compilers._shared.audit_mirror_cli",
        description=(
            "Print the dependency-free audit-mirror module emitted alongside "
            "each compiler artifact (see docs/observability/audit-mirror.md)."
        ),
    )
    p.add_argument(
        "--out",
        default=None,
        help="Write to this path instead of stdout.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    rendered = render_audit_mirror_module()
    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
