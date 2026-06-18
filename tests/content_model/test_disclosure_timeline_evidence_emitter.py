"""F-WF-07 CORE-N8N — codebase disclosure-timeline emitter round-trip.

Pins:

1. The shared emitter renders / writes a record that validates against
   ``content/evidence/codebase-vuln-management/disclosure-timeline-record.schema.json``.
2. The record ``id`` is deterministic on
   ``(workflow_id, sbom_content_hash, component.purl, advisory_id)``
   — same inputs reproduce the same id; different inputs do not.
3. The record persists to disk under ``<output_dir>/<id>.json`` and
   re-reads byte-identical to the rendered record.
4. The n8n adapter delegates to the shared helper and produces the
   same on-disk record for the same context, marshalled through the
   JSON-native shape an n8n Code / executeCommand node would send.

CORE-N8N only — Temporal and LangGraph adapters live in separate
CORE-TEMPORAL / CORE-LANGGRAPH siblings; per-target byte-parity
goldens land in an EXTEND-tests sibling.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    ComponentRef,
    DisclosureTimelineContext,
    DisclosureWindow,
    SourceData,
    derive_disclosure_timeline_artifact_id,
    emit_disclosure_timeline_artifact,
    render_disclosure_timeline_artifact,
)
from compilers._shared.evidence.disclosure_timeline import EmitError
from compilers.n8n.evidence import emit_disclosure_timeline_artifact_n8n

REPO = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO
    / "content"
    / "evidence"
    / "codebase-vuln-management"
    / "disclosure-timeline-record.schema.json"
)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(SCHEMA_PATH))


def _ctx(**overrides) -> DisclosureTimelineContext:
    started = datetime(2026, 6, 18, 5, 0, 0, tzinfo=timezone.utc)
    base: dict = dict(
        sbom_content_hash=(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        ),
        advisory_id="CVE-2026-0001",
        component=ComponentRef(
            purl="pkg:pypi/example-lib", version="1.4.2"
        ),
        severity="high",
        disclosure_window=DisclosureWindow(
            policy_ref="policy.cvd@v1",
            acknowledge_by=started.replace(day=19),
            fix_by=datetime(2026, 7, 2, 5, 0, 0, tzinfo=timezone.utc),
            disclose_by=datetime(2026, 7, 16, 5, 0, 0, tzinfo=timezone.utc),
        ),
        source_data=SourceData(kind="ocsf", ocsf_class_uid=2002),
        ref_viz="viz.codebase_vuln_management@v1",
        captured_at=started,
    )
    base.update(overrides)
    return DisclosureTimelineContext(**base)


def _n8n_payload(ctx: DisclosureTimelineContext) -> dict:
    """Mirror the on-the-wire shape an n8n Code node would send."""
    win = ctx.disclosure_window
    src = ctx.source_data
    source_data: dict = {"kind": src.kind}
    if src.ocsf_class_uid is not None:
        source_data["ocsf_class_uid"] = src.ocsf_class_uid
    if src.telemetry_ref is not None:
        source_data["telemetry_ref"] = src.telemetry_ref
    return {
        "sbom_content_hash": ctx.sbom_content_hash,
        "advisory_id": ctx.advisory_id,
        "component": {
            "purl": ctx.component.purl,
            "version": ctx.component.version,
        },
        "severity": ctx.severity,
        "disclosure_window": {
            "policy_ref": win.policy_ref,
            "acknowledge_by": win.acknowledge_by.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "fix_by": win.fix_by.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "disclose_by": win.disclose_by.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "source_data": source_data,
        "ref_viz": ctx.ref_viz,
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# --------------------------------------------------------------------------- #
# Schema-conformant emit                                                      #
# --------------------------------------------------------------------------- #


def test_rendered_record_validates_against_schema() -> None:
    _validator().validate(render_disclosure_timeline_artifact(_ctx()))


def test_telemetry_source_kind_validates() -> None:
    ctx = _ctx(
        source_data=SourceData(
            kind="telemetry",
            telemetry_ref="telemetry.codebase_advisory_intake@v1",
        )
    )
    _validator().validate(render_disclosure_timeline_artifact(ctx))


def test_none_source_kind_validates() -> None:
    ctx = _ctx(source_data=SourceData(kind="none"))
    _validator().validate(render_disclosure_timeline_artifact(ctx))


def test_ghsa_advisory_id_accepted() -> None:
    ctx = _ctx(advisory_id="GHSA-aaaa-bbbb-cccc")
    _validator().validate(render_disclosure_timeline_artifact(ctx))


def test_osv_advisory_id_accepted() -> None:
    ctx = _ctx(advisory_id="OSV-2026-0042")
    _validator().validate(render_disclosure_timeline_artifact(ctx))


# --------------------------------------------------------------------------- #
# Deterministic id                                                            #
# --------------------------------------------------------------------------- #


def test_id_is_deterministic_on_pinned_inputs() -> None:
    ctx = _ctx()
    a = render_disclosure_timeline_artifact(ctx)["id"]
    b = render_disclosure_timeline_artifact(ctx)["id"]
    assert a == b
    # ``captured_at`` is deliberately NOT part of the id — re-emissions
    # inside the same case stay byte-identical at the path level.
    later = datetime(2026, 6, 19, 7, 0, 0, tzinfo=timezone.utc)
    c = render_disclosure_timeline_artifact(_ctx(captured_at=later))["id"]
    assert a == c


def test_id_changes_when_any_pinned_input_changes() -> None:
    base = render_disclosure_timeline_artifact(_ctx())["id"]
    diff_sbom = render_disclosure_timeline_artifact(
        _ctx(
            sbom_content_hash=(
                "1111111111111111111111111111111111111111111111111111111111111111"
            )
        )
    )["id"]
    diff_adv = render_disclosure_timeline_artifact(
        _ctx(advisory_id="CVE-2026-9999")
    )["id"]
    diff_comp = render_disclosure_timeline_artifact(
        _ctx(component=ComponentRef(purl="pkg:npm/example", version="2.0.0"))
    )["id"]
    assert len({base, diff_sbom, diff_adv, diff_comp}) == 4


def test_derive_artifact_id_matches_rendered_id() -> None:
    ctx = _ctx()
    expected = derive_disclosure_timeline_artifact_id(
        ctx.workflow_id,
        ctx.sbom_content_hash,
        ctx.component.purl,
        ctx.advisory_id,
    )
    assert render_disclosure_timeline_artifact(ctx)["id"] == expected


# --------------------------------------------------------------------------- #
# On-disk persistence                                                          #
# --------------------------------------------------------------------------- #


def test_emit_writes_artifact_id_named_file(tmp_path: Path) -> None:
    ctx = _ctx()
    written = emit_disclosure_timeline_artifact(ctx, tmp_path)
    record = _load_json(written)
    assert written.name == f"{record['id']}.json"
    _validator().validate(record)


def test_emit_is_idempotent_on_re_emission(tmp_path: Path) -> None:
    ctx = _ctx()
    first = emit_disclosure_timeline_artifact(ctx, tmp_path).read_bytes()
    second = emit_disclosure_timeline_artifact(ctx, tmp_path).read_bytes()
    assert first == second


# --------------------------------------------------------------------------- #
# n8n adapter parity                                                           #
# --------------------------------------------------------------------------- #


def test_n8n_adapter_matches_shared_emitter(tmp_path: Path) -> None:
    ctx = _ctx()
    shared_dir = tmp_path / "shared"
    n8n_dir = tmp_path / "n8n"
    shared_path = emit_disclosure_timeline_artifact(ctx, shared_dir)
    result = emit_disclosure_timeline_artifact_n8n(
        _n8n_payload(ctx), n8n_dir
    )
    n8n_path = Path(result["artifact_path"])
    assert result["artifact_id"] == shared_path.stem
    assert n8n_path.name == shared_path.name
    assert n8n_path.read_bytes() == shared_path.read_bytes()


def test_n8n_adapter_parses_z_suffix() -> None:
    # n8n payloads carry ISO-8601 with the literal ``Z`` suffix; the
    # adapter must normalise to ``+00:00`` before parsing.
    payload = _n8n_payload(_ctx())
    assert payload["captured_at"].endswith("Z")
    # If the adapter could not parse the suffix the call would raise.
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        result = emit_disclosure_timeline_artifact_n8n(payload, td)
        assert Path(result["artifact_path"]).exists()


# --------------------------------------------------------------------------- #
# Shape-error surfacing                                                       #
# --------------------------------------------------------------------------- #


def test_invalid_sbom_hash_raises_emit_error() -> None:
    with pytest.raises(EmitError):
        render_disclosure_timeline_artifact(_ctx(sbom_content_hash="nothex"))


def test_invalid_severity_raises_emit_error() -> None:
    with pytest.raises(EmitError):
        render_disclosure_timeline_artifact(_ctx(severity="CRITICAL"))


def test_naive_captured_at_raises_emit_error() -> None:
    with pytest.raises(EmitError):
        render_disclosure_timeline_artifact(
            _ctx(captured_at=datetime(2026, 6, 18, 5, 0, 0))
        )


def test_telemetry_kind_requires_telemetry_ref() -> None:
    with pytest.raises(EmitError):
        render_disclosure_timeline_artifact(
            _ctx(source_data=SourceData(kind="telemetry"))
        )


def test_ocsf_kind_rejects_telemetry_ref() -> None:
    with pytest.raises(EmitError):
        render_disclosure_timeline_artifact(
            _ctx(
                source_data=SourceData(
                    kind="ocsf",
                    ocsf_class_uid=2002,
                    telemetry_ref="telemetry.example@v1",
                )
            )
        )


def test_none_kind_rejects_any_pointer_field() -> None:
    with pytest.raises(EmitError):
        render_disclosure_timeline_artifact(
            _ctx(source_data=SourceData(kind="none", ocsf_class_uid=2002))
        )


def test_invalid_policy_ref_raises_emit_error() -> None:
    bad_window = DisclosureWindow(
        policy_ref="cvd@v1",  # missing policy. prefix
        acknowledge_by=datetime(2026, 6, 19, 5, 0, 0, tzinfo=timezone.utc),
        fix_by=datetime(2026, 7, 2, 5, 0, 0, tzinfo=timezone.utc),
        disclose_by=datetime(2026, 7, 16, 5, 0, 0, tzinfo=timezone.utc),
    )
    with pytest.raises(EmitError):
        render_disclosure_timeline_artifact(_ctx(disclosure_window=bad_window))
