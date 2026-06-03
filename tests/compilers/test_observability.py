"""Per-target observability assertions on emitted compiler output.

This module asserts the contract the compiler-side OTel layer (see
``compilers/_shared/observability``) promises every reference compiler will
honour:

* For each CACAO ``action`` / ``playbook-action`` step in a playbook,
  the emitted code wraps the step body in **exactly one**
  ``tool.<step_id>`` span and records **exactly one** ``AuditRecord`` on
  ``AuditTrail.current()``.
* Re-running the emitter on the same parsed playbook produces
  byte-identical output — the helper layer is pure, and running the
  per-example ``regenerate.sh`` twice in a row produces no diff.

The LangGraph half shipped with F-CR-04 CORE-A3. The Temporal half ships
with F-CR-04 CORE-B3: per-step ``activity.<step_id>`` spans + a
``workflow.<stable_id>`` workflow-boundary span. Shared negatives at the
bottom of the file apply to both targets — no vendor SDK substrings, no
hard-coded ``http(s)://`` endpoints in the emitted OTel block, idempotent
emit on a second invocation.

Sovereign-stack guard
---------------------
Test imports use ``opentelemetry``-namespaced symbols only via the
emitted source. No vendor SDK strings appear in fixtures or assertions,
and no OTLP endpoint is hard-coded anywhere in this file.
"""
from __future__ import annotations

import ast
import os
import re
import subprocess
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import StepType, parse_file
from compilers.langgraph.state import render_module, render_module_from_file
from compilers.temporal import emit as render_temporal_module
from compilers.temporal import emit_file as render_temporal_module_from_file

REPO_ROOT = Path(__file__).resolve().parents[2]
LG_EXAMPLES = REPO_ROOT / "examples" / "langgraph"
LG_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "compilers"
    / "_shared"
    / "fixtures"
    / "vuln_intake.cacao.json"
)
TEMPORAL_EXAMPLES = REPO_ROOT / "examples" / "temporal"
TEMPORAL_FIXTURE = LG_FIXTURE  # same canonical CACAO source reused per A3 fixtures


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _action_step_ids(playbook) -> list[str]:
    """All CACAO step IDs that materialise as tool-wrapped action nodes."""
    return [
        step.step_id
        for step in playbook.workflow.values()
        if step.type in (StepType.ACTION, StepType.PLAYBOOK_ACTION)
    ]


def _count_tool_spans(source: str, step_id: str) -> int:
    """Count ``with _TRACER.start_as_current_span(name='tool.<step_id>'`` blocks.

    AST-based so whitespace / indentation drift in the emitter does not
    silently break the assertion.
    """
    return _count_spans_by_name(source, f"tool.{step_id}")


def _count_spans_by_name(source: str, expected: str) -> int:
    """Count ``with <tracer>.start_as_current_span(name=<expected>, ...)`` blocks.

    Generic AST helper used by both LangGraph (``tool.<step_id>``) and
    Temporal (``activity.<step_id>`` / ``workflow.<stable_id>``) assertions.
    """
    tree = ast.parse(source)
    n = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            call = item.context_expr
            if not isinstance(call, ast.Call):
                continue
            func = call.func
            if not (isinstance(func, ast.Attribute) and func.attr == "start_as_current_span"):
                continue
            for kw in call.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant) and kw.value.value == expected:
                    n += 1
                    break
    return n


def _count_audit_appends(source: str, step_id: str) -> int:
    """Count ``AuditTrail.current().append(AuditRecord(span_name='tool.<step_id>'...))``."""
    tree = ast.parse(source)
    expected = f"tool.{step_id}"
    n = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # outer call: AuditTrail.current().append(<AuditRecord(...)>)
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "append"):
            continue
        recv = func.value
        if not (
            isinstance(recv, ast.Call)
            and isinstance(recv.func, ast.Attribute)
            and recv.func.attr == "current"
            and isinstance(recv.func.value, ast.Name)
            and recv.func.value.id == "AuditTrail"
        ):
            continue
        if not node.args:
            continue
        inner = node.args[0]
        if not (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == "AuditRecord"):
            continue
        for kw in inner.keywords:
            if kw.arg == "span_name" and isinstance(kw.value, ast.Constant) and kw.value.value == expected:
                n += 1
                break
    return n


