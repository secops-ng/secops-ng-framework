"""Per-intent response directives for the phishing_triage playbook.

Backs the five response branches the ``route on intent`` switch fans out
to. Each primitive composes a *directive* — an ordered list of actions for
the email-security gateway, the identity platform, finance or an analyst
queue to carry out. Execution is the adapters' concern; which actions a
branch takes, against which indicators, is decided here.

Every branch re-checks that the switch routed the right intent to it. A
mis-wired switch then fails loud at the first branch instead of, say,
freezing payments on a generic phishing report.

What each branch blocks, and why the rules differ:

* **phishing** blocks only URLs verdicted ``malicious`` or ``suspicious``.
  Lures routinely link to the impersonated brand's real site, and a URL
  block on a legitimate page lands on every user.
* **credential_harvest** blocks every URL not verdicted ``clean``: the
  harvest page is typically too new to have a reputation, and the branch
  exists because the message is believed to harvest credentials.
* **malware_attached** blocks every attachment not verdicted ``clean``. A
  digest block is exact and cheap to reverse.

A sanctioned phishing simulation reported through the credential-harvest
branch records its clicks for the click-rate KPI and does nothing else:
quarantining the lure, blocking its landing page or resetting the people
who clicked would break the exercise and lock out the people it trains.

``metric_stamps`` names only metrics this playbook declares in its
``metric_refs``; a test pins that.
"""

from __future__ import annotations

import hashlib
import re

from .intake import InvalidReportedMessageError, canonical_url

__all__ = [
    "InvalidResponseDirectiveError",
    "bec_response",
    "credential_harvest_response",
    "malware_attachment_response",
    "manual_review_route",
    "phishing_response",
]

_ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_ASSESSMENT_KEYS = (
    "message_id", "fingerprint", "sender", "recipients", "authentication",
    "urls", "attachments", "flagged_indicators",
)
_MTTR = "kpi.mttr_phishing_triage@v1"


class InvalidResponseDirectiveError(ValueError):
    """Inputs are malformed, or the switch routed the wrong intent here."""


def _assessment(assessment: object) -> dict:
    if not isinstance(assessment, dict) or any(k not in assessment for k in _ASSESSMENT_KEYS):
        raise InvalidResponseDirectiveError(
            f"assessment must be the enrichment output carrying {list(_ASSESSMENT_KEYS)}"
        )
    return assessment


def _branch(intent_resolution: object, expected: str) -> dict:
    if not isinstance(intent_resolution, dict) or "intent" not in intent_resolution:
        raise InvalidResponseDirectiveError("intent_resolution must carry an intent")
    if intent_resolution["intent"] != expected:
        raise InvalidResponseDirectiveError(
            f"route on intent sent {intent_resolution['intent']!r} to the {expected!r} branch"
        )
    return intent_resolution


def _pointer(value: object, field: str) -> str:
    if not isinstance(value, str) or not _POINTER.match(value):
        raise InvalidResponseDirectiveError(f"{field} is not a reference: {value!r}")
    return value


def _zulu(value: object, field: str) -> str:
    if not isinstance(value, str) or not _ZULU.match(value):
        raise InvalidResponseDirectiveError(
            f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}"
        )
    return value


def _events(raw: object, keys: set, field: str) -> list:
    if not isinstance(raw, list):
        raise InvalidResponseDirectiveError(f"{field} must be a list")
    for i, event in enumerate(raw):
        if not isinstance(event, dict) or set(event) != keys:
            raise InvalidResponseDirectiveError(
                f"{field}[{i}] must carry exactly {sorted(keys)}"
            )
    return raw


def _quarantine(a: dict) -> dict:
    return {"action": "quarantine_message", "message_id": a["message_id"],
            "mailboxes": list(a["recipients"])}


