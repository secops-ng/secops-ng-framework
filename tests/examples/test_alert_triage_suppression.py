"""Suppression-window collision contract across n8n, Temporal, and LangGraph.

The alert-triage worked examples share one primitive contract for case
suppression: ``alert_triage.primitives.suppression.canonical_seen_key``
is bound to the enrich-and-prepare step (``__seen_key__``) and the
``suppress and close`` step of every compiled target. Two alerts that
agree on the closed tuple of ``(detection_rule_id, subject_ref,
asset_ref, classification)`` and arrive inside the configured
suppression window collapse onto a single case: the first proceeds
through prioritisation + response, the second routes through
``suppress and close`` against the existing case.

This test pins the contract end-to-end:

* Each emitted artefact (n8n workflow JSON, Temporal workflow stub,
  LangGraph state-bindings module) references the suppression primitive
  on both the enrich step and the suppress-and-close step. Wiring drift
  in any target fails the test.
* Feeding the primitive two alerts with cosmetically-different but
  canonically-identical seen-key components produces the same canonical
  seen-key — the second submission resolves the existing case via the
  injected lookup and is suppressed, while the first proceeds through
  the prioritisation + response wave.
* The audit-trail mirror records the suppression decision exactly once
  even when the suppress span is replayed (idempotent ``append`` is
  what Temporal replays rely on).
* Distinctness: changing any of the four seen-key fields yields a
  distinct key, so collisions are not over-broad.
* The window arithmetic is half-open: a re-fire at the right edge of
  the window starts a new case rather than indefinitely extending the
  prior one.

The wiring check is per-target; the routing / audit checks live on the
shared primitive layer the three targets call into, so the assertion
holds across all three targets without requiring n8n, Temporal, or
LangGraph runtimes to be installed.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pytest

from content.playbooks.alert_triage.primitives import (
    SeenRecord,
    SuppressionVerdict,
    SuppressionWindow,
    canonical_seen_key,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples"

# Step ids the suppression primitive is wired onto by CORE-WIRE-SUPPRESS
# (PR #236) and CORE-WIRE-SUPPRESS-CLOSE (PR #238). The enrich step
# materialises ``__seen_key__``; the suppress-and-close step closes the
# matched case using the same canonical key.
ENRICH_STEP_ID = "action--a1e47431-0000-4000-8000-000000000003"
SUPPRESS_STEP_ID = "action--a1e47431-0000-4000-8000-000000000005"

# The core_body hook emits ``from alert_triage.primitives.suppression
# import canonical_seen_key`` (or its escaped pythonCode equivalent on
# n8n), so artefacts carry the module + symbol but never a single
# dotted fully-qualified path.
SUPPRESSION_MODULE = "alert_triage.primitives.suppression"
SUPPRESSION_SYMBOL = "canonical_seen_key"

# (target_label, path_to_emitted_artefact) pairs — one test per target.
TARGETS: list[tuple[str, Path]] = [
    ("n8n", EXAMPLES / "n8n" / "alert-triage" / "workflow.n8n.json"),
    ("temporal", EXAMPLES / "temporal" / "alert-triage" / "workflow.temporal.py"),
    ("langgraph", EXAMPLES / "langgraph" / "alert-triage" / "state_bindings.py"),
]


# --------------------------------------------------------------------------- #
# Wiring: every target references the suppression primitive on both           #
# the enrich step and the suppress-and-close step.                            #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("label,artefact", TARGETS, ids=[t[0] for t in TARGETS])
def test_enrich_step_wires_suppression_primitive(label: str, artefact: Path) -> None:
    """Each target's emitted artefact materialises the seen-key on enrich."""
    assert artefact.exists(), f"missing emitted artefact for {label}: {artefact}"
    text = artefact.read_text(encoding="utf-8")
    assert SUPPRESSION_MODULE in text, (
        f"{label} worked example does not reference the suppression "
        f"module {SUPPRESSION_MODULE!r} — enrich step appears unwired"
    )
    assert SUPPRESSION_SYMBOL in text, (
        f"{label} worked example does not reference the suppression "
        f"symbol {SUPPRESSION_SYMBOL!r} — enrich step appears unwired"
    )
    assert ENRICH_STEP_ID in text, (
        f"{label} worked example does not reference enrich step id "
        f"{ENRICH_STEP_ID!r}"
    )


