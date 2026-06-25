"""FOUNDATION-property catalogue-coverage guard (G-04 KRI).

Mechanical enforcement of the G-04 definition-of-done KRI in GOALS.md:
the catalogue must cover all four FOUNDATION properties (auditability,
determinism, sovereignty, operability) declared in docs/FOUNDATION.md.

EXTEND wave: `foundation_property` is now a REQUIRED catalogue-schema
field. Per-entry presence is enforced by the schema; this module guards
the YAML side independently (presence, enum membership, and the G-04
union-coverage invariant).

Pure stdlib + PyYAML. No network.
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METRICS_DIR = REPO_ROOT / "content" / "metrics"

FOUNDATION_PROPERTIES = frozenset(
    {"auditability", "determinism", "sovereignty", "operability"}
)


def _yaml_files() -> list[Path]:
    # Only top-level YAMLs under content/metrics/ are catalog entries.
    return sorted(p for p in METRICS_DIR.glob("*.yaml") if p.is_file())


def _declared_union() -> set[str]:
    union: set[str] = set()
    for path in _yaml_files():
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        values = doc.get("foundation_property") or []
        if isinstance(values, list):
            union.update(str(v) for v in values)
    return union


def _per_property_counts() -> dict[str, int]:
    counts: dict[str, int] = {prop: 0 for prop in FOUNDATION_PROPERTIES}
    for path in _yaml_files():
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        values = doc.get("foundation_property") or []
        if not isinstance(values, list):
            continue
        for value in values:
            key = str(value)
            if key in counts:
                counts[key] += 1
    return counts


# Per-property minimum-coverage floor for the four FOUNDATION dimensions.
#
# The union-coverage assertion below catches the catastrophic case (a
# property falls to zero); this floor catches the SKEW case (a property
# silently slides toward zero across edits). The floor is set to the
# maximum value the current catalogue can honestly carry without
# mislabeling entries — see PR notes for the determinism / sovereignty
# audit. Future work raises the floor as new metric authoring lands.
PER_PROPERTY_MIN_COVERAGE = 2


def test_every_entry_declares_non_empty_foundation_property() -> None:
    """Per-entry required: every catalogue entry MUST carry a non-empty
    `foundation_property` list. The schema makes the field required;
    this assertion guards the YAML side independently so a contributor
    cannot accidentally land an entry that omits or empties it."""
    offenders: list[str] = []
    for path in _yaml_files():
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        values = doc.get("foundation_property")
        if not isinstance(values, list) or not values:
            offenders.append(path.name)
    assert not offenders, (
        "every entry under content/metrics/*.yaml MUST declare a non-empty "
        "`foundation_property` list (one or more of auditability, "
        "determinism, sovereignty, operability). Offending entries: "
        f"{offenders}."
    )


def test_declared_values_are_within_foundation_enum() -> None:
    """No entry may declare a value outside the four FOUNDATION properties."""
    union = _declared_union()
    extras = union - FOUNDATION_PROPERTIES
    assert not extras, (
        f"catalogue declares foundation_property values outside the "
        f"FOUNDATION enum: {sorted(extras)}. Allowed: "
        f"{sorted(FOUNDATION_PROPERTIES)}."
    )


def test_catalogue_covers_all_four_foundation_properties() -> None:
    """G-04 KRI: the union of declared values must cover all four properties."""
    union = _declared_union()
    missing = FOUNDATION_PROPERTIES - union
    assert not missing, (
        f"G-04 KRI fired: catalogue lacks coverage for FOUNDATION "
        f"properties {sorted(missing)}. The union of "
        f"`foundation_property` values across content/metrics/*.yaml "
        f"must cover all of {sorted(FOUNDATION_PROPERTIES)}."
    )


def test_per_property_minimum_coverage_floor() -> None:
    """G-04 KRI hardening: every FOUNDATION property must be carried by
    at least PER_PROPERTY_MIN_COVERAGE catalogue entries.

    The existing union-coverage assertion only guards against a property
    falling to zero. A property carried by a single entry is one re-tag
    away from triggering the KRI — a live fragility. This floor catches
    the skew case so any edit that drops a property below the floor
    fails CI rather than silently regressing.

    If a property cannot honestly reach the floor on current content,
    the correct response is to commission new metric authoring (raise
    the property's coverage by writing new metrics that legitimately
    evidence the property), not to mislabel existing entries.
    """
    counts = _per_property_counts()
    offenders = {
        prop: n
        for prop, n in counts.items()
        if n < PER_PROPERTY_MIN_COVERAGE
    }
    assert not offenders, (
        f"G-04 KRI floor fired: FOUNDATION properties below the "
        f"per-property minimum-coverage floor of "
        f"{PER_PROPERTY_MIN_COVERAGE}: {offenders}. Full distribution: "
        f"{counts}. The fix is to commission new metric authoring that "
        f"legitimately evidences the under-covered property per "
        f"docs/FOUNDATION.md — not to mislabel existing entries."
    )
