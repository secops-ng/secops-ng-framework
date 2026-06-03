"""Playbook content tree.

Each subdirectory is one workflow. Per-workflow shared Python primitives
(scoring, severity, dedup, etc.) live under
``<workflow>/primitives/`` on disk; an underscore-aliased import surface
(``content.playbooks.<workflow>_underscore.primitives``) is exposed where the
on-disk directory uses hyphens.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Hyphen → underscore import aliasing
# ---------------------------------------------------------------------------
#
# CACAO playbook directories on disk use hyphenated names because hyphens
# are the convention in the surrounding content tree (and on the published
# website). Python module names cannot contain hyphens, so we expose an
# underscore-aliased package per workflow that holds shared primitives.
#
# This module rewrites the ``__path__`` of any ``content.playbooks.<name>``
# import so that ``content.playbooks.vuln_intake`` resolves to the on-disk
# ``content/playbooks/vuln-intake/`` directory transparently. Concrete
# per-workflow aliases are declared explicitly below so static tooling
# (mypy, ruff) sees them.

_HERE = Path(__file__).resolve().parent


def _alias_hyphen_dir(underscore_name: str, hyphen_dir: str) -> None:
    """Bind ``content.playbooks.<underscore_name>`` to ``./<hyphen_dir>/``.

    The aliased package is a *namespace* shim: its ``__path__`` points at
    the hyphenated directory so submodule imports
    (``content.playbooks.<underscore_name>.primitives``) resolve to files
    under ``content/playbooks/<hyphen_dir>/primitives/``.
    """
    full = f"{__name__}.{underscore_name}"
    if full in sys.modules:
        return
    target = _HERE / hyphen_dir
    if not target.is_dir():
        return
    import types

    shim = types.ModuleType(full)
    shim.__path__ = [str(target)]  # type: ignore[attr-defined]
    shim.__doc__ = (
        f"Underscore alias for the on-disk ``content/playbooks/{hyphen_dir}/`` "
        "playbook directory."
    )
    sys.modules[full] = shim


_alias_hyphen_dir("vuln_intake", "vuln-intake")