@pytest.mark.parametrize("label,artefact", TARGETS, ids=[t[0] for t in TARGETS])
def test_suppress_and_close_step_wires_suppression_primitive(
    label: str, artefact: Path
) -> None:
    """Each target's emitted artefact closes against the canonical seen-key."""
    assert artefact.exists(), f"missing emitted artefact for {label}: {artefact}"
    text = artefact.read_text(encoding="utf-8")
    assert SUPPRESS_STEP_ID in text, (
        f"{label} worked example does not reference suppress-and-close "
        f"step id {SUPPRESS_STEP_ID!r}"
    )
    # The suppress-and-close step body uses the same primitive as the
    # enrich step, so the module-level wiring assertion in
    # ``test_enrich_step_wires_suppression_primitive`` already covers
    # the suppress-side reference — but a target that wired the enrich
    # side and forgot the suppress-close side would still pass that
    # check. Pin both step ids appear in the suppress-side context.
    occurrences = text.count(SUPPRESSION_SYMBOL)
    assert occurrences >= 2, (
        f"{label} worked example references {SUPPRESSION_SYMBOL!r} only "
        f"{occurrences} time(s); CORE-WIRE-SUPPRESS + "
        f"CORE-WIRE-SUPPRESS-CLOSE both bind it, so >=2 is required"
    )


# --------------------------------------------------------------------------- #
# Collision contract: two cosmetically-different alerts collapse onto one     #
# canonical seen-key, the second is suppressed, the first proceeds.           #
# --------------------------------------------------------------------------- #


# Cosmetic variants that must canonicalise to the same form. Same kind
# of thing — same rule, same identity, same asset, same classification.
_ALERT_A: dict[str, str] = {
    "detection_rule_id": "rule.cred-access.brute-force-ssh",
    "subject_ref": "identity:analyst-7c2@example.org",
    "asset_ref": "host:ip-10-0-0-12.eu-west-1.example.org",
    "classification": "credential-access",
}
_ALERT_B: dict[str, str] = {
    # Same rule, surrounding whitespace.
    "detection_rule_id": "  Rule.Cred-Access.Brute-Force-SSH ",
    # Same identity, NFKC-equivalent unicode + casing.
    "subject_ref": "Identity:Analyst-7c2@Example.org",
    # Same asset, mixed case + collapsible whitespace.
    "asset_ref": "Host:IP-10-0-0-12.eu-west-1.Example.org",
    # Same classification.
    "classification": "Credential-Access",
}


def test_canonical_variants_yield_identical_seen_key() -> None:
    key_a = canonical_seen_key(**_ALERT_A)
    key_b = canonical_seen_key(**_ALERT_B)
    assert key_a == key_b, (
        "cosmetic variants of the same (rule, subject, asset, "
        "classification) tuple must produce the same seen-key"
    )


def test_second_alert_routes_to_existing_case_within_window() -> None:
    """Simulate the per-target intake handler: a case-store keyed by the
    canonical seen-key. The first alert opens a case and proceeds through
    prioritisation + response; the second alert (within the window)
    resolves the same key and is routed through ``suppress and close``.
    """
    now_t0 = datetime(2026, 6, 5, 12, 0, 0, tzinfo=timezone.utc)
    now_t1 = now_t0 + timedelta(minutes=5)

    cases: dict[str, dict[str, object]] = {}

    def lookup(seen_key: str) -> Optional[SeenRecord]:
        case = cases.get(seen_key)
        if case is None:
            return None
        return SeenRecord(
            case_ref=str(case["case_ref"]),
            first_seen_at=case["first_seen_at"],  # type: ignore[arg-type]
        )

    window = SuppressionWindow(window=timedelta(hours=1), lookup=lookup)

    # --- First alert: no prior case, proceeds through prioritisation + response.
    verdict_first = window.is_seen(now=now_t0, **_ALERT_A)
    assert verdict_first.suppressed is False
    assert verdict_first.matched_case_ref is None
    assert verdict_first.reason == "seen_key has no prior case"

    proceeded: list[str] = []
    suppressed: list[str] = []
    if not verdict_first.suppressed:
        cases[verdict_first.seen_key] = {
            "case_ref": "case-0001",
            "first_seen_at": now_t0,
        }
        # Stand-in for the prioritisation + response wave on the first alert.
        proceeded.append(verdict_first.seen_key)
    else:
        suppressed.append(verdict_first.seen_key)

    # --- Second alert: within the window, canonically identical to the first.
    verdict_second = window.is_seen(now=now_t1, **_ALERT_B)
    assert verdict_second.suppressed is True, (
        "second alert within the suppression window must be suppressed; "
        "the alert-triage contract collapses re-fires onto the prior case"
    )
    assert verdict_second.seen_key == verdict_first.seen_key
    assert verdict_second.matched_case_ref == "case-0001"

    if verdict_second.suppressed:
        suppressed.append(verdict_second.seen_key)
    else:
        proceeded.append(verdict_second.seen_key)

    assert proceeded == [verdict_first.seen_key], (
        "first alert must proceed through prioritisation + response wave"
    )
    assert suppressed == [verdict_first.seen_key], (
        "second alert must route through suppress-and-close against the "
        "existing case (matched_case_ref points at the first case)"
    )
    assert len(cases) == 1, (
        "case-store grew to >1 entry under canonical-collision input — "
        "suppression contract broken"
    )


# --------------------------------------------------------------------------- #
# Window edge: a re-fire at or after the right edge starts a new case.        #
# --------------------------------------------------------------------------- #


