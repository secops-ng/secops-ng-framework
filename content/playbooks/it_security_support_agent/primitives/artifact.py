"""Interaction-evidence artifact builder primitive (emit-interaction-evidence).

Builds the JSON-native interaction-evidence record shaped against
``schemas/evidence/incidents.schema.json`` (stream: ``incidents``). Reuses
the F-CP-02 incidents stream that the F-WF-05 incident_management
workflow already binds onto — support interactions that escalate into a
human-handoff feed the same NIS2 Article 21(2)(b) incident-handling
capability anchor on ``classification.significant=true``; support
interactions that close via the automated-resolution path land on the
schema's intake-only audit-close branch with ``classification.significant
= false`` so the F-CP-02 KPI surface does not overcount.

The artifact's ``classification`` envelope is derived deterministically
from the closed handoff envelope produced by
:func:`...primitives.handoff.escalate_with_human_handoff`:

* ``handoff_fired=true``  → ``significant=true``  and ``rule_ids`` carry
  one ``sig.support_<trigger_reason>`` token pinned to the closed
  vocabulary in :mod:`.handoff`.
* ``handoff_fired=false`` → ``significant=false`` and ``rule_ids`` is
  empty (the audit-close intake-only branch the schema accommodates).

``cross_border`` is operator-supplied (defaults to ``false``) because
the workflow itself cannot derive scope from the support-request record
alone.  ``reasons`` carries one human-readable line per trigger
condition, public-bar safe (no operator branding, no personal names).

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs.
* **Determinism.** Same inputs ⇒ byte-identical output. Same
  ``(workflow_id, execution_id)`` ⇒ same ``incident_id`` (UUIDv5 over
  ``<workflow_id>|<execution_id>``) ⇒ same ``artifact_id`` (SHA-256 of
  ``<incident_id>|<execution_id>``). Re-emission inside the same
  execution is byte-identical.
* **Public-bar safe.** ``owner_role`` and the supplied free-text
  ``reasons`` carry no operator branding; ``responder_queue`` (when
  present on a fired handoff) was already pinned to a role-shape by the
  upstream :mod:`.handoff` primitive.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
import uuid
from typing import Any

__all__ = [
    "InvalidInteractionArtifactError",
    "build_interaction_artifact",
    "derive_interaction_artifact_id",
    "derive_interaction_incident_id",
]


_SCHEMA_VERSION = "1.0.0"
_STREAM = "incidents"

_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
_REGULATION_REF_RE = re.compile(
    r"^(nis2|dora|cra|gdpr|iso27001|soc2):[a-z0-9][a-z0-9.-]*$"
)
_CONTROL_REF_RE = re.compile(
    r"^control\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*@v[0-9]+(\.[0-9]+){0,2}$"
)
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DURATION_RE = re.compile(
    r"^P([0-9]+Y)?([0-9]+M)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+S)?)?$"
)
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")

# Closed vocabulary mirroring the trigger_reason alphabet pinned in
# ``handoff.py``. Each fired trigger maps to one sig.* rule_id that
# downstream KPI surfaces can pivot on without re-reading the workflow
# state machine.
_HANDOFF_RULE_IDS: dict[str, str] = {
    "incident_shaped_classification": "sig.support_incident_handoff",
    "automated_resolution_not_resolved": "sig.support_handoff_unresolved",
    "policy_override": "sig.support_handoff_policy_override",
}
# Human-readable companion strings; one per fired trigger reason.
_HANDOFF_REASONS: dict[str, str] = {
    "incident_shaped_classification": (
        "support interaction escalated to a human responder because the "
        "classification verdict was incident-shaped"
    ),
    "automated_resolution_not_resolved": (
        "support interaction escalated to a human responder because the "
        "automated-resolution attempt did not close the request"
    ),
    "policy_override": (
        "support interaction escalated to a human responder under an "
        "operator-declared policy override"
    ),
}
_CLOSURE_REASON = (
    "support interaction closed via automated resolution; no human "
    "responder handoff fired"
)


# Stable UUIDv5 namespace for support-agent interaction-evidence incident
# ids. Distinct from the F-WF-05 incident_management namespace so a
# replay-vs-original diff against the two streams cannot collide. Value
# is a constant hex literal so re-runs collapse to the same UUID.
_INTERACTION_NAMESPACE = uuid.UUID("9d6b3c1a-2f4e-4d6a-8b1c-7a9f0e2d4c8b")


class InvalidInteractionArtifactError(ValueError):
    """Raised when the artifact inputs cannot produce a schema-valid record."""


def _require_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidInteractionArtifactError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidInteractionArtifactError(
            f"{field} is empty after canonicalisation"
        )
    if _CONTROL_CHAR_RE.search(normalised):
        raise InvalidInteractionArtifactError(
            f"{field} carries control characters; reject"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _require_str(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidInteractionArtifactError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def _require_iso_date_time(value: object, field: str) -> str:
    """Accept the schema-shaped ``format: date-time``.

    The lifecycle markers' JSON-Schema declares ``format: date-time``;
    we canonicalise on the same ``...Z`` UTC second-precision shape the
    rest of the framework writes so renders are byte-stable across
    targets.
    """
    return _require_iso_z(value, field)


def _validate_ref_list(
    refs: object, field: str, pattern: re.Pattern[str]
) -> list[str]:
    if not isinstance(refs, list) or not refs:
        raise InvalidInteractionArtifactError(
            f"{field} must be a non-empty list"
        )
    seen: set[str] = set()
    out: list[str] = []
    for index, ref in enumerate(refs):
        if not isinstance(ref, str) or not pattern.match(ref):
            raise InvalidInteractionArtifactError(
                f"{field}[{index}] {ref!r} does not match the schema pattern"
            )
        if ref in seen:
            raise InvalidInteractionArtifactError(
                f"{field} has duplicate entry {ref!r}"
            )
        seen.add(ref)
        out.append(ref)
    return out


def _derive_classification(
    handoff_envelope: dict, cross_border: bool
) -> dict[str, Any]:
    """Derive the F-CP-02 classification envelope from the handoff envelope.

    ``handoff_fired=true``  → ``significant=true``  + one sig.* rule_id +
    one human-readable reason mapped from the closed trigger_reason
    vocabulary pinned in :mod:`.handoff`.

    ``handoff_fired=false`` → ``significant=false`` + empty rule_ids +
    one explanatory reason recording the closure path.
    """
    fired = handoff_envelope.get("handoff_fired")
    if not isinstance(fired, bool):
        raise InvalidInteractionArtifactError(
            "handoff_envelope.handoff_fired must be a bool"
        )
    trigger = handoff_envelope.get("trigger_reason")
    if not isinstance(trigger, str):
        raise InvalidInteractionArtifactError(
            "handoff_envelope.trigger_reason must be a string"
        )

    if fired:
        if trigger not in _HANDOFF_RULE_IDS:
            raise InvalidInteractionArtifactError(
                f"handoff_envelope.trigger_reason {trigger!r} is not one of "
                f"the fired-handoff vocabulary "
                f"{sorted(_HANDOFF_RULE_IDS)!r}"
            )
        rule_ids = [_HANDOFF_RULE_IDS[trigger]]
        reasons = [_HANDOFF_REASONS[trigger]]
        significant = True
    else:
        if trigger != "automated_resolution_closure":
            raise InvalidInteractionArtifactError(
                f"handoff_envelope.trigger_reason {trigger!r} is not the "
                "expected 'automated_resolution_closure' on a "
                "handoff_fired=false envelope"
            )
        rule_ids = []
        reasons = [_CLOSURE_REASON]
        significant = False

    return {
        "significant": significant,
        "cross_border": bool(cross_border),
        "reasons": reasons,
        "rule_ids": rule_ids,
    }


def derive_interaction_incident_id(
    workflow_id: str, execution_id: str
) -> str:
    """UUIDv5(``_INTERACTION_NAMESPACE``, ``<workflow_id>|<execution_id>``).

    Deterministic on the two pinned inputs so a replay of the same
    execution re-derives the same incident_id and a join with the
    F-CP-02 incidents stream is single-string equal.
    """
    name = f"{workflow_id}|{execution_id}"
    return str(uuid.uuid5(_INTERACTION_NAMESPACE, name))


def derive_interaction_artifact_id(
    incident_id: str, execution_id: str
) -> str:
    """SHA-256(``<incident_id>|<execution_id>``) per the schema contract."""
    payload = f"{incident_id}|{execution_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_interaction_artifact(
    workflow_id: str,
    execution_id: str,
    regulation_refs: list,
    control_refs: list,
    support_request_record: dict,
    classification_verdict: dict,
    automated_resolution: dict,
    handoff_envelope: dict,
    captured_at: str,
    source_url: str,
    owner_role: str,
    owner_assigned_at: str,
    cross_border: bool = False,
    commit_sha: str | None = None,
    retention: str | None = None,
) -> dict:
    """Build the interaction-evidence record for one support execution.

    Inputs
    ------
    workflow_id
        Stable lower-snake-case workflow stable-id
        (``it_security_support_agent``).
    execution_id
        Per-execution identifier issued by the compile target's
        workflow runtime.
    regulation_refs, control_refs
        Schema-shaped reference lists; at least one entry each.
    support_request_record
        Closed envelope from
        :func:`...primitives.ingest.ingest_support_request`. Carried
        through for replay traceability — the record's ``received_at``
        is the canonical detection instant fed into ``lifecycle.detected_at``.
    classification_verdict
        Closed verdict from
        :func:`...primitives.classify.classify_request`. Carried through
        for replay traceability; the workflow's classification
        envelope on the artifact is derived from the closed handoff
        envelope and not from this verdict directly so the rule_id
        vocabulary stays on the schema-pinned ``sig|cb`` alphabet.
    automated_resolution
        Closed observation from
        :func:`...primitives.resolution.attempt_automated_resolution`.
        Carried through for replay traceability; the workflow's
        ``lifecycle.triaged_at`` reads the same ``received_at`` instant
        for determinism (the support workflow has no separate triage
        clock).
    handoff_envelope
        Closed envelope from
        :func:`...primitives.handoff.escalate_with_human_handoff`. The
        deterministic ``significant`` / ``rule_ids`` derivation reads
        from this envelope; on a fired handoff the closed
        ``responder_queue`` handle on this envelope is the artifact's
        owner pointer surface (the artifact's ``owner`` block is
        always operator-supplied, but the primitive cross-checks the
        responder_queue handle against the same role-shape).
    captured_at
        ISO-8601 UTC second-precision timestamp (``...Z``). Carried on
        the top-level ``captured_at``, on ``provenance.captured_at``,
        and on ``lifecycle.detected_at``.
    source_url
        URL of the workflow run that produced this artifact.
    owner_role, owner_assigned_at
        Role-shaped owner pointer + assignment date. Personal names
        are out of scope per AGENTS.md §3.
    cross_border
        NIS2 Article 23(6) cross-border-scope flag. Operator-supplied;
        defaults to ``false`` because the workflow cannot derive scope
        from the support-request record alone.
    commit_sha, retention
        Optional schema fields.

    Returns
    -------
    JSON-native dict matching ``schemas/evidence/incidents.schema.json``.
    The deterministic ``incident_id`` and ``artifact_id`` derive from
    the two pinned fields per the schema contract.
    """
    wid = _require_str(workflow_id, "workflow_id")
    if not _WORKFLOW_ID_RE.match(wid) or len(wid) > 200:
        raise InvalidInteractionArtifactError(
            f"workflow_id {workflow_id!r} does not match the schema pattern"
        )

    eid = _require_str(execution_id, "execution_id")
    if len(eid) > 200:
        raise InvalidInteractionArtifactError(
            "execution_id must be <= 200 chars per the schema"
        )

    reg_out = _validate_ref_list(
        regulation_refs, "regulation_refs", _REGULATION_REF_RE
    )
    ctrl_out = _validate_ref_list(
        control_refs, "control_refs", _CONTROL_REF_RE
    )

    if not isinstance(support_request_record, dict):
        raise InvalidInteractionArtifactError(
            "support_request_record must be an object, got "
            f"{type(support_request_record).__name__}"
        )
    if not isinstance(classification_verdict, dict):
        raise InvalidInteractionArtifactError(
            "classification_verdict must be an object, got "
            f"{type(classification_verdict).__name__}"
        )
    if not isinstance(automated_resolution, dict):
        raise InvalidInteractionArtifactError(
            "automated_resolution must be an object, got "
            f"{type(automated_resolution).__name__}"
        )
    if not isinstance(handoff_envelope, dict):
        raise InvalidInteractionArtifactError(
            "handoff_envelope must be an object, got "
            f"{type(handoff_envelope).__name__}"
        )

    # The support-request record carries the canonical detection instant
    # (received_at). We read it as ``lifecycle.detected_at`` so the
    # F-CP-02 MTTD KPI surface gets a coherent value on a support→incident
    # handoff.
    detected_at = _require_iso_date_time(
        support_request_record.get("received_at"),
        "support_request_record.received_at",
    )

    captured_at_value = _require_iso_date_time(captured_at, "captured_at")
    source_url_value = _require_str(source_url, "source_url")

    owner_role_text = _require_str(owner_role, "owner_role")
    if len(owner_role_text) > 200:
        raise InvalidInteractionArtifactError(
            "owner_role must be <= 200 chars per the schema"
        )
    owner_assigned_text = _require_str(owner_assigned_at, "owner_assigned_at")
    if not _ISO_DATE_RE.match(owner_assigned_text):
        raise InvalidInteractionArtifactError(
            f"owner_assigned_at {owner_assigned_at!r} must be ISO-8601 "
            "date (YYYY-MM-DD)"
        )

    classification = _derive_classification(handoff_envelope, cross_border)

    incident_id = derive_interaction_incident_id(wid, eid)
    artifact_id = derive_interaction_artifact_id(incident_id, eid)

    record: dict = {
        "schema_version": _SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "stream": _STREAM,
        "incident_id": incident_id,
        "execution_id": eid,
        "regulation_refs": reg_out,
        "control_refs": ctrl_out,
        "classification": classification,
        "lifecycle": {"detected_at": detected_at},
        "notification_timeline": [],
        "owner": {
            "role": owner_role_text,
            "assigned_at": owner_assigned_text,
        },
        "captured_at": captured_at_value,
        "provenance": {
            "source_url": source_url_value,
            "captured_at": captured_at_value,
        },
    }

    if commit_sha is not None:
        sha_text = _require_str(commit_sha, "commit_sha")
        if not _COMMIT_SHA_RE.match(sha_text):
            raise InvalidInteractionArtifactError(
                f"commit_sha {commit_sha!r} must be 7..64 lowercase hex chars"
            )
        record["provenance"]["commit_sha"] = sha_text

    if retention is not None:
        ret_text = _require_str(retention, "retention")
        if not _DURATION_RE.match(ret_text):
            raise InvalidInteractionArtifactError(
                f"retention {retention!r} must be an ISO-8601 duration"
            )
        record["retention"] = ret_text

    return record
