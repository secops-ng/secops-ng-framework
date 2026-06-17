"""F-CP-07 EXTEND-tests-goldens — per-target byte-parity goldens.

These tests pin the on-disk bytes of the access evidence artifact
emitted by each compile target (n8n, Temporal, LangGraph) against a
checked-in fixture under
``tests/fixtures/access_evidence/<target>.json``.

The CORE-FANOUT round-trip in
``tests/content_model/test_access_evidence_emitter.py`` already pins
cross-target equivalence (all three targets agree byte-for-byte under
one execution). These tests are the EXTEND complement: each target's
adapter is exercised against an immutable golden so a refactor of the
shared emitter that silently changes serialisation gets caught at the
byte level — one fixture per target so the failure message names which
target drifted, mirroring the F-CP-04 vulnerabilities and F-CP-01
risk-analysis goldens.

Coverage axes (per the F-CP-07 EXTEND-tests-goldens contract,
adapted to the access schema):

1. **Schema-conformant emit.** Each target's on-disk artifact
   validates against ``schemas/evidence/access.schema.json``.
2. **Caller-identity + capability-list normalisation.** The
   ``caller_identity`` block (principal_type / principal_id /
   identity_provider) and the closed ``verb.resource`` capability
   list are passed through unchanged by each adapter — no coercion,
   no rewriting, no re-ordering.
3. **artifact_id determinism.** ``artifact_id`` on the on-disk record
   matches ``SHA-256(<workflow_id>|<execution_id>|<compile_target>)``
   per the schema contract; cross-target equivalence is already
   pinned by ``tests/content_model/test_access_evidence_emitter.py``
   — these goldens pin the immutable on-disk bytes per target so a
   silent serialisation drift names the target that moved.

If the shared emitter changes the on-disk serialisation intentionally,
regenerate the goldens by re-running the cross-target round-trip in
``test_access_evidence_emitter.py``, copying any one of the three
(they MUST be byte-identical) into each fixture, and committing the
updated bytes alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    AccessContext,
    CallerIdentity,
    derive_access_artifact_id,
    render_access_artifact,
)

REPO = Path(__file__).resolve().parents[3]
SCHEMAS = REPO / "schemas"
ACCESS_SCHEMA = SCHEMAS / "evidence" / "access.schema.json"

FIXTURES = REPO / "tests" / "fixtures" / "access_evidence"
N8N_GOLDEN = FIXTURES / "n8n.json"
TEMPORAL_GOLDEN = FIXTURES / "temporal.json"
LANGGRAPH_GOLDEN = FIXTURES / "langgraph.json"


# --------------------------------------------------------------------------- #
# Shared fixture context                                                       #
# --------------------------------------------------------------------------- #


def _ctx() -> AccessContext:
    """The canonical context the three goldens pin against.

    Covers the union of the schema's surface that the shared emitter
    materialises onto disk: required core fields, the nested
    ``caller_identity`` block (with the optional ``identity_provider``
    populated so the pass-through pin exercises it), a multi-element
    ``capabilities`` list (so list ordering is observable), the optional
    ``capability_count``, the owner block, ``commit_sha``, and
    ``retention``. The ``compile_target`` is pinned to ``temporal`` so
    the same context fed through every adapter yields the same
    ``artifact_id`` — the goldens are about per-target byte-parity of
    the on-disk record, not about each target stamping its own id, and
    cross-target id equivalence under a single execution is the
    contract the emitter ships.
    """
    return AccessContext(
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
        retention="P2Y",
    )


def _n8n_payload(ctx: AccessContext) -> dict:
    """Mirror the on-the-wire shape an n8n Code node would send.

    n8n cannot transport Python objects across the node-process
    boundary, so datetimes serialise to ISO-8601 ``...Z`` strings and
    the nested ``caller_identity`` dataclass serialises to a JSON
    object. Optional fields are omitted when the source context omits
    them. Kept in lockstep with the ``_payload_from_ctx`` helper in
    ``tests/content_model/test_access_evidence_emitter.py``.
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


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(ACCESS_SCHEMA))


# --------------------------------------------------------------------------- #
# Fixture-on-disk guardrails                                                  #
# --------------------------------------------------------------------------- #


def test_golden_fixtures_are_committed() -> None:
    for path in (N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN):
        assert path.exists(), f"missing golden fixture: {path}"
        assert path.stat().st_size > 0, f"empty golden fixture: {path}"


def test_golden_fixtures_are_byte_identical_across_targets() -> None:
    """The shared emitter's contract is record-shape parity across
    targets. The three checked-in fixtures must therefore be
    byte-identical; if they diverge, a per-target test below will
    succeed for one target and fail for the others, and the failure
    will be hard to diagnose. Pin the parity at fixture-load time too.
    """
    assert (
        N8N_GOLDEN.read_bytes()
        == TEMPORAL_GOLDEN.read_bytes()
        == LANGGRAPH_GOLDEN.read_bytes()
    )


# --------------------------------------------------------------------------- #
# Per-target byte-parity goldens                                              #
# --------------------------------------------------------------------------- #


def _drift_hint(target: str) -> str:
    return (
        f"{target} access evidence artifact drifted from the committed "
        f"golden. If the change is intentional, regenerate the goldens "
        f"by re-running the cross-target round-trip in "
        f"tests/content_model/test_access_evidence_emitter.py and "
        f"committing the new bytes alongside the emitter change."
    )


