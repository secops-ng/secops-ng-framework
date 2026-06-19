"""Regenerate scaffold for examples/langgraph/infra_posture_management.

F-WF-06 SKELETON-FANOUT-N8N: scaffold-only. At this layer the
canonical infra_posture_management playbook ships with declarative
placeholder step bodies (``x_secops_ng.core_body.placeholder: true``),
so there is no LangGraph compiler emitter binding to drive and no
representative posture-evidence artefact to materialise. The script
mirrors the canonical CACAO source into this directory so the
SKELETON example tracks the canonical playbook, and is otherwise a
no-op pending the F-WF-06 CORE-FANOUT-LG sibling card.

Run from the repository root::

    PYTHONPATH=. python examples/langgraph/infra_posture_management/regenerate.py

The committed ``evidence/`` placeholder will be replaced by one
representative posture-evidence artifact (shape:
``schemas/evidence/posture.schema.json``) when CORE-FANOUT-LG lands.
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CANON = REPO_ROOT / "content" / "playbooks" / "infra_posture_management" / "playbook.cacao.json"
MIRROR = HERE / "playbook.cacao.json"


def main() -> None:
    shutil.copyfile(CANON, MIRROR)
    print(
        f"infra_posture_management (langgraph): mirrored canonical CACAO source -> "
        f"{MIRROR.relative_to(REPO_ROOT)}."
    )
    print("Workflow emission and posture-evidence artefact deferred to F-WF-06 CORE-FANOUT-LG.")


if __name__ == "__main__":
    main()
