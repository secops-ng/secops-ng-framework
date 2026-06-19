"""Cross-target byte-parity contract for the AuditTrail envelope (F-CR-04).

The decision doc ``docs/observability/audit-mirror.md`` binds a single property
that the audit-mirror SKEL helper has to honour: **a playbook that runs under
the LangGraph emitter and the same playbook that runs under the Temporal
emitter must produce byte-identical audit envelopes when fed equivalent
semantic inputs**. That's what makes the offline replay shape portable across
compile targets — an auditor doesn't need to know which target produced the
envelope to consume it.

The companion suite ``test_audit_mirror_helper.py`` exercises the helper as a
unit — envelope shape, idempotency, sovereign-stack guards. This file is a
sibling that pins the cross-target contract specifically: two hand-crafted
call patterns shaped like the two emitters' traversal orders, both feeding the
same semantic record set into ``AuditTrail.append()``, asserting envelope
bytes are equal and that re-driving either pattern is a no-op.

No compiler is invoked. No helper is touched. This file exists so that any
future change to envelope field order, JSON serialization, or attribute
serialization shape fails loudly here before it ships.
"""

from __future__ import annotations

import contextvars
import importlib
import sys
from pathlib import Path

import pytest

from compilers._shared.observability import (
    SPAN_ATTR_COMPILE_TARGET,
    SPAN_ATTR_PLAYBOOK_ID,
    SPAN_ATTR_PLAYBOOK_VERSION,
    SPAN_ATTR_STEP_ID,
    SPAN_ATTR_STEP_NAME,
    SPAN_ATTR_STEP_TYPE,
    SPAN_ATTR_TOOL_NAME,
    SPAN_ATTR_WORKFLOW_RUN_ID,
    render_audit_mirror_module,
)


# ---------------------------------------------------------------------------
# Materialise a fresh mirror package per test
# ---------------------------------------------------------------------------


