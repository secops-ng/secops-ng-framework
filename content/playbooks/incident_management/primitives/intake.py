"""Intake-signal hydration primitive (intake significant-incident signal).

Derives the workflow-assigned ``__incident_id__`` deterministically
from the originating ``__signal_id__`` the upstream triage workflow
hands in. The id is a UUIDv5 over a namespaced seed, so the same
signal replayed through intake resolves to the same incident — intake
dedup is a property of the derivation, not of runtime state — and two
distinct signals can never collide onto one timeline.

The incident-timeline pattern (F-PT-02) consumes the id downstream:
``__incident_id__`` is CACAO-typed ``uuid`` and
:func:`..timeline_binding.open_timeline` requires a real
:class:`uuid.UUID`, so this primitive returns the canonical
36-character string form the compile targets marshal and the timeline
adapter re-parses.

Design constraints
------------------

* **Pure / replayable.** No clock reads, no network, no LLMs, no
  runtime state. Same ``signal_id`` ⇒ same ``incident_id`` on every
  target and every replay.
* **Public-bar safe.** The signal id must stay an opaque role-shaped
  pointer; free text with spaces and credential-shaped strings are
  rejected at the step boundary per AGENTS.md §3.
* **Namespace pinned.** The UUIDv5 namespace is the same fixed UUID
  the repo's OSCAL generators seed from; the seed string scopes the
  derivation to this playbook's intake step so another workflow
  deriving from the same signal id yields a different incident id.
"""

from __future__ import annotations

import re
import unicodedata
import uuid

__all__ = [
    "InvalidIncidentSignalError",
    "derive_incident_id",
]


# Same fixed namespace the gen_oscal_* generators use; the seed prefix
# below scopes it to this playbook's intake derivation.
_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
_SEED_PREFIX = "incident_management|intake|"

# Opaque role-shaped pointer: the shape the upstream triage workflow's
# signal identifiers carry (mirrors the lifecycle_event_ref convention).
_SIGNAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/@-]{0,255}$")


class InvalidIncidentSignalError(ValueError):
    """Raised when the intake signal cannot produce a valid incident id."""


def derive_incident_id(signal_id: str) -> str:
    """Derive the deterministic incident UUID for one intake signal.

    Inputs
    ------
    signal_id
        Identifier of the originating incident signal handed in by the
        upstream triage workflow (the CACAO ``__signal_id__``
        variable). Opaque role-shaped pointer; the framework does not
        interpret it beyond shape validation.

    Returns
    -------
    The canonical 36-character lowercase string form of
    ``UUIDv5(namespace, "incident_management|intake|<signal_id>")`` —
    the value the CACAO ``__incident_id__`` variable holds and the
    F-PT-02 open-timeline call re-parses into a :class:`uuid.UUID`.
    """
    if not isinstance(signal_id, str):
        raise InvalidIncidentSignalError(
            f"signal_id must be a string, got {type(signal_id).__name__}"
        )
    canonical = unicodedata.normalize("NFKC", signal_id).strip()
    if not canonical:
        raise InvalidIncidentSignalError(
            "signal_id is empty after canonicalisation"
        )
    if not _SIGNAL_ID_RE.match(canonical):
        raise InvalidIncidentSignalError(
            f"signal_id {signal_id!r} does not match the opaque "
            "role-shaped pointer pattern; free text and credential-"
            "shaped strings are out of scope per AGENTS.md §3"
        )
    return str(uuid.uuid5(_NAMESPACE, _SEED_PREFIX + canonical))
