"""Import alias for ``content/playbooks/incident-management/``.

The portable incident-management source playbook ships under the
hyphen-named directory ``content/playbooks/incident-management/`` to
keep the workflow-id convention consistent across the cookbook. Python
cannot import through hyphens, so this sibling package rewires
``__path__`` to point at the hyphen directory on disk.
``from content.playbooks.incident_management.primitives import ...``
then resolves to ``content/playbooks/incident-management/primitives/``
without copying or symlinking any files. Same pattern as
``alert_triage`` and ``vuln_intake``.
"""

from __future__ import annotations

import os as _os

_ON_DISK = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), "..", "incident-management")
)

# Make submodule imports resolve into the hyphen directory.
__path__ = [_ON_DISK]  # type: ignore[assignment]
