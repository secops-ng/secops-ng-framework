"""``python -m compilers.temporal <playbook.cacao.json>`` entry point.

Emits the generated Temporal stub to stdout, or to ``--out`` when given.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .emit import emit_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m compilers.temporal",
        description=(
            "Compile a CACAO v2 playbook to a Temporal workflow stub (Python). "
            "Output is deterministic: same input yields byte-identical source."
        ),
    )
    parser.add_argument(
        "playbook",
        type=Path,
        help="path to a CACAO v2 playbook JSON file",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="output path. Default: stdout.",
    )
    args = parser.parse_args(argv)

    source = emit_file(args.playbook)
    if args.out is None:
        sys.stdout.write(source)
    else:
        args.out.write_text(source, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
