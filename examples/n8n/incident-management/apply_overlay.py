"""Apply the SKELETON-wave per-step core_body overlay onto the canonical
CACAO source to produce the n8n mirror at this directory's
``playbook.cacao.json``.

F-WF-05 CORE-WIRE-N8N (SKELETON wave) seam: the canonical CACAO source
at ``content/playbooks/incident-management/playbook.cacao.json`` does
not yet carry ``x_secops_ng.core_body`` blocks. The n8n SKELETON example
diverges from the canonical to demonstrate the primitive wire-in shape
ahead of the sibling Temporal and LangGraph CORE-WIRE cards. When those
land, the canonical gets the core_body blocks promoted upward and this
overlay collapses to empty; the regenerate.sh script (and this module)
remain in place so the build path is stable across the seam closure.

The overlay JSON is documented at ``core_body.overlay.json``; its
``_meta.binding_layout`` enumerates the per-step bindings (classification
table, fail-closed destination resolver, three-stage NIS2 Article 23
stage clock) and ``_meta.wave_seam_closure_condition`` records when the
overlay can be deleted.

The overlay merge is a shallow deep-merge of ``x_secops_ng`` per step:
overlay keys are added on top of any canonical ``x_secops_ng`` block; for
SKELETON-stage incident-management the only overlay key is ``core_body``,
so the canonical's ``control_refs`` / ``telemetry_refs`` / ``metric_refs``
are preserved unchanged.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Merge ``overlay`` into a deep copy of ``base``.

    Dict values are merged recursively; non-dict overlay values replace
    whatever is in ``base`` at the same key. The base is not mutated.
    """
    out = copy.deepcopy(base)
    for key, overlay_value in overlay.items():
        if (
            key in out
            and isinstance(out[key], dict)
            and isinstance(overlay_value, dict)
        ):
            out[key] = _deep_merge(out[key], overlay_value)
        else:
            out[key] = copy.deepcopy(overlay_value)
    return out


def apply_overlay(
    canonical: dict[str, Any], overlay_doc: dict[str, Any]
) -> dict[str, Any]:
    """Return ``canonical`` with the per-step overlays applied.

    ``overlay_doc`` is the parsed ``core_body.overlay.json``. Its
    ``workflow_overlays`` key holds a mapping of CACAO step id ->
    partial step body to deep-merge onto the canonical step. Unknown
    step ids fail closed (raise ``KeyError``) so a typo in the overlay
    cannot silently drop a binding.
    """
    overlays = overlay_doc.get("workflow_overlays") or {}
    merged = copy.deepcopy(canonical)
    workflow = merged.get("workflow") or {}
    for step_id, step_overlay in overlays.items():
        if step_id not in workflow:
            raise KeyError(
                f"overlay references unknown CACAO step id {step_id!r}; "
                "canonical workflow has: " + ", ".join(sorted(workflow))
            )
        workflow[step_id] = _deep_merge(workflow[step_id], step_overlay)
    return merged


def _serialise(payload: dict[str, Any]) -> str:
    """Canonical serialisation matching ``tools.compile`` JSON output.

    ``ensure_ascii=False`` so the mirror preserves the canonical's
    non-ASCII characters (em-dashes, non-breaking spaces) verbatim
    rather than escaping them — the canonical source is the byte-level
    reference for everything outside the overlay-touched steps.
    """
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Apply the F-WF-05 CORE-WIRE-N8N SKELETON-wave per-step "
            "core_body overlay onto the canonical CACAO source."
        )
    )
    parser.add_argument(
        "--canonical",
        required=True,
        type=Path,
        help="Path to the canonical CACAO source.",
    )
    parser.add_argument(
        "--overlay",
        required=True,
        type=Path,
        help="Path to the overlay JSON.",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Path to write the n8n mirror to.",
    )
    args = parser.parse_args(argv)

    canonical = json.loads(args.canonical.read_text(encoding="utf-8"))
    overlay_doc = json.loads(args.overlay.read_text(encoding="utf-8"))
    merged = apply_overlay(canonical, overlay_doc)
    args.out.write_text(_serialise(merged), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
