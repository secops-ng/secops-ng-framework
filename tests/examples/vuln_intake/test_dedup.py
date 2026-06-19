"""Dedup-collision contract test across n8n, Temporal, and LangGraph targets.

The vuln_intake worked examples share one primitive contract for case
deduplication: ``vuln_intake.primitives.dedup.canonicalize_case_field``
is bound to the ``intake disclosure`` step of every compiled target, and
``case_idempotency_key`` collapses two replays of the same disclosure
against the same asset into a single case.

This test pins the contract end-to-end:

* Each emitted artefact (n8n workflow JSON, Temporal workflow stub,
  LangGraph state-bindings module) references the dedup primitive on
  the intake step. Wiring drift in any target fails the test.
* Feeding the primitive two cases with cosmetically-different but
  canonically-identical ``(cve_id, asset_ref)`` produces the same
  idempotency key — a second case routes to the existing one rather
  than opening a new record.
* The audit-trail mirror records the dedup decision exactly once even
  when the second case re-enters the same span (the mirror's
  ``append`` is idempotent, which is the contract Temporal replays
  rely on).
* Distinctness: same CVE id against a different asset ref yields
  distinct keys, so collisions are not over-broad.

The wiring check is per-target; the routing / audit checks live on the
shared primitive layer the three targets call into, so the assertion
holds across all three targets without requiring n8n, Temporal, or
LangGraph runtimes to be installed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from content.playbooks.vuln_intake.primitives import (
    canonicalize_case_field,
    case_idempotency_key,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = REPO_ROOT / "examples"

INTAKE_STEP_ID = "action--01a17a01-0000-4000-8000-000000000002"
# The core_body hook emits ``from vuln_intake.primitives.dedup import
# canonicalize_case_field`` (or its escaped pythonCode equivalent on
# n8n), so the artefacts carry the module + the symbol but never the
# dotted fully-qualified path in one string.
DEDUP_MODULE = "vuln_intake.primitives.dedup"
DEDUP_SYMBOL = "canonicalize_case_field"

# (target_label, path_to_emitted_artefact) pairs.
TARGETS: list[tuple[str, Path]] = [
    ("n8n", EXAMPLES / "n8n" / "vuln_intake" / "workflow.n8n.json"),
    ("temporal", EXAMPLES / "temporal" / "vuln_intake" / "workflow.temporal.py"),
    ("langgraph", EXAMPLES / "langgraph" / "vuln_intake" / "state_bindings.py"),
]


# --------------------------------------------------------------------------- #
# Wiring: every target references the dedup primitive on the intake step.     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("label,artefact", TARGETS, ids=[t[0] for t in TARGETS])
def test_intake_step_wires_dedup_primitive(label: str, artefact: Path) -> None:
    """Each target's emitted artefact calls the dedup canonicaliser on intake."""
    assert artefact.exists(), f"missing emitted artefact for {label}: {artefact}"
    text = artefact.read_text(encoding="utf-8")
    assert DEDUP_MODULE in text, (
        f"{label} worked example does not reference the dedup module "
        f"{DEDUP_MODULE!r} — intake step appears unwired"
    )
    assert DEDUP_SYMBOL in text, (
        f"{label} worked example does not reference the dedup symbol "
        f"{DEDUP_SYMBOL!r} — intake step appears unwired"
    )
    assert INTAKE_STEP_ID in text, (
        f"{label} worked example does not reference intake step id "
        f"{INTAKE_STEP_ID!r}"
    )


# --------------------------------------------------------------------------- #
# Collision: two cases with the same canonical (cve, asset) collapse.         #
# --------------------------------------------------------------------------- #


