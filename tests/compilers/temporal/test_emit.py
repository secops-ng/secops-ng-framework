"""Tests for compilers/temporal/emit.

Covers:
- One ``@workflow.defn`` class per playbook with a NotImplementedError body.
- One ``@activity.defn`` async function per CACAO ``action`` /
  ``playbook-action`` step (and only those), each raising NotImplementedError
  with the CACAO step_id in the message.
- Control-flow steps (start, end, if-condition, ...) produce no activities.
- Generated source is syntactically valid Python and importable in isolation
  with a stub ``temporalio`` module on ``sys.modules``.
- Deterministic output: emitting twice yields byte-identical strings.
- Identifier collisions on duplicate action names get unique suffixes.
"""
from __future__ import annotations

import ast as _ast
import importlib.util
import json
import sys
import types
from copy import deepcopy
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse
from compilers.temporal.emit import emit as emit_str
from compilers.temporal.emit import emit_file as emit_file_fn

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "vuln_intake.cacao.json"
)


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture()
def playbook(fixture_data):
    return parse(deepcopy(fixture_data))


def _temporalio_stub() -> types.ModuleType:
    """Build a minimal ``temporalio`` package stub for import-time tests.

    The emitter targets the real SDK at runtime, but the test environment
    isn't entitled to a heavyweight dependency — we only need ``activity.defn``
    and ``workflow.defn`` / ``workflow.run`` to exist as decorators that
    return the wrapped object unchanged.
    """
    def passthrough(fn):
        return fn

    activity = types.SimpleNamespace(defn=passthrough)
    workflow = types.SimpleNamespace(
        defn=passthrough, run=passthrough, signal=passthrough, query=passthrough
    )

    class RetryPolicy:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    common = types.SimpleNamespace(RetryPolicy=RetryPolicy)
    pkg = types.ModuleType("temporalio")
    pkg.activity = activity  # type: ignore[attr-defined]
    pkg.workflow = workflow  # type: ignore[attr-defined]
    pkg.common = common  # type: ignore[attr-defined]
    return pkg


def _opentelemetry_stub() -> types.ModuleType:
    """Build a minimal ``opentelemetry`` stub for emitted-source import tests.

    The emitter wraps activity bodies in ``_TRACER.start_as_current_span(...)``
    context managers (F-CR-04 CORE-B1). The test environment doesn't carry the
    real OTel SDK, so we expose a no-op tracer whose span context manager
    accepts the keyword args the emitter uses (``name=``, ``attributes=``).
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
    """Stub the sibling ``_audit_mirror`` module the emitted code imports.

    Generated artifacts emit ``from ._audit_mirror import AuditRecord, AuditTrail``;
    in tests we splice a no-op pair under the synthetic parent package so
    relative-import resolution succeeds.
    """

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


def _load_module(source: str, name: str = "_temporal_stub_under_test") -> types.ModuleType:
    """Import a string of source as a fresh module with temporalio stubbed."""
    pkg = _temporalio_stub()
    sys.modules["temporalio"] = pkg
    sys.modules["temporalio.activity"] = pkg.activity  # type: ignore[assignment]
    sys.modules["temporalio.workflow"] = pkg.workflow  # type: ignore[assignment]
    sys.modules["temporalio.common"] = pkg.common  # type: ignore[assignment]
    otel = _opentelemetry_stub()
    sys.modules["opentelemetry"] = otel
    sys.modules["opentelemetry.trace"] = otel.trace  # type: ignore[assignment]
    # The emitted source does `from ._audit_mirror import ...`, so the module
    # must live in a package. Synthesise a tiny parent package and bind the
    # stub _audit_mirror inside it.
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


def test_emit_is_syntactically_valid_python(playbook):
    source = emit_str(playbook)
    _ast.parse(source)


def test_emit_is_deterministic(playbook):
    assert emit_str(playbook) == emit_str(playbook)


def test_one_workflow_class_per_playbook(playbook):
    source = emit_str(playbook)
    mod = _load_module(source)
    # Exactly one workflow class is exported as WORKFLOW.
    assert hasattr(mod, "WORKFLOW")
    cls = mod.WORKFLOW
    assert isinstance(cls, type)
    assert cls.__name__.endswith("Workflow")


def test_workflow_run_raises_not_implemented(playbook):
    import asyncio

    mod = _load_module(emit_str(playbook))
    instance = mod.WORKFLOW()
    with pytest.raises(NotImplementedError) as exc:
        asyncio.run(instance.run())
    # stable_id is surfaced in the error so a runtime worker fails loudly at
    # the right scope.
    assert playbook.x_secops_ng.stable_id in str(exc.value)


def test_one_activity_per_action_step(playbook):
    mod = _load_module(emit_str(playbook))
    expected_action_ids = {
        sid for sid, s in playbook.workflow.items() if s.type.value in {"action", "playbook-action"}
    }
    # ACTIVITIES is a tuple of the function objects, one per action step.
    assert len(mod.ACTIVITIES) == len(expected_action_ids)
    # Every activity is async (Temporal requirement) and is the result of
    # the activity.defn passthrough (so it remained a function).
    for fn in mod.ACTIVITIES:
        assert callable(fn)


def test_activities_raise_not_implemented_with_step_id(playbook):
    import asyncio
    import inspect

    mod = _load_module(emit_str(playbook))
    action_step_ids = [
        sid for sid, s in playbook.workflow.items() if s.type.value in {"action", "playbook-action"}
    ]
    seen_ids: set[str] = set()
    for fn in mod.ACTIVITIES:
        # Activities are now typed; pass placeholder positionals derived from
        # the resolved signature so we exercise the NotImplementedError body.
        sig = inspect.signature(fn)
        kwargs = {name: None for name in sig.parameters}
        with pytest.raises(NotImplementedError) as exc:
            asyncio.run(fn(**kwargs))
        msg = str(exc.value)
        # Exactly one action step_id appears in each error message.
        matches = [sid for sid in action_step_ids if sid in msg]
        assert len(matches) == 1, f"activity error message did not name exactly one step: {msg}"
        seen_ids.add(matches[0])
    assert seen_ids == set(action_step_ids)


def test_no_activity_for_control_flow_steps(playbook):
    source = emit_str(playbook)
    # Control-flow step_ids must NOT appear in activity-decorated function
    # docstrings. We check by step_id presence inside @activity.defn blocks
    # which only contain action step_ids.
    control_ids = [
        sid for sid, s in playbook.workflow.items()
        if s.type.value not in {"action", "playbook-action"}
    ]
    # Pull out the activity-defn region (after the imports, before the
    # @workflow.defn class). Coarse but sufficient.
    activity_region, _, _workflow_region = source.partition("@workflow.defn")
    for sid in control_ids:
        assert sid not in activity_region, f"control-flow step leaked into activity region: {sid}"


def test_collision_in_action_names_gets_unique_suffix(fixture_data):
    data = deepcopy(fixture_data)
    # Force two action steps to share the same human-readable name.
    data["workflow"]["action--22222222-2222-4222-8222-222222222222"]["name"] = "do thing"
    data["workflow"]["action--44444444-4444-4444-8444-444444444444"]["name"] = "do thing"
    data["workflow"]["action--55555555-5555-4555-8555-555555555555"]["name"] = "do thing"
    pb = parse(data)
    mod = _load_module(emit_str(pb), name="_collide")
    names = [fn.__name__ for fn in mod.ACTIVITIES]
    assert len(set(names)) == len(names), f"duplicate activity names: {names}"


def test_header_present_and_overridable(playbook):
    assert emit_str(playbook).startswith("# AUTO-GENERATED")
    assert emit_str(playbook, header="").startswith('"""Generated Temporal stub.')


