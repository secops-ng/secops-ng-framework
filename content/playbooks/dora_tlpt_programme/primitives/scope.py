"""DORT-scope composition primitive (define DORT scope).

Composes the digital-operational-resilience-testing scope catalogue for one
testing-programme window from the three registers the operator already keeps:
the business-service register of ICT-supported critical or important
functions (identified per Art. 8), the ICT-asset register, and the ICT
third-party service-provider register (Art. 28).

**A function with no supporting assets is a scope gap, not an omission.**
Art. 24 requires the testing programme to cover ICT systems supporting
critical or important functions, so a function the asset register cannot
resolve means the operator cannot demonstrate coverage of it. That is
reported as ``unresolved_functions`` and makes the catalogue incomplete,
rather than silently shrinking the scope to whatever happened to resolve —
which is the failure mode that produces a testing programme that looks
complete because it tested less.

Third-party providers are composed into scope for **testing reach only**.
Third-party risk discharge is the ``supply_chain_security`` playbook's
surface; naming a provider here says its services fall inside the testing
boundary, nothing more.

Design constraints
------------------

* **Pure / replayable.** No network calls, no clock reads, no LLMs.
* **Determinism.** Same inputs => byte-identical output; every collection is
  emitted sorted.
* **Public-bar safe.** Function, asset and provider identifiers are matched
  against closed regexes. No service *descriptions* are accepted: a business
  service register entry names commercial relationships, and its prose is
  where a public-bar artifact would leak them.
* **Read-only-by-contract.** The three registers are read; none is written.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "InvalidDortScopeError",
    "define_dort_scope",
]


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_WINDOW_RE = re.compile(r"^\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}$")

_SCHEMA_VERSION = "1.0.0"
_STREAM = "dora_tlpt_programme_scope"


class InvalidDortScopeError(ValueError):
    """Raised when a scope input or Art. 24 coverage invariant is violated."""


def _canonical_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise InvalidDortScopeError(
            f"{field} must be a string, got {type(value).__name__}"
        )
    normalised = unicodedata.normalize("NFKC", value).strip()
    if not normalised:
        raise InvalidDortScopeError(f"{field} is empty after canonicalisation")
    return normalised


def _require_pattern(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _canonical_text(value, field)
    if not pattern.match(text):
        raise InvalidDortScopeError(
            f"{field} {text!r} does not match the schema pattern"
        )
    return text


def _id_list(value: object, field: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise InvalidDortScopeError(f"{field} must be a list of identifiers")
    return tuple(
        _require_pattern(v, f"{field}[{i}]", _ID_RE) for i, v in enumerate(value)
    )


def define_dort_scope(
    testing_window: str,
    critical_functions: list,
    asset_register: dict,
    third_party_register: dict,
) -> dict:
    """Compose the Art. 24 DORT-scope catalogue for one programme window.

    Args:
        testing_window: The programme window as ``YYYY-MM-DD/YYYY-MM-DD``
            (``__testing_window__``).
        critical_functions: Identifiers of the ICT-supported critical or
            important functions in scope, from the business-service register.
        asset_register: Function identifier to the list of supporting ICT
            asset identifiers.
        third_party_register: Function identifier to the list of ICT
            third-party service-provider identifiers whose services fall
            inside the testing boundary.

    Returns:
        JSON-native catalogue envelope with ``schema_version``, ``stream``,
        ``testing_window``, ``functions`` (each with its sorted ``assets``
        and ``third_parties``), ``unresolved_functions``, ``asset_count``,
        ``third_party_count`` and ``complete``.

    Raises:
        InvalidDortScopeError: any input fails validation, the window is
            malformed or inverted, ``critical_functions`` is empty, or a
            register names a function absent from ``critical_functions``.
    """
    window = _canonical_text(testing_window, "testing_window")
    if not _WINDOW_RE.match(window):
        raise InvalidDortScopeError(
            f"testing_window {window!r} is not YYYY-MM-DD/YYYY-MM-DD"
        )
    start, end = window.split("/")
    if start >= end:
        raise InvalidDortScopeError(
            f"testing_window {window!r} does not start before it ends"
        )

    functions = _id_list(critical_functions, "critical_functions")
    if not functions:
        raise InvalidDortScopeError(
            "critical_functions is empty; an entity with no ICT-supported "
            "critical or important function has no Art. 24 testing programme "
            "to scope, and that is a finding about the Art. 8 identification "
            "rather than an empty catalogue"
        )
    known = set(functions)

    for name, register in (
        ("asset_register", asset_register),
        ("third_party_register", third_party_register),
    ):
        if not isinstance(register, dict):
            raise InvalidDortScopeError(
                f"{name} must be a mapping of function id to identifier list"
            )
        stray = sorted(set(register) - known)
        if stray:
            raise InvalidDortScopeError(
                f"{name} names function(s) {stray} absent from "
                f"critical_functions; a register entry for an unscoped "
                f"function would silently widen the testing boundary"
            )

    entries = []
    unresolved = []
    for fn in sorted(known):
        assets = sorted(set(_id_list(
            asset_register.get(fn, []), f"asset_register[{fn!r}]"
        )))
        parties = sorted(set(_id_list(
            third_party_register.get(fn, []), f"third_party_register[{fn!r}]"
        )))
        if not assets:
            unresolved.append(fn)
        entries.append({
            "function_id": fn,
            "assets": assets,
            "third_parties": parties,
        })

    return {
        "schema_version": _SCHEMA_VERSION,
        "stream": _STREAM,
        "testing_window": window,
        "window_start": start,
        "window_end": end,
        "functions": entries,
        "unresolved_functions": unresolved,
        "asset_count": sum(len(e["assets"]) for e in entries),
        "third_party_count": len({p for e in entries for p in e["third_parties"]}),
        "complete": not unresolved,
    }
