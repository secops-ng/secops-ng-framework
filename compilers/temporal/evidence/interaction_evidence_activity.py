"""Temporal-side adapter for the IT and security support-agent interaction-evidence emitter.

F-WF-12 CORE-FANOUT-TEMPORAL. Mirrors the merged n8n adapter at
:mod:`compilers.n8n.evidence.interaction_evidence_node` exactly — same
JSON-native payload contract, same return shape, same atomic-write
semantics. The interaction-evidence record reuses the F-CP-02
incidents-stream shape (``schemas/evidence/incidents.schema.json``) so a
support→incident handoff lands on the same NIS2 Article 21(2)(b)
capability anchor F-WF-05 already discharges.

Unlike the F-WF-10 contractual-obligations and F-CP-02 incidents
Temporal activities, this activity does **not** delegate through a
shared ``compilers/_shared/evidence`` helper — record assembly,
``incident_id`` (UUIDv5 of ``<workflow_id>|<execution_id>``), and
``artifact_id`` (SHA-256 of ``<incident_id>|<execution_id>``) derivation
are owned by the workflow-local primitive at
:func:`content.playbooks.it_security_support_agent.primitives.artifact.build_interaction_artifact`,
which is purpose-shaped for the support workflow's closed handoff
envelope (a F-CP-02 ``IncidentsContext`` carries a richer state-machine
shape than the support-agent execution produces). This activity is glue
only: payload in (typed-or-mapping), atomic write to disk via the
shared primitive's record, written absolute path out — exactly the
shape the F-WF-10 / F-CP-02 Temporal activities return so a Temporal
worker sees one contract across streams.

Importing ``temporalio`` is required at install time; it is already a
transitive dependency of the Temporal worked examples under
``examples/temporal/`` (including the F-WF-12 it_security_support_agent
worked example this activity wraps).

Per AGENTS.md § 3 — sovereign-stack default. The helpdesk source, the
classification-policy reference the workflow reads, and the responder
queue the handoff targets are all operator-configured at execution
time. The activity does not impose a hosted helpdesk or any non-EU
endpoint; it persists the artifact bytes to whatever ``output_dir``
the caller (a Temporal workflow or operator harness) hands it.

Re-emission for the same ``(workflow_id, execution_id)`` is idempotent:
the primitive derives the same ``incident_id`` and therefore the same
``artifact_id``, and the activity writes the same bytes through a
sibling ``.tmp`` + ``os.replace`` so a concurrent reader cannot observe
a partial write.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from temporalio import activity

from content.playbooks.it_security_support_agent.primitives.artifact import (
    build_interaction_artifact,
)

__all__ = ["emit_interaction_evidence_artifact_activity"]


def _serialise(record: Mapping[str, Any]) -> str:
    """Render the record bytes the activity writes to disk.

    Matches the convention the F-CP-02 / F-CP-07 shared emitters and the
    F-WF-12 n8n adapter use (``indent=2``, ``sort_keys=True``, trailing
    newline) so a diff of the interaction-evidence artifact against any
    other incidents- or access-stream artifact reads with the same
    shape, and the per-target byte-parity invariant holds against the
    n8n sibling for the same canonical payload.
    """
    return json.dumps(record, indent=2, sort_keys=True) + "\n"


@activity.defn
async def emit_interaction_evidence_artifact_activity(
    payload: Mapping[str, Any],
    output_dir: str | os.PathLike[str],
) -> str:
    """Persist one interaction-evidence artifact from a Temporal payload.

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
    Absolute path of the written record as a string so the Temporal-side
    caller can attach it to subsequent activity inputs (the F-CP-02
    incidents-stream KPI rollup, an Article 23(4) notification timer,
    etc.) and to the workflow's audit trail. The ``artifact_id`` is
    deterministic on ``(workflow_id, execution_id)`` so a replay of the
    same execution re-derives the same id and downstream deduplication
    is trivial.
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

    return str(out_path.resolve())
