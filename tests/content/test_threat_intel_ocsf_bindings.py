"""Tests for the threat-intel-&-phishing-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension for the threat-intel
& phishing metric family: every metric whose ``playbook_refs`` resolve
exclusively to the threat-intel cluster must declare at least one
``telemetry.ocsf.*`` ref.

Coverage mirrors ``test_vuln_patch_ocsf_bindings.py``:

* the shipped tree passes (every threat-intel/phishing metric on main
  is bound to at least one OCSF source-data shape);
* the classifier identifies the full seven-metric cluster (structural
  anchor against silent no-op degradation);
* a synthetic threat-intel-cluster metric missing its OCSF ref is
  caught;
* fan-out pipeline metrics that span threat-intel + other playbooks
  are correctly excluded from the cluster gate;
* stripping the OCSF ref from any shipped threat-intel/phishing metric
  trips the assertion (per-metric structural guard);
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

from tools.lint_threat_intel_ocsf_bindings import (
    THREAT_INTEL_PLAYBOOK_IDS,
    has_ocsf_binding,
    is_threat_intel_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_threat_intel_metrics() -> None:
    """Every threat-intel/phishing-cluster metric on main must carry OCSF."""
    findings = scan()
    assert findings == [], (
        "shipped threat-intel & phishing cluster has metrics without an "
        "OCSF source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_full_threat_intel_cluster() -> None:
    """Sanity check: the scan classifies every shipped threat-intel/
    phishing metric as cluster-class.

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
        if is_threat_intel_metric(pb):
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                classified.add(sid)
    expected = {
        "kpi.mttd_threat_intel_indicator@v1",
        "kpi.coverage_threat_intel_feed@v1",
        "kpi.mttr_blocklist_propagation@v1",
        "kpi.mttd_phishing@v1",
        "kpi.mttr_phishing_triage@v1",
        "kri.phishing_suppression_rate@v1",
        "kpi.phishing_sim_click_rate@v1",
        # F-MET-G04-THREATINTEL SKELETON — threat-intelligence-operations
        # KPI/KRI pair (NIS2 Art.23 / Art.26(2), DORA Art.19). Both pin
        # their host chain through playbook.threat_intel_ingest@v1, so
        # they classify into this cluster and must stay OCSF-bound.
        "kpi.threat_intel_indicator_ingestion_rate@v1",
        "kri.threat_intel_stale_ioc_ratio@v1",
    }
    missing = expected - classified
    assert not missing, (
        "threat-intel-&-phishing-cluster classifier no longer identifies "
        f"the full metric set — missing={sorted(missing)} "
        f"(classified={sorted(classified)})."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: threat-intel-cluster metric missing OCSF binding
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


def test_threat_intel_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_threat_intel",
        {
            "stable_id": "kpi.synthetic_unbound_threat_intel@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.threat_intel_ingest@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id
        == "kpi.synthetic_unbound_threat_intel@v1"
    )


def test_threat_intel_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_bound_threat_intel",
        {
            "stable_id": "kpi.synthetic_bound_threat_intel@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.threat_intel_ingest@v1"}
            ],
            "telemetry_refs": ["telemetry.ocsf.detection_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_phishing_triage_metric_without_ocsf_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    """The other member of the cluster — the phishing_triage playbook
    — is gated the same way."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_phishing",
        {
            "stable_id": "kri.synthetic_unbound_phishing@v1",
            "kind": "kri",
            "playbook_refs": [
                {"playbook_id": "playbook.phishing_triage@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].metric_stable_id == "kri.synthetic_unbound_phishing@v1"


def test_fanout_sovereignty_metric_is_not_threat_intel(
    synthetic_metrics_dir: Path,
) -> None:
    """Fan-out / sovereignty pipeline metrics that span phishing_triage
    plus non-cluster playbooks (e.g. executive_metrics,
    it_security_support_agent — the lm_endpoint_* residency metrics)
    must be kept out by the exclusivity gate."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_sovereignty_fanout",
        {
            "stable_id": "kpi.synthetic_sovereignty_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.phishing_triage@v1"},
                {"playbook_id": "playbook.executive_metrics@v1"},
                {"playbook_id": "playbook.it_security_support_agent@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_playbook_refs_is_not_threat_intel(
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
# Negative regression for every threat-intel/phishing metric in the
# cluster: stripping its OCSF telemetry_refs MUST trip the assertion.
# Per-metric coverage so a regression on any single binding surfaces.
# ---------------------------------------------------------------------------


THREAT_INTEL_METRICS = (
    "mttd_threat_intel_indicator",
    "coverage_threat_intel_feed",
    "mttr_blocklist_propagation",
    "mttd_phishing",
    "mttr_phishing_triage",
    "phishing_suppression_rate",
    "phishing_sim_click_rate",
    # F-MET-G04-THREATINTEL SKELETON — threat-intelligence-operations
    # KPI/KRI pair. Guard the OCSF binding on each catalogue entry
    # independently so a silent detach on either file surfaces.
    "threat_intel_indicator_ingestion_rate",
    "threat_intel_stale_ioc_ratio",
)


@pytest.mark.parametrize("metric_name", THREAT_INTEL_METRICS)
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
        "threat-intel-&-phishing cluster is supposed to leave every "
        "metric bound; fix the metric file before this test can guard "
        "it."
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
        "the threat-intel-&-phishing-cluster assertion "
        f"(findings={[f.metric_stable_id for f in findings]})"
    )
    assert findings[0].metric_stable_id == doc.get("stable_id")


# ---------------------------------------------------------------------------
# Helpers / CLI
# ---------------------------------------------------------------------------


def test_has_ocsf_binding_helper() -> None:
    assert has_ocsf_binding(["telemetry.ocsf.detection_finding@v1"])
    assert has_ocsf_binding(
        ["telemetry.internal.something@v1", "telemetry.ocsf.email_activity@v1"]
    )
    assert not has_ocsf_binding([])
    assert not has_ocsf_binding(["telemetry.internal.something@v1"])


def test_is_threat_intel_metric_helper() -> None:
    assert is_threat_intel_metric(["playbook.threat_intel_ingest@v1"])
    assert is_threat_intel_metric(["playbook.phishing_triage@v1"])
    assert is_threat_intel_metric(
        [
            "playbook.threat_intel_ingest@v1",
            "playbook.phishing_triage@v1",
        ]
    )
    assert not is_threat_intel_metric([])
    assert not is_threat_intel_metric(
        [
            "playbook.phishing_triage@v1",
            "playbook.executive_metrics@v1",
        ]
    )
    assert not is_threat_intel_metric(["playbook.identity_compromise@v1"])


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_threat_intel_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "threat-intel-ocsf-bindings: PASS" in proc.stdout


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
                {"playbook_id": "playbook.threat_intel_ingest@v1"}
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
                {"playbook_id": "playbook.threat_intel_ingest@v1"}
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
    assert payload["threat_intel_cluster"] == sorted(
        THREAT_INTEL_PLAYBOOK_IDS
    )
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.synthetic_unbound@v1"
    )
