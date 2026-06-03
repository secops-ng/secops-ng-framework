"""Import alias for ``content/playbooks/vuln-intake/``.

The portable playbook lives at ``content/playbooks/vuln-intake/`` (hyphen).
This package's ``__path__`` is rewritten to point at that directory so
``from content.playbooks.vuln_intake.primitives import ...`` resolves to
``content/playbooks/vuln-intake/primitives/`` on disk.
"""

from __future__ import annotations

import os as _os

_ON_DISK = _os.path.join(_os.path.dirname(__file__), "..", "vuln-intake")
_ON_DISK = _os.path.normpath(_ON_DISK)

# Make submodule imports resolve into the hyphen directory.
__path__ = [_ON_DISK]  # type: ignore[assignment]
