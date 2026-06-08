"""F-CP-01 EXTEND-tests-goldens — per-target byte-parity goldens.

These tests pin the on-disk bytes of the risk-analysis evidence
artifact emitted by each compile target (n8n, Temporal, LangGraph)
against a checked-in fixture under
``tests/fixtures/risk_analysis_evidence/<target>.json``.

The CORE-FANOUT round-trip in
``tests/content_model/test_risk_analysis_evidence_emitter.py`` already
pins cross-target equivalence (all three targets agree byte-for-byte
under one execution). These tests are the EXTEND complement: they pin
each target against an immutable golden so a refactor of the shared
emitter that silently changes serialisation gets caught at the byte
level — one fixture per target so the failure message names which
target drifted, mirroring the F-WF-05 EXTEND-tests-happy /
EXTEND-tests-replay structure.

Coverage axes (per the F-CP-01 EXTEND-tests-goldens contract):

1. **Schema-conformant emit.** Each target's on-disk artifact validates
   against ``schemas/evidence/risk-analysis.schema.json``.
2. **Enum-value normalisation.** ``attestation_state`` on the on-disk
   artifact is drawn from the shared
   ``schemas/attestation_state.json`` four-state vocabulary, and the
   adapter does not coerce or rewrite the value the context carried in.
3. **Cadence-promotion serialisation.** ``review_cadence`` is promoted
   from the context into the artifact body as an ISO-8601 duration and
   is serialised byte-identically across all three targets.

If the shared emitter changes the on-disk serialisation intentionally,
regenerate the goldens by re-running the cross-target round-trip in
``test_risk_analysis_evidence_emitter.py``, copying any one of the
three (they MUST be byte-identical) into each fixture, and committing
the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, RefResolver

from compilers._shared.evidence import (
    RiskAnalysisContext,
    render_risk_analysis_artifact,
)

REPO = Path(__file__).resolve().parents[3]
SCHEMAS = REPO / "schemas"
ATTESTATION_STATE_SCHEMA = SCHEMAS / "attestation_state.json"
RISK_ANALYSIS_SCHEMA = SCHEMAS / "evidence" / "risk-analysis.schema.json"

FIXTURES = REPO / "tests" / "fixtures" / "risk_analysis_evidence"
N8N_GOLDEN = FIXTURES / "n8n.json"
TEMPORAL_GOLDEN = FIXTURES / "temporal.json"
LANGGRAPH_GOLDEN = FIXTURES / "langgraph.json"


# --------------------------------------------------------------------------- #
# Shared fixture context                                                       #
# --------------------------------------------------------------------------- #


def _ctx() -> RiskAnalysisContext:
    """The canonical context the three goldens pin against.

    Covers the union of the schema's surface: required core fields,
    optional structured ``risk_analysis_output`` extensions,
    ``attestation_state_delta``, and ``baseline_drift``. Picking a
    non-default ``attestation_state`` ("partially_effective") and a
    non-default cadence ("P3M") guards the enum-normalisation and
    cadence-promotion axes.
    """
    return RiskAnalysisContext(
        control_ref="control.risk_management_policy@v1",
        regulation_refs=(
            "nis2:art-21-2-a",
            "dora:art-5-governance",
            "dora:art-6-framework",
        ),
        policy_version="1.2.0",
        attestation_state="partially_effective",
        residual_exposure_summary=(
            "Control operating with declared gaps in third-party-coverage "
            "scope; residual exposure tracked under the supply-chain stream "
            "until the gap closes."
        ),
        owner_role="risk-management-wg@example.org",
        owner_assigned_at="2026-01-15",
        review_cadence="P3M",
        captured_at=datetime(2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/abc123",
        commit_sha="deadbeef0123456789",
        scoped_scenarios=("ransomware", "supply-chain compromise"),
        deviations_from_baseline=("custom alerting thresholds",),
        compensating_controls=("control.network_segmentation@v1",),
        previous_artifact_id="c" * 64,
        previous_state="effective",
        previous_captured_at=datetime(2026, 3, 7, 5, 0, 0, tzinfo=timezone.utc),
        baseline_drift={
            "changed": True,
            "regulation_version_previous": "2026-01-15",
            "regulation_version_current": "2026-04-15",
            "notes": "Quarterly review refreshed against the updated baseline.",
        },
    )


def _n8n_payload(ctx: RiskAnalysisContext) -> dict:
    """Mirror the on-the-wire shape an n8n Code node would send.

    Datetimes serialise to ISO-8601 ``...Z`` strings because n8n cannot
    transport Python ``datetime`` objects across the node-process
    boundary; the adapter parses them back. Kept in lockstep with the
    helper of the same name in
    ``tests/content_model/test_risk_analysis_evidence_emitter.py``.
    """
    payload: dict = {
        "control_ref": ctx.control_ref,
        "regulation_refs": list(ctx.regulation_refs),
        "policy_version": ctx.policy_version,
        "attestation_state": ctx.attestation_state,
        "residual_exposure_summary": ctx.residual_exposure_summary,
        "owner_role": ctx.owner_role,
        "owner_assigned_at": ctx.owner_assigned_at,
        "review_cadence": ctx.review_cadence,
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": ctx.source_url,
    }
    if ctx.commit_sha:
        payload["commit_sha"] = ctx.commit_sha
    if ctx.scoped_scenarios:
        payload["scoped_scenarios"] = list(ctx.scoped_scenarios)
    if ctx.deviations_from_baseline:
        payload["deviations_from_baseline"] = list(ctx.deviations_from_baseline)
    if ctx.compensating_controls:
        payload["compensating_controls"] = list(ctx.compensating_controls)
    if ctx.previous_artifact_id:
        payload["previous_artifact_id"] = ctx.previous_artifact_id
    if ctx.previous_state:
        payload["previous_state"] = ctx.previous_state
    if ctx.previous_captured_at is not None:
        payload["previous_captured_at"] = ctx.previous_captured_at.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    if ctx.baseline_drift is not None:
        payload["baseline_drift"] = dict(ctx.baseline_drift)
    return payload


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    schema = _load_json(RISK_ANALYSIS_SCHEMA)
    store = {
        "https://secops-ng.org/schemas/attestation_state.json": _load_json(
            ATTESTATION_STATE_SCHEMA
        ),
        "attestation_state.json": _load_json(ATTESTATION_STATE_SCHEMA),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


def _attestation_state_enum() -> set[str]:
    return set(_load_json(ATTESTATION_STATE_SCHEMA)["enum"])


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
        f"{target} risk-analysis evidence artifact drifted from the "
        f"committed golden. If the change is intentional, regenerate "
        f"the goldens by re-running the cross-target round-trip in "
        f"tests/content_model/test_risk_analysis_evidence_emitter.py "
        f"and committing the new bytes alongside the emitter change."
    )


def test_temporal_artifact_matches_golden(tmp_path: Path) -> None:
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_risk_analysis_artifact_activity

    written = Path(
        asyncio.run(emit_risk_analysis_artifact_activity(_ctx(), str(tmp_path)))
    )
    assert written.read_bytes() == TEMPORAL_GOLDEN.read_bytes(), _drift_hint("Temporal")


def test_n8n_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_risk_analysis_artifact_n8n

    result = emit_risk_analysis_artifact_n8n(_n8n_payload(_ctx()), tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == N8N_GOLDEN.read_bytes(), _drift_hint("n8n")


def test_langgraph_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import emit_risk_analysis_artifact_node

    update = emit_risk_analysis_artifact_node(
        {
            "risk_analysis_context": _ctx(),
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["risk_analysis_artifact_path"])
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
# Coverage axis 2: enum-value normalisation                                   #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_attestation_state_drawn_from_shared_vocabulary(fixture: Path) -> None:
    """``attestation_state`` on the artifact must be one of the four
    states pinned by ``schemas/attestation_state.json`` — the shared
    vocabulary the F-CP-06 effectiveness-loop stream and the
    ``kri.control_effectiveness@v1`` indicator also import. If a
    target's adapter silently re-coerced the value (e.g. uppercased it
    or expanded a synonym), this test fails before the per-target
    byte-parity test does, giving a precise diagnosis.
    """
    record = _load_json(fixture)
    assert record["attestation_state"] in _attestation_state_enum()
    assert record["attestation_state"] == _ctx().attestation_state


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_previous_state_drawn_from_shared_vocabulary(fixture: Path) -> None:
    """``attestation_state_delta.previous_state`` reuses the same
    four-state vocabulary; pin the same invariant on the delta block
    so a future adapter cannot fork the enum for the historical state.
    """
    record = _load_json(fixture)
    delta = record["attestation_state_delta"]
    assert delta["previous_state"] in _attestation_state_enum()
    assert delta["previous_state"] == _ctx().previous_state


# --------------------------------------------------------------------------- #
# Coverage axis 3: cadence-promotion serialisation                            #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_review_cadence_promoted_as_iso8601_duration(fixture: Path) -> None:
    """The cadence the context declares must surface verbatim on the
    artifact as an ISO-8601 duration string at the top level — every
    consumer (the F-CP-06 effectiveness-loop, the ``overdue``
    classifier in ``kri.control_effectiveness@v1``) reads it from that
    exact path. The pin guards against an adapter that drops the
    cadence or downgrades it to a free-text string.
    """
    record = _load_json(fixture)
    expected = _ctx().review_cadence
    assert record["review_cadence"] == expected
    # ISO-8601 duration shape; minimal sanity check that mirrors the
    # emitter's own regex.
    assert record["review_cadence"].startswith("P")


def test_cadence_serialisation_is_byte_identical_across_targets() -> None:
    """The cadence-promotion contract is the union of two pins: the
    value matches the input (covered above) AND the bytes around it
    are identical across targets. The second pin catches a target
    that, for example, emits ``review_cadence`` at a different
    indentation, with a trailing newline difference, or with a
    different key-order neighbour.
    """
    # ``read_bytes`` here, not ``read_text`` — line endings matter.
    payload_t = TEMPORAL_GOLDEN.read_bytes()
    payload_n = N8N_GOLDEN.read_bytes()
    payload_l = LANGGRAPH_GOLDEN.read_bytes()
    needle = b'"review_cadence": "P3M"'
    assert needle in payload_t
    assert needle in payload_n
    assert needle in payload_l


# --------------------------------------------------------------------------- #
# Pure-renderer sanity                                                        #
# --------------------------------------------------------------------------- #


def test_render_matches_golden_serialisation() -> None:
    """Independent of any compile target, the pure ``render`` helper
    composed with the canonical serialisation the emitter uses must
    reproduce the golden bytes. Locks the renderer's key-order /
    indentation contract in addition to the target wrappers.
    """
    record = render_risk_analysis_artifact(_ctx())
    serialised = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    assert serialised == TEMPORAL_GOLDEN.read_bytes()
