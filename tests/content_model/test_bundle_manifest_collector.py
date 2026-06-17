"""F-WF-09 SKELETON — auditor evidence bundle manifest round-trip.

Pins (SKELETON scope — the full three-target collector fan-out (n8n +
Temporal + LangGraph) lands in the CORE-FANOUT sibling card; per-target
byte-parity goldens land in the EXTEND-tests sibling):

1. The shared collector writes a manifest that validates against
   ``schemas/evidence/bundle.schema.json``.
2. The ``bundle_id`` is deterministic on
   ``(generated_at, bundle_window_start, bundle_window_end)`` — same
   inputs reproduce the same id; a different window does not.
3. The manifest carries all seven shipped streams in canonical order.
   The ``effectiveness`` stream is present as an empty slot
   (``present: false`` and empty ``artifact_paths``) because F-CP-06 is
   still Proposed.
4. A stream directory containing JSON artifacts is indexed with
   sorted relative paths (POSIX, anchored at ``content/evidence/``).
5. The collector refuses non-canonical regulation refs and missing
   provenance fields at the Python boundary, ahead of JSON Schema
   validation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from compilers._shared.evidence import (
    STREAMS,
    BundleContext,
    StreamSlot,
    derive_bundle_id,
    emit_bundle_manifest,
    render_bundle_manifest,
)

REPO = Path(__file__).resolve().parents[2]
BUNDLE_SCHEMA = REPO / "schemas" / "evidence" / "bundle.schema.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(BUNDLE_SCHEMA))


def _ctx(content_root: Path, **overrides) -> BundleContext:
    base = dict(
        content_root=content_root,
        generated_at=datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc),
        regulation_refs=("nis2:art-20", "nis2:art-21-2-f"),
        source_url="https://example.org/runs/bundle-skeleton-001",
        bundle_window_start=datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        bundle_window_end=datetime(2026, 6, 17, 0, 0, 0, tzinfo=timezone.utc),
    )
    base.update(overrides)
    return BundleContext(**base)


def _stub_content_root(tmp_path: Path) -> Path:
    """Make an empty ``content/evidence/<stream>/`` tree under tmp."""
    root = tmp_path / "repo"
    base = root / "content" / "evidence"
    for stream in ("risk-analysis", "incidents", "supply-chain", "vulns",
                   "crypto", "access"):
        (base / stream).mkdir(parents=True, exist_ok=True)
    return root


def test_render_validates_against_schema(tmp_path: Path) -> None:
    ctx = _ctx(_stub_content_root(tmp_path))
    record = render_bundle_manifest(ctx)
    _validator().validate(record)


def test_seven_streams_in_canonical_order(tmp_path: Path) -> None:
    ctx = _ctx(_stub_content_root(tmp_path))
    record = render_bundle_manifest(ctx)
    assert [s["stream"] for s in record["streams"]] == list(STREAMS)
    assert len(record["streams"]) == 7


def test_effectiveness_slot_is_present_but_empty(tmp_path: Path) -> None:
    """F-CP-06 effectiveness is gated; the slot must still appear, empty."""
    ctx = _ctx(_stub_content_root(tmp_path))
    record = render_bundle_manifest(ctx)
    eff = next(s for s in record["streams"] if s["stream"] == "effectiveness")
    assert eff["present"] is False
    assert eff["artifact_paths"] == []
    assert eff["artifact_count"] == 0
    assert eff["feature_ref"] == "F-CP-06"
    assert "gated" in eff["notes"]


def test_artifact_paths_sorted_and_relative(tmp_path: Path) -> None:
    root = _stub_content_root(tmp_path)
    risk_dir = root / "content" / "evidence" / "risk-analysis"
    # Place two artifacts in reverse-lex order on disk to confirm the
    # collector returns them sorted.
    (risk_dir / "z-second.json").write_text("{}", encoding="utf-8")
    (risk_dir / "a-first.json").write_text("{}", encoding="utf-8")

    record = render_bundle_manifest(_ctx(root))
    risk = next(s for s in record["streams"] if s["stream"] == "risk-analysis")
    assert risk["present"] is True
    assert risk["artifact_paths"] == [
        "content/evidence/risk-analysis/a-first.json",
        "content/evidence/risk-analysis/z-second.json",
    ]
    assert risk["artifact_count"] == 2


def test_bundle_id_is_deterministic_on_window(tmp_path: Path) -> None:
    ctx = _ctx(_stub_content_root(tmp_path))
    a = derive_bundle_id(
        ctx.generated_at, ctx.bundle_window_start, ctx.bundle_window_end
    )
    b = derive_bundle_id(
        ctx.generated_at, ctx.bundle_window_start, ctx.bundle_window_end
    )
    assert a == b

    # Different upper bound -> different id.
    c = derive_bundle_id(
        ctx.generated_at,
        ctx.bundle_window_start,
        datetime(2026, 6, 18, 0, 0, 0, tzinfo=timezone.utc),
    )
    assert c != a


def test_emit_writes_atomically_to_named_file(tmp_path: Path) -> None:
    root = _stub_content_root(tmp_path)
    out_dir = tmp_path / "bundle-out"
    path = emit_bundle_manifest(_ctx(root), out_dir)
    assert path == out_dir / "bundle.manifest.json"
    on_disk = _load_json(path)
    rendered = render_bundle_manifest(_ctx(root))
    assert on_disk == rendered
    _validator().validate(on_disk)


def test_stream_override_carries_notes_and_force_empty(tmp_path: Path) -> None:
    root = _stub_content_root(tmp_path)
    # Drop a file under access/ then force the slot empty.
    (root / "content" / "evidence" / "access" / "x.json").write_text(
        "{}", encoding="utf-8"
    )
    ctx = _ctx(
        root,
        stream_overrides={
            "access": StreamSlot(
                stream="access",
                notes="forced empty for SKELETON smoke",
                force_empty=True,
            )
        },
    )
    record = render_bundle_manifest(ctx)
    access = next(s for s in record["streams"] if s["stream"] == "access")
    assert access["present"] is False
    assert access["artifact_paths"] == []
    assert access["notes"] == "forced empty for SKELETON smoke"


def test_invalid_regulation_ref_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="regulation_ref"):
        render_bundle_manifest(
            _ctx(_stub_content_root(tmp_path),
                 regulation_refs=("not-a-regime:foo",))
        )


def test_missing_source_url_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source_url"):
        render_bundle_manifest(
            _ctx(_stub_content_root(tmp_path), source_url="")
        )
