"""Oversight roster for the ai_human_oversight playbook.

Backs the ``establish_oversight_roster`` step. The Art. 26(2) assignment of
Regulation (EU) 2024/1689 names who oversees a high-risk AI system; this
step makes it operational for one review window: who is on watch, what each
is empowered to do, and who can be reached when an intervention is needed.

**Authority is the limb that matters most.** Art. 14(4)(d) and (e) require
the overseer to be able to decide not to use the system, to disregard,
override or reverse its output, and to intervene in or interrupt its
operation. A roster entry without delegated power for all four produces an
overseer who cannot lawfully oversee, however well briefed, so such an entry
is recorded with its missing powers and does not count as empowered. The
roster is effective only when at least one empowered natural person on watch
is reachable for the window.
"""

from __future__ import annotations

from ._common import POWERS, boolean, choice, digest, exact_keys, interval, optional_pointer, pointer, zulu

__all__ = ["InvalidOversightRosterError", "resolve_oversight_roster"]


class InvalidOversightRosterError(ValueError):
    """The window or a roster entry is malformed."""


def resolve_oversight_roster(deployment_id: str, oversight_cycle: str, entries: list, resolved_at: str) -> dict:
    """Record the watch for the window, entry by entry.

    Parameters
    ----------
    deployment_id
        The deployment this cycle covers.
    oversight_cycle
        The review window as an RFC 3339 interval ``<start>/<end>``.
    entries
        A non-empty list, each exactly ``person_ref``, ``natural_person``,
        ``on_watch`` and ``reachable`` (real booleans), ``powers`` (the
        delegated Art. 14(4)(d)-(e) powers, from ``decline_use``,
        ``disregard_output``, ``override_or_reverse_output`` and
        ``interrupt_operation``) and ``authority_ref`` (the delegation
        record, or unset).
    resolved_at
        Zulu instant the roster is resolved.
    """
    deployment = pointer(deployment_id, "deployment_id", InvalidOversightRosterError)
    interval(oversight_cycle, "oversight_cycle", InvalidOversightRosterError)
    zulu(resolved_at, "resolved_at", InvalidOversightRosterError)
    if not isinstance(entries, list) or not entries:
        raise InvalidOversightRosterError("entries must be a non-empty list")

    records, seen = [], set()
    for i, e in enumerate(entries):
        x = exact_keys(e, {"person_ref", "natural_person", "on_watch", "reachable", "powers", "authority_ref"},
                       f"entries[{i}]", InvalidOversightRosterError)
        person = pointer(x["person_ref"], f"entries[{i}].person_ref", InvalidOversightRosterError)
        if person in seen:
            raise InvalidOversightRosterError(f"{person!r} is on the roster twice")
        seen.add(person)
        natural = boolean(x["natural_person"], f"entries[{i}].natural_person", InvalidOversightRosterError)
        on_watch = boolean(x["on_watch"], f"entries[{i}].on_watch", InvalidOversightRosterError)
        reachable = boolean(x["reachable"], f"entries[{i}].reachable", InvalidOversightRosterError)
        if not isinstance(x["powers"], list):
            raise InvalidOversightRosterError(f"entries[{i}].powers must be a list")
        powers = sorted({choice(p, POWERS, f"entries[{i}].powers[{j}]", InvalidOversightRosterError)
                         for j, p in enumerate(x["powers"])}, key=POWERS.index)
        authority = optional_pointer(x["authority_ref"], f"entries[{i}].authority_ref", InvalidOversightRosterError)
        missing = [p for p in POWERS if p not in powers]
        empowered = natural and authority is not None and not missing
        records.append({"person_ref": person, "natural_person": natural, "on_watch": on_watch,
                        "reachable": reachable, "powers": powers, "missing_powers": missing,
                        "authority_ref": authority, "empowered": empowered})
    records.sort(key=lambda r: r["person_ref"])
    empowered = [r["person_ref"] for r in records if r["empowered"] and r["on_watch"]]
    reachable = [r["person_ref"] for r in records if r["empowered"] and r["on_watch"] and r["reachable"]]
    return {
        "roster_id": digest(deployment, oversight_cycle, "roster", resolved_at, *[r["person_ref"] for r in records]),
        "deployment_id": deployment,
        "oversight_cycle": oversight_cycle,
        "entries": records,
        "empowered_overseers": empowered,
        "reachable_empowered_overseers": reachable,
        "not_empowered": [r["person_ref"] for r in records if not r["empowered"]],
        "effective": bool(reachable),
        "resolved_at": resolved_at,
        "metric_stamps": [],
    }
