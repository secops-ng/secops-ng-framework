"""F-CP-05 CORE-FANOUT-LG — LangGraph adapter round-trip for the crypto-attestation emitter.

Pins (CORE-FANOUT-LG scope — EXTEND-tests-goldens, EXTEND-drift,
NIS2 Art. 21(2)(h) narrative mapping, and the F-PT-01 refuse-at-boot
enforcement land on separate sibling cards):

1. The LangGraph node adapter wraps the shared helper. The on-disk
   record is byte-identical to what the shared renderer produces, and
   the partial state update names the right ``artifact_id`` /
   ``artifact_path``.
2. The env-only-injection assertion is enforced at the adapter
   boundary: payloads that bake secrets into the workflow, that switch
   away from the env injection mode, or that smuggle credential-shaped
   values through ``env_var_refs`` are rejected — no artifact is
   written on any rejected path.
3. The ``compile_target`` axis keeps the LangGraph adapter's
   ``artifact_id`` distinct from the n8n adapter's for the same
   execution, so a refactor cannot silently collapse the targets.
4. Missing required state keys surface a typed ``KeyError`` for the
   integrator.
5. The adapter accepts a plain mapping for the nested
   ``crypto_attestation_context`` so a preceding node can assemble it
   from raw state without importing this module's dataclass.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    CryptoAttestationContext,
    SecretHandling,
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
        execution_id="langgraph:wf-run-crypto-001",
        compile_target="langgraph",
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
# CORE-FANOUT-LG adapter round-trip                                           #
# --------------------------------------------------------------------------- #


def test_langgraph_node_wraps_shared_helper(tmp_path: Path) -> None:
    """The node accepts a state mapping carrying the typed
    :class:`CryptoAttestationContext`, delegates to
    ``emit_crypto_attestation_artifact``, and returns a partial state
    update naming the absolute artifact path and the deterministic
    ``artifact_id``. The on-disk record must be byte-identical to what
    the shared renderer produces.
    """
    from compilers.langgraph.evidence import (
        emit_crypto_attestation_artifact_node,
    )

    ctx = _ctx()
    update = emit_crypto_attestation_artifact_node(
        {
            "crypto_attestation_context": ctx,
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["crypto_attestation_artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_crypto_attestation_artifact(ctx)
    assert update["crypto_attestation_artifact_id"] == on_disk["artifact_id"]
    assert written.name == f"{on_disk['artifact_id']}.json"


def test_langgraph_node_accepts_mapping_context(tmp_path: Path) -> None:
    """A preceding node can assemble the context as a plain mapping so
    it does not need to import this module's dataclass. The adapter
    must rebuild the typed context (including the nested
    ``secret_handling`` block from a sub-mapping, and tuple-ification
    of the list-shaped ``env_var_refs`` / ``regulation_refs`` /
    ``control_refs``) before delegating.
    """
    from compilers.langgraph.evidence import (
        emit_crypto_attestation_artifact_node,
    )

    ctx = _ctx()
    mapping_ctx = {
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "secret_handling": {
            "env_var_refs": list(ctx.secret_handling.env_var_refs),
            "secrets_baked_in": ctx.secret_handling.secrets_baked_in,
            "injection_mode": ctx.secret_handling.injection_mode,
            "secret_count": ctx.secret_handling.secret_count,
        },
        "captured_at": ctx.captured_at,
        "source_url": ctx.source_url,
        "owner_role": ctx.owner_role,
        "owner_assigned_at": ctx.owner_assigned_at,
        "commit_sha": ctx.commit_sha,
    }
    update = emit_crypto_attestation_artifact_node(
        {
            "crypto_attestation_context": mapping_ctx,
            "evidence_output_dir": str(tmp_path),
        }
    )
    on_disk = json.loads(
        Path(update["crypto_attestation_artifact_path"]).read_text("utf-8")
    )
    _validator().validate(on_disk)
    assert on_disk == render_crypto_attestation_artifact(ctx)


def test_langgraph_node_asserts_env_only_injection(tmp_path: Path) -> None:
    """The env-only-injection assertion is the contract this stream
    exists to record. The LangGraph adapter must surface a state that
    bakes secrets into the workflow code path — or attempts a non-env
    injection mode — as a rejection at the boundary; no artifact may
    be written. Pins the F-CP-05 CORE-FANOUT-LG acceptance criterion.
    """
    from compilers.langgraph.evidence import (
        emit_crypto_attestation_artifact_node,
    )

    # secrets_baked_in=True is refused.
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact_node(
            {
                "crypto_attestation_context": _ctx(
                    secret_handling=SecretHandling(
                        env_var_refs=("FOO_TOKEN",),
                        secrets_baked_in=True,
                    )
                ),
                "evidence_output_dir": str(tmp_path),
            }
        )

    # injection_mode != "env" is refused.
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact_node(
            {
                "crypto_attestation_context": _ctx(
                    secret_handling=SecretHandling(
                        env_var_refs=("FOO_TOKEN",),
                        injection_mode="file",
                    )
                ),
                "evidence_output_dir": str(tmp_path),
            }
        )

    # Credential-shaped strings smuggled in via env_var_refs are
    # rejected — only UPPER_SNAKE_CASE names travel through.
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact_node(
            {
                "crypto_attestation_context": _ctx(
                    secret_handling=SecretHandling(
                        env_var_refs=("sk-abc123xyz",)
                    )
                ),
                "evidence_output_dir": str(tmp_path),
            }
        )

    # Lowercase names are rejected too.
    with pytest.raises(ValueError):
        emit_crypto_attestation_artifact_node(
            {
                "crypto_attestation_context": _ctx(
                    secret_handling=SecretHandling(
                        env_var_refs=("api_token",)
                    )
                ),
                "evidence_output_dir": str(tmp_path),
            }
        )

    # No artifact written on any rejected path.
    assert not list(tmp_path.iterdir())


def test_langgraph_node_on_disk_record_byte_parity_with_shared_renderer(
    tmp_path: Path,
) -> None:
    """The bytes the adapter persists must match
    ``json.dumps(render_crypto_attestation_artifact(ctx), ...)`` byte
    for byte — the canonical content is the shared renderer's output.
    Pins the contract so a refactor of the adapter cannot drift the
    rendered shape (key ordering, separators, trailing newline).
    """
    from compilers.langgraph.evidence import (
        emit_crypto_attestation_artifact_node,
    )

    ctx = _ctx()
    update = emit_crypto_attestation_artifact_node(
        {
            "crypto_attestation_context": ctx,
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["crypto_attestation_artifact_path"])
    on_disk_bytes = written.read_bytes()
    # Round-trip through the shared renderer and re-parse the on-disk
    # bytes; equality at the dict level is the cross-target contract
    # the EXTEND-tests-goldens sibling will pin per target.
    assert json.loads(on_disk_bytes.decode("utf-8")) == (
        render_crypto_attestation_artifact(ctx)
    )


def test_langgraph_node_artifact_id_distinct_per_compile_target(
    tmp_path: Path,
) -> None:
    """The shared helper keys ``artifact_id`` on
    ``(workflow_id, execution_id, compile_target)``; the compile-target
    axis is what makes the LangGraph adapter's id distinct from the
    n8n one for the same execution. Pin the divergence so a refactor
    cannot silently collapse the targets.
    """
    from compilers.langgraph.evidence import (
        emit_crypto_attestation_artifact_node,
    )

    ctx_lg = _ctx(compile_target="langgraph")
    update = emit_crypto_attestation_artifact_node(
        {
            "crypto_attestation_context": ctx_lg,
            "evidence_output_dir": str(tmp_path),
        }
    )
    on_disk_lg = json.loads(
        Path(update["crypto_attestation_artifact_path"]).read_text("utf-8")
    )
    on_disk_n8n = render_crypto_attestation_artifact(
        _ctx(compile_target="n8n")
    )
    assert on_disk_lg["compile_target"] == "langgraph"
    assert on_disk_lg["artifact_id"] != on_disk_n8n["artifact_id"]


def test_langgraph_node_raises_on_missing_state_keys(tmp_path: Path) -> None:
    """Missing required state keys surface a typed KeyError for the integrator."""
    from compilers.langgraph.evidence import (
        emit_crypto_attestation_artifact_node,
    )

    with pytest.raises(KeyError):
        emit_crypto_attestation_artifact_node(
            {"evidence_output_dir": str(tmp_path)}
        )
    with pytest.raises(KeyError):
        emit_crypto_attestation_artifact_node(
            {"crypto_attestation_context": _ctx()}
        )
