"""Regenerate the committed contractual-obligations-tracker worked example (LangGraph).

F-WF-10 CORE-FANOUT-LANGGRAPH — the contractual-obligations-tracker
workflow emits one obligation-evidence artifact per supplier contract
reviewed on a given execution. This script materialises one such
record for one representative execution by driving the LangGraph node
adapter at
``compilers.langgraph.evidence.emit_contractual_obligations_artifact_node``
exactly as a LangGraph integrator would: a state mapping carrying the
typed :class:`ContractualObligationsContext` and an
``evidence_output_dir`` is handed to the node function, the adapter
delegates to the framework-agnostic shared helper, and the partial
state update returned by the node carries the absolute artifact path
the rest of the graph attaches to its audit trail.

Inputs are pulled byte-identical from the Temporal sibling at
``examples/temporal/contractual_obligations_tracker/regenerate.py`` so
the per-target adapters write byte-identical records — every emission
runs through one shared helper, which is the F-WF-10 CORE invariant.
A cross-target byte-parity test under
``tests/examples/contractual_obligations_tracker/`` pins this.

Public-bar artifact: no individual personal names, no operator
branding, no internal infrastructure references on any free-text
field. Contract identifiers are role-shaped opaque operator ids;
obligation text is operator-canonicalised; owner is a role handle,
not a personal name.

Run from the repo root after any change to the contractual-obligations
shared emitter or the LangGraph node adapter::

    PYTHONPATH=. python examples/langgraph/contractual_obligations_tracker/regenerate.py

The committed ``obligation-evidence-record.json`` is the resulting
artifact renamed for human-friendly diffing; the deterministic
``<artifact_id>.json`` written by the node is the SHA-256-named
sibling of the same bytes.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

from compilers.langgraph.evidence import (
    emit_contractual_obligations_artifact_node,
)

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
SNAPSHOT = EVIDENCE_DIR / "obligation-evidence-record.json"
REPO = HERE.parents[2]
TEMPORAL_REGEN = (
    REPO
    / "examples"
    / "temporal"
    / "contractual_obligations_tracker"
    / "regenerate.py"
)


def _load_temporal_ctx():
    """Import the Temporal sibling's CTX without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "_contractual_obligations_tracker_temporal_regen", TEMPORAL_REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CTX


# Pull the typed context from the Temporal sibling so the LangGraph
# example is byte-identical to the n8n + Temporal siblings at the
# payload level. The cross-target byte-parity invariant lives in the
# tests; this just keeps the source of truth singular.
CTX = _load_temporal_ctx()


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "contractual_obligations_context": CTX,
        "evidence_output_dir": EVIDENCE_DIR,
    }
    update = emit_contractual_obligations_artifact_node(state)
    written = Path(update["contractual_obligations_artifact_path"])
    # The node writes <artifact_id>.json; copy to the stable
    # human-friendly filename the example commits for diffing.
    shutil.copyfile(written, SNAPSHOT)
    # Drop the sha-named twin so the committed tree only carries the
    # human-friendly snapshot.
    written.unlink()
    record = json.loads(SNAPSHOT.read_text("utf-8"))
    # Sanity check — execution-anchor shape carried through.
    assert record["stream"] == "contractual-obligations"
    assert record["workflow_id"] == "contractual_obligations_tracker"
    assert record["schema_version"] == "0.1.0"
    assert len(record["obligations"]) == 4
    assert len(record["review_schedule"]) == 4
    assert record["owner"]["role"] == "supplier-governance@example.org"
    print(
        f"wrote {SNAPSHOT} "
        f"(artifact_id={update['contractual_obligations_artifact_id']})"
    )


if __name__ == "__main__":
    main()
