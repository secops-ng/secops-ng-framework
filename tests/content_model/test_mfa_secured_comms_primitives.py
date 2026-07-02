"""F-WF-MFA CORE-PRIM primitives: shape, happy-path, and negative tests.

Pins the contract of:

* ``content.playbooks.mfa_secured_comms.primitives.probe.probe_mfa_coverage``
* ``content.playbooks.mfa_secured_comms.primitives.assess.assess_continuous_auth``
* ``content.playbooks.mfa_secured_comms.primitives.verify.verify_oob_channel``
* ``content.playbooks.mfa_secured_comms.primitives.artifact.build_mfa_posture_attestation_artifact``

Per-target compile-target fan-out and byte-parity goldens against
``examples/{n8n,temporal,langgraph}/mfa_secured_comms/`` are covered by
the CORE-FANOUT side of this same card.
"""
from __future__ import annotations

import json

import pytest

from content.playbooks.mfa_secured_comms.primitives import (
    InvalidContinuousAuthAssessmentError,
    InvalidMfaCoverageProbeError,
    InvalidMfaPostureAttestationArtifactError,
    InvalidOobChannelVerificationError,
    assess_continuous_auth,
    build_mfa_posture_attestation_artifact,
    derive_mfa_posture_attestation_artifact_id,
    probe_mfa_coverage,
    verify_oob_channel,
)


# ---------------------------------------------------------------------------
# probe_mfa_coverage
# ---------------------------------------------------------------------------


def _probe_kwargs() -> dict:
    return {
        "auth_scope": "prod-idp-core",
        "posture_window": "2026-06-28T00:00:00Z/2026-06-29T00:00:00Z",
        "principals": [
            {
                "principal_id": "svc-scheduler@prod",
                "principal_class": "service-account",
                "factors_enrolled": ["webauthn", "totp"],
                "enforcement_state": "enforced",
                "last_mfa_at": "2026-06-28T08:15:00Z",
            },
            {
                "principal_id": "svc-worker@prod",
                "principal_class": "service-account",
                "factors_enrolled": [],
                "enforcement_state": "advisory",
            },
            {
                "principal_id": "svc-legacy@prod",
                "principal_class": "service-account",
                "factors_enrolled": [],
                "enforcement_state": "policy_gap",
            },
        ],
    }


def test_probe_happy_path_sorts_and_counts() -> None:
    out = probe_mfa_coverage(**_probe_kwargs())
    ids = [p["principal_id"] for p in out["principals"]]
    assert ids == sorted(ids)
    # webauthn/totp sorted alphabetically
    scheduler = next(p for p in out["principals"] if p["principal_id"] == "svc-scheduler@prod")
    assert scheduler["factors_enrolled"] == ["totp", "webauthn"]
    assert out["coverage_counts"]["enforced"] == 1
    assert out["coverage_counts"]["advisory"] == 1
    assert out["coverage_counts"]["policy_gap"] == 1
    assert out["coverage_counts"]["missing_factors"] == 2


def test_probe_is_deterministic_under_input_reordering() -> None:
    kw = _probe_kwargs()
    forward = probe_mfa_coverage(**kw)
    kw["principals"] = list(reversed(kw["principals"]))
    reverse = probe_mfa_coverage(**kw)
    assert json.dumps(forward, sort_keys=True) == json.dumps(reverse, sort_keys=True)


def test_probe_rejects_personal_name_principal() -> None:
    kw = _probe_kwargs()
    kw["principals"][0]["principal_id"] = "Jane Doe"
    with pytest.raises(InvalidMfaCoverageProbeError, match="principal_id"):
        probe_mfa_coverage(**kw)


def test_probe_rejects_unknown_factor_type() -> None:
    kw = _probe_kwargs()
    kw["principals"][0]["factors_enrolled"] = ["carrier_pigeon"]
    with pytest.raises(InvalidMfaCoverageProbeError, match="factors_enrolled"):
        probe_mfa_coverage(**kw)


def test_probe_rejects_enforced_with_no_factors() -> None:
    kw = _probe_kwargs()
    kw["principals"][0]["factors_enrolled"] = []
    with pytest.raises(InvalidMfaCoverageProbeError, match="enforced requires"):
        probe_mfa_coverage(**kw)


def test_probe_rejects_duplicate_principals() -> None:
    kw = _probe_kwargs()
    kw["principals"][1]["principal_id"] = kw["principals"][0]["principal_id"]
    with pytest.raises(InvalidMfaCoverageProbeError, match="duplicate"):
        probe_mfa_coverage(**kw)