def _directive(a: dict, intent: str, actions: list, notify: list, stamps: list, **extra) -> dict:
    directive_id = hashlib.sha256(
        "\u001f".join((a["message_id"], intent, a["fingerprint"])).encode("utf-8")
    ).hexdigest()
    return {
        "directive_id": directive_id,
        "intent": intent,
        "message_id": a["message_id"],
        "fingerprint": a["fingerprint"],
        "actions": actions,
        "notify": notify,
        "metric_stamps": stamps,
        **extra,
    }


def phishing_response(assessment: dict, intent_resolution: dict) -> dict:
    """Generic phishing: quarantine, block the sender, block flagged URLs, notify.

    Only URLs verdicted ``malicious`` or ``suspicious`` are blocked.
    """
    a = _assessment(assessment)
    _branch(intent_resolution, "phishing")
    actions = [_quarantine(a), {"action": "block_sender", "sender": a["sender"]}]
    actions += [{"action": "block_url", "url": u["url"]}
                for u in a["urls"] if u["verdict"] in ("malicious", "suspicious")]
    return _directive(a, "phishing", actions, ["response_team"], [_MTTR])


def credential_harvest_response(
    assessment: dict,
    intent_resolution: dict,
    click_events: list,
    simulation_campaign_ref: str | None = None,
) -> dict:
    """Credential harvest: quarantine, block landing pages, reset whoever clicked.

    ``click_events`` are URL-activity records correlated to this message —
    ``identity``, ``url``, ``clicked_at``. A click on a URL the message does
    not carry means the correlation looked at something else, and fails loud.

    With ``simulation_campaign_ref`` set, the message is the operator's own
    sanctioned simulation: the directive records the clickers against the
    campaign for the click-rate KPI and takes no containment action.
    """
    a = _assessment(assessment)
    _branch(intent_resolution, "credential_harvest")
    carried = {u["url"] for u in a["urls"]}
    clickers: set[str] = set()
    for i, event in enumerate(_events(click_events, {"identity", "url", "clicked_at"}, "click_events")):
        try:
            url = canonical_url(event["url"], f"click_events[{i}].url")
        except InvalidReportedMessageError as exc:
            raise InvalidResponseDirectiveError(str(exc)) from exc
        if url not in carried:
            raise InvalidResponseDirectiveError(
                f"click_events[{i}] is a click on {url!r}, which the message does not carry"
            )
        _zulu(event["clicked_at"], f"click_events[{i}].clicked_at")
        clickers.add(_pointer(event["identity"], f"click_events[{i}].identity"))
    identities = sorted(clickers)

    if simulation_campaign_ref is not None:
        campaign = _pointer(simulation_campaign_ref, "simulation_campaign_ref")
        actions = [{"action": "record_simulation_clicks", "campaign_ref": campaign,
                    "identities": identities}]
        return _directive(a, "credential_harvest", actions, [],
                          ["kpi.phishing_sim_click_rate@v1"], simulation=True)

    actions = [_quarantine(a)]
    actions += [{"action": "block_url", "url": u["url"]} for u in a["urls"] if u["verdict"] != "clean"]
    actions += [{"action": "force_credential_reset", "identity": ident} for ident in identities]
    return _directive(a, "credential_harvest", actions, ["identity_team"], [_MTTR], simulation=False)


