"""CRA Article 14 reporting trigger and notification chain.

Two CORE action bodies for the vulnerability-intake playbook (F-WF-01):
*assess CRA reporting trigger* and *regulator-notification chain*. Both are
deterministic and offline — whether a regulator clock starts, and when each
stage falls due, are arithmetic over the case facts, not a judgement call and
not an LM's opinion (``docs/FOUNDATION.md`` §LLM determinism).

Grounding, from ``content/mappings/cra/article-14-and-annex-i.yaml``:

* ``cra:art-14-early-warning`` (Art. 14(1)) — notify the coordinator CSIRT and
  ENISA of any **actively exploited** vulnerability without undue delay and in
  any event **within 24 hours** of becoming aware of it.
* ``cra:art-14-notification-72h`` (Art. 14(2)) — vulnerability notification
  **within 72 hours** of awareness.
* ``cra:art-14-final-report`` (Art. 14(2)) — final report **no later than 14
  days** after a corrective or mitigating measure becomes available.

Two deliberate design choices:

**Active exploitation is evidence-driven, never inferred from scores.** A high
EPSS probability is a *forecast*; Art. 14(1) turns on exploitation actually
observed. Passing ``exploitation_evidence`` is the only way to start the
24-hour clock. EPSS and CVSS are recorded on the verdict for audit and inform
the advisory, but they cannot manufacture a reporting obligation — inventing
one would put an operator into a regulator conversation they do not owe, and
suppressing one is worse. The scores appear in ``reasons`` so a reviewer sees
what was known.

**The final-report clock is anchored to remedy availability, not awareness.**
Art. 14(2) measures the 14 days from when a corrective or mitigating measure
becomes available, so ``final_report_due_at`` is ``None`` until the caller
supplies ``remedy_available_at``. Anchoring it to awareness would invent a
deadline the regulation does not set.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
from dataclasses import dataclass
from typing import Literal, Tuple

# Closed alphabet of Art. 14 submission stages, in regulatory order.
CRAStage = Literal["early_warning", "notification", "final_report"]

# Hours from awareness for the two awareness-anchored stages, and days from
# remedy availability for the final report. Art. 14(1) and 14(2).
EARLY_WARNING_HOURS = 24
NOTIFICATION_HOURS = 72
FINAL_REPORT_DAYS = 14

# Mapping refs this module's verdicts attest against. Kept here so the
# evidence artifact and the audit trail cite the same ids the crosswalk uses.
EARLY_WARNING_REF = "cra:art-14-early-warning"
NOTIFICATION_REF = "cra:art-14-notification-72h"
FINAL_REPORT_REF = "cra:art-14-final-report"

# Evidence kinds that constitute observed exploitation. Closed on purpose:
# "someone thinks it is likely" is not on the list.
ExploitationEvidence = Literal[
    "none",
    "public_exploit_observed",
    "incident_confirmed",
    "kev_listed",
    "vendor_confirmed",
]

_EXPLOITING_EVIDENCE = frozenset(
    {"public_exploit_observed", "incident_confirmed", "kev_listed", "vendor_confirmed"}
)


def _parse_utc(value: str, *, field_name: str) -> _dt.datetime:
    """Parse an ISO-8601 UTC instant, rejecting naive or non-UTC input.

    Regulator clocks are absolute. A naive timestamp would silently adopt
    whatever timezone the runtime happens to sit in, which is how a 24-hour
    deadline becomes a 25-hour one across a DST boundary.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO-8601 string")
    text = value.strip()
    try:
        parsed = _dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} is not a valid ISO-8601 instant: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError(
            f"{field_name} must carry an explicit UTC offset (got naive {value!r}); "
            f"a regulator deadline cannot depend on the runtime's local timezone"
        )
    return parsed.astimezone(_dt.timezone.utc)


