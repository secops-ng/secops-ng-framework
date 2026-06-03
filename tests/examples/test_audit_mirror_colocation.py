"""Co-located ``_audit_mirror.py`` siblings are byte-identical to the helper.

F-CR-04 CORE-C decision: every emitted compiler artifact imports the
audit-trail mirror via a package-relative ``from ._audit_mirror import``,
and the mirror is materialised as a sibling file at regenerate time
(see :doc:`/docs/observability/audit-mirror`). This module pins that
contract:

* Each committed ``_audit_mirror.py`` next to an emitted artifact is
  byte-identical to :func:`render_audit_mirror_module`.
* Re-running ``regenerate.sh`` is idempotent: it overwrites
  ``_audit_mirror.py`` with the same bytes.

A drift here is the same kind of CI failure as a stale golden — the
operator-visible audit-mirror module diverged from the canonical source.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from compilers._shared.observability import render_audit_mirror_module

REPO_ROOT = Path(__file__).resolve().parents[2]

# Every example directory that emits an artifact importing
# ``from ._audit_mirror import ...`` must commit the mirror sibling.
MIRROR_PATHS = [
    REPO_ROOT / "examples" / "langgraph" / "vuln-intake" / "_audit_mirror.py",
    REPO_ROOT / "examples" / "temporal" / "vuln-intake" / "_audit_mirror.py",
    REPO_ROOT / "examples" / "temporal" / "data-exfil" / "_audit_mirror.py",
    REPO_ROOT / "examples" / "temporal" / "threat-intel-ingest" / "_audit_mirror.py",
]


@pytest.mark.parametrize("path", MIRROR_PATHS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_committed_mirror_matches_helper(path: Path) -> None:
    """The committed ``_audit_mirror.py`` is byte-identical to the helper output."""
    assert path.exists(), f"missing co-located audit-mirror at {path}"
    assert path.read_text(encoding="utf-8") == render_audit_mirror_module()


def test_every_emitted_artifact_with_relative_import_has_a_sibling_mirror() -> None:
    """Drift catcher: any file emitting ``from ._audit_mirror import`` must have a sibling mirror.

    Catches the case where a new compile target / example lands an emitted
    artifact that imports the mirror but forgets to add the sibling file
    and the regenerate-time materialisation step.
    """
    examples = REPO_ROOT / "examples"
    importers: list[Path] = []
    for py in examples.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if "from ._audit_mirror import" in text:
            importers.append(py)

    missing: list[Path] = []
    for py in importers:
        sibling = py.parent / "_audit_mirror.py"
        if not sibling.exists():
            missing.append(sibling)
    assert not missing, (
        "emitted artifacts import ``from ._audit_mirror`` but no sibling "
        f"mirror file is committed: {sorted(str(m) for m in missing)}"
    )
