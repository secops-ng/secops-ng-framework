"""F-CP-07 — access evidence-artifact round-trip (shared emitter).

Pins (EMITTER SKELETON scope — n8n and LangGraph adapters land in the
CORE-FANOUT sibling cards; per-target byte-parity goldens land in the
EXTEND-tests sibling):

1. The shared emitter writes a record that validates against
   ``schemas/evidence/access.schema.json``.
2. The ``artifact_id`` is deterministic on
   ``(workflow_id, execution_id, compile_target)`` — same inputs reproduce
   the same id; different inputs do not. ``captured_at`` is deliberately
   *not* part of the id.
3. The record persists to disk under ``<output_dir>/<artifact_id>.json``
   and re-reads byte-identical to the rendered record.
4. The Temporal activity wrapper delegates to the shared helper and
   produces the same on-disk record for the same context.
5. Public-bar discipline: the emitter accepts role-shaped principal
   identifiers and `verb.resource` capability tokens only;
   personal-user identities, free-text capabilities, and
   credential-shaped strings are rejected at the emitter boundary.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    AccessContext,
    CallerIdentity,
    derive_access_artifact_id,
    emit_access_artifact,
    render_access_artifact,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
ACCESS_SCHEMA = SCHEMAS / "evidence" / "access.schema.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(ACCESS_SCHEMA))


def _ctx(**overrides) -> AccessContext:
    base = dict(
        workflow_id="incident_management",
        execution_id="temporal:wf-run-access-001",
        compile_target="temporal",
        regulation_refs=("nis2:art-21-2-i",),
        control_refs=(
            "control.jml_evidence@v1",
            "control.privileged_access_review@v1",
        ),
        caller_identity=CallerIdentity(
            principal_type="workflow_runtime",
            principal_id="temporal-worker-incident-mgmt",
            identity_provider="temporal",
        ),
        capabilities=(
            "secrets.read",
            "workflows.execute",
            "incidents.classify",
        ),
        capability_count=3,
        captured_at=datetime(2026, 6, 9, 5, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/access-001",
        owner_role="identity-wg",
        owner_assigned_at="2026-01-15",
        commit_sha="deadbeef0123456789",
    )
    base.update(overrides)
    return AccessContext(**base)


# --------------------------------------------------------------------------- #
# Schema / determinism pins                                                   #
# --------------------------------------------------------------------------- #


def test_rendered_record_validates_against_schema() -> None:
    record = render_access_artifact(_ctx())
    _validator().validate(record)


def test_artifact_id_is_deterministic_on_anchors() -> None:
    ctx_a = _ctx()
    assert (
        render_access_artifact(ctx_a)["artifact_id"]
        == render_access_artifact(ctx_a)["artifact_id"]
    )
    expected = derive_access_artifact_id(
        ctx_a.workflow_id, ctx_a.execution_id, ctx_a.compile_target
    )
    assert render_access_artifact(ctx_a)["artifact_id"] == expected
    ctx_b = _ctx(execution_id="temporal:wf-run-access-002")
    rendered_b = render_access_artifact(ctx_b)
    assert (
        rendered_b["artifact_id"]
        != render_access_artifact(ctx_a)["artifact_id"]
    )
    assert rendered_b["workflow_id"] == render_access_artifact(ctx_a)[
        "workflow_id"
    ]
    ctx_c = _ctx(compile_target="n8n")
    assert (
        render_access_artifact(ctx_c)["artifact_id"]
        != render_access_artifact(ctx_a)["artifact_id"]
    )


def test_artifact_id_is_independent_of_captured_at() -> None:
    """Re-emissions inside the same execution stay byte-identical at the
    path level — ``captured_at`` is deliberately not part of the id.
    """
    ctx_a = _ctx()
    ctx_b = _ctx(
        captured_at=datetime(2026, 6, 9, 6, 0, 0, tzinfo=timezone.utc)
    )
    assert (
        render_access_artifact(ctx_a)["artifact_id"]
        == render_access_artifact(ctx_b)["artifact_id"]
    )


def test_emit_persists_round_trip(tmp_path: Path) -> None:
    ctx = _ctx()
    written = emit_access_artifact(ctx, tmp_path)
    assert written.exists()
    assert (
        written.name == f"{render_access_artifact(ctx)['artifact_id']}.json"
    )
    on_disk = json.loads(written.read_text("utf-8"))
    assert on_disk == render_access_artifact(ctx)
    _validator().validate(on_disk)


def test_emit_omits_owner_when_caller_supplies_none(tmp_path: Path) -> None:
    ctx = _ctx(owner_role=None, owner_assigned_at=None)
    written = emit_access_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert "owner" not in on_disk


def test_emit_omits_retention_commit_sha_capcount_provider_when_not_supplied(
    tmp_path: Path,
) -> None:
    ctx = _ctx(
        retention=None,
        commit_sha=None,
        capability_count=None,
        caller_identity=CallerIdentity(
            principal_type="service_account",
            principal_id="incident-bot",
        ),
    )
    written = emit_access_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert "retention" not in on_disk
    assert "commit_sha" not in on_disk["provenance"]
    assert "capability_count" not in on_disk
    assert "identity_provider" not in on_disk["caller_identity"]


def test_emit_accepts_all_principal_types(tmp_path: Path) -> None:
    for ptype in ("service_account", "workflow_runtime", "automation_role"):
        ctx = _ctx(
            caller_identity=CallerIdentity(
                principal_type=ptype,
                principal_id="some-role",
            ),
            execution_id=f"temporal:exec-{ptype}",
        )
        written = emit_access_artifact(ctx, tmp_path)
        on_disk = json.loads(written.read_text("utf-8"))
        _validator().validate(on_disk)
        assert on_disk["caller_identity"]["principal_type"] == ptype


# --------------------------------------------------------------------------- #
# Public-bar / shape rejections                                               #
# --------------------------------------------------------------------------- #


def test_emit_rejects_unknown_principal_type(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(
                caller_identity=CallerIdentity(
                    principal_type="end_user",
                    principal_id="some-role",
                )
            ),
            tmp_path,
        )


def test_emit_rejects_principal_id_with_whitespace(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(
                caller_identity=CallerIdentity(
                    principal_type="service_account",
                    principal_id="some role",
                )
            ),
            tmp_path,
        )


def test_emit_rejects_principal_id_with_email_localpart(
    tmp_path: Path,
) -> None:
    """Personal-user-shaped identifiers (free-text localpart with dots)
    must be rejected — the pattern allows ``@<authority>`` mailbox
    suffixes but not localparts with embedded dots in the local segment.
    """
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(
                caller_identity=CallerIdentity(
                    principal_type="service_account",
                    principal_id="jane.doe@example.com",
                )
            ),
            tmp_path,
        )


def test_emit_rejects_bad_identity_provider(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(
                caller_identity=CallerIdentity(
                    principal_type="service_account",
                    principal_id="some-role",
                    identity_provider="Some Bad Value",
                )
            ),
            tmp_path,
        )


def test_emit_rejects_empty_capabilities(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(_ctx(capabilities=()), tmp_path)


def test_emit_rejects_wildcard_capability(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(capabilities=("secrets.*",)),
            tmp_path,
        )


def test_emit_rejects_free_text_capability(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(capabilities=("read all secrets",)),
            tmp_path,
        )


def test_emit_rejects_credential_shaped_capability(tmp_path: Path) -> None:
    """An emitter passing a credential-shaped string in via the
    capabilities list must be rejected at the boundary; the schema
    regex pins ``verb.resource`` tokens only.
    """
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(capabilities=("sk-abc123xyz",)),
            tmp_path,
        )


def test_emit_rejects_duplicate_capability(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(capabilities=("secrets.read", "secrets.read")),
            tmp_path,
        )


def test_emit_rejects_unknown_compile_target(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(_ctx(compile_target="make"), tmp_path)


def test_emit_rejects_bad_workflow_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(_ctx(workflow_id="Bad ID"), tmp_path)


def test_emit_rejects_bad_control_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(control_refs=("not-a-control-ref",)), tmp_path
        )


def test_emit_rejects_bad_regulation_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(regulation_refs=("invented:ref",)), tmp_path
        )


def test_emit_rejects_naive_captured_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(captured_at=datetime(2026, 6, 9, 5, 0, 0)),
            tmp_path,
        )


def test_emit_rejects_partial_owner_block(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(owner_role="identity-wg", owner_assigned_at=None),
            tmp_path,
        )


def test_emit_rejects_bad_owner_assigned_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(
            _ctx(owner_assigned_at="2026/01/15"),
            tmp_path,
        )


def test_emit_rejects_bad_commit_sha(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(_ctx(commit_sha="not-hex"), tmp_path)


def test_emit_rejects_bad_retention(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(_ctx(retention="2years"), tmp_path)


def test_emit_rejects_negative_capability_count(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_access_artifact(_ctx(capability_count=-1), tmp_path)


# --------------------------------------------------------------------------- #
# Temporal activity wrapper                                                   #
# --------------------------------------------------------------------------- #


def test_temporal_activity_wraps_shared_helper(tmp_path: Path) -> None:
    """Happy-path Temporal pin required by the F-CP-07 EMITTER SKELETON.

    The activity-level test asserts one well-formed access evidence
    record is emitted per workflow execution by exercising the
    Temporal-side wrapper end-to-end.
    """
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_access_artifact_activity

    ctx = _ctx()
    written_str = asyncio.run(
        emit_access_artifact_activity(ctx, str(tmp_path))
    )
    written = Path(written_str)
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_access_artifact(ctx)
    written_files = [
        p for p in Path(tmp_path).iterdir() if p.suffix == ".json"
    ]
    assert len(written_files) == 1
    assert written_files[0].name == f"{on_disk['artifact_id']}.json"


# --------------------------------------------------------------------------- #
# CORE-FANOUT — n8n + LangGraph adapters                                      #
# --------------------------------------------------------------------------- #


def _payload_from_ctx(ctx: AccessContext) -> dict:
    """Render an AccessContext as the JSON-native payload an n8n node ships.

    Mirrors the wire shape an ``executeCommand`` / ``Code`` node hands to
    the Python helper: nested ``caller_identity`` as a JSON object,
    timestamps as ISO-8601 strings, sequence fields as JSON arrays.
    Optional fields are omitted when the source context omits them.
    """
    identity = ctx.caller_identity
    identity_payload: dict = {
        "principal_type": identity.principal_type,
        "principal_id": identity.principal_id,
    }
    if identity.identity_provider is not None:
        identity_payload["identity_provider"] = identity.identity_provider

    payload: dict = {
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "caller_identity": identity_payload,
        "capabilities": list(ctx.capabilities),
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": ctx.source_url,
    }
    if ctx.capability_count is not None:
        payload["capability_count"] = ctx.capability_count
    if ctx.owner_role is not None:
        payload["owner_role"] = ctx.owner_role
    if ctx.owner_assigned_at is not None:
        payload["owner_assigned_at"] = ctx.owner_assigned_at
    if ctx.commit_sha is not None:
        payload["commit_sha"] = ctx.commit_sha
    if ctx.retention is not None:
        payload["retention"] = ctx.retention
    return payload


def test_n8n_adapter_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_access_artifact_n8n

    ctx = _ctx()
    result = emit_access_artifact_n8n(_payload_from_ctx(ctx), tmp_path)
    written = Path(result["artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_access_artifact(ctx)
    assert result["artifact_id"] == on_disk["artifact_id"]
    assert written.name == f"{on_disk['artifact_id']}.json"
    # One artifact per workflow execution.
    written_files = [p for p in Path(tmp_path).iterdir() if p.suffix == ".json"]
    assert len(written_files) == 1


def test_langgraph_node_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import emit_access_artifact_node

    ctx = _ctx()
    state = {
        "access_context": ctx,
        "evidence_output_dir": str(tmp_path),
    }
    update = emit_access_artifact_node(state)
    written = Path(update["access_artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_access_artifact(ctx)
    assert update["access_artifact_id"] == on_disk["artifact_id"]
    # One artifact per workflow execution.
    written_files = [p for p in Path(tmp_path).iterdir() if p.suffix == ".json"]
    assert len(written_files) == 1


def test_all_three_targets_produce_byte_identical_records(tmp_path: Path) -> None:
    """CORE-FANOUT parity pin.

    The whole point of the shared emitter is that the three compile
    targets cannot drift on record shape. Each adapter writes the same
    context into its own subdirectory; the on-disk JSON must match byte
    for byte across targets. Per-target byte-parity goldens against a
    checked-in fixture land in the EXTEND-tests sibling; this test
    pins the cross-target equivalence today.
    """
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_access_artifact_activity
    from compilers.n8n.evidence import emit_access_artifact_n8n
    from compilers.langgraph.evidence import emit_access_artifact_node

    ctx = _ctx()

    tmp_temporal = tmp_path / "temporal"
    tmp_n8n = tmp_path / "n8n"
    tmp_langgraph = tmp_path / "langgraph"

    temporal_path = Path(
        asyncio.run(emit_access_artifact_activity(ctx, str(tmp_temporal)))
    )
    n8n_result = emit_access_artifact_n8n(_payload_from_ctx(ctx), tmp_n8n)
    n8n_path = Path(n8n_result["artifact_path"])
    langgraph_update = emit_access_artifact_node(
        {
            "access_context": ctx,
            "evidence_output_dir": str(tmp_langgraph),
        }
    )
    langgraph_path = Path(langgraph_update["access_artifact_path"])

    # Same artifact_id across all three targets.
    assert temporal_path.stem == n8n_path.stem == langgraph_path.stem

    # Byte-identical on-disk JSON.
    bytes_temporal = temporal_path.read_bytes()
    bytes_n8n = n8n_path.read_bytes()
    bytes_langgraph = langgraph_path.read_bytes()
    assert bytes_temporal == bytes_n8n == bytes_langgraph
