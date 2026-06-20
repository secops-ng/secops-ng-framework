"""LangGraph node adapter for the IT and security support-agent interaction-evidence emitter.

F-WF-12 CORE-FANOUT-LANGGRAPH. Mirrors the merged n8n adapter at
:mod:`compilers.n8n.evidence.interaction_evidence_node` and the
Temporal activity at
:mod:`compilers.temporal.evidence.interaction_evidence_activity` exactly
— same JSON-native payload contract, same atomic-write semantics, same
deterministic ``artifact_id`` derivation. The interaction-evidence
record reuses the F-CP-02 incidents-stream shape
(``schemas/evidence/incidents.schema.json``) so a support→incident
handoff lands on the same NIS2 Article 21(2)(b) capability anchor
F-WF-05 already discharges.

The adapter is a plain LangGraph node function: ``state -> state``.
The integrator wires it into a ``StateGraph`` with
``graph.add_node("emit_interaction_evidence",
emit_interaction_evidence_artifact_node)``; no LangGraph or
LangChain import is required at the compiler layer, matching the
runtime-free convention documented in
``compilers/langgraph/__init__.py``.

Unlike the F-CP-02 incidents adapter under
:mod:`compilers.langgraph.evidence.incidents_node`, this adapter does
**not** delegate through a shared ``compilers/_shared/evidence``
helper — record assembly, ``incident_id`` (UUIDv5 of
``<workflow_id>|<execution_id>``), and ``artifact_id`` (SHA-256 of
``<incident_id>|<execution_id>``) derivation are owned by the
workflow-local primitive at
:func:`content.playbooks.it_security_support_agent.primitives.artifact.build_interaction_artifact`,
which is purpose-shaped for the support workflow's closed handoff
envelope (a F-CP-02 ``IncidentsContext`` carries a richer state-machine
shape than the support-agent execution produces). The node is glue
only: state mapping in, atomic write to disk, partial state update out
— same shape the n8n adapter and Temporal activity produce so cross-
target byte-parity holds against the same canonical payload.

Expected state keys:

* ``interaction_evidence_payload`` — a JSON-native mapping mirroring
  the keyword arguments of :func:`build_interaction_artifact`.
  Required keys: ``workflow_id``, ``execution_id``,
  ``regulation_refs``, ``control_refs``, ``support_request_record``,
  ``classification_verdict``, ``automated_resolution``,
  ``handoff_envelope``, ``captured_at``, ``source_url``,
  ``owner_role``, ``owner_assigned_at``. Optional keys:
  ``cross_border`` (defaults to false), ``commit_sha``, ``retention``.
* ``evidence_output_dir`` — operator-supplied directory the artifact
  lands in. Created if it does not exist.

The node returns a partial state update:
``{"interaction_evidence_artifact_path": <abspath>,
   "interaction_evidence_artifact_id": <sha256>}``. LangGraph merges
the update into the running state by key so downstream nodes (the
F-CP-02 incidents-stream KPI rollup, an Article 23(4) notification
timer, etc.) can attach the path to their own audit trail.

Re-emission for the same ``(workflow_id, execution_id)`` is idempotent:
the primitive derives the same ``incident_id`` and therefore the same
``artifact_id``, and the node writes the same bytes through a sibling
``.tmp`` + ``os.replace`` so a concurrent reader cannot observe a
partial write.

Per AGENTS.md § 3 — sovereign-stack default. The helpdesk source, the
classification-policy reference the workflow reads, and the responder
queue the handoff targets are all operator-configured at execution
time. The node does not impose a hosted helpdesk or any non-EU
endpoint; it persists the artifact bytes to whatever
``evidence_output_dir`` the integrator binds in state.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from content.playbooks.it_security_support_agent.primitives.artifact import (
    build_interaction_artifact,
)

__all__ = ["emit_interaction_evidence_artifact_node"]


def _serialise(record: Mapping[str, Any]) -> str:
    """Render the record bytes the node writes to disk.

    Matches the convention the F-CP-02 / F-CP-07 shared emitters and
    the F-WF-12 n8n adapter and Temporal activity use (``indent=2``,
    ``sort_keys=True``, trailing newline) so a diff of the
    interaction-evidence artifact against any other incidents- or
    access-stream artifact reads with the same shape, and the
    per-target byte-parity invariant holds against the n8n and
    Temporal siblings for the same canonical payload.
    """
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


def emit_interaction_evidence_artifact_node(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist one interaction-evidence artifact from LangGraph state.

    Reads ``interaction_evidence_payload`` and ``evidence_output_dir``
    from ``state`` and returns a partial state update carrying the
    written path and the deterministic ``artifact_id``. The primitive
    does its own validation; this function is a thin adapter only.

    CORE-FANOUT pins the payload contract; the per-target byte-parity
    golden and the cross-target byte-parity invariant are pinned by
    the sibling tests under
    ``tests/examples/it_security_support_agent/``.
    """
    try:
        payload = state["interaction_evidence_payload"]
        output_dir = state["evidence_output_dir"]
    except KeyError as exc:  # pragma: no cover - guard against integrator typos
        raise KeyError(
            "emit_interaction_evidence_artifact_node requires "
            "'interaction_evidence_payload' and 'evidence_output_dir' in state"
        ) from exc

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
        "interaction_evidence_artifact_path": str(out_path.resolve()),
        "interaction_evidence_artifact_id": artifact_id,
    }
