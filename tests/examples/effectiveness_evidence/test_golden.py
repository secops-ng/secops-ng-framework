"""F-CP-06 EXTEND-tests-goldens — per-target byte-parity goldens.

These tests pin the on-disk bytes of the effectiveness evidence
artifact emitted by each compile target (n8n, Temporal, LangGraph)
against a checked-in fixture under
``tests/fixtures/effectiveness_evidence/<target>.json``.

The CORE-FANOUT round-trips in
``tests/content_model/test_effectiveness_evidence_emitter.py`` and the
sibling ``..._langgraph.py`` already pin cross-target equivalence —
each adapter produces the same record bytes for the same context. These
tests are the EXTEND complement: each target's adapter is exercised
against an immutable golden so a refactor of the shared emitter that
silently changes serialisation gets caught at the byte level — one
fixture per target so the failure message names which target drifted,
mirroring the F-CP-01/03/04/05/07 EXTEND-tests-goldens cards that
preceded it.

Coverage axes (per the F-CP-06 EXTEND-tests-goldens contract):

1. **Schema-conformant emit.** Each target's on-disk artifact validates
   against ``schemas/evidence/effectiveness.schema.json``.
2. **Indicator-anchor + subject-version pass-through.** ``metric_ref``,
   ``subject_version.kind``, ``subject_version.value``,
   ``measurement.unit``, ``measurement.direction`` and the
   ``measurement.source_shape`` discriminator are passed through
   unchanged by each adapter — no coercion, no rewriting, no synonym
   expansion.
3. **NIS2 Article 21(2)(f) anchor.** Every golden carries
   ``nis2:art-21-2-f`` on ``regulation_refs`` — the G-02 regulatory
   mapping beat for this stream. Adapters must not drop it.
4. **artifact_id determinism.** ``artifact_id`` on the on-disk record
   matches ``SHA-256(<workflow_id>|<execution_id>|<compile_target>|
   <metric_ref>|<subject_version.value>)`` per the schema contract;
   ``captured_at`` is deliberately *not* part of the key, so
   re-emissions inside the same evaluation stay byte-identical at the
   path level. Cross-target equivalence is already pinned by the
   CORE-FANOUT round-trip — these goldens pin the immutable on-disk
   bytes per target so a silent serialisation drift names the target
   that moved.

If the shared emitter changes the on-disk serialisation intentionally,
regenerate the goldens by re-running the cross-target round-trip in
``test_effectiveness_evidence_emitter.py``, copying any one of the
three (they MUST be byte-identical) into each fixture, and committing
the updated bytes alongside the emitter change.
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
    EffectivenessContext,
    Measurement,
    OcsfPointer,
    SourceShape,
    SubjectVersion,
    derive_effectiveness_artifact_id,
    render_effectiveness_artifact,
)

REPO = Path(__file__).resolve().parents[3]
SCHEMAS = REPO / "schemas"
EFFECTIVENESS_SCHEMA = SCHEMAS / "evidence" / "effectiveness.schema.json"

FIXTURES = REPO / "tests" / "fixtures" / "effectiveness_evidence"
N8N_GOLDEN = FIXTURES / "n8n.json"
TEMPORAL_GOLDEN = FIXTURES / "temporal.json"
LANGGRAPH_GOLDEN = FIXTURES / "langgraph.json"


# --------------------------------------------------------------------------- #
# Shared fixture context                                                       #
# --------------------------------------------------------------------------- #


def _ctx() -> EffectivenessContext:
    """The canonical context the three goldens pin against.

    Covers the union of the schema's surface that the shared emitter
    materialises onto disk for one effectiveness evaluation: required
    core fields, the nested ``subject_version`` block (``policy_version``
    + semver-shaped value), a full ``measurement`` with the ``ratio``
    unit / ``lower_is_better`` direction / a populated ``ocsf``
    ``source_shape`` pointer (so the discriminator branch is exercised
    on disk) / a populated ``evaluation_window`` / ``threshold_crossed``,
    the owner block, ``commit_sha``, and ``retention``. The
    ``compile_target`` is pinned to ``temporal`` so the same context
    fed through every adapter yields the same ``artifact_id`` — the
    goldens are about per-target byte-parity of the on-disk record,
    not about each target stamping its own id. Cross-target id
    divergence on the ``compile_target`` axis is already pinned by the
    CORE-FANOUT round-trip in
    ``tests/content_model/test_effectiveness_evidence_emitter.py``.

    Anchored on the F-WF-01 vulnerability-triage worked example and
    NIS2 Article 21(2)(f) — the regulatory wire the G-02 milestone
    reads for the effectiveness stream.
    """
    return EffectivenessContext(
        workflow_id="vulnerability_triage",
        execution_id="wf-run-effectiveness-vuln-intake-0001",
        compile_target="temporal",
        regulation_refs=("nis2:art-21-2-f",),
        control_refs=(
            "control.control_effectiveness_test@v1",
            "control.risk_management_policy@v1",
        ),
        metric_ref="kri.control_effectiveness@v1",
        subject_version=SubjectVersion(kind="policy_version", value="1.2.0"),
        measurement=Measurement(
            value=0.08,
            unit="ratio",
            direction="lower_is_better",
            source_shape=SourceShape(
                kind="ocsf",
                ocsf=OcsfPointer(
                    class_uid=2004,
                    class_name="Detection Finding",
                    ocsf_version="1.1.0",
                ),
            ),
            evaluation_window="P1D",
            threshold_crossed="warn",
        ),
        captured_at=datetime(2026, 6, 18, 5, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/effectiveness-vuln-intake-0001",
        owner_role="metrics-wg",
        owner_assigned_at="2026-01-15",
        commit_sha="deadbeef0123456789",
        retention="P2Y",
    )


def _n8n_payload(ctx: EffectivenessContext) -> dict:
    """Re-shape a context as the JSON-native payload an n8n node sends.

    n8n cannot transport Python objects across the node-process
    boundary, so datetimes serialise to ISO-8601 ``...Z`` strings and
    nested ``subject_version`` / ``measurement`` / ``source_shape`` /
    ``ocsf`` dataclasses serialise to JSON sub-objects. Optional
    fields are omitted when the source context omits them. Kept in
    lockstep with the ``_payload_from_ctx`` helper in
    ``tests/content_model/test_effectiveness_evidence_emitter.py``.
    """
    sv = ctx.subject_version
    sv_payload = {"kind": sv.kind, "value": sv.value}

    ss = ctx.measurement.source_shape
    ss_payload: dict = {"kind": ss.kind}
    if ss.ocsf is not None:
        ocsf_payload: dict = {"class_uid": ss.ocsf.class_uid}
        if ss.ocsf.class_name is not None:
            ocsf_payload["class_name"] = ss.ocsf.class_name
        if ss.ocsf.ocsf_version is not None:
            ocsf_payload["ocsf_version"] = ss.ocsf.ocsf_version
        ss_payload["ocsf"] = ocsf_payload
    if ss.telemetry_ref is not None:
        ss_payload["telemetry_ref"] = ss.telemetry_ref

    m = ctx.measurement
    m_payload: dict = {
        "value": m.value,
        "unit": m.unit,
        "direction": m.direction,
        "source_shape": ss_payload,
    }
    if m.evaluation_window is not None:
        m_payload["evaluation_window"] = m.evaluation_window
    if m.threshold_crossed is not None:
        m_payload["threshold_crossed"] = m.threshold_crossed

    payload: dict = {
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "compile_target": ctx.compile_target,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "metric_ref": ctx.metric_ref,
        "subject_version": sv_payload,
        "measurement": m_payload,
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": ctx.source_url,
    }
    if ctx.owner_role is not None:
        payload["owner_role"] = ctx.owner_role
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
    return Draft202012Validator(_load_json(EFFECTIVENESS_SCHEMA))


# --------------------------------------------------------------------------- #
# Fixture-on-disk guardrails                                                  #
# --------------------------------------------------------------------------- #


def test_golden_fixtures_are_committed() -> None:
    for path in (N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN):
        assert path.exists(), f"missing golden fixture: {path}"
        assert path.stat().st_size > 0, f"empty golden fixture: {path}"


def test_golden_fixtures_are_byte_identical_across_targets() -> None:
    """The shared emitter's contract is record-shape parity across
    targets when fed the same context (including the same
    ``compile_target``). The three checked-in fixtures must therefore
    be byte-identical; if they diverge, a per-target test below will
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
        f"{target} effectiveness evidence artifact drifted from the "
        f"committed golden. If the change is intentional, regenerate "
        f"the goldens by re-running the cross-target round-trip in "
        f"tests/content_model/test_effectiveness_evidence_emitter.py "
        f"and committing the new bytes alongside the emitter change."
    )