def _example_dirs_with_regenerate() -> list[Path]:
    return sorted(p.parent for p in LG_EXAMPLES.glob("*/regenerate.sh"))


# --------------------------------------------------------------------------- #
# LangGraph: per-step span + audit cardinality                                #
# --------------------------------------------------------------------------- #


def test_langgraph_fixture_emits_one_span_per_action_step() -> None:
    """Each action step shows up as exactly one ``tool.<step_id>`` span."""
    playbook = parse_file(LG_FIXTURE)
    source = render_module(playbook)
    step_ids = _action_step_ids(playbook)
    assert step_ids, "fixture has no action steps to assert against"
    for step_id in step_ids:
        n = _count_tool_spans(source, step_id)
        assert n == 1, f"expected 1 span for {step_id!r}, found {n}"


def test_langgraph_fixture_emits_one_audit_record_per_action_step() -> None:
    """Each action step records exactly one ``AuditTrail.current().append(...)``."""
    playbook = parse_file(LG_FIXTURE)
    source = render_module(playbook)
    step_ids = _action_step_ids(playbook)
    assert step_ids, "fixture has no action steps to assert against"
    for step_id in step_ids:
        n = _count_audit_appends(source, step_id)
        assert n == 1, f"expected 1 audit append for {step_id!r}, found {n}"


def test_langgraph_total_span_count_matches_action_count() -> None:
    """Defence in depth: no stray spans the per-step loop could miss."""
    playbook = parse_file(LG_FIXTURE)
    source = render_module(playbook)
    expected = len(_action_step_ids(playbook))
    # Every span emitted by the LangGraph state generator is a tool.* span;
    # node-level spans live inside the assembled graph, not the bindings module.
    actual = source.count("_TRACER.start_as_current_span(")
    assert actual == expected, (
        f"expected {expected} start_as_current_span(...) calls "
        f"(one per action step), found {actual}"
    )


def test_langgraph_total_audit_count_matches_action_count() -> None:
    expected = len(_action_step_ids(parse_file(LG_FIXTURE)))
    source = render_module_from_file(LG_FIXTURE)
    actual = source.count("AuditTrail.current().append(")
    assert actual == expected, (
        f"expected {expected} AuditTrail.current().append(...) calls "
        f"(one per action step), found {actual}"
    )


@pytest.mark.parametrize(
    "example_dir",
    _example_dirs_with_regenerate(),
    ids=lambda p: p.name,
)
def test_langgraph_every_example_emits_one_span_per_action_step(example_dir: Path) -> None:
    """Cross-fixture: every langgraph example holds the per-step span contract."""
    playbook_path = example_dir / "playbook.cacao.json"
    playbook = parse_file(playbook_path)
    source = render_module(playbook)
    step_ids = _action_step_ids(playbook)
    if not step_ids:
        pytest.skip(f"{example_dir.name} has no action steps")
    for step_id in step_ids:
        spans = _count_tool_spans(source, step_id)
        audits = _count_audit_appends(source, step_id)
        assert spans == 1, f"{example_dir.name}/{step_id}: {spans} spans (want 1)"
        assert audits == 1, f"{example_dir.name}/{step_id}: {audits} audits (want 1)"


# --------------------------------------------------------------------------- #
# Idempotent emit                                                             #
# --------------------------------------------------------------------------- #


def test_langgraph_render_module_is_idempotent() -> None:
    """Re-running the emitter on the same playbook produces byte-identical output.

    This is the in-process counterpart to the regenerate.sh idempotency
    check below: it isolates the emitter from any shell-script edge case.
    """
    playbook = parse_file(LG_FIXTURE)
    first = render_module(playbook)
    second = render_module(playbook)
    third = render_module(parse_file(LG_FIXTURE))  # reparse to defeat caching
    assert first == second
    assert first == third


