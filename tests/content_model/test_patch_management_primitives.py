"""F-WF-PATCH CORE-PRIM primitives: shape, happy-path, and negative tests.

Pins the contract of:

* ``content.playbooks.patch_management.primitives.detect.detect_patch_availability``
* ``content.playbooks.patch_management.primitives.classify.classify_patch_criticality``
* ``content.playbooks.patch_management.primitives.stage.stage_rollout_to_canary_ring``
* ``content.playbooks.patch_management.primitives.validate.validate_canary``
* ``content.playbooks.patch_management.primitives.fanout.fan_out_to_broad_rings``
* ``content.playbooks.patch_management.primitives.artifact.build_patch_application_evidence_artifact``

Per-target compile-target fan-out and byte-parity goldens against
``examples/{n8n,temporal,langgraph}/patch_management/`` are out of scope
(CORE-FANOUT siblings).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from content.playbooks.patch_management.primitives import (
    InvalidCanaryValidationError,
    InvalidPatchApplicationArtifactError,
    InvalidPatchCriticalityError,
    InvalidPatchDetectionError,
    InvalidPatchFanOutError,
    InvalidPatchStagingError,
    build_patch_application_evidence_artifact,
    classify_patch_criticality,
    derive_patch_application_artifact_id,
    detect_patch_availability,
    fan_out_to_broad_rings,
    stage_rollout_to_canary_ring,
    validate_canary,
)

REPO = Path(__file__).resolve().parents[2]
PATCH_EVIDENCE_SCHEMA = REPO / "schemas" / "evidence" / "patch.schema.json"


def _validator() -> Draft202012Validator:
    return Draft202012Validator(
        json.loads(PATCH_EVIDENCE_SCHEMA.read_text(encoding="utf-8"))
    )


# ---------------------------------------------------------------------------
# detect_patch_availability
# ---------------------------------------------------------------------------


def test_detect_happy_path_in_scope() -> None:
    out = detect_patch_availability(
        update_subject="pkg.openssl",
        update_reference="CVE-2026-12345",
        advisory_kind="vendor_feed",
        tracked_inventory=["pkg.openssl", "pkg.curl"],
    )
    assert out == {
        "update_subject": "pkg.openssl",
        "update_reference": "CVE-2026-12345",
        "advisory_kind": "vendor_feed",
        "in_scope": True,
    }


def test_detect_not_in_scope_marked_explicitly() -> None:
    out = detect_patch_availability(
        update_subject="pkg.unknown",
        update_reference="REL-9.0",
        advisory_kind="upstream_release",
        tracked_inventory=["pkg.openssl"],
    )
    assert out["in_scope"] is False


def test_detect_rejects_bad_subject_shape() -> None:
    with pytest.raises(InvalidPatchDetectionError, match="update_subject"):
        detect_patch_availability(
            update_subject="contains spaces",
            update_reference="REL-1",
            advisory_kind="vendor_feed",
            tracked_inventory=["pkg.x"],
        )


def test_detect_rejects_unknown_advisory_kind() -> None:
    with pytest.raises(InvalidPatchDetectionError, match="advisory_kind"):
        detect_patch_availability(
            update_subject="pkg.x",
            update_reference="REL-1",
            advisory_kind="rumour_mill",
            tracked_inventory=["pkg.x"],
        )


def test_detect_rejects_duplicate_inventory() -> None:
    with pytest.raises(InvalidPatchDetectionError, match="duplicate"):
        detect_patch_availability(
            update_subject="pkg.x",
            update_reference="REL-1",
            advisory_kind="vendor_feed",
            tracked_inventory=["pkg.x", "pkg.x"],
        )


# ---------------------------------------------------------------------------
# classify_patch_criticality
# ---------------------------------------------------------------------------


def test_classify_exploit_forces_critical() -> None:
    assert (
        classify_patch_criticality(
            update_subject="pkg.x",
            severity_band="low",
            exploit_observed=True,
            is_feature_only=False,
        )
        == "security-critical"
    )


def test_classify_high_severity_is_critical() -> None:
    assert (
        classify_patch_criticality(
            update_subject="pkg.x",
            severity_band="high",
            exploit_observed=False,
            is_feature_only=False,
        )
        == "security-critical"
    )


def test_classify_medium_is_routine() -> None:
    assert (
        classify_patch_criticality(
            update_subject="pkg.x",
            severity_band="medium",
            exploit_observed=False,
            is_feature_only=False,
        )
        == "security-routine"
    )


def test_classify_feature_only_is_feature_only() -> None:
    assert (
        classify_patch_criticality(
            update_subject="pkg.x",
            severity_band="low",
            exploit_observed=False,
            is_feature_only=True,
        )
        == "feature-only"
    )


def test_classify_informational_no_feature_flag_is_feature_only() -> None:
    assert (
        classify_patch_criticality(
            update_subject="pkg.x",
            severity_band="informational",
            exploit_observed=False,
            is_feature_only=False,
        )
        == "feature-only"
    )


def test_classify_deadline_missed_sentinel() -> None:
    assert (
        classify_patch_criticality(
            update_subject="pkg.x",
            severity_band="low",
            exploit_observed=False,
            is_feature_only=False,
            deadline_missed=True,
        )
        == "unclassified"
    )


def test_classify_feature_only_and_exploit_conflict_rejected() -> None:
    with pytest.raises(InvalidPatchCriticalityError, match="exploit"):
        classify_patch_criticality(
            update_subject="pkg.x",
            severity_band="low",
            exploit_observed=True,
            is_feature_only=True,
        )


def test_classify_feature_only_with_critical_band_rejected() -> None:
    with pytest.raises(InvalidPatchCriticalityError, match="severity_band"):
        classify_patch_criticality(
            update_subject="pkg.x",
            severity_band="critical",
            exploit_observed=False,
            is_feature_only=True,
        )


def test_classify_rejects_unknown_band() -> None:
    with pytest.raises(InvalidPatchCriticalityError, match="severity_band"):
        classify_patch_criticality(
            update_subject="pkg.x",
            severity_band="catastrophic",
            exploit_observed=False,
            is_feature_only=False,
        )


# ---------------------------------------------------------------------------
# stage_rollout_to_canary_ring
# ---------------------------------------------------------------------------


def _stage_inputs(crit: str = "security-critical") -> dict:
    return {
        "update_subject": "pkg.openssl",
        "update_reference": "CVE-2026-12345",
        "patch_criticality": crit,
        "ring_topology": ["test-fleet", "canary-eu", "broad-prod"],
    }


def test_stage_happy_path() -> None:
    out = stage_rollout_to_canary_ring(**_stage_inputs())
    assert out["canary_ring"] == "canary-eu"
    assert out["cadence"] == "immediate"
    assert len(out["staged_ring_id"]) == 64
    int(out["staged_ring_id"], 16)


def test_stage_cadence_maps_criticality() -> None:
    cadence = {
        "security-critical": "immediate",
        "security-routine": "next-window",
        "feature-only": "maintenance-window",
        "unclassified": "immediate",
        "": "immediate",
    }
    for crit, expected in cadence.items():
        assert (
            stage_rollout_to_canary_ring(**_stage_inputs(crit))["cadence"]
            == expected
        )


def test_stage_deterministic_replay() -> None:
    a = stage_rollout_to_canary_ring(**_stage_inputs())
    b = stage_rollout_to_canary_ring(**_stage_inputs())
    assert a == b


def test_stage_ring_topology_shape_enforced() -> None:
    inputs = _stage_inputs()
    inputs["ring_topology"] = ["test-fleet", "canary-eu"]
    with pytest.raises(InvalidPatchStagingError, match="exactly three"):
        stage_rollout_to_canary_ring(**inputs)


def test_stage_rejects_duplicate_rings() -> None:
    inputs = _stage_inputs()
    inputs["ring_topology"] = ["test-fleet", "test-fleet", "broad-prod"]
    with pytest.raises(InvalidPatchStagingError, match="duplicate"):
        stage_rollout_to_canary_ring(**inputs)


# ---------------------------------------------------------------------------
# validate_canary
# ---------------------------------------------------------------------------


def test_validate_canary_all_green_healthy() -> None:
    out = validate_canary(
        functional_probe="green",
        error_rate_within_threshold=True,
        latency_within_threshold=True,
        rollback_ready=True,
    )
    assert out["canary_healthy"] is True


@pytest.mark.parametrize(
    "probe,err,lat,rb",
    [
        ("red", True, True, True),
        ("unknown", True, True, True),
        ("green", False, True, True),
        ("green", True, False, True),
        ("green", True, True, False),
    ],
)
def test_validate_canary_any_failing_gate_is_unhealthy(probe, err, lat, rb) -> None:
    out = validate_canary(
        functional_probe=probe,
        error_rate_within_threshold=err,
        latency_within_threshold=lat,
        rollback_ready=rb,
    )
    assert out["canary_healthy"] is False


def test_validate_canary_rejects_unknown_probe_outcome() -> None:
    with pytest.raises(InvalidCanaryValidationError, match="functional_probe"):
        validate_canary(
            functional_probe="amber",
            error_rate_within_threshold=True,
            latency_within_threshold=True,
            rollback_ready=True,
        )


# ---------------------------------------------------------------------------
# fan_out_to_broad_rings
# ---------------------------------------------------------------------------


def _fanout_inputs(healthy: bool = True) -> dict:
    staged = stage_rollout_to_canary_ring(**_stage_inputs())["staged_ring_id"]
    return {
        "update_subject": "pkg.openssl",
        "update_reference": "CVE-2026-12345",
        "staged_ring_id": staged,
        "canary_healthy": healthy,
        "broad_rings": ["broad-eu-west", "broad-eu-north"],
    }


def test_fanout_healthy_canary_emits_digest() -> None:
    out = fan_out_to_broad_rings(**_fanout_inputs(healthy=True))
    assert len(out["broad_rollout_id"]) == 64
    int(out["broad_rollout_id"], 16)
    assert out["broad_rollout_skip_reason"] is None


def test_fanout_unhealthy_canary_emits_skip_marker() -> None:
    out = fan_out_to_broad_rings(**_fanout_inputs(healthy=False))
    assert out == {
        "broad_rollout_id": "",
        "broad_rollout_skip_reason": "canary_unhealthy",
    }


def test_fanout_skip_path_is_deterministic() -> None:
    a = fan_out_to_broad_rings(**_fanout_inputs(healthy=False))
    b = fan_out_to_broad_rings(**_fanout_inputs(healthy=False))
    assert a == b


def test_fanout_ring_order_does_not_shift_id() -> None:
    inputs_a = _fanout_inputs(healthy=True)
    inputs_b = _fanout_inputs(healthy=True)
    inputs_b["broad_rings"] = list(reversed(inputs_a["broad_rings"]))
    assert (
        fan_out_to_broad_rings(**inputs_a)["broad_rollout_id"]
        == fan_out_to_broad_rings(**inputs_b)["broad_rollout_id"]
    )


def test_fanout_rejects_bad_staged_id() -> None:
    inputs = _fanout_inputs()
    inputs["staged_ring_id"] = "not-a-digest"
    with pytest.raises(InvalidPatchFanOutError, match="staged_ring_id"):
        fan_out_to_broad_rings(**inputs)


# ---------------------------------------------------------------------------
# build_patch_application_evidence_artifact
# ---------------------------------------------------------------------------


def _healthy_artifact_kwargs() -> dict:
    staged = stage_rollout_to_canary_ring(**_stage_inputs())["staged_ring_id"]
    fanout = fan_out_to_broad_rings(**_fanout_inputs(healthy=True))
    health = validate_canary(
        functional_probe="green",
        error_rate_within_threshold=True,
        latency_within_threshold=True,
        rollback_ready=True,
    )
    return {
        "workflow_id": "patch_management",
        "execution_id": "exec-2026-06-28-001",
        "regulation_refs": ["nis2:art-21-2-e"],
        "control_refs": ["control.patch_evidence@v1"],
        "update_subject": "pkg.openssl",
        "update_reference": "CVE-2026-12345",
        "patch_criticality": "security-critical",
        "staged_ring_id": staged,
        "canary_healthy": True,
        "broad_rollout_id": fanout["broad_rollout_id"],
        "broad_rollout_skip_reason": fanout["broad_rollout_skip_reason"],
        "health_observations": health["health_observations"],
        "captured_at": "2026-06-28T10:30:00Z",
        "source_url": "https://workflows.example.org/runs/abc",
    }


def _unhealthy_artifact_kwargs() -> dict:
    staged = stage_rollout_to_canary_ring(**_stage_inputs())["staged_ring_id"]
    fanout = fan_out_to_broad_rings(**_fanout_inputs(healthy=False))
    health = validate_canary(
        functional_probe="red",
        error_rate_within_threshold=True,
        latency_within_threshold=True,
        rollback_ready=True,
    )
    return {
        "workflow_id": "patch_management",
        "execution_id": "exec-2026-06-28-002",
        "regulation_refs": [
            "nis2:art-21-2-e",
            "dora:art-9-maintenance-patch-rollout",
        ],
        "control_refs": ["control.patch_evidence@v1"],
        "update_subject": "pkg.openssl",
        "update_reference": "CVE-2026-12345",
        "patch_criticality": "security-critical",
        "staged_ring_id": staged,
        "canary_healthy": False,
        "broad_rollout_id": fanout["broad_rollout_id"],
        "broad_rollout_skip_reason": fanout["broad_rollout_skip_reason"],
        "health_observations": health["health_observations"],
        "captured_at": "2026-06-28T10:35:00Z",
        "source_url": "https://workflows.example.org/runs/def",
    }


def test_artifact_healthy_round_trip_validates() -> None:
    record = build_patch_application_evidence_artifact(
        **_healthy_artifact_kwargs()
    )
    _validator().validate(record)
    assert record["stream"] == "patch"
    assert record["canary_healthy"] is True
    assert record["broad_rollout_id"]
    assert "broad_rollout_skip_reason" not in record


def test_artifact_unhealthy_carries_skip_marker_and_validates() -> None:
    record = build_patch_application_evidence_artifact(
        **_unhealthy_artifact_kwargs()
    )
    _validator().validate(record)
    assert record["broad_rollout_id"] == ""
    assert record["broad_rollout_skip_reason"] == "canary_unhealthy"
    assert record["canary_healthy"] is False


def test_artifact_id_keys_on_workflow_execution_captured_at() -> None:
    derived = derive_patch_application_artifact_id(
        "patch_management", "exec-2026-06-28-001", "2026-06-28T10:30:00Z"
    )
    record = build_patch_application_evidence_artifact(
        **_healthy_artifact_kwargs()
    )
    assert record["artifact_id"] == derived


def test_artifact_id_is_compile_target_independent_by_construction() -> None:
    # The primitive does not even accept compile_target — the digest cannot
    # carry it. Belt-and-braces: re-emission at the same captured_at over
    # the same inputs is byte-identical.
    a = build_patch_application_evidence_artifact(**_healthy_artifact_kwargs())
    b = build_patch_application_evidence_artifact(**_healthy_artifact_kwargs())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_artifact_rejects_inconsistent_skip_marker_on_healthy() -> None:
    kw = _healthy_artifact_kwargs()
    kw["broad_rollout_skip_reason"] = "canary_unhealthy"
    with pytest.raises(
        InvalidPatchApplicationArtifactError,
        match="must be omitted",
    ):
        build_patch_application_evidence_artifact(**kw)


def test_artifact_rejects_missing_skip_marker_on_empty_broad() -> None:
    kw = _unhealthy_artifact_kwargs()
    kw["broad_rollout_skip_reason"] = None
    with pytest.raises(
        InvalidPatchApplicationArtifactError,
        match="broad_rollout_skip_reason is required",
    ):
        build_patch_application_evidence_artifact(**kw)


def test_artifact_rejects_canary_healthy_with_failing_gate() -> None:
    kw = _healthy_artifact_kwargs()
    kw["health_observations"] = {
        **kw["health_observations"],
        "rollback_ready": False,
    }
    with pytest.raises(
        InvalidPatchApplicationArtifactError,
        match="canary_healthy=True is inconsistent",
    ):
        build_patch_application_evidence_artifact(**kw)


def test_artifact_rejects_canary_unhealthy_with_all_green() -> None:
    kw = _unhealthy_artifact_kwargs()
    kw["health_observations"] = {
        "functional_probe": "green",
        "error_rate_within_threshold": True,
        "latency_within_threshold": True,
        "rollback_ready": True,
    }
    with pytest.raises(
        InvalidPatchApplicationArtifactError,
        match="canary_healthy=False is inconsistent",
    ):
        build_patch_application_evidence_artifact(**kw)


def test_artifact_rejects_canary_healthy_with_empty_broad() -> None:
    kw = _healthy_artifact_kwargs()
    kw["broad_rollout_id"] = ""
    kw["broad_rollout_skip_reason"] = "canary_unhealthy"
    with pytest.raises(
        InvalidPatchApplicationArtifactError,
        match="broad_rollout_id must be populated",
    ):
        build_patch_application_evidence_artifact(**kw)


def test_artifact_rejects_bad_regulation_ref() -> None:
    kw = _healthy_artifact_kwargs()
    kw["regulation_refs"] = ["NIS2-art-21"]  # uppercase / wrong shape
    with pytest.raises(
        InvalidPatchApplicationArtifactError,
        match="regulation_refs",
    ):
        build_patch_application_evidence_artifact(**kw)


def test_artifact_supports_optional_owner_and_retention() -> None:
    kw = _healthy_artifact_kwargs()
    kw["owner_role"] = "maintenance-wg"
    kw["owner_assigned_at"] = "2026-06-28"
    kw["retention"] = "P2Y"
    record = build_patch_application_evidence_artifact(**kw)
    _validator().validate(record)
    assert record["owner"] == {
        "role": "maintenance-wg",
        "assigned_at": "2026-06-28",
    }
    assert record["retention"] == "P2Y"


# ---------------------------------------------------------------------------
# End-to-end determinism: detect -> classify -> stage -> validate ->
# fan-out -> artifact, re-emitted at the same captured_at, is byte-identical
# at the path level. Also the unhealthy-canary skip path is deterministic.
# ---------------------------------------------------------------------------


def _full_pipeline(canary_healthy: bool) -> dict:
    detect = detect_patch_availability(
        update_subject="pkg.openssl",
        update_reference="CVE-2026-12345",
        advisory_kind="vendor_feed",
        tracked_inventory=["pkg.openssl", "pkg.curl"],
    )
    crit = classify_patch_criticality(
        update_subject=detect["update_subject"],
        severity_band="high",
        exploit_observed=False,
        is_feature_only=False,
    )
    stage = stage_rollout_to_canary_ring(
        update_subject=detect["update_subject"],
        update_reference=detect["update_reference"],
        patch_criticality=crit,
        ring_topology=["test-fleet", "canary-eu", "broad-prod"],
    )
    validate = validate_canary(
        functional_probe="green" if canary_healthy else "red",
        error_rate_within_threshold=True,
        latency_within_threshold=True,
        rollback_ready=True,
    )
    fanout = fan_out_to_broad_rings(
        update_subject=detect["update_subject"],
        update_reference=detect["update_reference"],
        staged_ring_id=stage["staged_ring_id"],
        canary_healthy=validate["canary_healthy"],
        broad_rings=["broad-eu-west", "broad-eu-north"],
    )
    return build_patch_application_evidence_artifact(
        workflow_id="patch_management",
        execution_id="exec-determinism-001",
        regulation_refs=["nis2:art-21-2-e"],
        control_refs=["control.patch_evidence@v1"],
        update_subject=detect["update_subject"],
        update_reference=detect["update_reference"],
        patch_criticality=crit,
        staged_ring_id=stage["staged_ring_id"],
        canary_healthy=validate["canary_healthy"],
        broad_rollout_id=fanout["broad_rollout_id"],
        broad_rollout_skip_reason=fanout["broad_rollout_skip_reason"],
        health_observations=validate["health_observations"],
        captured_at="2026-06-28T11:00:00Z",
        source_url="https://workflows.example.org/runs/xyz",
    )


def test_end_to_end_healthy_pipeline_is_byte_identical_on_replay() -> None:
    a = _full_pipeline(canary_healthy=True)
    b = _full_pipeline(canary_healthy=True)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    _validator().validate(a)


def test_end_to_end_unhealthy_canary_skip_is_byte_identical_on_replay() -> None:
    a = _full_pipeline(canary_healthy=False)
    b = _full_pipeline(canary_healthy=False)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert a["broad_rollout_id"] == ""
    assert a["broad_rollout_skip_reason"] == "canary_unhealthy"
    _validator().validate(a)


def test_end_to_end_artifact_id_differs_between_healthy_and_unhealthy_only_via_execution_id() -> None:
    # Same workflow_id + execution_id + captured_at => same artifact_id even
    # though the rest of the record diverges. This is the byte-parity
    # contract: artifact_id is keyed only on the path, body diverges as
    # the canary outcome dictates.
    healthy = _full_pipeline(canary_healthy=True)
    unhealthy = _full_pipeline(canary_healthy=False)
    assert healthy["artifact_id"] == unhealthy["artifact_id"]
    assert healthy != unhealthy
