"""Comms plan for the ransomware_containment playbook.

Backs the ``comms plan`` step: page the IR lead and the comms officer, and
draft the NIS2 Article 23(4)(a) early warning. The draft is **staged for
human sign-off and never auto-sent** — a regulator notification is a legal
act, and this primitive only prepares it.

The early-warning clock runs 24 hours from initial detection, as the step
defines it. ``within_clock`` records whether the draft was prepared inside
it; a late draft stamps the regulator-notification-overrun KRI's input
rather than hiding the lateness.

The draft carries what the playbook knows: ransomware is a malicious act
by definition, so the "suspected unlawful or malicious act" field of an
early warning is set; the cross-border-impact assessment is left to the
signer, who knows the operator's footprint.
"""

from __future__ import annotations

from datetime import timedelta

from ._common import boolean, confirmed_triage, digest, exact_keys, pointer, zulu

__all__ = ["InvalidCommsPlanError", "compose_comms_plan"]

_EARLY_WARNING = timedelta(hours=24)


class InvalidCommsPlanError(ValueError):
    """Inputs are malformed, inconsistent, or the event is not confirmed."""


def compose_comms_plan(triage: dict, backup_selection: dict, channels: dict, drafted_at: str) -> dict:
    """Compose the notifications and the staged early-warning draft.

    Parameters
    ----------
    triage
        The triage record; reachable only when the event is confirmed.
    backup_selection
        The output of :func:`.backup.select_known_good_snapshot`.
    channels
        Exactly ``ir_lead`` and ``comms_officer`` channel references.
    drafted_at
        Zulu instant the draft is prepared; before detection is inconsistent
        input and fails loud.
    """
    t = confirmed_triage(triage, InvalidCommsPlanError, "comms plan")
    if not isinstance(backup_selection, dict) or not {
        "latest_known_good_snapshot", "snapshot_integrity_ok"} <= set(backup_selection):
        raise InvalidCommsPlanError("backup_selection must be the backup-verification output")
    integrity = boolean(backup_selection["snapshot_integrity_ok"],
                        "backup_selection.snapshot_integrity_ok", InvalidCommsPlanError)
    c = exact_keys(channels, {"ir_lead", "comms_officer"}, "channels", InvalidCommsPlanError)
    lead = pointer(c["ir_lead"], "channels.ir_lead", InvalidCommsPlanError)
    officer = pointer(c["comms_officer"], "channels.comms_officer", InvalidCommsPlanError)
    detected = zulu(t["detected_at"], "triage.detected_at", InvalidCommsPlanError)
    drafted = zulu(drafted_at, "drafted_at", InvalidCommsPlanError)
    if drafted < detected:
        raise InvalidCommsPlanError(
            f"drafted_at {drafted_at} is before detection at {t['detected_at']}"
        )
    due = detected + _EARLY_WARNING
    return {
        "plan_id": digest(t["triage_id"], "comms_plan"),
        "notifications": [
            {"role": "ir_lead", "channel_ref": lead},
            {"role": "comms_officer", "channel_ref": officer},
        ],
        "early_warning": {
            "regulation": "NIS2 Art. 23(4)(a)",
            "status": "staged_for_sign_off",
            "auto_send": False,
            "due_at": due.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "drafted_at": drafted_at,
            "within_clock": drafted <= due,
            "suspected_malicious_act": True,
            "cross_border_impact": "for_signer_to_assess",
            "facts": {
                "detected_at": t["detected_at"],
                "host_ref": t["host_ref"],
                "identity_ref": t["identity_ref"],
                "latest_known_good_snapshot": backup_selection["latest_known_good_snapshot"],
                "snapshot_integrity_ok": integrity,
            },
        },
        "metric_stamps": [
            "kpi.notification_sla_compliance@v1",
            "kpi.timeline_completeness@v1",
            "kri.regulator_notification_overrun@v1",
        ],
    }
