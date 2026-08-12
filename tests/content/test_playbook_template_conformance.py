"""Test the playbook _template conformance linter against every shipped playbook.

Structural tier must pass on every canonical playbook currently under
``content/playbooks/``. This is the F-CONTRIB-ONBOARD-01 EXTEND (G-06)
invariant: the shipped set stays lintable as the mechanical floor for
new contributions.

Strict tier is exercised as a smoke test on the ``_template`` scaffold
copied into a tmp workspace (verifies the strict headings AND
placeholder detection fire when they should).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from tools import lint_playbook_template as lint_mod

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_template_workflow_start_resolves_to_start_step() -> None:
    """The copied scaffold names a valid CACAO start step."""
    template = (
        REPO_ROOT / "content" / "playbooks" / "_template" / "playbook.cacao.yaml"
    )
    playbook = yaml.safe_load(template.read_text(encoding="utf-8"))

    workflow_start = playbook["workflow_start"]
    assert workflow_start == "step--TODO_UUID_START"
    assert playbook["workflow"][workflow_start]["type"] == "start"


def test_structural_tier_clean_on_shipped_playbooks() -> None:
    """Every canonical playbook passes the structural tier."""
    report = lint_mod.lint(REPO_ROOT)
    structural = [f for f in report.findings if f.tier == "structural"]
    assert not structural, (
        "structural-tier violations on shipped playbooks:\n"
        + "\n".join(f"  {f.slug}: {f.code}: {f.message}" for f in structural)
    )
    # Sanity: the walk visited a non-trivial set. The shipped
    # canonical count is 45 as of F-CONTRIB-ONBOARD-01 EXTEND.
    assert len(report.checked) >= 45, (
        f"expected at least 45 canonical playbooks visited, got "
        f"{len(report.checked)}: {report.checked}"
    )


def test_excluded_directories_not_visited() -> None:
    """Template scaffold and legacy hyphenated stubs are not walked."""
    report = lint_mod.lint(REPO_ROOT)
    for excluded in ("_template", "alert-triage", "incident-management", "vuln-intake"):
        assert excluded not in report.checked, (
            f"excluded directory {excluded!r} unexpectedly visited"
        )


def test_default_scope_puts_no_playbook_in_strict_tier() -> None:
    """Default invocation (no --strict, no --baseline-ref) skips strict checks."""
    report = lint_mod.lint(REPO_ROOT)
    strict = [f for f in report.findings if f.tier == "strict"]
    assert not strict, (
        "unexpected strict findings in default scope: "
        + ", ".join(f"{f.slug}:{f.code}" for f in strict)
    )
    assert report.strict_targets == []


def test_strict_all_fires_on_template_copy(tmp_path: Path) -> None:
    """A verbatim copy of _template (with TODOs and canonical headings) fires
    both TEMPLATE_PLACEHOLDER_LEAK (structural) and passes strict headings.

    The template README carries the four canonical headings, so a
    contributor who preserved them earns a green strict tier — but the
    verbatim TODO_ placeholders in the CACAO artifact keep the
    structural tier red until they are filled in. This locks in the
    exact "mechanical feedback" story the extend was scoped for.
    """
    root = tmp_path / "repo"
    (root / "content" / "playbooks").mkdir(parents=True)
    (root / "content" / "mappings").mkdir(parents=True)
    # Copy the shipped template into a new slug directory.
    src = REPO_ROOT / "content" / "playbooks" / "_template"
    dst = root / "content" / "playbooks" / "new_contribution"
    shutil.copytree(src, dst)

    report = lint_mod.lint(root, strict_all=True)
    codes = {(f.slug, f.code) for f in report.findings}

    # Structural placeholder leak must fire.
    assert (
        "new_contribution",
        "TEMPLATE_PLACEHOLDER_LEAK",
    ) in codes, f"expected placeholder-leak finding, got: {codes}"

    # No mapping edge — template ships no mappings.yaml.
    assert (
        "new_contribution",
        "NO_MAPPING_EDGE",
    ) in codes, f"expected no-mapping-edge finding, got: {codes}"


def test_mappings_stub_validates_once_renamed_and_filled() -> None:
    """The shipped mappings.yaml.example is one rename and one slug away
    from passing the playbook-mappings schema — the exact promise
    quickstart § 5 makes for it. The verbatim stub must NOT validate:
    the schema's lowercase pattern rejects TODO_SLUG by design, so the
    schema itself names the remaining fill-in.
    """
    stub = (
        REPO_ROOT / "content" / "playbooks" / "_template"
        / "mappings.yaml.example"
    )
    text = stub.read_text(encoding="utf-8")
    schema = json.loads(
        (REPO_ROOT / "schemas" / "playbook-mappings.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)

    verbatim_errors = list(validator.iter_errors(yaml.safe_load(text)))
    assert verbatim_errors, (
        "the verbatim TODO_SLUG stub should fail the schema's lowercase "
        "pattern until the contributor fills the slug in"
    )

    filled = yaml.safe_load(text.replace("TODO_SLUG", "new_contribution"))
    errors = sorted(validator.iter_errors(filled), key=str)
    assert not errors, [e.message for e in errors]


def test_renamed_stub_satisfies_mapping_edge(tmp_path: Path) -> None:
    """Renaming mappings.yaml.example to mappings.yaml — the deliberate
    act quickstart § 5 asks for — clears NO_MAPPING_EDGE while the
    placeholder leak keeps the structural tier red until the TODOs are
    filled. The two signals decouple exactly as designed.
    """
    root = tmp_path / "repo"
    (root / "content" / "playbooks").mkdir(parents=True)
    (root / "content" / "mappings").mkdir(parents=True)
    src = REPO_ROOT / "content" / "playbooks" / "_template"
    dst = root / "content" / "playbooks" / "new_contribution"
    shutil.copytree(src, dst)
    (dst / "mappings.yaml.example").rename(dst / "mappings.yaml")

    report = lint_mod.lint(root, strict_all=True)
    codes = {(f.slug, f.code) for f in report.findings}
    assert ("new_contribution", "NO_MAPPING_EDGE") not in codes, (
        f"renamed stub should satisfy the mapping edge, got: {codes}"
    )
    assert ("new_contribution", "TEMPLATE_PLACEHOLDER_LEAK") in codes, (
        f"placeholder leak should keep firing until TODOs are filled: {codes}"
    )


def test_strict_missing_heading_flagged(tmp_path: Path) -> None:
    """A playbook README with no canonical headings trips strict tier."""
    root = tmp_path / "repo"
    playbook = root / "content" / "playbooks" / "novel_flow"
    playbook.mkdir(parents=True)
    (root / "content" / "mappings" / "nis2").mkdir(parents=True)

    (playbook / "playbook.cacao.yaml").write_text(
        "type: playbook\nspec_version: '2.0'\nid: playbook--abc\nname: Novel Flow\n",
        encoding="utf-8",
    )
    (playbook / "README.md").write_text(
        "# novel_flow\n\nA prose-only description with no canonical headings.\n",
        encoding="utf-8",
    )
    (playbook / "mappings.yaml").write_text("# stub\n", encoding="utf-8")

    report = lint_mod.lint(root, strict_all=True)
    codes = {(f.slug, f.code, f.tier) for f in report.findings}
    assert (
        "novel_flow",
        "MISSING_CANONICAL_HEADING",
        "strict",
    ) in codes, f"expected strict-heading finding, got: {codes}"


def test_missing_cacao_and_readme_flagged(tmp_path: Path) -> None:
    """A directory with neither artifact would not even be walked; a
    directory with a CACAO but no README trips MISSING_README."""
    root = tmp_path / "repo"
    playbook = root / "content" / "playbooks" / "cacao_only"
    playbook.mkdir(parents=True)
    (root / "content" / "mappings" / "nis2").mkdir(parents=True)

    (playbook / "playbook.cacao.yaml").write_text("type: playbook\n", encoding="utf-8")
    (playbook / "mappings.yaml").write_text("# stub\n", encoding="utf-8")

    report = lint_mod.lint(root)
    codes = {(f.slug, f.code) for f in report.findings}
    assert ("cacao_only", "MISSING_README") in codes


def test_inbound_edge_satisfies_mapping_check(tmp_path: Path) -> None:
    """A playbook without mappings.yaml is OK if inbound edge exists."""
    root = tmp_path / "repo"
    playbook = root / "content" / "playbooks" / "cited_only"
    playbook.mkdir(parents=True)
    (root / "content" / "mappings" / "nis2").mkdir(parents=True)

    (playbook / "playbook.cacao.yaml").write_text(
        "type: playbook\nspec_version: '2.0'\nid: playbook--abc\n",
        encoding="utf-8",
    )
    (playbook / "README.md").write_text(
        "# cited_only\n\n## Overview\n\nx\n\n## Regulatory anchors\n\ny\n"
        "\n## How to compile\n\nz\n\n## Operator customisation\n\nq\n",
        encoding="utf-8",
    )
    (root / "content" / "mappings" / "nis2" / "article-21-2-e.yaml").write_text(
        "playbook_refs:\n  - playbook.cited_only@v1\n",
        encoding="utf-8",
    )

    report = lint_mod.lint(root, strict_all=True)
    assert report.ok, f"expected clean report, got: {report.findings}"
