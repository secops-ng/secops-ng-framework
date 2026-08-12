"""Render a publishable sovereignty conformance disclosure pack (F-ADOPT-02).

The pack is the redacted, self-contained subset of an F-SV-05 verdict an
operator can link from their ``USED-BY.md`` row — "we use it" becomes
"we use it and here is the posture we hold". Deterministic: same record
file plus same profile file yields byte-identical output — no clock
read, no network access.

The redaction contract is enforced by construction, not by filtering:
the pack is assembled from an explicit allowlist of verdict fields, so
raw observed values, observation payloads, endpoint literals and
internal identifiers never enter it. What the pack carries per
indicator is the outcome and the band pair — the posture, not the
telemetry. A defensive scan of the serialised output backstops the
allowlist: if a future evaluator field smuggles a URL or an
``observed_value`` in, rendering fails loudly rather than leaking.

The full contract is documented in
``content/evidence/sovereignty/DISCLOSURE.md``.

Usage::

    python -m tools.render_disclosure_pack <record.json>
    python -m tools.render_disclosure_pack <record.json> \\
        --profile content/profiles/sovereignty_conformance.yaml \\
        --baseline content/profiles/sovereignty_conformance.yaml \\
        --output disclosure-pack.json

When ``--baseline`` is given the profile is first checked for
unrecorded relaxations, exactly as the evaluator CLI does — a pack
rendered against a quietly loosened profile would be the airbrushing
this artifact exists to prevent.

Exit codes: 0 the pack was rendered (whether or not the posture
holds — disclosure is not a gate), 2 the inputs are not evaluable or
the redaction backstop fired. The verdict inside the pack is
per-indicator with a pass/fail roll-up — never a score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

import yaml

from compilers._shared.evidence.sovereignty_profile import (
    ProfileError,
    evaluate_record,
    validate_profile_against_baseline,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = REPO_ROOT / "content" / "profiles" / "sovereignty_conformance.yaml"
CLI_NAME = "render-disclosure-pack"
TOOL_VERSION = "1.0.0"
PACK_FORMAT = "sovereignty-conformance-disclosure/v1"

# Markers that must never appear in a serialised pack. "://" catches
# any URL scheme (endpoint literals); the other two catch raw
# observation payloads should the evaluator's verdict ever grow them.
FORBIDDEN_MARKERS = ("observed_value", '"observations"', "://")


class RedactionError(ValueError):
    """The serialised pack failed the redaction backstop."""


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def render_pack(
    record: Mapping[str, Any],
    profile: Mapping[str, Any],
    record_bytes: bytes,
) -> dict[str, Any]:
    """Build the pack from an explicit allowlist of verdict fields."""
    verdict = evaluate_record(record, profile)

    indicators: dict[str, dict[str, Any]] = {}
    for stable_id, entry in verdict["indicators"].items():
        row: dict[str, Any] = {"outcome": entry["outcome"]}
        if entry.get("observed_band") is not None:
            row["observed_band"] = entry["observed_band"]
        if entry.get("required_band") is not None:
            row["required_band"] = entry["required_band"]
        if entry.get("via_override"):
            row["via_override"] = True
        indicators[stable_id] = row

    return {
        "disclosure_pack": PACK_FORMAT,
        "profile": verdict["profile"],
        "record": verdict["record"],
        "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
        "assessment_window": verdict["assessment_window"],
        "indicators": indicators,
        "pass": verdict["pass"],
        "provenance": {
            "renderer": CLI_NAME,
            "renderer_version": TOOL_VERSION,
            "evaluator": "compilers._shared.evidence.sovereignty_profile",
        },
    }


def serialise_pack(pack: Mapping[str, Any]) -> str:
    """Canonical serialisation, then the redaction backstop."""
    text = json.dumps(pack, indent=2, sort_keys=True) + "\n"
    hits = [m for m in FORBIDDEN_MARKERS if m in text]
    if hits:
        raise RedactionError(
            "serialised pack contains forbidden marker(s) "
            f"{hits} — the allowlist in render_pack no longer covers "
            "the evaluator's verdict shape; fix the leak, do not "
            "publish"
        )
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description="Render the redacted, deterministic disclosure pack "
        "for one F-SV-04 evidence record evaluated against a declared "
        "sovereignty conformance profile.",
    )
    parser.add_argument("record", type=Path)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="When given, refuse a profile that relaxes below this "
        "baseline without a recorded override before rendering.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write the pack to this path (atomic replace) instead of "
        "stdout.",
    )
    args = parser.parse_args(argv)

    try:
        record_bytes = args.record.read_bytes()
        record = json.loads(record_bytes.decode("utf-8"))
        profile = _load(args.profile)
        if args.baseline is not None:
            validate_profile_against_baseline(profile, _load(args.baseline))
        text = serialise_pack(render_pack(record, profile, record_bytes))
    except (ProfileError, RedactionError) as exc:
        print(f"{CLI_NAME}: refused — {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError) as exc:
        print(f"{CLI_NAME}: bad input — {exc}", file=sys.stderr)
        return 2

    if args.output is None:
        sys.stdout.write(text)
    else:
        fd, tmp = tempfile.mkstemp(
            dir=str(args.output.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(text)
            os.replace(tmp, args.output)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
