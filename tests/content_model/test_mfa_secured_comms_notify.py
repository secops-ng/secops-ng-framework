"""Unit tests for the notify primitive (notify authentication owner).

The #937 wire card bound the playbook's last unbound action step to
``compose_owner_notification`` — the deterministic composition half of
owner notification, split from delivery per the incident_management
destination-resolver precedent. The behaviours pinned here are the
ones a later change could quietly reverse:

* The payload is a **pure function of (attestation_id, auth_scope)**,
  and ``notification_id`` is pinned against a hand-computed SHA-256 so
  the messaging surface's delivery dedup key cannot drift silently — a
  replayed workflow must not page the owner twice for one attestation.
* The recipient is the **role, never a person**: ``recipient_role`` is
  the fixed ``authentication-owner`` token and no free-text recipient
  field exists on the payload.
* A caller passing a path or free text instead of the 64-hex
  attestation record id fails at this boundary, not at the messaging
  surface.
"""
from __future__ import annotations

import hashlib

import pytest

from content.playbooks.mfa_secured_comms.primitives import (
    InvalidOwnerNotificationError,
    compose_owner_notification,
    derive_mfa_posture_attestation_artifact_id,
)

SCOPE = "auth.scope/corp-sso"
ATTESTATION = derive_mfa_posture_attestation_artifact_id(
    "mfa_secured_comms", "exec-2026-06-19-0001", "2026-06-19T01:05:00Z"
)


def test_payload_is_deterministic_with_pinned_dedup_key() -> None:
    payload = compose_owner_notification(ATTESTATION, SCOPE)
    assert payload == compose_owner_notification(ATTESTATION, SCOPE)
    expected_id = hashlib.sha256(
        f"mfa_secured_comms|notify|{ATTESTATION}|{SCOPE}".encode("utf-8")
    ).hexdigest()
    assert payload["notification_id"] == expected_id
    assert payload["attestation_ref"] == ATTESTATION
    assert payload["auth_scope"] == SCOPE
    assert payload["notification_kind"] == "mfa_posture_attestation_delivery"


def test_distinct_attestations_get_distinct_dedup_keys() -> None:
    other = derive_mfa_posture_attestation_artifact_id(
        "mfa_secured_comms", "exec-2026-06-19-0002", "2026-06-19T02:05:00Z"
    )
    a = compose_owner_notification(ATTESTATION, SCOPE)["notification_id"]
    b = compose_owner_notification(other, SCOPE)["notification_id"]
    assert a != b


def test_recipient_is_the_role_never_a_person() -> None:
    payload = compose_owner_notification(ATTESTATION, SCOPE)
    assert payload["recipient_role"] == "authentication-owner"
    assert set(payload) == {
        "notification_id",
        "notification_kind",
        "recipient_role",
        "auth_scope",
        "attestation_ref",
        "summary",
    }, "no free-text recipient field may exist on the payload"


def test_summary_references_the_attestation_and_scope() -> None:
    payload = compose_owner_notification(ATTESTATION, SCOPE)
    assert ATTESTATION[:12] in payload["summary"]
    assert SCOPE in payload["summary"]


def test_shape_gates_fail_loud() -> None:
    with pytest.raises(InvalidOwnerNotificationError, match="attestation_id"):
        compose_owner_notification("artifacts/attestation.json", SCOPE)
    with pytest.raises(InvalidOwnerNotificationError, match="attestation_id"):
        compose_owner_notification(ATTESTATION.upper(), SCOPE)
    with pytest.raises(InvalidOwnerNotificationError, match="auth_scope"):
        compose_owner_notification(ATTESTATION, "the corp SSO estate")
    with pytest.raises(InvalidOwnerNotificationError, match="empty"):
        compose_owner_notification(ATTESTATION, "   ")
