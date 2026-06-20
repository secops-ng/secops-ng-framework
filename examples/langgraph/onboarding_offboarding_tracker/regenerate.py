"""Regenerate scaffold for examples/langgraph/onboarding_offboarding_tracker.

F-WF-11 SKELETON-FANOUT-LG: scaffold-only. At this layer the canonical
onboarding_offboarding_tracker playbook ships with declarative
placeholder step bodies (no ``core_body`` bindings), so there is no
langgraph compiler emitter binding to drive and no representative
access-evidence artefact to materialise. The script mirrors the
canonical CACAO source into this directory so the SKELETON example
tracks the canonical playbook, and is otherwise a no-op pending the
F-WF-11 CORE-FANOUT-LG sibling card.

Run from the repository root::

    PYTHONPATH=. python examples/langgraph/onboarding_offboarding_tracker/regenerate.py

The committed ``evidence/`` placeholder will be replaced by one
representative access-evidence artifact (shape:
``schemas/evidence/access.schema.json``, reused from F-CP-07) when
CORE-FANOUT-LG lands.
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CANON = REPO_ROOT / "content" / "playbooks" / "onboarding_offboarding_tracker" / "playbook.cacao.json"
MIRROR = HERE / "playbook.cacao.json"


def main() -> None:
    shutil.copyfile(CANON, MIRROR)
    print(
        f"onboarding_offboarding_tracker (langgraph): mirrored canonical CACAO source -> "
        f"{MIRROR.relative_to(REPO_ROOT)}."
    )
    print("Workflow emission and access-evidence artefact deferred to F-WF-11 CORE-FANOUT-LG.")


if __name__ == "__main__":
    main()
