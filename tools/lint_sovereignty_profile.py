"""Sovereignty conformance-profile linter (F-SV-05). All findings HARD.

Guards the shipped baseline at ``content/profiles/sovereignty_conformance
.yaml`` — born all-HARD with no SOFT tier and no ceiling, because unlike
the three guards that started SOFT (#866, #875, #902) this one lands
together with a complete profile, so there is no debt to ceiling.

Codes:

* ``profile_invalid`` — the profile does not validate against
  ``schemas/sovereignty-profile.schema.json``.
* ``unclassified_sovereignty_metric`` — a catalogue metric carrying
  ``foundation_property: sovereignty`` is absent from the profile's
  ``indicators``. The force-a-classification shape: a new sovereignty
  indicator surfaces as a named failure pointing at the profile, never
  as a silently unclassified slice of the posture.
* ``unknown_profile_indicator`` — the profile classifies an indicator
  no sovereignty-tagged metric declares (renamed, retired, untagged).
* ``baseline_with_overrides`` — the shipped baseline carries override
  entries or a ``baseline_ref``; the baseline cannot relax itself.
* ``profile_not_evaluable`` — ``effective_bands`` rejects the profile
  (mis-shaped override, band vocabulary violation).

Usage::

    python -m tools.lint_sovereignty_profile [--format text|json]

Exit code is non-zero iff any finding is emitted. Pure stdlib +
PyYAML + jsonschema, no network.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from compilers._shared.evidence.sovereignty_profile import (
    ProfileError,
    effective_bands,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / "content" / "profiles" / "sovereignty_conformance.yaml"
SCHEMA_PATH = REPO_ROOT / "schemas" / "sovereignty-profile.schema.json"
METRICS_DIR = REPO_ROOT / "content" / "metrics"
CLI_NAME = "sovereignty-profile"


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str

    def as_text(self) -> str:
        return f"[{self.code}] {self.detail}"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _catalogue_sovereignty_ids(metrics_dir: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted(metrics_dir.glob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        prop = doc.get("foundation_property") or []
        if isinstance(prop, str):
            prop = [prop]
        if "sovereignty" in prop:
            ids.add(doc["stable_id"])
    return ids


def scan(
    profile_path: Path = PROFILE_PATH, metrics_dir: Path = METRICS_DIR
) -> list[Finding]:
    findings: list[Finding] = []
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(profile), key=str):
        findings.append(Finding("profile_invalid", err.message))
    if findings:
        return findings  # shape first; the rest assumes a valid document

    declared = set(profile["indicators"])
    tagged = _catalogue_sovereignty_ids(metrics_dir)

    for sid in sorted(tagged - declared):
        findings.append(Finding(
            "unclassified_sovereignty_metric",
            f"{sid} carries foundation_property: sovereignty but "
            f"{_rel(profile_path)} does not classify it — "
            "add an indicators entry with a max_band and a rationale; an "
            "unclassified indicator is a silent hole in the posture.",
        ))
    for sid in sorted(declared - tagged):
        findings.append(Finding(
            "unknown_profile_indicator",
            f"profile classifies {sid} but no sovereignty-tagged metric "
            "declares it — the metric was renamed, retired, or untagged; "
            f"update {_rel(profile_path)}.",
        ))

    if profile.get("overrides"):
        findings.append(Finding(
            "baseline_with_overrides",
            "the shipped baseline carries override entries — the baseline "
            "cannot relax itself; overrides belong on operator profiles "
            "derived via baseline_ref.",
        ))
    if profile.get("baseline_ref"):
        findings.append(Finding(
            "baseline_with_overrides",
            "the shipped baseline declares baseline_ref — it IS the "
            "baseline.",
        ))

    try:
        effective_bands(profile)
    except ProfileError as exc:
        findings.append(Finding("profile_not_evaluable", str(exc)))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=CLI_NAME,
        description="Assert the shipped sovereignty conformance profile is "
        "valid, complete against the sovereignty-tagged catalogue, and "
        "evaluable.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    findings = scan()
    if args.format == "json":
        json.dump(
            {"tool": CLI_NAME, "findings": [asdict(f) for f in findings]},
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        print(f"{CLI_NAME} — {len(findings)} finding(s)")
        for f in findings:
            print(f"  {f.as_text()}")
        if not findings:
            print(
                "  OK — profile valid, complete against the "
                "sovereignty-tagged catalogue, and evaluable."
            )
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
