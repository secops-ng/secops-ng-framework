"""F-CP-02 EXTEND-tests-goldens — per-target byte-parity goldens.

These tests pin the on-disk bytes of the incidents evidence
artifact emitted by each compile target (n8n, Temporal, LangGraph)
against a checked-in fixture under
``tests/fixtures/incidents_evidence/<target>.json``.

The CORE-FANOUT round-trip in
``tests/content_model/test_incidents_evidence_emitter.py`` already
pins cross-target equivalence (all three targets agree byte-for-byte
under one execution). These tests are the EXTEND complement: each
target's adapter is exercised against an immutable golden so a refactor
of the shared emitter that silently changes serialisation gets caught
at the byte level — one fixture per target so the failure message names
which target drifted, mirroring the F-CP-01 risk-analysis and F-CP-04
vulnerabilities goldens.

Coverage axes (per the F-CP-02 EXTEND-tests-goldens contract):

1. **Schema-conformant emit.** Each target's on-disk artifact validates
   against ``schemas/evidence/incidents.schema.json`` (with the promoted
   ``nis2_incident_notification_milestone`` schema resolved).
2. **NIS2 Article 23(4) milestone vocabulary.** The fixture exercises
   all three milestones on a single ``notification_timeline`` — the
   24h early warning, the 72h incident notification, and the
   one-month final report — drawn from the promoted
   ``nis2_incident_notification_milestone`` vocabulary; the adapters
   do not coerce or rewrite the values the context carried in.
3. **artifact_id determinism.** ``artifact_id`` on the on-disk record
   matches ``SHA-256(<incident_id>|<execution_id>)`` per the schema
   contract and is byte-identical across targets.

If the shared emitter changes the on-disk serialisation intentionally,
regenerate the goldens by re-running the cross-target round-trip in
``test_incidents_evidence_emitter.py``, copying any one of the three
(they MUST be byte-identical) into each fixture, and committing the
updated bytes alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, RefResolver

from compilers._shared.evidence import (
    ClassificationVerdict,
    IncidentsContext,
    KpiWindows,
    Lifecycle,
    NotificationMilestone,
    derive_incidents_artifact_id,
    render_incidents_artifact,
)

REPO = Path(__file__).resolve().parents[3]
SCHEMAS = REPO / "schemas"
NIS2_MILESTONE_SCHEMA = SCHEMAS / "nis2_incident_notification_milestone.json"
INCIDENTS_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "incidents.schema.json"

FIXTURES = REPO / "tests" / "fixtures" / "incidents_evidence"
N8N_GOLDEN = FIXTURES / "n8n.json"
TEMPORAL_GOLDEN = FIXTURES / "temporal.json"
LANGGRAPH_GOLDEN = FIXTURES / "langgraph.json"


# --------------------------------------------------------------------------- #
# Shared fixture context                                                       #
# --------------------------------------------------------------------------- #


def _ctx() -> IncidentsContext:
    """The canonical incident context the three goldens pin against.

    Covers the union of the schema's significant-incident surface: a
    significant, single-jurisdiction case with the High severity band,
    a full lifecycle with every optional marker populated, a
    ``notification_timeline`` exercising all three NIS2 Article 23(4)
    milestones — 24h early warning, 72h incident notification, and the
    one-month final report — drawn from the promoted
    ``nis2_incident_notification_milestone`` vocabulary, and a full
    ``kpi_windows`` quartet. Picking the union shape on every
    promoted-vocabulary axis guards the enum-normalisation pin below
    and makes the fixture a single byte-stable witness of the schema's
    SKELETON-tier coverage.
    """
    started = datetime(2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc)
    return IncidentsContext(
        incident_id="1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
        execution_id="temporal:wf-run-incident-001",
        regulation_refs=(
            "nis2:art-21-2-b",
            "nis2:art-23-early-warning",
            "nis2:art-23-notification-72h",
            "nis2:art-23-final-report",
        ),
        control_refs=(
            "control.incident_handling_capability@v1",
            "control.incident_timeline_signals@v1",
        ),
        classification=ClassificationVerdict(
            significant=True,
            cross_border=False,
            reasons=(
                "Severe disruption to availability of an essential service.",
            ),
            rule_ids=("sig.severe_disruption",),
            severity="High",
            summary=(
                "Authentication-edge availability lost for 47 minutes; "
                "containment via failover to standby region; root cause "
                "scoped to misapplied configuration change."
            ),
        ),
        lifecycle=Lifecycle(
            first_observation_at=datetime(
                2026, 6, 5, 12, 0, 0, tzinfo=timezone.utc
            ),
            detected_at=datetime(2026, 6, 5, 12, 30, 0, tzinfo=timezone.utc),
            triaged_at=datetime(2026, 6, 5, 12, 45, 0, tzinfo=timezone.utc),
            contained_at=datetime(2026, 6, 5, 13, 17, 0, tzinfo=timezone.utc),
            eradicated_at=datetime(2026, 6, 5, 14, 0, 0, tzinfo=timezone.utc),
            recovered_at=datetime(2026, 6, 5, 14, 30, 0, tzinfo=timezone.utc),
            closed_at=datetime(2026, 6, 6, 9, 0, 0, tzinfo=timezone.utc),
        ),
        owner_role="csirt@example.org",
        owner_assigned_at="2026-06-05",
        captured_at=datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/incident-001",
        notification_timeline=(
            NotificationMilestone(
                milestone="early_warning_24h",
                clock_started_at=started,
                submitted_at=datetime(
                    2026, 6, 5, 18, 0, 0, tzinfo=timezone.utc
                ),
                submission_ref="csirt-early_warning_24h",
                on_time=True,
            ),
            NotificationMilestone(
                milestone="incident_notification_72h",
                clock_started_at=started,
                submitted_at=datetime(
                    2026, 6, 6, 9, 0, 0, tzinfo=timezone.utc
                ),
                submission_ref="csirt-incident_notification_72h",
                on_time=True,
            ),
            NotificationMilestone(
                milestone="final_report_1mo",
                clock_started_at=started,
                submitted_at=datetime(
                    2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc
                ),
                submission_ref="csirt-final_report_1mo",
                on_time=True,
            ),
        ),
        kpi_windows=KpiWindows(
            mttd_minutes=30.0,
            mttr_minutes=47.0,
            containment_window_minutes=43.0,
            eradication_window_minutes=30.0,
        ),
        commit_sha="deadbeef0123456789",
    )


def _n8n_payload(ctx: IncidentsContext) -> dict:
    """Re-shape a context as the JSON-native payload an n8n node sends.

    n8n cannot transport Python objects across the node-process boundary,
    so datetimes arrive as ISO-8601 ``...Z`` strings and nested
    dataclasses arrive as JSON objects / arrays. Kept in lockstep with
    the ``_payload_from_ctx`` helper in
    ``tests/content_model/test_incidents_evidence_emitter.py``.
    """
    cls = ctx.classification
    classification: dict = {
        "significant": cls.significant,
        "cross_border": cls.cross_border,
        "reasons": list(cls.reasons),
        "rule_ids": list(cls.rule_ids),
    }
    if cls.severity is not None:
        classification["severity"] = cls.severity
    if cls.summary is not None:
        classification["summary"] = cls.summary

    lc = ctx.lifecycle
    lifecycle: dict = {
        "detected_at": lc.detected_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    for name in (
        "first_observation_at",
        "triaged_at",
        "contained_at",
        "eradicated_at",
        "recovered_at",
        "closed_at",
    ):
        value = getattr(lc, name)
        if value is not None:
            lifecycle[name] = value.strftime("%Y-%m-%dT%H:%M:%SZ")

    payload: dict = {
        "incident_id": ctx.incident_id,
        "execution_id": ctx.execution_id,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "classification": classification,
        "lifecycle": lifecycle,
        "owner_role": ctx.owner_role,
        "owner_assigned_at": ctx.owner_assigned_at,
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": ctx.source_url,
    }
    if ctx.commit_sha:
        payload["commit_sha"] = ctx.commit_sha
    if ctx.retention:
        payload["retention"] = ctx.retention
    if ctx.notification_timeline:
        payload["notification_timeline"] = []
        for m in ctx.notification_timeline:
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
            payload["notification_timeline"].append(entry)
    if ctx.kpi_windows is not None:
        kw = ctx.kpi_windows
        windows: dict = {}
        if kw.mttd_minutes is not None:
            windows["mttd_minutes"] = kw.mttd_minutes
        if kw.mttr_minutes is not None:
            windows["mttr_minutes"] = kw.mttr_minutes
        if kw.containment_window_minutes is not None:
            windows["containment_window_minutes"] = kw.containment_window_minutes
        if kw.eradication_window_minutes is not None:
            windows["eradication_window_minutes"] = kw.eradication_window_minutes
        if windows:
            payload["kpi_windows"] = windows
    return payload


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    schema = _load_json(INCIDENTS_EVIDENCE_SCHEMA)
    store = {
        "https://secops-ng.org/schemas/nis2_incident_notification_milestone.json": _load_json(
            NIS2_MILESTONE_SCHEMA
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
        f"{target} incidents evidence artifact drifted from the "
        f"committed golden. If the change is intentional, regenerate "
        f"the goldens by re-running the cross-target round-trip in "
        f"tests/content_model/test_incidents_evidence_emitter.py and "
        f"committing the new bytes alongside the emitter change."
    )


def test_temporal_artifact_matches_golden(tmp_path: Path) -> None:
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_incidents_artifact_activity

    written = Path(
        asyncio.run(emit_incidents_artifact_activity(_ctx(), str(tmp_path)))
    )
    assert written.read_bytes() == TEMPORAL_GOLDEN.read_bytes(), _drift_hint(
        "Temporal"
    )


def test_n8n_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_incidents_artifact_n8n

    result = emit_incidents_artifact_n8n(_n8n_payload(_ctx()), tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == N8N_GOLDEN.read_bytes(), _drift_hint("n8n")


def test_langgraph_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import emit_incidents_artifact_node

    update = emit_incidents_artifact_node(
        {
            "incidents_context": _ctx(),
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["incidents_artifact_path"])
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
# Coverage axis 2: NIS2 Article 23(4) milestone vocabulary                    #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_notification_milestones_drawn_from_shared_vocabulary(
    fixture: Path,
) -> None:
    """Each entry on ``notification_timeline`` carries a milestone name
    drawn from ``schemas/nis2_incident_notification_milestone.json``.
    The pin guards against an adapter that re-spells one of the three
    names (e.g. ``early-warning-24h`` instead of ``early_warning_24h``)
    or coerces them to a different casing.
    """
    record = _load_json(fixture)
    allowed = _enum(NIS2_MILESTONE_SCHEMA)
    seen = [entry["milestone"] for entry in record["notification_timeline"]]
    assert seen, "fixture must exercise the notification_timeline branch"
    for name in seen:
        assert name in allowed, f"unknown NIS2 milestone: {name}"
    assert seen == [m.milestone for m in _ctx().notification_timeline]


def test_fixture_exercises_all_three_nis2_milestones() -> None:
    """Acceptance pin from the task body: the fixture MUST cover the
    NIS2 Article 23(4) three-milestone vocabulary — 24h early warning,
    72h incident notification, 1mo final report — on a single
    notification_timeline. If a future edit drops one, fail loudly so
    the parity beat doesn't silently lose schema-surface coverage.
    """
    record = _load_json(TEMPORAL_GOLDEN)
    seen = {entry["milestone"] for entry in record["notification_timeline"]}
    assert seen == {
        "early_warning_24h",
        "incident_notification_72h",
        "final_report_1mo",
    }


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_classification_significance_preserved(fixture: Path) -> None:
    """``classification.significant`` is the NIS2 Article 23(3)
    gateway: false suppresses regulator notification, true gates the
    Article 23(4) clock. Adapters must not coerce the boolean.
    """
    record = _load_json(fixture)
    assert record["classification"]["significant"] is True
    assert (
        record["classification"]["significant"]
        == _ctx().classification.significant
    )


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_classification_severity_preserved(fixture: Path) -> None:
    """``classification.severity`` is constrained by the incidents
    schema; the adapters must not re-coerce the value the context
    carried in.
    """
    record = _load_json(fixture)
    assert record["classification"]["severity"] == _ctx().classification.severity


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
    ``SHA-256(<incident_id>|<execution_id>)`` per the schema contract.
    Replays of the same execution must re-derive the same id, so
    downstream deduplication is trivial. Pin the value alongside the
    per-target bytes so a target that silently re-derives the id from
    a different key fails fast.
    """
    ctx = _ctx()
    record = _load_json(fixture)
    expected = derive_incidents_artifact_id(
        ctx.incident_id, ctx.execution_id
    )
    assert record["artifact_id"] == expected


def test_artifact_id_byte_identical_across_targets() -> None:
    """The artifact_id is contained verbatim in each golden's bytes;
    cross-target parity at the byte level is already pinned in
    ``test_golden_fixtures_are_byte_identical_across_targets``, but
    naming the id in this test gives a precise diagnosis if a target
    drifts on the derivation rather than on the surrounding shape.
    """
    ctx = _ctx()
    needle = (
        f'"artifact_id": "{derive_incidents_artifact_id(ctx.incident_id, ctx.execution_id)}"'
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
    reproduce the golden bytes. Guards the case where a future
    refactor moves serialisation logic out of the emitter into the
    adapters — the byte-parity pin should still hold against the
    pure render path.
    """
    rendered = render_incidents_artifact(_ctx())
    serialised = (
        json.dumps(rendered, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert serialised == TEMPORAL_GOLDEN.read_bytes()
