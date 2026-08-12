"""Evaluate an F-SV-04 sovereignty evidence record against a profile.

CLI wrapper over the pure evaluator at
``compilers._shared.evidence.sovereignty_profile.evaluate_record``.
Deterministic: same record file plus same profile file yields the same
output bytes — no clock read, no network access.

Usage::

    python -m tools.evaluate_sovereignty_conformance <record.json>
    python -m tools.evaluate_sovereignty_conformance <record.json> \\
        --profile content/profiles/sovereignty_conformance.yaml \\
        --baseline content/profiles/sovereignty_conformance.yaml
    python -m tools.evaluate_sovereignty_conformance <record.json> --format json

When ``--baseline`` is given the profile is first checked for
unrecorded relaxations (``validate_profile_against_baseline``) — an
operator profile that quietly loosens a band below the baseline is
refused before any evaluation happens.

Exit codes: 0 the posture holds, 1 it does not, 2 the inputs are not
evaluable. The verdict is per-indicator with a pass/fail roll-up —
never a score.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from compilers._shared.evidence.sovereignty_profile import (
    ProfileError,
    evaluate_record,
    validate_profile_against_baseline,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = REPO_ROOT / "content" / "profiles" / "sovereignty_conformance.yaml"
CLI_NAME = "sovereignty-conformance"


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description="Deterministically evaluate one F-SV-04 evidence record "
        "against a declared sovereignty conformance profile.",
    )
    parser.add_argument("record", type=Path)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="When given, refuse a profile that relaxes below this baseline "
        "without a recorded override.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        record = _load(args.record)
        profile = _load(args.profile)
        if args.baseline is not None:
            validate_profile_against_baseline(profile, _load(args.baseline))
        verdict = evaluate_record(record, profile)
    except ProfileError as exc:
        print(f"{CLI_NAME}: not evaluable — {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError) as exc:
        print(f"{CLI_NAME}: bad input — {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        json.dump(verdict, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"{CLI_NAME} — record {str(verdict['record'])[:12]}… against "
            f"{verdict['profile']}"
        )
        for sid in sorted(verdict["indicators"]):
            entry = verdict["indicators"][sid]
            mark = {"pass": "ok  ", "fail": "FAIL", "unobserved": "MISS",
                    "unprofiled": "UNCL"}[entry["outcome"]]
            observed = entry.get("observed_band", "-")
            required = entry.get("required_band", "-")
            via = " (override)" if entry.get("via_override") else ""
            print(f"  {mark}  {sid}: observed {observed}, allowed {required}{via}")
        print(f"  posture holds: {'yes' if verdict['pass'] else 'NO'}")

    return 0 if verdict["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
