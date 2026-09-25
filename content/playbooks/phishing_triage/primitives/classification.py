"""Intent resolution for the phishing_triage playbook.

Backs the ``classify intent`` step. The classifier itself — heuristics, a
model, or an analyst — is operator-bound; this playbook fixes only its
output contract, and this primitive is where that contract is enforced
before the ``route on intent`` switch reads it.

Every doubtful case resolves to ``unknown``, which routes to a human
analyst rather than to an automated response:

* the classifier abstained (it said ``unknown``);
* its confidence is below the operator's threshold;
* it emitted a label outside the closed enumeration — a misconfigured
  classifier then floods the manual-review queue, visibly, instead of
  triggering automated quarantines on a label nothing downstream
  understands. The raw label is kept so the flood is diagnosable.

Malformed *types* still fail loud: a confidence that is a boolean, NaN or
outside [0, 1] is a broken adapter, not a doubtful message.

The threshold is an integer percentage, not a fraction. CACAO playbook
variables have no float type, so a fractional threshold could only travel
as a string, and this primitive rejects strings; ``threat_intel_ingest``
carries its confidence threshold the same way. The comparison is
``confidence >= percent / 100``: IEEE division is correctly rounded, so
``29 / 100`` is exactly the double a classifier's ``0.29`` parses to and
the boundary holds, where ``confidence * 100 >= percent`` would drop it.
"""

from __future__ import annotations

import math
import unicodedata

__all__ = ["INTENTS", "InvalidIntentResolutionError", "resolve_intent"]

INTENTS: tuple[str, ...] = (
    "phishing",
    "credential_harvest",
    "malware_attached",
    "business_email_compromise",
    "unknown",
)


class InvalidIntentResolutionError(ValueError):
    """The classifier output or the threshold is malformed."""


def _unit_interval(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidIntentResolutionError(
            f"{field} must be a number, got {type(value).__name__}"
        )
    number = float(value)
    if math.isnan(number) or not 0.0 <= number <= 1.0:
        raise InvalidIntentResolutionError(f"{field} must be in [0, 1], got {value!r}")
    return number


def resolve_intent(classifier_output: dict, confidence_threshold_percent: int) -> dict:
    """Resolve the classifier's output to one routable intent.

    Parameters
    ----------
    classifier_output
        Exactly ``label`` (string) and ``confidence`` (number in [0, 1]).
    confidence_threshold_percent
        The operator's floor for acting on a label automatically, as an
        integer percentage from 1 to 100.

    Returns
    -------
    ``intent`` (always one of :data:`INTENTS`), the canonical
    ``classifier_label`` as received, ``confidence``,
    ``threshold_percent``, and a ``reason``: ``accepted``,
    ``classifier_abstained``, ``below_confidence_threshold`` or
    ``label_outside_enumeration``.
    """
    if not isinstance(classifier_output, dict) or set(classifier_output) != {"label", "confidence"}:
        raise InvalidIntentResolutionError(
            "classifier_output must carry exactly label and confidence"
        )
    raw_label = classifier_output["label"]
    if not isinstance(raw_label, str):
        raise InvalidIntentResolutionError(
            f"label must be a string, got {type(raw_label).__name__}"
        )
    label = unicodedata.normalize("NFKC", raw_label).strip().lower()
    confidence = _unit_interval(classifier_output["confidence"], "confidence")
    percent = confidence_threshold_percent
    if isinstance(percent, bool) or not isinstance(percent, int) or not 1 <= percent <= 100:
        raise InvalidIntentResolutionError(
            f"confidence_threshold_percent must be an integer from 1 to 100, got {percent!r}"
        )

    if label not in INTENTS:
        intent, reason = "unknown", "label_outside_enumeration"
    elif label == "unknown":
        intent, reason = "unknown", "classifier_abstained"
    elif confidence < percent / 100:
        intent, reason = "unknown", "below_confidence_threshold"
    else:
        intent, reason = label, "accepted"
    return {
        "intent": intent,
        "classifier_label": label,
        "confidence": confidence,
        "threshold_percent": percent,
        "reason": reason,
    }
