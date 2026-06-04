"""Smoke test: temporal emitter materializes ``x_secops_ng.core_body`` bindings.

Covers the F-WF-01 CORE-MECH-EMIT-TMPRL contract:

- When an action step carries ``x_secops_ng.core_body``, the emitted
  ``@activity.defn`` function body becomes the deterministic primitive
  call (leaf ``from <module> import <callable>`` + ``return
  <callable>(**kwargs)``), spliced inside the existing OTel /
  AuditTrail wrapping.
- When the step does not carry ``core_body``, the emitted body is
  unchanged from the pre-CORE behaviour (``raise NotImplementedError``
  with the CACAO ``step_id`` in the message). This is the
  back-compat half of the contract.
- Emitter output remains deterministic and the generated module parses
  as valid Python.

This card explicitly defers a full unit-test matrix (variable-context
expressions, multi-arg primitives, nullary primitives, golden-output
regen) to sibling follow-up cards (CORE-MECH-CONTENT, per-target
EMIT-N8N / EMIT-LG, and the goldens regen card). This file ships ONE
smoke test exercising the new path with a synthetic step + ONE that
pins the no-binding back-compat path.
"""
from __future__ import annotations

import ast as _ast
import json
from copy import deepcopy
from pathlib import Path

import pytest

from compilers._shared.cacao_parser import parse
from compilers.temporal.emit import emit as emit_str

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "vuln_intake.cacao.json"
)

# The first action step in the vuln-intake fixture — the one we attach
# a synthetic ``core_body`` to so we exercise the new emitter path.
_ENRICH_STEP_ID = "action--22222222-2222-4222-8222-222222222222"


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _with_core_body(data: dict) -> dict:
    """Return a deep-copied fixture whose enrich step has a CORE binding."""
    out = deepcopy(data)
    step = out["workflow"][_ENRICH_STEP_ID]
    step.setdefault("x_secops_ng", {})["core_body"] = {
        "primitive": "secops_ng.primitives.enrich.vuln_finding",
        "in": {"finding_id": "__finding_id__"},
        "out": "__severity__",
    }
    return out


def test_emit_materializes_core_body_when_present(fixture_data):
    """Smoke: a step with ``core_body`` emits the primitive call inline."""
    src = emit_str(parse(_with_core_body(fixture_data)))

    # The leaf import + return call must both appear in the emitted source.
    assert "from secops_ng.primitives.enrich import vuln_finding\n" in src
    assert "return vuln_finding(finding_id=__finding_id__)" in src

    # The pre-CORE NotImplementedError body MUST be gone for the bound
    # step (matched on the step_id in the f-string so we don't false-hit
    # other un-bound steps in the same playbook).
    assert (
        f"CACAO action stub not implemented: step_id={_ENRICH_STEP_ID!r}"
        not in src
    )

    # A breadcrumb comment naming the binding is emitted so an integrator
    # opening the generated file sees the CACAO → primitive mapping.
    assert (
        "# SecOps-NG CORE primitive binding: "
        "secops_ng.primitives.enrich.vuln_finding"
    ) in src
    assert "# CACAO out arg                  : __severity__" in src

    # The result must still be syntactically valid Python — no string
    # surgery accidentally broke the surrounding span block.
    _ast.parse(src)

    # Determinism: emitting twice yields byte-identical output.
    assert src == emit_str(parse(_with_core_body(fixture_data)))


def test_emit_preserves_notimplemented_when_core_body_absent(fixture_data):
    """Back-compat: steps without ``core_body`` still emit the NIE stub."""
    src = emit_str(parse(deepcopy(fixture_data)))

    # The enrich step has no core_body in the unmodified fixture, so the
    # pre-CORE NotImplementedError body must still be there.
    assert (
        f"CACAO action stub not implemented: step_id={_ENRICH_STEP_ID!r}"
        in src
    )
    # And no spurious CORE comment for unbound steps.
    assert "# SecOps-NG CORE primitive binding:" not in src

    _ast.parse(src)
