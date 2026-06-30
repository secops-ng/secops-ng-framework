"""Tests for the determinism-cluster replay pairing assertion.

Defends the G-04 determinism corner pairing invariant: every
determinism-cluster replay coverage KPI must ship with a
determinism-cluster replay drift residual-risk KRI at the same
version family.

Coverage mirrors the sibling sovereignty test
(``test_sovereignty_lm_endpoint_pairing.py``):

* the shipped tree passes clean today (the F-MET-DET replay pair on
  main is intact);
* the real catalogue actually contains at least one
  determinism-cluster replay coverage KPI, so the guard is not
  silently no-op-ing;
* a synthetic determinism-cluster coverage KPI without a paired KRI
  is caught;
* a synthetic non-determinism coverage KPI is correctly ignored;
* a synthetic version-family mismatch (KPI@v2 with KRI only at @v1)
  is caught;
* the CLI exits non-zero with a contributor-friendly message on
  failure and zero on pass, in both ``text`` and ``json`` formats.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.lint_determinism_replay_pairing import (
    DETERMINISM_PROPERTY,
    coverage_kpi_match,
    drift_kri_match,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_pairing_is_intact() -> None:
    """Every determinism-cluster replay coverage KPI on main must
    carry a paired drift KRI at the same version family."""
    findings = scan()
    assert findings == [], (
        "shipped catalogue has determinism-cluster replay coverage "
        "KPI(s) without the paired drift KRI: "
        + ", ".join(
            f"{f.kpi_stable_id} (@v{f.kpi_version})" for f in findings
        )
    )


def test_real_tree_actually_contains_a_coverage_kpi() -> None:
    """Sanity check: the shipped catalogue contains at least one
    determinism-cluster replay coverage KPI. Without this anchor the
    pairing scan could degrade to a no-op (zero coverage KPIs to
    pair) and pass for the wrong reason.
    """
    coverage_kpis: set[str] = set()
    for path in sorted((REPO_ROOT / "content" / "metrics").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if coverage_kpi_match(doc) is not None:
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                coverage_kpis.add(sid)
    assert coverage_kpis, (
        "catalogue has no determinism-cluster replay coverage KPIs — "
        "the pairing guard would silently no-op."
    )
    # The F-MET-DET replay coverage KPI shipped this exact id; assert
    # it so a rename without rewiring is caught.
    assert "kpi.same_target_replay_determinism_rate@v1" in coverage_kpis


def test_real_tree_actually_contains_a_drift_kri() -> None:
    """Sanity check companion: the shipped catalogue also contains at
    least one determinism-cluster replay drift KRI — the right-hand
    side of the pairing must exist on disk too.
    """
    drift_kris: set[str] = set()
    for path in sorted((REPO_ROOT / "content" / "metrics").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if drift_kri_match(doc) is not None:
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                drift_kris.add(sid)
    assert drift_kris, (
        "catalogue has no determinism-cluster replay drift KRIs — "
        "the right-hand side of the pairing is empty."
    )
    assert "kri.same_target_replay_drift@v1" in drift_kris


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_metrics_dir(tmp_path: Path) -> Path:
    d = tmp_path / "metrics"
    d.mkdir()
    return d


def _write_metric(directory: Path, name: str, payload: dict) -> Path:
    path = directory / f"{name}.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def _coverage_kpi_payload(stable_id: str, determinism: bool = True) -> dict:
    return {
        "stable_id": stable_id,
        "kind": "kpi",
        "measurement": {"source": "composite"},
        "foundation_property": [DETERMINISM_PROPERTY] if determinism else ["sovereignty"],
    }


def _drift_kri_payload(stable_id: str, determinism: bool = True) -> dict:
    return {
        "stable_id": stable_id,
        "kind": "kri",
        "measurement": {"source": "composite"},
        "foundation_property": [DETERMINISM_PROPERTY] if determinism else ["sovereignty"],
    }


# ---------------------------------------------------------------------------
# Synthetic positive: coverage KPI without the paired KRI
# ---------------------------------------------------------------------------


def test_coverage_kpi_without_pair_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "kpi_unpaired",
        _coverage_kpi_payload("kpi.same_target_replay_determinism_rate@v1"),
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].kpi_stable_id == "kpi.same_target_replay_determinism_rate@v1"
    assert findings[0].kpi_version == "1"


def test_coverage_kpi_with_paired_kri_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "kpi_paired",
        _coverage_kpi_payload("kpi.same_target_replay_determinism_rate@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri_pair",
        _drift_kri_payload("kri.same_target_replay_drift@v1"),
    )
    assert scan(synthetic_metrics_dir) == []


def test_pairing_must_match_version_family(
    synthetic_metrics_dir: Path,
) -> None:
    """A v2 coverage KPI cannot be silently covered by a v1 KRI — the
    pairing is keyed per version family.
    """
    _write_metric(
        synthetic_metrics_dir,
        "kpi_v2",
        _coverage_kpi_payload("kpi.same_target_replay_determinism_rate@v2"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri_v1",
        _drift_kri_payload("kri.same_target_replay_drift@v1"),
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].kpi_version == "2"


def test_non_determinism_coverage_kpi_is_ignored(
    synthetic_metrics_dir: Path,
) -> None:
    """A coverage KPI whose foundation_property does not include
    determinism is out of cluster and the pairing rule does not apply.
    """
    _write_metric(
        synthetic_metrics_dir,
        "kpi_non_determinism",
        _coverage_kpi_payload(
            "kpi.some_replay_determinism_rate@v1", determinism=False
        ),
    )
    assert scan(synthetic_metrics_dir) == []


def test_drift_kri_must_carry_determinism(
    synthetic_metrics_dir: Path,
) -> None:
    """A candidate KRI that matches the stable-id shape but does not
    declare determinism as a foundation_property does not satisfy the
    pairing — the rule is determinism-cluster on both sides.
    """
    _write_metric(
        synthetic_metrics_dir,
        "kpi",
        _coverage_kpi_payload("kpi.same_target_replay_determinism_rate@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri_wrong_corner",
        _drift_kri_payload(
            "kri.same_target_replay_drift@v1",
            determinism=False,
        ),
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1


def test_pairing_generalises_to_alternative_kri_name(
    synthetic_metrics_dir: Path,
) -> None:
    """The pairing rule is keyed on the replay-drift shape, not on a
    fixed name — a future determinism-corner replay coverage KPI that
    ships a differently-named replay drift KRI at the same version
    family should still satisfy the pairing.
    """
    _write_metric(
        synthetic_metrics_dir,
        "kpi",
        _coverage_kpi_payload("kpi.cross_target_replay_parity_rate@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri_alt",
        _drift_kri_payload("kri.cross_target_replay_drift@v1"),
    )
    assert scan(synthetic_metrics_dir) == []


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_cli_text_pass_exits_zero(
    synthetic_metrics_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "kpi",
        _coverage_kpi_payload("kpi.same_target_replay_determinism_rate@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri",
        _drift_kri_payload("kri.same_target_replay_drift@v1"),
    )
    rc = main(["--metrics-dir", str(synthetic_metrics_dir), "--format", "text"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "PASS" in out


def test_cli_text_fail_exits_nonzero(
    synthetic_metrics_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "kpi_unpaired",
        _coverage_kpi_payload("kpi.same_target_replay_determinism_rate@v1"),
    )
    rc = main(["--metrics-dir", str(synthetic_metrics_dir), "--format", "text"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL" in out
    assert "kpi.same_target_replay_determinism_rate@v1" in out


def test_cli_json_fail_payload(
    synthetic_metrics_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "kpi_unpaired",
        _coverage_kpi_payload("kpi.same_target_replay_determinism_rate@v1"),
    )
    rc = main(["--metrics-dir", str(synthetic_metrics_dir), "--format", "json"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 1
    assert payload["status"] == "fail"
    assert payload["finding_count"] == 1
    assert payload["findings"][0]["kpi_version"] == "1"


def test_cli_json_pass_payload(
    synthetic_metrics_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "kpi",
        _coverage_kpi_payload("kpi.same_target_replay_determinism_rate@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri",
        _drift_kri_payload("kri.same_target_replay_drift@v1"),
    )
    rc = main(["--metrics-dir", str(synthetic_metrics_dir), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["status"] == "pass"
    assert payload["finding_count"] == 0


def test_cli_subprocess_real_tree() -> None:
    """End-to-end subprocess invocation against the shipped tree."""
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_determinism_replay_pairing"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS" in proc.stdout
