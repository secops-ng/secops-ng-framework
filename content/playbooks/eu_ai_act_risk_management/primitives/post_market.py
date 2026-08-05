"""Post-market monitoring primitive (monitor post-market signals).

Records one Article 72 post-market observation against the current register
and decides whether it reopens the Art. 9(2) cycle.

This is the step that makes Art. 9 a loop rather than a one-off assessment.
Art. 9(2)(c) requires the evaluation of risks identified from post-market
monitoring data gathered under Art. 72, so a signal that reveals a new or
changed hazard has to produce a *new iteration* carrying a ``9(2)(c)``-origin
risk — it cannot be patched into the closed iteration it was observed
against. ``reopens_art9_cycle`` is that decision, and it is derived from the
signal kind rather than left to the caller.

**Art. 73 is flagged, never performed.** A serious incident triggers the
Art. 73 reporting obligation on its own clock, and that surface is a
different artifact in this repo
(``content/mappings/eu_ai_act/article-73-serious-incident-reporting.yaml``).
So a ``serious_incident`` signal sets ``art73_escalation_required`` and stops
there. Emitting a report from here would put a statutory notification behind
a risk-management step, where nothing is watching its deadline.

**A quiet window is a recorded observation, not an absent one.** The
``no_change`` kind exists so that a monitoring period which surfaced nothing
still produces a record. Art. 72 requires monitoring to be active across the
lifetime; an absence of records is indistinguishable from an absence of
monitoring, and the honest way to say "we looked and saw nothing" is to say
it.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output; affected risk ids
  are emitted sorted.
* **Public-bar safe.** Signal ids and evidence references are matched against
  closed regexes. No observation *narrative* is accepted, because a
  post-market signal describes real-world harm and is the most likely place
  in this playbook for personal data to enter a public-bar artifact.
* **Read-only-by-contract.** No notification is dispatched and no register is
  mutated; the envelope is the record and the hand-off.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "SIGNAL_KINDS",
    "InvalidPostMarketSignalError",
    "record_post_market_signal",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# Signal kinds and whether each reopens the Art. 9(2) cycle. Held as a
# mapping rather than two sets so the reopen decision cannot drift out of
# step with the vocabulary.
SIGNAL_KINDS: dict[str, bool] = {
    "no_change": False,
    "performance_drift": True,
    "unforeseen_risk": True,
    "misuse_observed": True,
    "serious_incident": True,
}

_ART73_KIND = "serious_incident"

_SCHEMA_VERSION = "1.0.0"
_STREAM = "eu_ai_act_risk_management_post_market"


class InvalidPostMarketSignalError(ValueError):
    """Raised when a post-market input or Art. 72 invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidPostMarketSignalError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidPostMarketSignalError(
            f"{field} is empty after canonicalisation"
        )
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidPostMarketSignalError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def record_post_market_signal(
    risk_register: dict,
    observation: dict,
) -> dict:
    """Record one Art. 72 observation and decide whether Art. 9(2) reopens.

    Args:
        risk_register: The register envelope from the assessment step
            (``__risk_register_id__``), so the observation is anchored to the
            iteration it was observed against.
        observation: Mapping with ``signal_id``, ``signal_kind`` (a key of
            :data:`SIGNAL_KINDS`), ``observed_at`` (ISO-8601 ``Z`` instant,
            supplied rather than clock-read), ``evidence_ref``, and optional
            ``affects_risk_ids`` naming existing register entries the signal
            bears on.

    Returns:
        JSON-native envelope with ``schema_version``, ``stream``,
        ``signal_id``, ``ai_system_id``, ``risk_register_id``,
        ``observed_against_iteration``, ``signal_kind``, ``observed_at``,
        ``evidence_ref``, sorted ``affects_risk_ids``,
        ``reopens_art9_cycle``, and ``art73_escalation_required``.

    Raises:
        InvalidPostMarketSignalError: any input fails validation, the signal
            kind is unknown, or ``affects_risk_ids`` names an entry absent
            from the supplied register.
    """
    if not isinstance(risk_register, dict):
        raise InvalidPostMarketSignalError(
            f"risk_register must be a mapping, got {type(risk_register).__name__}"
        )
    register_id = _require_pattern(
        risk_register.get("risk_register_id"),
        "risk_register.risk_register_id",
        _REF_RE,
    )
    system = _require_pattern(
        risk_register.get("ai_system_id"), "risk_register.ai_system_id", _REF_RE
    )
    iteration = _require_pattern(
        risk_register.get("iteration_id"), "risk_register.iteration_id", _REF_RE
    )
    known_risk_ids = {
        e.get("risk_id")
        for e in (risk_register.get("entries") or [])
        if isinstance(e, dict)
    }

    if not isinstance(observation, dict):
        raise InvalidPostMarketSignalError(
            f"observation must be a mapping, got {type(observation).__name__}"
        )
    signal_id = _require_pattern(
        observation.get("signal_id"), "observation.signal_id", _ID_RE
    )
    kind = _canonical_text(observation.get("signal_kind"), "observation.signal_kind")
    if kind not in SIGNAL_KINDS:
        raise InvalidPostMarketSignalError(
            f"observation.signal_kind {kind!r} not in {sorted(SIGNAL_KINDS)}"
        )
    observed_at = _canonical_text(
        observation.get("observed_at"), "observation.observed_at"
    )
    if not _ISO_Z_RE.match(observed_at):
        raise InvalidPostMarketSignalError(
            f"observation.observed_at {observed_at!r} is not an ISO-8601 "
            f"UTC instant (YYYY-MM-DDTHH:MM:SSZ)"
        )
    evidence_ref = _require_pattern(
        observation.get("evidence_ref"), "observation.evidence_ref", _REF_RE
    )

    raw_affects = observation.get("affects_risk_ids") or []
    if isinstance(raw_affects, str) or not isinstance(raw_affects, (list, tuple)):
        raise InvalidPostMarketSignalError(
            "observation.affects_risk_ids must be a list of register risk ids"
        )
    affects = sorted({
        _require_pattern(
            r, f"observation.affects_risk_ids[{i}]", _ID_RE
        )
        for i, r in enumerate(raw_affects)
    })
    dangling = [r for r in affects if r not in known_risk_ids]
    if dangling:
        raise InvalidPostMarketSignalError(
            f"observation.affects_risk_ids names {dangling}, absent from "
            f"register {register_id!r}; a signal bearing on a risk the "
            f"register does not carry is a new hazard, and belongs in the next "
            f"iteration as a 9(2)(c) entry rather than as a reference to an "
            f"entry that does not exist"
        )

    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "signal_id": signal_id,
        "ai_system_id": system,
        "risk_register_id": register_id,
        "observed_against_iteration": iteration,
        "signal_kind": kind,
        "observed_at": observed_at,
        "evidence_ref": evidence_ref,
        "affects_risk_ids": affects,
        "reopens_art9_cycle": SIGNAL_KINDS[kind],
        "art73_escalation_required": kind == _ART73_KIND,
    }
