"""Remediation-tracking primitive (remediation tracking).

Composes the findings register from the red-team engagement, binds each
finding to a remediation deadline against the operator's declared severity
rubric, and assembles the dated Art. 26(8) remediation attestation.

**One envelope carries both step outputs.** The CACAO step declares
``__findings_register_id__`` and ``__remediation_attestation_id__``, but a
``core_body`` binds a single ``out``. Rather than drop one, the attestation
envelope embeds ``findings_register_id`` — the register is not a separate
artifact, it is what the attestation attests to, and splitting them would let
an attestation exist with no register behind it.

**Deadlines are derived, not asserted.** Each finding's deadline is its
observation date plus the rubric's window for its severity. An operator
supplying the deadline directly could report a date the rubric does not
support, and the whole point of the rubric is that the mapping is
inspectable. The rubric ships no defaults: severity windows are the
operator's policy.

**An attestation over open findings is still an attestation.** Art. 26(8)
asks for the remediation plan alongside the attestation, and an engagement
whose findings are all closed on the day of attestation is the exception.
``all_findings_closed`` and ``overdue_count`` report the position honestly
rather than blocking the artifact — but ``overdue_count`` above zero is the
number a reviewer reads first, which is why it is a top-level field and not
buried per finding.

The attestation is **assembled, not published**. The evidence store is an
adapter-bound surface; ``artifact_id`` follows the house derivation
``SHA-256(workflow_id|execution_id|captured_at)`` so the content-addressed
filename is fixed before any sink is chosen.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
  ``captured_at`` is supplied.
* **Determinism.** Same inputs => byte-identical output; findings are
  emitted sorted by id.
* **Public-bar safe.** Findings carry references and severities, never
  vulnerability narrative — a red-team finding body is exploitable detail
  and has no place in a public-bar artifact.
* **Read-only-by-contract.** Nothing is published or notified.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, timedelta

__all__ = [
    "InvalidRemediationTrackingError",
    "derive_attestation_artifact_id",
    "track_remediation",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_SEVERITY_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_SCHEMA_VERSION = "1.0.0"
_STREAM = "dora_tlpt_programme_remediation"


class InvalidRemediationTrackingError(ValueError):
    """Raised when a remediation input or Art. 26(8) invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidRemediationTrackingError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidRemediationTrackingError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidRemediationTrackingError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def derive_attestation_artifact_id(
    workflow_id: str, execution_id: str, captured_at: str
) -> str:
    """SHA-256(``<workflow_id>|<execution_id>|<captured_at>``)."""
    payload = f"{workflow_id}|{execution_id}|{captured_at}".encode()
    return hashlib.sha256(payload).hexdigest()


def _validate_finding(record: object, index: int, rubric: dict) -> dict:
    if not isinstance(record, dict):
        raise InvalidRemediationTrackingError(
            f"findings[{index}] must be a mapping, got {type(record).__name__}"
        )
    finding_id = _require_pattern(
        record.get("finding_id"), f"findings[{index}].finding_id", _ID_RE
    )
    severity = _canonical_text(
        record.get("severity"), f"findings[{index}].severity"
    )
    if not _SEVERITY_RE.match(severity):
        raise InvalidRemediationTrackingError(
            f"findings[{index}].severity {severity!r} does not match the "
            f"schema pattern"
        )
    if severity not in rubric:
        raise InvalidRemediationTrackingError(
            f"findings[{index}].severity {severity!r} has no window in the "
            f"declared rubric {sorted(rubric)}; remediation windows are the "
            f"operator's policy and this primitive ships no defaults"
        )
    observed = _canonical_text(
        record.get("observed_on"), f"findings[{index}].observed_on"
    )
    if not _ISO_DATE_RE.match(observed):
        raise InvalidRemediationTrackingError(
            f"findings[{index}].observed_on {observed!r} is not an ISO-8601 date"
        )
    evidence = _require_pattern(
        record.get("evidence_ref"), f"findings[{index}].evidence_ref", _REF_RE
    )
    closed_on = record.get("closed_on")
    closed: str | None = None
    if closed_on is not None:
        closed = _canonical_text(closed_on, f"findings[{index}].closed_on")
        if not _ISO_DATE_RE.match(closed):
            raise InvalidRemediationTrackingError(
                f"findings[{index}].closed_on {closed!r} is not an ISO-8601 date"
            )
        if closed < observed:
            raise InvalidRemediationTrackingError(
                f"findings[{index}].closed_on {closed!r} precedes observed_on "
                f"{observed!r}"
            )
    deadline = (
        date.fromisoformat(observed) + timedelta(days=rubric[severity])
    ).isoformat()
    return {
        "finding_id": finding_id,
        "severity": severity,
        "observed_on": observed,
        "remediation_deadline": deadline,
        "evidence_ref": evidence,
        "closed_on": closed,
        "closed": closed is not None,
    }


