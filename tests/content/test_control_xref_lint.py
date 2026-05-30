"""CI gate for the control-xref resolution linter.

Fails if any ``control_ref`` referenced from
``content/mappings/<regime>/*.yaml`` does not resolve to a populated
cross-reference file under ``content/controls/`` that conforms to
``content-model/control_xref.schema.json``.

The heavy lifting lives in ``tools.lint_control_xref``; this test is the
pytest entrypoint that wires it into CI and also exercises a synthetic
"unresolved" tree so we know the linter catches the failure modes it
claims to catch.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tools.lint_control_xref import Finding, lint

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_tree_is_clean() -> None:
    """The real repository tree must lint clean."""
    findings = lint(REPO_ROOT)
    assert not findings, "control-xref linter findings:\n" + "\n".join(
        f.format() for f in findings
    )


# ---------------------------------------------------------------------------
# Synthetic-tree exercise: the linter must catch each failure mode it claims.
# We mirror the minimum repo layout into a tmp dir, then mutate the copy.
# ---------------------------------------------------------------------------


def _stage_tree(tmp_path: Path) -> Path:
    """Copy schema + controls + mappings into ``tmp_path`` and return it."""
    for rel in (
        "content-model/control_xref.schema.json",
        "content/controls",
        "content/mappings",
    ):
        src = REPO_ROOT / rel
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copyfile(src, dst)
    return tmp_path


def test_linter_flags_missing_xref_file(tmp_path: Path) -> None:
    root = _stage_tree(tmp_path)
    # Delete a control file that is referenced from mappings.
    target = root / "content/controls/control.incident_handling_capability@v1.yaml"
    assert target.is_file(), "fixture assumption broken"
    target.unlink()

    findings = lint(root)
    codes = {f.code for f in findings}
    assert "missing_xref_file" in codes, [f.format() for f in findings]
    relevant = [f for f in findings if f.code == "missing_xref_file"]
    assert any(
        f.control_ref == "control.incident_handling_capability@v1" for f in relevant
    )
    # The finding must name the mapping entry that referenced it.
    assert any("nis2:art-21-2-b" in src for f in relevant for src in f.referenced_from)


def test_linter_flags_missing_d3fend_ref(tmp_path: Path) -> None:
    root = _stage_tree(tmp_path)
    target = root / "content/controls/control.incident_handling_capability@v1.yaml"
    text = target.read_text(encoding="utf-8")
    # Build a clearly-broken file: drop d3fend_refs entirely.
    # We rebuild from scratch to avoid brittle string replace logic.
    import yaml as _yaml

    doc = _yaml.safe_load(text)
    doc.pop("d3fend_refs", None)
    target.write_text(_yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    findings = lint(root)
    codes = {f.code for f in findings}
    # Either the schema layer or the belt-and-braces check must fire.
    assert codes & {"missing_d3fend_refs", "schema_violation"}, [
        f.format() for f in findings
    ]


def test_linter_flags_missing_provenance(tmp_path: Path) -> None:
    root = _stage_tree(tmp_path)
    target = root / "content/controls/control.incident_handling_capability@v1.yaml"
    import yaml as _yaml

    doc = _yaml.safe_load(target.read_text(encoding="utf-8"))
    doc["provenance"] = {}  # drop both source_url and captured_at
    target.write_text(_yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    findings = lint(root)
    codes = {f.code for f in findings}
    # Schema requires both keys — schema_violation will fire — and our
    # belt-and-braces checks ALSO surface clearer per-field codes.
    assert codes & {
        "missing_provenance_source_url",
        "missing_provenance_captured_at",
        "schema_violation",
    }, [f.format() for f in findings]


def test_finding_format_includes_referenced_from() -> None:
    f = Finding(
        control_ref="control.example@v1",
        code="missing_xref_file",
        message="example",
        referenced_from=("nis2/article-21-and-23.yaml#nis2:art-21-2-a",),
    )
    rendered = f.format()
    assert "control.example@v1" in rendered
    assert "missing_xref_file" in rendered
    assert "nis2:art-21-2-a" in rendered


@pytest.mark.parametrize(
    "code",
    [
        "missing_xref_file",
        "missing_oscal_refs",
        "missing_d3fend_refs",
        "missing_provenance_source_url",
        "missing_provenance_captured_at",
        "schema_violation",
    ],
)
def test_known_finding_codes_documented(code: str) -> None:
    """Lock the public finding-code surface so consumers can rely on it."""
    # Importing here keeps the parametrize id list explicit at the top of
    # the test file rather than reflected out of the module under test.
    from tools import lint_control_xref as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert f'"{code}"' in src, f"code {code!r} not referenced by linter source"
