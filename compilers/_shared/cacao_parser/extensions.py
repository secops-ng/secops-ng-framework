"""Where a playbook carries its SecOps-NG data: the legacy ``x_secops_ng``
object, or the CACAO 2.0 extension slots.

SecOps-NG joins every playbook and step to the rest of the content model —
stable ids, maturity, reference bundles, primitive bindings. Historically
that data sat under a private ``x_secops_ng`` key. CACAO 2.0 defines a
mechanism for exactly this (§10.10): an ``extension_definitions`` entry
naming the extension, and its payload under that entry's id in
``playbook_extensions`` (playbook level) and ``step_extensions`` (step
level). CACAO tooling keeps extension data and discards unknown keys —
CACAO Roaster drops ``x_secops_ng`` on import (#1027) — so the corpus is
moving to the extension slots.

For one release both placements are read:

* :func:`secops_extension` returns the payload from either place, for a
  playbook or a step, and rejects an object carrying both, because two
  copies of the same data can disagree and nothing says which one wins;
* :func:`migrate_to_extensions` rewrites a legacy document into the
  extension placement — pure and idempotent, so the content move and the
  parity tests use the same function.

The payload is identical in both placements; only its location changes.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

__all__ = [
    "EXTENSION_SCHEMA_URL",
    "SECOPS_NG_EXTENSION_DEFINITION",
    "SECOPS_NG_EXTENSION_ID",
    "ExtensionPlacementError",
    "migrate_to_extensions",
    "secops_extension",
]

#: uuid5(NAMESPACE_URL, "https://github.com/secops-ng/secops-ng-framework/extensions/x-secops-ng")
SECOPS_NG_EXTENSION_ID = "extension-definition--4f4cc5db-ab05-5939-b7af-58a7082d081a"

EXTENSION_SCHEMA_URL = (
    "https://raw.githubusercontent.com/secops-ng/secops-ng-framework/main/"
    "content-model/x-secops-ng.extension.schema.json"
)

SECOPS_NG_EXTENSION_DEFINITION: dict[str, str] = {
    "type": "extension-definition",
    "name": "SecOps-NG content model",
    "description": (
        "Joins a CACAO playbook and its steps to the SecOps-NG content model: stable "
        "identifiers, maturity and compile targets at playbook level; detection, control, "
        "telemetry and metric references and deterministic primitive bindings at step level."
    ),
    "created_by": "identity--5ec075c0-5ec0-475c-85ec-075c05ec075c",
    "schema": EXTENSION_SCHEMA_URL,
    "version": "1.0.0",
}

_LEGACY = "x_secops_ng"
_SLOTS = ("playbook_extensions", "step_extensions")


class ExtensionPlacementError(ValueError):
    """The SecOps-NG payload is in both placements, or its definition is missing."""


def secops_extension(obj: Mapping[str, Any], where: str = "object") -> Mapping[str, Any] | None:
    """The SecOps-NG payload of a playbook or step, from whichever placement it uses.

    Returns ``None`` when the object carries none. A playbook never has
    ``step_extensions`` and a step never has ``playbook_extensions``, so one
    function serves both levels.
    """
    legacy = obj.get(_LEGACY)
    extended = None
    for slot in _SLOTS:
        slot_value = obj.get(slot)
        if isinstance(slot_value, Mapping) and SECOPS_NG_EXTENSION_ID in slot_value:
            extended = slot_value[SECOPS_NG_EXTENSION_ID]
    if legacy is not None and extended is not None:
        raise ExtensionPlacementError(
            f"{where}: SecOps-NG data is present both under {_LEGACY} and under "
            f"{SECOPS_NG_EXTENSION_ID}; keep one (the extension slot)"
        )
    return extended if extended is not None else legacy


def migrate_to_extensions(playbook: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of ``playbook`` with its SecOps-NG data in the extension slots.

    The root ``x_secops_ng`` moves to ``playbook_extensions``, each step's to
    ``step_extensions``, and the extension is declared in
    ``extension_definitions``. Other extensions a tool added — CACAO Roaster's
    diagram coordinates, say — are kept. Idempotent: a migrated document
    comes back unchanged.
    """
    doc = copy.deepcopy(dict(playbook))
    root = doc.pop(_LEGACY, None)
    if root is not None:
        doc.setdefault("playbook_extensions", {})[SECOPS_NG_EXTENSION_ID] = root
    for step in doc.get("workflow", {}).values():
        payload = step.pop(_LEGACY, None)
        if payload is not None:
            step.setdefault("step_extensions", {})[SECOPS_NG_EXTENSION_ID] = payload
    uses = SECOPS_NG_EXTENSION_ID in doc.get("playbook_extensions", {}) or any(
        SECOPS_NG_EXTENSION_ID in step.get("step_extensions", {}) for step in doc.get("workflow", {}).values()
    )
    if uses:
        doc.setdefault("extension_definitions", {})[SECOPS_NG_EXTENSION_ID] = dict(SECOPS_NG_EXTENSION_DEFINITION)
    return doc
