"""F-WF-07 CORE-FANOUT-N8N — byte-parity golden for the n8n workflow.

The committed
``examples/n8n/codebase_vuln_management/workflow.n8n.json``
is the n8n compiler's output for the canonical CACAO playbook at
``content/playbooks/codebase_vuln_management/playbook.cacao.json``.

This module pins the workflow JSON against the emitter so a refactor
of the n8n compiler that silently changes serialisation (or a drift
between the canonical playbook and the mirrored example copy) gets
caught at the byte level.

If the change is intentional, regenerate the example::

    ./examples/n8n/codebase_vuln_management/regenerate.sh

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit as emit_n8n

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "n8n" / "codebase_vuln_management"
SOURCE = (
    REPO / "content" / "playbooks" / "codebase_vuln_management" / "playbook.cacao.json"
)
WORKFLOW_GOLDEN = EXAMPLE / "workflow.n8n.json"
MIRROR = EXAMPLE / "playbook.cacao.json"


def _serialise_n8n(payload: dict) -> str:
    """Match ``python -m tools.compile --target n8n`` (indent=2)."""
    return json.dumps(payload, indent=2) + "\n"


def test_workflow_golden_is_committed() -> None:
    assert WORKFLOW_GOLDEN.exists(), f"missing golden: {WORKFLOW_GOLDEN}"
    assert WORKFLOW_GOLDEN.stat().st_size > 0


def test_mirrored_playbook_matches_canonical() -> None:
    """The mirrored example copy of playbook.cacao.json must stay
    byte-identical to the canonical source — the regenerate.sh script
    copies the canonical playbook into the example dir on every run."""
    assert MIRROR.read_bytes() == SOURCE.read_bytes(), (
        "examples/n8n/codebase_vuln_management/playbook.cacao.json drifted "
        "from the canonical content/playbooks/codebase_vuln_management/"
        "playbook.cacao.json. Regenerate via "
        "`./examples/n8n/codebase_vuln_management/regenerate.sh`."
    )


def test_n8n_workflow_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_n8n(emit_n8n(playbook))
    expected = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "codebase_vuln_management n8n workflow drifted. Regenerate via "
        "`./examples/n8n/codebase_vuln_management/regenerate.sh` and commit "
        "the new bytes alongside the emitter change."
    )


def test_n8n_workflow_emit_is_deterministic() -> None:
    playbook = parse_file(SOURCE)
    assert _serialise_n8n(emit_n8n(playbook)) == _serialise_n8n(emit_n8n(playbook))