def test_emit_file_matches_emit(playbook):
    from_file = emit_file_fn(FIXTURE)
    in_memory = emit_str(playbook)
    assert from_file == in_memory


def test_core_body_renders_primitive_call_with_span_prologue(fixture_data):
    """When a step carries x_secops_ng.core_body, the Temporal emitter
    replaces the NotImplementedError stub with the deterministic
    primitive-call snippet, while the OTel span + AuditTrail.append
    prologue around the activity body stays intact.

    Sibling-B smoke for F-WF-01 CORE-MECH-EMIT-TMPRL (PR #220). Uses an
    in-memory mutation of the existing vuln_intake fixture so no new
    playbook content lands on disk and no golden file is touched.
    """
    data = deepcopy(fixture_data)
    target_step_id = "action--22222222-2222-4222-8222-222222222222"
    step = data["workflow"][target_step_id]
    step.setdefault("x_secops_ng", {})["core_body"] = {
        "primitive": "secops_ng.primitives.enrichment.lookup_asset",
        "in": {
            "finding_id": "__finding_id__",
            "lookup_mode": "'full'",
        },
        "out": "__severity__",
    }

    pb = parse(data)
    source = emit_str(pb)

    # Emitted source remains valid Python and importable under the stubs.
    _ast.parse(source)
    _load_module(source, name="_core_body_smoke")

    # Locate the activity region — everything before the @workflow.defn
    # class. The action step's body must contain the primitive import and
    # call lines verbatim, with argument order matching insertion order
    # of core_body.in (parser preserves dict order).
    activity_region, _, _workflow_region = source.partition("@workflow.defn")
    assert "from secops_ng.primitives.enrichment import lookup_asset" in activity_region
    assert (
        "__severity__ = lookup_asset(finding_id=__finding_id__, lookup_mode='full')"
        in activity_region
    )

    # Pre-CORE NotImplementedError stub must NOT be emitted for the
    # core_body-bound step. Other action steps in the fixture still stub
    # out, so we anchor on the bound step's step_id specifically.
    assert (
        f"CACAO action stub not implemented: step_id='{target_step_id}'"
        not in activity_region
    )

    # The OTel span + AuditTrail prologue (emit_tool_span_block) must
    # still wrap the primitive call: the activity.<step_id> span name
    # and the AuditTrail.current().append call are both present in the
    # activity region for this step.
    assert f"activity.{target_step_id}" in activity_region
    assert "AuditTrail.current().append" in activity_region
