"""Governance-record evidence primitive (log_governance_evidence).

Emits the OCSF API Activity (``class_uid`` 6003) governance-record
artifact and the sibling audit-envelope the operator's evidence store
persists. The dated evidence artifact closes the auditable-lifecycle
obligation NIS2 Directive (EU) 2022/2555 Article 20(1) names: it is
always emitted, including on the referral branch (no approval) and on
the ad-hoc-trigger branch (no scheduled review slot).

The deterministic ``artifact_id`` derives from
``SHA-256(<governance_cycle>|<review_id>|<approval_record_id>|<captured_at>)``
-- ``compile_target`` is intentionally NOT part of the id so the three
reference compilers (n8n, Temporal, LangGraph) re-derive byte-identical
bytes from the same primitive output (CORE-FANOUT byte-parity
contract).

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  ``captured_at`` is supplied by the caller.
* **Determinism.** Same inputs => byte-identical output. Same
  ``(governance_cycle, review_id, approval_record_id, captured_at)``
  => same ``artifact_id``.
* **OCSF v1.3.0.** Emits an API Activity payload (``category_uid``
  6, ``class_uid`` 6003, ``activity_id`` 6 -- Other, since the OCSF
  API Activity vocabulary does not have a governance-approval verb;
  the specific governance semantic is carried in
  ``unmapped.secops_ng``).
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "InvalidGovernanceEvidenceError",
    "derive_governance_evidence_artifact_id",
    "emit_governance_evidence",
]


_CYCLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_APPROVAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SNAPSHOT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_EVIDENCE_ID_RE = re.compile(r"^ev_[0-9a-f]{16}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_OUTCOMES = frozenset({"approved", "referred"})
_TRIGGERS = frozenset({"scheduled", "ad_hoc", "supervisory_request"})
_SCHEMA_VERSION = "1.0.0"
_STREAM = "nis2_art20_governance_evidence"

# OCSF v1.3.0 API Activity (class_uid 6003) constants.
_OCSF_CATEGORY_UID = 6
_OCSF_CLASS_UID = 6003
_OCSF_ACTIVITY_ID = 6  # Other
_OCSF_TYPE_UID = _OCSF_CLASS_UID * 100 + _OCSF_ACTIVITY_ID


class InvalidGovernanceEvidenceError(ValueError):
    """Raised when the evidence inputs cannot produce a deterministic artifact."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidGovernanceEvidenceError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidGovernanceEvidenceError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _optional_canonical(value: object, field: str) -> str:
    # Accepts empty strings verbatim (ad-hoc branch review_id / referral
    # branch approval_record_id).
    if not isinstance(value, str):
        raise InvalidGovernanceEvidenceError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    return unicodedata.normalize("NFKC", value).strip()


