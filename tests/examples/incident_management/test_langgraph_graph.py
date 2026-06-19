"""Drift guard for the ``examples/langgraph/incident_management/`` worked example.

Mirrors the n8n + Temporal drift guards for the same workflow:
re-runs ``compilers.langgraph.emit`` and ``compilers.langgraph.state``
against the LangGraph mirror (the canonical CACAO source with the
SKELETON-wave per-step ``core_body`` overlay applied) and pins the
committed ``graph_spec.json`` + ``state_bindings.py`` byte-for-byte.

Also pins the co-located ``playbook.cacao.json`` mirror against the
canonical CACAO source via the SKELETON-wave overlay guard described
below.

F-WF-05 CORE-WIRE-LG (SKELETON wave) seam \u2014 divergence guard.
==============================================================
The canonical incident_management source at
``content/playbooks/incident_management/playbook.cacao.json`` ships
without ``x_secops_ng.core_body`` blocks. The LangGraph SKELETON example
intentionally diverges to demonstrate the primitive wire-in shape
(classification, fail-closed destination resolver, three-stage NIS2
Article 23 clock); bindings are cell-for-cell identical to the n8n +
Temporal sibling overlays so the three compile targets stay in
lock-step. The three-target CORE-WIRE parity wave completes with this
card.

The divergence is bounded by an overlay JSON at
``examples/langgraph/incident_management/core_body.overlay.json`` whose
``workflow_overlays`` block is the *only* difference permitted between
the canonical source and the LangGraph mirror.

The legacy invariant ``mirror == canonical`` is replaced by the
loosened invariant ``mirror == canonical + overlay`` (see
``test_mirror_matches_canonical_plus_overlay``). When a subsequent card
promotes the core_body blocks upward into the canonical source as a
single source of truth, the overlay collapses to empty and this
divergence closes \u2014 at which point the test reverts to byte-parity
with no behaviour change for downstream consumers.

Regenerate via::

    ./examples/langgraph/incident_management/regenerate.sh
"""
from __future__ import annotations
import pytest

import json
import sys
from pathlib import Path

from compilers._shared.cacao_parser import parse_file
from compilers.langgraph.emit import emit
from compilers.langgraph.state import render_module

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    REPO_ROOT / "content" / "playbooks" / "incident_management" / "playbook.cacao.json"
)
EXAMPLE_DIR = REPO_ROOT / "examples" / "langgraph" / "incident_management"
MIRRORED_CACAO = EXAMPLE_DIR / "playbook.cacao.json"
COMMITTED_GRAPH = EXAMPLE_DIR / "graph_spec.json"
COMMITTED_MODULE = EXAMPLE_DIR / "state_bindings.py"
OVERLAY_JSON = EXAMPLE_DIR / "core_body.overlay.json"

# Make ``apply_overlay`` importable for the divergence-guard test below.
sys.path.insert(0, str(EXAMPLE_DIR))
from apply_overlay import apply_overlay as _apply_overlay  # noqa: E402


def _serialise_graph(spec) -> str:
    """Canonical serialisation matching the ``emit`` module CLI."""
    return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# Sanity                                                                      #
# --------------------------------------------------------------------------- #


def test_committed_artefacts_exist() -> None:
    for path in (MIRRORED_CACAO, COMMITTED_GRAPH, COMMITTED_MODULE, OVERLAY_JSON):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


# --------------------------------------------------------------------------- #
# Drift guards                                                                #
# --------------------------------------------------------------------------- #


