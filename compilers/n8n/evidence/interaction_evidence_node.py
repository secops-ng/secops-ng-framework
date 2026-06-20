"""n8n-side adapter for the IT and security support-agent interaction-evidence emitter.

F-WF-12 CORE-FANOUT-N8N-GOLDEN. The interaction-evidence record reuses
the F-CP-02 incidents-stream shape (``schemas/evidence/incidents.schema.json``)
so a support→incident handoff lands on the same Article 21(2)(b)
capability anchor F-WF-05 already discharges. Unlike the F-CP-02
incidents adapter under :mod:`compilers.n8n.evidence.incidents_node`,
this adapter does not go through the shared
``compilers._shared.evidence.incidents`` helper — record assembly,
``incident_id`` derivation, ``artifact_id`` derivation, and the closed
classification envelope are owned by the workflow-local primitive at
:func:`content.playbooks.it_security_support_agent.primitives.artifact.build_interaction_artifact`,
which is purpose-shaped for the support workflow's closed handoff
envelope (a F-CP-02 ``IncidentsContext`` carries a richer state-machine
shape than the support-agent execution produces). The adapter is glue
only: JSON payload in, atomic write to disk, ``{artifact_id,
artifact_path}`` out — exactly the shape the access-evidence and
incidents-evidence n8n adapters return so an operator's ``executeCommand``
/ ``Code`` node sees one contract across streams.

The payload mirrors the primitive's keyword arguments; every field is
JSON-native because n8n cannot ship Python objects across the
node-process boundary. The primitive validates the shape and raises
:class:`InvalidInteractionArtifactError` on a bad input — the adapter
re-raises so the n8n node-side error surface is one Python traceback.

Re-emission for the same ``(workflow_id, execution_id)`` is idempotent:
the primitive derives the same ``incident_id`` (UUIDv5 of
``<workflow_id>|<execution_id>``) and therefore the same ``artifact_id``
(SHA-256 of ``<incident_id>|<execution_id>``), and the adapter writes
the same bytes through a sibling ``.tmp`` + ``os.replace`` so a
concurrent reader cannot observe a partial write.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from content.playbooks.it_security_support_agent.primitives.artifact import (
    build_interaction_artifact,
)

__all__ = ["emit_interaction_evidence_artifact_n8n"]


def _serialise(record: Mapping[str, Any]) -> str:
    """Render the record bytes the adapter writes to disk.

    Matches the convention the F-CP-02 / F-CP-07 shared emitters use
    (``indent=2``, ``sort_keys=True``, trailing newline) so a diff of
    the interaction-evidence artifact against any other incidents- or
    access-stream artifact reads with the same shape and a reviewer
    does not have to track per-stream serialisation rules.
    """
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def emit_interaction_evidence_artifact_n8n(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> dict[str, Any]:
    """Persist one interaction-evidence artifact from an n8n payload.

    Inputs
    ------
    payload
        JSON-native mapping mirroring the keyword arguments of
        :func:`build_interaction_artifact`. Required keys:
        ``workflow_id``, ``execution_id``, ``regulation_refs``,
        ``control_refs``, ``support_request_record``,
        ``classification_verdict``, ``automated_resolution``,
        ``handoff_envelope``, ``captured_at``, ``source_url``,
        ``owner_role``, ``owner_assigned_at``. Optional keys:
        ``cross_border`` (defaults to false), ``commit_sha``,
        ``retention``.
    output_dir
        Operator-supplied directory the artifact lands in. Created if
        it does not exist.

    Returns
    -------
    JSON-serialisable dict shaped for an n8n node's next-node output:
    ``{"artifact_id": <sha256>, "artifact_path": "<abspath>"}``. The
    artifact_id is deterministic on ``(workflow_id, execution_id)`` so
    a replay of the same execution re-derives the same id and
    downstream deduplication is trivial.
    """
    record = build_interaction_artifact(
        workflow_id=payload["workflow_id"],
        execution_id=payload["execution_id"],
        regulation_refs=payload["regulation_refs"],
        control_refs=payload["control_refs"],
        support_request_record=payload["support_request_record"],
        classification_verdict=payload["classification_verdict"],
        automated_resolution=payload["automated_resolution"],
        handoff_envelope=payload["handoff_envelope"],
        captured_at=payload["captured_at"],
        source_url=payload["source_url"],
        owner_role=payload["owner_role"],
        owner_assigned_at=payload["owner_assigned_at"],
        cross_border=bool(payload.get("cross_border", False)),
        commit_sha=payload.get("commit_sha"),
        retention=payload.get("retention"),
    )

    artifact_id = record["artifact_id"]

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{artifact_id}.json"
    tmp_path = out_dir / f".{artifact_id}.json.tmp"
    tmp_path.write_text(_serialise(record), encoding="utf-8")
    os.replace(tmp_path, out_path)

    return {
        "artifact_id": artifact_id,
        "artifact_path": str(out_path.resolve()),
    }