def _iso(moment: _dt.datetime) -> str:
    """Render a UTC instant in the ``...Z`` form the rest of the content uses."""
    return moment.astimezone(_dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(*parts: str) -> str:
    """Short hex digest over canonical inputs; 16 lower-hex chars."""
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class CRATriggerVerdict:
    """Whether Art. 14 reporting is owed, and when each stage falls due.

    Immutable so the notification chain downstream and the audit trail pin
    against one handle.

    Attributes:
        reporting_required: True when an Art. 14 obligation is engaged.
        actively_exploited: True when the supplied evidence establishes
            observed exploitation — the Art. 14(1) trigger.
        early_warning_due_at: 24h from awareness, or ``None`` when no
            obligation is engaged.
        notification_due_at: 72h from awareness, or ``None``.
        final_report_due_at: 14 days from remedy availability; ``None`` until
            ``remedy_available_at`` is known.
        mapping_refs: Crosswalk ids this verdict attests against.
        reasons: Ordered tuple naming every rule that fired.
        inputs_digest: Short hex digest of the canonical inputs.
    """

    reporting_required: bool
    actively_exploited: bool
    early_warning_due_at: str | None
    notification_due_at: str | None
    final_report_due_at: str | None
    mapping_refs: Tuple[str, ...]
    reasons: Tuple[str, ...]
    inputs_digest: str


def assess_cra_reporting_trigger(
    *,
    cve_id: str,
    awareness_at: str,
    exploitation_evidence: ExploitationEvidence,
    cvss_base_score: float | None = None,
    epss_value: str | None = None,
    remedy_available_at: str | None = None,
) -> CRATriggerVerdict:
    """Decide whether CRA Art. 14 reporting is owed and compute the deadlines.

    Policy (deterministic, replay-safe):

    * ``exploitation_evidence`` in the observed set (public exploit, confirmed
      incident, KEV listing, vendor confirmation) ⇒ actively exploited ⇒
      Art. 14(1) engaged: early warning due 24h from awareness, notification
      due 72h from awareness.
    * ``exploitation_evidence == "none"`` ⇒ no Art. 14 obligation, and both
      awareness-anchored deadlines are ``None``. CVSS and EPSS are recorded in
      ``reasons`` but never promote a forecast into an obligation.
    * ``final_report_due_at`` is 14 days after ``remedy_available_at`` when
      supplied, else ``None`` — Art. 14(2) anchors it to remedy availability,
      not to awareness.

    Args:
        cve_id: Case identifier, carried into the digest.
        awareness_at: ISO-8601 UTC instant the operator became aware. Must
            carry an explicit offset.
        exploitation_evidence: Closed alphabet — :data:`ExploitationEvidence`.
        cvss_base_score: Optional; recorded for audit, never a trigger.
        epss_value: Optional canonical EPSS probability string; recorded for
            audit, never a trigger.
        remedy_available_at: Optional ISO-8601 UTC instant a corrective or
            mitigating measure became available.

    Returns:
        :class:`CRATriggerVerdict`.

    Raises:
        ValueError: ``cve_id`` empty, ``exploitation_evidence`` outside the
            closed alphabet, or a timestamp that is not ISO-8601 UTC.
        TypeError: ``cvss_base_score`` is neither ``None`` nor a real number.
    """
    if not isinstance(cve_id, str) or not cve_id.strip():
        raise ValueError("cve_id must be a non-empty string")
    if exploitation_evidence not in (
        "none", "public_exploit_observed", "incident_confirmed",
        "kev_listed", "vendor_confirmed",
    ):
        raise ValueError(
            f"unknown exploitation_evidence {exploitation_evidence!r}; expected one of "
            f"('none', 'public_exploit_observed', 'incident_confirmed', 'kev_listed', "
            f"'vendor_confirmed')"
        )
    if cvss_base_score is not None and isinstance(cvss_base_score, bool):
        raise TypeError("cvss_base_score must be a number or None, got bool")
    if cvss_base_score is not None and not isinstance(cvss_base_score, (int, float)):
        raise TypeError(
            f"cvss_base_score must be a number or None, got "
            f"{type(cvss_base_score).__name__}"
        )

    aware = _parse_utc(awareness_at, field_name="awareness_at")
    actively_exploited = exploitation_evidence in _EXPLOITING_EVIDENCE

    reasons: list[str] = []
    refs: list[str] = []
    if actively_exploited:
        reasons.append(
            f"exploitation_evidence={exploitation_evidence} → actively exploited "
            f"→ CRA Art. 14(1) engaged"
        )
        early = _iso(aware + _dt.timedelta(hours=EARLY_WARNING_HOURS))
        notify = _iso(aware + _dt.timedelta(hours=NOTIFICATION_HOURS))
        refs += [EARLY_WARNING_REF, NOTIFICATION_REF]
        reasons.append(f"early warning due {early} ({EARLY_WARNING_HOURS}h from awareness)")
        reasons.append(f"notification due {notify} ({NOTIFICATION_HOURS}h from awareness)")
    else:
        reasons.append(
            "exploitation_evidence=none → no observed exploitation → no CRA Art. 14 "
            "reporting obligation engaged"
        )
        early = notify = None

    # Scores are audit context, never a trigger. Recorded either way so a
    # reviewer can see what was known when the call was made.
    if cvss_base_score is not None:
        reasons.append(f"cvss_base_score={cvss_base_score} (recorded, not a trigger)")
    if epss_value is not None:
        reasons.append(
            f"epss={epss_value} (forecast, recorded; Art. 14(1) turns on observed "
            f"exploitation, not predicted)"
        )

    final = None
    if remedy_available_at is not None:
        remedy = _parse_utc(remedy_available_at, field_name="remedy_available_at")
        final = _iso(remedy + _dt.timedelta(days=FINAL_REPORT_DAYS))
        refs.append(FINAL_REPORT_REF)
        reasons.append(
            f"final report due {final} ({FINAL_REPORT_DAYS} days from remedy availability)"
        )
    else:
        reasons.append(
            "remedy_available_at unknown → final-report clock not started "
            "(Art. 14(2) anchors it to remedy availability)"
        )

    return CRATriggerVerdict(
        reporting_required=actively_exploited,
        actively_exploited=actively_exploited,
        early_warning_due_at=early,
        notification_due_at=notify,
        final_report_due_at=final,
        mapping_refs=tuple(refs),
        reasons=tuple(reasons),
        inputs_digest=_digest(
            cve_id.strip(),
            _iso(aware),
            exploitation_evidence,
            "" if cvss_base_score is None else f"{float(cvss_base_score):.1f}",
            epss_value or "",
            remedy_available_at or "",
        ),
    )


@dataclass(frozen=True)
class NotificationChainPlan:
    """The ordered Art. 14 submissions owed for one case.

    Attributes:
        stages: Stages owed, in regulatory order. Empty when nothing is owed.
        destinations: Resolved recipient handle per stage owed.
        due_at: Deadline per stage owed.
        mapping_refs: Crosswalk ids the plan attests against.
        reasons: Ordered tuple naming every rule that fired.
        inputs_digest: Short hex digest of the canonical inputs.
    """

    stages: Tuple[CRAStage, ...]
    destinations: Tuple[Tuple[str, str], ...]
    due_at: Tuple[Tuple[str, str], ...]
    mapping_refs: Tuple[str, ...]
    reasons: Tuple[str, ...]
    inputs_digest: str


def build_notification_chain(
    *,
    cve_id: str,
    trigger: CRATriggerVerdict,
    destinations: dict[str, str],
) -> NotificationChainPlan:
    """Plan the Art. 14 submission chain from a trigger verdict.

    **Fail-closed on destinations**, matching ``incident_management``'s
    regulator-submission resolver: the framework ships no default CSIRT or
    ENISA endpoint, because a wrong default would send a regulatory
    notification to the wrong place — worse than not sending it. A stage that
    is owed with no configured destination raises.

    Args:
        cve_id: Case identifier, carried into the digest.
        trigger: Verdict from :func:`assess_cra_reporting_trigger`.
        destinations: Stage name → recipient handle, operator-supplied.

    Returns:
        :class:`NotificationChainPlan`. Empty ``stages`` when nothing is owed.

    Raises:
        TypeError: ``trigger`` is not a :class:`CRATriggerVerdict`, or
            ``destinations`` is not a mapping.
        ValueError: a stage is owed but has no configured destination.
    """
    if not isinstance(trigger, CRATriggerVerdict):
        raise TypeError(
            f"trigger must be a CRATriggerVerdict, got {type(trigger).__name__}"
        )
    if not isinstance(destinations, dict):
        raise TypeError(
            f"destinations must be a mapping of stage -> recipient, got "
            f"{type(destinations).__name__}"
        )

    if not trigger.reporting_required:
        return NotificationChainPlan(
            stages=(),
            destinations=(),
            due_at=(),
            mapping_refs=(),
            reasons=("no Art. 14 obligation engaged → no submissions planned",),
            inputs_digest=_digest(cve_id.strip(), trigger.inputs_digest, ""),
        )

    owed: list[tuple[CRAStage, str]] = [
        ("early_warning", trigger.early_warning_due_at or ""),
        ("notification", trigger.notification_due_at or ""),
    ]
    if trigger.final_report_due_at:
        owed.append(("final_report", trigger.final_report_due_at))

    reasons: list[str] = []
    resolved: list[tuple[str, str]] = []
    missing = [stage for stage, _ in owed if not destinations.get(stage)]
    if missing:
        raise ValueError(
            f"no destination configured for owed Art. 14 stage(s) {missing!r}; the "
            f"framework ships no default CSIRT/ENISA endpoint on purpose — configure "
            f"them rather than letting a submission default somewhere"
        )
    for stage, _due in owed:
        resolved.append((stage, destinations[stage]))
        reasons.append(f"{stage} → {destinations[stage]}")

    if not trigger.final_report_due_at:
        reasons.append(
            "final_report deferred: remedy not yet available, so its 14-day clock "
            "has not started"
        )

    return NotificationChainPlan(
        stages=tuple(stage for stage, _ in owed),
        destinations=tuple(resolved),
        due_at=tuple(owed),
        mapping_refs=trigger.mapping_refs,
        reasons=tuple(reasons),
        inputs_digest=_digest(
            cve_id.strip(),
            trigger.inputs_digest,
            "|".join(f"{s}={destinations[s]}" for s, _ in owed),
        ),
    )


__all__ = [
    "CRAStage",
    "CRATriggerVerdict",
    "EARLY_WARNING_HOURS",
    "EARLY_WARNING_REF",
    "ExploitationEvidence",
    "FINAL_REPORT_DAYS",
    "FINAL_REPORT_REF",
    "NOTIFICATION_HOURS",
    "NOTIFICATION_REF",
    "NotificationChainPlan",
    "assess_cra_reporting_trigger",
    "build_notification_chain",
]