def test_temporal_artifact_matches_golden(tmp_path: Path) -> None:
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import (
        emit_effectiveness_artifact_activity,
    )

    written = Path(
        asyncio.run(
            emit_effectiveness_artifact_activity(_ctx(), str(tmp_path))
        )
    )
    assert written.read_bytes() == TEMPORAL_GOLDEN.read_bytes(), _drift_hint(
        "Temporal"
    )


def test_n8n_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_effectiveness_artifact_n8n

    result = emit_effectiveness_artifact_n8n(_n8n_payload(_ctx()), tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == N8N_GOLDEN.read_bytes(), _drift_hint("n8n")


def test_langgraph_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import (
        emit_effectiveness_artifact_node,
    )

    update = emit_effectiveness_artifact_node(
        {
            "effectiveness_context": _ctx(),
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["effectiveness_artifact_path"])
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
# Coverage axis 2: indicator-anchor + subject-version pass-through            #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_metric_ref_passed_through_unchanged(fixture: Path) -> None:
    """``metric_ref`` on the on-disk artifact must equal the context
    value byte-for-byte — no coercion, no @v stripping, no kpi/kri
    re-spelling. The schema regex pins the shape at the boundary; this
    pin guards against an adapter that silently re-anchors the metric
    on the way to disk.
    """
    record = _load_json(fixture)
    assert record["metric_ref"] == _ctx().metric_ref


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_subject_version_passed_through_unchanged(fixture: Path) -> None:
    """``subject_version.kind`` and ``subject_version.value`` on the
    on-disk artifact must match the context byte-for-byte. The
    deterministic ``artifact_id`` derivation pins on the value
    verbatim, so any silent rewrite (e.g. ``policy_version`` -> ``policy``,
    or semver normalisation) would cascade into a wrong id — pin both
    here so the diagnostic names the field, not just the id.
    """
    record = _load_json(fixture)
    expected = _ctx().subject_version
    assert record["subject_version"]["kind"] == expected.kind
    assert record["subject_version"]["value"] == expected.value


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_measurement_unit_and_direction_passed_through_unchanged(
    fixture: Path,
) -> None:
    """``measurement.unit`` and ``measurement.direction`` on the
    on-disk artifact must equal the context values verbatim. The
    schema's closed enums catch most drift at the boundary; pinning
    the round-trip values guards against an adapter that quietly
    coerces ``ratio`` to ``percent`` (or flips the direction) on the
    way to disk.
    """
    record = _load_json(fixture)
    m = _ctx().measurement
    assert record["measurement"]["unit"] == m.unit
    assert record["measurement"]["direction"] == m.direction


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_source_shape_discriminator_and_payload_passed_through(
    fixture: Path,
) -> None:
    """The ``measurement.source_shape`` discriminator (``ocsf`` /
    ``telemetry`` / ``none``) and the ``ocsf`` block carried by the
    canonical fixture (``class_uid`` / ``class_name`` / ``ocsf_version``)
    must pass through unchanged. The shared emitter already rejects
    cross-branch shapes at the boundary; this pin guards against an
    adapter that re-keys the OCSF pointer on the way to disk.
    """
    record = _load_json(fixture)
    expected = _ctx().measurement.source_shape
    on_disk = record["measurement"]["source_shape"]
    assert on_disk["kind"] == expected.kind
    assert expected.ocsf is not None  # fixture pin
    assert on_disk["ocsf"]["class_uid"] == expected.ocsf.class_uid
    assert on_disk["ocsf"]["class_name"] == expected.ocsf.class_name
    assert on_disk["ocsf"]["ocsf_version"] == expected.ocsf.ocsf_version


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_measurement_value_window_and_threshold_passed_through(
    fixture: Path,
) -> None:
    """The pre-computed indicator ``value``, the optional
    ``evaluation_window`` (ISO-8601 duration), and the optional
    ``threshold_crossed`` token must pass through unchanged. The
    schema's closed token regex on ``threshold_crossed`` already
    pins shape; this pin guards against an adapter that re-rolls the
    window string or up/lowercases the threshold name on the way to
    disk.
    """
    record = _load_json(fixture)
    m = _ctx().measurement
    assert record["measurement"]["value"] == m.value
    assert record["measurement"]["evaluation_window"] == m.evaluation_window
    assert record["measurement"]["threshold_crossed"] == m.threshold_crossed


# --------------------------------------------------------------------------- #
# Coverage axis 3: NIS2 Article 21(2)(f) regulatory anchor                    #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_regulation_refs_carry_nis2_art_21_2_f(fixture: Path) -> None:
    """G-02 regulatory-mapping anchor for the effectiveness stream.

    NIS2 Article 21(2)(f) is the obligation the effectiveness snapshot
    feeds. The golden must carry it on ``regulation_refs`` per the
    F-CP-06 contract; adapters must not drop it on the way to disk.
    """
    record = _load_json(fixture)
    assert "nis2:art-21-2-f" in record["regulation_refs"]
    assert record["regulation_refs"] == list(_ctx().regulation_refs)


# --------------------------------------------------------------------------- #
# Coverage axis 4: artifact_id determinism                                    #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_artifact_id_matches_derivation(fixture: Path) -> None:
    """``artifact_id`` on the on-disk record must equal ``SHA-256(
    <workflow_id>|<execution_id>|<compile_target>|<metric_ref>|
    <subject_version.value>)`` per the effectiveness schema contract.
    Replays of the same evaluation under the same compile target must
    re-derive the same id; the pin here catches a target that
    silently changes the keying. ``captured_at`` is deliberately *not*
    part of the key so re-emissions inside the same evaluation stay
    byte-identical at the path level.
    """
    ctx = _ctx()
    record = _load_json(fixture)
    expected = derive_effectiveness_artifact_id(
        ctx.workflow_id,
        ctx.execution_id,
        ctx.compile_target,
        ctx.metric_ref,
        ctx.subject_version.value,
    )
    assert record["artifact_id"] == expected
    # Re-derive locally to guard against the helper itself drifting
    # from the schema-documented formula.
    raw = (
        f"{ctx.workflow_id}|{ctx.execution_id}|{ctx.compile_target}|"
        f"{ctx.metric_ref}|{ctx.subject_version.value}"
    ).encode("utf-8")
    assert record["artifact_id"] == sha256(raw).hexdigest()


def test_artifact_id_byte_identical_across_targets() -> None:
    """The artifact_id is contained verbatim in each golden's bytes;
    cross-target parity at the byte level is already pinned in
    ``test_golden_fixtures_are_byte_identical_across_targets``, but
    naming the id in this test gives a precise diagnosis if a target
    drifts on the derivation rather than on the surrounding shape.
    """
    ctx = _ctx()
    needle = (
        f'"artifact_id": "'
        f"{derive_effectiveness_artifact_id(ctx.workflow_id, ctx.execution_id, ctx.compile_target, ctx.metric_ref, ctx.subject_version.value)}"
        f'"'
    ).encode("utf-8")
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
    record = render_effectiveness_artifact(_ctx())
    serialised = (
        json.dumps(record, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert serialised == TEMPORAL_GOLDEN.read_bytes()
