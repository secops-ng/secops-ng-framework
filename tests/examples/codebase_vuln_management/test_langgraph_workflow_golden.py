"""F-WF-07 CORE-FANOUT-LG — byte-parity golden for the LangGraph workflow.

The committed
``examples/langgraph/codebase-vuln-management/graph_spec.json`` and
``examples/langgraph/codebase-vuln-management/state_bindings.py`` are
the LangGraph compiler's output for the canonical CACAO playbook at
``content/playbooks/codebase-vuln-management/playbook.cacao.json``.

This module pins both artifacts against the emitters so a refactor of
the LangGraph compiler that silently changes serialisation (or a drift
between the canonical playbook and the mirrored example copy) gets
caught at the byte level. Tool-function-name <-> CACAO action-id parity
is verified too — every CACAO action step gets exactly one ``@tool``
async def whose docstring records the originating ``step_id``.

If the change is intentional, regenerate the example::

    ./examples/langgraph/codebase-vuln-management/regenerate.sh

and commit the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO = Path(__file__).resolve().parents[3]
EXAMPLE = REPO / "examples" / "langgraph" / "codebase-vuln-management"
SOURCE = (
    REPO / "content" / "playbooks" / "codebase-vuln-management" / "playbook.cacao.json"
)
GRAPH_GOLDEN = EXAMPLE / "graph_spec.json"
STATE_GOLDEN = EXAMPLE / "state_bindings.py"
MIRRORED_CACAO = EXAMPLE / "playbook.cacao.json"

_ACTION_STEP_TYPES = {"action"}
_TOOL_DEFN_RE = re.compile(
    r"@tool\nasync def (?P<name>[A-Za-z_][A-Za-z_0-9]*)\("
    r"[^)]*\)[^:]*:\n"
    r'    """[^"]*?\n\n'
    r"    CACAO step_id : (?P<step_id>[^\n]+)\n",
    re.DOTALL,
)


def _serialise_graph(spec) -> str:
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


def test_example_artifacts_are_committed() -> None:
    for path in (GRAPH_GOLDEN, STATE_GOLDEN, MIRRORED_CACAO):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == SOURCE.read_bytes(), (
        "examples/langgraph/codebase-vuln-management/playbook.cacao.json "
        "drifted from the canonical content/playbooks/codebase-vuln-management/"
        "playbook.cacao.json. Regenerate via "
        "`./examples/langgraph/codebase-vuln-management/regenerate.sh`."
    )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_graph(emit(playbook))
    expected = GRAPH_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/codebase-vuln-management/graph_spec.json drifted "
        "from the LangGraph emitter output. Regenerate via "
        "`./examples/langgraph/codebase-vuln-management/regenerate.sh` and "
        "commit the new bytes."
    )


def test_state_bindings_matches_state_emitter_output() -> None:
    # ``compilers.langgraph.state`` CLI uses ``print()`` which appends a
    # trailing newline; ``render_module`` itself does not.
    playbook = parse_file(SOURCE)
    rendered = render_module(playbook) + "\n"
    expected = STATE_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/codebase-vuln-management/state_bindings.py "
        "drifted from the LangGraph state emitter output. Regenerate via "
        "`./examples/langgraph/codebase-vuln-management/regenerate.sh` and "
        "commit the new bytes."
    )


def test_emit_is_deterministic() -> None:
    playbook = parse_file(SOURCE)
    assert _serialise_graph(emit(playbook)) == _serialise_graph(emit(playbook))
    assert render_module(playbook) == render_module(playbook)


def _action_step_ids_from_cacao() -> list[str]:
    playbook = json.loads(SOURCE.read_text(encoding="utf-8"))
    return [
        step_id
        for step_id, step in playbook["workflow"].items()
        if step.get("type") in _ACTION_STEP_TYPES
    ]


def _tool_blocks_from_stub() -> list[tuple[str, str]]:
    """Return ``(tool_function_name, cacao_step_id)`` tuples in source order."""
    text = STATE_GOLDEN.read_text(encoding="utf-8")
    return [(m.group("name"), m.group("step_id")) for m in _TOOL_DEFN_RE.finditer(text)]


def test_tool_names_mirror_cacao_action_ids() -> None:
    """Every CACAO action step gets exactly one ``@tool`` async def whose
    docstring records the originating ``step_id``, and vice versa.
    """
    cacao_action_ids = set(_action_step_ids_from_cacao())
    stub_blocks = _tool_blocks_from_stub()
    stub_step_ids = {step_id for _, step_id in stub_blocks}

    missing = cacao_action_ids - stub_step_ids
    assert not missing, (
        f"CACAO action step ids without a matching LangGraph @tool: "
        f"{sorted(missing)}"
    )
    extra = stub_step_ids - cacao_action_ids
    assert not extra, (
        f"LangGraph @tool wrappers without a matching CACAO action step id: "
        f"{sorted(extra)}"
    )
    assert len(stub_blocks) == len(cacao_action_ids), (
        "duplicate @tool wrapper for the same CACAO step id in the stub"
    )

    function_names = [name for name, _ in stub_blocks]
    assert len(function_names) == len(set(function_names)), (
        "duplicate @tool function names in the stub"
    )


def test_state_bindings_call_real_primitives() -> None:
    """CORE-FANOUT-LG bar: tool bodies call the deterministic primitives
    in ``content.playbooks.codebase_vuln_management.primitives``, not
    ``NotImplementedError`` placeholders.
    """
    text = STATE_GOLDEN.read_text(encoding="utf-8")
    # The agentic-extension hook (``llm_step``) intentionally raises
    # NotImplementedError — integrators wire it to their own LLM
    # provider. Every CACAO @tool action body, however, must call its
    # deterministic primitive. Scan the @tool blocks specifically.
    tool_block_re = re.compile(
        r"^@tool\nasync def [A-Za-z_][A-Za-z_0-9]*\([^)]*\)[^:]*:\n"
        r"(?:(?!^@tool|^async def|^def |^STATE_SCHEMA|^TOOLS|^AGENTIC_HOOK).*\n)*",
        re.MULTILINE,
    )
    for match in tool_block_re.finditer(text):
        block = match.group(0)
        assert "NotImplementedError" not in block, (
            f"a @tool action body still carries NotImplementedError — "
            f"CORE-FANOUT-LG requires every CACAO action body to call its "
            f"deterministic primitive. Offending block:\n{block[:400]}"
        )
    expected_primitives = (
        "from content.playbooks.codebase_vuln_management.primitives.sbom "
        "import pin_sbom_content_hash",
        "from content.playbooks.codebase_vuln_management.primitives.sbom "
        "import normalise_findings",
        "from content.playbooks.codebase_vuln_management.primitives."
        "disclosure_window import resolve_disclosure_window",
        "from content.playbooks.codebase_vuln_management.primitives."
        "timeline import build_disclosure_timeline_stub",
    )
    for fragment in expected_primitives:
        assert fragment in text, f"missing primitive call: {fragment}"


def test_assemble_module_imports_cleanly() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "codebase_vuln_management_langgraph_assemble", EXAMPLE / "assemble.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = module.load_graph_spec()
    assert "nodes" in loaded and "edges" in loaded
