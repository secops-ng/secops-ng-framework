"""Import alias for ``content/playbooks/codebase-vuln-management/``.

The portable playbook lives at ``content/playbooks/codebase-vuln-management/``
(hyphen, matching the workflow-id convention). Python cannot import through
hyphens, so this sibling package rewires ``__path__`` to point at the hyphen
directory on disk. ``from content.playbooks.codebase_vuln_management.primitives
import ...`` then resolves to
``content/playbooks/codebase-vuln-management/primitives/`` without copying or
symlinking any files. Mirrors the precedent set by ``vuln_intake/`` (F-WF-01).
"""

from __future__ import annotations

import os as _os

_ON_DISK = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), "..", "codebase-vuln-management")
)

# Make submodule imports resolve into the hyphen directory.
__path__ = [_ON_DISK]  # type: ignore[assignment]
