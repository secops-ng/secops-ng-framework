"""Tests for compilers/temporal/emit — bindings + signal-hook integration.

Companion to test_emit.py. These tests target the second-pass features
(typed activity signatures, retry-policy constants, HITL signal/query
handlers) against the incident-escalation HITL fixture.
"""
from __future__ import annotations

import ast as _ast
import importlib.util
import json
import sys
import types
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse
from compilers.temporal.emit import emit as emit_str

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "incident_escalation_hitl.cacao.json"
)


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture()
def playbook(fixture_data):
    return parse(deepcopy(fixture_data))


def _temporalio_stub() -> types.ModuleType:
    """Stub package mirroring the surface the generated module imports."""

    def passthrough(fn):
        return fn

    activity = types.SimpleNamespace(defn=passthrough)
    workflow = types.SimpleNamespace(
        defn=passthrough,
        run=passthrough,
        signal=passthrough,
        query=passthrough,
    )

    class RetryPolicy:
        def __init__(
            self,
            initial_interval=None,
            maximum_interval=None,
            backoff_coefficient=None,
            maximum_attempts=None,
        ):
            self.initial_interval = initial_interval
            self.maximum_interval = maximum_interval
            self.backoff_coefficient = backoff_coefficient
            self.maximum_attempts = maximum_attempts

    common = types.SimpleNamespace(RetryPolicy=RetryPolicy)
    pkg = types.ModuleType("temporalio")
    pkg.activity = activity  # type: ignore[attr-defined]
    pkg.workflow = workflow  # type: ignore[attr-defined]
    pkg.common = common  # type: ignore[attr-defined]
    return pkg


def _opentelemetry_stub() -> types.ModuleType:
    """No-op ``opentelemetry`` stub for emitted-source import tests.

    The F-CR-04 CORE-B1 emitter wraps activity bodies in
    ``_TRACER.start_as_current_span(...)``. The test environment doesn't ship
    the real OTel SDK, so we expose a tracer whose span context manager
    accepts the emitter's keyword args (``name=``, ``attributes=``).
    """

    class _NoopSpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _NoopTracer:
        def start_as_current_span(self, *args, **kwargs):
            return _NoopSpan()

    trace_mod = types.SimpleNamespace(get_tracer=lambda *_a, **_kw: _NoopTracer())
    pkg = types.ModuleType("opentelemetry")
    pkg.trace = trace_mod  # type: ignore[attr-defined]
    return pkg


def _audit_mirror_stub(parent_pkg_name: str) -> types.ModuleType:
    """Stub the sibling ``_audit_mirror`` module the emitted code imports."""

    class AuditRecord:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class _Trail:
        def append(self, _record):
            return None

    class AuditTrail:
        @classmethod
        def current(cls):
            return _Trail()

    mod = types.ModuleType(f"{parent_pkg_name}._audit_mirror")
    mod.AuditRecord = AuditRecord  # type: ignore[attr-defined]
    mod.AuditTrail = AuditTrail  # type: ignore[attr-defined]
    return mod


def _load_module(source: str, name: str = "_temporal_hitl_under_test") -> types.ModuleType:
    pkg = _temporalio_stub()
    sys.modules["temporalio"] = pkg
    sys.modules["temporalio.activity"] = pkg.activity  # type: ignore[assignment]
    sys.modules["temporalio.workflow"] = pkg.workflow  # type: ignore[assignment]
    sys.modules["temporalio.common"] = pkg.common  # type: ignore[assignment]
    otel = _opentelemetry_stub()
    sys.modules["opentelemetry"] = otel
    sys.modules["opentelemetry.trace"] = otel.trace  # type: ignore[assignment]
    parent_name = f"{name}_pkg"
    parent = types.ModuleType(parent_name)
    parent.__path__ = []  # type: ignore[attr-defined]
    sys.modules[parent_name] = parent
    sys.modules[f"{parent_name}._audit_mirror"] = _audit_mirror_stub(parent_name)
    full_name = f"{parent_name}.{name}"
    spec = importlib.util.spec_from_loader(full_name, loader=None)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    module.__package__ = parent_name
    exec(compile(source, f"<{full_name}>", "exec"), module.__dict__)
    return module


# --------------------------------------------------------------------------- #
# Source-level checks                                                         #
# --------------------------------------------------------------------------- #


def test_emit_hitl_is_syntactically_valid(playbook):
    _ast.parse(emit_str(playbook))


def test_emit_hitl_is_deterministic(playbook):
    assert emit_str(playbook) == emit_str(playbook)


def test_emit_imports_retry_policy(playbook):
    src = emit_str(playbook)
    assert "from temporalio.common import RetryPolicy" in src
    assert "from datetime import timedelta" in src


# --------------------------------------------------------------------------- #
# Typed activity signatures                                                   #
# --------------------------------------------------------------------------- #


def test_activity_signature_is_typed(playbook):
    src = emit_str(playbook)
    # The HITL action consumes two strings, returns a bool.
    assert "async def request_human_approval(incident_id: str, owner_email: str) -> bool:" in src
    # The playbook-action has two out_args → dict return.
    assert "async def open_mitigation_ticket(incident_id: str) -> dict[str, object]:" in src


# --------------------------------------------------------------------------- #
# Retry policy constants                                                      #
# --------------------------------------------------------------------------- #


def test_retry_policy_constants_present(playbook):
    mod = _load_module(emit_str(playbook))
    # HITL step gets a single-attempt policy.
    hitl_policy = mod.REQUEST_HUMAN_APPROVAL_RETRY_POLICY
    assert hitl_policy.maximum_attempts == 1
    # Plain action gets multi-attempt default.
    plain_policy = mod.OPEN_MITIGATION_TICKET_RETRY_POLICY
    assert plain_policy.maximum_attempts >= 2
    assert plain_policy.initial_interval == timedelta(seconds=1)
    # Registry tuple lines up with ACTIVITIES.
    assert len(mod.RETRY_POLICIES) == len(mod.ACTIVITIES)


# --------------------------------------------------------------------------- #
# HITL signal/query handlers                                                  #
# --------------------------------------------------------------------------- #


def test_workflow_class_has_signal_and_query_for_hitl_step(playbook):
    mod = _load_module(emit_str(playbook))
    cls = mod.WORKFLOW
    instance = cls()

    # Pre-signal state: query reports pending.
    assert instance.request_human_approval_status() == "pending"

    # Send the signal — state advances to approved.
    instance.request_human_approval_approve(True, reason="ok")
    assert instance.request_human_approval_status() == "approved"
    assert instance._request_human_approval_decision is True
    assert instance._request_human_approval_reason == "ok"

    # Reset and deny.
    instance._request_human_approval_decision = None
    instance.request_human_approval_approve(False)
    assert instance.request_human_approval_status() == "denied"


def test_no_signal_query_for_non_hitl_action(playbook):
    mod = _load_module(emit_str(playbook))
    cls = mod.WORKFLOW
    # The playbook-action step is NOT marked HITL — no handlers should exist.
    assert not hasattr(cls, "open_mitigation_ticket_approve")
    assert not hasattr(cls, "open_mitigation_ticket_status")


def test_emit_hitl_run_still_raises_not_implemented(playbook):
    import asyncio

    mod = _load_module(emit_str(playbook))
    with pytest.raises(NotImplementedError) as exc:
        asyncio.run(mod.WORKFLOW().run())
    assert playbook.x_secops_ng.stable_id in str(exc.value)
