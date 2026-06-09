"""F-CP-04 — vulnerabilities evidence-artifact round-trip (cross-target).

Pins:

1. The shared emitter writes a record that validates against
   ``schemas/evidence/vulns.schema.json`` (with the promoted
   ``cra_clock_kind``, ``cra_timing_milestone``, and
   ``vuln_response_band`` schemas resolved).
2. The ``artifact_id`` is deterministic on ``(case_ref, execution_id)``
   — same inputs reproduce the same id; different inputs do not.
3. The record persists to disk under ``<output_dir>/<artifact_id>.json``
   and re-reads byte-identical to the rendered record.
4. All three compile-target adapters (Temporal activity, n8n CLI/Code
   adapter, LangGraph node) delegate to the shared helper and produce
   the same on-disk record for the same context — CORE-FANOUT pins
   parity at the record-shape level; per-target byte-parity goldens
   land in the EXTEND-tests sibling.
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
    emit_vulns_artifact,
    render_vulns_artifact,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
VULN_RESPONSE_BAND_SCHEMA = SCHEMAS / "vuln_response_band.json"
CRA_CLOCK_KIND_SCHEMA = SCHEMAS / "cra_clock_kind.json"
CRA_TIMING_MILESTONE_SCHEMA = SCHEMAS / "cra_timing_milestone.json"
VULNS_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "vulns.schema.json"


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


def _case_ref() -> str:
    return sha256(b"CVE-2026-0001|pkg:generic/example@1.0.0").hexdigest()


def _ctx(**overrides) -> VulnsContext:
    base = dict(
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
                "Pre-authentication RCE on the network edge; exploitation "
                "observed in the wild. Mitigation requires the upcoming patch."
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
                clock_started_at=datetime(
                    2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc
                ),
                submitted_at=datetime(2026, 6, 7, 18, 0, 0, tzinfo=timezone.utc),
                submission_ref="csirt-ticket-001",
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
    base.update(overrides)
    return VulnsContext(**base)


def test_rendered_record_validates_against_schema() -> None:
    record = render_vulns_artifact(_ctx())
    _validator().validate(record)


def test_artifact_id_is_deterministic_on_case_ref_and_execution_id() -> None:
    ctx_a = _ctx()
    # Same inputs → same id.
    assert (
        render_vulns_artifact(ctx_a)["artifact_id"]
        == render_vulns_artifact(ctx_a)["artifact_id"]
    )
    expected = derive_vulns_artifact_id(ctx_a.case_ref, ctx_a.execution_id)
    assert render_vulns_artifact(ctx_a)["artifact_id"] == expected
    # Different execution_id → different id; same case_ref carries through.
    ctx_b = _ctx(execution_id="temporal:wf-run-zzz999")
    rendered_b = render_vulns_artifact(ctx_b)
    assert rendered_b["artifact_id"] != render_vulns_artifact(ctx_a)["artifact_id"]
    assert rendered_b["case_ref"] == render_vulns_artifact(ctx_a)["case_ref"]


def test_emit_persists_round_trip(tmp_path: Path) -> None:
    ctx = _ctx()
    written = emit_vulns_artifact(ctx, tmp_path)
    assert written.exists()
    assert written.name == f"{render_vulns_artifact(ctx)['artifact_id']}.json"
    on_disk = json.loads(written.read_text("utf-8"))
    assert on_disk == render_vulns_artifact(ctx)
    _validator().validate(on_disk)


def test_emit_covers_all_four_cra_milestones(tmp_path: Path) -> None:
    """Acceptance pin: SCHEMA names four CRA-timing milestones; one
    artifact MUST be able to carry all four on a single
    ``disclosure_timeline``. CRA Article 14(3) (severe_incident_24h)
    typically lands on a separate case than the 14(1) chain in
    practice, but the schema admits both; the SKELETON pins the shape.
    """
    started = datetime(2026, 6, 7, 5, 0, 0, tzinfo=timezone.utc)
    submitted = datetime(2026, 6, 8, 5, 0, 0, tzinfo=timezone.utc)
    timeline = tuple(
        DisclosureMilestone(
            milestone=name,
            clock_started_at=started,
            submitted_at=submitted,
            submission_ref=f"csirt-{name}",
            on_time=True,
        )
        for name in (
            "early_warning_24h",
            "severe_incident_24h",
            "incident_notification_72h",
            "final_report_14d",
        )
    )
    written = emit_vulns_artifact(_ctx(disclosure_timeline=timeline), tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert [m["milestone"] for m in on_disk["disclosure_timeline"]] == [
        "early_warning_24h",
        "severe_incident_24h",
        "incident_notification_72h",
        "final_report_14d",
    ]


def test_emit_accepts_accept_band_with_rationale(tmp_path: Path) -> None:
    ctx = _ctx(
        triage_decision=TriageDecision(
            severity="Low",
            cvss_severity="Low",
            cra_clock="none",
            dedup_outcome="new",
            cvss_base_score=3.1,
            actively_exploited=False,
        ),
        response=ResponseBranch(
            band="accept",
            accept_rationale=(
                "Asset out of support; compensating controls in place per "
                "control.network_segmentation@v1."
            ),
            compensating_controls=("control.network_segmentation@v1",),
        ),
    )
    written = emit_vulns_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk["response"]["band"] == "accept"


def test_emit_omits_reporter_acknowledgement_for_internal_finding(
    tmp_path: Path,
) -> None:
    """Internal scanner findings do not carry a CVD-intake acknowledgement.
    The schema marks ``reporter_acknowledgement`` as optional; the
    helper must not emit an empty key.
    """
    ctx = _ctx(reporter_acknowledgement=None)
    written = emit_vulns_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert "reporter_acknowledgement" not in on_disk


def test_emit_rejects_bad_case_ref(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_vulns_artifact(_ctx(case_ref="not-a-hex-digest"), tmp_path)


def test_emit_rejects_bad_response_band(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_vulns_artifact(
            _ctx(response=ResponseBranch(band="bogus")),
            tmp_path,
        )


def test_emit_rejects_accept_band_without_rationale(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_vulns_artifact(
            _ctx(response=ResponseBranch(band="accept")),
            tmp_path,
        )


def test_emit_rejects_duplicate_without_collision_pointer(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_vulns_artifact(
            _ctx(
                triage_decision=TriageDecision(
                    severity="High",
                    cvss_severity="High",
                    cra_clock="none",
                    dedup_outcome="duplicate",
                )
            ),
            tmp_path,
        )


def test_emit_rejects_naive_captured_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_vulns_artifact(
            _ctx(captured_at=datetime(2026, 6, 7, 5, 0, 0)),
            tmp_path,
        )


def test_emit_rejects_bad_cra_clock(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_vulns_artifact(
            _ctx(
                triage_decision=TriageDecision(
                    severity="High",
                    cvss_severity="High",
                    cra_clock="art-14-bogus",
                    dedup_outcome="new",
                )
            ),
            tmp_path,
        )


def test_temporal_activity_wraps_shared_helper(tmp_path: Path) -> None:
    # Import lazily so the rest of the test module still runs in environments
    # without temporalio installed.
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_vulns_artifact_activity

    ctx = _ctx()
    # ``@activity.defn`` returns the original async callable, so the
    # function is awaitable directly without unwrapping.
    written_str = asyncio.run(emit_vulns_artifact_activity(ctx, str(tmp_path)))
    written = Path(written_str)
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_vulns_artifact(ctx)


def _payload_from_ctx(ctx: VulnsContext) -> dict:
    """Re-shape a context as the JSON-native payload an n8n node sends.

    n8n cannot transport Python objects across the node-process boundary,
    so datetimes arrive as ISO-8601 strings and nested dataclasses
    arrive as JSON objects / arrays. We mirror the on-the-wire shape
    here so the adapter exercises the same parse path an operator would
    hit in production.
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