def track_remediation(
    dort_scope: dict,
    red_team_scoping: dict,
    findings: list,
    severity_rubric: dict,
    workflow_id: str,
    execution_id: str,
    captured_at: str,
) -> dict:
    """Compose the findings register and the Art. 26(8) attestation.

    Args:
        dort_scope: The catalogue envelope from the scope step.
        red_team_scoping: The submission envelope from the scoping step
            (``__red_team_scoping_id__``). Must carry
            ``engagement_may_proceed: true``.
        findings: Finding records, each with ``finding_id``, ``severity``,
            ``observed_on``, ``evidence_ref`` and optional ``closed_on``.
        severity_rubric: Severity to remediation window in whole days. The
            operator's policy; no defaults ship.
        workflow_id: Runtime workflow identifier.
        execution_id: Runtime execution identifier.
        captured_at: ISO-8601 ``Z`` instant the attestation is dated at,
            supplied rather than clock-read.

    Returns:
        JSON-native attestation envelope with ``schema_version``, ``stream``,
        ``remediation_attestation_id``, the embedded
        ``findings_register_id``, ``artifact_id``, ``testing_window``,
        ``red_team_scoping_id``, sorted ``findings`` with derived deadlines,
        ``open_count``, ``overdue_count``, ``all_findings_closed``,
        ``captured_at`` and a ``provenance`` block.

    Raises:
        InvalidRemediationTrackingError: any input fails validation, the
            engagement was not approved to proceed, the rubric is malformed,
            or a finding id repeats.
    """
    for name, env in (
        ("dort_scope", dort_scope),
        ("red_team_scoping", red_team_scoping),
    ):
        if not isinstance(env, dict):
            raise InvalidRemediationTrackingError(
                f"{name} must be a mapping, got {type(env).__name__}"
            )
    if red_team_scoping.get("engagement_may_proceed") is not True:
        raise InvalidRemediationTrackingError(
            f"red_team_scoping.engagement_may_proceed is not true (outcome "
            f"{red_team_scoping.get('outcome')!r}); there is no engagement to "
            f"attest remediation for"
        )
    window = _canonical_text(
        dort_scope.get("testing_window"), "dort_scope.testing_window"
    )
    scoping_id = _require_pattern(
        red_team_scoping.get("red_team_scoping_id"),
        "red_team_scoping.red_team_scoping_id",
        _ID_RE,
    )

    if not isinstance(severity_rubric, dict) or not severity_rubric:
        raise InvalidRemediationTrackingError(
            "severity_rubric must be a non-empty mapping of severity to a "
            "remediation window in whole days"
        )
    rubric: dict[str, int] = {}
    for key, value in severity_rubric.items():
        sev = _canonical_text(key, "severity_rubric key")
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise InvalidRemediationTrackingError(
                f"severity_rubric[{sev!r}] must be a non-negative int number "
                f"of days"
            )
        rubric[sev] = value

    if isinstance(findings, str) or not isinstance(findings, (list, tuple)):
        raise InvalidRemediationTrackingError(
            "findings must be a list of finding records"
        )
    validated = [_validate_finding(f, i, rubric) for i, f in enumerate(findings)]
    seen: set[str] = set()
    for entry in validated:
        if entry["finding_id"] in seen:
            raise InvalidRemediationTrackingError(
                f"findings carries {entry['finding_id']!r} more than once; a "
                f"repeated finding id would double-count in the register"
            )
        seen.add(entry["finding_id"])
    validated.sort(key=lambda e: e["finding_id"])

    stamp = _canonical_text(captured_at, "captured_at")
    if not _ISO_Z_RE.match(stamp):
        raise InvalidRemediationTrackingError(
            f"captured_at {stamp!r} is not an ISO-8601 UTC instant "
            f"(YYYY-MM-DDTHH:MM:SSZ)"
        )
    as_of = stamp[:10]
    wf = _require_pattern(workflow_id, "workflow_id", _REF_RE)
    ex = _require_pattern(execution_id, "execution_id", _REF_RE)

    open_entries = [e for e in validated if not e["closed"]]
    overdue = [e for e in open_entries if e["remediation_deadline"] < as_of]

    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "remediation_attestation_id": f"{scoping_id}:attestation:{as_of}",
        "findings_register_id": f"{scoping_id}:findings",
        "artifact_id": derive_attestation_artifact_id(wf, ex, stamp),
        "testing_window": window,
        "red_team_scoping_id": scoping_id,
        "findings": validated,
        "finding_count": len(validated),
        "open_count": len(open_entries),
        "overdue_count": len(overdue),
        "all_findings_closed": not open_entries,
        "captured_at": stamp,
        "provenance": {
            "workflow_id": wf,
            "execution_id": ex,
            "captured_at": stamp,
        },
    }
