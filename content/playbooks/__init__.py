"""Playbooks namespace.

Portable CACAO playbooks live in hyphen-named directories on disk
(``content/playbooks/vuln-intake/``) but are importable under
Python-friendly underscore aliases (``content.playbooks.vuln_intake``).

Aliases are registered as standard Python packages whose ``__path__``
points at the hyphen-named on-disk directory. Per-target CORE bodies
import via ``from content.playbooks.vuln_intake.primitives import ...``.
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