def test_langgraph_render_module_does_not_accumulate_spans() -> None:
    """The emitter is pure: a second render does not append additional spans / audits.

    Catches the regression where an emitter holds list state across calls
    and a second invocation doubles the wrapped bodies.
    """
    playbook = parse_file(LG_FIXTURE)
    expected_spans = len(_action_step_ids(playbook))
    for _ in range(3):
        source = render_module(playbook)
        assert source.count("_TRACER.start_as_current_span(") == expected_spans
        assert source.count("AuditTrail.current().append(") == expected_spans


# --------------------------------------------------------------------------- #
# regenerate.sh idempotency                                                   #
# --------------------------------------------------------------------------- #


_REGENERATE_OUTPUTS = ("graph_spec.json", "state_bindings.py", "playbook.cacao.json")


def _run_regenerate(example_dir: Path) -> dict[str, bytes]:
    """Invoke the committed ``regenerate.sh`` in place and snapshot its outputs.

    Some example ``regenerate.sh`` scripts derive ``REPO_ROOT`` from
    ``${HERE}/../../..``, so they only work when run from inside the
    real example directory. To keep the working tree clean, we snapshot
    the relevant files before any run and restore them in the caller's
    ``finally``.
    """
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(REPO_ROOT))
    script = example_dir / "regenerate.sh"
    proc = subprocess.run(
        ["bash", str(script)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=False,
        timeout=60,
    )
    assert proc.returncode == 0, (
        f"regenerate.sh failed in {example_dir}:\n"
        f"stdout:\n{proc.stdout.decode('utf-8', 'replace')}\n"
        f"stderr:\n{proc.stderr.decode('utf-8', 'replace')}"
    )
    snapshot: dict[str, bytes] = {}
    for name in ("graph_spec.json", "state_bindings.py"):
        target = example_dir / name
        assert target.exists(), f"regenerate.sh did not produce {target}"
        snapshot[name] = target.read_bytes()
    return snapshot


def _snapshot_outputs(example_dir: Path) -> dict[str, bytes | None]:
    snap: dict[str, bytes | None] = {}
    for name in _REGENERATE_OUTPUTS:
        p = example_dir / name
        snap[name] = p.read_bytes() if p.exists() else None
    return snap


def _restore_outputs(example_dir: Path, snap: dict[str, bytes | None]) -> None:
    for name, data in snap.items():
        p = example_dir / name
        if data is None:
            if p.exists():
                p.unlink()
        else:
            p.write_bytes(data)


@pytest.mark.parametrize(
    "example_dir",
    _example_dirs_with_regenerate(),
    ids=lambda p: p.name,
)
def test_langgraph_regenerate_sh_is_idempotent(example_dir: Path) -> None:
    """Re-running ``regenerate.sh`` on its own output produces no diff.

    Runs in place (some scripts resolve ``REPO_ROOT`` from their own path)
    and restores the pre-test snapshot in a ``finally`` so the working
    tree is unchanged whether the assertion passes or fails. The contract:
    run #1 produces some bytes; run #2, starting from those bytes,
    produces the *same* bytes — i.e. the script is a fixed point.
    """
    pristine = _snapshot_outputs(example_dir)
    try:
        first = _run_regenerate(example_dir)
        second = _run_regenerate(example_dir)
        for name in first:
            assert first[name] == second[name], (
                f"{example_dir.name}/{name} drifted between two consecutive "
                f"regenerate.sh runs — emitter is not idempotent"
            )
    finally:
        _restore_outputs(example_dir, pristine)


def test_langgraph_regenerate_sh_uses_only_opentelemetry_api() -> None:
    """Sovereign-stack guard: emitted state module imports ``opentelemetry``\
    (the API), never a vendor SDK or hard-coded OTLP endpoint."""
    example_dir = LG_EXAMPLES / "vuln-intake"
    pristine = _snapshot_outputs(example_dir)
    try:
        _run_regenerate(example_dir)
        emitted = (example_dir / "state_bindings.py").read_text(encoding="utf-8")
    finally:
        _restore_outputs(example_dir, pristine)

    assert "from opentelemetry import trace" in emitted
    for forbidden in ("datadog", "honeycomb", "newrelic", "new_relic"):
        assert forbidden not in emitted.lower(), (
            f"vendor SDK substring leaked into emitted state_bindings.py: {forbidden!r}"
        )
    # No hard-coded OTLP endpoint URL in the emitted source.
    assert not re.search(r"https?://[^\s'\"]*otlp", emitted, re.IGNORECASE), (
        "OTLP endpoint URL hard-coded in emitted state_bindings.py"
    )


# --------------------------------------------------------------------------- #
# Temporal: per-activity span + workflow-boundary span cardinality            #
# --------------------------------------------------------------------------- #


def test_temporal_fixture_emits_one_span_per_action_step() -> None:
    """Each action step shows up as exactly one ``activity.<step_id>`` span."""
    playbook = parse_file(TEMPORAL_FIXTURE)
    source = render_temporal_module(playbook)
    step_ids = _action_step_ids(playbook)
    assert step_ids, "fixture has no action steps to assert against"
    for step_id in step_ids:
        n = _count_spans_by_name(source, f"activity.{step_id}")
        assert n == 1, f"expected 1 activity span for {step_id!r}, found {n}"


def test_temporal_fixture_emits_one_audit_record_per_activity_span() -> None:
    """Each activity span pairs with exactly one ``AuditTrail.current().append(...)``."""
    playbook = parse_file(TEMPORAL_FIXTURE)
    source = render_temporal_module(playbook)
    step_ids = _action_step_ids(playbook)
    assert step_ids
    for step_id in step_ids:
        expected = f"activity.{step_id}"
        # Reuse the LangGraph audit AST walker by counting AuditRecord(span_name=...)
        # entries — the contract is the same string identity per emitted span.
        tree = ast.parse(source)
        n = 0
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "AuditRecord"):
                continue
            for kw in node.keywords:
                if kw.arg == "span_name" and isinstance(kw.value, ast.Constant) and kw.value.value == expected:
                    n += 1
                    break
        assert n == 1, f"expected 1 audit record for {expected!r}, found {n}"