def test_temporal_artifact_matches_golden(tmp_path: Path) -> None:
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_access_artifact_activity

    written = Path(
        asyncio.run(emit_access_artifact_activity(_ctx(), str(tmp_path)))
    )
    assert written.read_bytes() == TEMPORAL_GOLDEN.read_bytes(), _drift_hint(
        "Temporal"
    )


def test_n8n_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_access_artifact_n8n

    result = emit_access_artifact_n8n(_n8n_payload(_ctx()), tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == N8N_GOLDEN.read_bytes(), _drift_hint("n8n")


def test_langgraph_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import emit_access_artifact_node

    update = emit_access_artifact_node(
        {
            "access_context": _ctx(),
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["access_artifact_path"])
    assert written.read_bytes() == LANGGRAPH_GOLDEN.read_bytes(), _drift_hint(
        "LangGraph"
    )


# --------------------------------------------------------------------------- #
# Coverage axis 1: schema-conformant emit                                     #
# --------------------------------------------------------------------------- #


def test_temporal_golden_validates_against_schema() -> None:
    _validator().validate(_load_json(TEMPORAL_GOLDEN))


def test_n8n_golden_validates_against_schema() -> None:
    _validator().validate(_load_json(N8N_GOLDEN))


def test_langgraph_golden_validates_against_schema() -> None:
    _validator().validate(_load_json(LANGGRAPH_GOLDEN))


# --------------------------------------------------------------------------- #
# Coverage axis 2: caller-identity + capability-list normalisation            #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_caller_identity_passed_through_unchanged(fixture: Path) -> None:
    """``principal_type``, ``principal_id`` and ``identity_provider``
    on the on-disk artifact must match the context byte-for-byte —
    no uppercase coercion, no synonym expansion, no provider
    re-spelling. The closed schema regex on ``principal_id`` already
    rejects most drift at the boundary, but pinning the round-trip
    value alongside the per-target bytes gives a precise diagnosis if
    a target's adapter starts rewriting the identity block.
    """
    record = _load_json(fixture)
    expected = _ctx().caller_identity
    on_disk = record["caller_identity"]
    assert on_disk["principal_type"] == expected.principal_type
    assert on_disk["principal_id"] == expected.principal_id
    assert on_disk["identity_provider"] == expected.identity_provider


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_capabilities_passed_through_unchanged(fixture: Path) -> None:
    """The capability list on the artifact must equal the context's
    capability tuple — same tokens, same order, no coercion to set or
    sorted list. Capability-token shape (``verb.resource``) is pinned
    at the emitter boundary; this pin guards against adapter-level
    re-ordering or de-duplication that the schema would not catch.
    """
    record = _load_json(fixture)
    expected = list(_ctx().capabilities)
    assert record["capabilities"] == expected
    # ``capability_count`` on the context surfaces as a top-level field
    # on the record (separate from the ``capabilities`` list length —
    # the platform may assert a higher count than the redacted list).
    assert record["capability_count"] == _ctx().capability_count


# --------------------------------------------------------------------------- #
# Coverage axis 3: artifact_id determinism                                    #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_artifact_id_matches_derivation(fixture: Path) -> None:
    """``artifact_id`` on the on-disk record must equal
    ``SHA-256(<workflow_id>|<execution_id>|<compile_target>)`` per
    the access schema contract. Replays of the same execution under
    the same compile target must re-derive the same id; the pin here
    catches a target that silently changes the keying.
    """
    ctx = _ctx()
    record = _load_json(fixture)
    expected = derive_access_artifact_id(
        ctx.workflow_id, ctx.execution_id, ctx.compile_target
    )
    assert record["artifact_id"] == expected
    # Re-derive locally to guard against the helper itself drifting from
    # the schema-documented formula.
    raw = f"{ctx.workflow_id}|{ctx.execution_id}|{ctx.compile_target}".encode(
        "utf-8"
    )
    assert record["artifact_id"] == sha256(raw).hexdigest()


def test_artifact_id_byte_identical_across_targets() -> None:
    """The artifact_id is contained verbatim in each golden's bytes;
    cross-target parity at the byte level is already pinned in
    ``test_golden_fixtures_are_byte_identical_across_targets``, but
    naming the id in this test gives a precise diagnosis if a target
    drifts on the derivation rather than on the surrounding shape.
    """
    ctx = _ctx()
    needle = f'"artifact_id": "{derive_access_artifact_id(ctx.workflow_id, ctx.execution_id, ctx.compile_target)}"'.encode(
        "utf-8"
    )
    assert needle in N8N_GOLDEN.read_bytes()
    assert needle in TEMPORAL_GOLDEN.read_bytes()
    assert needle in LANGGRAPH_GOLDEN.read_bytes()


# --------------------------------------------------------------------------- #
# Pure-renderer sanity                                                        #
# --------------------------------------------------------------------------- #


def test_render_matches_golden_serialisation() -> None:
    """Independent of any compile target, the pure ``render`` helper
    composed with the canonical serialisation the emitter uses must
    reproduce the golden bytes. Locks the renderer's key-order /
    indentation contract in addition to the target wrappers.
    """
    record = render_access_artifact(_ctx())
    serialised = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    assert serialised == TEMPORAL_GOLDEN.read_bytes()
