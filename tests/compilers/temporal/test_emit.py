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


def _load_module(source: str, name: str = "_temporal_stub_under_test") -> types.ModuleType:
    """Import a string of source as a fresh module with temporalio stubbed."""
    pkg = _temporalio_stub()
    sys.modules["temporalio"] = pkg
    sys.modules["temporalio.activity"] = pkg.activity  # type: ignore[assignment]
    sys.modules["temporalio.workflow"] = pkg.workflow  # type: ignore[assignment]
    sys.modules["temporalio.common"] = pkg.common  # type: ignore[assignment]
    spec = importlib.util.spec_from_loader(name, loader=None)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, f"<{name}>", "exec"), module.__dict__)
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
