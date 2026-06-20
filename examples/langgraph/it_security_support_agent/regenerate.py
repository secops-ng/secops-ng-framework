"""Regenerate scaffold for examples/langgraph/it_security_support_agent.

F-WF-12 SKELETON-FANOUT-LG: scaffold for the example directory. The
worked LangGraph artefacts (graph_spec.json, state_bindings.py,
_audit_mirror.py) are emitted from the canonical CACAO source by the
sibling ``regenerate.sh`` driving the LangGraph emitter directly; this
Python module is a placeholder pending the CORE-FANOUT-LG sibling that
follows this SKELETON.

Run from the repository root::

    PYTHONPATH=. python examples/langgraph/it_security_support_agent/regenerate.py

The committed ``evidence/`` placeholder will be replaced by one
representative interaction-evidence artifact (shape:
``schemas/evidence/incidents.schema.json``, reused from F-CP-02) when
CORE-FANOUT-LG lands.
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CANON = REPO_ROOT / "content" / "playbooks" / "it_security_support_agent" / "playbook.cacao.json"
MIRROR = HERE / "playbook.cacao.json"


def main() -> None:
    shutil.copyfile(CANON, MIRROR)
    print(
        f"it_security_support_agent (langgraph): mirrored canonical CACAO source -> "
        f"{MIRROR.relative_to(REPO_ROOT)}."
    )
    print(
        "Run regenerate.sh to re-emit GraphSpec + state bindings stub + audit-mirror sibling."
    )
    print("Workflow primitive bindings and interaction-evidence artefact deferred to CORE-FANOUT-LG.")


if __name__ == "__main__":
    main()
