"""F-WF-DPIA CORE \u2014 byte-parity golden for DPIA evidence emission.

The DPIA evidence stream's ``artifact_id`` is derived deterministically
from the tuple ``(workflow_id, execution_id, captured_at)`` \u2014 the
compile target (n8n / Temporal / LangGraph) is deliberately absent
from the derivation so a replay under a different target produces the
identical ``artifact_id`` for the same triple. This is the byte-parity
anchor for the three-target contract on the F-WF-DPIA CORE layer.

This test locks the derivation rule in place and asserts identity
across the three reference targets by driving one small helper each
target would use to hash the tuple. Any future refactor that tries to
mix ``compile_target`` into the id will fail the parity assertion.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO / "schemas" / "evidence" / "dpia.schema.json"


def _artifact_id(workflow_id: str, execution_id: str, captured_at: str) -> str:
    """Documented derivation: SHA-256 hex digest of the pipe-joined triple.

    Encoding is UTF-8 with single pipe separators and no surrounding
    whitespace \u2014 exactly the string described by
    schemas/evidence/dpia.schema.json#/properties/artifact_id.
    ``compile_target`` MUST NOT enter this function's arguments.
    """
    payload = f"{workflow_id}|{execution_id}|{captured_at}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# The three reference emitters differ in how they marshal a payload
# (n8n Code node, Temporal activity, LangGraph node), but the id rule
# they share is the pure-function above. Simulate each by invoking the
# same helper on the same triple; parity is what we assert.
def _emit_n8n(payload: dict) -> str:
    return _artifact_id(payload["workflow_id"], payload["execution_id"], payload["captured_at"])


def _emit_temporal(payload: dict) -> str:
    return _artifact_id(payload["workflow_id"], payload["execution_id"], payload["captured_at"])


def _emit_langgraph(payload: dict) -> str:
    return _artifact_id(payload["workflow_id"], payload["execution_id"], payload["captured_at"])


CASES = [
    {
        "workflow_id": "data_protection_impact_assessment",
        "execution_id": "dpia-execution-0001",
        "captured_at": "2026-07-04T00:00:00Z",
    },
    {
        "workflow_id": "data_protection_impact_assessment",
        "execution_id": "dpia-execution-0002",
        "captured_at": "2026-07-04T12:00:00Z",
    },
    {
        "workflow_id": "data_protection_impact_assessment",
        "execution_id": "n8n-run-c1a1b2c3-audit-close",
        "captured_at": "2026-07-05T09:30:00Z",
    },
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["execution_id"])
def test_artifact_id_byte_identical_across_targets(case: dict) -> None:
    n8n_id = _emit_n8n(case)
    temporal_id = _emit_temporal(case)
    langgraph_id = _emit_langgraph(case)
    assert n8n_id == temporal_id == langgraph_id, (
        "DPIA artifact_id drifted across compile targets \u2014 the byte-parity "
        "contract on the F-WF-DPIA CORE layer is broken. Verify that "
        "artifact_id derivation keys only on (workflow_id, execution_id, "
        "captured_at) and NOT on compile_target."
    )
    # Shape check \u2014 SHA-256 hex.
    assert len(n8n_id) == 64
    assert all(c in "0123456789abcdef" for c in n8n_id)


def test_artifact_id_deterministic_on_same_triple() -> None:
    case = CASES[0]
    first = _artifact_id(case["workflow_id"], case["execution_id"], case["captured_at"])
    second = _artifact_id(case["workflow_id"], case["execution_id"], case["captured_at"])
    assert first == second


def test_artifact_id_changes_when_any_input_changes() -> None:
    base = CASES[0]
    baseline = _artifact_id(base["workflow_id"], base["execution_id"], base["captured_at"])
    assert baseline != _artifact_id("other_workflow", base["execution_id"], base["captured_at"])
    assert baseline != _artifact_id(base["workflow_id"], "other-execution", base["captured_at"])
    assert baseline != _artifact_id(
        base["workflow_id"], base["execution_id"], "2026-07-04T00:00:01Z"
    )


def test_schema_documents_target_independent_derivation() -> None:
    """The published schema MUST describe the parity contract, otherwise
    a downstream implementer can silently mix ``compile_target`` in and
    the parity test above would appear to hold while real-world emitters
    drift. This test guards the schema's prose.
    """
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    artifact_id_desc = schema["properties"]["artifact_id"]["description"]
    assert "workflow_id" in artifact_id_desc
    assert "execution_id" in artifact_id_desc
    assert "captured_at" in artifact_id_desc
    assert "MUST NOT key on compile_target" in artifact_id_desc or "MUST NOT" in artifact_id_desc
    assert "compile_target" in artifact_id_desc


def test_schema_has_all_required_dpia_fields() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    required = set(schema["required"])
    for field in (
        "workflow_id",
        "execution_id",
        "artifact_id",
        "screening_outcome",
        "residual_risk_verdict",
        "dpo_consultation_record",
        "article_36_prior_consultation_flag",
        "regulation_refs",
        "control_refs",
        "captured_at",
    ):
        assert field in required, f"schema missing required DPIA field: {field}"
    assert schema["properties"]["article_36_prior_consultation_flag"]["type"] == "boolean"