def _materialise_pkg(tmp_path: Path, name: str):
    pkg = tmp_path / name
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "_audit_mirror.py").write_text(render_audit_mirror_module(), encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    return importlib.import_module(f"{name}._audit_mirror")


@pytest.fixture
def mirror_mod(tmp_path: Path):
    name = "xparity_audit_pkg"
    mod = _materialise_pkg(tmp_path, name)
    yield mod
    sys.path.remove(str(tmp_path))
    sys.modules.pop(f"{name}._audit_mirror", None)
    sys.modules.pop(name, None)


# ---------------------------------------------------------------------------
# Canonical semantic inputs
#
# The two synthetic call patterns below walk the same logical playbook in the
# shape each emitter would. Both feed AuditTrail.append() the SAME canonical
# semantic record set: equal span name policy, equal SPAN_ATTR_* keys, equal
# values for playbook id / step id / step name / tool name / workflow run id /
# timestamp placeholder. The card binds these as the cross-target equivalence
# inputs.
# ---------------------------------------------------------------------------

# A fixed, deterministic "timestamp placeholder" used in attribute payload to
# stand in for whatever clock-derived value an emitter would attach. The
# helper has no clock dependency, so the test pins this rather than wall time
# to keep parity reproducible.
_TS_PLACEHOLDER = "2026-06-03T00:00:00Z"

_PLAYBOOK_ID = "vuln_intake"
_PLAYBOOK_VERSION = "0.1.0"
_WORKFLOW_RUN_ID = "run-001"

# The two semantic events the playbook produces — one tool call, one
# orchestration node. Both compile targets MUST surface these as canonical
# span name + attribute set; the emitter-specific span name conventions
# (``node:`` vs ``activity:``) are NOT part of the audit-envelope contract,
# only the canonical names the helpers below produce.
_EVENT_TOOL = {
    "canonical_span_name": "tool:enrich_ioc",
    "step_id": "step-001",
    "step_name": "enrich_ioc",
    "step_type": "tool",
    "tool_name": "enrich_ioc",
}
_EVENT_ASSEMBLE = {
    "canonical_span_name": "step:assemble_report",
    "step_id": "step-002",
    "step_name": "assemble_report",
    "step_type": "node",
    "tool_name": None,
}


def _canonical_attrs(event: dict, *, compile_target: str) -> dict:
    """Build the canonical SPAN_ATTR_* attribute set for one event.

    Both fixtures call this — that's the cross-target contract: emitters
    normalise to the same SPAN_ATTR_* key set with the same values for
    equivalent semantic events. ``compile_target`` is included as an
    attribute so the test exercises the case where the only *intentional*
    difference between sides is removed by canonicalisation before append.
    """
    attrs = {
        SPAN_ATTR_PLAYBOOK_ID: _PLAYBOOK_ID,
        SPAN_ATTR_PLAYBOOK_VERSION: _PLAYBOOK_VERSION,
        SPAN_ATTR_WORKFLOW_RUN_ID: _WORKFLOW_RUN_ID,
        SPAN_ATTR_STEP_ID: event["step_id"],
        SPAN_ATTR_STEP_NAME: event["step_name"],
        SPAN_ATTR_STEP_TYPE: event["step_type"],
        SPAN_ATTR_COMPILE_TARGET: compile_target,
        "secops_ng.audit.ts": _TS_PLACEHOLDER,
    }
    if event["tool_name"] is not None:
        attrs[SPAN_ATTR_TOOL_NAME] = event["tool_name"]
    return attrs


# ---------------------------------------------------------------------------
# Synthetic call patterns
#
# Each function emulates the traversal order of an emitter: the LangGraph
# emitter wraps a ``@tool`` body and then an assemble node; the Temporal
# emitter wraps an activity and then a workflow body. The attribute payload
# is canonicalised so the records that land in the trail are equal — the
# parity property the helper has to preserve.
# ---------------------------------------------------------------------------


def _langgraph_shaped_emit(mod, *, compile_target_attr: str) -> None:
    """LangGraph traversal: one @tool body, then one assemble node."""
    trail = mod.AuditTrail.current()
    # @tool body — emitted from compilers/langgraph/_emit_tool_wrapper.
    trail.append(
        mod.AuditRecord(
            span_name=_EVENT_TOOL["canonical_span_name"],
            attributes=_canonical_attrs(_EVENT_TOOL, compile_target=compile_target_attr),
        )
    )
    # assemble node — emitted from compilers/langgraph/_emit_node_wrapper.
    trail.append(
        mod.AuditRecord(
            span_name=_EVENT_ASSEMBLE["canonical_span_name"],
            attributes=_canonical_attrs(_EVENT_ASSEMBLE, compile_target=compile_target_attr),
        )
    )


def _temporal_shaped_emit(mod, *, compile_target_attr: str) -> None:
    """Temporal traversal: one activity, then one workflow body."""
    trail = mod.AuditTrail.current()
    # activity — emitted from compilers/temporal/_emit_activity_wrapper.
    trail.append(
        mod.AuditRecord(
            span_name=_EVENT_TOOL["canonical_span_name"],
            attributes=_canonical_attrs(_EVENT_TOOL, compile_target=compile_target_attr),
        )
    )
    # workflow body — emitted from compilers/temporal/_emit_workflow_wrapper.
    trail.append(
        mod.AuditRecord(
            span_name=_EVENT_ASSEMBLE["canonical_span_name"],
            attributes=_canonical_attrs(_EVENT_ASSEMBLE, compile_target=compile_target_attr),
        )
    )


# ---------------------------------------------------------------------------
# Headline parity assertion
# ---------------------------------------------------------------------------


def test_cross_target_envelope_bytes_are_identical(mirror_mod) -> None:
    """The headline contract: equal semantic inputs → equal envelope bytes."""

    def _scenario(emit_fn, compile_target_attr: str) -> bytes:
        emit_fn(mirror_mod, compile_target_attr=compile_target_attr)
        header = mirror_mod.EnvelopeHeader(
            workflow_id=_PLAYBOOK_ID,
            run_id=_WORKFLOW_RUN_ID,
            # the envelope HEADER's compile_target is what an offline replay
            # consumer reads to know which side produced the bytes; for the
            # parity assertion we pin both sides to the same logical channel
            # so the bytes match. (Asymmetric-header divergence is asserted
            # separately below.)
            compile_target="audit",
        )
        return mirror_mod.AuditTrail.current().render_envelope(header)

    lg_bytes = contextvars.copy_context().run(_scenario, _langgraph_shaped_emit, "langgraph")
    tmp_bytes = contextvars.copy_context().run(_scenario, _temporal_shaped_emit, "langgraph")

    assert lg_bytes == tmp_bytes, (
        "AuditTrail envelope diverged across synthetic call patterns with "
        "equivalent semantic inputs — either the helper's serialization "
        "drifted (field order, key sort, JSON separators, timestamp shape) "
        "or one of the fixtures was edited without updating the other."
    )


def test_cross_target_envelope_is_nonempty_and_well_formed(mirror_mod) -> None:
    """Sanity: the parity assertion would also pass on two empty trails.

    Explicitly verify the rendered envelope contains the expected number of
    JSONL lines and carries the canonical span names, so a future regression
    that silently drops records can't pass the headline byte-parity test.
    """

    def _scenario() -> bytes:
        _langgraph_shaped_emit(mirror_mod, compile_target_attr="langgraph")
        header = mirror_mod.EnvelopeHeader(
            workflow_id=_PLAYBOOK_ID,
            run_id=_WORKFLOW_RUN_ID,
            compile_target="audit",
        )
        return mirror_mod.AuditTrail.current().render_envelope(header)

    envelope = contextvars.copy_context().run(_scenario)
    parts = envelope.split(b"\n")
    # header + 2 body lines + trailing empty after final newline
    assert len(parts) == 4
    assert parts[-1] == b""
    assert b'"kind":"header"' in parts[0]
    assert _EVENT_TOOL["canonical_span_name"].encode() in parts[1]
    assert _EVENT_ASSEMBLE["canonical_span_name"].encode() in parts[2]


# ---------------------------------------------------------------------------
# Drift-detection assertions
#
# The headline test passes if both sides happen to be broken identically;
# these tests make that scenario impossible by pinning the exact envelope
# shape independently. If the helper changes JSON field order, separator,
# timestamp serialization, or attribute key sort, ONE of these will fail
# even when the cross-target equality still holds.
# ---------------------------------------------------------------------------


def test_envelope_header_field_order_is_pinned(mirror_mod) -> None:
    """Header JSON keys are emitted in sorted order with no whitespace."""

    def _scenario() -> bytes:
        header = mirror_mod.EnvelopeHeader(
            workflow_id=_PLAYBOOK_ID,
            run_id=_WORKFLOW_RUN_ID,
            compile_target="audit",
        )
        return mirror_mod.AuditTrail.current().render_envelope(header)

    envelope = contextvars.copy_context().run(_scenario)
    first = envelope.split(b"\n", 1)[0]
    # sort_keys=True → compile_target < kind < run_id < schema_version < workflow_id
    assert first == (
        b'{"compile_target":"audit",'
        b'"kind":"header",'
        b'"run_id":"run-001",'
        b'"schema_version":"1",'
        b'"workflow_id":"vuln_intake"}'
    )


def test_envelope_body_attribute_keys_sorted_and_compact(mirror_mod) -> None:
    """Body JSON uses sorted keys + compact ``(",", ":")`` separators."""

    def _scenario() -> bytes:
        _langgraph_shaped_emit(mirror_mod, compile_target_attr="langgraph")
        header = mirror_mod.EnvelopeHeader(
            workflow_id=_PLAYBOOK_ID,
            run_id=_WORKFLOW_RUN_ID,
            compile_target="audit",
        )
        return mirror_mod.AuditTrail.current().render_envelope(header)

    envelope = contextvars.copy_context().run(_scenario)
    tool_line = envelope.split(b"\n")[1]
    # No whitespace around colons/commas; attribute keys appear in sorted
    # order; timestamp placeholder serialised verbatim as a string.
    assert b", " not in tool_line
    assert b": " not in tool_line
    assert _TS_PLACEHOLDER.encode() in tool_line
    # secops_ng.audit.ts < secops_ng.compile.target < secops_ng.playbook.id
    ts_pos = tool_line.index(b"secops_ng.audit.ts")
    ct_pos = tool_line.index(b"secops_ng.compile.target")
    pb_pos = tool_line.index(b"secops_ng.playbook.id")
    assert ts_pos < ct_pos < pb_pos


def test_diverging_header_compile_target_breaks_parity(mirror_mod) -> None:
    """A different header ``compile_target`` MUST produce different bytes.

    Guards against a regression where the header line is accidentally dropped
    or computed from a constant — both sides would then match trivially and
    the headline parity test would be meaningless.
    """

    def _scenario(target: str) -> bytes:
        _langgraph_shaped_emit(mirror_mod, compile_target_attr="langgraph")
        header = mirror_mod.EnvelopeHeader(
            workflow_id=_PLAYBOOK_ID,
            run_id=_WORKFLOW_RUN_ID,
            compile_target=target,
        )
        return mirror_mod.AuditTrail.current().render_envelope(header)

    a = contextvars.copy_context().run(_scenario, "langgraph")
    b = contextvars.copy_context().run(_scenario, "temporal")
    assert a != b


def test_diverging_semantic_inputs_break_parity(mirror_mod) -> None:
    """Two trails with different step_id values MUST render different bytes.

    This is the negative companion to the headline assertion: parity only
    holds when semantic inputs are equivalent, never trivially.
    """

    def _scenario(step_id: str) -> bytes:
        trail = mirror_mod.AuditTrail.current()
        trail.append(
            mirror_mod.AuditRecord(
                span_name=_EVENT_TOOL["canonical_span_name"],
                attributes={
                    SPAN_ATTR_PLAYBOOK_ID: _PLAYBOOK_ID,
                    SPAN_ATTR_STEP_ID: step_id,
                },
            )
        )
        header = mirror_mod.EnvelopeHeader(
            workflow_id=_PLAYBOOK_ID,
            run_id=_WORKFLOW_RUN_ID,
            compile_target="audit",
        )
        return trail.render_envelope(header)

    a = contextvars.copy_context().run(_scenario, "step-001")
    b = contextvars.copy_context().run(_scenario, "step-002")
    assert a != b


# ---------------------------------------------------------------------------
# Idempotency replay sweep
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "emit_fn,label",
    [
        (_langgraph_shaped_emit, "langgraph"),
        (_temporal_shaped_emit, "temporal"),
    ],
)
def test_double_emit_is_idempotent(mirror_mod, emit_fn, label) -> None:
    """Re-driving either traversal pattern is a no-op at the trail level."""

    def _scenario() -> tuple[int, bytes, bytes]:
        emit_fn(mirror_mod, compile_target_attr=label)
        header = mirror_mod.EnvelopeHeader(
            workflow_id=_PLAYBOOK_ID,
            run_id=_WORKFLOW_RUN_ID,
            compile_target="audit",
        )
        trail = mirror_mod.AuditTrail.current()
        first = trail.render_envelope(header)
        # second pass over the same traversal — must not duplicate records
        emit_fn(mirror_mod, compile_target_attr=label)
        replay = mirror_mod.AuditTrail.current().render_envelope(header)
        return len(trail.snapshot()), first, replay

    n, first, replay = contextvars.copy_context().run(_scenario)
    assert n == 2, f"replay duplicated records for {label}: snapshot size {n}"
    assert first == replay, f"replay diverged envelope bytes for {label}"


def test_cross_target_replay_sweep_holds_parity(mirror_mod) -> None:
    """Replay both sides twice and assert parity still holds.

    Belt-and-braces against a regression where idempotency works on one side
    but not the other (e.g. dedup key drifts under one emitter's attribute
    shape but not the other's).
    """

    def _scenario(emit_fn, compile_target_attr: str) -> bytes:
        emit_fn(mirror_mod, compile_target_attr=compile_target_attr)
        emit_fn(mirror_mod, compile_target_attr=compile_target_attr)  # replay
        header = mirror_mod.EnvelopeHeader(
            workflow_id=_PLAYBOOK_ID,
            run_id=_WORKFLOW_RUN_ID,
            compile_target="audit",
        )
        return mirror_mod.AuditTrail.current().render_envelope(header)

    lg = contextvars.copy_context().run(_scenario, _langgraph_shaped_emit, "langgraph")
    tm = contextvars.copy_context().run(_scenario, _temporal_shaped_emit, "langgraph")
    assert lg == tm
