"""Playbooks namespace.

Portable CACAO playbooks live in hyphen-named directories on disk
(``content/playbooks/vuln-intake/``) so the on-disk layout matches the
project's contributor-facing naming conventions. Python cannot import
through hyphens, so we register an underscore-aliased package per
workflow whose ``__path__`` rewires to the hyphen directory. Per-target
CORE bodies then import via
``from content.playbooks.vuln_intake.primitives import ...`` and the
resolver lands in ``content/playbooks/vuln-intake/primitives/`` on disk.

This file deliberately does *not* enumerate the aliases — each workflow
ships its own ``vuln_intake/`` (or analogous) sibling package that owns
its own ``__path__`` rewrite. Adding workflows here would couple every
workflow's primitive landing PR through a single file and break the
``parallel-safe`` decomposition documented in the F-WF-01 gap inventory.
"""

from __future__ import annotations

import os as _os

_HERE = _os.path.dirname(__file__)


# Map import-alias -> on-disk directory name. The alias directory
# (``vuln_intake/``) is a sibling of the hyphen directory on disk; it
# carries only an ``__init__.py`` whose ``__path__`` mirrors the hyphen
# directory so submodule imports resolve there.
_ALIASES = {
    "vuln_intake": "vuln-intake",
}


def _on_disk_path_for_alias(alias: str) -> str | None:
    """Return the on-disk path the alias resolves to, or None."""
    target = _ALIASES.get(alias)
    if target is None:
        return None
    candidate = _os.path.join(_HERE, target)
    if _os.path.isdir(candidate):
        return candidate
    return None
