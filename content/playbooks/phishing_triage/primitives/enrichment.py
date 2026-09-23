"""Enrichment verdict join and suppression decision for phishing_triage.

Backs the ``enrich headers, URLs, attachments`` step, whose output drives
the ``known-benign sender or already seen?`` gate. The lookups themselves —
SPF / DKIM / DMARC evaluation, URL reputation, attachment static analysis,
the suppression cache — are adapter surfaces. What is deterministic is how
their results combine, and that is where the safety of this playbook sits:
the gate closes reports without paging anyone.

Two suppression lanes, deliberately asymmetric:

* **Already seen.** The report's case fingerprint matches a case opened
  within the suppression window. It links onto that case *whatever the
  verdicts say*: fifty users reporting the same phish must collapse onto
  the one case already handling it, and that phish is malicious by
  definition.
* **Known-benign sender.** The sender matches an operator allow entry. This
  lane requires DMARC ``pass`` — a known-benign address with failing DMARC
  is what spoofing looks like — *and* no ``malicious`` or ``suspicious``
  indicator, because a benign sender carrying a bad link is what a
  compromised partner account looks like. A claim that fails either test
  is recorded, not silently dropped.

The fingerprint (:func:`case_fingerprint`) errs toward *not* collapsing:
it keys on the full sender address, the normalised subject, the URL set
and the attachment digests. Two text-only messages from one domain with
different subjects — a BEC follow-up, say — stay separate cases.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta

from .intake import InvalidReportedMessageError, canonical_address, canonical_url

__all__ = [
    "AUTHENTICATION_RESULTS",
    "INDICATOR_VERDICTS",
    "InvalidMessageAssessmentError",
    "assess_reported_message",
    "case_fingerprint",
]

AUTHENTICATION_RESULTS: tuple[str, ...] = (
    "pass", "fail", "softfail", "neutral", "none", "temperror", "permerror",
)
INDICATOR_VERDICTS: tuple[str, ...] = ("malicious", "suspicious", "clean", "unknown")

_ZULU = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_POINTER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")
_ENVELOPE_KEYS = (
    "message_id", "sender", "sender_domain", "recipients", "subject", "urls",
    "attachments", "report_source",
)
_BENIGN_VETO = ("malicious", "suspicious")


class InvalidMessageAssessmentError(ValueError):
    """Enrichment inputs are malformed or inconsistent with the envelope."""


def case_fingerprint(message: dict) -> str:
    """SHA-256 naming the phishing *case* a canonical envelope belongs to.

    Fields are joined with the ASCII unit separator and the two sets with
    the record separator, so no field boundary can be forged by content.
    Recipients and timestamps are excluded on purpose: the same message
    delivered to many people is one case.
    """
    fields = [
        message["sender"],
        message["subject"].lower(),
        "\u001e".join(message["urls"]),
        "\u001e".join(a["sha256"] for a in message["attachments"]),
    ]
    return hashlib.sha256("\u001f".join(fields).encode("utf-8")).hexdigest()


def _instant(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not _ZULU.match(value):
        raise InvalidMessageAssessmentError(
            f"{field} must be a Zulu instant YYYY-MM-DDTHH:MM:SSZ, got {value!r}"
        )
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def _choice(value: object, allowed: tuple[str, ...], field: str) -> str:
    if not isinstance(value, str) or value.strip().lower() not in allowed:
        raise InvalidMessageAssessmentError(
            f"{field} must be one of {list(allowed)}, got {value!r}"
        )
    return value.strip().lower()


def _verdicts(raw: object, known: list[str], canon, field: str) -> dict[str, str]:
    """Join adapter verdicts onto the envelope's indicators.

    A verdict for an indicator the message does not carry means the adapter
    looked at something else — that fails loud. An indicator with no verdict
    is recorded as ``unknown``: absence of evidence is data, not an error.
    """
    if not isinstance(raw, dict):
        raise InvalidMessageAssessmentError(f"{field} must be an object")
    joined: dict[str, str] = {}
    for key, verdict in raw.items():
        try:
            ckey = canon(key)
        except InvalidReportedMessageError as exc:
            raise InvalidMessageAssessmentError(f"{field} key {key!r}: {exc}") from exc
        if ckey not in known:
            raise InvalidMessageAssessmentError(
                f"{field} has a verdict for {key!r}, which the message does not carry"
            )
        joined[ckey] = _choice(verdict, INDICATOR_VERDICTS, f"{field}[{key!r}]")
    return {k: joined.get(k, "unknown") for k in known}


def _canonical_digest(value: object) -> str:
    text = value.strip().lower() if isinstance(value, str) else ""
    if not _SHA256.match(text):
        raise InvalidReportedMessageError(f"not a SHA-256 digest: {value!r}")
    return text


def _benign_entry(value: object, index: int) -> str:
    text = value.strip() if isinstance(value, str) else value
    if isinstance(text, str) and "@" not in text:
        domain = text.lower()
        if not re.match(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$", domain):
            raise InvalidMessageAssessmentError(
                f"known_benign_senders[{index}] is neither an address nor a domain: {value!r}"
            )
        return domain
    try:
        return canonical_address(text, f"known_benign_senders[{index}]")
    except InvalidReportedMessageError as exc:
        raise InvalidMessageAssessmentError(str(exc)) from exc


def assess_reported_message(
    message: dict,
    authentication: dict,
    url_verdicts: dict,
    attachment_verdicts: dict,
    known_benign_senders: list,
    seen_cases: list,
    as_of: str,
    suppression_window_hours: int,
) -> dict:
    """Join enrichment verdicts onto the envelope and decide the suppression gate.

    Parameters
    ----------
    message
        The canonical envelope from :func:`.intake.validate_reported_message`.
    authentication
        Exactly ``spf``, ``dkim`` and ``dmarc``, each one of
        :data:`AUTHENTICATION_RESULTS`.
    url_verdicts / attachment_verdicts
        Verdict per URL / per SHA-256, from :data:`INDICATOR_VERDICTS`.
        Keys are canonicalised before the join.
    known_benign_senders
        Operator allow entries: a full address, or a bare domain matching
        every address at it.
    seen_cases
        Cases the suppression cache returned: ``fingerprint``, ``case_ref``,
        ``seen_at``. Only a case seen within the window before ``as_of``
        counts; a case recorded *after* ``as_of`` is inconsistent input and
        fails loud.
    as_of / suppression_window_hours
        The evaluation instant and the operator's window, a positive integer.

    Returns
    -------
    The assessment: envelope identity, fingerprint, authentication, the
    verdict-joined indicators, ``benign_or_seen`` (a real boolean — the gate
    reads it directly) and a ``suppression`` block naming the lane taken,
    the matched reference, and any benign claim that was refused and why.
    """
    if not isinstance(message, dict) or any(k not in message for k in _ENVELOPE_KEYS):
        raise InvalidMessageAssessmentError(
            f"message must be the intake envelope carrying {list(_ENVELOPE_KEYS)}"
        )
    if not isinstance(authentication, dict) or set(authentication) != {"spf", "dkim", "dmarc"}:
        raise InvalidMessageAssessmentError(
            "authentication must carry exactly spf, dkim and dmarc"
        )
    auth = {k: _choice(authentication[k], AUTHENTICATION_RESULTS, f"authentication.{k}")
            for k in ("spf", "dkim", "dmarc")}

    url_v = _verdicts(url_verdicts, message["urls"], canonical_url, "url_verdicts")
    digests = [a["sha256"] for a in message["attachments"]]
    att_v = _verdicts(attachment_verdicts, digests, _canonical_digest, "attachment_verdicts")

    if not isinstance(known_benign_senders, list):
        raise InvalidMessageAssessmentError("known_benign_senders must be a list")
    entries = [_benign_entry(v, i) for i, v in enumerate(known_benign_senders)]

    now = _instant(as_of, "as_of")
    window = suppression_window_hours
    if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
        raise InvalidMessageAssessmentError(
            f"suppression_window_hours must be a positive integer, got {window!r}"
        )
    if not isinstance(seen_cases, list):
        raise InvalidMessageAssessmentError("seen_cases must be a list")

    fingerprint = case_fingerprint(message)
    in_window: list[tuple[datetime, str]] = []
    for i, case in enumerate(seen_cases):
        where = f"seen_cases[{i}]"
        if not isinstance(case, dict) or set(case) != {"fingerprint", "case_ref", "seen_at"}:
            raise InvalidMessageAssessmentError(
                f"{where} must carry exactly fingerprint, case_ref, seen_at"
            )
        fp = case["fingerprint"]
        if not isinstance(fp, str) or not _SHA256.match(fp):
            raise InvalidMessageAssessmentError(f"{where}.fingerprint must be 64 lower-hex chars")
        ref = case["case_ref"]
        if not isinstance(ref, str) or not _POINTER.match(ref):
            raise InvalidMessageAssessmentError(f"{where}.case_ref is not a reference: {ref!r}")
        seen_at = _instant(case["seen_at"], f"{where}.seen_at")
        if seen_at > now:
            raise InvalidMessageAssessmentError(
                f"{where}.seen_at {case['seen_at']} is after as_of {as_of}"
            )
        if fp == fingerprint and now - seen_at <= timedelta(hours=window):
            in_window.append((seen_at, ref))

    urls = [{"url": u, "verdict": url_v[u]} for u in message["urls"]]
    attachments = [{"sha256": a["sha256"], "filename": a["filename"], "verdict": att_v[a["sha256"]]}
                   for a in message["attachments"]]
    flagged = sorted(
        [u["url"] for u in urls if u["verdict"] in _BENIGN_VETO]
        + [a["sha256"] for a in attachments if a["verdict"] in _BENIGN_VETO]
    )

    sender, domain = message["sender"], message["sender_domain"]
    matched_entry = next((e for e in entries if e == sender or e == domain), None)
    refused: str | None = None
    if matched_entry is not None and auth["dmarc"] != "pass":
        refused = "dmarc_not_pass"
    elif matched_entry is not None and flagged:
        refused = "flagged_indicator"

    if in_window:
        reason, matched = "already_seen", max(in_window)[1]
    elif matched_entry is not None and refused is None:
        reason, matched = "known_benign_sender", matched_entry
    else:
        reason, matched = None, None

    return {
        "message_id": message["message_id"],
        "fingerprint": fingerprint,
        "sender": sender,
        "sender_domain": domain,
        "recipients": list(message["recipients"]),
        "report_source": message["report_source"],
        "authentication": auth,
        "urls": urls,
        "attachments": attachments,
        "flagged_indicators": flagged,
        "benign_or_seen": reason is not None,
        "suppression": {
            "reason": reason,
            "matched_ref": matched,
            "refused_benign_claim": refused,
        },
    }
