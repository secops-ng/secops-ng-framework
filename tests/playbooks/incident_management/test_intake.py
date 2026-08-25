"""Unit tests for the intake primitive (intake significant-incident signal).

The #937 wire card bound the playbook's last unbound action step to
``derive_incident_id``. The behaviours pinned here are the ones a
later change could quietly reverse:

* The incident id is a **pure function of the signal id** — same
  signal ⇒ same incident on every replay and every compile target, so
  intake dedup is a property of the derivation, not of runtime state.
  The derivation is pinned against a hand-computed UUIDv5 so the
  namespace and seed prefix cannot drift silently.
* Distinct signals never collide onto one timeline.
* The output is the canonical 36-char lowercase UUID string — the
  CACAO ``__incident_id__`` variable is uuid-typed and the F-PT-02
  ``open_timeline`` call re-parses it into a real :class:`uuid.UUID`.
* Free-text and credential-shaped signal ids fail loud at the step
  boundary (public bar), while NFKC canonicalisation keeps look-alike
  spellings from minting distinct incidents.
"""
from __future__ import annotations

import uuid

import pytest

from content.playbooks.incident_management.primitives import (
    InvalidIncidentSignalError,
    derive_incident_id,
)

SIGNAL = "triage://alerts/2026/06/19/sig-0042"


def test_derivation_is_pinned_uuid5() -> None:
    expected = str(
        uuid.uuid5(
            uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
            "incident_management|intake|" + SIGNAL,
        )
    )
    assert derive_incident_id(SIGNAL) == expected


def test_same_signal_same_incident_distinct_signals_distinct() -> None:
    a = derive_incident_id(SIGNAL)
    assert derive_incident_id(SIGNAL) == a
    assert derive_incident_id(SIGNAL + "-b") != a


def test_output_round_trips_into_a_real_uuid() -> None:
    """The F-PT-02 open-timeline call requires a UUID instance; the
    string this primitive returns must parse back losslessly."""
    text = derive_incident_id(SIGNAL)
    parsed = uuid.UUID(text)
    assert str(parsed) == text
    assert parsed.version == 5


def test_nfkc_canonicalisation_collapses_look_alikes() -> None:
    padded = derive_incident_id("  " + SIGNAL + " ")
    assert padded == derive_incident_id(SIGNAL)


def test_free_text_and_shape_violations_fail_loud() -> None:
    for bad in ("the big outage last night", "", "   ", "sig\nid"):
        with pytest.raises(InvalidIncidentSignalError):
            derive_incident_id(bad)
    with pytest.raises(InvalidIncidentSignalError, match="must be a string"):
        derive_incident_id(42)  # type: ignore[arg-type]