def test_n8n_adapter_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_vulns_artifact_n8n

    ctx = _ctx()
    result = emit_vulns_artifact_n8n(_payload_from_ctx(ctx), tmp_path)
    written = Path(result["artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_vulns_artifact(ctx)
    assert result["artifact_id"] == on_disk["artifact_id"]
    assert written.name == f"{on_disk['artifact_id']}.json"


def test_langgraph_node_wraps_shared_helper(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import emit_vulns_artifact_node

    ctx = _ctx()
    state = {
        "vulns_context": ctx,
        "evidence_output_dir": str(tmp_path),
    }
    update = emit_vulns_artifact_node(state)
    written = Path(update["vulns_artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_vulns_artifact(ctx)
    assert update["vulns_artifact_id"] == on_disk["artifact_id"]


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
    from compilers.temporal.evidence import emit_vulns_artifact_activity
    from compilers.n8n.evidence import emit_vulns_artifact_n8n
    from compilers.langgraph.evidence import emit_vulns_artifact_node

    ctx = _ctx()

    tmp_temporal = tmp_path / "temporal"
    tmp_n8n = tmp_path / "n8n"
    tmp_langgraph = tmp_path / "langgraph"

    temporal_path = Path(
        asyncio.run(emit_vulns_artifact_activity(ctx, str(tmp_temporal)))
    )
    n8n_result = emit_vulns_artifact_n8n(_payload_from_ctx(ctx), tmp_n8n)
    n8n_path = Path(n8n_result["artifact_path"])
    langgraph_update = emit_vulns_artifact_node(
        {
            "vulns_context": ctx,
            "evidence_output_dir": str(tmp_langgraph),
        }
    )
    langgraph_path = Path(langgraph_update["vulns_artifact_path"])

    # Same artifact_id across all three targets.
    assert temporal_path.stem == n8n_path.stem == langgraph_path.stem

    # Byte-identical on-disk JSON.
    bytes_temporal = temporal_path.read_bytes()
    bytes_n8n = n8n_path.read_bytes()
    bytes_langgraph = langgraph_path.read_bytes()
    assert bytes_temporal == bytes_n8n == bytes_langgraph