def test_probe_rejects_bad_iso_last_mfa() -> None:
    kw = _probe_kwargs()
    kw["principals"][0]["last_mfa_at"] = "2026-06-28 08:15:00"
    with pytest.raises(InvalidMfaCoverageProbeError, match="last_mfa_at"):
        probe_mfa_coverage(**kw)


def test_probe_rejects_empty_principals() -> None:
    kw = _probe_kwargs()
    kw["principals"] = []
    with pytest.raises(InvalidMfaCoverageProbeError, match="non-empty"):
        probe_mfa_coverage(**kw)


# ---------------------------------------------------------------------------
# assess_continuous_auth
# ---------------------------------------------------------------------------


def _assess_kwargs() -> dict:
    return {
        "auth_scope": "prod-idp-core",
        "sessions": [
            {
                "session_id": "sess-002",
                "principal_id": "svc-scheduler@prod",
                "session_age_minutes": 30,
                "declared_cadence_minutes": 60,
            },
            {
                "session_id": "sess-001",
                "principal_id": "svc-worker@prod",
                "session_age_minutes": 120,
                "declared_cadence_minutes": 60,
            },
            {
                "session_id": "sess-003",
                "principal_id": "svc-legacy@prod",
                "session_age_minutes": 15,
            },
        ],
    }


def test_assess_happy_path_verdicts_and_sort() -> None:
    out = assess_continuous_auth(**_assess_kwargs())
    ids = [s["session_id"] for s in out["sessions"]]
    assert ids == sorted(ids)
    by_id = {s["session_id"]: s for s in out["sessions"]}
    assert by_id["sess-001"]["verdict"] == "overdue"
    assert by_id["sess-001"]["overdue_by_minutes"] == 60
    assert by_id["sess-002"]["verdict"] == "fresh"
    assert by_id["sess-003"]["verdict"] == "policy_gap"
    assert "declared_cadence_minutes" not in by_id["sess-003"]
    assert out["verdict_counts"] == {"fresh": 1, "overdue": 1, "policy_gap": 1}


def test_assess_empty_sessions_is_allowed() -> None:
    out = assess_continuous_auth(auth_scope="prod-idp-core", sessions=[])
    assert out["sessions"] == []
    assert out["verdict_counts"] == {"fresh": 0, "overdue": 0, "policy_gap": 0}


def test_assess_is_deterministic_under_input_reordering() -> None:
    kw = _assess_kwargs()
    a = assess_continuous_auth(**kw)
    kw["sessions"] = list(reversed(kw["sessions"]))
    b = assess_continuous_auth(**kw)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_assess_rejects_negative_age() -> None:
    kw = _assess_kwargs()
    kw["sessions"][0]["session_age_minutes"] = -1
    with pytest.raises(InvalidContinuousAuthAssessmentError, match=">= 0"):
        assess_continuous_auth(**kw)


def test_assess_rejects_zero_cadence() -> None:
    kw = _assess_kwargs()
    kw["sessions"][0]["declared_cadence_minutes"] = 0
    with pytest.raises(InvalidContinuousAuthAssessmentError, match="> 0"):
        assess_continuous_auth(**kw)


def test_assess_rejects_duplicate_session_ids() -> None:
    kw = _assess_kwargs()
    kw["sessions"][1]["session_id"] = kw["sessions"][0]["session_id"]
    with pytest.raises(InvalidContinuousAuthAssessmentError, match="duplicate"):
        assess_continuous_auth(**kw)


def test_assess_rejects_personal_name_principal() -> None:
    kw = _assess_kwargs()
    kw["sessions"][0]["principal_id"] = "Jane Doe"
    with pytest.raises(InvalidContinuousAuthAssessmentError, match="principal_id"):
        assess_continuous_auth(**kw)


# ---------------------------------------------------------------------------
# verify_oob_channel
# ---------------------------------------------------------------------------


