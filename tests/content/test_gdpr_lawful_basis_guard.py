"""Tests for the F-GD-02 EXTEND GDPR data-flow CI guard.

Covers:

- pass case: a fixture tree with a playbook directory and a complete
  data-flow-<workflow>.md that has all seven canonical sections filled;
- pass case against the real shipped phishing_triage doc;
- fail case (missing_doc): playbook present, no data-flow doc;
- fail cases per canonical section: each individually-missing or
  empty section flagged with its heading;
- drift fail cases: renamed section (drift) and extra section
  (unexpected) flagged with the offending heading;
- backward-compat behaviour of the SKELETON's
  ``lawful_basis_is_non_empty`` body-cases parser.

Fixtures are built in tmp_path; the real ``content/`` tree is never
mutated. The canonical template is copied into each tmp tree so the
EXTEND drift check has a reference to compare against.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from textwrap import dedent

import pytest

from tools.lint_gdpr_lawful_basis import (
    canonical_sections,
    check,
    discover_playbooks,
    lawful_basis_is_non_empty,
    skeleton_pending_sections,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_TEMPLATE_PATH = (
    REPO_ROOT
    / "content"
    / "mappings"
    / "gdpr"
    / "_data-flow-template.md"
)


# ---------------------------------------------------------------------------
# Canonical sections (read live from the real template so any rename in
# the template propagates here without code edits).
# ---------------------------------------------------------------------------


def _canonical() -> list[str]:
    return canonical_sections(REAL_TEMPLATE_PATH.read_text(encoding="utf-8"))


def _skeleton_pending() -> set[str]:
    return skeleton_pending_sections(REAL_TEMPLATE_PATH.read_text(encoding="utf-8"))


def _required() -> list[str]:
    """Canonical sections that are NOT skeleton-pending (i.e. enforced now)."""
    pending = _skeleton_pending()
    return [h for h in _canonical() if h not in pending]


# ---------------------------------------------------------------------------
# Fixture-tree helpers
# ---------------------------------------------------------------------------


def _seed_template(root: Path) -> None:
    """Copy the real canonical template into ``root``'s tree.

    EXTEND check reads section headings from this template; without it
    the linter cannot tell whether a doc is missing or drifting.
    """
    gdpr_dir = root / "content" / "mappings" / "gdpr"
    gdpr_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REAL_TEMPLATE_PATH, gdpr_dir / "_data-flow-template.md")


def _make_playbook(root: Path, name: str) -> None:
    """Create ``content/playbooks/<name>/README.md`` under ``root``."""
    pb_dir = root / "content" / "playbooks" / name
    pb_dir.mkdir(parents=True, exist_ok=True)
    (pb_dir / "README.md").write_text(f"# {name}\n", encoding="utf-8")


def _make_data_flow(
    root: Path,
    name: str,
    *,
    section_bodies: dict[str, str] | None = None,
    omit: set[str] | None = None,
    extra_sections: list[tuple[str, str]] | None = None,
    rename: dict[str, str] | None = None,
) -> Path:
    """Build a data-flow doc for ``name`` with the seven canonical sections.

    - ``section_bodies``: override the default ("Test <heading> body.")
      filled body for individual sections, keyed by canonical heading.
    - ``omit``: set of canonical headings to omit from the doc entirely.
    - ``extra_sections``: additional sections (heading, body) appended.
    - ``rename``: map of canonical heading -> renamed heading (e.g.
      simulate ``## 6. Cross border transfers`` instead of ``## 6.
      Cross-border transfers``).
    """
    omit = omit or set()
    section_bodies = section_bodies or {}
    rename = rename or {}
    extra_sections = extra_sections or []

    gdpr_dir = root / "content" / "mappings" / "gdpr"
    gdpr_dir.mkdir(parents=True, exist_ok=True)
    path = gdpr_dir / f"data-flow-{name}.md"

    parts = [f"# GDPR data flow — {name}", ""]
    for heading in _canonical():
        if heading in omit:
            continue
        rendered = rename.get(heading, heading)
        body = section_bodies.get(heading, f"Body for {heading}.")
        parts.append(rendered)
        parts.append("")
        parts.append(body)
        parts.append("")
    for heading, body in extra_sections:
        parts.append(heading)
        parts.append("")
        parts.append(body)
        parts.append("")
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Pass cases
# ---------------------------------------------------------------------------


def test_pass_when_all_seven_sections_filled(tmp_path: Path) -> None:
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(tmp_path, "demo-workflow")

    assert discover_playbooks(tmp_path) == ["demo-workflow"]
    assert check(tmp_path) == []


def test_pass_against_real_phishing_triage_doc() -> None:
    """The shipped phishing_triage doc must satisfy the parser.

    Guards against the parser drifting away from what the contributor
    convention actually writes for the lawful-basis body.
    """
    text = (
        REPO_ROOT
        / "content"
        / "mappings"
        / "gdpr"
        / "data-flow-phishing_triage.md"
    ).read_text(encoding="utf-8")
    assert lawful_basis_is_non_empty(text)


def test_pass_against_real_content_tree() -> None:
    """All shipped data-flow docs must pass the full EXTEND check.

    This is the regression net: if anyone lands a doc that drifts from
    the template or leaves a section empty, this test fails locally
    before CI does.
    """
    findings = check(REPO_ROOT)
    assert findings == [], "\n".join(f.message for f in findings)


# ---------------------------------------------------------------------------
# Missing-doc fail case
# ---------------------------------------------------------------------------


def test_fail_when_doc_missing(tmp_path: Path) -> None:
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    # Intentionally do not create the GDPR data-flow doc.

    findings = check(tmp_path)
    assert len(findings) == 1
    f = findings[0]
    assert f.workflow == "demo-workflow"
    assert f.kind == "missing_doc"
    assert f.path == "content/mappings/gdpr/data-flow-demo-workflow.md"
    assert "no GDPR data-flow doc" in f.message


# ---------------------------------------------------------------------------
# Per-section missing / empty fail cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing_heading", _required())
def test_fail_when_individual_section_missing(
    tmp_path: Path, missing_heading: str
) -> None:
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(tmp_path, "demo-workflow", omit={missing_heading})

    findings = check(tmp_path)
    missing = [f for f in findings if f.kind == "missing_section"]
    assert len(missing) == 1, (
        f"expected one missing_section, got {[(f.kind, f.section) for f in findings]}"
    )
    assert missing[0].section == missing_heading
    assert missing[0].workflow == "demo-workflow"
    assert missing_heading in missing[0].message


@pytest.mark.parametrize("empty_heading", _required())
def test_fail_when_individual_section_empty(
    tmp_path: Path, empty_heading: str
) -> None:
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(
        tmp_path,
        "demo-workflow",
        section_bodies={empty_heading: "`<fill in>`"},
    )

    findings = check(tmp_path)
    empty = [f for f in findings if f.kind == "empty_section"]
    assert len(empty) == 1, (
        f"expected one empty_section, got {[(f.kind, f.section) for f in findings]}"
    )
    assert empty[0].section == empty_heading
    assert empty[0].workflow == "demo-workflow"
    assert "empty" in empty[0].message.lower()


def test_fail_when_section_is_only_template_guidance(tmp_path: Path) -> None:
    """A data-flow doc whose section body is just the template's
    blockquote guidance and the ``<fill in>`` placeholder must fail."""
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(
        tmp_path,
        "demo-workflow",
        section_bodies={
            "## 2. Lawful basis": (
                "> **GDPR Art. 6(1).** Name the lawful basis…\n\n"
                "`<fill in>`"
            ),
        },
    )

    findings = [f for f in check(tmp_path) if f.kind == "empty_section"]
    assert len(findings) == 1
    assert findings[0].section == "## 2. Lawful basis"


# ---------------------------------------------------------------------------
# Drift fail cases
# ---------------------------------------------------------------------------


def test_fail_when_section_is_renamed(tmp_path: Path) -> None:
    """Renaming a canonical section trips both an unexpected_section
    (the renamed heading) and a missing_section (the original)."""
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(
        tmp_path,
        "demo-workflow",
        rename={"## 6. Cross-border transfers": "## 6. Cross border transfers"},
    )

    findings = check(tmp_path)
    kinds = {(f.kind, f.section) for f in findings}
    assert ("unexpected_section", "## 6. Cross border transfers") in kinds
    assert ("missing_section", "## 6. Cross-border transfers") in kinds


def test_fail_when_extra_section_present(tmp_path: Path) -> None:
    """An extra non-canonical section is flagged as unexpected."""
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(
        tmp_path,
        "demo-workflow",
        extra_sections=[("## 8. Extra appendix", "Some body.")],
    )

    findings = check(tmp_path)
    drift = [f for f in findings if f.kind == "unexpected_section"]
    assert len(drift) == 1
    assert drift[0].section == "## 8. Extra appendix"
    assert drift[0].workflow == "demo-workflow"
    assert "not in the canonical template" in drift[0].message


# ---------------------------------------------------------------------------
# Mixed-tree behaviour
# ---------------------------------------------------------------------------


def test_underscore_playbook_dirs_are_ignored(tmp_path: Path) -> None:
    """The underscore-prefixed package shims must not be treated as
    playbooks — they have no README.md and they're Python shims, not
    cookbook entries."""
    _seed_template(tmp_path)
    pb_dir = tmp_path / "content" / "playbooks" / "_legacy_shim"
    pb_dir.mkdir(parents=True)
    (pb_dir / "__init__.py").write_text("", encoding="utf-8")

    assert discover_playbooks(tmp_path) == []
    assert check(tmp_path) == []


def test_multiple_workflows_report_independently(tmp_path: Path) -> None:
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "alpha")
    _make_playbook(tmp_path, "beta")
    _make_playbook(tmp_path, "gamma")

    # alpha: all filled (pass). beta: missing doc. gamma: lawful basis
    # is placeholder-only.
    _make_data_flow(tmp_path, "alpha")
    _make_data_flow(
        tmp_path,
        "gamma",
        section_bodies={"## 2. Lawful basis": "`<fill in>`"},
    )

    findings = check(tmp_path)
    summary = {(f.workflow, f.kind, f.section) for f in findings}
    assert ("beta", "missing_doc", "") in summary
    assert ("gamma", "empty_section", "## 2. Lawful basis") in summary
    # alpha must not appear at all.
    assert not any(f.workflow == "alpha" for f in findings)


# ---------------------------------------------------------------------------
# Missing-template guard
# ---------------------------------------------------------------------------


def test_fail_when_template_missing(tmp_path: Path) -> None:
    """If the canonical template itself is missing, the linter must
    surface that as a single explanatory finding rather than crashing
    or silently passing."""
    _make_playbook(tmp_path, "demo-workflow")
    # No template seeded.

    findings = check(tmp_path)
    assert len(findings) == 1
    assert findings[0].kind == "missing_template"
    assert "_data-flow-template.md" in findings[0].path


# ---------------------------------------------------------------------------
# Skeleton-pending behaviour (rollout-optional sections)
# ---------------------------------------------------------------------------


def test_skeleton_pending_section_absent_does_not_fail(tmp_path: Path) -> None:
    """A canonical section tagged ``<!-- skeleton-pending -->`` in the
    template may be omitted from a workflow's data-flow doc without
    tripping missing_section."""
    pending = _skeleton_pending()
    if not pending:
        pytest.skip("no skeleton-pending sections in template")
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(tmp_path, "demo-workflow", omit=pending)

    findings = check(tmp_path)
    assert findings == [], "\n".join(f.message for f in findings)


def test_skeleton_pending_section_unfilled_does_not_fail(tmp_path: Path) -> None:
    """A skeleton-pending section that IS present but carries only the
    template placeholder body must not trip empty_section."""
    pending = _skeleton_pending()
    if not pending:
        pytest.skip("no skeleton-pending sections in template")
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(
        tmp_path,
        "demo-workflow",
        section_bodies={heading: "`<fill in>`" for heading in pending},
    )

    findings = check(tmp_path)
    assert findings == [], "\n".join(f.message for f in findings)


def test_skeleton_pending_section_still_drift_checked(tmp_path: Path) -> None:
    """Renaming a skeleton-pending heading still trips drift —
    pending-status only relaxes presence/fill, not the heading text."""
    pending = _skeleton_pending()
    if not pending:
        pytest.skip("no skeleton-pending sections in template")
    target = sorted(pending)[0]
    renamed = target + " (renamed)"
    _seed_template(tmp_path)
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(
        tmp_path,
        "demo-workflow",
        rename={target: renamed},
    )

    findings = check(tmp_path)
    kinds = {(f.kind, f.section) for f in findings}
    # Drift: the renamed heading is unexpected.
    assert ("unexpected_section", renamed) in kinds
    # The original heading is pending, so its absence is NOT a finding.
    assert ("missing_section", target) not in kinds


# ---------------------------------------------------------------------------
# Backward-compat parser micro-tests (SKELETON behaviour preserved)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "body,expected",
    [
        ("Primary: Art. 6(1)(f).", True),
        ("`<fill in>`", False),
        ("<fill in>", False),
        ("> blockquote-only guidance line", False),
        ("", False),
        ("   \n\n   ", False),
    ],
)
def test_lawful_basis_is_non_empty_body_cases(body: str, expected: bool) -> None:
    doc = dedent(
        f"""\
        # x

        ## 2. Lawful basis

        {body}

        ## 3. Categories of data subjects and personal data

        next
        """
    )
    assert lawful_basis_is_non_empty(doc) is expected


def test_lawful_basis_missing_heading_is_empty() -> None:
    doc = "# x\n\n## 1. Purpose\n\nbody\n"
    assert lawful_basis_is_non_empty(doc) is False
