"""Regulator and data-subject notifications for the data_exfil playbook.

Backs the two notification steps. Delivery along the operator's
pre-bound channels is the adapter's concern; which notifications are owed,
to whom, on what basis and by when is composed here.

**Regulator.** One notification per applicable regime the operator has an
authority channel for, each with its own clock, all anchored on the
instant the operator became *aware* — not first detection:

* GDPR Art. 33(1) — the supervisory authority, 72 hours. Only when
  personal data was affected; with no affected subjects there is no
  personal-data breach and the regime is recorded as skipped, not dropped.
* NIS2 Art. 23(4)(a) — the CSIRT or competent authority, early warning
  within 24 hours.
* DORA Art. 19(4)(a) — the competent authority, initial notification at
  the latest 24 hours after awareness. The four-hour-from-classification
  leg belongs to the DORA major-incident playbook, which classifies.

A required notification that no configured channel can carry fails loud:
an unroutable legal obligation is not something to compose as an empty
list.

**Data subjects.** GDPR Art. 34 requires telling data subjects only when
the breach is likely to result in a high risk to them. The operator's
policy names the classifications that meet that bar; uninspected content
meets it too. Either way the step records a determination with its basis
— **an unjustified non-notification is not representable**, because that
record is what a supervisory authority asks for.
"""

from __future__ import annotations

from datetime import timedelta

from ._common import FMT, confirmed_scope, digest, exact_keys, pointer, zulu

__all__ = ["InvalidNotificationError", "compose_regulator_notification", "compose_subject_notification"]

_REGIMES = {
    "gdpr": ("GDPR Art. 33(1)", timedelta(hours=72)),
    "nis2": ("NIS2 Art. 23(4)(a)", timedelta(hours=24)),
    "dora": ("DORA Art. 19(4)(a)", timedelta(hours=24)),
}
_CLASSIFICATIONS = ("public", "internal", "confidential", "restricted", "special-category")


class InvalidNotificationError(ValueError):
    """Inputs are malformed, inconsistent, or the gate does not lead here."""


def _finding(triage: dict, scope: dict, aware_at: str) -> dict:
    return {
        "detected_at": triage["detected_at"],
        "aware_at": aware_at,
        "data_classification": scope["data_classification"],
        "uninspected_content": scope["uninspected_content"],
        "affected_subjects_count": scope["affected_subjects_count"],
        "subjects_count_is_lower_bound": scope["subjects_count_is_lower_bound"],
        "channel": triage["channel"],
        "destination": triage["destination"],
        "bytes_out": triage["bytes_out"],
    }


def _aware(triage: object, aware_at: str) -> None:
    if not isinstance(triage, dict) or not {"triage_id", "detected_at", "channel", "destination",
                                            "bytes_out"} <= set(triage):
        raise InvalidNotificationError("triage must be the triage output")
    detected = zulu(triage["detected_at"], "triage.detected_at", InvalidNotificationError)
    if zulu(aware_at, "aware_at", InvalidNotificationError) < detected:
        raise InvalidNotificationError(
            f"aware_at {aware_at} is before detection at {triage['detected_at']}"
        )


def compose_regulator_notification(triage: dict, scope: dict, authority_channels: dict, aware_at: str) -> dict:
    """Compose one notification per applicable regime.

    Parameters
    ----------
    triage / scope
        Reachable only when exfiltration is confirmed and the regulator
        threshold is met.
    authority_channels
        Authority channel reference per regime the operator is subject to:
        a non-empty subset of ``gdpr``, ``nis2``, ``dora``.
    aware_at
        Zulu instant the operator became aware; the clocks run from here.
    """
    s = confirmed_scope(scope, InvalidNotificationError, "notify regulator")
    if s["regulator_required"] is not True:
        raise InvalidNotificationError(
            f"notify regulator is reachable only when regulator_required is True; got {s['regulator_required']!r}"
        )
    _aware(triage, aware_at)
    if not isinstance(authority_channels, dict) or not authority_channels or not set(authority_channels) <= set(_REGIMES):
        raise InvalidNotificationError(
            f"authority_channels must map a non-empty subset of {sorted(_REGIMES)} to channel references"
        )
    aware = zulu(aware_at, "aware_at", InvalidNotificationError)
    notifications, skipped = [], []
    for regime in sorted(authority_channels):
        channel = pointer(authority_channels[regime], f"authority_channels.{regime}", InvalidNotificationError)
        if regime == "gdpr" and s["affected_subjects_count"] == 0 and not s["uninspected_content"]:
            skipped.append({"regime": "gdpr", "reason": "no_personal_data_affected"})
            continue
        basis, window = _REGIMES[regime]
        notifications.append({"regime": regime, "basis": basis, "authority_channel_ref": channel,
                              "due_at": (aware + window).strftime(FMT)})
    if not notifications:
        raise InvalidNotificationError(
            "a regulator notification is required but no configured authority channel applies: "
            f"skipped {skipped}"
        )
    return {
        "notification_id": digest(triage["triage_id"], "regulator"),
        "notifications": notifications,
        "skipped": skipped,
        "finding": _finding(triage, s, aware_at),
        "metric_stamps": ["kpi.notification_sla_compliance@v1", "kri.regulator_notification_overrun@v1"],
    }


def compose_subject_notification(
    triage: dict, scope: dict, high_risk_policy: dict, subject_channel: str, aware_at: str
) -> dict:
    """Determine whether data subjects must be told, and compose the notice if so.

    Reached on both branches of the regulator gate. Returns a determination
    whatever the outcome: ``required`` with its ``basis``, and a notice only
    when required.

    Parameters
    ----------
    high_risk_policy
        Exactly ``high_risk_classifications``: the classes the operator
        treats as likely high risk under GDPR Art. 34(1).
    subject_channel
        The pre-bound channel reference for data-subject notices.
    """
    s = confirmed_scope(scope, InvalidNotificationError, "notify affected party")
    _aware(triage, aware_at)
    p = exact_keys(high_risk_policy, {"high_risk_classifications"}, "high_risk_policy",
                   InvalidNotificationError)
    listed = p["high_risk_classifications"]
    if not isinstance(listed, list) or any(c not in _CLASSIFICATIONS for c in listed):
        raise InvalidNotificationError(
            f"high_risk_policy.high_risk_classifications must list values from {list(_CLASSIFICATIONS)}"
        )
    channel = pointer(subject_channel, "subject_channel", InvalidNotificationError)

    if s["affected_subjects_count"] == 0 and not s["uninspected_content"]:
        required, basis = False, "no_affected_subjects"
    elif s["uninspected_content"]:
        required, basis = True, "GDPR Art. 34(1): uninspected content treated as high risk"
    elif s["data_classification"] in listed:
        required, basis = True, "GDPR Art. 34(1): high-risk classification"
    else:
        required, basis = False, "below_high_risk_policy"
    return {
        "determination_id": digest(triage["triage_id"], "subjects"),
        "required": required,
        "basis": basis,
        "notice": ({"channel_ref": channel, "affected_subjects_count": s["affected_subjects_count"],
                    "subjects_count_is_lower_bound": s["subjects_count_is_lower_bound"],
                    "data_classification": s["data_classification"], "timing": "without undue delay"}
                   if required else None),
        "finding": _finding(triage, s, aware_at),
        "metric_stamps": ["kpi.notification_sla_compliance@v1"],
    }
