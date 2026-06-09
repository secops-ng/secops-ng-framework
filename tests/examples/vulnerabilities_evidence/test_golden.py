"""F-CP-04 EXTEND-tests-goldens — per-target byte-parity goldens.

These tests pin the on-disk bytes of the vulnerabilities evidence
artifact emitted by each compile target (n8n, Temporal, LangGraph)
against a checked-in fixture under
``tests/fixtures/vulnerabilities_evidence/<target>.json``.

The CORE-FANOUT round-trip in
``tests/content_model/test_vulns_evidence_emitter.py`` already pins
cross-target equivalence (all three targets agree byte-for-byte under
one execution). These tests are the EXTEND complement: each target's
adapter is exercised against an immutable golden so a refactor of the
shared emitter that silently changes serialisation gets caught at the
byte level — one fixture per target so the failure message names
which target drifted, mirroring the F-CP-01 risk-analysis goldens.

Coverage axes (per the F-CP-04 EXTEND-tests-goldens contract):

1. **Schema-conformant emit.** Each target's on-disk artifact validates
   against ``schemas/evidence/vulns.schema.json`` (with the promoted
   ``vuln_response_band``, ``cra_clock_kind``, and
   ``cra_timing_milestone`` schemas resolved).
2. **Enum-value normalisation.** ``triage_decision.cra_clock``,
   ``triage_decision.dedup_outcome``, ``response.band``, and
   ``disclosure_timeline[*].milestone`` are drawn from the promoted
   vocabularies; the adapters do not coerce or rewrite the values the
   context carried in.
3. **artifact_id determinism.** ``artifact_id`` on the on-disk record
   matches ``SHA-256(<case_ref>|<execution_id>)`` per the schema
   contract and is byte-identical across targets.

If the shared emitter changes the on-disk serialisation intentionally,
regenerate the goldens by re-running the cross-target round-trip in
``test_vulns_evidence_emitter.py``, copying any one of the three (they
MUST be byte-identical) into each fixture, and committing the updated
bytes alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, RefResolver

from compilers._shared.evidence import (
    DisclosureMilestone,
    ReporterAcknowledgement,
    ResponseBranch,
    TriageDecision,
    VulnsContext,
    derive_vulns_artifact_id,
    render_vulns_artifact,
)

REPO = Path(__file__).resolve().parents[3]
SCHEMAS = REPO / "schemas"
VULN_RESPONSE_BAND_SCHEMA = SCHEMAS / "vuln_response_band.json"
CRA_CLOCK_KIND_SCHEMA = SCHEMAS / "cra_clock_kind.json"
CRA_TIMING_MILESTONE_SCHEMA = SCHEMAS / "cra_timing_milestone.json"
VULNS_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "vulns.schema.json"

FIXTURES = REPO / "tests" / "fixtures" / "vulnerabilities_evidence"
N8N_GOLDEN = FIXTURES / "n8n.json"
TEMPORAL_GOLDEN = FIXTURES / "temporal.json"
LANGGRAPH_GOLDEN = FIXTURES / "langgraph.json"


# --------------------------------------------------------------------------- #
# Shared fixture context                                                       #
# --------------------------------------------------------------------------- #


def _case_ref() -> str:
    return sha256(b"CVE-2026-0001|pkg:generic/example@1.0.0").hexdigest()


def _ctx() -> VulnsContext:
    """The canonical context the three goldens pin against.

    Covers the union of the schema's surface: a Critical triage with
    full CVSS / EPSS / exploitation flags, the ``critical`` response
    band, an ``article_14_1`` CRA clock, all four CRA-timing
    milestones on ``disclosure_timeline`` (the schema admits the union
    even though ``article_14_3`` typically lands on a separate case in
    practice), and a CVD-intake reporter acknowledgement. Picking
    non-default enum members on every promoted-vocabulary axis guards
    the enum-normalisation pin below.
    """
    started = datetime(2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc)
    submitted = datetime(2026, 6, 8, 5, 0, 0, tzinfo=timezone.utc)
    return VulnsContext(
        case_ref=_case_ref(),
        execution_id="temporal:wf-run-abc123",
        regulation_refs=("nis2:art-21-2-e", "cra:art-14-1"),
        control_refs=("control.vuln_disclosure_intake@v1",),
        triage_decision=TriageDecision(
            severity="Critical",
            cvss_severity="Critical",
            cra_clock="article_14_1",
            dedup_outcome="new",
            cvss_base_score=9.8,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            epss_probability=0.42,
            actively_exploited=True,
            risk_summary=(
                "Pre-authentication RCE on the network edge; "
                "exploitation observed in the wild. Mitigation "
                "requires the upcoming patch."
            ),
        ),
        response=ResponseBranch(
            band="critical",
            case_opened_at=datetime(2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc),
            advisory_ref="GHSA-xxxx-xxxx-xxxx",
        ),
        owner_role="psirt@example.org",
        owner_assigned_at="2026-01-15",
        captured_at=datetime(2026, 6, 7, 6, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/abc123",
        disclosure_timeline=(
            DisclosureMilestone(
                milestone="early_warning_24h",
                clock_started_at=started,
                submitted_at=submitted,
                submission_ref="csirt-early_warning_24h",
                on_time=True,
            ),
            DisclosureMilestone(
                milestone="severe_incident_24h",
                clock_started_at=started,
                submitted_at=submitted,
                submission_ref="csirt-severe_incident_24h",
                on_time=True,
            ),
            DisclosureMilestone(
                milestone="incident_notification_72h",
                clock_started_at=started,
                submitted_at=submitted,
                submission_ref="csirt-incident_notification_72h",
                on_time=True,
            ),
            DisclosureMilestone(
                milestone="final_report_14d",
                clock_started_at=started,
                submitted_at=submitted,
                submission_ref="csirt-final_report_14d",
                on_time=True,
            ),
        ),
        reporter_acknowledgement=ReporterAcknowledgement(
            disclosure_received_at=datetime(
                2026, 6, 7, 4, 0, 0, tzinfo=timezone.utc
            ),
            acknowledged_at=datetime(2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc),
            sla_duration="P1D",
        ),
        commit_sha="deadbeef0123456789",
    )


def _n8n_payload(ctx: VulnsContext) -> dict:
    """Mirror the on-the-wire shape an n8n Code node would send.

    n8n cannot transport Python objects across the node-process
    boundary, so datetimes serialise to ISO-8601 ``...Z`` strings and
    nested dataclasses serialise to JSON objects / arrays. Kept in
    lockstep with the ``_payload_from_ctx`` helper in
    ``tests/content_model/test_vulns_evidence_emitter.py``.
    """
    td = ctx.triage_decision
    triage: dict = {
        "severity": td.severity,
        "cvss_severity": td.cvss_severity,
        "cra_clock": td.cra_clock,
        "dedup_outcome": td.dedup_outcome,
    }
    if td.cvss_base_score is not None:
        triage["cvss_base_score"] = td.cvss_base_score
    if td.cvss_vector is not None:
        triage["cvss_vector"] = td.cvss_vector
    if td.epss_probability is not None:
        triage["epss_probability"] = td.epss_probability
    if td.actively_exploited is not None:
        triage["actively_exploited"] = td.actively_exploited
    if td.dedup_collided_with is not None:
        triage["dedup_collided_with"] = td.dedup_collided_with
    if td.risk_summary is not None:
        triage["risk_summary"] = td.risk_summary

    rb = ctx.response
    response: dict = {"band": rb.band}
    if rb.case_opened_at is not None:
        response["case_opened_at"] = rb.case_opened_at.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    if rb.patch_disseminated_at is not None:
        response["patch_disseminated_at"] = rb.patch_disseminated_at.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    if rb.advisory_ref is not None:
        response["advisory_ref"] = rb.advisory_ref
    if rb.accept_rationale is not None:
        response["accept_rationale"] = rb.accept_rationale
    if rb.compensating_controls:
        response["compensating_controls"] = list(rb.compensating_controls)

    payload: dict = {
        "case_ref": ctx.case_ref,
        "execution_id": ctx.execution_id,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "triage_decision": triage,
        "response": response,
        "owner_role": ctx.owner_role,
        "owner_assigned_at": ctx.owner_assigned_at,
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": ctx.source_url,
    }
    if ctx.commit_sha:
        payload["commit_sha"] = ctx.commit_sha
    if ctx.retention:
        payload["retention"] = ctx.retention
    if ctx.disclosure_timeline:
        payload["disclosure_timeline"] = []
        for m in ctx.disclosure_timeline:
            entry: dict = {
                "milestone": m.milestone,
                "clock_started_at": m.clock_started_at.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "submitted_at": m.submitted_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            if m.submission_ref is not None:
                entry["submission_ref"] = m.submission_ref
            if m.on_time is not None:
                entry["on_time"] = m.on_time
            payload["disclosure_timeline"].append(entry)
    if ctx.reporter_acknowledgement is not None:
        ack = ctx.reporter_acknowledgement
        ack_payload: dict = {
            "disclosure_received_at": ack.disclosure_received_at.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "acknowledged_at": ack.acknowledged_at.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }
        if ack.sla_duration is not None:
            ack_payload["sla_duration"] = ack.sla_duration
        payload["reporter_acknowledgement"] = ack_payload
    return payload


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    schema = _load_json(VULNS_EVIDENCE_SCHEMA)
    store = {
        "https://secops-ng.org/schemas/vuln_response_band.json": _load_json(
            VULN_RESPONSE_BAND_SCHEMA
        ),
        "https://secops-ng.org/schemas/cra_clock_kind.json": _load_json(
            CRA_CLOCK_KIND_SCHEMA
        ),
        "https://secops-ng.org/schemas/cra_timing_milestone.json": _load_json(
            CRA_TIMING_MILESTONE_SCHEMA
        ),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


def _enum(path: Path) -> set[str]:
    return set(_load_json(path)["enum"])


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
        f"{target} vulnerabilities evidence artifact drifted from the "
        f"committed golden. If the change is intentional, regenerate "
        f"the goldens by re-running the cross-target round-trip in "
        f"tests/content_model/test_vulns_evidence_emitter.py and "
        f"committing the new bytes alongside the emitter change."
    )


def test_temporal_artifact_matches_golden(tmp_path: Path) -> None:
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_vulns_artifact_activity

    written = Path(
        asyncio.run(emit_vulns_artifact_activity(_ctx(), str(tmp_path)))
    )
    assert written.read_bytes() == TEMPORAL_GOLDEN.read_bytes(), _drift_hint(
        "Temporal"
    )


def test_n8n_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_vulns_artifact_n8n

    result = emit_vulns_artifact_n8n(_n8n_payload(_ctx()), tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == N8N_GOLDEN.read_bytes(), _drift_hint("n8n")


def test_langgraph_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import emit_vulns_artifact_node

    update = emit_vulns_artifact_node(
        {
            "vulns_context": _ctx(),
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["vulns_artifact_path"])
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
def test_response_band_drawn_from_shared_vocabulary(fixture: Path) -> None:
    """``response.band`` on the artifact must be one of the four bands
    pinned by ``schemas/vuln_response_band.json``. If a target's
    adapter silently re-coerced the value (e.g. uppercased it or
    expanded a synonym), this test fails before the per-target
    byte-parity test does, giving a precise diagnosis.
    """
    record = _load_json(fixture)
    assert record["response"]["band"] in _enum(VULN_RESPONSE_BAND_SCHEMA)
    assert record["response"]["band"] == _ctx().response.band


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_cra_clock_drawn_from_shared_vocabulary(fixture: Path) -> None:
    """``triage_decision.cra_clock`` reuses the promoted
    ``cra_clock_kind`` vocabulary; pin the invariant so a future
    adapter cannot fork the enum.
    """
    record = _load_json(fixture)
    assert record["triage_decision"]["cra_clock"] in _enum(CRA_CLOCK_KIND_SCHEMA)
    assert record["triage_decision"]["cra_clock"] == _ctx().triage_decision.cra_clock


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_disclosure_milestones_drawn_from_shared_vocabulary(
    fixture: Path,
) -> None:
    """Each entry on ``disclosure_timeline`` carries a milestone name
    drawn from ``schemas/cra_timing_milestone.json``. The pin guards
    against an adapter that re-spells one of the four names (e.g.
    ``early-warning-24h`` instead of ``early_warning_24h``).
    """
    record = _load_json(fixture)
    allowed = _enum(CRA_TIMING_MILESTONE_SCHEMA)
    seen = [entry["milestone"] for entry in record["disclosure_timeline"]]
    assert seen, "fixture must exercise the disclosure_timeline branch"
    for name in seen:
        assert name in allowed, f"unknown CRA milestone: {name}"
    assert seen == [m.milestone for m in _ctx().disclosure_timeline]


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_dedup_outcome_preserved(fixture: Path) -> None:
    """``triage_decision.dedup_outcome`` is one of the two-value
    vocabulary pinned by the shared emitter. Adapters must not
    re-coerce ``new`` / ``duplicate``.
    """
    record = _load_json(fixture)
    assert record["triage_decision"]["dedup_outcome"] in {"new", "duplicate"}
    assert (
        record["triage_decision"]["dedup_outcome"]
        == _ctx().triage_decision.dedup_outcome
    )


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
    ``SHA-256(<case_ref>|<execution_id>)`` per the schema contract.
    Replays of the same execution must re-derive the same id, so
    downstream deduplication is trivial. Pin the value alongside the
    per-target bytes so a target that silently re-derives the id from
    a different key fails fast.
    """
    ctx = _ctx()
    record = _load_json(fixture)
    expected = derive_vulns_artifact_id(ctx.case_ref, ctx.execution_id)
    assert record["artifact_id"] == expected


def test_artifact_id_byte_identical_across_targets() -> None:
    """The artifact_id is contained verbatim in each golden's bytes;
    cross-target parity at the byte level is already pinned in
    ``test_golden_fixtures_are_byte_identical_across_targets``, but
    naming the id in this test gives a precise diagnosis if a target
    drifts on the derivation rather than on the surrounding shape.
    """
    ctx = _ctx()
    needle = f'"artifact_id": "{derive_vulns_artifact_id(ctx.case_ref, ctx.execution_id)}"'.encode(
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
    record = render_vulns_artifact(_ctx())
    serialised = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    assert serialised == TEMPORAL_GOLDEN.read_bytes()
