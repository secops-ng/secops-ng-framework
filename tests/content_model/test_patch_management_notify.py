"""Unit tests for the notify primitive (notify maintenance owner).

The #937 wire card bound the playbook's last unbound action step to
``compose_maintenance_notification`` — the deterministic composition
half of owner notification, split from delivery per the
incident_management destination-resolver precedent. The behaviours
pinned here are the ones a later change could quietly reverse:

* **Urgency derives from the canary outcome** — a healthy canary
  composes ``routine``; an unhealthy one composes ``action_required``
  and carries the step's documented escalation levers verbatim, in
  the documented order. Carrying the options is not choosing among
  them: no field names a picked lever.
* **``canary_healthy`` must be a real boolean** — ``"false"`` is
  truthy in Python, so a marshalling layer that stringifies the flag
  would page at the wrong urgency; the boundary refuses it.
* ``notification_id`` is pinned against a hand-computed SHA-256 over
  ``evidence|subject`` (the canary outcome is deliberately NOT part of
  the dedup key — one evidence record pages at most once).
* The recipient is the role, never a person; the payload's exact key
  set is asserted per branch so no free-text recipient field can
  arrive later.
"""
from __future__ import annotations

import hashlib

import pytest

from content.playbooks.patch_management.primitives import (
    InvalidMaintenanceNotificationError,
    compose_maintenance_notification,
    derive_patch_application_artifact_id,
)

SUBJECT = "pkg:deb/openssl@3.0"
EVIDENCE = derive_patch_application_artifact_id(
    "patch_management", "exec-2026-06-19-0001", "2026-06-19T01:05:00Z"
)


def test_healthy_canary_composes_routine_delivery() -> None:
    payload = compose_maintenance_notification(EVIDENCE, SUBJECT, True)
    assert payload["urgency"] == "routine"
    assert payload["canary_healthy"] is True
    assert payload["recipient_role"] == "maintenance-owner"
    assert set(payload) == {
        "notification_id",
        "notification_kind",
        "recipient_role",
        "update_subject",
        "evidence_ref",
        "canary_healthy",
        "urgency",
        "summary",
    }, "no free-text recipient or lever field may exist on the routine payload"


def test_unhealthy_canary_composes_action_required_with_documented_levers() -> None:
    payload = compose_maintenance_notification(EVIDENCE, SUBJECT, False)
    assert payload["urgency"] == "action_required"
    assert payload["escalation_levers"] == [
        "rollback_canary",
        "escalate_advisory",
        "hold_broad_rollout",
    ], "the documented levers, verbatim and in the documented order"
    assert "UNHEALTHY" in payload["summary"]
    assert "chosen_lever" not in payload and "recommended_lever" not in payload, (
        "carrying the options is not choosing among them"
    )


def test_dedup_key_is_pinned_and_outcome_independent() -> None:
    """One evidence record pages at most once — the dedup key must not
    vary with the canary outcome."""
    expected = hashlib.sha256(
        f"patch_management|notify|{EVIDENCE}|{SUBJECT}".encode("utf-8")
    ).hexdigest()
    healthy = compose_maintenance_notification(EVIDENCE, SUBJECT, True)
    unhealthy = compose_maintenance_notification(EVIDENCE, SUBJECT, False)
    assert healthy["notification_id"] == expected
    assert unhealthy["notification_id"] == expected


def test_stringified_boolean_is_refused() -> None:
    """'false' is truthy — a stringified flag would page at the wrong
    urgency, so the boundary refuses non-bool flags outright."""
    for bad in ("false", "true", 1, 0, None):
        with pytest.raises(
            InvalidMaintenanceNotificationError, match="boolean"
        ):
            compose_maintenance_notification(EVIDENCE, SUBJECT, bad)  # type: ignore[arg-type]


def test_shape_gates_fail_loud() -> None:
    with pytest.raises(InvalidMaintenanceNotificationError, match="evidence_id"):
        compose_maintenance_notification("evidence/latest.json", SUBJECT, True)
    with pytest.raises(InvalidMaintenanceNotificationError, match="update_subject"):
        compose_maintenance_notification(EVIDENCE, "the openssl packages", True)
    with pytest.raises(InvalidMaintenanceNotificationError, match="empty"):
        compose_maintenance_notification(EVIDENCE, "  ", True)


def test_payload_is_deterministic() -> None:
    assert compose_maintenance_notification(
        EVIDENCE, SUBJECT, False
    ) == compose_maintenance_notification(EVIDENCE, SUBJECT, False)
