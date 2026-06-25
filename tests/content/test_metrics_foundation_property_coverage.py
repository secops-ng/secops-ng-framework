"""FOUNDATION-property catalogue-coverage guard (G-04 KRI).

Mechanical enforcement of the G-04 definition-of-done KRI in GOALS.md:
the catalogue must cover all four FOUNDATION properties (auditability,
determinism, sovereignty, operability) declared in docs/FOUNDATION.md.

This is a SKELETON-wave guard. The schema field `foundation_property`
on a metric entry is OPTIONAL in this wave; a follow-on CORE wave will
backfill all 44 catalogue entries and flip the field to required. This
test is the contract that says: regardless of how many entries have
been tagged, the union of declared values across the catalogue MUST
cover all four FOUNDATION properties.

Until CORE lands a sovereignty-tagged seed, the union from the
SKELETON seed set covers three of the four properties. The full union
assertion is xfailed with `strict=False` so the test surfaces the
pending gap on every CI run without weakening the assertion or
breaking the lane.

Pure stdlib + PyYAML. No network.
"""
from __future__ import annotations

from pathlib import Path

import pytest
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


def test_at_least_one_entry_declares_foundation_property() -> None:
    """The SKELETON wave ships a seed set; the field must be live somewhere."""
    union = _declared_union()
    assert union, (
        "no catalogue entry declares `foundation_property`; the SKELETON "
        "seed set is missing. At least one entry under content/metrics/ "
        "must declare the field so the G-04 KRI guard has live data."
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


@pytest.mark.xfail(
    strict=False,
    reason=(
        "SKELETON wave: seed set covers auditability + determinism + "
        "operability; sovereignty seed lands with the CORE backfill that "
        "tags all 44 catalogue entries. This xfail is the live signal "
        "for the pending G-04 KRI gap and flips to a passing assertion "
        "the moment CORE lands."
    ),
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
