"""Red-team scoping primitive (red-team scoping approval).

Packages the Art. 26(3) scoping submission and binds the competent
authority's outcome.

**Nothing is scoped when nothing is due.** A submission built on a
``tlpt_due: false`` decision would ask the authority to approve testing the
entity is not obliged to run, so it is refused rather than emitted as an
empty package. The out-of-scope evidence is the trigger envelope itself.

**Internal testers carry Art. 27 conditions.** Art. 27 permits internal
testers under additional requirements, so an ``internal`` posture must supply
the independence attestation the JC RTS names. External testers supply a
certification reference. Neither substitutes for the other, and the primitive
will not accept a posture with the wrong evidence attached — that mismatch is
precisely what a reviewer is checking.

**Third parties in the testing boundary must be represented.** Art. 26(3)
scoping covers the ICT third-party services within reach of the engagement,
so any provider the scope catalogue placed in the boundary must appear in the
submission's participants — or be named as an explicit carve-out with a
reason. Silent omission is refused: a provider dropped without a reason is
indistinguishable from a provider overlooked.

The submission is **packaged, not dispatched**. The
competent-authority channel is an adapter-bound surface the sibling EXTEND
card binds; this step records what will be submitted and the outcome once
returned.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output; participants and
  carve-outs are emitted sorted.
* **Public-bar safe.** Tester and provider identifiers are references,
  matched against closed regexes. No tester contact detail or contractual
  term is accepted.
* **Read-only-by-contract.** No submission is transmitted.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

__all__ = [
    "SCOPING_OUTCOMES",
    "InvalidRedTeamScopingError",
    "approve_red_team_scoping",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_REASON_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")

# Art. 26(3): the authority validates the scope. Deferral is a real outcome
# and is carried rather than collapsed into a failure.
SCOPING_OUTCOMES = frozenset({"approved", "deferred", "rejected"})

_SCHEMA_VERSION = "1.0.0"
_STREAM = "dora_tlpt_programme_scoping"


class InvalidRedTeamScopingError(ValueError):
    """Raised when a scoping input or Art. 26(3) / Art. 27 invariant fails."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidRedTeamScopingError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidRedTeamScopingError(f"{field} is empty after canonicalisation")
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidRedTeamScopingError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def derive_scoping_id(testing_window: str, tester_ref: str, outcome: str) -> str:
    """SHA-256(``<testing_window>|<tester_ref>|<outcome>``), first 16 hex."""
    payload = f"{testing_window}|{tester_ref}|{outcome}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]


