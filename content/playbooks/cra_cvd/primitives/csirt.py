"""National-CSIRT notification primitive.

Emits the pure JSON-native envelope the operator's CSIRT-notification
adapter dispatches when the coordinate_disclosure step needs to loop
in a national CSIRT (typically because the case has crossed CRA
Article 14(2) or 14(3) thresholds via the sibling cra_srp_notify
handoff, or because the operator's CVD policy names a coordinating
CSIRT unconditionally).

The primitive is not currently bound as a CACAO ``core_body`` step
body -- ``coordinate_disclosure`` has an out_args-collapse conflict
that defers its CORE binding to the EXTEND scope (see CORE-DEFERRED
marker on the CACAO step). It is landed here so the EXTEND scope can
wire it later without re-shaping the primitive surface.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output dict.
* **Public-bar safe.** All strings are canonicalised (NFKC + strip)
  and length-bounded; opaque handles are carried verbatim.
* **No default endpoint.** The framework ships no CSIRT endpoint;
  the operator wires the concrete endpoint at the compile target's
  config layer (typically via env-var indirection in the runtime,
  resolved to the ``csirt_endpoint`` argument here). An empty /
  missing endpoint fails closed with
  :class:`InvalidCsirtNotificationError`.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidCsirtNotificationError",
    "notify_national_csirt",
]


_SCHEMA_VERSION = "1.0.0"
_STREAM = "cra_cvd_csirt_notification"

_CASE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")
# ENISA / EU MS CSIRT codes are short lowercase tokens (e.g. "nl-ncsc",
# "de-cert-bund", "enisa"). Keep the pattern tight to catch obvious
# personal-name / free-text drift at this boundary.
_CSIRT_CODE_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

_ALLOWED_TRIGGERS = frozenset(
    {
        "actively_exploited",
        "policy_mandate",
        "cross_border_scope",
        "regulator_referral",
        "operator_discretion",
    }
)


class InvalidCsirtNotificationError(ValueError):
    """Raised when the notification inputs cannot produce a deterministic envelope."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidCsirtNotificationError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidCsirtNotificationError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_iso_z(value: object, field: str) -> str:
    text = _canonical_text(value, field)
    if not _ISO_Z_RE.match(text):
        raise InvalidCsirtNotificationError(
            f"{field} {text!r} is not ISO-8601 UTC 'YYYY-MM-DDTHH:MM:SSZ'"
        )
    return text


def notify_national_csirt(
    case_id: str,
    csirt_code: str,
    notification_trigger: str,
    notified_at: str,
    csirt_endpoint: str,
    summary: str,
    disclosure_target_date: str | None = None,
) -> dict:
    """Build the national-CSIRT notification envelope.

    Args:
        case_id: Operator-assigned CVD case identifier.
        csirt_code: Short lowercase code identifying the target
            national CSIRT (e.g. ``nl-ncsc``, ``de-cert-bund``,
            ``enisa``). Framework ships no default mapping; the
            operator wires the concrete code at the compile target's
            config layer.
        notification_trigger: Closed-alphabet reason for the
            notification; one of ``actively_exploited``,
            ``policy_mandate``, ``cross_border_scope``,
            ``regulator_referral``, ``operator_discretion``.
        notified_at: ISO-8601 UTC instant the notification is
            stamped at.
        csirt_endpoint: Opaque CSIRT endpoint handle the compile
            target resolved from operator config. Framework ships
            no default; empty / missing fails closed.
        summary: Short operator-authored summary of the case.
            Length-bounded to <= 2000 chars; carried verbatim.
        disclosure_target_date: Optional ISO-8601 UTC instant of the
            agreed coordinated public disclosure date. Included when
            the CSIRT is looped in for coordination on the embargo
            hold; omitted when the notification is a bare handoff
            (e.g. actively-exploited early warning before a
            disclosure date is agreed).

    Returns:
        JSON-native dict envelope carrying ``schema_version``,
        ``stream``, ``case_id``, ``csirt_code``,
        ``notification_trigger``, ``notified_at``, ``summary``,
        ``delivery`` (``csirt_endpoint``), and the optional
        ``disclosure_target_date``.

    Raises:
        InvalidCsirtNotificationError: any input fails validation, or
            ``csirt_endpoint`` is empty / whitespace.
    """
    cid = _canonical_text(case_id, "case_id")
    if not _CASE_ID_RE.match(cid):
        raise InvalidCsirtNotificationError(
            f"case_id {case_id!r} does not match the schema pattern"
        )

    code = _canonical_text(csirt_code, "csirt_code").lower()
    if not _CSIRT_CODE_RE.match(code):
        raise InvalidCsirtNotificationError(
            f"csirt_code {csirt_code!r} does not match the schema pattern"
        )

    trigger = _canonical_text(notification_trigger, "notification_trigger")
    if trigger not in _ALLOWED_TRIGGERS:
        raise InvalidCsirtNotificationError(
            f"notification_trigger {trigger!r} is not in the closed "
            f"alphabet {sorted(_ALLOWED_TRIGGERS)!r}"
        )

    ts = _require_iso_z(notified_at, "notified_at")

    endpoint = _canonical_text(csirt_endpoint, "csirt_endpoint")
    if not endpoint:
        raise InvalidCsirtNotificationError(
            "csirt_endpoint is empty; the framework ships no default "
            "CSIRT endpoint. Wire an operator-configured endpoint at "
            "the compile target's config layer."
        )

    summary_text = _canonical_text(summary, "summary")
    if len(summary_text) > 2000:
        raise InvalidCsirtNotificationError(
            "summary must be <= 2000 chars"
        )

    envelope: dict = {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "case_id": cid,
        "csirt_code": code,
        "notification_trigger": trigger,
        "notified_at": ts,
        "summary": summary_text,
        "delivery": {"csirt_endpoint": endpoint},
    }

    if disclosure_target_date is not None:
        envelope["disclosure_target_date"] = _require_iso_z(
            disclosure_target_date, "disclosure_target_date"
        )

    return envelope
