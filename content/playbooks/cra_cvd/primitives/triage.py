"""CVD triage primitive (triage).

Derives the deterministic ``__triage_verdict__`` and
``__actively_exploited__`` pair from the operator's triage
observations. The verdict vocabulary and its short-circuit semantics
are the ones the playbook's variable table pins: non-actionable
verdicts route to a reporter-facing rationale communication; only
``valid_needs_fix`` takes the develop → validate → coordinate →
publish lane. When ``actively_exploited`` is true the caller forks a
sibling ``cra_srp_notify`` run — that fork is workflow topology, not
this primitive's concern; the flag simply travels.

Verdict precedence (first match wins, pinned by the unit suite):

1. ``out_of_scope``     — the report is not in the product's scope.
2. ``duplicate``        — the observations name an existing case.
3. ``not_reproducible`` — reproduction failed.
4. ``valid_no_action``  — reproduced and in scope, but a documented
   compensating control makes a fix unnecessary.
5. ``valid_needs_fix``  — everything else: reproduced, in scope,
   no compensating control.

Design constraints
------------------

* **Pure / replayable.** No network, no clock reads, no LLMs — the
  judgement lives in the operator's observations; the primitive only
  derives the verdict from them, deterministically.
* **Booleans only.** ``in_scope``, ``reproduced``, and
  ``actively_exploited`` must be real JSON booleans — the string
  ``"false"`` is truthy, and a stringified flag here would mis-route
  a vulnerability lifecycle.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidTriageObservationsError",
    "triage_case",
]


_CASE_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")


class InvalidTriageObservationsError(ValueError):
    """Raised when the observations cannot produce a valid verdict."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidTriageObservationsError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidTriageObservationsError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise InvalidTriageObservationsError(
            f"{field} must be a boolean, got {type(value).__name__}; a "
            "stringified flag would mis-route the lifecycle"
        )
    return value


def triage_case(case_id: str, observations: dict) -> dict:
    """Derive the triage verdict for one CVD case.

    Inputs
    ------
    case_id
        The case identifier assigned at intake.
    observations
        Operator-supplied JSON-native triage observations. Required
        boolean keys: ``in_scope``, ``reproduced``,
        ``actively_exploited``. Optional: ``duplicate_of`` (an existing
        case id — presence makes the verdict ``duplicate``),
        ``compensating_control`` (a non-empty description — with
        ``reproduced`` and ``in_scope`` both true it makes the verdict
        ``valid_no_action``).

    Returns
    -------
    JSON-native dict::

        {
            "case_id": "...",
            "triage_verdict": "<one of the five documented verdicts>",
            "actively_exploited": bool,
            "rationale": "<deterministic one-liner>"
        }
    """
    cid = _canonical_text(case_id, "case_id")
    if not _CASE_ID_RE.match(cid):
        raise InvalidTriageObservationsError(
            f"case_id {case_id!r} does not match the case-identifier shape"
        )
    if not isinstance(observations, dict):
        raise InvalidTriageObservationsError(
            f"observations must be an object, got "
            f"{type(observations).__name__}"
        )

    in_scope = _require_bool(observations.get("in_scope"), "observations.in_scope")
    reproduced = _require_bool(
        observations.get("reproduced"), "observations.reproduced"
    )
    actively_exploited = _require_bool(
        observations.get("actively_exploited"),
        "observations.actively_exploited",
    )

    duplicate_of = observations.get("duplicate_of")
    if duplicate_of is not None:
        duplicate_of = _canonical_text(duplicate_of, "observations.duplicate_of")
        if not _CASE_ID_RE.match(duplicate_of):
            raise InvalidTriageObservationsError(
                f"observations.duplicate_of {duplicate_of!r} does not match "
                "the case-identifier shape"
            )
        if duplicate_of == cid:
            raise InvalidTriageObservationsError(
                "observations.duplicate_of names the case itself"
            )

    compensating = observations.get("compensating_control")
    if compensating is not None:
        compensating = _canonical_text(
            compensating, "observations.compensating_control"
        )

    if not in_scope:
        verdict = "out_of_scope"
        rationale = "report is outside the product's documented CVD scope"
    elif duplicate_of is not None:
        verdict = "duplicate"
        rationale = f"duplicate of existing case {duplicate_of}"
    elif not reproduced:
        verdict = "not_reproducible"
        rationale = "reproduction failed against the reported versions"
    elif compensating is not None:
        verdict = "valid_no_action"
        rationale = f"compensating control applies: {compensating}"
    else:
        verdict = "valid_needs_fix"
        rationale = "reproduced in scope with no compensating control"

    return {
        "case_id": cid,
        "triage_verdict": verdict,
        "actively_exploited": actively_exploited,
        "rationale": rationale,
    }