def test_temporal_fixture_emits_workflow_boundary_span() -> None:
    """The workflow ``run`` method wraps its body in a single
    ``workflow.<stable_id>`` span — the workflow-boundary scaffold.
    """
    playbook = parse_file(TEMPORAL_FIXTURE)
    source = render_temporal_module(playbook)
    expected = f"workflow.{playbook.x_secops_ng.stable_id}"
    n = _count_spans_by_name(source, expected)
    assert n == 1, f"expected exactly 1 workflow-boundary span {expected!r}, found {n}"


def _count_spans_by_prefix(source: str, prefix: str) -> int:
    """Count ``with <tracer>.start_as_current_span(name=<prefix>...)`` blocks.

    AST-based; used for cardinality assertions over a span-name namespace
    (e.g. all ``activity.*`` spans).
    """
    tree = ast.parse(source)
    n = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            call = item.context_expr
            if not isinstance(call, ast.Call):
                continue
            func = call.func
            if not (isinstance(func, ast.Attribute) and func.attr == "start_as_current_span"):
                continue
            for kw in call.keywords:
                if (
                    kw.arg == "name"
                    and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, str)
                    and kw.value.value.startswith(prefix)
                ):
                    n += 1
                    break
    return n


def test_temporal_total_activity_span_count_matches_action_count() -> None:
    """Defence in depth: total ``activity.*`` span count = action-step count."""
    playbook = parse_file(TEMPORAL_FIXTURE)
    source = render_temporal_module(playbook)
    expected = len(_action_step_ids(playbook))
    actual = _count_spans_by_prefix(source, "activity.")
    assert actual == expected, (
        f"expected {expected} activity.* spans, found {actual}"
    )


def test_temporal_total_workflow_boundary_span_count_is_one() -> None:
    """Exactly one ``workflow.<stable_id>`` span across the emitted module."""
    source = render_temporal_module(parse_file(TEMPORAL_FIXTURE))
    workflow_spans = _count_spans_by_prefix(source, "workflow.")
    assert workflow_spans == 1, (
        f"expected exactly 1 workflow.* boundary span, found {workflow_spans}"
    )


