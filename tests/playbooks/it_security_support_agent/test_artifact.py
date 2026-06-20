"""Unit tests for the build_interaction_artifact primitive (F-WF-12 PRIM)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from content.playbooks.it_security_support_agent.primitives import (
    InvalidInteractionArtifactError,
    attempt_automated_resolution,
    build_interaction_artifact,
    classify_request,
    derive_interaction_artifact_id,
    derive_interaction_incident_id,
    escalate_with_human_handoff,
    ingest_support_request,
)

# Resolve the schema relative to the repo root so the test runs from any
# pytest cwd. The schema lives in schemas/evidence/incidents.schema.json.
_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "schemas"
    / "evidence"
    / "incidents.schema.json"
)


def _pipeline(
    *,
    category: str = "actionable",
    outcome: str = "resolved",
    actions: list[str] | None = None,
    policy_override: bool = False,
    cross_border: bool = False,
    execution_id: str = "exec-1",
) -> dict:
    """Run all four upstream primitives and emit a candidate artifact."""
    if actions is None:
        actions = ["net.restart_tunnel"] if outcome != "not_attempted" else []
    req = ingest_support_request(
        {
            "request_kind": category,
            "requester_handle": "helpdesk-rota",
            "declared_symptom": "vpn drops every five minutes",
            "received_at": "2026-06-01T12:00:00Z",
        },
        "ticket/abc-1",
    )
    cls = classify_request(
        req,
        {
            "category": category,
            "severity": "Medium",
            "rule_ids": ["cls.network", "sev.medium"],
            "policy_version": "v1.2.0",
        },
    )
    res = attempt_automated_resolution(
        req,
        cls,
        {
            "outcome": outcome,
            "declared_action_set": actions,
            "observed_state": "post-attempt state",
        },
    )
    hand_inputs: dict = {"policy_override": policy_override}
    # When the closed rule fires, supply the required responder fields.
    if (
        category == "incident-shaped"
        or outcome != "resolved"
        or policy_override
    ):
        hand_inputs["responder_queue"] = "soc-oncall"
        hand_inputs["acknowledgement_ref"] = "queue/recv-1"
    hand = escalate_with_human_handoff(cls, res, hand_inputs)

    return build_interaction_artifact(
        workflow_id="it_security_support_agent",
        execution_id=execution_id,
        regulation_refs=["nis2:art21.2.b"],
        control_refs=["control.support_intake@v1"],
        support_request_record=req,
        classification_verdict=cls,
        automated_resolution=res,
        handoff_envelope=hand,
        captured_at="2026-06-01T12:05:00Z",
        source_url="https://example.invalid/run/1",
        owner_role="helpdesk-rota",
        owner_assigned_at="2026-06-01",
        cross_border=cross_border,
    )


class TestInteractionArtifactShape:
    def test_top_level_required_fields_present(self) -> None:
        art = _pipeline()
        for key in (
            "schema_version",
            "artifact_id",
            "stream",
            "incident_id",
            "execution_id",
            "regulation_refs",
            "control_refs",
            "classification",
            "lifecycle",
            "notification_timeline",
            "owner",
            "captured_at",
            "provenance",
        ):
            assert key in art, f"missing required field {key!r}"

    def test_schema_version_pinned(self) -> None:
        art = _pipeline()
        assert art["schema_version"] == "1.0.0"
        assert art["stream"] == "incidents"

    def test_artifact_id_is_sha256_hex(self) -> None:
        art = _pipeline()
        assert len(art["artifact_id"]) == 64
        assert all(c in "0123456789abcdef" for c in art["artifact_id"])

    def test_incident_id_is_uuid_shape(self) -> None:
        import re

        art = _pipeline()
        assert re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
            r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            art["incident_id"],
        )

    def test_provenance_carries_captured_at(self) -> None:
        art = _pipeline()
        assert art["provenance"]["source_url"].startswith("https://")
        assert (
            art["provenance"]["captured_at"]
            == "2026-06-01T12:05:00Z"
        )

    def test_lifecycle_detected_at_is_received_at(self) -> None:
        art = _pipeline()
        assert (
            art["lifecycle"]["detected_at"]
            == "2026-06-01T12:00:00Z"
        )


class TestClassificationDerivation:
    def test_closure_path_significant_false(self) -> None:
        art = _pipeline(outcome="resolved")
        assert art["classification"]["significant"] is False
        assert art["classification"]["rule_ids"] == []
        assert (
            "closed via automated resolution"
            in art["classification"]["reasons"][0]
        )

    def test_incident_shaped_significant_true(self) -> None:
        art = _pipeline(category="incident-shaped", outcome="not_attempted")
        assert art["classification"]["significant"] is True
        assert art["classification"]["rule_ids"] == [
            "sig.support_incident_handoff"
        ]

    def test_unresolved_significant_true(self) -> None:
        art = _pipeline(outcome="failed")
        assert art["classification"]["rule_ids"] == [
            "sig.support_handoff_unresolved"
        ]
        assert art["classification"]["significant"] is True

    def test_policy_override_significant_true(self) -> None:
        art = _pipeline(outcome="resolved", policy_override=True)
        assert art["classification"]["rule_ids"] == [
            "sig.support_handoff_policy_override"
        ]
        assert art["classification"]["significant"] is True

    def test_cross_border_passthrough(self) -> None:
        art = _pipeline(cross_border=True)
        assert art["classification"]["cross_border"] is True


class TestDeterministicIds:
    def test_artifact_id_derives_from_incident_and_execution(self) -> None:
        incident_id = derive_interaction_incident_id(
            "it_security_support_agent", "exec-1"
        )
        artifact_id = derive_interaction_artifact_id(
            incident_id, "exec-1"
        )
        art = _pipeline(execution_id="exec-1")
        assert art["incident_id"] == incident_id
        assert art["artifact_id"] == artifact_id

    def test_same_workflow_execution_pins_same_incident_id(self) -> None:
        a = derive_interaction_incident_id(
            "it_security_support_agent", "exec-z"
        )
        b = derive_interaction_incident_id(
            "it_security_support_agent", "exec-z"
        )
        assert a == b

    def test_different_executions_different_artifact_ids(self) -> None:
        a = _pipeline(execution_id="exec-1")
        b = _pipeline(execution_id="exec-2")
        assert a["artifact_id"] != b["artifact_id"]
        assert a["incident_id"] != b["incident_id"]

    def test_byte_identical_reemission_inside_same_execution(self) -> None:
        a = _pipeline(execution_id="exec-stable")
        b = _pipeline(execution_id="exec-stable")
        assert json.dumps(a, sort_keys=True) == json.dumps(
            b, sort_keys=True
        )


class TestArtifactRejections:
    def test_bad_workflow_id(self) -> None:
        with pytest.raises(InvalidInteractionArtifactError):
            build_interaction_artifact(
                workflow_id="HasCaps",
                execution_id="e",
                regulation_refs=["nis2:x"],
                control_refs=["control.support@v1"],
                support_request_record={
                    "received_at": "2026-06-01T12:00:00Z"
                },
                classification_verdict={},
                automated_resolution={},
                handoff_envelope={
                    "handoff_fired": False,
                    "trigger_reason": "automated_resolution_closure",
                },
                captured_at="2026-06-01T12:05:00Z",
                source_url="https://x",
                owner_role="helpdesk-rota",
                owner_assigned_at="2026-06-01",
            )

    def test_empty_regulation_refs(self) -> None:
        with pytest.raises(InvalidInteractionArtifactError):
            build_interaction_artifact(
                workflow_id="it_security_support_agent",
                execution_id="e",
                regulation_refs=[],
                control_refs=["control.support@v1"],
                support_request_record={
                    "received_at": "2026-06-01T12:00:00Z"
                },
                classification_verdict={},
                automated_resolution={},
                handoff_envelope={
                    "handoff_fired": False,
                    "trigger_reason": "automated_resolution_closure",
                },
                captured_at="2026-06-01T12:05:00Z",
                source_url="https://x",
                owner_role="helpdesk-rota",
                owner_assigned_at="2026-06-01",
            )

    def test_handoff_envelope_unknown_trigger_when_fired(self) -> None:
        with pytest.raises(
            InvalidInteractionArtifactError, match="fired-handoff vocabulary"
        ):
            build_interaction_artifact(
                workflow_id="it_security_support_agent",
                execution_id="e",
                regulation_refs=["nis2:x"],
                control_refs=["control.support@v1"],
                support_request_record={
                    "received_at": "2026-06-01T12:00:00Z"
                },
                classification_verdict={},
                automated_resolution={},
                handoff_envelope={
                    "handoff_fired": True,
                    "trigger_reason": "something_else",
                },
                captured_at="2026-06-01T12:05:00Z",
                source_url="https://x",
                owner_role="helpdesk-rota",
                owner_assigned_at="2026-06-01",
            )

    def test_handoff_envelope_wrong_closure_reason(self) -> None:
        with pytest.raises(
            InvalidInteractionArtifactError, match="automated_resolution_closure"
        ):
            build_interaction_artifact(
                workflow_id="it_security_support_agent",
                execution_id="e",
                regulation_refs=["nis2:x"],
                control_refs=["control.support@v1"],
                support_request_record={
                    "received_at": "2026-06-01T12:00:00Z"
                },
                classification_verdict={},
                automated_resolution={},
                handoff_envelope={
                    "handoff_fired": False,
                    "trigger_reason": "policy_override",  # wrong on closure
                },
                captured_at="2026-06-01T12:05:00Z",
                source_url="https://x",
                owner_role="helpdesk-rota",
                owner_assigned_at="2026-06-01",
            )

    def test_owner_assigned_at_must_be_date(self) -> None:
        with pytest.raises(InvalidInteractionArtifactError):
            _ = build_interaction_artifact(
                workflow_id="it_security_support_agent",
                execution_id="e",
                regulation_refs=["nis2:x"],
                control_refs=["control.support@v1"],
                support_request_record={
                    "received_at": "2026-06-01T12:00:00Z"
                },
                classification_verdict={},
                automated_resolution={},
                handoff_envelope={
                    "handoff_fired": False,
                    "trigger_reason": "automated_resolution_closure",
                },
                captured_at="2026-06-01T12:05:00Z",
                source_url="https://x",
                owner_role="helpdesk-rota",
                owner_assigned_at="not-a-date",
            )

    def test_bad_commit_sha(self) -> None:
        with pytest.raises(InvalidInteractionArtifactError):
            build_interaction_artifact(
                workflow_id="it_security_support_agent",
                execution_id="e",
                regulation_refs=["nis2:x"],
                control_refs=["control.support@v1"],
                support_request_record={
                    "received_at": "2026-06-01T12:00:00Z"
                },
                classification_verdict={},
                automated_resolution={},
                handoff_envelope={
                    "handoff_fired": False,
                    "trigger_reason": "automated_resolution_closure",
                },
                captured_at="2026-06-01T12:05:00Z",
                source_url="https://x",
                owner_role="helpdesk-rota",
                owner_assigned_at="2026-06-01",
                commit_sha="NOT-HEX-ZZ",
            )

    def test_bad_retention(self) -> None:
        with pytest.raises(InvalidInteractionArtifactError):
            build_interaction_artifact(
                workflow_id="it_security_support_agent",
                execution_id="e",
                regulation_refs=["nis2:x"],
                control_refs=["control.support@v1"],
                support_request_record={
                    "received_at": "2026-06-01T12:00:00Z"
                },
                classification_verdict={},
                automated_resolution={},
                handoff_envelope={
                    "handoff_fired": False,
                    "trigger_reason": "automated_resolution_closure",
                },
                captured_at="2026-06-01T12:05:00Z",
                source_url="https://x",
                owner_role="helpdesk-rota",
                owner_assigned_at="2026-06-01",
                retention="forever",
            )


@pytest.mark.skipif(
    not _SCHEMA_PATH.exists(),
    reason="incidents schema not found relative to test file",
)
class TestSchemaValidation:
    """Cross-check the emitted record against the F-CP-02 schema directly.

    Uses the bundled draft-2020-12 validator. The cross-target byte-parity
    goldens land in the GOLDEN sibling card; here we only assert that
    the primitive's emitted record passes the schema on the two closed
    paths (fired / closure).
    """

    @classmethod
    @pytest.fixture(scope="class")
    def validator(cls):
        jsonschema = pytest.importorskip("jsonschema")
        with _SCHEMA_PATH.open() as f:
            schema = json.load(f)
        return jsonschema.Draft202012Validator(schema)

    def test_closure_path_validates(self, validator) -> None:
        art = _pipeline(outcome="resolved")
        errors = list(validator.iter_errors(art))
        assert errors == [], "\n".join(e.message for e in errors)

    def test_fired_path_validates(self, validator) -> None:
        art = _pipeline(category="incident-shaped", outcome="not_attempted")
        errors = list(validator.iter_errors(art))
        assert errors == [], "\n".join(e.message for e in errors)

    def test_policy_override_path_validates(self, validator) -> None:
        art = _pipeline(policy_override=True)
        errors = list(validator.iter_errors(art))
        assert errors == [], "\n".join(e.message for e in errors)
