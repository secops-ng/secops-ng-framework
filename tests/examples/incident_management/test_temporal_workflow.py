"""Drift guard for the ``examples/temporal/incident-management/`` worked example.

Mirrors the phishing-triage temporal example test: re-emits the Temporal
workflow stub from the canonical CACAO playbook and pins the result
byte-for-byte against the committed
``examples/temporal/incident-management/workflow.temporal.py``. Adds an
activity-name \u2194 CACAO action-id parity check so the one-to-one
mirroring contract documented in
``examples/temporal/incident-management/README.md`` is enforced by
tests, not by convention.

Also pins the co-located ``playbook.cacao.json`` mirror against the
canonical CACAO source via the SKELETON-wave overlay guard described
below.

F-WF-05 CORE-WIRE-TMPRL (SKELETON wave) seam \u2014 divergence guard.
==================================================================
The canonical incident-management source at
``content/playbooks/incident-management/playbook.cacao.json`` ships
without ``x_secops_ng.core_body`` blocks. The Temporal SKELETON example
intentionally diverges to demonstrate the primitive wire-in shape
(classification, fail-closed destination resolver, three-stage NIS2
Article 23 clock) ahead of the sibling LangGraph CORE-WIRE card. The
divergence is bounded by an overlay JSON at
``examples/temporal/incident-management/core_body.overlay.json`` whose
``workflow_overlays`` block is the *only* difference permitted between
the canonical source and the Temporal mirror. The bindings are
cell-for-cell identical to the n8n sibling overlay so the three compile
targets stay in lock-step.

The legacy invariant ``mirror == canonical`` is replaced by the
loosened invariant ``mirror == canonical + overlay`` (see
``test_mirror_matches_canonical_plus_overlay``). When the CORE-WIRE-LG
sibling card lands and the canonical gains the core_body blocks as a
single source of truth, the overlay collapses to empty and this
divergence closes \u2014 at which point the test reverts to byte-parity
with no behaviour change for downstream consumers.

Regenerate via::

    ./examples/temporal/incident-management/regenerate.sh
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from compilers.temporal.emit import emit_file

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    REPO_ROOT / "content" / "playbooks" / "incident-management" / "playbook.cacao.json"
)
EXAMPLE_DIR = REPO_ROOT / "examples" / "temporal" / "incident-management"
WORKED_EXAMPLE = EXAMPLE_DIR / "workflow.temporal.py"
MIRRORED_CACAO = EXAMPLE_DIR / "playbook.cacao.json"
OVERLAY_JSON = EXAMPLE_DIR / "core_body.overlay.json"

# Make ``apply_overlay`` importable for the divergence-guard test below.
sys.path.insert(0, str(EXAMPLE_DIR))
from apply_overlay import apply_overlay as _apply_overlay  # noqa: E402

_ACTIVITY_STEP_TYPES = {"action"}
_ACTIVITY_DEFN_RE = re.compile(
    r"@activity\.defn\nasync def (?P<name>[A-Za-z_][A-Za-z_0-9]*)\("
    r"[^)]*\)[^:]*:\n"
    r'    """[^"]*?\n\n'
    r"    CACAO step_id: (?P<step_id>[^\n]+)\n",
    re.DOTALL,
)


def test_committed_artefacts_exist() -> None:
    for path in (MIRRORED_CACAO, WORKED_EXAMPLE, OVERLAY_JSON):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


def test_worked_example_matches_emitter_output() -> None:
    rendered = emit_file(MIRRORED_CACAO)
    expected = WORKED_EXAMPLE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/temporal/incident-management/workflow.temporal.py drifted "
        "from the Temporal emitter output. Regenerate via "
        "`./examples/temporal/incident-management/regenerate.sh` and commit "
        "the new bytes."
    )


def test_mirror_matches_canonical_plus_overlay() -> None:
    """SKELETON-wave divergence guard: ``mirror == canonical + overlay``.

    The Temporal mirror diverges from the canonical CACAO source by
    exactly the per-step ``x_secops_ng.core_body`` blocks declared in
    ``core_body.overlay.json``; no other drift is permitted. When the
    sibling CORE-WIRE-LG card lands and the canonical source gains the
    ``core_body`` blocks as the single source of truth, the overlay
    collapses to empty and the mirror returns to byte-parity with the
    canonical with no test change required.
    """
    canonical = json.loads(SOURCE.read_text(encoding="utf-8"))
    overlay_doc = json.loads(OVERLAY_JSON.read_text(encoding="utf-8"))
    expected = _apply_overlay(canonical, overlay_doc)
    expected_text = json.dumps(expected, indent=2, ensure_ascii=False) + "\n"

    rendered = MIRRORED_CACAO.read_text(encoding="utf-8")
    assert rendered == expected_text, (
        "examples/temporal/incident-management/playbook.cacao.json drift from "
        "(canonical CACAO source + core_body.overlay.json). Regenerate via "
        "`./examples/temporal/incident-management/regenerate.sh` and commit "
        "the result. If the canonical source itself now carries the core_body "
        "blocks (CORE-WIRE-LG has landed), the overlay should be emptied in "
        "the same PR."
    )


def test_overlay_only_touches_core_body_blocks() -> None:
    """Bound the SKELETON divergence to ``x_secops_ng.core_body`` only.

    Nothing else is allowed to differ between the canonical source and
    the Temporal mirror; if a contributor adds a non-``core_body``
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


def _action_step_ids_from_cacao() -> list[str]:
    playbook = json.loads(MIRRORED_CACAO.read_text(encoding="utf-8"))
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
    assert emit_file(MIRRORED_CACAO) == emit_file(MIRRORED_CACAO)
