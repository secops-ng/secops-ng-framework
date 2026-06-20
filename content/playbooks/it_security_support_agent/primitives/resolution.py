"""Automated-resolution primitive (attempt-automated-resolution).

Captures the closed observation envelope read back from the operator's
self-service surface after the workflow ran the declared automated-
resolution action set. The actual self-service execution is the
compile target's job (an n8n HTTP node walking the operator's knowledge
base, a Temporal activity calling into the operator's self-service
API, a LangGraph tool node); this primitive only re-shapes and
re-validates the closed observation envelope so a free-text outcome
or an unbounded action set cannot slip past the step boundary.

Closed observation shape
------------------------

* ``outcome``              — one of ``resolved``, ``partial``,
                             ``not_attempted``, ``failed``.
* ``declared_action_set``  — ordered, deduplicated list of action ids
                             the workflow ran (shape
                             ``<a-z][a-z0-9_]*\\.[a-z][a-z0-9_]*$``);
                             for ``not_attempted`` the list MUST be
                             empty.
* ``observed_state``       — bounded free-text description of the
                             post-attempt state the workflow read back
                             (1..400 chars, single line, no control
                             characters). Public-bar discipline: no
                             personal names, no credentials, no
                             internal infra paths — the operator's
                             compile target is expected to sanitise
                             before this primitive sees it.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

__all__ = [
    "InvalidAutomatedResolutionError",
    "attempt_automated_resolution",
]


_ALLOWED_OUTCOMES = frozenset(
    {"resolved", "partial", "not_attempted", "failed"}
)
_ACTION_ID_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")


class InvalidAutomatedResolutionError(ValueError):
    """Raised when the automated-resolution inputs cannot produce a record."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidAutomatedResolutionError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidAutomatedResolutionError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def attempt_automated_resolution(
    support_request_record: dict,
    classification: dict,
    observation: dict,
) -> dict[str, Any]:
    """Validate and canonicalise the automated-resolution observation.

    Inputs
    ------
    support_request_record
        Closed envelope from
        :func:`...primitives.ingest.ingest_support_request`. Carried
        through for replay traceability; not mutated.
    classification
        Closed verdict from
        :func:`...primitives.classify.classify_request`. Carried
        through for replay traceability; the ``incident-shaped``
        category pins ``outcome == 'not_attempted'`` (the workflow
        does not run an automated resolution on a case that is
        already incident-shaped — the handoff step takes it).
    observation
        Operator-supplied observation envelope read back from the
        self-service surface: ``{outcome, declared_action_set,
        observed_state}``.

    Returns
    -------
    JSON-native dict with the closed observation envelope.
    """
    if not isinstance(support_request_record, dict):
        raise InvalidAutomatedResolutionError(
            "support_request_record must be an object, got "
            f"{type(support_request_record).__name__}"
        )
    if not isinstance(classification, dict):
        raise InvalidAutomatedResolutionError(
            "classification must be an object, got "
            f"{type(classification).__name__}"
        )
    if not isinstance(observation, dict):
        raise InvalidAutomatedResolutionError(
            "observation must be an object, got "
            f"{type(observation).__name__}"
        )

    category = classification.get("category")

    outcome = _canonical_text(
        observation.get("outcome"), "observation.outcome"
    )
    if outcome not in _ALLOWED_OUTCOMES:
        raise InvalidAutomatedResolutionError(
            f"observation.outcome {outcome!r} is not one of "
            f"{sorted(_ALLOWED_OUTCOMES)!r}"
        )
    if category == "incident-shaped" and outcome != "not_attempted":
        raise InvalidAutomatedResolutionError(
            "incident-shaped classification pins outcome='not_attempted'; "
            f"got {outcome!r} — the handoff step takes incident-shaped "
            "cases, the workflow does not run an automated resolution"
        )

    raw_actions = observation.get("declared_action_set")
    if not isinstance(raw_actions, list):
        raise InvalidAutomatedResolutionError(
            "observation.declared_action_set must be a list, got "
            f"{type(raw_actions).__name__}"
        )
    if outcome == "not_attempted" and raw_actions:
        raise InvalidAutomatedResolutionError(
            "observation.declared_action_set must be empty when "
            "outcome='not_attempted'"
        )
    seen: set[str] = set()
    actions: list[str] = []
    for index, raw in enumerate(raw_actions):
        if not isinstance(raw, str):
            raise InvalidAutomatedResolutionError(
                f"observation.declared_action_set[{index}] must be a string"
            )
        token = unicodedata.normalize("NFKC", raw).strip()
        if not token:
            raise InvalidAutomatedResolutionError(
                f"observation.declared_action_set[{index}] is empty after "
                "canonicalisation"
            )
        if len(token) > 128:
            raise InvalidAutomatedResolutionError(
                f"observation.declared_action_set[{index}] must be "
                "<= 128 chars"
            )
        if not _ACTION_ID_RE.match(token):
            raise InvalidAutomatedResolutionError(
                f"observation.declared_action_set[{index}] {raw!r} does "
                "not match the <family>.<slug> shape"
            )
        if token in seen:
            raise InvalidAutomatedResolutionError(
                f"observation.declared_action_set has duplicate entry "
                f"{token!r}"
            )
        seen.add(token)
        actions.append(token)

    if outcome in {"resolved", "partial", "failed"} and not actions:
        raise InvalidAutomatedResolutionError(
            f"observation.declared_action_set must be non-empty when "
            f"outcome={outcome!r}"
        )

    observed_state = _canonical_text(
        observation.get("observed_state"), "observation.observed_state"
    )
    if len(observed_state) > 400:
        raise InvalidAutomatedResolutionError(
            "observation.observed_state must be <= 400 chars"
        )
    if _CONTROL_CHAR_RE.search(observed_state):
        raise InvalidAutomatedResolutionError(
            "observation.observed_state must not contain control characters"
        )

    return {
        "outcome": outcome,
        "declared_action_set": actions,
        "observed_state": observed_state,
    }
