"""Import alias for ``content/playbooks/alert-triage/``.

The portable alert-triage source playbook ships as a flat YAML at
``content/playbooks/alert-triage.cacao.yaml``; the workflow-local
primitives and typed payload models live under the sibling directory
``content/playbooks/alert-triage/`` (hyphen, matching the workflow-id
convention). Python cannot import through hyphens, so this sibling
package rewires ``__path__`` to point at the hyphen directory on disk.
``from content.playbooks.alert_triage.primitives import ...`` then
resolves to ``content/playbooks/alert-triage/primitives/`` without
copying or symlinking any files. The same pattern is used for
``vuln_intake``.
"""

from __future__ import annotations

import os as _os

_ON_DISK = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), "..", "alert-triage")
)

# Make submodule imports resolve into the hyphen directory.
__path__ = [_ON_DISK]  # type: ignore[assignment]
