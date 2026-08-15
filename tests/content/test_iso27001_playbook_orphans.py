"""Tests for the ISO 27001 orphan-CI assertion (F-MAP-ORPHAN-PARITY pkg 2).

Mirrors the soc2 module against the framework-parametrised linter at
``tools.lint_playbook_orphans``. Real-tree pass case covers the shipped
``content/mappings/iso27001/`` plus the audited ``_orphan_skip.yaml``
manifest (package 2 classifies every finalized playbook: 23 already
cited by the Annex A crosswalk, 14 durable other-regime exclusions,
11 interim entries whose Annex A citations #943 owes); synthetic
fixtures cover grace window, regression lane, skip-manifest
validation, and KRI emission shape.

Fixtures are built in tmp_path; the real ``content/`` tree is never
mutated.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import subprocess
from pathlib import Path
from textwrap import dedent

import pytest

from tools.lint_playbook_orphans import (
    KRI_ID,
    check,
    kri_name_for,
    main,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK = "iso27001"
KRI_NAME = kri_name_for(FRAMEWORK)


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_real_tree_passes_orphan_ci() -> None:
    """The shipped tree must be clean on the current main snapshot.

    Stage-1 floor (soc2 axis) is zero HIGH findings: every finalized
    playbook is either cited from a ``tsc-*.yaml`` entry or carries an
    audited skip — durable for other-regime duty ledgers, interim for
    the twelve TSC surfaces whose criteria citations #931 owes.
    """
    findings, summary = check(
        REPO_ROOT,
        framework=FRAMEWORK,
        baseline_ref=None,
        grace_days=7,
    )
    high = [f for f in findings if f.severity == "HIGH"]
    assert not high, (
        f"real tree has HIGH {FRAMEWORK} orphan-CI findings on the "
        f"current main snapshot: {[f.to_dict() for f in high]}"
    )
    assert summary["framework"] == FRAMEWORK
    assert summary["finalized"] > 0
    assert summary["orphans"] == 0



# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _scaffold(tmp_path: Path) -> Path:
    """Build a minimal repo-shaped tree under tmp_path."""
    root = tmp_path / "repo"
    (root / "content" / "playbooks").mkdir(parents=True)
    (root / "content" / "mappings" / FRAMEWORK).mkdir(parents=True)
    return root


def _add_playbook(
    root: Path,
    slug: str,
    *,
    age_days: float = 0.0,
    cacao_ext: str = "json",
) -> Path:
    d = root / "content" / "playbooks" / slug
    d.mkdir(parents=True, exist_ok=True)
    marker = d / f"playbook.cacao.{cacao_ext}"
    marker.write_text("{}\n" if cacao_ext == "json" else "kind: cacao\n")
    if age_days:
        ts = (_dt.datetime.now(tz=_dt.timezone.utc)
              - _dt.timedelta(days=age_days)).timestamp()
        os.utime(marker, (ts, ts))
    return marker


def _add_mapping(root: Path, name: str, slugs: list[str]) -> Path:
    yml = root / "content" / "mappings" / FRAMEWORK / f"{name}.yaml"
    body = f"regime: {FRAMEWORK}\nentries:\n"
    body += "  - id: " + FRAMEWORK + ":test-" + name + "\n"
    body += "    playbook_refs:\n"
    for slug in slugs:
        body += f"      - playbook.{slug}@v1\n"
    yml.write_text(body)
    return yml


# ---------------------------------------------------------------------------
# Grace window
# ---------------------------------------------------------------------------


def test_net_new_orphan_inside_grace_window_does_not_trip(tmp_path: Path) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "shiny_new_thing", age_days=2.0)
    findings, summary = check(
        root, framework=FRAMEWORK, baseline_ref=None, grace_days=7
    )
    high = [f for f in findings if f.severity == "HIGH"]
    assert not high
    assert summary["finalized"] == 1
    assert summary["orphans"] == 0
    assert summary["grace_window"] == [{"slug": "shiny_new_thing", "age_days": 2.0}]


def test_net_new_orphan_past_grace_window_trips_high(tmp_path: Path) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "stale_orphan", age_days=14.0)
    findings, summary = check(
        root, framework=FRAMEWORK, baseline_ref=None, grace_days=7
    )
    codes = sorted({(f.code, f.severity) for f in findings})
    assert ("ORPHAN_NEW", "HIGH") in codes
    assert summary["orphans"] == 1


# ---------------------------------------------------------------------------
# Regression lane
# ---------------------------------------------------------------------------


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _init_repo(root: Path) -> None:
    _git("init", "-q", "-b", "main", cwd=root)
    _git("config", "user.email", "test@example.invalid", cwd=root)
    _git("config", "user.name", "Test", cwd=root)
    _git("config", "commit.gpgsign", "false", cwd=root)


def test_orphan_regression_against_baseline_trips_immediately(
    tmp_path: Path,
) -> None:
    root = _scaffold(tmp_path)
    _init_repo(root)
    _add_playbook(root, "regressing_pb", age_days=0.5)
    _add_mapping(root, "entry-test-cited", ["regressing_pb"])
    _git("add", "-A", cwd=root)
    _git("commit", "-q", "-m", "baseline: cite regressing_pb", cwd=root)
    baseline_sha = _git("rev-parse", "HEAD", cwd=root).strip()

    # Drop the citation but keep the playbook — this is the regression.
    (root / "content" / "mappings" / FRAMEWORK / "entry-test-cited.yaml").unlink()
    _git("add", "-A", cwd=root)
    _git("commit", "-q", "-m", "regress: drop citation", cwd=root)

    findings, summary = check(
        root, framework=FRAMEWORK, baseline_ref=baseline_sha, grace_days=7
    )
    codes = [(f.code, f.severity, f.slug) for f in findings]
    assert ("ORPHAN_REGRESSION", "HIGH", "regressing_pb") in codes
    assert summary["baseline_resolved"] is True


def test_unresolvable_baseline_falls_back_silently(tmp_path: Path) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "fresh_pb", age_days=0.0)
    findings, summary = check(
        root,
        framework=FRAMEWORK,
        baseline_ref="origin/this-does-not-exist",
        grace_days=7,
    )
    high = [f for f in findings if f.severity == "HIGH"]
    assert not high
    assert summary["baseline_resolved"] is False


# ---------------------------------------------------------------------------
# Skip manifest
# ---------------------------------------------------------------------------


def _write_skip(root: Path, body: str) -> None:
    (root / "content" / "mappings" / FRAMEWORK / "_orphan_skip.yaml").write_text(body)


def test_skip_manifest_accepts_audited_exclusion(tmp_path: Path) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "intentionally_unmapped", age_days=999.0)
    _write_skip(
        root,
        dedent(
            """
            skip:
              - slug: intentionally_unmapped
                rationale: >-
                  Test fixture — deliberate exclusion documenting why
                  no iso27001 edge is appropriate here.
            """
        ),
    )
    findings, summary = check(
        root, framework=FRAMEWORK, baseline_ref=None, grace_days=7
    )
    high = [f for f in findings if f.severity == "HIGH"]
    assert not high
    assert summary["skipped"] == ["intentionally_unmapped"]


def test_skip_manifest_rejects_non_finalized_slug(tmp_path: Path) -> None:
    root = _scaffold(tmp_path)
    _write_skip(
        root,
        dedent(
            """
            skip:
              - slug: ghost_slug
                rationale: this slug does not exist on disk
            """
        ),
    )
    findings, _ = check(
        root, framework=FRAMEWORK, baseline_ref=None, grace_days=7
    )
    codes = [(f.code, f.severity, f.slug) for f in findings]
    assert ("SKIP_INVALID", "HIGH", "ghost_slug") in codes


def test_skip_manifest_rejects_missing_rationale(tmp_path: Path) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "needs_rationale", age_days=999.0)
    _write_skip(
        root,
        dedent(
            """
            skip:
              - slug: needs_rationale
            """
        ),
    )
    findings, _ = check(
        root, framework=FRAMEWORK, baseline_ref=None, grace_days=7
    )
    codes = [(f.code, f.severity, f.slug) for f in findings]
    assert ("SKIP_INVALID", "HIGH", "needs_rationale") in codes


# ---------------------------------------------------------------------------
# KRI emission
# ---------------------------------------------------------------------------


def test_kri_emission_shape(tmp_path: Path, capsys) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "stale_orphan", age_days=14.0)
    rc = main([
        "--framework", FRAMEWORK,
        "--root", str(root),
        "--baseline-ref", "",
        "--format", "kri",
    ])
    captured = capsys.readouterr().out
    payload = json.loads(captured)
    assert payload["kri_id"] == KRI_ID
    assert payload["kri_name"] == KRI_NAME
    assert payload["regime"] == FRAMEWORK
    assert payload["status"] == "tripped"
    assert payload["coverage"]["orphans"] == 1
    assert any(
        f["code"] == "ORPHAN_NEW" and f["slug"] == "stale_orphan"
        for f in payload["findings"]
    )
    assert rc == 1


def test_kri_emission_status_ok_on_clean_tree(tmp_path: Path, capsys) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "cited_pb", age_days=14.0)
    _add_mapping(root, "entry-some", ["cited_pb"])
    rc = main([
        "--framework", FRAMEWORK,
        "--root", str(root),
        "--baseline-ref", "",
        "--format", "kri",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["coverage"]["mapped"] == 1
    assert rc == 0


def test_kri_emission_status_degraded_inside_grace(tmp_path: Path, capsys) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "fresh_orphan", age_days=1.0)
    rc = main([
        "--framework", FRAMEWORK,
        "--root", str(root),
        "--baseline-ref", "",
        "--format", "kri",
    ])
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "degraded"
    assert rc == 0
