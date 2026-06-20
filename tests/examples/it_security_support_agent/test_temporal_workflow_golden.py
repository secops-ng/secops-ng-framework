"""F-WF-12 CORE-FANOUT-TEMPORAL — byte-parity golden for the Temporal workflow.

The committed
``examples/temporal/it_security_support_agent/workflow.temporal.py`` is
the Temporal compiler's output for the canonical CACAO playbook at
``content/playbooks/it_security_support_agent/playbook.cacao.json``.

This module pins the workflow stub against the emitter so a refactor
of the Temporal compiler that silently changes serialisation (or a
drift between the canonical playbook and the mirrored example copy)
gets caught at the byte level.

If the change is intentional, regenerate the example::

    ./examples/temporal/it_security_support_agent/regenerate.sh

and commit the updated bytes alongside the emitter change.

The interaction-evidence byte-parity golden and the immutable
interaction-evidence fixture are owned by the sibling module
``test_temporal_interaction_evidence`` — this module covers the
workflow graph only.
"""
from __future__ import annotations

from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.temporal.emit import emit as emit_temporal

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "temporal" / "it_security_support_agent"
SOURCE = (
    REPO
    / "content"
    / "playbooks"
    / "it_security_support_agent"
    / "playbook.cacao.json"
)
WORKFLOW_GOLDEN = EXAMPLE / "workflow.temporal.py"
MIRROR = EXAMPLE / "playbook.cacao.json"


def test_workflow_golden_is_committed() -> None:
    assert WORKFLOW_GOLDEN.exists(), f"missing golden: {WORKFLOW_GOLDEN}"
    assert WORKFLOW_GOLDEN.stat().st_size > 0


def test_mirrored_playbook_matches_canonical() -> None:
    """The mirrored example copy of playbook.cacao.json must stay
    byte-identical to the canonical source — the regenerate.sh script
    copies the canonical playbook into the example dir on every run."""
    assert MIRROR.read_bytes() == SOURCE.read_bytes(), (
        "examples/temporal/it_security_support_agent/playbook.cacao.json "
        "drifted from the canonical content/playbooks/"
        "it_security_support_agent/playbook.cacao.json. Regenerate "
        "via `./examples/temporal/it_security_support_agent/regenerate.sh`."
    )


def test_temporal_workflow_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = emit_temporal(playbook)
    expected = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "it_security_support_agent Temporal workflow drifted. "
        "Regenerate via "
        "`./examples/temporal/it_security_support_agent/regenerate.sh` "
        "and commit the new bytes alongside the emitter change."
    )


def test_temporal_workflow_emit_is_deterministic() -> None:
    playbook = parse_file(SOURCE)
    assert emit_temporal(playbook) == emit_temporal(playbook)
