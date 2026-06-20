"""Regenerate scaffold for examples/n8n/it_security_support_agent.

F-WF-12 SKELETON-FANOUT-N8N: scaffold-only. At this layer the canonical
it_security_support_agent playbook ships with declarative placeholder
step bodies (no ``core_body`` bindings), so there is no n8n compiler
emitter binding to drive and no representative interaction-evidence
artefact to materialise. The script mirrors the canonical CACAO source
into this directory so the SKELETON example tracks the canonical
playbook, and is otherwise a no-op pending the CORE-FANOUT-N8N sibling
that follows this SKELETON.

Run from the repository root::

    PYTHONPATH=. python examples/n8n/it_security_support_agent/regenerate.py

The committed ``evidence/`` placeholder will be replaced by one
representative interaction-evidence artifact (shape:
``schemas/evidence/incidents.schema.json``, reused from F-CP-02) when
CORE-FANOUT-N8N lands.
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
        f"it_security_support_agent (n8n): mirrored canonical CACAO source -> "
        f"{MIRROR.relative_to(REPO_ROOT)}."
    )
    print("Workflow emission and interaction-evidence artefact deferred to CORE-FANOUT-N8N.")


if __name__ == "__main__":
    main()