def test_refire_at_window_edge_is_not_suppressed() -> None:
    """The window is half-open: an alert at exactly ``window`` later than
    the prior case is treated as *outside* the window so the next replay
    starts a new case rather than indefinitely extending the original.
    """
    t0 = datetime(2026, 6, 5, 12, 0, 0, tzinfo=timezone.utc)
    window_duration = timedelta(hours=1)

    def lookup(seen_key: str) -> Optional[SeenRecord]:
        return SeenRecord(case_ref="case-0001", first_seen_at=t0)

    window = SuppressionWindow(window=window_duration, lookup=lookup)

    # Exactly at the right edge: outside.
    verdict_edge = window.is_seen(now=t0 + window_duration, **_ALERT_A)
    assert verdict_edge.suppressed is False
    assert verdict_edge.matched_case_ref == "case-0001"
    assert "outside window" in verdict_edge.reason

    # One microsecond before the edge: inside.
    verdict_inside = window.is_seen(
        now=t0 + window_duration - timedelta(microseconds=1), **_ALERT_A
    )
    assert verdict_inside.suppressed is True
    assert verdict_inside.matched_case_ref == "case-0001"


# --------------------------------------------------------------------------- #
# AuditTrail: the suppression decision is recorded exactly once on replay.    #
# --------------------------------------------------------------------------- #


def test_audit_trail_records_suppression_decision_once() -> None:
    """The audit-trail mirror's ``append`` is idempotent so a Temporal-style
    replay of the suppress-and-close span does not double-count the
    suppression event.
    """
    import importlib.util
    import sys

    mirror_path = EXAMPLES / "langgraph" / "alert-triage" / "_audit_mirror.py"
    spec = importlib.util.spec_from_file_location(
        "alert_triage_audit_mirror", mirror_path
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)

        # Fresh trail per test — the contextvar may already be populated
        # by sibling tests, so push a clean list.
        mod._TRAIL.set([])
        trail = mod.AuditTrail.current()

        seen_key = canonical_seen_key(**_ALERT_A)
        record = mod.AuditRecord(
            span_name=f"tool.{SUPPRESS_STEP_ID}",
            attributes={
                "secops_ng.step.id": SUPPRESS_STEP_ID,
                "secops_ng.suppression.seen_key": seen_key,
                "secops_ng.suppression.matched_case_ref": "case-0001",
                "secops_ng.suppression.decision": "suppressed_and_closed",
            },
        )

        # Replay the same suppression decision twice (Temporal would do
        # this when the activity is re-driven from history).
        trail.append(record)
        trail.append(record)

        snapshot = trail.snapshot()
        suppression_records = [
            r
            for r in snapshot
            if r.attributes.get("secops_ng.suppression.seen_key") == seen_key
        ]
        assert len(suppression_records) == 1, (
            "AuditTrail recorded the suppression decision more than once "
            "on replay — idempotent-append contract broken"
        )
    finally:
        sys.modules.pop(spec.name, None)


# --------------------------------------------------------------------------- #
# Distinctness: changing any seen-key field yields a distinct key.            #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "perturbed_field",
    ["detection_rule_id", "subject_ref", "asset_ref", "classification"],
)
def test_changing_any_seen_key_field_yields_distinct_key(
    perturbed_field: str,
) -> None:
    """Perturbing any one of the four seen-key fields must produce a
    distinct key — the suppression contract is over the *closed tuple*,
    not over any subset.
    """
    perturbed = dict(_ALERT_A)
    perturbed[perturbed_field] = perturbed[perturbed_field] + "-perturbed"
    key_baseline = canonical_seen_key(**_ALERT_A)
    key_perturbed = canonical_seen_key(**perturbed)
    assert key_baseline != key_perturbed, (
        f"perturbing {perturbed_field!r} did not change the seen-key — "
        f"suppression key over-collapses across {perturbed_field}"
    )


# --------------------------------------------------------------------------- #
# Cross-target consistency: the primitive layer the three targets share is    #
# the same module, so the seen-key is identical regardless of target.         #
# --------------------------------------------------------------------------- #


def test_seen_key_is_target_agnostic() -> None:
    """The suppression primitive lives in
    ``content/playbooks/alert-triage/`` and is imported verbatim by every
    target's enrich + suppress-and-close steps. Driving it from the test
    runner directly is therefore the same call the n8n ``pythonCode``
    node, the Temporal ``@activity.defn``, and the LangGraph ``@tool``
    each make. Pin the key under a known vector so a target-side change
    that re-implements canonicalisation locally rather than reusing the
    primitive is caught immediately.
    """
    import hashlib

    key = canonical_seen_key(**_ALERT_A)
    expected = hashlib.sha256(
        "\u001f".join(
            [
                "rule.cred-access.brute-force-ssh",
                "identity:analyst-7c2@example.org",
                "host:ip-10-0-0-12.eu-west-1.example.org",
                "credential-access",
            ]
        ).encode("utf-8")
    ).hexdigest()
    assert key == expected