def derive_governance_evidence_artifact_id(
    governance_cycle: str,
    review_id: str,
    approval_record_id: str,
    captured_at: str,
) -> str:
    """Derive the deterministic evidence artifact id.

    The four inputs join on ``|`` and the resulting bytes are SHA-256
    hashed; the id is ``ev_<first-16-hex-chars>``. ``compile_target``
    is deliberately not part of the input so the three reference
    compilers re-derive byte-identical bytes.
    """
    cycle = _canonical_text(governance_cycle, "governance_cycle")
    if not _CYCLE_ID_RE.match(cycle):
        raise InvalidGovernanceEvidenceError(
            f"governance_cycle {cycle!r} does not match the schema pattern"
        )
    review = _optional_canonical(review_id, "review_id")
    if review and not _REVIEW_ID_RE.match(review):
        raise InvalidGovernanceEvidenceError(
            f"review_id {review!r} does not match the schema pattern"
        )
    approval = _optional_canonical(approval_record_id, "approval_record_id")
    if approval and not _APPROVAL_ID_RE.match(approval):
        raise InvalidGovernanceEvidenceError(
            f"approval_record_id {approval!r} does not match the schema pattern"
        )
    ts = _canonical_text(captured_at, "captured_at")
    if not _ISO_Z_RE.match(ts):
        raise InvalidGovernanceEvidenceError(
            f"captured_at {ts!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    joined = f"{cycle}|{review}|{approval}|{ts}".encode("utf-8")
    return "ev_" + hashlib.sha256(joined).hexdigest()[:16]


def emit_governance_evidence(
    governance_cycle: str,
    trigger: str,
    review_id: str,
    posture_snapshot_id: str,
    approval_record_id: str,
    outcome: str,
    captured_at: str,
    workflow_id: str,
    execution_id: str,
    compile_target: str,
) -> dict:
    """Emit the OCSF API Activity 6003 governance-record artifact.

    Args:
        governance_cycle: The cycle key discharged.
        trigger: ``scheduled`` / ``ad_hoc`` / ``supervisory_request``.
        review_id: The scheduled review slot id (empty for ad-hoc).
        posture_snapshot_id: The composed per-cycle governance view id.
        approval_record_id: The signed approval record id (empty for
            the referral branch).
        outcome: ``approved`` or ``referred``.
        captured_at: ISO-8601 UTC ``YYYY-MM-DDTHH:MM:SSZ`` instant of
            the governance-record capture (``__captured_at__``).
        workflow_id: Runtime workflow identifier the artifact is
            written from.
        execution_id: Runtime execution identifier for this cycle run.
        compile_target: ``n8n`` / ``temporal`` / ``langgraph``. Carried
            in the ``metadata.product`` block but *not* in the
            deterministic ``artifact_id`` derivation.

    Returns:
        JSON-native envelope with the OCSF API Activity payload plus
        the sibling audit-envelope block. The envelope's ``artifact_id``
        is deterministic (see :func:`derive_governance_evidence_artifact_id`).

    Raises:
        InvalidGovernanceEvidenceError: any input fails validation.
    """
    trig = _canonical_text(trigger, "trigger")
    if trig not in _TRIGGERS:
        raise InvalidGovernanceEvidenceError(
            f"trigger {trig!r} not in {sorted(_TRIGGERS)}"
        )
    outcome_text = _canonical_text(outcome, "outcome")
    if outcome_text not in _OUTCOMES:
        raise InvalidGovernanceEvidenceError(
            f"outcome {outcome_text!r} not in {sorted(_OUTCOMES)}"
        )
    snap = _canonical_text(posture_snapshot_id, "posture_snapshot_id")
    if not _SNAPSHOT_ID_RE.match(snap):
        raise InvalidGovernanceEvidenceError(
            f"posture_snapshot_id {snap!r} does not match the schema pattern"
        )
    wf = _canonical_text(workflow_id, "workflow_id")
    ex = _canonical_text(execution_id, "execution_id")
    ct = _canonical_text(compile_target, "compile_target")
    if ct not in {"n8n", "temporal", "langgraph"}:
        raise InvalidGovernanceEvidenceError(
            f"compile_target {ct!r} not in ('n8n', 'temporal', 'langgraph')"
        )

    # Cross-branch invariants: approved requires approval_record_id;
    # referred forbids it. Runs through canonicalisation via the id
    # derivation, which will also validate the string shapes.
    cycle_norm = _canonical_text(governance_cycle, "governance_cycle")
    review_norm = _optional_canonical(review_id, "review_id")
    approval_norm = _optional_canonical(approval_record_id, "approval_record_id")
    if outcome_text == "approved" and not approval_norm:
        raise InvalidGovernanceEvidenceError(
            "approved outcome requires a non-empty approval_record_id"
        )
    if outcome_text == "referred" and approval_norm:
        raise InvalidGovernanceEvidenceError(
            "referred outcome must carry an empty approval_record_id"
        )
    if trig == "scheduled" and not review_norm:
        raise InvalidGovernanceEvidenceError(
            "scheduled trigger requires a non-empty review_id"
        )
    if trig != "scheduled" and review_norm:
        raise InvalidGovernanceEvidenceError(
            f"{trig} trigger must carry an empty review_id"
        )

    artifact_id = derive_governance_evidence_artifact_id(
        governance_cycle=cycle_norm,
        review_id=review_norm,
        approval_record_id=approval_norm,
        captured_at=captured_at,
    )
    ts = _canonical_text(captured_at, "captured_at")

    ocsf: dict = {
        "category_uid": _OCSF_CATEGORY_UID,
        "class_uid": _OCSF_CLASS_UID,
        "activity_id": _OCSF_ACTIVITY_ID,
        "type_uid": _OCSF_TYPE_UID,
        "time": ts,
        "severity_id": 1,  # Informational
        "status_id": 1 if outcome_text == "approved" else 2,  # Success / Failure
        "metadata": {
            "version": "1.3.0",
            "product": {
                "vendor_name": "SecOps-NG",
                "name": "nis2_art20_governance",
                "feature": {"name": compile_target},
            },
        },
        "unmapped": {
            "secops_ng": {
                "playbook_id": "playbook.nis2_art20_governance@v1",
                "governance_cycle": cycle_norm,
                "trigger": trig,
                "review_id": review_norm,
                "posture_snapshot_id": snap,
                "approval_record_id": approval_norm,
                "outcome": outcome_text,
                "workflow_id": wf,
                "execution_id": ex,
            }
        },
    }

    envelope: dict = {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "artifact_id": artifact_id,
        "captured_at": ts,
        "ocsf": ocsf,
        "audit_envelope": {
            "workflow_id": wf,
            "execution_id": ex,
            "compile_target": ct,
            "governance_cycle": cycle_norm,
            "review_id": review_norm,
            "approval_record_id": approval_norm,
            "outcome": outcome_text,
        },
    }
    return envelope