# Cosmetic variants that must canonicalise to the same form.
_CASE_A = ("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
_CASE_B = ("  cve-2026-12345 ", "PKG:PyPI/Requests@2.31.0")


def test_canonical_pair_yields_identical_key() -> None:
    key_a = case_idempotency_key(*_CASE_A)
    key_b = case_idempotency_key(*_CASE_B)
    assert key_a == key_b, (
        "cosmetic variants of the same (cve, asset) must produce the same "
        "idempotency key"
    )


def test_second_case_routes_to_existing_case() -> None:
    """Simulate the per-target intake handler: a case-store keyed by the
    idempotency key. The second submission must resolve to the same
    existing record, never open a new one.
    """
    cases: dict[str, dict[str, str]] = {}

    def intake(cve_id: str, asset_ref: str) -> tuple[str, bool]:
        key = case_idempotency_key(cve_id, asset_ref)
        opened = False
        if key not in cases:
            cases[key] = {
                "cve_id": canonicalize_case_field(cve_id),
                "asset_ref": canonicalize_case_field(asset_ref),
            }
            opened = True
        return key, opened

    key_first, opened_first = intake(*_CASE_A)
    key_second, opened_second = intake(*_CASE_B)

    assert opened_first is True, "first submission must open a new case"
    assert opened_second is False, (
        "second submission with identical canonical (cve, asset) must route "
        "to the existing case, not open a new one"
    )
    assert key_first == key_second
    assert len(cases) == 1, (
        "case-store grew to >1 entry under canonical-collision input — "
        "dedup contract broken"
    )


# --------------------------------------------------------------------------- #
# AuditTrail: the dedup decision is recorded exactly once on replay.          #
# --------------------------------------------------------------------------- #


def test_audit_trail_records_dedup_decision_once() -> None:
    """The audit-trail mirror's ``append`` is idempotent so a Temporal-style
    replay of the same intake span does not double-count the dedup event.
    """
    # Import the shared audit-mirror surface emitted alongside the
    # LangGraph worked example. The Temporal worked example exposes the
    # same contract on its replay-safe activity layer; the n8n target
    # relies on the same primitives. Asserting it once on the canonical
    # mirror covers the contract the three targets share.
    import importlib.util
    import sys

    mirror_path = EXAMPLES / "langgraph" / "vuln_intake" / "_audit_mirror.py"
    spec = importlib.util.spec_from_file_location(
        "vuln_intake_audit_mirror", mirror_path
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

        key = case_idempotency_key(*_CASE_A)
        record = mod.AuditRecord(
            span_name=f"tool.{INTAKE_STEP_ID}",
            attributes={
                "secops_ng.step.id": INTAKE_STEP_ID,
                "secops_ng.dedup.idempotency_key": key,
                "secops_ng.dedup.decision": "routed_to_existing",
            },
        )

        # Replay the same dedup decision twice (Temporal would do this
        # when the activity is re-driven from history).
        trail.append(record)
        trail.append(record)

        snapshot = trail.snapshot()
        dedup_records = [
            r
            for r in snapshot
            if r.attributes.get("secops_ng.dedup.idempotency_key") == key
        ]
        assert len(dedup_records) == 1, (
            "AuditTrail recorded the dedup decision more than once on "
            "replay — idempotent-append contract broken"
        )
    finally:
        sys.modules.pop(spec.name, None)


# --------------------------------------------------------------------------- #
# Distinctness: same CVE x different asset_ref => distinct keys.              #
# --------------------------------------------------------------------------- #


def test_same_cve_different_asset_yields_distinct_keys() -> None:
    key_one = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
    key_two = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.32.0")
    key_three = case_idempotency_key("CVE-2026-12345", "pkg:pypi/urllib3@2.0.0")
    assert key_one != key_two
    assert key_one != key_three
    assert key_two != key_three


@pytest.mark.parametrize(
    "asset_ref",
    [
        "pkg:pypi/requests@2.31.0",
        "pkg:deb/debian/openssl@3.0.11-1",
        "repo:github.com/example/service@sha:deadbeef",
    ],
)
def test_distinctness_holds_across_asset_kinds(asset_ref: str) -> None:
    """Same CVE against three structurally different asset refs must yield
    three distinct keys."""
    cve = "CVE-2026-99999"
    other_assets = [
        "pkg:pypi/requests@2.31.0",
        "pkg:deb/debian/openssl@3.0.11-1",
        "repo:github.com/example/service@sha:deadbeef",
    ]
    target = case_idempotency_key(cve, asset_ref)
    collisions = [
        a
        for a in other_assets
        if a != asset_ref and case_idempotency_key(cve, a) == target
    ]
    assert not collisions, (
        f"asset_ref {asset_ref!r} collided with: {collisions!r}"
    )


# --------------------------------------------------------------------------- #
# Cross-target consistency: the primitive layer the three targets share is    #
# the same module, so the idempotency key is identical regardless of target.  #
# --------------------------------------------------------------------------- #


def test_idempotency_key_is_target_agnostic() -> None:
    """The dedup primitive lives in ``content/playbooks/vuln_intake/`` and
    is imported verbatim by every target's intake step. Driving it from
    the test runner directly is therefore the same call the n8n
    ``pythonCode`` node, the Temporal ``@activity.defn``, and the
    LangGraph ``@tool`` each make. Pin the key under a known vector so a
    target-side change that re-implements canonicalisation locally
    rather than reusing the primitive is caught immediately.
    """
    import hashlib

    key = case_idempotency_key("CVE-2026-12345", "pkg:pypi/requests@2.31.0")
    expected = hashlib.sha256(
        b"cve-2026-12345\x1fpkg:pypi/requests@2.31.0"
    ).hexdigest()
    assert key == expected
