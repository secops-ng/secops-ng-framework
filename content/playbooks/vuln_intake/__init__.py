"""Import alias for ``content/playbooks/vuln-intake/``.

The portable playbook lives at ``content/playbooks/vuln-intake/`` (hyphen,
matching the workflow-id convention). Python cannot import through hyphens,
so this sibling package rewires ``__path__`` to point at the hyphen directory
on disk. ``from content.playbooks.vuln_intake.primitives import ...`` then
resolves to ``content/playbooks/vuln-intake/primitives/`` without copying or
symlinking any files.
"""

from __future__ import annotations

import os as _os

_ON_DISK = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), "..", "vuln-intake")
)

# Make submodule imports resolve into the hyphen directory.
__path__ = [_ON_DISK]  # type: ignore[assignment]
