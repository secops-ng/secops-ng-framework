"""Unit tests for the alert-triage typed-payload validators.

Covers both source shapes:

* Happy path: valid push and pull payloads materialise into the right
  frozen Pydantic models.
* Reject paths: missing fields, unknown fields, wrong types, naive
  datetimes, empty refs, discriminator mismatch, unsupported source
  shape, non-mapping input.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from content.playbooks.alert_triage.primitives import (
    PayloadValidationError,
    SUPPORTED_SHAPES,
    validate_alert_payload,
)
from content.playbooks.alert_triage.payloads import (
    PullAlertStorePayload,
    PushDetectionPipelinePayload,
)


_PUSH = {
    "alert_id": "alert-001",
    "received_at": "2026-06-04T12:00:00+00:00",
    "detection_rule_id": "rule.cred_access@v1",
    "subject_ref": "user:alice",
    "asset_ref": "host:web-01",
    "severity_hint": "p2_high",
    "evidence_event_uids": ["evt-1", "evt-2"],
}

_PULL = {
    "alert_id": "alert-002",
    "received_at": "2026-06-04T12:05:00+00:00",
    "store_ref": "siem-eu-west",
    "classification": "credential-access",
    "subject_ref": "user:bob",
    "asset_ref": "host:db-03",
}


class TestSupportedShapes:
    def test_alphabet_pinned(self) -> None:
        assert SUPPORTED_SHAPES == (
            "push_detection_pipeline",
            "pull_alert_store",
        )


class TestPushHappyPath:
    def test_validates(self) -> None:
        p = validate_alert_payload(_PUSH, source_shape="push_detection_pipeline")
        assert isinstance(p, PushDetectionPipelinePayload)
        assert p.alert_id == "alert-001"
        assert p.severity_hint == "p2_high"
        assert p.evidence_event_uids == ("evt-1", "evt-2")

    def test_discriminator_synthesised_when_omitted(self) -> None:
        # The dispatcher fills in source_shape from the argument when
        # the wire omitted it. This is the only field synthesised.
        p = validate_alert_payload(_PUSH, source_shape="push_detection_pipeline")
        assert p.source_shape == "push_detection_pipeline"

    def test_discriminator_match_accepted(self) -> None:
        raw = {**_PUSH, "source_shape": "push_detection_pipeline"}
        p = validate_alert_payload(raw, source_shape="push_detection_pipeline")
        assert isinstance(p, PushDetectionPipelinePayload)

    def test_severity_hint_optional(self) -> None:
        raw = {k: v for k, v in _PUSH.items() if k != "severity_hint"}
        p = validate_alert_payload(raw, source_shape="push_detection_pipeline")
        assert p.severity_hint is None


class TestPullHappyPath:
    def test_validates(self) -> None:
        p = validate_alert_payload(_PULL, source_shape="pull_alert_store")
        assert isinstance(p, PullAlertStorePayload)
        assert p.store_ref == "siem-eu-west"
        assert p.classification == "credential-access"


class TestRejectPaths:
    def test_non_mapping_rejected(self) -> None:
        with pytest.raises(PayloadValidationError, match="must be a mapping"):
            validate_alert_payload(["alert-001"], source_shape="push_detection_pipeline")  # type: ignore[arg-type]

    def test_unknown_shape_rejected(self) -> None:
        with pytest.raises(PayloadValidationError, match="unknown alert source_shape"):
            validate_alert_payload(_PUSH, source_shape="webhook")

    def test_discriminator_mismatch_rejected(self) -> None:
        raw = {**_PUSH, "source_shape": "pull_alert_store"}
        with pytest.raises(PayloadValidationError, match="source_shape mismatch"):
            validate_alert_payload(raw, source_shape="push_detection_pipeline")

    def test_missing_required_field_rejected(self) -> None:
        raw = {k: v for k, v in _PUSH.items() if k != "detection_rule_id"}
        with pytest.raises(PayloadValidationError, match="failed validation"):
            validate_alert_payload(raw, source_shape="push_detection_pipeline")

    def test_unknown_field_rejected(self) -> None:
        raw = {**_PUSH, "phantom_field": "x"}
        with pytest.raises(PayloadValidationError, match="failed validation"):
            validate_alert_payload(raw, source_shape="push_detection_pipeline")

    def test_naive_received_at_rejected(self) -> None:
        raw = {**_PUSH, "received_at": "2026-06-04T12:00:00"}  # no tz
        with pytest.raises(PayloadValidationError, match="failed validation"):
            validate_alert_payload(raw, source_shape="push_detection_pipeline")

    def test_empty_alert_id_rejected(self) -> None:
        raw = {**_PUSH, "alert_id": "   "}
        with pytest.raises(PayloadValidationError, match="failed validation"):
            validate_alert_payload(raw, source_shape="push_detection_pipeline")

    def test_bad_severity_hint_rejected(self) -> None:
        raw = {**_PUSH, "severity_hint": "high"}  # not in the closed alphabet
        with pytest.raises(PayloadValidationError, match="failed validation"):
            validate_alert_payload(raw, source_shape="push_detection_pipeline")

    def test_pull_missing_classification_rejected(self) -> None:
        raw = {k: v for k, v in _PULL.items() if k != "classification"}
        with pytest.raises(PayloadValidationError, match="failed validation"):
            validate_alert_payload(raw, source_shape="pull_alert_store")

    def test_error_chain_preserved(self) -> None:
        try:
            validate_alert_payload(
                {"alert_id": "x"}, source_shape="push_detection_pipeline"
            )
        except PayloadValidationError as exc:
            assert isinstance(exc.__cause__, ValidationError)
        else:
            pytest.fail("expected PayloadValidationError")


class TestModelsAreFrozen:
    def test_push_frozen(self) -> None:
        p = validate_alert_payload(_PUSH, source_shape="push_detection_pipeline")
        with pytest.raises((ValidationError, TypeError)):
            p.alert_id = "tampered"  # type: ignore[misc]

    def test_pull_frozen(self) -> None:
        p = validate_alert_payload(_PULL, source_shape="pull_alert_store")
        with pytest.raises((ValidationError, TypeError)):
            p.alert_id = "tampered"  # type: ignore[misc]
