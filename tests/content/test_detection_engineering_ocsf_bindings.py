"""Tests for the detection-engineering-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension for the
detection-engineering metric family: every metric whose
``playbook_refs`` resolve exclusively to the detection-engineering
cluster must declare at least one ``telemetry.ocsf.*`` ref.

Coverage mirrors ``test_backup_recovery_ocsf_bindings.py``:

* the shipped tree passes (every detection-engineering metric on main
  is bound to at least one OCSF source-data shape);
* the classifier identifies the anchor metric (structural anchor
  against silent no-op degradation);
* a synthetic detection-engineering-cluster metric missing its OCSF
  ref is caught;
* fan-out metrics that span detection-engineering + other playbooks
  are correctly excluded from the cluster gate;
* stripping the OCSF ref from any shipped detection-engineering
  metric trips the assertion (per-metric structural guard);
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

from tools.lint_detection_engineering_ocsf_bindings import (
    DETECTION_ENGINEERING_PLAYBOOK_IDS,
    has_ocsf_binding,
    is_detection_engineering_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_detection_engineering_metrics() -> None:
    """Every detection-engineering-cluster metric on main must carry OCSF."""
    findings = scan()
    assert findings == [], (
        "shipped detection-engineering cluster has metrics without an "
        "OCSF source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_detection_engineering_anchor() -> None:
    """Sanity check: the scan classifies the anchor detection-
    engineering metric as cluster-class.

    Without this anchor the assertion could silently degrade to a
    no-op (zero findings because zero metrics classify) and pass for
    the wrong reason. SKELETON anchors on
    ``kpi.detection_coverage@v1``; the CORE wave may widen the
    expected set.
    """
    classified: set[str] = set()
    for path in sorted((REPO_ROOT / "content" / "metrics").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        pb: tuple[str, ...] = tuple(
            r["playbook_id"]
            for r in (doc.get("playbook_refs") or [])
            if isinstance(r, dict) and isinstance(r.get("playbook_id"), str)
        )
        if is_detection_engineering_metric(pb):
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                classified.add(sid)
    expected = {"kpi.detection_coverage@v1"}
    missing = expected - classified
    assert not missing, (
        "detection-engineering-cluster classifier no longer identifies "
        f"the anchor metric — missing={sorted(missing)} "
        f"(classified={sorted(classified)})."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: detection-engineering-cluster metric missing OCSF binding
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


def test_detection_engineering_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_deteng",
        {
            "stable_id": "kpi.synthetic_unbound_deteng@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.detection_engineering@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id
        == "kpi.synthetic_unbound_deteng@v1"
    )


def test_detection_engineering_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_bound_deteng",
        {
            "stable_id": "kpi.synthetic_bound_deteng@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.detection_engineering@v1"}
            ],
            "telemetry_refs": ["telemetry.ocsf.detection_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_fanout_incident_metric_is_not_detection_engineering(
    synthetic_metrics_dir: Path,
) -> None:
    """Fan-out metrics that span detection-engineering plus
    non-cluster playbooks (e.g. incident_management) must be kept out
    by the exclusivity gate — those belong to a different cluster,
    not this one."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_incident_fanout",
        {
            "stable_id": "kpi.synthetic_incident_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.detection_engineering@v1"},
                {"playbook_id": "playbook.incident_management@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_fanout_executive_metrics_is_not_detection_engineering(
    synthetic_metrics_dir: Path,
) -> None:
    """Fan-out metrics that span detection-engineering plus the
    executive_metrics catch-all must be kept out by the exclusivity
    gate."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_exec_fanout",
        {
            "stable_id": "kpi.synthetic_exec_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.detection_engineering@v1"},
                {"playbook_id": "playbook.executive_metrics@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_playbook_refs_is_not_detection_engineering(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_no_playbook",
        {
            "stable_id": "kpi.synthetic_no_playbook@v1",
            "kind": "kpi",
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


# ---------------------------------------------------------------------------
# Negative regression for every detection-engineering metric in the
# cluster: stripping its OCSF telemetry_refs MUST trip the assertion.
# Per-metric coverage so a regression on any single binding surfaces.
# ---------------------------------------------------------------------------


DETECTION_ENGINEERING_METRICS = (
    "detection_coverage",
)


@pytest.mark.parametrize("metric_name", DETECTION_ENGINEERING_METRICS)
def test_stripping_ocsf_ref_trips_assertion(
    tmp_path: Path, metric_name: str
) -> None:
    src = REPO_ROOT / "content" / "metrics" / f"{metric_name}.yaml"
    doc = yaml.safe_load(src.read_text(encoding="utf-8"))
    original_ocsf_refs = [
        r for r in (doc.get("telemetry_refs") or [])
        if isinstance(r, str) and r.startswith("telemetry.ocsf.")
    ]
    assert original_ocsf_refs, (
        f"{metric_name}.yaml has no OCSF telemetry_refs on main — the "
        "detection-engineering cluster is supposed to leave every metric "
        "bound; fix the metric file before this test can guard it."
    )
    doc["telemetry_refs"] = [
        r for r in (doc.get("telemetry_refs") or [])
        if not (isinstance(r, str) and r.startswith("telemetry.ocsf."))
    ]
    dst_dir = tmp_path / "metrics"
    dst_dir.mkdir()
    (dst_dir / f"{metric_name}.yaml").write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )
    findings = scan(dst_dir)
    assert len(findings) == 1, (
        f"stripping OCSF refs from {metric_name}.yaml did not trip "
        "the detection-engineering-cluster assertion "
        f"(findings={[f.metric_stable_id for f in findings]})"
    )
    assert findings[0].metric_stable_id == doc.get("stable_id")


# ---------------------------------------------------------------------------
# Helpers / CLI
# ---------------------------------------------------------------------------


def test_has_ocsf_binding_helper() -> None:
    assert has_ocsf_binding(["telemetry.ocsf.detection_finding@v1"])
    assert has_ocsf_binding(
        ["telemetry.internal.something@v1", "telemetry.ocsf.api_activity@v1"]
    )
    assert not has_ocsf_binding([])
    assert not has_ocsf_binding(["telemetry.internal.something@v1"])


def test_is_detection_engineering_metric_helper() -> None:
    assert is_detection_engineering_metric(
        ["playbook.detection_engineering@v1"]
    )
    assert not is_detection_engineering_metric([])
    assert not is_detection_engineering_metric(
        [
            "playbook.detection_engineering@v1",
            "playbook.incident_management@v1",
        ]
    )
    assert not is_detection_engineering_metric(
        ["playbook.incident_management@v1"]
    )


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_detection_engineering_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "detection-engineering-ocsf-bindings: PASS" in proc.stdout


def test_cli_fails_with_synthetic_unbound(tmp_path: Path) -> None:
    d = tmp_path / "metrics"
    d.mkdir()
    _write_metric(
        d,
        "synthetic_unbound",
        {
            "stable_id": "kpi.synthetic_unbound@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.detection_engineering@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    rc = main(["--format", "text", "--metrics-dir", str(d)])
    assert rc == 1


def test_cli_json_output_shape(tmp_path: Path, capsys) -> None:
    d = tmp_path / "metrics"
    d.mkdir()
    _write_metric(
        d,
        "synthetic_unbound",
        {
            "stable_id": "kpi.synthetic_unbound@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.detection_engineering@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    rc = main(["--format", "json", "--metrics-dir", str(d)])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 1
    assert payload["status"] == "fail"
    assert payload["finding_count"] == 1
    assert payload["detection_engineering_cluster"] == sorted(
        DETECTION_ENGINEERING_PLAYBOOK_IDS
    )
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.synthetic_unbound@v1"
    )