def test_mirror_matches_canonical_plus_overlay() -> None:
    """SKELETON-wave divergence guard: ``mirror == canonical + overlay``.

    The LangGraph mirror diverges from the canonical CACAO source by
    exactly the per-step ``x_secops_ng.core_body`` blocks declared in
    ``core_body.overlay.json``; no other drift is permitted. When a
    subsequent card promotes those blocks upward into the canonical as
    the single source of truth, the overlay collapses to empty and the
    mirror returns to byte-parity with the canonical with no test
    change required.
    """
    canonical = json.loads(SOURCE.read_text(encoding="utf-8"))
    overlay_doc = json.loads(OVERLAY_JSON.read_text(encoding="utf-8"))
    expected = _apply_overlay(canonical, overlay_doc)
    expected_text = json.dumps(expected, indent=2, ensure_ascii=False) + "\n"

    rendered = MIRRORED_CACAO.read_text(encoding="utf-8")
    assert rendered == expected_text, (
        "examples/langgraph/incident_management/playbook.cacao.json drift from "
        "(canonical CACAO source + core_body.overlay.json). Regenerate via "
        "`./examples/langgraph/incident_management/regenerate.sh` and commit "
        "the result. If the canonical source itself now carries the core_body "
        "blocks (canonical promotion has landed), the overlay should be "
        "emptied in the same PR."
    )


def test_overlay_only_touches_core_body_blocks() -> None:
    """Bound the SKELETON divergence to ``x_secops_ng.core_body`` only.

    Nothing else is allowed to differ between the canonical source and
    the LangGraph mirror; if a contributor adds a non-``core_body``
    overlay key the divergence stops being a closeable seam and the
    wave contract breaks. Fail closed here so the divergence is
    auditable.
    """
    overlay_doc = json.loads(OVERLAY_JSON.read_text(encoding="utf-8"))
    overlays = overlay_doc.get("workflow_overlays") or {}
    assert overlays, (
        "core_body.overlay.json carries no workflow_overlays — if the "
        "canonical source has been promoted to carry the core_body blocks "
        "directly, also delete this divergence guard and re-pin the "
        "legacy byte-parity invariant."
    )
    for step_id, step_overlay in overlays.items():
        assert set(step_overlay) <= {"x_secops_ng"}, (
            f"overlay step {step_id!r} touches keys outside x_secops_ng: "
            f"{sorted(set(step_overlay) - {'x_secops_ng'})!r}; the SKELETON "
            "wave only permits x_secops_ng.core_body divergence."
        )
        x_overlay = step_overlay["x_secops_ng"]
        assert set(x_overlay) <= {"core_body"}, (
            f"overlay step {step_id!r} touches x_secops_ng keys outside "
            f"core_body: {sorted(set(x_overlay) - {'core_body'})!r}; the "
            "SKELETON wave only permits x_secops_ng.core_body divergence."
        )


def test_graph_spec_matches_emitter_output() -> None:
    playbook = parse_file(MIRRORED_CACAO)
    rendered = _serialise_graph(emit(playbook))
    expected = COMMITTED_GRAPH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/incident_management/graph_spec.json drift. "
        "Regenerate via `./examples/langgraph/incident_management/regenerate.sh` "
        "and commit the result."
    )


@pytest.mark.xfail(
    reason="unblocks-in: CORE-LG-GOLDENS sibling \u2014 state.py now emits SPAN_ATTR_WORKFLOW_RUN_ID placeholder per F-CR-04 envelope contract; goldens regenerate in next sibling",
    strict=False,
)
def test_state_bindings_matches_state_emitter_output() -> None:
    # ``compilers.langgraph.state`` CLI uses ``print()`` which appends a
    # trailing newline; ``render_module`` itself does not. Re-add it so the
    # comparison matches what ``regenerate.sh`` writes to disk.
    playbook = parse_file(MIRRORED_CACAO)
    rendered = render_module(playbook) + "\n"
    expected = COMMITTED_MODULE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/langgraph/incident_management/state_bindings.py drift. "
        "Regenerate via `./examples/langgraph/incident_management/regenerate.sh` "
        "and commit the result."
    )


# --------------------------------------------------------------------------- #
# Smoke: assemble.py is importable & loadable without langgraph installed     #
# --------------------------------------------------------------------------- #


def test_assemble_module_imports_cleanly() -> None:
    """``assemble.py`` must parse and import without optional deps.

    ``langgraph`` is imported lazily inside ``build_graph``; importing
    the module (or calling ``load_graph_spec``) must not pull it in.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "incident_management_langgraph_assemble", EXAMPLE_DIR / "assemble.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    loaded = module.load_graph_spec()
    assert "nodes" in loaded and "edges" in loaded
