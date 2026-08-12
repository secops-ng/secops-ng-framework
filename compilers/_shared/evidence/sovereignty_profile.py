"""Sovereignty conformance-profile evaluation (F-SV-05).

Pure helpers that evaluate one F-SV-04 sovereignty evidence record
against a declared conformance profile. Deterministic by construction:
same record plus same profile yields the same verdict — no clock read,
no network access, no environment consultation. The profile is data the
three compile targets read (``content/profiles/`` ships the baseline);
this module is the one place the band comparison is defined so the
targets cannot drift on semantics.

Band semantics: ``on_target < warn < high < breach``. An indicator
passes when the record's observed ``threshold_band`` is at or better
than the profile's effective band for that indicator. The effective
band is the profile's ``max_band`` unless a recorded override names the
indicator — overrides are how a relaxation below a baseline stays a
visible decision, and :func:`validate_profile_against_baseline` is the
rule that makes an unrecorded relaxation an error rather than a drift.

The verdict is per-indicator with a pass/fail roll-up and carries no
score of any kind — the same no-aggregate discipline as the record
itself (F-SV-04) and the profile's own summary.
"""
from __future__ import annotations

from typing import Any, Mapping

__all__ = [
    "BAND_ORDER",
    "ProfileError",
    "effective_bands",
    "evaluate_record",
    "validate_profile_against_baseline",
]

BAND_ORDER: Mapping[str, int] = {
    "on_target": 0,
    "warn": 1,
    "high": 2,
    "breach": 3,
}


class ProfileError(ValueError):
    """Raised when a profile (or profile/baseline pair) is not evaluable."""


def _band_rank(band: str, where: str) -> int:
    try:
        return BAND_ORDER[band]
    except KeyError:
        raise ProfileError(
            f"{where}: {band!r} is not a threshold band "
            f"({list(BAND_ORDER)})"
        ) from None


def effective_bands(profile: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Resolve each indicator's effective band after recorded overrides.

    Returns ``{stable_id: {"band": <band>, "via_override": <bool>}}``.
    An override must name an indicator the profile declares, and its
    ``declared_band`` must equal the indicator's ``max_band`` — the
    override *is* the record of how that band came to be, not a second
    place the band lives. Whether the relaxation was legitimate against
    a baseline is :func:`validate_profile_against_baseline`'s question.
    """
    indicators = profile.get("indicators") or {}
    out: dict[str, dict[str, Any]] = {}
    for stable_id, entry in indicators.items():
        band = entry["max_band"]
        _band_rank(band, f"indicators[{stable_id!r}].max_band")
        out[stable_id] = {"band": band, "via_override": False}

    for i, ov in enumerate(profile.get("overrides") or []):
        stable_id = ov["indicator"]
        if stable_id not in out:
            raise ProfileError(
                f"overrides[{i}] names {stable_id!r}, which the profile "
                "does not declare under indicators"
            )
        if ov["declared_band"] != out[stable_id]["band"]:
            raise ProfileError(
                f"overrides[{i}]: declared_band {ov['declared_band']!r} "
                f"disagrees with indicators[{stable_id!r}].max_band "
                f"{out[stable_id]['band']!r} — the override records the "
                "band, it does not introduce a second one"
            )
        if _band_rank(ov["declared_band"], f"overrides[{i}].declared_band") <= _band_rank(
            ov["baseline_band"], f"overrides[{i}].baseline_band"
        ):
            raise ProfileError(
                f"overrides[{i}] on {stable_id!r} does not relax anything "
                f"({ov['declared_band']!r} is not looser than "
                f"{ov['baseline_band']!r}) — tightening never needs an "
                "override, so this entry is a mistake"
            )
        out[stable_id]["via_override"] = True
    return out


def validate_profile_against_baseline(
    profile: Mapping[str, Any], baseline: Mapping[str, Any]
) -> None:
    """Every relaxation below the baseline must carry a recorded override.

    Tightening needs nothing. Loosening without an override entry — or
    with an override whose ``baseline_band`` misstates the baseline —
    raises :class:`ProfileError` naming the indicator.
    """
    base_bands = {
        sid: entry["max_band"]
        for sid, entry in (baseline.get("indicators") or {}).items()
    }
    overridden = {
        ov["indicator"]: ov for ov in (profile.get("overrides") or [])
    }
    for sid, entry in (profile.get("indicators") or {}).items():
        if sid not in base_bands:
            continue  # indicator newer than the baseline — lint owns sync
        declared = _band_rank(entry["max_band"], f"indicators[{sid!r}]")
        base = _band_rank(base_bands[sid], f"baseline indicators[{sid!r}]")
        if declared <= base:
            continue  # equal or tighter — always fine
        ov = overridden.get(sid)
        if ov is None:
            raise ProfileError(
                f"{sid}: profile relaxes max_band to "
                f"{entry['max_band']!r} below the baseline "
                f"{base_bands[sid]!r} with no recorded override — a "
                "relaxation is a decision someone records, or it is drift"
            )
        if ov["baseline_band"] != base_bands[sid]:
            raise ProfileError(
                f"{sid}: override records baseline_band "
                f"{ov['baseline_band']!r} but the baseline declares "
                f"{base_bands[sid]!r} — the record must match the thing "
                "it relaxes"
            )


def evaluate_record(
    record: Mapping[str, Any], profile: Mapping[str, Any]
) -> dict[str, Any]:
    """Evaluate one F-SV-04 record against one profile. Pure and total.

    Per-indicator verdict entries:

    * ``pass`` — observed band at or better than the effective band.
    * ``fail`` — observed band worse than the effective band.
    * ``unobserved`` — the profile requires the indicator, the record
      does not carry it (cannot happen for records that validate
      against the F-SV-04 schema, but the evaluator does not assume
      its inputs were validated).
    * ``unprofiled`` — the record observes an indicator the profile
      does not classify. Fails the roll-up: an unclassified indicator
      is the exact silence F-SV-05 exists to forbid.

    The roll-up ``pass`` is true iff every entry is ``pass``. No count,
    no ratio, no score.
    """
    bands = effective_bands(profile)
    observations = record.get("observations") or {}

    indicators: dict[str, dict[str, Any]] = {}
    for stable_id, eff in bands.items():
        obs = observations.get(stable_id)
        if obs is None:
            indicators[stable_id] = {
                "outcome": "unobserved",
                "required_band": eff["band"],
                "via_override": eff["via_override"],
            }
            continue
        observed = obs["threshold_band"]
        ok = _band_rank(
            observed, f"observations[{stable_id!r}].threshold_band"
        ) <= _band_rank(eff["band"], f"indicators[{stable_id!r}]")
        indicators[stable_id] = {
            "outcome": "pass" if ok else "fail",
            "observed_band": observed,
            "required_band": eff["band"],
            "via_override": eff["via_override"],
        }

    for stable_id in observations:
        if stable_id not in bands:
            indicators[stable_id] = {
                "outcome": "unprofiled",
                "observed_band": observations[stable_id].get(
                    "threshold_band"
                ),
            }

    return {
        "profile": profile.get("stable_id"),
        "record": record.get("artifact_id"),
        "assessment_window": record.get("assessment_window"),
        "indicators": indicators,
        "pass": all(v["outcome"] == "pass" for v in indicators.values()),
    }