def _verify_kwargs() -> dict:
    return {
        "auth_scope": "prod-idp-core",
        "posture_window": "2026-06-28T00:00:00Z/2026-06-29T00:00:00Z",
        "channels": [
            {
                "channel_id": "oob.voice.primary",
                "channel_class": "voice",
                "reachable": True,
                "independence_path_declared": True,
                "independence_path_verified": True,
                "last_tested_at": "2026-06-27T09:00:00Z",
                "owner_role": "operations-owner",
            },
            {
                "channel_id": "oob.paging.backup",
                "channel_class": "paging",
                "reachable": False,
                "independence_path_declared": True,
                "independence_path_verified": False,
                "last_tested_at": "2026-06-27T09:05:00Z",
            },
            {
                "channel_id": "oob.messaging.tertiary",
                "channel_class": "secure_messaging",
                "reachable": True,
                "independence_path_declared": False,
                "independence_path_verified": False,
                "last_tested_at": "2026-06-27T09:10:00Z",
            },
        ],
    }


def test_verify_happy_path_status_derivation() -> None:
    out = verify_oob_channel(**_verify_kwargs())
    by_id = {c["channel_id"]: c for c in out["channels"]}
    assert by_id["oob.voice.primary"]["status"] == "ready"
    assert by_id["oob.paging.backup"]["status"] == "unreachable"
    assert by_id["oob.messaging.tertiary"]["status"] == "policy_gap"
    assert out["status_counts"] == {
        "ready": 1,
        "unreachable": 1,
        "independence_failure": 0,
        "policy_gap": 1,
    }


def test_verify_independence_failure_branch() -> None:
    kw = _verify_kwargs()
    kw["channels"] = [
        {
            "channel_id": "oob.voice.primary",
            "channel_class": "voice",
            "reachable": True,
            "independence_path_declared": True,
            "independence_path_verified": False,
            "last_tested_at": "2026-06-27T09:00:00Z",
        }
    ]
    out = verify_oob_channel(**kw)
    assert out["channels"][0]["status"] == "independence_failure"


def test_verify_is_deterministic_under_input_reordering() -> None:
    kw = _verify_kwargs()
    a = verify_oob_channel(**kw)
    kw["channels"] = list(reversed(kw["channels"]))
    b = verify_oob_channel(**kw)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_verify_rejects_verified_without_declared() -> None:
    kw = _verify_kwargs()
    kw["channels"][0]["independence_path_declared"] = False
    kw["channels"][0]["independence_path_verified"] = True
    with pytest.raises(InvalidOobChannelVerificationError, match="inconsistent"):
        verify_oob_channel(**kw)


def test_verify_rejects_unknown_channel_class() -> None:
    kw = _verify_kwargs()
    kw["channels"][0]["channel_class"] = "carrier_pigeon"
    with pytest.raises(InvalidOobChannelVerificationError, match="channel_class"):
        verify_oob_channel(**kw)


def test_verify_rejects_duplicate_channel_ids() -> None:
    kw = _verify_kwargs()
    kw["channels"][1]["channel_id"] = kw["channels"][0]["channel_id"]
    with pytest.raises(InvalidOobChannelVerificationError, match="duplicate"):
        verify_oob_channel(**kw)


def test_verify_rejects_bad_last_tested_iso() -> None:
    kw = _verify_kwargs()
    kw["channels"][0]["last_tested_at"] = "yesterday"
    with pytest.raises(InvalidOobChannelVerificationError, match="last_tested_at"):
        verify_oob_channel(**kw)


def test_verify_rejects_empty_channels() -> None:
    kw = _verify_kwargs()
    kw["channels"] = []
    with pytest.raises(InvalidOobChannelVerificationError, match="non-empty"):
        verify_oob_channel(**kw)


# ---------------------------------------------------------------------------
# build_mfa_posture_attestation_artifact
# ---------------------------------------------------------------------------


def _artifact_kwargs() -> dict:
    mfa = probe_mfa_coverage(**_probe_kwargs())
    ca = assess_continuous_auth(**_assess_kwargs())
    oob = verify_oob_channel(**_verify_kwargs())
    return {
        "workflow_id": "mfa_secured_comms",
        "execution_id": "exec-2026-06-28-001",
        "regulation_refs": ["nis2:art-21-2-j", "dora:art-9-authentication"],
        "control_refs": [
            "control.mfa_state_probe@v1",
            "control.oob_channel_probe@v1",
        ],
        "auth_scope": "prod-idp-core",
        "posture_window": "2026-06-28T00:00:00Z/2026-06-29T00:00:00Z",
        "mfa_coverage_snapshot": mfa,
        "continuous_auth_assessment": ca,
        "oob_channel_status": oob,
        "captured_at": "2026-06-28T10:30:00Z",
        "source_url": "https://workflows.example.org/runs/abc",
    }


