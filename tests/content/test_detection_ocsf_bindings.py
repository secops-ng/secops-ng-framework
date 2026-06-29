"""Tests for the detection-latency-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension for the
detection-latency ``mttd_*`` metric family: every metric whose
``playbook_refs`` resolve exclusively to the detection-latency cluster
must declare at least one ``telemetry.ocsf.*`` ref.

Coverage mirrors ``test_posture_ocsf_bindings.py``:

* the shipped tree passes (the F-MET-OCSF-DETECT SKELETON green
  anchor — mttd_phishing — is bound to OCSF Email Activity and OCSF
  Detection Finding);
* a synthetic detection-cluster metric missing its OCSF ref is caught;
* fan-out pipeline/sovereignty metrics that span detection + other
  playbooks are correctly excluded from the cluster gate;
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

from tools.lint_detection_ocsf_bindings import (
    DETECTION_PLAYBOOK_IDS,
    has_ocsf_binding,
    is_detection_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_detection_metrics() -> None:
    """Every detection-latency-cluster metric on main must carry OCSF."""
    findings = scan()
    assert findings == [], (
        "shipped detection-latency cluster has metrics without an OCSF "
        "source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_full_mttd_cluster() -> None:
    """Sanity check: the scan classifies every shipped mttd_* metric
    as detection-latency-class once the CORE wave widens the cluster.

    Without this anchor the assertion could silently degrade to a
    no-op (zero findings because zero metrics classify) and pass for
    the wrong reason.
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
        if is_detection_metric(pb):
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                classified.add(sid)
    expected = {
        "kpi.mttd_phishing@v1",
        "kpi.mttd_ransomware@v1",
        "kpi.mttd_exfil@v1",
        "kpi.mttd_cloud_misconfig@v1",
        "kpi.mttd_identity_compromise@v1",
        "kpi.mttd_threat_intel_indicator@v1",
    }
    missing = expected - classified
    assert not missing, (
        "detection-latency-cluster classifier no longer identifies the "
        f"full mttd_* set — missing={sorted(missing)} "
        f"(classified={sorted(classified)})."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: detection-cluster metric missing OCSF binding
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


def test_detection_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_detection",
        {
            "stable_id": "kpi.synthetic_unbound_detection@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.phishing_triage@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id == "kpi.synthetic_unbound_detection@v1"
    )


def test_detection_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_bound_detection",
        {
            "stable_id": "kpi.synthetic_bound_detection@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.phishing_triage@v1"}
            ],
            "telemetry_refs": ["telemetry.ocsf.detection_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_fanout_pipeline_metric_is_not_detection(
    synthetic_metrics_dir: Path,
) -> None:
    """Pipeline/sovereignty metrics fan out across detection + non-
    detection playbooks; the exclusivity gate must keep them out."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_pipeline_fanout",
        {
            "stable_id": "kpi.synthetic_pipeline_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.phishing_triage@v1"},
                {"playbook_id": "playbook.executive_metrics@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_playbook_refs_is_not_detection(
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
# Negative regression for every mttd_* metric in the cluster: stripping
# its OCSF telemetry_refs MUST trip the assertion. This is the
# structural guard the F-MET-OCSF-DETECT CORE card asks for —
# per-metric coverage so a regression on any single binding surfaces.
# ---------------------------------------------------------------------------


MTTD_METRICS = (
    "mttd_phishing",
    "mttd_ransomware",
    "mttd_exfil",
    "mttd_cloud_misconfig",
    "mttd_identity_compromise",
    "mttd_threat_intel_indicator",
)


@pytest.mark.parametrize("metric_name", MTTD_METRICS)
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
        "CORE wave is supposed to leave every mttd_* metric bound; "
        "fix the metric file before this test can guard it."
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
        "the detection-latency-cluster assertion "
        f"(findings={[f.metric_stable_id for f in findings]})"
    )
    assert findings[0].metric_stable_id == doc.get("stable_id")


# ---------------------------------------------------------------------------
# Helpers / CLI
# ---------------------------------------------------------------------------


def test_has_ocsf_binding_helper() -> None:
    assert has_ocsf_binding(["telemetry.ocsf.detection_finding@v1"])
    assert has_ocsf_binding(
        ["telemetry.internal.something@v1", "telemetry.ocsf.foo@v1"]
    )
    assert not has_ocsf_binding([])
    assert not has_ocsf_binding(["telemetry.internal.something@v1"])


def test_is_detection_metric_helper() -> None:
    assert is_detection_metric(["playbook.phishing_triage@v1"])
    assert not is_detection_metric([])
    assert not is_detection_metric(
        ["playbook.phishing_triage@v1", "playbook.executive_metrics@v1"]
    )
    assert not is_detection_metric(["playbook.asset_management@v1"])


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_detection_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "detection-ocsf-bindings: PASS" in proc.stdout


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
                {"playbook_id": "playbook.phishing_triage@v1"}
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
                {"playbook_id": "playbook.phishing_triage@v1"}
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
    assert payload["detection_cluster"] == sorted(DETECTION_PLAYBOOK_IDS)
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.synthetic_unbound@v1"
    )
