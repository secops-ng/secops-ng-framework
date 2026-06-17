"""F-WF-09 — auditor-bundle collector cross-target equivalence (CORE-FANOUT).

Pins (CORE-FANOUT scope — per-target byte-parity goldens land in the
EXTEND-tests-goldens sibling card; the ROADMAP flip lands in the
CLOSEOUT sibling):

1. Each of the three reference adapters (n8n + Temporal + LangGraph)
   delegates to ``compilers._shared.evidence.emit_bundle_manifest`` and
   writes a manifest that validates against
   ``schemas/evidence/bundle.schema.json``.
2. All three adapters produce a byte-identical
   ``bundle.manifest.json`` for the same evidence-tree context — the
   whole point of the shared helper is that the three compile targets
   cannot drift on manifest shape.
3. The ``bundle_id`` is deterministic on
   ``(generated_at, bundle_window_start, bundle_window_end)`` —
   re-emissions within the same window stay stable across targets.

Mirrors exactly the cross-target equivalence pin in
``tests/content_model/test_access_evidence_emitter.py``.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    BundleContext,
    StreamSlot,
    derive_bundle_id,
    emit_bundle_manifest,
    render_bundle_manifest,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
BUNDLE_SCHEMA = SCHEMAS / "evidence" / "bundle.schema.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(BUNDLE_SCHEMA))


def _seed_content_root(root: Path) -> None:
    """Seed an evidence tree with one artifact per non-gated stream.

    Each path matches the canonical
    ``content/evidence/<stream>/<id>.json`` shape the collector walks.
    The ``effectiveness`` stream is left empty on disk to exercise the
    optional/empty slot the SKELETON already carries (F-CP-06 still
    Proposed).
    """
    seeds = {
        "risk-analysis": "risk-001.json",
        "incidents": "incident-001.json",
        "supply-chain": "sbom-001.json",
        "vulns": "vuln-001.json",
        "crypto": "attestation-001.json",
        "access": "access-001.json",
    }
    for stream, name in seeds.items():
        stream_dir = root / "content" / "evidence" / stream
        stream_dir.mkdir(parents=True, exist_ok=True)
        (stream_dir / name).write_text(
            json.dumps({"stream": stream, "id": name.rsplit(".", 1)[0]}),
            encoding="utf-8",
        )


def _ctx(content_root: Path, **overrides) -> BundleContext:
    base: dict[str, Any] = dict(
        content_root=content_root,
        generated_at=datetime(2026, 6, 17, 10, 0, 0, tzinfo=timezone.utc),
        regulation_refs=("nis2:art-21-2-a", "nis2:art-23"),
        source_url="https://example.org/runs/bundle-001",
        bundle_window_start=datetime(
            2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc
        ),
        bundle_window_end=datetime(
            2026, 6, 30, 23, 59, 59, tzinfo=timezone.utc
        ),
        commit_sha="deadbeef0123456789",
        owner_role="compliance-wg",
        owner_assigned_at="2026-01-15",
        retention="P2Y",
    )
    base.update(overrides)
    return BundleContext(**base)


def _payload_from_ctx(ctx: BundleContext) -> dict[str, Any]:
    """Render a BundleContext as the JSON-native payload an n8n node ships.

    Mirrors the wire shape an ``executeCommand`` / ``Code`` node hands to
    the Python helper: ``content_root`` as a string, timestamps as
    ISO-8601 strings, sequence fields as JSON arrays. Optional fields
    are omitted when the source context omits them.
    """
    payload: dict[str, Any] = {
        "content_root": str(ctx.content_root),
        "generated_at": ctx.generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "regulation_refs": list(ctx.regulation_refs),
        "source_url": ctx.source_url,
    }
    if ctx.bundle_window_start is not None:
        payload["bundle_window_start"] = ctx.bundle_window_start.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    if ctx.bundle_window_end is not None:
        payload["bundle_window_end"] = ctx.bundle_window_end.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    if ctx.commit_sha is not None:
        payload["commit_sha"] = ctx.commit_sha
    if ctx.owner_role is not None:
        payload["owner_role"] = ctx.owner_role
    if ctx.owner_assigned_at is not None:
        payload["owner_assigned_at"] = ctx.owner_assigned_at
    if ctx.retention is not None:
        payload["retention"] = ctx.retention
    if ctx.stream_overrides:
        overrides_payload: dict[str, Any] = {}
        for stream_id, slot in ctx.stream_overrides.items():
            sub: dict[str, Any] = {"force_empty": slot.force_empty}
            if slot.regulation_refs is not None:
                sub["regulation_refs"] = list(slot.regulation_refs)
            if slot.notes is not None:
                sub["notes"] = slot.notes
            overrides_payload[stream_id] = sub
        payload["stream_overrides"] = overrides_payload
    return payload


# --------------------------------------------------------------------------- #
# Schema / determinism baseline                                               #
# --------------------------------------------------------------------------- #


def test_rendered_manifest_validates_against_schema(tmp_path: Path) -> None:
    _seed_content_root(tmp_path)
    record = render_bundle_manifest(_ctx(tmp_path))
    _validator().validate(record)


def test_bundle_id_is_deterministic_on_window(tmp_path: Path) -> None:
    _seed_content_root(tmp_path)
    ctx_a = _ctx(tmp_path)
    rendered_a = render_bundle_manifest(ctx_a)
    rendered_a2 = render_bundle_manifest(ctx_a)
    assert rendered_a["bundle_id"] == rendered_a2["bundle_id"]
    assert rendered_a["bundle_id"] == derive_bundle_id(
        ctx_a.generated_at,
        ctx_a.bundle_window_start,
        ctx_a.bundle_window_end,
    )
    ctx_b = _ctx(
        tmp_path,
        bundle_window_end=datetime(
            2026, 7, 31, 23, 59, 59, tzinfo=timezone.utc
        ),
    )
    assert (
        render_bundle_manifest(ctx_b)["bundle_id"]
        != rendered_a["bundle_id"]
    )


# --------------------------------------------------------------------------- #
# CORE-FANOUT — n8n + Temporal + LangGraph cross-target equivalence           #
# --------------------------------------------------------------------------- #


def test_n8n_adapter_wraps_shared_helper(tmp_path: Path) -> None:
    content_root = tmp_path / "content_root"
    content_root.mkdir()
    _seed_content_root(content_root)
    out_dir = tmp_path / "out"
    from compilers.n8n.evidence import emit_bundle_manifest_n8n

    ctx = _ctx(content_root)
    result = emit_bundle_manifest_n8n(
        _payload_from_ctx(ctx), out_dir
    )
    written = Path(result["manifest_path"])
    assert written.exists()
    assert written.name == "bundle.manifest.json"
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_bundle_manifest(ctx)
    assert result["bundle_id"] == on_disk["bundle_id"]


def test_langgraph_node_wraps_shared_helper(tmp_path: Path) -> None:
    content_root = tmp_path / "content_root"
    content_root.mkdir()
    _seed_content_root(content_root)
    out_dir = tmp_path / "out"
    from compilers.langgraph.evidence import emit_bundle_manifest_node

    ctx = _ctx(content_root)
    update = emit_bundle_manifest_node(
        {
            "bundle_context": ctx,
            "evidence_output_dir": str(out_dir),
        }
    )
    written = Path(update["bundle_manifest_path"])
    assert written.exists()
    assert written.name == "bundle.manifest.json"
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_bundle_manifest(ctx)
    assert update["bundle_id"] == on_disk["bundle_id"]


def test_temporal_activity_wraps_shared_helper(tmp_path: Path) -> None:
    pytest.importorskip("temporalio")
    content_root = tmp_path / "content_root"
    content_root.mkdir()
    _seed_content_root(content_root)
    out_dir = tmp_path / "out"
    from compilers.temporal.evidence import emit_bundle_manifest_activity

    ctx = _ctx(content_root)
    written_str = asyncio.run(
        emit_bundle_manifest_activity(ctx, str(out_dir))
    )
    written = Path(written_str)
    assert written.exists()
    assert written.name == "bundle.manifest.json"
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_bundle_manifest(ctx)


def test_all_three_targets_produce_byte_identical_manifests(
    tmp_path: Path,
) -> None:
    """CORE-FANOUT parity pin.

    The whole point of the shared collector is that the three compile
    targets cannot drift on manifest shape. Each adapter writes the
    same context into its own subdirectory; the on-disk JSON must match
    byte for byte across targets. Per-target byte-parity goldens
    against a checked-in fixture land in the EXTEND-tests-goldens
    sibling; this test pins the cross-target equivalence today.
    """
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_bundle_manifest_activity
    from compilers.n8n.evidence import emit_bundle_manifest_n8n
    from compilers.langgraph.evidence import emit_bundle_manifest_node

    content_root = tmp_path / "content_root"
    content_root.mkdir()
    _seed_content_root(content_root)

    ctx = _ctx(content_root)

    tmp_temporal = tmp_path / "temporal"
    tmp_n8n = tmp_path / "n8n"
    tmp_langgraph = tmp_path / "langgraph"

    temporal_path = Path(
        asyncio.run(
            emit_bundle_manifest_activity(ctx, str(tmp_temporal))
        )
    )
    n8n_result = emit_bundle_manifest_n8n(
        _payload_from_ctx(ctx), tmp_n8n
    )
    n8n_path = Path(n8n_result["manifest_path"])
    langgraph_update = emit_bundle_manifest_node(
        {
            "bundle_context": ctx,
            "evidence_output_dir": str(tmp_langgraph),
        }
    )
    langgraph_path = Path(langgraph_update["bundle_manifest_path"])

    # Each adapter wrote the canonical filename.
    assert (
        temporal_path.name
        == n8n_path.name
        == langgraph_path.name
        == "bundle.manifest.json"
    )

    # Byte-identical on-disk JSON across all three targets.
    bytes_temporal = temporal_path.read_bytes()
    bytes_n8n = n8n_path.read_bytes()
    bytes_langgraph = langgraph_path.read_bytes()
    assert bytes_temporal == bytes_n8n == bytes_langgraph

    # And the bundle_id channels match.
    assert (
        n8n_result["bundle_id"]
        == langgraph_update["bundle_id"]
        == json.loads(bytes_temporal)["bundle_id"]
    )


def test_effectiveness_slot_stays_empty_across_targets(
    tmp_path: Path,
) -> None:
    """F-CP-06 is still Proposed (F-CR-03 Removed); the SKELETON carries
    the ``effectiveness`` slot as an optional/empty entry. CORE-FANOUT
    must preserve that contract across all three targets.
    """
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_bundle_manifest_activity
    from compilers.n8n.evidence import emit_bundle_manifest_n8n
    from compilers.langgraph.evidence import emit_bundle_manifest_node

    content_root = tmp_path / "content_root"
    content_root.mkdir()
    _seed_content_root(content_root)

    ctx = _ctx(
        content_root,
        stream_overrides={
            "effectiveness": StreamSlot(
                stream="effectiveness", force_empty=True
            ),
        },
    )

    tmp_temporal = tmp_path / "temporal"
    tmp_n8n = tmp_path / "n8n"
    tmp_langgraph = tmp_path / "langgraph"

    temporal_path = Path(
        asyncio.run(
            emit_bundle_manifest_activity(ctx, str(tmp_temporal))
        )
    )
    n8n_result = emit_bundle_manifest_n8n(
        _payload_from_ctx(ctx), tmp_n8n
    )
    langgraph_update = emit_bundle_manifest_node(
        {
            "bundle_context": ctx,
            "evidence_output_dir": str(tmp_langgraph),
        }
    )

    on_disk = json.loads(temporal_path.read_bytes())
    eff = next(s for s in on_disk["streams"] if s["stream"] == "effectiveness")
    assert eff["present"] is False
    assert eff["artifact_paths"] == []

    # And it stays byte-identical across all three.
    assert (
        temporal_path.read_bytes()
        == Path(n8n_result["manifest_path"]).read_bytes()
        == Path(langgraph_update["bundle_manifest_path"]).read_bytes()
    )