def approve_red_team_scoping(
    dort_scope: dict,
    tlpt_trigger: dict,
    tester_ref: str,
    outcome: str,
    tester_certification_ref: str | None = None,
    tester_independence_attestation_ref: str | None = None,
    third_party_carve_outs: dict | None = None,
) -> dict:
    """Package the Art. 26(3) scoping submission and bind its outcome.

    Args:
        dort_scope: The catalogue envelope from the scope step.
        tlpt_trigger: The decision envelope from the trigger step
            (``__tlpt_trigger_decision__``). Must carry ``tlpt_due: true``.
        tester_ref: Reference to the red-team provider or internal unit.
        outcome: One of :data:`SCOPING_OUTCOMES`.
        tester_certification_ref: Certification reference. Required for an
            ``external`` posture, forbidden for ``internal``.
        tester_independence_attestation_ref: Independence attestation the
            JC RTS names. Required for an ``internal`` posture (Art. 27),
            forbidden for ``external``.
        third_party_carve_outs: Provider id to a slug reason, for providers
            in the testing boundary deliberately excluded from the engagement.

    Returns:
        JSON-native submission envelope with ``schema_version``, ``stream``,
        ``red_team_scoping_id``, ``testing_window``, ``tester_ref``,
        ``tester_posture``, the supplied evidence reference, sorted
        ``third_party_participants`` and ``third_party_carve_outs``,
        ``outcome`` and ``engagement_may_proceed``.

    Raises:
        InvalidRedTeamScopingError: any input fails validation, TLPT is not
            due, the tester evidence does not match the posture, or a
            provider in the boundary is neither a participant nor a
            reasoned carve-out.
    """
    for name, env in (("dort_scope", dort_scope), ("tlpt_trigger", tlpt_trigger)):
        if not isinstance(env, dict):
            raise InvalidRedTeamScopingError(
                f"{name} must be a mapping, got {type(env).__name__}"
            )
    if tlpt_trigger.get("tlpt_due") is not True:
        raise InvalidRedTeamScopingError(
            f"tlpt_trigger.tlpt_due is not true (basis "
            f"{tlpt_trigger.get('basis')!r}); there is nothing to scope, and a "
            f"submission here would ask the authority to approve testing the "
            f"entity is not obliged to run"
        )
    window = _canonical_text(dort_scope.get("testing_window"), "dort_scope.testing_window")
    if window != tlpt_trigger.get("testing_window"):
        raise InvalidRedTeamScopingError(
            f"dort_scope.testing_window {window!r} does not match "
            f"tlpt_trigger.testing_window {tlpt_trigger.get('testing_window')!r}"
        )
    posture = _canonical_text(
        tlpt_trigger.get("tester_posture"), "tlpt_trigger.tester_posture"
    )

    tester = _require_pattern(tester_ref, "tester_ref", _REF_RE)
    result = _canonical_text(outcome, "outcome")
    if result not in SCOPING_OUTCOMES:
        raise InvalidRedTeamScopingError(
            f"outcome {result!r} not in {sorted(SCOPING_OUTCOMES)}"
        )

    if posture == "external":
        if tester_independence_attestation_ref is not None:
            raise InvalidRedTeamScopingError(
                "tester_independence_attestation_ref is for an internal "
                "posture (Art. 27); an external tester supplies a "
                "certification reference"
            )
        if tester_certification_ref is None:
            raise InvalidRedTeamScopingError(
                "an external tester_posture requires tester_certification_ref"
            )
        evidence_field = "tester_certification_ref"
        evidence = _require_pattern(
            tester_certification_ref, evidence_field, _REF_RE
        )
    else:
        if tester_certification_ref is not None:
            raise InvalidRedTeamScopingError(
                "tester_certification_ref is for an external posture; an "
                "internal tester supplies the Art. 27 independence attestation"
            )
        if tester_independence_attestation_ref is None:
            raise InvalidRedTeamScopingError(
                "an internal tester_posture requires "
                "tester_independence_attestation_ref — Art. 27 permits internal "
                "testers only under the additional conditions the JC RTS names"
            )
        evidence_field = "tester_independence_attestation_ref"
        evidence = _require_pattern(
            tester_independence_attestation_ref, evidence_field, _REF_RE
        )

    in_boundary = {
        p
        for entry in (dort_scope.get("functions") or [])
        if isinstance(entry, dict)
        for p in (entry.get("third_parties") or [])
    }
    carve_outs_raw = third_party_carve_outs or {}
    if not isinstance(carve_outs_raw, dict):
        raise InvalidRedTeamScopingError(
            "third_party_carve_outs must be a mapping of provider id to reason"
        )
    carve_outs = {
        _require_pattern(k, "third_party_carve_outs key", _ID_RE):
            _require_pattern(v, f"third_party_carve_outs[{k!r}]", _REASON_RE)
        for k, v in carve_outs_raw.items()
    }
    stray = sorted(set(carve_outs) - in_boundary)
    if stray:
        raise InvalidRedTeamScopingError(
            f"third_party_carve_outs names {stray}, absent from the scope "
            f"catalogue's testing boundary; carving out a provider that was "
            f"never in scope misrepresents the submission"
        )
    participants = sorted(in_boundary - set(carve_outs))

    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "red_team_scoping_id": derive_scoping_id(window, tester, result),
        "testing_window": window,
        "tester_ref": tester,
        "tester_posture": posture,
        evidence_field: evidence,
        "third_party_participants": participants,
        "third_party_carve_outs": dict(sorted(carve_outs.items())),
        "outcome": result,
        "engagement_may_proceed": result == "approved",
    }
