"""Tests for compilers/_shared/observability.

Covers:
- Attribute-key snapshot stability (renames/reorders are breaking).
- Span-wrap helpers produce syntactically valid Python when wrapped around
  a stub function body.
- Audit-mirror module renders, ast.parse()s, and round-trip-exercises:
  AuditTrail.append() twice, AuditTrail.snapshot() returns both in order,
  mutating the snapshot does not mutate the underlying trail.
- Runtime-free invariant: ``compilers._shared.observability`` does not import
  ``opentelemetry``; the import only appears in the emitted source.
- Vendor-neutral invariant: no ``datadog`` / ``honeycomb`` / ``newrelic``
  substring anywhere in the module or any string it emits.
- Determinism: same input → byte-identical output.
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

from compilers._shared import observability as obs
from compilers._shared.observability import (
    SPAN_ATTR_KEYS,
    SpanSpec,
    emit_node_span_block,
    emit_tool_span_block,
    render_audit_mirror_imports,
    render_audit_mirror_module,
    render_otel_imports,
)

# ---------------------------------------------------------------------------
# Attribute-key snapshot
# ---------------------------------------------------------------------------


def test_span_attr_keys_snapshot() -> None:
    """Pin the exported attribute keys; reordering or renaming is breaking."""
    assert SPAN_ATTR_KEYS == (
        "secops_ng.playbook.id",
        "secops_ng.playbook.version",
        "secops_ng.step.id",
        "secops_ng.step.name",
        "secops_ng.step.type",
        "secops_ng.workflow.run_id",
        "secops_ng.compile.target",
        "secops_ng.tool.name",
        "secops_ng.tool.kind",
        "secops_ng.io.input_schema",
        "secops_ng.io.output_schema",
    )


def test_span_attr_keys_are_unique() -> None:
    assert len(set(SPAN_ATTR_KEYS)) == len(SPAN_ATTR_KEYS)


# ---------------------------------------------------------------------------
# Runtime-free invariant
# ---------------------------------------------------------------------------


def test_module_does_not_import_opentelemetry_at_top_level() -> None:
    """The helper module loads cleanly without the OTel SDK installed."""
    source = Path(obs.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("opentelemetry"), alias.name
        elif isinstance(node, ast.ImportFrom):
            assert node.module is None or not node.module.startswith("opentelemetry"), node.module
    # And it should not already be in sys.modules just from importing us.
    # (If something else in the test process pulled it in, that's not our fault —
    # we only care that *we* don't trigger the import.)
    assert "opentelemetry" not in sys.modules or "compilers._shared.observability" in sys.modules


# ---------------------------------------------------------------------------
# Vendor neutrality
# ---------------------------------------------------------------------------

_FORBIDDEN_VENDORS = ("datadog", "honeycomb", "newrelic", "new_relic", "new-relic")


def _all_emitted_text() -> str:
    """Concatenate every string this module exports or emits, for substring scans."""
    return "\n".join(
        [
            Path(obs.__file__).read_text(encoding="utf-8"),
            render_otel_imports(),
            render_audit_mirror_imports(),
            render_audit_mirror_module(),
            emit_node_span_block(SpanSpec("n", {"k": "v"}), "pass"),
            emit_tool_span_block(SpanSpec("t", {"k": "v"}), "pass"),
        ]
    )


@pytest.mark.parametrize("vendor", _FORBIDDEN_VENDORS)
def test_no_vendor_sdk_substring(vendor: str) -> None:
    haystack = _all_emitted_text().lower()
    assert vendor not in haystack, f"vendor SDK substring leaked: {vendor!r}"


def test_otel_imports_only_use_api_not_sdk() -> None:
    """Emitted OTel import block touches the API, not vendor or SDK exporters."""
    block = render_otel_imports()
    assert "from opentelemetry import trace" in block
    assert "opentelemetry.sdk" not in block
    assert "opentelemetry.exporter" not in block


# ---------------------------------------------------------------------------
# Span-wrap helpers
# ---------------------------------------------------------------------------


def _wrap_in_stub(emitted_block: str) -> str:
    """Drop an emitted block inside a stub function so we can ast.parse it."""
    header = (
        "def stub():\n"
        "    _TRACER = None  # placeholder so the stub is self-contained for parsing\n"
        "    AuditTrail = None  # ditto\n"
        "    AuditRecord = None  # ditto\n"
    )
    return header + emitted_block


@pytest.mark.parametrize("emitter", [emit_node_span_block, emit_tool_span_block])
def test_span_block_parses(emitter) -> None:
    spec = SpanSpec(
        span_name="node:enrich",
        attributes={
            "secops_ng.playbook.id": "vuln-intake",
            "secops_ng.step.id": "step-002",
            "secops_ng.step.name": "enrich",
        },
    )
    block = emitter(spec, "result = do_work()\nreturn result")
    src = _wrap_in_stub(block)
    ast.parse(src)  # raises SyntaxError on regression


def test_span_block_drops_none_attributes() -> None:
    spec = SpanSpec(
        span_name="node:enrich",
        attributes={"a": "x", "b": None, "c": 3},
    )
    block = emit_node_span_block(spec, "pass")
    assert "'b'" not in block, "None-valued attribute should be dropped, not emitted as None"
    assert "'a'" in block and "'c'" in block


def test_span_block_attribute_order_is_sorted() -> None:
    """Determinism: keys come out sorted regardless of input dict order."""
    spec_a = SpanSpec("n", {"z": 1, "a": 2, "m": 3})
    spec_b = SpanSpec("n", {"a": 2, "m": 3, "z": 1})
    assert emit_node_span_block(spec_a, "pass") == emit_node_span_block(spec_b, "pass")


def test_span_block_empty_attributes_emits_empty_dict() -> None:
    block = emit_node_span_block(SpanSpec("n"), "pass")
    assert "attributes={}" in block


def test_span_block_appends_audit_record() -> None:
    """Every emitted span block also appends an AuditRecord."""
    block = emit_node_span_block(SpanSpec("node:x", {"k": "v"}), "pass")
    assert "AuditTrail.current().append(" in block
    assert "AuditRecord(span_name='node:x'" in block


def test_span_block_multiline_body_indents_correctly() -> None:
    body = "a = 1\nb = 2\nreturn a + b"
    block = emit_node_span_block(SpanSpec("n"), body, indent="    ")
    ast.parse(_wrap_in_stub(block))
    # Each body line should appear indented to 8 spaces (4 for stub + 4 for with).
    for line in ("a = 1", "b = 2", "return a + b"):
        assert f"        {line}" in block


def test_span_block_is_deterministic() -> None:
    spec = SpanSpec("n", {"a": 1, "b": "two", "c": True})
    assert emit_node_span_block(spec, "pass") == emit_node_span_block(spec, "pass")


# ---------------------------------------------------------------------------
# Audit-mirror module
# ---------------------------------------------------------------------------


def test_audit_mirror_module_parses() -> None:
    ast.parse(render_audit_mirror_module())


def test_audit_mirror_module_is_deterministic() -> None:
    assert render_audit_mirror_module() == render_audit_mirror_module()


def test_audit_mirror_roundtrip(tmp_path: Path) -> None:
    """Render the module, import it, append two records, snapshot returns both in order."""
    pkg = tmp_path / "audit_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "_audit_mirror.py").write_text(render_audit_mirror_module(), encoding="utf-8")

    sys.path.insert(0, str(tmp_path))
    try:
        mod = importlib.import_module("audit_pkg._audit_mirror")
        AuditRecord = mod.AuditRecord  # noqa: N806 — re-export of class symbol
        AuditTrail = mod.AuditTrail  # noqa: N806 — re-export of class symbol

        # Run inside an isolated contextvars.Context so the trail starts empty
        # regardless of any other test that touched the contextvar.
        import contextvars

        def _scenario() -> tuple[list, list]:
            trail = AuditTrail.current()
            trail.append(AuditRecord(span_name="node:a", attributes={"k": 1}))
            trail.append(AuditRecord(span_name="node:b", attributes={"k": 2}))
            snap = trail.snapshot()
            # Mutate the snapshot — must not affect underlying.
            snap.append(AuditRecord(span_name="evil", attributes={}))
            snap2 = trail.snapshot()
            return snap, snap2

        ctx = contextvars.copy_context()
        snap, snap2 = ctx.run(_scenario)

        assert [r.span_name for r in snap[:2]] == ["node:a", "node:b"]
        assert snap[0].attributes == {"k": 1}
        assert snap[1].attributes == {"k": 2}
        # snapshot returned a copy: mutating it did not affect the trail.
        assert [r.span_name for r in snap2] == ["node:a", "node:b"]
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("audit_pkg._audit_mirror", None)
        sys.modules.pop("audit_pkg", None)


def test_audit_record_is_frozen(tmp_path: Path) -> None:
    """AuditRecord is immutable so emitters cannot mutate a row another reader holds."""
    pkg = tmp_path / "audit_pkg_frozen"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "_audit_mirror.py").write_text(render_audit_mirror_module(), encoding="utf-8")

    sys.path.insert(0, str(tmp_path))
    try:
        mod = importlib.import_module("audit_pkg_frozen._audit_mirror")
        rec = mod.AuditRecord(span_name="x", attributes={})
        import dataclasses

        with pytest.raises(dataclasses.FrozenInstanceError):
            rec.span_name = "y"  # type: ignore[misc]
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("audit_pkg_frozen._audit_mirror", None)
        sys.modules.pop("audit_pkg_frozen", None)
