"""CRA orphan-CI assertion — thin shim over the generic linter.

The G-02 KRI implementation now lives in
``tools.lint_playbook_orphans`` (parametrised by ``--framework``).
This module preserves the original CRA-specific public surface for
backward compatibility:

* ``KRI_ID`` / ``KRI_NAME``     — re-exported constants
* ``PLAYBOOK_REF_RE``           — re-exported regex (used by ad-hoc scripts)
* ``GRACE_DAYS_DEFAULT``        — re-exported default
* ``check(root, *, baseline_ref, grace_days, now=None)`` — same signature,
  framework pinned to ``"cra"``
* ``main(argv=None)``           — same CLI surface (no ``--framework`` flag);
  delegates to the generic ``main`` with ``--framework cra`` prepended,
  honouring the ``CRA_ORPHAN_BASELINE_REF`` env override.

Behaviour against the ``content/mappings/cra/`` tree, the KRI emission
shape, and the exit code semantics are byte-unchanged.
"""
from __future__ import annotations

import datetime as _dt
import os
import sys
from pathlib import Path

from tools.lint_playbook_orphans import (
    CACAO_FILENAMES,
    DEFAULT_ROOT,
    Finding,
    GRACE_DAYS_DEFAULT,
    KRI_ID,
    PLAYBOOK_REF_RE,
    PLAYBOOKS_RELPATH,
    SKIP_FILENAME,
    check as _check,
    kri_name_for,
    main as _main,
    mapping_relpath_for,
)

__all__ = [
    "CACAO_FILENAMES",
    "DEFAULT_ROOT",
    "Finding",
    "GRACE_DAYS_DEFAULT",
    "KRI_ID",
    "KRI_NAME",
    "PLAYBOOK_REF_RE",
    "PLAYBOOKS_RELPATH",
    "CRA_RELPATH",
    "SKIP_FILENAME",
    "check",
    "main",
]

# Public constants pinned to the CRA framework.
KRI_NAME = kri_name_for("cra")
CRA_RELPATH = mapping_relpath_for("cra")


def check(
    root: Path,
    *,
    baseline_ref: str | None,
    grace_days: int,
    now: _dt.datetime | None = None,
):
    """Run the orphan-CI assertion against the CRA mapping tree."""
    return _check(
        root,
        framework="cra",
        baseline_ref=baseline_ref,
        grace_days=grace_days,
        now=now,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI compatibility wrapper.

    Honours the legacy ``CRA_ORPHAN_BASELINE_REF`` env knob as the
    default baseline ref when no ``--baseline-ref`` is supplied.
    """
    argv = list(argv) if argv is not None else list(sys.argv[1:])
    if not any(a == "--baseline-ref" or a.startswith("--baseline-ref=") for a in argv):
        default = os.environ.get("CRA_ORPHAN_BASELINE_REF", "origin/main")
        argv = ["--baseline-ref", default, *argv]
    return _main(["--framework", "cra", *argv])


if __name__ == "__main__":
    raise SystemExit(main())