# --------------------------------------------------------------------------- #
# Idempotent emit — Temporal                                                  #
# --------------------------------------------------------------------------- #


def test_temporal_render_module_is_idempotent() -> None:
    """Re-running the Temporal emitter produces byte-identical output."""
    playbook = parse_file(TEMPORAL_FIXTURE)
    first = render_temporal_module(playbook)
    second = render_temporal_module(playbook)
    third = render_temporal_module(parse_file(TEMPORAL_FIXTURE))  # reparse to defeat caching
    assert first == second
    assert first == third


def test_temporal_render_module_does_not_accumulate_spans() -> None:
    """A second Temporal render does not double the activity / workflow spans."""
    playbook = parse_file(TEMPORAL_FIXTURE)
    expected_activity = len(_action_step_ids(playbook))
    for _ in range(3):
        source = render_temporal_module(playbook)
        assert _count_spans_by_prefix(source, "activity.") == expected_activity
        assert _count_spans_by_prefix(source, "workflow.") == 1


# --------------------------------------------------------------------------- #
# Shared negatives — apply to BOTH langgraph + temporal emitters              #
# --------------------------------------------------------------------------- #


_VENDOR_CASE_INSENSITIVE = ("datadog", "honeycomb", "newrelic", "new_relic")
_VENDOR_CASE_SENSITIVE = ("DD_",)  # Datadog env-var prefix; uppercase only to avoid `add_messages` false-positive


def _emit_both_targets() -> dict[str, str]:
    """Render both reference compiler outputs from the shared CACAO fixture."""
    playbook = parse_file(TEMPORAL_FIXTURE)  # same canonical source as LG_FIXTURE
    return {
        "langgraph": render_module(playbook),
        "temporal": render_temporal_module(playbook),
    }


@pytest.mark.parametrize("target", ["langgraph", "temporal"])
def test_emitted_output_has_no_vendor_sdk_substrings(target: str) -> None:
    """No ``datadog|honeycomb|newrelic|DD_`` substrings in either emitter's output.

    The compile-target layer is sovereign-stack neutral: it speaks the OTel
    API, not any vendor SDK. Vendor names are matched case-insensitively;
    the ``DD_`` env-var prefix is uppercase-only so legitimate identifiers
    like ``add_messages`` are not flagged.
    """
    source = _emit_both_targets()[target]
    lowered = source.lower()
    for needle in _VENDOR_CASE_INSENSITIVE:
        assert needle not in lowered, (
            f"{target}: forbidden vendor substring {needle!r} leaked into emitted output"
        )
    for needle in _VENDOR_CASE_SENSITIVE:
        assert needle not in source, (
            f"{target}: forbidden vendor env-var prefix {needle!r} leaked into emitted output"
        )


@pytest.mark.parametrize("target", ["langgraph", "temporal"])
def test_emitted_output_has_no_hardcoded_http_endpoint(target: str) -> None:
    """No hard-coded ``http(s)://`` URL in the emitted OTel block.

    The OTel endpoint MUST be env-var driven (``OTEL_EXPORTER_OTLP_ENDPOINT``
    or operator equivalent) so the same artifact runs against any backend
    the operator has chosen.
    """
    source = _emit_both_targets()[target]
    assert not re.search(r"https?://", source), (
        f"{target}: hard-coded http(s):// URL found in emitted output — "
        f"OTel endpoint must be env-var driven, not baked into the artifact"
    )


@pytest.mark.parametrize("target", ["langgraph", "temporal"])
def test_emitted_output_is_idempotent_across_targets(target: str) -> None:
    """Both emitters are pure: a second invocation produces identical bytes."""
    playbook = parse_file(TEMPORAL_FIXTURE)
    renderer = {
        "langgraph": render_module,
        "temporal": render_temporal_module,
    }[target]
    first = renderer(playbook)
    second = renderer(playbook)
    third = renderer(parse_file(TEMPORAL_FIXTURE))
    assert first == second, f"{target}: second emit drifted from first"
    assert first == third, f"{target}: emit after reparse drifted"
