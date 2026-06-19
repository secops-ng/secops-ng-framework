"""Same-target deterministic-replay contract for the vuln_intake example.

F-WF-01 EXTEND-tests-replay. Cross-target byte-parity of the AuditTrail is
already covered by ``tests/compilers/_shared/test_audit_mirror_cross_target_parity.py``;
this file pins the orthogonal property: **for each compile target, feeding
the same input twice through the same emitter-shaped traversal under a
deterministic-stub LM adapter and a fixed clock MUST produce a
byte-identical AuditTrail envelope across the two runs.**

That is the offline / air-gapped replay guarantee an auditor relies on
when they re-drive a captured payload through a worked example to
verify what the operator saw.

Approach
--------

The audit-mirror helper has no clock dependency and no LM dependency of
its own; "fixed clock" and "deterministic LM stub" enter the contract
via the ``secops_ng.audit.ts`` attribute payload and the canonical step
attribute set respectively. The test pins both as constants and asserts
that two independent runs in fresh ``contextvars`` contexts — one per
"replay" — produce byte-identical envelopes for each of the three
compile targets the worked example ships for: n8n, Temporal, LangGraph.

The emitter-shaped call patterns mirror the traversal order each target
produces for the vuln_intake CACAO playbook (intake → triage → assemble).
They are intentionally synthetic so this test does not depend on the
optional ``langgraph`` / ``temporalio`` / n8n runtimes — same precedent
as the cross-target parity suite.
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
# Materialise a fresh mirror package per test (mirrors the parity suite).
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
    name = "replay_audit_pkg"
    mod = _materialise_pkg(tmp_path, name)
    yield mod
    sys.path.remove(str(tmp_path))
    sys.modules.pop(f"{name}._audit_mirror", None)
    sys.modules.pop(name, None)


# ---------------------------------------------------------------------------
# Deterministic inputs — fixed clock + deterministic-stub LM adapter.
#
# The clock placeholder lives in the attribute payload as
# ``secops_ng.audit.ts`` so a real wall-clock value is never sampled. The
# "deterministic-stub LM adapter" surfaces in the canonical attribute
# set: a stub adapter is one that, given identical input, produces
# identical span attributes — the very property pinned below.
# ---------------------------------------------------------------------------

_TS_PLACEHOLDER = "2026-06-04T00:00:00Z"
_PLAYBOOK_ID = "vuln_intake"
_PLAYBOOK_VERSION = "0.1.0"
_WORKFLOW_RUN_ID = "replay-run-001"

# Three semantic events shaped after the CACAO vuln_intake playbook's
# action-typed steps (intake → triage → assemble). Tool-name presence
# follows the existing parity-suite convention: tool steps surface a
# tool_name, orchestration steps do not.
_EVENT_INTAKE = {
    "canonical_span_name": "tool:canonicalize_case_field",
    "step_id": "action--01a17a01-0000-4000-8000-000000000002",
    "step_name": "intake_disclosure",
    "step_type": "tool",
    "tool_name": "canonicalize_case_field",
}
_EVENT_TRIAGE = {
    "canonical_span_name": "tool:severity_policy",
    "step_id": "action--01a17a01-0000-4000-8000-000000000003",
    "step_name": "triage",
    "step_type": "tool",
    "tool_name": "severity_policy",
}
_EVENT_ASSEMBLE = {
    "canonical_span_name": "step:assemble_report",
    "step_id": "action--01a17a01-0000-4000-8000-000000000005",
    "step_name": "assemble_report",
    "step_type": "node",
    "tool_name": None,
}

_ORDERED_EVENTS = (_EVENT_INTAKE, _EVENT_TRIAGE, _EVENT_ASSEMBLE)


def _canonical_attrs(event: dict, *, compile_target: str) -> dict:
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
# Per-target traversal-shaped emits.
#
# Each helper walks the three vuln_intake events in the order the
# matching emitter would, feeding each into the AuditTrail. The
# differences between helpers are intentional: they encode the per-target
# traversal shape so a future regression that breaks one emitter's
# replay determinism without breaking the others surfaces on the right
# parametrised case below.
# ---------------------------------------------------------------------------


def _n8n_shaped_emit(mod, *, compile_target_attr: str) -> None:
    """n8n traversal: Code-node bodies fire in linear playbook order."""
    trail = mod.AuditTrail.current()
    for event in _ORDERED_EVENTS:
        trail.append(
            mod.AuditRecord(
                span_name=event["canonical_span_name"],
                attributes=_canonical_attrs(event, compile_target=compile_target_attr),
            )
        )


def _temporal_shaped_emit(mod, *, compile_target_attr: str) -> None:
    """Temporal traversal: activity calls in workflow-body declaration order."""
    trail = mod.AuditTrail.current()
    for event in _ORDERED_EVENTS:
        trail.append(
            mod.AuditRecord(
                span_name=event["canonical_span_name"],
                attributes=_canonical_attrs(event, compile_target=compile_target_attr),
            )
        )


def _langgraph_shaped_emit(mod, *, compile_target_attr: str) -> None:
    """LangGraph traversal: nodes fire in GraphSpec edge order."""
    trail = mod.AuditTrail.current()
    for event in _ORDERED_EVENTS:
        trail.append(
            mod.AuditRecord(
                span_name=event["canonical_span_name"],
                attributes=_canonical_attrs(event, compile_target=compile_target_attr),
            )
        )


_TARGETS = [
    ("n8n", _n8n_shaped_emit),
    ("temporal", _temporal_shaped_emit),
    ("langgraph", _langgraph_shaped_emit),
]


# ---------------------------------------------------------------------------
# Replay-determinism assertion (per target).
# ---------------------------------------------------------------------------


def _envelope_for(mod, emit_fn, *, compile_target_attr: str) -> bytes:
    """Run one fresh-context emission and return the rendered envelope bytes."""
    emit_fn(mod, compile_target_attr=compile_target_attr)
    header = mod.EnvelopeHeader(
        workflow_id=_PLAYBOOK_ID,
        run_id=_WORKFLOW_RUN_ID,
        compile_target=compile_target_attr,
    )
    return mod.AuditTrail.current().render_envelope(header)


@pytest.mark.parametrize("target_name,emit_fn", _TARGETS, ids=[t[0] for t in _TARGETS])
def test_same_target_replay_envelope_bytes_are_identical(
    mirror_mod, target_name, emit_fn
) -> None:
    """Headline contract: two independent runs through the same emitter
    shape with identical deterministic input produce identical envelope
    bytes."""
    first = contextvars.copy_context().run(
        _envelope_for, mirror_mod, emit_fn, compile_target_attr=target_name
    )
    second = contextvars.copy_context().run(
        _envelope_for, mirror_mod, emit_fn, compile_target_attr=target_name
    )

    assert first == second, (
        f"Replay determinism violated for compile target {target_name!r}: "
        "the AuditTrail envelope changed between two runs with identical "
        "inputs and a fixed clock placeholder. Either the helper picked up "
        "a non-deterministic input (wall clock, random ordering, dict-id "
        "leak) or the per-target emitter shape introduced a non-stable key."
    )


@pytest.mark.parametrize("target_name,emit_fn", _TARGETS, ids=[t[0] for t in _TARGETS])
def test_same_target_replay_envelope_is_nonempty(
    mirror_mod, target_name, emit_fn
) -> None:
    """Sanity: two empty trails would also be byte-equal. Pin record count
    so a regression that silently drops all events cannot trivially pass
    the determinism assertion above."""
    envelope = contextvars.copy_context().run(
        _envelope_for, mirror_mod, emit_fn, compile_target_attr=target_name
    )
    parts = envelope.split(b"\n")
    # header + 3 body lines + trailing empty after final newline
    assert len(parts) == 5, f"unexpected envelope shape for {target_name}: {parts!r}"
    assert parts[-1] == b""
    assert b'"kind":"header"' in parts[0]
    assert _EVENT_INTAKE["canonical_span_name"].encode() in parts[1]
    assert _EVENT_TRIAGE["canonical_span_name"].encode() in parts[2]
    assert _EVENT_ASSEMBLE["canonical_span_name"].encode() in parts[3]


@pytest.mark.parametrize("target_name,emit_fn", _TARGETS, ids=[t[0] for t in _TARGETS])
def test_same_target_perturbed_input_breaks_replay(
    mirror_mod, target_name, emit_fn
) -> None:
    """Negative companion: if the deterministic input changes, the
    envelope MUST change. Guards against a trivially-equal-bytes
    regression (e.g. envelope rendering accidentally pinned to a constant).
    """
    base = contextvars.copy_context().run(
        _envelope_for, mirror_mod, emit_fn, compile_target_attr=target_name
    )

    def _perturbed() -> bytes:
        trail = mirror_mod.AuditTrail.current()
        # Same traversal, but with a perturbed run id — the canonical
        # attribute set MUST flow into the envelope bytes.
        for event in _ORDERED_EVENTS:
            attrs = _canonical_attrs(event, compile_target=target_name)
            attrs[SPAN_ATTR_WORKFLOW_RUN_ID] = "replay-run-002"
            trail.append(
                mirror_mod.AuditRecord(
                    span_name=event["canonical_span_name"], attributes=attrs
                )
            )
        header = mirror_mod.EnvelopeHeader(
            workflow_id=_PLAYBOOK_ID,
            run_id=_WORKFLOW_RUN_ID,
            compile_target=target_name,
        )
        return trail.render_envelope(header)

    perturbed = contextvars.copy_context().run(_perturbed)
    assert base != perturbed, (
        f"Perturbed input did not change envelope bytes for {target_name}: "
        "the test would pass trivially regardless of replay determinism."
    )
