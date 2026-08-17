"""Unit tests for the onboarding_offboarding_tracker primitives.

Closes the last of the #937 audit's five coverage gaps (evidence-ring
era: goldens pinned emitter output, nothing executed the primitives).
The behaviours pinned here are the ones a later change could quietly
reverse:

* ``ingest_lifecycle_event`` enforces the per-event-kind delta shape —
  a joiner grants only, a leaver revokes only, a mover does at least
  one — and refuses a capability that appears in both sets: nothing
  can be granted and revoked in the same lifecycle event.
* ``apply_capability_delta`` refuses a delta whose event principal and
  resolved principal differ — the delta MUST target the resolved
  principal, so an identity-resolution drift cannot silently re-point
  a grant.
* ``confirm_grant_revoke`` treats **divergence as data, not an
  exception**: a missing grant or a lingering revoke comes back as
  ``confirmed=False`` plus the divergence detail — the workflow's job
  is to *record* the divergence for reviewers, not to crash on it.
  Shape errors (malformed observed tokens) still raise.
* ``build_access_artifact`` carries the *observed* capability list
  into the schema envelope while the ``confirmed`` verdict and
  divergence detail deliberately stay outside it; its ``artifact_id``
  excludes ``captured_at`` (re-emissions land on the same path).

One test runs the whole ingest → resolve → delta → confirm → emit
chain — including an unconfirmed read-back — replayed to
byte-identity.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from content.playbooks.onboarding_offboarding_tracker.primitives import (
    InvalidAccessArtifactError,
    InvalidCapabilityDeltaError,
    InvalidConfirmationError,
    InvalidLifecycleEventError,
    apply_capability_delta,
    build_access_artifact,
    confirm_grant_revoke,
    derive_access_artifact_id,
    ingest_lifecycle_event,
    resolve_identity,
)

CAPTURED_AT = "2026-06-19T01:05:00Z"
EFFECTIVE_AT = "2026-06-19T01:00:00Z"


def _raw_event(**overrides) -> dict:
    base = {
        "event_kind": "joiner",
        "principal_type": "service_account",
        "principal_id": "ci-deploy-bot@ops.example.org",
        "identity_provider": "keycloak",
        "effective_at": EFFECTIVE_AT,
        "add_set": ["read.logs", "write.reports"],
        "remove_set": [],
    }
    base.update(overrides)
    return base


def _chain_to_confirmation(observed: list) -> tuple[dict, dict]:
    event = ingest_lifecycle_event(_raw_event(), "hr://events/1001")
    identity = resolve_identity(event)
    delta = apply_capability_delta(event, identity)
    return identity, confirm_grant_revoke(delta, observed)


# --------------------------------------------------------------------------- #
# ingest.ingest_lifecycle_event                                               #
# --------------------------------------------------------------------------- #


def test_ingest_happy_path_per_event_kind() -> None:
    joiner = ingest_lifecycle_event(_raw_event(), "hr://events/1001")
    assert joiner["event_kind"] == "joiner"
    assert joiner["add_set"] == ["read.logs", "write.reports"]
    leaver = ingest_lifecycle_event(
        _raw_event(event_kind="leaver", add_set=[], remove_set=["read.logs"]),
        "hr://events/1002",
    )
    assert leaver["remove_set"] == ["read.logs"]
    mover = ingest_lifecycle_event(
        _raw_event(
            event_kind="mover",
            add_set=["read.reports"],
            remove_set=["write.reports"],
        ),
        "hr://events/1003",
    )
    assert mover["add_set"] == ["read.reports"]
    assert mover["remove_set"] == ["write.reports"]


def test_ingest_enforces_per_kind_delta_shape() -> None:
    with pytest.raises(InvalidLifecycleEventError, match="joiner.*add_set"):
        ingest_lifecycle_event(_raw_event(add_set=[]), "hr://events/1")
    with pytest.raises(InvalidLifecycleEventError, match="joiner.*remove_set"):
        ingest_lifecycle_event(
            _raw_event(remove_set=["admin.panel"]), "hr://events/2"
        )
    with pytest.raises(InvalidLifecycleEventError, match="leaver"):
        ingest_lifecycle_event(
            _raw_event(event_kind="leaver", add_set=[], remove_set=[]),
            "hr://events/3",
        )
    with pytest.raises(InvalidLifecycleEventError, match="mover"):
        ingest_lifecycle_event(
            _raw_event(event_kind="mover", add_set=[], remove_set=[]),
            "hr://events/4",
        )


def test_ingest_refuses_grant_and_revoke_of_same_capability() -> None:
    with pytest.raises(InvalidLifecycleEventError, match="overlap"):
        ingest_lifecycle_event(
            _raw_event(
                event_kind="mover",
                add_set=["read.logs"],
                remove_set=["read.logs"],
            ),
            "hr://events/5",
        )


def test_ingest_canonicalises_and_gates_capability_tokens() -> None:
    record = ingest_lifecycle_event(
        _raw_event(add_set=["READ.LOGS", "read.logs", "write.reports"]),
        "hr://events/6",
    )
    assert record["add_set"] == ["read.logs", "write.reports"]
    with pytest.raises(InvalidLifecycleEventError, match=r"add_set\[0\]"):
        ingest_lifecycle_event(_raw_event(add_set=["*.logs"]), "hr://events/7")


def test_ingest_gates_enums_principals_and_timestamps() -> None:
    with pytest.raises(InvalidLifecycleEventError, match="event_kind"):
        ingest_lifecycle_event(_raw_event(event_kind="rehire"), "hr://e/8")
    with pytest.raises(InvalidLifecycleEventError, match="out of scope"):
        ingest_lifecycle_event(
            _raw_event(principal_type="user"), "hr://e/9"
        )
    with pytest.raises(InvalidLifecycleEventError, match="principal_id"):
        ingest_lifecycle_event(
            _raw_event(principal_id="jane doe"), "hr://e/10"
        )
    with pytest.raises(InvalidLifecycleEventError, match="effective_at"):
        ingest_lifecycle_event(
            _raw_event(effective_at="2026-06-19 01:00"), "hr://e/11"
        )
    with pytest.raises(InvalidLifecycleEventError, match="lifecycle_event_ref"):
        ingest_lifecycle_event(_raw_event(), "has spaces")


# --------------------------------------------------------------------------- #
# identity.resolve_identity                                                   #
# --------------------------------------------------------------------------- #


def test_identity_resolves_from_ingested_record() -> None:
    event = ingest_lifecycle_event(_raw_event(), "hr://events/1001")
    identity = resolve_identity(event)
    assert identity == {
        "principal_type": "service_account",
        "principal_id": "ci-deploy-bot@ops.example.org",
        "identity_provider": "keycloak",
    }


# --------------------------------------------------------------------------- #
# delta.apply_capability_delta                                                #
# --------------------------------------------------------------------------- #


def test_delta_pins_the_closed_shape() -> None:
    event = ingest_lifecycle_event(_raw_event(), "hr://events/1001")
    identity = resolve_identity(event)
    delta = apply_capability_delta(event, identity)
    assert delta == {
        "event_kind": "joiner",
        "principal_id": "ci-deploy-bot@ops.example.org",
        "add_set": ["read.logs", "write.reports"],
        "remove_set": [],
        "effective_at": EFFECTIVE_AT,
    }


def test_delta_refuses_principal_mismatch() -> None:
    """The delta MUST target the resolved principal — an identity-
    resolution drift cannot silently re-point a grant."""
    event = ingest_lifecycle_event(_raw_event(), "hr://events/1001")
    other = dict(resolve_identity(event), principal_id="other-bot@ops.example.org")
    with pytest.raises(InvalidCapabilityDeltaError, match="MUST target"):
        apply_capability_delta(event, other)


# --------------------------------------------------------------------------- #
# confirmation.confirm_grant_revoke                                           #
# --------------------------------------------------------------------------- #


def test_confirmation_divergence_is_data_not_exception() -> None:
    """A missing grant comes back as confirmed=False plus detail — the
    artifact's job is to record the divergence, not to crash on it."""
    _, confirmation = _chain_to_confirmation(observed=["read.logs"])
    assert confirmation == {
        "confirmed": False,
        "capabilities": ["read.logs"],
        "missing_grants": ["write.reports"],
        "lingering_revokes": [],
    }


