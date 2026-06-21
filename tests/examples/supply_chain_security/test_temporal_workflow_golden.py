"""F-WF-SCS CORE-FANOUT-TMP — byte-parity golden for the temporal workflow.

The committed
``examples/temporal/supply_chain_security/workflow.temporal.py`` is
the Temporal compiler's output for the canonical CACAO playbook at
``content/playbooks/supply_chain_security/playbook.cacao.json``.

This module pins the workflow stub against the emitter so a refactor
of the Temporal compiler that silently changes serialisation (or a
drift between the canonical playbook and the mirrored example copy)
gets caught at the byte level. Activity-name <-> CACAO action-id
parity is verified too — every CACAO action step gets exactly one
``@activity.defn`` whose docstring records the originating ``step_id``.

If the change is intentional, regenerate the example::

    ./examples/temporal/supply_chain_security/regenerate.sh

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from compilers.temporal.emit import emit_file

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "temporal" / "supply_chain_security"
SOURCE = (
    REPO
    / "content"
    / "playbooks"
    / "supply_chain_security"
    / "playbook.cacao.json"
)
WORKFLOW_GOLDEN = EXAMPLE / "workflow.temporal.py"
MIRRORED_CACAO = EXAMPLE / "playbook.cacao.json"

_ACTIVITY_STEP_TYPES = {"action"}
_ACTIVITY_DEFN_RE = re.compile(
    r"@activity\.defn\nasync def (?P<name>[A-Za-z_][A-Za-z_0-9]*)\("
    r"[^)]*\)[^:]*:\n"
    r'    """[^"]*?\n\n'
    r"    CACAO step_id: (?P<step_id>[^\n]+)\n",
    re.DOTALL,
)


def test_example_artifacts_are_committed() -> None:
    for path in (WORKFLOW_GOLDEN, MIRRORED_CACAO):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_worked_example_matches_emitter_output() -> None:
    rendered = emit_file(SOURCE)
    expected = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/temporal/supply_chain_security/workflow.temporal.py "
        "drifted from the Temporal emitter output. Regenerate via "
        "`./examples/temporal/supply_chain_security/regenerate.sh` "
        "and commit the new bytes."
    )


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == SOURCE.read_bytes(), (
        "examples/temporal/supply_chain_security/playbook.cacao.json "
        "drifted from the canonical content/playbooks/"
        "supply_chain_security/playbook.cacao.json. Regenerate via "
        "`./examples/temporal/supply_chain_security/regenerate.sh`."
    )


def test_emit_is_deterministic() -> None:
    assert emit_file(SOURCE) == emit_file(SOURCE)


def test_canonical_declares_temporal_compile_target() -> None:
    """The canonical playbook must declare ``temporal`` so the unified
    CLI dispatches to the Temporal emitter without an out-of-band
    override.

    The n8n binding is already pinned by the sibling test; this test
    pins the Temporal binding owned by this card.
    """
    playbook = json.loads(SOURCE.read_text(encoding="utf-8"))
    targets = playbook["x_secops_ng"]["compile_targets"]
    assert "temporal" in targets, (
        "compile_targets on the canonical supply_chain_security "
        "playbook must include 'temporal' once the CORE-FANOUT-TMP "
        "card lands."
    )


def _action_step_ids_from_cacao() -> list[str]:
    playbook = json.loads(SOURCE.read_text(encoding="utf-8"))
    return [
        step_id
        for step_id, step in playbook["workflow"].items()
        if step.get("type") in _ACTIVITY_STEP_TYPES
    ]


def _activity_blocks_from_stub() -> list[tuple[str, str]]:
    """Return ``(activity_function_name, cacao_step_id)`` tuples in source order."""
    text = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    return [
        (m.group("name"), m.group("step_id"))
        for m in _ACTIVITY_DEFN_RE.finditer(text)
    ]


def test_activity_names_mirror_cacao_action_ids() -> None:
    """Every CACAO action step gets exactly one ``@activity.defn`` whose
    docstring records the originating ``step_id``, and vice versa.
    """
    cacao_action_ids = set(_action_step_ids_from_cacao())
    stub_blocks = _activity_blocks_from_stub()
    stub_step_ids = {step_id for _, step_id in stub_blocks}

    missing = cacao_action_ids - stub_step_ids
    assert not missing, (
        f"CACAO action step ids without a matching Temporal activity: "
        f"{sorted(missing)}"
    )
    extra = stub_step_ids - cacao_action_ids
    assert not extra, (
        f"Temporal activities without a matching CACAO action step id: "
        f"{sorted(extra)}"
    )
    assert len(stub_blocks) == len(cacao_action_ids), (
        "duplicate @activity.defn for the same CACAO step id in the stub"
    )

    function_names = [name for name, _ in stub_blocks]
    assert len(function_names) == len(set(function_names)), (
        "duplicate activity function names in the stub"
    )
