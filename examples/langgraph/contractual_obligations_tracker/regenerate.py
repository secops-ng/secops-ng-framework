"""Regenerate scaffold for examples/langgraph/contractual_obligations_tracker.

F-WF-10 SKELETON-FANOUT-LG: scaffold-only. At this layer the
canonical contractual_obligations_tracker playbook ships with declarative
placeholder step bodies (``x_secops_ng.core_body.placeholder: true``),
so there is no LangGraph compiler emitter binding to drive and no
representative obligation-evidence artefact to materialise. The script
mirrors the canonical CACAO source into this directory so the
SKELETON example tracks the canonical playbook, and is otherwise a
no-op pending the F-WF-10 CORE-FANOUT-LG sibling card.

Run from the repository root::

    PYTHONPATH=. python examples/langgraph/contractual_obligations_tracker/regenerate.py

The committed ``evidence/`` placeholder will be replaced by one
representative obligation-evidence artifact (shape:
``schemas/evidence/contractual-obligations.schema.json``) when
CORE-FANOUT-LG lands.
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CANON = REPO_ROOT / "content" / "playbooks" / "contractual_obligations_tracker" / "playbook.cacao.json"
MIRROR = HERE / "playbook.cacao.json"


def main() -> None:
    shutil.copyfile(CANON, MIRROR)
    print(
        f"contractual_obligations_tracker (langgraph): mirrored canonical CACAO source -> "
        f"{MIRROR.relative_to(REPO_ROOT)}."
    )
    print("Workflow emission and obligation-evidence artefact deferred to F-WF-10 CORE-FANOUT-LG.")


if __name__ == "__main__":
    main()
