"""Tests for the sovereignty-cluster LM-endpoint pairing assertion.

Defends the G-04 sovereignty corner pairing invariant: every
sovereignty-cluster LM-endpoint coverage KPI must ship with a
sovereignty-cluster UNKNOWN-exposure residual-risk KRI at the same
version family.

Coverage mirrors the per-cluster sibling tests
(``test_catalogue_ocsf_bindings.py`` / ``test_detection_ocsf_bindings.py``):

* the shipped tree passes clean today (the F-MET-SOV SKELETON pairing
  on main is intact);
* the real catalogue actually contains at least one sovereignty-cluster
  LM-endpoint coverage KPI, so the guard is not silently no-op-ing;
* a synthetic sovereignty-cluster coverage KPI without a paired KRI is
  caught;
* a synthetic non-sovereignty coverage KPI is correctly ignored;
* a synthetic version-family mismatch (KPI@v2 with KRI only at @v1) is
  caught;
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

from tools.lint_sovereignty_lm_endpoint_pairing import (
    SOVEREIGNTY_PROPERTY,
    coverage_kpi_match,
    main,
    scan,
    unknown_exposure_kri_match,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_pairing_is_intact() -> None:
    """Every sovereignty-cluster LM-endpoint coverage KPI on main must
    carry a paired UNKNOWN-exposure KRI at the same version family."""
    findings = scan()
    assert findings == [], (
        "shipped catalogue has sovereignty-cluster LM-endpoint coverage "
        "KPI(s) without the paired UNKNOWN-exposure KRI: "
        + ", ".join(
            f"{f.kpi_stable_id} (@v{f.kpi_version})" for f in findings
        )
    )


def test_real_tree_actually_contains_a_coverage_kpi() -> None:
    """Sanity check: the shipped catalogue contains at least one
    sovereignty-cluster LM-endpoint coverage KPI. Without this anchor
    the pairing scan could degrade to a no-op (zero coverage KPIs to
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
        "catalogue has no sovereignty-cluster LM-endpoint coverage "
        "KPIs — the pairing guard would silently no-op."
    )
    # The F-MET-SOV SKELETON shipped this exact id; assert it so a
    # rename without rewiring is caught.
    assert "kpi.lm_endpoint_eu_residency_coverage@v1" in coverage_kpis


def test_real_tree_actually_contains_an_unknown_exposure_kri() -> None:
    """Sanity check companion: the shipped catalogue also contains at
    least one sovereignty-cluster UNKNOWN-exposure KRI — the right-hand
    side of the pairing must exist on disk too.
    """
    unknown_kris: set[str] = set()
    for path in sorted((REPO_ROOT / "content" / "metrics").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if unknown_exposure_kri_match(doc) is not None:
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                unknown_kris.add(sid)
    assert unknown_kris, (
        "catalogue has no sovereignty-cluster LM-endpoint UNKNOWN-"
        "exposure KRIs — the right-hand side of the pairing is empty."
    )
    assert "kri.lm_endpoint_unknown_residency_exposure@v1" in unknown_kris


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


def _coverage_kpi_payload(stable_id: str, sovereignty: bool = True) -> dict:
    return {
        "stable_id": stable_id,
        "kind": "kpi",
        "measurement": {"source": "composite"},
        "foundation_property": [SOVEREIGNTY_PROPERTY] if sovereignty else ["determinism"],
    }


def _unknown_exposure_kri_payload(
    stable_id: str, sovereignty: bool = True
) -> dict:
    return {
        "stable_id": stable_id,
        "kind": "kri",
        "measurement": {"source": "composite"},
        "foundation_property": [SOVEREIGNTY_PROPERTY] if sovereignty else ["determinism"],
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
        _coverage_kpi_payload("kpi.lm_endpoint_eu_residency_coverage@v1"),
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].kpi_stable_id == "kpi.lm_endpoint_eu_residency_coverage@v1"
    assert findings[0].kpi_version == "1"


def test_coverage_kpi_with_paired_kri_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "kpi_paired",
        _coverage_kpi_payload("kpi.lm_endpoint_eu_residency_coverage@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri_pair",
        _unknown_exposure_kri_payload(
            "kri.lm_endpoint_unknown_residency_exposure@v1"
        ),
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
        _coverage_kpi_payload("kpi.lm_endpoint_eu_residency_coverage@v2"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri_v1",
        _unknown_exposure_kri_payload(
            "kri.lm_endpoint_unknown_residency_exposure@v1"
        ),
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].kpi_version == "2"


def test_non_sovereignty_coverage_kpi_is_ignored(
    synthetic_metrics_dir: Path,
) -> None:
    """A coverage KPI whose foundation_property does not include
    sovereignty is out of cluster and the pairing rule does not apply.
    """
    _write_metric(
        synthetic_metrics_dir,
        "kpi_non_sovereignty",
        _coverage_kpi_payload(
            "kpi.lm_endpoint_audit_coverage@v1", sovereignty=False
        ),
    )
    assert scan(synthetic_metrics_dir) == []


def test_unknown_exposure_kri_must_carry_sovereignty(
    synthetic_metrics_dir: Path,
) -> None:
    """A candidate KRI that matches the stable-id shape but does not
    declare sovereignty as a foundation_property does not satisfy the
    pairing — the rule is sovereignty-cluster on both sides.
    """
    _write_metric(
        synthetic_metrics_dir,
        "kpi",
        _coverage_kpi_payload("kpi.lm_endpoint_eu_residency_coverage@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri_wrong_corner",
        _unknown_exposure_kri_payload(
            "kri.lm_endpoint_unknown_residency_exposure@v1",
            sovereignty=False,
        ),
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1


def test_pairing_generalises_to_alternative_kri_name(
    synthetic_metrics_dir: Path,
) -> None:
    """The pairing rule is keyed on the UNKNOWN-exposure shape, not on
    a fixed name — a future sovereignty LM-endpoint coverage KPI that
    ships a differently-named UNKNOWN-exposure KRI at the same version
    family should still satisfy the pairing.
    """
    _write_metric(
        synthetic_metrics_dir,
        "kpi",
        _coverage_kpi_payload("kpi.lm_endpoint_provider_coverage@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri_alt",
        _unknown_exposure_kri_payload(
            "kri.lm_endpoint_provider_unknown_exposure@v1"
        ),
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
        _coverage_kpi_payload("kpi.lm_endpoint_eu_residency_coverage@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri",
        _unknown_exposure_kri_payload(
            "kri.lm_endpoint_unknown_residency_exposure@v1"
        ),
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
        _coverage_kpi_payload("kpi.lm_endpoint_eu_residency_coverage@v1"),
    )
    rc = main(["--metrics-dir", str(synthetic_metrics_dir), "--format", "text"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "FAIL" in out
    assert "kpi.lm_endpoint_eu_residency_coverage@v1" in out


def test_cli_json_fail_payload(
    synthetic_metrics_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "kpi_unpaired",
        _coverage_kpi_payload("kpi.lm_endpoint_eu_residency_coverage@v1"),
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
        _coverage_kpi_payload("kpi.lm_endpoint_eu_residency_coverage@v1"),
    )
    _write_metric(
        synthetic_metrics_dir,
        "kri",
        _unknown_exposure_kri_payload(
            "kri.lm_endpoint_unknown_residency_exposure@v1"
        ),
    )
    rc = main(["--metrics-dir", str(synthetic_metrics_dir), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["status"] == "pass"
    assert payload["finding_count"] == 0


def test_cli_subprocess_real_tree() -> None:
    """End-to-end subprocess invocation against the shipped tree."""
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_sovereignty_lm_endpoint_pairing"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS" in proc.stdout
