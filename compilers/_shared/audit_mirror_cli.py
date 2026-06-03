"""Module CLI: write the audit-mirror module source to disk or stdout.

Usage::

    python -m compilers._shared.audit_mirror_cli > path/to/_audit_mirror.py
    python -m compilers._shared.audit_mirror_cli --out path/to/_audit_mirror.py

This is the co-location entrypoint referenced by
``docs/observability/audit-mirror.md``: every worked example's
``regenerate.sh`` invokes it to materialise a sibling ``_audit_mirror.py``
next to the emitted playbook module. The audit-mirror source is the
single source of truth for the in-process audit trail an emitted
artifact uses when no OpenTelemetry exporter is configured.

The implementation is intentionally thin: it is a deterministic adapter
over :func:`compilers._shared.observability.render_audit_mirror_module`.
Same input (no input) produces byte-identical output; re-running it
overwrites an existing file with identical bytes (the regenerate-sh
idempotency contract).

No vendor SDK is imported. No OTLP endpoint is hard-coded. The emitted
source likewise has no third-party dependencies — stdlib only — and
imports nothing from this repository, so an integrator who copies the
example directory into their own runtime keeps the sibling import
shape working.

Exit codes:
    0 — module source written successfully (to ``--out`` or stdout).
    2 — CLI usage error (handled by :mod:`argparse`).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from compilers._shared.observability import render_audit_mirror_module


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m compilers._shared.audit_mirror_cli",
        description=(
            "Print the dependency-free audit-mirror module emitted "
            "alongside each compiler artifact "
            "(see docs/observability/audit-mirror.md)."
        ),
    )
    parser.add_argument(
        "--out",
        default=None,
        help=(
            "Write the rendered module to this path instead of stdout. "
            "Parent directories must already exist; the file is "
            "overwritten atomically with the same bytes on every run."
        ),
    )
    return parser


def materialize(out_path: Path) -> Path:
    """Write the audit-mirror module source to ``out_path``.

    Deterministic: two invocations against the same path produce
    byte-identical content. Returns the path written for the caller's
    convenience.
    """
    rendered = render_audit_mirror_module()
    out_path.write_text(rendered, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    rendered = render_audit_mirror_module()
    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":  # pragma: no cover - module CLI entrypoint
    sys.exit(main())
