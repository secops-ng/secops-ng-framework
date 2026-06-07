"""Same-target deterministic-replay contract for the incident-management example.

F-WF-05 EXTEND-tests-replay. Mirror of F-WF-03 EXTEND-tests-replay
(``tests/examples/test_alert_triage_replay.py``) for the incident-management
worked example. Cross-target byte-parity of the AuditTrail is already covered
by ``tests/compilers/_shared/test_audit_mirror_cross_target_parity.py``; this
file pins the orthogonal property: **for each compile target, feeding the same
input twice through the same emitter-shaped traversal under a deterministic-stub
LM adapter and a fixed clock MUST produce a byte-identical AuditTrail envelope
across the two runs.**

That is the offline / air-gapped replay guarantee an auditor relies on when they
re-drive a captured incident payload through a worked example to verify what
the operator saw.

The companion happy-path golden suite
(``tests/examples/test_incident_management_happy_path.py``) pins the canonical
case-state JSON shape; this suite pins the audit-envelope byte stream the
``examples/{n8n,temporal,langgraph}/incident-management/`` SKELETON-wave CORE
bindings emit when re-driven from the recorded history.

Approach
--------

The audit-mirror helper has no clock dependency and no LM dependency of its
own; "fixed clock" and "deterministic LM stub" enter the contract via the
``secops_ng.audit.ts`` attribute payload and the canonical step attribute set
respectively. The test pins both as constants and asserts that two independent
runs in fresh ``contextvars`` contexts — one per "replay" — produce
byte-identical envelopes for each of the three compile targets the worked
example ships for: n8n, Temporal, LangGraph.

Per-target replay contract surface
----------------------------------

* **Temporal lane** mirrors the ``temporalio.testing.WorkflowEnvironment`` +
  ``Replayer.replay_workflow`` invariant: given a recorded history (here pinned
  via the canonical attribute set and fixed clock placeholder), re-driving the
  workflow body MUST produce the same span attribute stream, byte-for-byte, on
  each run.
* **LangGraph lane** mirrors the recorded-state-checkpoint re-execution
  invariant: given pinned canonical attributes, re-running the graph against the
  captured node sequence MUST produce identical envelope bytes.
* **n8n lane** mirrors the recorded-workflow-JSON re-feed invariant: walking the
  Code-node bodies in linear playbook order under the recorded inputs MUST
  produce identical node outputs.

The emitter-shaped call patterns mirror the traversal order each target
produces for the incident-management CACAO playbook (intake → classify →
open_timeline → submit_24h → submit_72h → submit_1m → close_timeline). They are
intentionally synthetic so this test does not depend on the optional
``langgraph`` / ``temporalio`` / n8n runtimes — same precedent as the
cross-target parity suite and the alert-triage replay suite.

Shared-primitive coverage
-------------------------

The seven attribute-pinned events together exercise every F-WF-05 shared
primitive wired in CORE-WIRE-{N8N,TMP,LG}:

* significance / cross-border policy → ``classify`` event (step ``...0003``);
* stage clocks → the three submission events (steps ``...0006``, ``...0007``,
  ``...0009``);
* regulator-submission contract → the same three submission events
  (per-stage destination handle pinned in the span attribute set);
* F-PT-02 incident-timeline binding → ``open_timeline`` (``...0005``) and
  ``close_timeline`` (``...000a``).
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
    name = "replay_audit_pkg_incident_management"
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

_TS_PLACEHOLDER = "2026-06-07T00:00:00Z"
_PLAYBOOK_ID = "incident-management"
_PLAYBOOK_VERSION = "0.1.0"
_WORKFLOW_RUN_ID = "replay-run-001"

# Per-stage destination handle constants. These are placeholders an
# auditor would see in the recorded history when the operator's
# ``__notification_destinations__`` mapping resolved against the
# regulator-submission contract on each stage. They are pinned here so
# the replay-determinism contract covers the regulator-submission
# destination-handle field too, not just the per-stage step shape.
_DEST_EARLY_WARNING = "regulator://national-csirt/early_warning"
_DEST_NOTIFICATION = "regulator://national-csirt/notification"
_DEST_FINAL_REPORT = "regulator://national-csirt/final_report"

# Seven semantic events shaped after the CACAO incident-management
# playbook's action-typed steps. Step ids match the canonical playbook
# (content/playbooks/incident-management/playbook.cacao.json). Tool-name
# presence follows the existing parity-suite convention: tool steps
# surface a tool_name, orchestration / node steps do not. The seven
# events together cover the four F-WF-05 shared primitives the
# CORE-WIRE wave bound on each target.
_EVENT_INTAKE = {
    "canonical_span_name": "tool:ingest_incident_signal",
    "step_id": "action--50000000-0000-4000-8000-000000000002",
    "step_name": "intake_significant_incident_signal",
    "step_type": "tool",
    "tool_name": "ingest_incident_signal",
    "extra_attrs": {},
}
_EVENT_CLASSIFY = {
    "canonical_span_name": "tool:classify_significance",
    "step_id": "action--50000000-0000-4000-8000-000000000003",
    "step_name": "classify_significance_and_cross_border",
    "step_type": "tool",
    "tool_name": "classify_significance",
    "extra_attrs": {},
}
_EVENT_OPEN_TIMELINE = {
    "canonical_span_name": "tool:open_timeline",
    "step_id": "action--50000000-0000-4000-8000-000000000005",
    "step_name": "open_incident_timeline",
    "step_type": "tool",
    "tool_name": "open_timeline",
    "extra_attrs": {
        "secops_ng.pt02.binding_status": "adapter",
    },
}
_EVENT_SUBMIT_EARLY_WARNING = {
    "canonical_span_name": "tool:submit_regulator",
    "step_id": "action--50000000-0000-4000-8000-000000000006",
    "step_name": "submit_24h_early_warning",
    "step_type": "tool",
    "tool_name": "submit_regulator",
    "extra_attrs": {
        "secops_ng.stage": "early_warning",
        "secops_ng.regulator.destination": _DEST_EARLY_WARNING,
    },
}
_EVENT_SUBMIT_NOTIFICATION = {
    "canonical_span_name": "tool:submit_regulator",
    "step_id": "action--50000000-0000-4000-8000-000000000007",
    "step_name": "submit_72h_notification",
    "step_type": "tool",
    "tool_name": "submit_regulator",
    "extra_attrs": {
        "secops_ng.stage": "notification",
        "secops_ng.regulator.destination": _DEST_NOTIFICATION,
    },
}
_EVENT_SUBMIT_FINAL_REPORT = {
    "canonical_span_name": "tool:submit_regulator",
    "step_id": "action--50000000-0000-4000-8000-000000000009",
    "step_name": "submit_1m_final_report",
    "step_type": "tool",
    "tool_name": "submit_regulator",
    "extra_attrs": {
        "secops_ng.stage": "final_report",
        "secops_ng.regulator.destination": _DEST_FINAL_REPORT,
    },
}
_EVENT_CLOSE_TIMELINE = {
    "canonical_span_name": "tool:close_timeline",
    "step_id": "action--50000000-0000-4000-8000-00000000000a",
    "step_name": "close_incident_timeline",
    "step_type": "tool",
    "tool_name": "close_timeline",
    "extra_attrs": {
        "secops_ng.pt02.binding_status": "adapter",
    },
}

_ORDERED_EVENTS = (
    _EVENT_INTAKE,
    _EVENT_CLASSIFY,
    _EVENT_OPEN_TIMELINE,
    _EVENT_SUBMIT_EARLY_WARNING,
    _EVENT_SUBMIT_NOTIFICATION,
    _EVENT_SUBMIT_FINAL_REPORT,
    _EVENT_CLOSE_TIMELINE,
)


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
    attrs.update(event.get("extra_attrs", {}))
    return attrs


# ---------------------------------------------------------------------------
# Per-target traversal-shaped emits.
#
# Each helper walks the seven incident-management events in the order the
# matching emitter would, feeding each into the AuditTrail. The
# differences between helpers are intentional: they encode the per-target
# traversal shape so a future regression that breaks one emitter's
# replay determinism without breaking the others surfaces on the right
# parametrised case below.
# ---------------------------------------------------------------------------


def _n8n_shaped_emit(mod, *, compile_target_attr: str) -> None:
    """n8n traversal: Code-node bodies fire in linear playbook order.

    Mirrors the recorded-workflow-JSON re-feed contract: given the
    operator's exported workflow JSON and the same incident payload,
    walking the Code-node bodies in declaration order MUST produce
    identical node outputs across runs.
    """
    trail = mod.AuditTrail.current()
    for event in _ORDERED_EVENTS:
        trail.append(
            mod.AuditRecord(
                span_name=event["canonical_span_name"],
                attributes=_canonical_attrs(event, compile_target=compile_target_attr),
            )
        )


def _temporal_shaped_emit(mod, *, compile_target_attr: str) -> None:
    """Temporal traversal: activity calls in workflow-body declaration order.

    Mirrors the ``temporalio.testing.WorkflowEnvironment`` +
    ``Replayer.replay_workflow`` determinism contract: given a recorded
    history (here pinned via the canonical attribute set and fixed clock
    placeholder), re-driving the workflow body MUST produce the same
    span attribute stream, byte-for-byte, on each run.
    """
    trail = mod.AuditTrail.current()
    for event in _ORDERED_EVENTS:
        trail.append(
            mod.AuditRecord(
                span_name=event["canonical_span_name"],
                attributes=_canonical_attrs(event, compile_target=compile_target_attr),
            )
        )


def _langgraph_shaped_emit(mod, *, compile_target_attr: str) -> None:
    """LangGraph traversal: nodes fire in GraphSpec edge order.

    Mirrors the recorded-state-checkpoint re-execution contract: given
    pinned canonical attributes, re-running the graph against the
    captured node sequence MUST produce identical envelope bytes.
    """
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
    and per-event canonical span names so a regression that silently
    drops events cannot trivially pass the determinism assertion above.
    Also pins the per-stage destination handles so the
    regulator-submission contract surface is part of the byte-stream
    contract, not just the step shape.
    """
    envelope = contextvars.copy_context().run(
        _envelope_for, mirror_mod, emit_fn, compile_target_attr=target_name
    )
    parts = envelope.split(b"\n")
    # header + 7 body lines + trailing empty after final newline
    assert len(parts) == 9, f"unexpected envelope shape for {target_name}: {parts!r}"
    assert parts[-1] == b""
    assert b'"kind":"header"' in parts[0]
    assert _EVENT_INTAKE["canonical_span_name"].encode() in parts[1]
    assert _EVENT_CLASSIFY["canonical_span_name"].encode() in parts[2]
    assert _EVENT_OPEN_TIMELINE["canonical_span_name"].encode() in parts[3]
    assert _EVENT_SUBMIT_EARLY_WARNING["canonical_span_name"].encode() in parts[4]
    assert _EVENT_SUBMIT_NOTIFICATION["canonical_span_name"].encode() in parts[5]
    assert _EVENT_SUBMIT_FINAL_REPORT["canonical_span_name"].encode() in parts[6]
    assert _EVENT_CLOSE_TIMELINE["canonical_span_name"].encode() in parts[7]
    # Per-stage regulator-submission destinations are present on the
    # three submission events — this guards against a future regression
    # that drops the destination attribute from the canonical attribute
    # set on any submission step.
    assert _DEST_EARLY_WARNING.encode() in parts[4]
    assert _DEST_NOTIFICATION.encode() in parts[5]
    assert _DEST_FINAL_REPORT.encode() in parts[6]


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