def test_confirmation_detects_lingering_revokes() -> None:
    event = ingest_lifecycle_event(
        _raw_event(event_kind="leaver", add_set=[], remove_set=["write.reports"]),
        "hr://events/1002",
    )
    delta = apply_capability_delta(event, resolve_identity(event))
    confirmation = confirm_grant_revoke(
        delta, ["read.logs", "write.reports"]
    )
    assert confirmation["confirmed"] is False
    assert confirmation["lingering_revokes"] == ["write.reports"]


def test_confirmation_confirms_a_clean_read_back() -> None:
    _, confirmation = _chain_to_confirmation(
        observed=["READ.LOGS", "write.reports", "read.logs"]
    )
    assert confirmation["confirmed"] is True
    assert confirmation["capabilities"] == ["read.logs", "write.reports"]
    assert confirmation["missing_grants"] == []


def test_confirmation_shape_errors_still_raise() -> None:
    with pytest.raises(InvalidConfirmationError, match="observed_capabilities"):
        _chain_to_confirmation(observed=["not a capability"])


# --------------------------------------------------------------------------- #
# artifact.derive_access_artifact_id / build_access_artifact                  #
# --------------------------------------------------------------------------- #


def _artifact_kwargs(**overrides) -> dict:
    identity, confirmation = _chain_to_confirmation(
        observed=["read.logs", "write.reports"]
    )
    base = {
        "workflow_id": "onboarding_offboarding_tracker",
        "execution_id": "exec-2026-06-19-0001",
        "compile_target": "temporal",
        "regulation_refs": ["nis2:art-21-2-i", "iso27001:a-5-16"],
        "control_refs": ["control.access_review@v1"],
        "resolved_identity": identity,
        "confirmation": confirmation,
        "captured_at": CAPTURED_AT,
        "source_url": "https://ci.example.org/runs/1",
    }
    base.update(overrides)
    return base


