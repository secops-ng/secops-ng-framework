"""CLI: ``python -m compilers.n8n <playbook.json> [-o workflow.json]``.

Reads a CACAO v2 playbook JSON file, emits the n8n workflow JSON to
stdout or to ``-o``, and prints any compiler warnings to stderr.

Exit codes:
  0 — success (with or without warnings)
  2 — input could not be parsed / not a CACAO v2 playbook
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from compilers.n8n.compiler import compile_playbook


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m compilers.n8n",
        description="Compile a CACAO v2 playbook into an n8n workflow JSON.",
    )
    parser.add_argument("playbook", type=Path, help="Path to a CACAO v2 playbook JSON.")
    parser.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Write the n8n workflow JSON here. Defaults to stdout.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress the warnings summary on stderr.",
    )
    args = parser.parse_args(argv)

    try:
        cacao = json.loads(args.playbook.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: could not read CACAO playbook: {exc}", file=sys.stderr)
        return 2

    try:
        result = compile_playbook(cacao)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(result.workflow, indent=2, sort_keys=False)
    if args.output is None:
        sys.stdout.write(payload + "\n")
    else:
        args.output.write_text(payload + "\n", encoding="utf-8")

    if result.warnings and not args.quiet:
        print(
            f"compiler: {len(result.warnings)} lossy translation(s):",
            file=sys.stderr,
        )
        for w in result.warnings:
            print(f"  [{w.code}] {w.step_id}: {w.message}", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