def test_artifact_happy_path_and_gap_summary() -> None:
    record = build_mfa_posture_attestation_artifact(**_artifact_kwargs())
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "mfa_posture_attestation"
    assert record["gap_summary"]["missing_mfa"] == 3  # 2 missing + 1 advisory
    assert record["gap_summary"]["policy_gap_mfa"] == 1
    assert record["gap_summary"]["stale_session"] == 1
    assert record["gap_summary"]["policy_gap_session"] == 1
    assert record["gap_summary"]["unreachable_oob"] == 1
    assert record["gap_summary"]["independence_failure_oob"] == 0
    assert record["gap_summary"]["policy_gap_oob"] == 1


def test_artifact_id_keys_on_workflow_execution_captured_at() -> None:
    derived = derive_mfa_posture_attestation_artifact_id(
        "mfa_secured_comms", "exec-2026-06-28-001", "2026-06-28T10:30:00Z"
    )
    record = build_mfa_posture_attestation_artifact(**_artifact_kwargs())
    assert record["artifact_id"] == derived


def test_artifact_id_is_compile_target_independent_by_construction() -> None:
    # The primitive does not accept compile_target -- the digest cannot
    # carry it. Belt-and-braces byte-parity check.
    a = build_mfa_posture_attestation_artifact(**_artifact_kwargs())
    b = build_mfa_posture_attestation_artifact(**_artifact_kwargs())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_artifact_rejects_scope_mismatch_against_snapshots() -> None:
    kw = _artifact_kwargs()
    kw["auth_scope"] = "other-scope"
    with pytest.raises(
        InvalidMfaPostureAttestationArtifactError, match="auth_scope"
    ):
        build_mfa_posture_attestation_artifact(**kw)


def test_artifact_rejects_bad_regulation_ref() -> None:
    kw = _artifact_kwargs()
    kw["regulation_refs"] = ["NIS2:art-21"]
    with pytest.raises(
        InvalidMfaPostureAttestationArtifactError, match="regulation_refs"
    ):
        build_mfa_posture_attestation_artifact(**kw)


def test_artifact_rejects_bad_control_ref() -> None:
    kw = _artifact_kwargs()
    kw["control_refs"] = ["control.mfa_state_probe"]  # missing @vN
    with pytest.raises(
        InvalidMfaPostureAttestationArtifactError, match="control_refs"
    ):
        build_mfa_posture_attestation_artifact(**kw)


def test_artifact_rejects_bad_workflow_id() -> None:
    kw = _artifact_kwargs()
    kw["workflow_id"] = "MFA_secured_comms"
    with pytest.raises(
        InvalidMfaPostureAttestationArtifactError, match="workflow_id"
    ):
        build_mfa_posture_attestation_artifact(**kw)


def test_artifact_rejects_bad_captured_at() -> None:
    kw = _artifact_kwargs()
    kw["captured_at"] = "2026-06-28 10:30:00"
    with pytest.raises(
        InvalidMfaPostureAttestationArtifactError, match="captured_at"
    ):
        build_mfa_posture_attestation_artifact(**kw)


def test_artifact_supports_optional_owner_and_retention() -> None:
    kw = _artifact_kwargs()
    kw["owner_role"] = "authentication-owner"
    kw["owner_assigned_at"] = "2026-06-28"
    kw["retention"] = "P2Y"
    record = build_mfa_posture_attestation_artifact(**kw)
    assert record["owner"] == {
        "role": "authentication-owner",
        "assigned_at": "2026-06-28",
    }
    assert record["retention"] == "P2Y"


def test_artifact_owner_role_and_assigned_at_must_pair() -> None:
    kw = _artifact_kwargs()
    kw["owner_role"] = "authentication-owner"
    with pytest.raises(
        InvalidMfaPostureAttestationArtifactError, match="together"
    ):
        build_mfa_posture_attestation_artifact(**kw)


# ---------------------------------------------------------------------------
# End-to-end determinism: probe -> assess -> verify -> artifact,
# re-emitted at the same captured_at, is byte-identical.
# ---------------------------------------------------------------------------


def _pipeline_artifact() -> dict:
    return build_mfa_posture_attestation_artifact(**_artifact_kwargs())


def test_pipeline_is_deterministic_at_the_bytes_level() -> None:
    a = _pipeline_artifact()
    b = _pipeline_artifact()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_pipeline_artifact_id_is_stable_across_reruns() -> None:
    a = _pipeline_artifact()
    b = _pipeline_artifact()
    assert a["artifact_id"] == b["artifact_id"]
