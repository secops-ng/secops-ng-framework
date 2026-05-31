"""CLI wrapper: ``secops-ng compile <playbook> --target n8n [--out PATH]``.

Thin orchestration layer that dispatches to the reference compilers under
``compilers/``. The compilers themselves are I/O-free Python APIs; this
module owns argument parsing, target dispatch, and writing to disk.

Exit codes:
    0 — emitted workflow written to ``--out`` (or stdout).
    1 — parser/emitter raised. Error printed to stderr.
    2 — CLI usage error (unknown target, missing args, etc.).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Targets registered here. Adding langgraph is a single-line change once that
# emitter lands on its own card.
_TARGETS = {"n8n", "temporal"}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="secops-ng compile",
        description=(
            "Compile a CACAO v2 playbook to an orchestrator-native artifact. "
            "Reference compilers ship in compilers/<target>."
        ),
    )
    p.add_argument("playbook", help="path to a CACAO v2 playbook JSON file")
    p.add_argument(
        "--target",
        required=True,
        choices=sorted(_TARGETS),
        help="compile target (currently: n8n, temporal)",
    )
    p.add_argument(
        "--out",
        default=None,
        help="output path. Default: stdout.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.target == "n8n":
            from compilers._shared.cacao_parser import parse_file
            from compilers.n8n.emit import emit as emit_n8n

            playbook = parse_file(args.playbook)
            workflow = emit_n8n(playbook)
            rendered = json.dumps(workflow, indent=2) + "\n"
        elif args.target == "temporal":
            from compilers.temporal.emit import emit_file as emit_temporal_file

            rendered = emit_temporal_file(args.playbook)
        else:  # pragma: no cover — argparse choices guards this
            print(f"error: unknown target {args.target!r}", file=sys.stderr)
            return 2
    except Exception as exc:  # surface parser/emitter errors cleanly
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