def malware_attachment_response(
    assessment: dict, intent_resolution: dict, file_open_events: list
) -> dict:
    """Malware attachment: quarantine, block attachment digests, hand off opened hosts.

    ``file_open_events`` are file-activity records — ``identity``,
    ``host_ref``, ``sha256``, ``opened_at`` — for recipients who opened an
    attachment. Each distinct host is handed to the endpoint owner with the
    digests opened on it. A message with no attachment at all cannot be
    acted on by this branch; classifier and enrichment disagree, and that
    fails loud rather than issuing an empty directive.
    """
    a = _assessment(assessment)
    _branch(intent_resolution, "malware_attached")
    if not a["attachments"]:
        raise InvalidResponseDirectiveError(
            "intent is malware_attached but the message carries no attachment"
        )
    carried = {att["sha256"] for att in a["attachments"]}
    opened: dict[tuple[str, str], set[str]] = {}
    keys = {"identity", "host_ref", "sha256", "opened_at"}
    for i, event in enumerate(_events(file_open_events, keys, "file_open_events")):
        digest = event["sha256"].lower() if isinstance(event["sha256"], str) else event["sha256"]
        if not isinstance(digest, str) or not _SHA256.match(digest) or digest not in carried:
            raise InvalidResponseDirectiveError(
                f"file_open_events[{i}].sha256 is not an attachment of this message: {event['sha256']!r}"
            )
        _zulu(event["opened_at"], f"file_open_events[{i}].opened_at")
        host = _pointer(event["host_ref"], f"file_open_events[{i}].host_ref")
        ident = _pointer(event["identity"], f"file_open_events[{i}].identity")
        opened.setdefault((host, ident), set()).add(digest)

    actions = [_quarantine(a)]
    actions += [{"action": "block_attachment", "sha256": att["sha256"], "filename": att["filename"]}
                for att in a["attachments"] if att["verdict"] != "clean"]
    actions += [{"action": "hand_off_host_investigation", "host_ref": host, "identity": ident,
                 "sha256s": sorted(digests)}
                for (host, ident), digests in sorted(opened.items())]
    return _directive(a, "malware_attached", actions, ["response_team"], [_MTTR])


def bec_response(assessment: dict, intent_resolution: dict, pending_payment_refs: list) -> dict:
    """Business email compromise: escalate to finance, freeze payments, open an identity case.

    ``pending_payment_refs`` are the payment instructions the finance
    adapter tied to this message. The identity sub-investigation targets the
    sender; ``sender_assessment`` records whether that address looks
    compromised (DMARC passed, so the mail really came from it) or
    impersonated (it did not). BEC routinely trips NIS2 / DORA reporting
    clocks, so the directive stamps the regulator-notification-overrun KRI
    and the timeline-completeness KPI alongside the MTTR clock — whether a
    report is owed is the incident-management playbook's decision, not this
    one's.
    """
    a = _assessment(assessment)
    _branch(intent_resolution, "business_email_compromise")
    if not isinstance(pending_payment_refs, list):
        raise InvalidResponseDirectiveError("pending_payment_refs must be a list")
    payments = sorted({_pointer(p, f"pending_payment_refs[{i}]")
                       for i, p in enumerate(pending_payment_refs)})
    basis = ("compromised_sender_account" if a["authentication"].get("dmarc") == "pass"
             else "impersonated_sender")
    actions = [{"action": "escalate_to_fraud_liaison", "message_id": a["message_id"]}]
    actions += [{"action": "freeze_payment_instruction", "payment_ref": p} for p in payments]
    actions.append({"action": "open_sub_investigation", "playbook": "playbook.identity_compromise@v1",
                    "principal": a["sender"], "basis": basis})
    stamps = [_MTTR, "kri.regulator_notification_overrun@v1", "kpi.timeline_completeness@v1"]
    return _directive(a, "business_email_compromise", actions,
                      ["fraud_finance_liaison", "identity_team"], stamps, sender_assessment=basis)


def manual_review_route(assessment: dict, intent_resolution: dict, queue_ref: str) -> dict:
    """Unknown intent: route the evidence packet to an analyst queue.

    The packet carries the verdict-joined indicators and the classifier's
    raw label, confidence and the reason it resolved to ``unknown``, so the
    analyst sees why the message is theirs. The outcome is requested back as
    labelled data for the classifier.
    """
    a = _assessment(assessment)
    resolution = _branch(intent_resolution, "unknown")
    evidence = {k: a[k] for k in ("fingerprint", "authentication", "urls", "attachments",
                                  "flagged_indicators")}
    classifier = {k: resolution.get(k) for k in ("classifier_label", "confidence", "threshold", "reason")}
    actions = [{"action": "route_to_analyst_queue", "queue_ref": _pointer(queue_ref, "queue_ref"),
                "evidence": evidence, "classifier": classifier}]
    return _directive(a, "unknown", actions, [], [], label_feedback_requested=True)
