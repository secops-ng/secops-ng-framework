"""Tests for the F-GD-02 SKELETON lawful-basis CI guard.

Covers:

- pass case: a fixture tree with a playbook directory and a
  data-flow-<workflow>.md that has a filled lawful-basis section;
- fail case (missing_doc): playbook present, no data-flow doc;
- fail case (empty_lawful_basis): doc present but the section body
  is only template guidance / placeholder, no contributor prose.

Fixtures are built in tmp_path; the real ``content/`` tree is never
mutated. The pass case round-trips against the canonical template to
make sure the parser matches reality and against the existing
phishing-triage doc to make sure a real filled doc passes.
"""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from tools.lint_gdpr_lawful_basis import (
    check,
    discover_playbooks,
    lawful_basis_is_non_empty,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Fixture-tree helpers
# ---------------------------------------------------------------------------


def _make_playbook(root: Path, name: str) -> None:
    """Create ``content/playbooks/<name>/README.md`` under ``root``."""
    pb_dir = root / "content" / "playbooks" / name
    pb_dir.mkdir(parents=True, exist_ok=True)
    (pb_dir / "README.md").write_text(f"# {name}\n", encoding="utf-8")


def _make_data_flow(root: Path, name: str, lawful_basis_body: str) -> Path:
    """Create ``content/mappings/gdpr/data-flow-<name>.md`` with the seven
    canonical sections; ``## 2. Lawful basis`` is filled with the supplied
    body verbatim."""
    gdpr_dir = root / "content" / "mappings" / "gdpr"
    gdpr_dir.mkdir(parents=True, exist_ok=True)
    path = gdpr_dir / f"data-flow-{name}.md"
    path.write_text(
        dedent(
            f"""\
            # GDPR data flow — {name}

            ## 1. Purpose

            Test purpose body.

            ## 2. Lawful basis

            {lawful_basis_body}

            ## 3. Categories of data subjects and personal data

            Test categories body.

            ## 4. Recipients

            Test recipients body.

            ## 5. Retention

            Test retention body.

            ## 6. Cross-border transfers

            no transfer.

            ## 7. Data subject rights

            Test rights body.
            """
        ),
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# Pass case
# ---------------------------------------------------------------------------


def test_pass_when_doc_present_and_lawful_basis_filled(tmp_path: Path) -> None:
    _make_playbook(tmp_path, "demo-workflow")
    _make_data_flow(
        tmp_path,
        "demo-workflow",
        "Primary: **GDPR Art. 6(1)(f)** — legitimate interests.",
    )

    assert discover_playbooks(tmp_path) == ["demo-workflow"]
    assert check(tmp_path) == []


def test_pass_against_real_phishing_triage_doc() -> None:
    """The shipped phishing-triage doc must satisfy the parser.

    Guards against the parser drifting away from what the contributor
    convention actually writes for the lawful-basis body.
    """
    text = (
        REPO_ROOT
        / "content"
        / "mappings"
        / "gdpr"
        / "data-flow-phishing-triage.md"
    ).read_text(encoding="utf-8")
    assert lawful_basis_is_non_empty(text)


# ---------------------------------------------------------------------------
# Fail cases
# ---------------------------------------------------------------------------


def test_fail_when_doc_missing(tmp_path: Path) -> None:
    _make_playbook(tmp_path, "demo-workflow")
    # Intentionally do not create the GDPR data-flow doc.

    findings = check(tmp_path)
    assert len(findings) == 1
    f = findings[0]
    assert f.workflow == "demo-workflow"
    assert f.kind == "missing_doc"
    assert f.path == "content/mappings/gdpr/data-flow-demo-workflow.md"
    assert "no GDPR data-flow doc" in f.message


def test_fail_when_lawful_basis_is_only_template_guidance(
    tmp_path: Path,
) -> None:
    """A data-flow doc whose lawful-basis section is just the template's
    blockquote guidance and the ``<fill in>`` placeholder must fail."""
    _make_playbook(tmp_path, "demo-workflow")
    gdpr_dir = tmp_path / "content" / "mappings" / "gdpr"
    gdpr_dir.mkdir(parents=True, exist_ok=True)
    (gdpr_dir / "data-flow-demo-workflow.md").write_text(
        dedent(
            """\
            # GDPR data flow — demo-workflow

            ## 1. Purpose

            Test purpose body.

            ## 2. Lawful basis

            > **GDPR Art. 6(1).** Name the lawful basis the operator relies on
            > when running this workflow against EU data subjects.

            `<fill in>`

            ## 3. Categories of data subjects and personal data

            Test categories body.
            """
        ),
        encoding="utf-8",
    )

    findings = check(tmp_path)
    assert len(findings) == 1
    f = findings[0]
    assert f.workflow == "demo-workflow"
    assert f.kind == "empty_lawful_basis"
    assert "empty" in f.message.lower()


# ---------------------------------------------------------------------------
# Mixed-tree behaviour
# ---------------------------------------------------------------------------


def test_underscore_playbook_dirs_are_ignored(tmp_path: Path) -> None:
    """The underscore-prefixed package shims must not be treated as
    playbooks — they have no README.md and they're Python shims, not
    cookbook entries."""
    pb_dir = tmp_path / "content" / "playbooks" / "_legacy_shim"
    pb_dir.mkdir(parents=True)
    (pb_dir / "__init__.py").write_text("", encoding="utf-8")

    assert discover_playbooks(tmp_path) == []
    assert check(tmp_path) == []


def test_multiple_workflows_report_independently(tmp_path: Path) -> None:
    _make_playbook(tmp_path, "alpha")
    _make_playbook(tmp_path, "beta")
    _make_playbook(tmp_path, "gamma")

    # alpha: filled (pass). beta: missing doc. gamma: empty section.
    _make_data_flow(tmp_path, "alpha", "Primary: Art. 6(1)(f).")
    gdpr_dir = tmp_path / "content" / "mappings" / "gdpr"
    (gdpr_dir / "data-flow-gamma.md").write_text(
        dedent(
            """\
            # GDPR data flow — gamma

            ## 2. Lawful basis

            `<fill in>`

            ## 3. Categories of data subjects and personal data

            body
            """
        ),
        encoding="utf-8",
    )

    findings = check(tmp_path)
    kinds = {(f.workflow, f.kind) for f in findings}
    assert kinds == {("beta", "missing_doc"), ("gamma", "empty_lawful_basis")}


# ---------------------------------------------------------------------------
# Parser micro-tests
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
