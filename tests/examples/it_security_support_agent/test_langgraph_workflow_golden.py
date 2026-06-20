"""F-WF-12 CORE-FANOUT-LANGGRAPH — byte-parity golden for the LangGraph workflow.

The committed
``examples/langgraph/it_security_support_agent/graph_spec.json`` is the
LangGraph emitter's topology output for the canonical CACAO playbook at
``content/playbooks/it_security_support_agent/playbook.cacao.json``;
the committed ``state_bindings.py`` is the matching state-schema +
tool-binding output; the committed ``_audit_mirror.py`` is the
dependency-free audit-mirror sibling emitted alongside.

This module pins all three artefacts against the emitter so a refactor
of the LangGraph compiler that silently changes serialisation (or a
drift between the canonical playbook and the mirrored example copy)
gets caught at the byte level.

If the change is intentional, regenerate the example::

    ./examples/langgraph/it_security_support_agent/regenerate.sh

and commit the updated bytes alongside the emitter change.

The interaction-evidence byte-parity golden and the immutable
interaction-evidence fixture are owned by the sibling module
``test_langgraph_interaction_evidence`` — this module covers the
workflow graph + state bindings only.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit as emit_langgraph
from compilers.langgraph.state import render_module as render_state_module

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "langgraph" / "it_security_support_agent"
SOURCE = (
    REPO
    / "content"
    / "playbooks"
    / "it_security_support_agent"
    / "playbook.cacao.json"
)
GRAPH_GOLDEN = EXAMPLE / "graph_spec.json"
STATE_GOLDEN = EXAMPLE / "state_bindings.py"
AUDIT_MIRROR_GOLDEN = EXAMPLE / "_audit_mirror.py"
MIRROR = EXAMPLE / "playbook.cacao.json"


def _serialise_graph_spec(payload: dict) -> str:
    """Match ``python -m compilers.langgraph.emit`` (indent=2, sort_keys, trailing newline)."""
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def test_graph_golden_is_committed() -> None:
    assert GRAPH_GOLDEN.exists(), f"missing golden: {GRAPH_GOLDEN}"
    assert GRAPH_GOLDEN.stat().st_size > 0


def test_state_bindings_golden_is_committed() -> None:
    assert STATE_GOLDEN.exists(), f"missing golden: {STATE_GOLDEN}"
    assert STATE_GOLDEN.stat().st_size > 0


def test_audit_mirror_golden_is_committed() -> None:
    assert AUDIT_MIRROR_GOLDEN.exists(), (
        f"missing golden: {AUDIT_MIRROR_GOLDEN}"
    )
    assert AUDIT_MIRROR_GOLDEN.stat().st_size > 0


def test_mirrored_playbook_matches_canonical() -> None:
    """The mirrored example copy of playbook.cacao.json must stay
    byte-identical to the canonical source — the regenerate.sh script
    copies the canonical playbook into the example dir on every run."""
    assert MIRROR.read_bytes() == SOURCE.read_bytes(), (
        "examples/langgraph/it_security_support_agent/playbook.cacao.json "
        "drifted from the canonical content/playbooks/"
        "it_security_support_agent/playbook.cacao.json. Regenerate "
        "via `./examples/langgraph/it_security_support_agent/regenerate.sh`."
    )


def test_langgraph_graph_spec_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    spec = emit_langgraph(playbook)
    rendered = _serialise_graph_spec(spec.to_dict())
    expected = GRAPH_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "it_security_support_agent LangGraph graph_spec.json drifted. "
        "Regenerate via "
        "`./examples/langgraph/it_security_support_agent/regenerate.sh` "
        "and commit the new bytes alongside the emitter change."
    )


def test_langgraph_state_bindings_match_golden() -> None:
    playbook = parse_file(SOURCE)
    # The state emitter CLI prints the rendered module followed by a
    # trailing newline (``print(...)``). Mirror that here so the
    # rendered bytes round-trip against the committed golden, which
    # was written by the CLI via the regenerate.sh path.
    rendered = render_state_module(playbook) + "\n"
    expected = STATE_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "it_security_support_agent LangGraph state_bindings.py "
        "drifted. Regenerate via "
        "`./examples/langgraph/it_security_support_agent/regenerate.sh` "
        "and commit the new bytes alongside the emitter change."
    )


def test_langgraph_audit_mirror_matches_emitter(tmp_path: Path) -> None:
    """The committed ``_audit_mirror.py`` must agree with what the CLI emits.

    The audit-mirror sibling is dependency-free and shared across
    compile targets via ``compilers._shared.audit_mirror_cli``; the
    regenerate.sh script materialises it alongside the LangGraph
    artefacts so the operator-facing example is self-contained. A
    drift here means the shared audit-mirror module was edited but
    the worked example was not refreshed.
    """
    out_path = tmp_path / "_audit_mirror.py"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "compilers._shared.audit_mirror_cli",
            "--out",
            str(out_path),
        ],
        cwd=REPO,
        check=True,
    )
    assert out_path.read_bytes() == AUDIT_MIRROR_GOLDEN.read_bytes(), (
        "examples/langgraph/it_security_support_agent/_audit_mirror.py "
        "drifted from compilers/_shared/audit_mirror_cli emission. "
        "Refresh via "
        "`./examples/langgraph/it_security_support_agent/regenerate.sh`."
    )


def test_langgraph_graph_spec_emit_is_deterministic() -> None:
    playbook = parse_file(SOURCE)
    first = _serialise_graph_spec(emit_langgraph(playbook).to_dict())
    second = _serialise_graph_spec(emit_langgraph(playbook).to_dict())
    assert first == second


def test_langgraph_state_bindings_emit_is_deterministic() -> None:
    playbook = parse_file(SOURCE)
    assert render_state_module(playbook) == render_state_module(playbook)