def test_artifact_id_is_documented_hash_and_excludes_captured_at() -> None:
    expected = hashlib.sha256(
        b"onboarding_offboarding_tracker|exec-2026-06-19-0001|temporal"
    ).hexdigest()
    record = build_access_artifact(**_artifact_kwargs())
    assert record["artifact_id"] == expected
    later = build_access_artifact(
        **_artifact_kwargs(captured_at="2026-06-19T09:00:00Z")
    )
    assert later["artifact_id"] == record["artifact_id"]


def test_artifact_carries_observed_list_but_not_the_verdict() -> None:
    """The observed capability list enters the schema envelope; the
    confirmed boolean and divergence detail deliberately stay outside
    it, consumed by the compile target."""
    identity, confirmation = _chain_to_confirmation(observed=["read.logs"])
    assert confirmation["confirmed"] is False
    record = build_access_artifact(
        **_artifact_kwargs(resolved_identity=identity, confirmation=confirmation)
    )
    assert record["capabilities"] == ["read.logs"]
    assert record["capability_count"] == 1
    for leaked in ("confirmed", "missing_grants", "lingering_revokes"):
        assert leaked not in record, (
            f"{leaked} must stay outside the F-CP-07 schema envelope"
        )


def test_artifact_owner_fields_travel_together() -> None:
    record = build_access_artifact(
        **_artifact_kwargs(
            owner_role="platform-security", owner_assigned_at="2026-01-15"
        )
    )
    assert record["owner"] == {
        "role": "platform-security",
        "assigned_at": "2026-01-15",
    }
    with pytest.raises(InvalidAccessArtifactError, match="together"):
        build_access_artifact(**_artifact_kwargs(owner_role="platform-security"))


# --------------------------------------------------------------------------- #
# The whole chain: ingest → resolve → delta → confirm → emit,                 #
# including an unconfirmed read-back, replayed to byte-identity.              #
# --------------------------------------------------------------------------- #


def test_full_chain_replays_byte_identically() -> None:
    def run_chain() -> str:
        event = ingest_lifecycle_event(
            _raw_event(
                event_kind="mover",
                add_set=["read.reports"],
                remove_set=["write.reports"],
            ),
            "hr://events/2002",
        )
        identity = resolve_identity(event)
        delta = apply_capability_delta(event, identity)
        # read-back shows the revoke lingering: unconfirmed but recorded
        confirmation = confirm_grant_revoke(
            delta, ["read.logs", "read.reports", "write.reports"]
        )
        record = build_access_artifact(
            workflow_id="onboarding_offboarding_tracker",
            execution_id="exec-2026-06-19-0002",
            compile_target="langgraph",
            regulation_refs=["nis2:art-21-2-i"],
            control_refs=["control.access_review@v1"],
            resolved_identity=identity,
            confirmation=confirmation,
            captured_at=CAPTURED_AT,
            source_url="https://ci.example.org/runs/2",
        )
        return json.dumps(
            {"confirmation": confirmation, "record": record}, sort_keys=True
        )

    first = run_chain()
    assert first == run_chain()
    payload = json.loads(first)
    assert payload["confirmation"]["confirmed"] is False
    assert payload["confirmation"]["lingering_revokes"] == ["write.reports"]
    assert payload["record"]["capabilities"] == [
        "read.logs",
        "read.reports",
        "write.reports",
    ]
