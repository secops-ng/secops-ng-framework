"""Tests for the CRA orphan-CI assertion (G-02 KRI).

Covers:

- pass case on the real shipped tree (current main): no findings;
- pass case for a synthetic finalized playbook still inside the
  7-day grace window;
- HIGH ORPHAN_NEW fail case for a synthetic finalized playbook that
  is older than the grace window with no inbound CRA citation;
- HIGH ORPHAN_REGRESSION fail case when a slug present in the
  baseline-ref's CRA inbound set drops out of the current tree;
- skip-manifest acceptance for a deliberate exclusion;
- SKIP_INVALID fail when the manifest names a non-finalized slug or
  is missing the required ``rationale`` field;
- KRI emission shape (kri_id / status / coverage / findings).

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

from tools.lint_cra_playbook_orphans import (
    KRI_ID,
    KRI_NAME,
    check,
    main,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_real_tree_passes_orphan_ci() -> None:
    """The shipped tree must be clean on the current main snapshot.

    G-02 floor is zero HIGH findings; the assertion fires only on
    regressions or net-new orphans past the grace window.
    """
    findings, summary = check(
        REPO_ROOT,
        baseline_ref=None,
        grace_days=7,
    )
    high = [f for f in findings if f.severity == "HIGH"]
    assert not high, (
        "real tree has HIGH orphan-CI findings on the current main "
        f"snapshot: {[f.to_dict() for f in high]}"
    )
    assert summary["finalized"] > 0
    assert summary["orphans"] == 0


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _scaffold(tmp_path: Path) -> Path:
    """Build a minimal repo-shaped tree under tmp_path."""
    root = tmp_path / "repo"
    (root / "content" / "playbooks").mkdir(parents=True)
    (root / "content" / "mappings" / "cra").mkdir(parents=True)
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
    yml = root / "content" / "mappings" / "cra" / f"{name}.yaml"
    body = "regime: cra\nentries:\n"
    body += "  - id: cra:test-" + name + "\n"
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
    findings, summary = check(root, baseline_ref=None, grace_days=7)
    high = [f for f in findings if f.severity == "HIGH"]
    assert not high
    assert summary["finalized"] == 1
    assert summary["orphans"] == 0
    assert summary["grace_window"] == [{"slug": "shiny_new_thing", "age_days": 2.0}]


def test_net_new_orphan_past_grace_window_trips_high(tmp_path: Path) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "stale_orphan", age_days=14.0)
    findings, summary = check(root, baseline_ref=None, grace_days=7)
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
    _add_mapping(root, "art-test-cited", ["regressing_pb"])
    _git("add", "-A", cwd=root)
    _git("commit", "-q", "-m", "baseline: cite regressing_pb", cwd=root)
    baseline_sha = _git("rev-parse", "HEAD", cwd=root).strip()

    # Drop the citation but keep the playbook — this is the regression.
    (root / "content" / "mappings" / "cra" / "art-test-cited.yaml").unlink()
    _git("add", "-A", cwd=root)
    _git("commit", "-q", "-m", "regress: drop citation", cwd=root)

    findings, summary = check(root, baseline_ref=baseline_sha, grace_days=7)
    codes = [(f.code, f.severity, f.slug) for f in findings]
    assert ("ORPHAN_REGRESSION", "HIGH", "regressing_pb") in codes
    assert summary["baseline_resolved"] is True


def test_unresolvable_baseline_falls_back_silently(tmp_path: Path) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "fresh_pb", age_days=0.0)
    findings, summary = check(
        root, baseline_ref="origin/this-does-not-exist", grace_days=7
    )
    # No git regression info available — net-new orphan inside grace
    # window must still pass.
    high = [f for f in findings if f.severity == "HIGH"]
    assert not high
    assert summary["baseline_resolved"] is False


# ---------------------------------------------------------------------------
# Skip manifest
# ---------------------------------------------------------------------------


def _write_skip(root: Path, body: str) -> None:
    (root / "content" / "mappings" / "cra" / "_orphan_skip.yaml").write_text(body)


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
                  no CRA edge is appropriate here.
            """
        ),
    )
    findings, summary = check(root, baseline_ref=None, grace_days=7)
    high = [f for f in findings if f.severity == "HIGH"]
    assert not high
    assert summary["skipped"] == ["intentionally_unmapped"]


def test_skip_manifest_rejects_non_finalized_slug(tmp_path: Path) -> None:
    root = _scaffold(tmp_path)
    # Note: no playbook scaffolded for this slug.
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
    findings, _ = check(root, baseline_ref=None, grace_days=7)
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
    findings, _ = check(root, baseline_ref=None, grace_days=7)
    codes = [(f.code, f.severity, f.slug) for f in findings]
    assert ("SKIP_INVALID", "HIGH", "needs_rationale") in codes


# ---------------------------------------------------------------------------
# KRI emission
# ---------------------------------------------------------------------------


def test_kri_emission_shape(tmp_path: Path, capsys) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "stale_orphan", age_days=14.0)
    rc = main(["--root", str(root), "--baseline-ref", "", "--format", "kri"])
    captured = capsys.readouterr().out
    payload = json.loads(captured)
    assert payload["kri_id"] == KRI_ID
    assert payload["kri_name"] == KRI_NAME
    assert payload["regime"] == "cra"
    assert payload["status"] == "tripped"
    assert payload["coverage"]["orphans"] == 1
    assert any(
        f["code"] == "ORPHAN_NEW" and f["slug"] == "stale_orphan"
        for f in payload["findings"]
    )
    # ``tripped`` must be a non-zero exit so CI rejects the regression.
    assert rc == 1


def test_kri_emission_status_ok_on_clean_tree(tmp_path: Path, capsys) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "cited_pb", age_days=14.0)
    _add_mapping(root, "art-some", ["cited_pb"])
    rc = main(["--root", str(root), "--baseline-ref", "", "--format", "kri"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert payload["coverage"]["mapped"] == 1
    assert rc == 0


def test_kri_emission_status_degraded_inside_grace(tmp_path: Path, capsys) -> None:
    root = _scaffold(tmp_path)
    _add_playbook(root, "fresh_orphan", age_days=1.0)
    rc = main(["--root", str(root), "--baseline-ref", "", "--format", "kri"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "degraded"
    assert rc == 0  # degraded is informational, not a CI hard fail
