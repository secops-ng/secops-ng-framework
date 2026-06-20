"""Regenerate driver for examples/n8n/it_security_support_agent.

F-WF-12 CORE-FANOUT-N8N-WIRE: the n8n workflow emitter is bound and
the five action bodies carry deterministic ``core_body`` bindings
into ``content.playbooks.it_security_support_agent.primitives.*``.
At this layer the script keeps the local CACAO mirror byte-identical
to the canonical playbook; ``regenerate.sh`` drives the unified
compile CLI to emit ``workflow.n8n.json`` directly.

The representative per-execution interaction-evidence artefact under
``evidence/`` (shape: ``schemas/evidence/incidents.schema.json``,
reused from F-CP-02) is materialised by the GOLDEN sibling that
follows this WIRE — that sibling owns the interaction-evidence
emitter wiring, the immutable fixture, and the byte-parity golden
test. This script is the WIRE-stage placeholder; it asserts the
canonical playbook is importable and the primitives package resolves
so a downstream GOLDEN sibling can rely on the binding being live.

Run from the repository root::

    PYTHONPATH=. python examples/n8n/it_security_support_agent/regenerate.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
CANON = (
    REPO_ROOT
    / "content"
    / "playbooks"
    / "it_security_support_agent"
    / "playbook.cacao.json"
)
MIRROR = HERE / "playbook.cacao.json"


def main() -> None:
    shutil.copyfile(CANON, MIRROR)

    # Sanity-check that the CORE primitives package resolves so the
    # core_body bindings in the canonical playbook are live. The
    # GOLDEN sibling will drive these primitives end-to-end against
    # the incidents-evidence schema.
    from content.playbooks.it_security_support_agent.primitives import (  # noqa: F401
        attempt_automated_resolution,
        build_interaction_artifact,
        classify_request,
        escalate_with_human_handoff,
        ingest_support_request,
    )

    print(
        "it_security_support_agent (n8n): mirrored canonical CACAO source -> "
        f"{MIRROR.relative_to(REPO_ROOT)}; primitives package resolves."
    )
    print(
        "Interaction-evidence artefact materialisation deferred to "
        "CORE-FANOUT-N8N-GOLDEN."
    )


if __name__ == "__main__":
    main()
