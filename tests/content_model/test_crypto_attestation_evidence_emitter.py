"""F-CP-05 — crypto-attestation evidence-artifact round-trip (shared emitter).

Pins (EMITTER SKELETON scope — n8n and LangGraph adapters land in the
CORE-FANOUT sibling card; per-target byte-parity goldens land in the
EXTEND-tests sibling):

1. The shared emitter writes a record that validates against
   ``schemas/evidence/crypto-attestation.schema.json``.
2. The ``artifact_id`` is deterministic on
   ``(workflow_id, execution_id, compile_target)`` — same inputs reproduce
   the same id; different inputs do not. ``captured_at`` is deliberately
   *not* part of the id.
3. The record persists to disk under ``<output_dir>/<artifact_id>.json``
   and re-reads byte-identical to the rendered record.
4. The Temporal activity wrapper delegates to the shared helper and
   produces the same on-disk record for the same context.
5. Public-bar discipline: the emitter accepts UPPER_SNAKE_CASE env-var
   names only; values, fragments of values, or credential-shaped
   strings are rejected at the emitter boundary.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    CryptoAttestationContext,
    SecretHandling,
    derive_crypto_attestation_artifact_id,
    emit_crypto_attestation_artifact,
    render_crypto_attestation_artifact,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
CRYPTO_ATTESTATION_SCHEMA = (
    SCHEMAS / "evidence" / "crypto-attestation.schema.json"
)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(CRYPTO_ATTESTATION_SCHEMA))


def _ctx(**overrides) -> CryptoAttestationContext:
    base = dict(
        workflow_id="incident_management",
        execution_id="temporal:wf-run-crypto-001",
        compile_target="temporal",
        regulation_refs=("nis2:art-21-2-h",),
        control_refs=("control.crypto_policy_inventory@v1",),
        secret_handling=SecretHandling(
            env_var_refs=(
                "INCIDENT_NOTIFIER_API_TOKEN",
                "CSIRT_PORTAL_CLIENT_SECRET",
            ),
            secret_count=2,
        ),
        captured_at=datetime(2026, 6, 9, 5, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/crypto-001",
        owner_role="platform-security-wg",
        owner_assigned_at="2026-01-15",
        commit_sha="deadbeef0123456789",
    )
    base.update(overrides)
    return CryptoAttestationContext(**base)


# --------------------------------------------------------------------------- #
# Schema / determinism pins                                                   #
# --------------------------------------------------------------------------- #


def test_rendered_record_validates_against_schema() -> None:
    record = render_crypto_attestation_artifact(_ctx())
    _validator().validate(record)


def test_artifact_id_is_deterministic_on_anchors() -> None:
    ctx_a = _ctx()
    # Same inputs → same id.
    assert (
        render_crypto_attestation_artifact(ctx_a)["artifact_id"]
        == render_crypto_attestation_artifact(ctx_a)["artifact_id"]
    )
    expected = derive_crypto_attestation_artifact_id(
        ctx_a.workflow_id, ctx_a.execution_id, ctx_a.compile_target
    )
    assert render_crypto_attestation_artifact(ctx_a)["artifact_id"] == expected
    # Different execution_id → different id; same workflow_id carries through.
    ctx_b = _ctx(execution_id="temporal:wf-run-crypto-002")
    rendered_b = render_crypto_attestation_artifact(ctx_b)
    assert (
        rendered_b["artifact_id"]
        != render_crypto_attestation_artifact(ctx_a)["artifact_id"]
    )
    assert rendered_b["workflow_id"] == render_crypto_attestation_artifact(
        ctx_a
    )["workflow_id"]
    # Different compile_target → different id at the same execution.
    ctx_c = _ctx(compile_target="n8n")
    assert (
        render_crypto_attestation_artifact(ctx_c)["artifact_id"]
        != render_crypto_attestation_artifact(ctx_a)["artifact_id"]
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
        render_crypto_attestation_artifact(ctx_a)["artifact_id"]
        == render_crypto_attestation_artifact(ctx_b)["artifact_id"]
    )


def test_emit_persists_round_trip(tmp_path: Path) -> None:
    ctx = _ctx()
    written = emit_crypto_attestation_artifact(ctx, tmp_path)
    assert written.exists()
    assert (
        written.name
        == f"{render_crypto_attestation_artifact(ctx)['artifact_id']}.json"
    )
    on_disk = json.loads(written.read_text("utf-8"))
    assert on_disk == render_crypto_attestation_artifact(ctx)
    _validator().validate(on_disk)


def test_emit_omits_owner_when_caller_supplies_none(tmp_path: Path) -> None:
    """Schema marks ``owner`` optional. The helper must not emit an
    empty key when the caller leaves it unset.
    """
    ctx = _ctx(owner_role=None, owner_assigned_at=None)
    written = emit_crypto_attestation_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert "owner" not in on_disk


def test_emit_omits_retention_and_commit_sha_when_not_supplied(
    tmp_path: Path,
) -> None:
    ctx = _ctx(retention=None, commit_sha=None)
    written = emit_crypto_attestation_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert "retention" not in on_disk
    assert "commit_sha" not in on_disk["provenance"]


def test_emit_accepts_zero_secrets(tmp_path: Path) -> None:
    """A workflow that consumes no secrets still emits an attestation
    to that effect — ``env_var_refs`` may be empty per the schema.
    """
    ctx = _ctx(secret_handling=SecretHandling(env_var_refs=(), secret_count=0))
    written = emit_crypto_attestation_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk["secret_handling"]["env_var_refs"] == []


# --------------------------------------------------------------------------- #
# Public-bar / shape rejections                                               #
# --------------------------------------------------------------------------- #


def test_emit_rejects_lowercase_env_var_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(secret_handling=SecretHandling(env_var_refs=("api_token",))),
            tmp_path,
        )


def test_emit_rejects_credential_shaped_env_var_ref(tmp_path: Path) -> None:
    """An emitter passing a value-shaped string into env_var_refs must
    be rejected at the boundary; the schema regex pins names only.
    """
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(
                secret_handling=SecretHandling(
                    env_var_refs=("sk-abc123xyz",)
                )
            ),
            tmp_path,
        )


def test_emit_rejects_duplicate_env_var_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(
                secret_handling=SecretHandling(
                    env_var_refs=("A_TOKEN", "A_TOKEN")
                )
            ),
            tmp_path,
        )


def test_emit_rejects_secrets_baked_in_true(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(
                secret_handling=SecretHandling(
                    env_var_refs=("FOO",),
                    secrets_baked_in=True,
                )
            ),
            tmp_path,
        )


def test_emit_rejects_non_env_injection_mode(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(
                secret_handling=SecretHandling(
                    env_var_refs=("FOO",),
                    injection_mode="file",
                )
            ),
            tmp_path,
        )


def test_emit_rejects_unknown_compile_target(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(compile_target="make"), tmp_path
        )


def test_emit_rejects_bad_workflow_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(_ctx(workflow_id="Bad ID"), tmp_path)


def test_emit_rejects_bad_control_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(control_refs=("not-a-control-ref",)), tmp_path
        )


def test_emit_rejects_bad_regulation_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(regulation_refs=("invented:ref",)), tmp_path
        )


def test_emit_rejects_naive_captured_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(captured_at=datetime(2026, 6, 9, 5, 0, 0)),
            tmp_path,
        )


def test_emit_rejects_partial_owner_block(tmp_path: Path) -> None:
    """Schema marks owner ``required: [role, assigned_at]`` — caller
    must supply both halves or neither.
    """
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(owner_role="platform-security-wg", owner_assigned_at=None),
            tmp_path,
        )


def test_emit_rejects_bad_owner_assigned_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(owner_assigned_at="2026/01/15"),
            tmp_path,
        )


def test_emit_rejects_bad_commit_sha(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(commit_sha="not-hex"), tmp_path
        )


def test_emit_rejects_bad_retention(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact(
            _ctx(retention="2years"), tmp_path
        )


# --------------------------------------------------------------------------- #
# Temporal activity wrapper                                                   #
# --------------------------------------------------------------------------- #


def test_temporal_activity_wraps_shared_helper(tmp_path: Path) -> None:
    """Happy-path Temporal pin required by the F-CP-05 EMITTER SKELETON card.

    The activity-level test asserts one well-formed crypto-attestation
    evidence record is emitted per workflow execution by exercising the
    Temporal-side wrapper end-to-end.
    """
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import (
        emit_crypto_attestation_artifact_activity,
    )

    ctx = _ctx()
    written_str = asyncio.run(
        emit_crypto_attestation_artifact_activity(ctx, str(tmp_path))
    )
    written = Path(written_str)
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_crypto_attestation_artifact(ctx)
    # One artifact per workflow execution — directory has exactly one
    # record file (ignoring the atomic-write tempfile, which os.replace
    # removes on success).
    written_files = [p for p in Path(tmp_path).iterdir() if p.suffix == ".json"]
    assert len(written_files) == 1
    assert written_files[0].name == f"{on_disk['artifact_id']}.json"
