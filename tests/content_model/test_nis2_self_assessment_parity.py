"""F-WF-NIS2-SELF-ASSESS CORE — cross-target byte-parity contract test.

Asserts that the same canonical CACAO playbook at
``content/playbooks/nis2_self_assessment/playbook.cacao.json`` produces
the byte-identical worked-example artifacts shipped under all three
reference compile targets:

- ``examples/n8n/nis2_self_assessment/workflow.n8n.json``
- ``examples/temporal/nis2_self_assessment/workflow.temporal.py``
- ``examples/langgraph/nis2_self_assessment/graph_spec.json``

The per-target golden tests under ``tests/examples/{n8n,temporal,
langgraph}/nis2_self_assessment/`` already pin each emitter's output
against its committed artifact. This module closes the parity contract
from the other side: it re-parses the canonical CACAO source, re-runs
each emitter through its documented serialisation path, and asserts
byte equality against every committed target artifact in one place.

Together with the per-target goldens, this guarantees the three
compile-target emissions are a byte-deterministic regeneration of the
same evidence-tree context, not hand-edited copies — the G-03
three-target parity contract for the ``nis2_self_assessment`` playbook
(NIS2 Art. 21(2) whole-Article operator self-assessment roll-up).

If an emitter change is intentional, regenerate the worked examples
via each target's ``regenerate.sh`` and commit the updated bytes
alongside the emitter change.
"""
from __future__ import annotations

import json
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit as emit_langgraph
from compilers.n8n.emit import emit as emit_n8n
from compilers.temporal.emit import emit_file as emit_temporal_file

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "nis2_self_assessment"
    / "playbook.cacao.json"
)
N8N_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "n8n"
    / "nis2_self_assessment"
    / "workflow.n8n.json"
)
TEMPORAL_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "temporal"
    / "nis2_self_assessment"
    / "workflow.temporal.py"
)
LANGGRAPH_GOLDEN = (
    REPO_ROOT
    / "examples"
    / "langgraph"
    / "nis2_self_assessment"
    / "graph_spec.json"
)


def _serialise_n8n(payload: dict) -> str:
    """Match ``python -m tools.compile --target n8n`` (indent=2)."""
    return json.dumps(payload, indent=2) + "\n"


def _serialise_langgraph(payload: dict) -> str:
    """Match ``python -m compilers.langgraph.emit`` (indent=2, sort_keys=True)."""
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# Per-target byte-parity                                                      #
# --------------------------------------------------------------------------- #


def test_n8n_workflow_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_n8n(emit_n8n(playbook))
    expected = N8N_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "nis2_self_assessment n8n example drifted. Regenerate via "
        "`./examples/n8n/nis2_self_assessment/regenerate.sh` and commit "
        "alongside the change."
    )


def test_temporal_workflow_matches_golden() -> None:
    rendered = emit_temporal_file(SOURCE)
    expected = TEMPORAL_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "nis2_self_assessment Temporal example drifted. Regenerate via "
        "`./examples/temporal/nis2_self_assessment/regenerate.sh` and "
        "commit alongside the change."
    )


def test_langgraph_graph_spec_matches_golden() -> None:
    playbook = parse_file(SOURCE)
    rendered = _serialise_langgraph(emit_langgraph(playbook).to_dict())
    expected = LANGGRAPH_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "nis2_self_assessment LangGraph example drifted. Regenerate via "
        "`./examples/langgraph/nis2_self_assessment/regenerate.sh` and "
        "commit alongside the change."
    )


# --------------------------------------------------------------------------- #
# Cross-target invariants                                                     #
# --------------------------------------------------------------------------- #


def test_emit_is_deterministic_across_compilers() -> None:
    """Every emitter yields identical bytes when re-run on the same source."""
    playbook = parse_file(SOURCE)
    assert _serialise_n8n(emit_n8n(playbook)) == _serialise_n8n(emit_n8n(playbook))
    assert emit_temporal_file(SOURCE) == emit_temporal_file(SOURCE)
    assert _serialise_langgraph(
        emit_langgraph(playbook).to_dict()
    ) == _serialise_langgraph(emit_langgraph(playbook).to_dict())


def test_step_ids_are_shared_across_targets() -> None:
    """CACAO step ids surface identically in the n8n and LangGraph goldens.

    The Temporal stub encodes step ids in activity docstrings (verified
    in its per-target golden); the byte-preserving surfaces here are
    n8n node ids and LangGraph GraphSpec ``step_id`` fields.

    n8n preserves the full CACAO workflow key set as node ids (including
    the ``start--`` and ``end--`` sentinels). The LangGraph emitter
    models those two sentinels structurally via ``entry`` (the target of
    ``start--…``'s ``on_completion``) and ``end_sentinel`` (the
    ``__END__`` edge dst), so its ``nodes`` array carries only the
    intermediate action step ids. Both surfaces must therefore be a
    byte-identical projection of the same canonical CACAO step space.
    """
    canonical = set(
        json.loads(SOURCE.read_text(encoding="utf-8"))["workflow"].keys()
    )
    action_ids = {
        key
        for key in canonical
        if not (key.startswith("start--") or key.startswith("end--"))
    }

    n8n_ids = {
        node["id"]
        for node in json.loads(N8N_GOLDEN.read_text(encoding="utf-8"))["nodes"]
    }
    assert n8n_ids == canonical, (
        f"n8n node ids drift from CACAO step ids. "
        f"missing: {sorted(canonical - n8n_ids)!r}; "
        f"extra: {sorted(n8n_ids - canonical)!r}"
    )

    langgraph_ids = {
        node["step_id"]
        for node in json.loads(LANGGRAPH_GOLDEN.read_text(encoding="utf-8"))["nodes"]
    }
    assert langgraph_ids == action_ids, (
        f"LangGraph GraphSpec step ids drift from CACAO action step ids. "
        f"missing: {sorted(action_ids - langgraph_ids)!r}; "
        f"extra: {sorted(langgraph_ids - action_ids)!r}"
    )


def test_example_artifacts_are_committed() -> None:
    for path in (N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"
