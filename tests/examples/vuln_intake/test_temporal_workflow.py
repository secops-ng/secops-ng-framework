"""Drift guard for the ``examples/temporal/vuln-intake/`` worked example.

Mirrors the data-exfil and threat-intel-ingest temporal example tests:
re-emits the Temporal workflow stub from the canonical CACAO playbook
and pins the result byte-for-byte against the committed
``examples/temporal/vuln-intake/workflow_stub.py``. Adds an
activity-name ↔ CACAO action-id parity check so the one-to-one mirroring
contract documented in ``examples/temporal/vuln-intake/README.md`` is
enforced by tests, not by convention.

Regenerate via::

    python -m compilers.temporal \\
        content/playbooks/vuln-intake/playbook.cacao.json \\
        --out examples/temporal/vuln-intake/workflow_stub.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from compilers.temporal.emit import emit_file

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPO_ROOT / "content" / "playbooks" / "vuln-intake" / "playbook.cacao.json"
WORKED_EXAMPLE = (
    REPO_ROOT / "examples" / "temporal" / "vuln-intake" / "workflow_stub.py"
)

_ACTIVITY_STEP_TYPES = {"action"}
_ACTIVITY_DEFN_RE = re.compile(
    r"@activity\.defn\nasync def (?P<name>[A-Za-z_][A-Za-z_0-9]*)\("
    r"[^)]*\)[^:]*:\n"
    r'    """[^"]*?\n\n'
    r"    CACAO step_id: (?P<step_id>[^\n]+)\n",
    re.DOTALL,
)


def test_worked_example_matches_emitter_output() -> None:
    rendered = emit_file(SOURCE)
    expected = WORKED_EXAMPLE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/temporal/vuln-intake/workflow_stub.py drifted from the "
        "Temporal emitter output. Regenerate via `python -m "
        "compilers.temporal content/playbooks/vuln-intake/playbook.cacao.json "
        "--out examples/temporal/vuln-intake/workflow_stub.py` and commit "
        "the new bytes."
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
    text = WORKED_EXAMPLE.read_text(encoding="utf-8")
    return [(m.group("name"), m.group("step_id")) for m in _ACTIVITY_DEFN_RE.finditer(text)]


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


def test_emit_is_deterministic() -> None:
    assert emit_file(SOURCE) == emit_file(SOURCE)
