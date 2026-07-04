"""Tests for the DORA-latency-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension for the DORA
Article 19(4) regulator-notification dispatch-latency KRI triad:
every metric whose ``stable_id`` is in the DORA-latency allow-list
must declare at least one ``telemetry.ocsf.*`` ref.

Coverage mirrors ``test_cra_latency_ocsf_bindings.py`` (with the
playbook-exclusivity fan-out cases dropped — this cluster
classifies by ``stable_id`` allow-list, not ``playbook_refs``):

* the shipped tree passes (every DORA-latency metric on main is
  bound to at least one OCSF source-data shape);
* the classifier identifies the three anchor metrics from the
  SKELETON PR (structural anchor against silent no-op degradation);
* a synthetic DORA-latency-cluster metric missing its OCSF ref is
  caught;
* metrics whose ``stable_id`` is outside the allow-list are
  correctly excluded;
* stripping the OCSF ref from any shipped DORA-latency metric trips
  the assertion (per-metric structural guard);
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

from tools.lint_dora_latency_ocsf_bindings import (
    DORA_LATENCY_STABLE_IDS,
    has_ocsf_binding,
    is_dora_latency_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_dora_latency_metrics() -> None:
    """Every DORA-latency-cluster metric on main must carry OCSF."""
    findings = scan()
    assert findings == [], (
        "shipped DORA-latency cluster has metrics without an OCSF "
        "source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_dora_latency_anchors() -> None:
    """Sanity check: the scan classifies the three DORA Article 19(4)
    dispatch-latency KRI anchors as cluster-class.

    Without this anchor the assertion could silently degrade to a
    no-op (zero findings because zero metrics classify) and pass for
    the wrong reason. SKELETON anchors on the three KRIs shipped in
    F-MET-DORA-LATENCY SKELETON; a future CORE wave may widen the
    expected set.
    """
    classified: set[str] = set()
    for path in sorted((REPO_ROOT / "content" / "metrics").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        sid = doc.get("stable_id")
        if is_dora_latency_metric(sid):
            classified.add(sid)
    expected = {
        "kri.dora_incident_initial_report_latency_hours@v1",
        "kri.dora_incident_intermediate_report_latency_hours@v1",
        "kri.dora_incident_final_report_latency_days@v1",
    }
    missing = expected - classified
    assert not missing, (
        "DORA-latency-cluster classifier no longer identifies the "
        f"anchor metrics — missing={sorted(missing)} "
        f"(classified={sorted(classified)})."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: DORA-latency-cluster metric missing OCSF binding
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


def test_dora_latency_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "dora_incident_initial_report_latency_hours",
        {
            "stable_id": "kri.dora_incident_initial_report_latency_hours@v1",
            "kind": "kri",
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id
        == "kri.dora_incident_initial_report_latency_hours@v1"
    )


def test_dora_latency_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "dora_incident_initial_report_latency_hours",
        {
            "stable_id": "kri.dora_incident_initial_report_latency_hours@v1",
            "kind": "kri",
            "telemetry_refs": ["telemetry.ocsf.compliance_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_out_of_allowlist_stable_id_is_not_dora_latency(
    synthetic_metrics_dir: Path,
) -> None:
    """Metrics whose ``stable_id`` is not in the DORA-latency
    allow-list must be kept out — even if their file name is
    suggestive or they share ``playbook.incident_management@v1``
    with the host chain."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_out_of_allowlist",
        {
            "stable_id": "kri.dora_something_else_latency_hours@v1",
            "kind": "kri",
            "playbook_refs": [
                {"playbook_id": "playbook.incident_management@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_stable_id_is_not_dora_latency(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_no_stable_id",
        {
            "kind": "kri",
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


# ---------------------------------------------------------------------------
# Negative regression for every DORA-latency metric in the cluster:
# stripping its OCSF telemetry_refs MUST trip the assertion.
# Per-metric coverage so a regression on any single binding surfaces.
# ---------------------------------------------------------------------------


DORA_LATENCY_METRICS = (
    "dora_incident_initial_report_latency_hours",
    "dora_incident_intermediate_report_latency_hours",
    "dora_incident_final_report_latency_days",
)


@pytest.mark.parametrize("metric_name", DORA_LATENCY_METRICS)
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
        "DORA-latency cluster is supposed to leave every metric bound; "
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
        "the DORA-latency-cluster assertion "
        f"(findings={[f.metric_stable_id for f in findings]})"
    )
    assert findings[0].metric_stable_id == doc.get("stable_id")


# ---------------------------------------------------------------------------
# Helpers / CLI
# ---------------------------------------------------------------------------


def test_has_ocsf_binding_helper() -> None:
    assert has_ocsf_binding(["telemetry.ocsf.compliance_finding@v1"])
    assert has_ocsf_binding(
        ["telemetry.internal.something@v1", "telemetry.ocsf.api_activity@v1"]
    )
    assert not has_ocsf_binding([])
    assert not has_ocsf_binding(["telemetry.internal.something@v1"])


def test_is_dora_latency_metric_helper() -> None:
    assert is_dora_latency_metric(
        "kri.dora_incident_initial_report_latency_hours@v1"
    )
    assert is_dora_latency_metric(
        "kri.dora_incident_final_report_latency_days@v1"
    )
    assert not is_dora_latency_metric(None)
    assert not is_dora_latency_metric("")
    assert not is_dora_latency_metric(
        "kri.dora_something_else_latency_hours@v1"
    )
    assert not is_dora_latency_metric(
        "kri.cra_early_warning_latency_hours@v1"
    )


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_dora_latency_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "dora-latency-ocsf-bindings: PASS" in proc.stdout


def test_cli_fails_with_synthetic_unbound(tmp_path: Path) -> None:
    d = tmp_path / "metrics"
    d.mkdir()
    _write_metric(
        d,
        "dora_incident_initial_report_latency_hours",
        {
            "stable_id": "kri.dora_incident_initial_report_latency_hours@v1",
            "kind": "kri",
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
        "dora_incident_initial_report_latency_hours",
        {
            "stable_id": "kri.dora_incident_initial_report_latency_hours@v1",
            "kind": "kri",
            "telemetry_refs": [],
        },
    )
    rc = main(["--format", "json", "--metrics-dir", str(d)])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 1
    assert payload["status"] == "fail"
    assert payload["finding_count"] == 1
    assert payload["dora_latency_cluster"] == sorted(
        DORA_LATENCY_STABLE_IDS
    )
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kri.dora_incident_initial_report_latency_hours@v1"
    )
