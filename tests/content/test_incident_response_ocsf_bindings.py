"""Tests for the incident-response-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension for the
incident-response metric family: every metric whose ``playbook_refs``
resolve exclusively to the incident-response cluster must declare at
least one ``telemetry.ocsf.*`` ref.

Coverage mirrors ``test_vuln_patch_ocsf_bindings.py``:

* the shipped tree passes (every incident-response metric on main is
  bound to at least one OCSF source-data shape);
* the classifier identifies the full seven-metric cluster (structural
  anchor against silent no-op degradation);
* a synthetic incident-response-cluster metric missing its OCSF ref
  is caught;
* fan-out pipeline metrics that span incident-response + other
  playbooks are correctly excluded from the cluster gate;
* stripping the OCSF ref from any shipped incident-response metric
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

from tools.lint_incident_response_ocsf_bindings import (
    INCIDENT_RESPONSE_PLAYBOOK_IDS,
    has_ocsf_binding,
    is_incident_response_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_incident_response_metrics() -> None:
    """Every incident-response-cluster metric on main must carry OCSF."""
    findings = scan()
    assert findings == [], (
        "shipped incident-response cluster has metrics without an "
        "OCSF source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_full_incident_response_cluster() -> None:
    """Sanity check: the scan classifies every shipped incident-
    response metric as cluster-class.

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
        if is_incident_response_metric(pb):
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                classified.add(sid)
    expected = {
        "kpi.backup_integrity_pass_rate@v1",
        "kri.breach_notification_clock_margin@v1",
        "kpi.mttd_exfil@v1",
        "kpi.mttd_ransomware@v1",
        "kpi.mttr_containment@v1",
        "kpi.notification_sla_compliance@v1",
        "kri.regulator_notification_overrun@v1",
    }
    missing = expected - classified
    assert not missing, (
        "incident-response-cluster classifier no longer identifies "
        f"the full metric set — missing={sorted(missing)} "
        f"(classified={sorted(classified)})."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: incident-response-cluster metric missing OCSF binding
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


def test_incident_response_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_mttr_containment",
        {
            "stable_id": "kpi.synthetic_unbound_mttr_containment@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.incident_management@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id
        == "kpi.synthetic_unbound_mttr_containment@v1"
    )


def test_incident_response_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_bound_incident",
        {
            "stable_id": "kpi.synthetic_bound_incident@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.incident_management@v1"}
            ],
            "telemetry_refs": ["telemetry.ocsf.incident_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_ransomware_containment_metric_without_ocsf_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    """Another cluster member — the ransomware_containment playbook —
    is gated the same way."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_ransomware",
        {
            "stable_id": "kri.synthetic_unbound_ransomware@v1",
            "kind": "kri",
            "playbook_refs": [
                {"playbook_id": "playbook.ransomware_containment@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id
        == "kri.synthetic_unbound_ransomware@v1"
    )


def test_ddos_response_metric_without_ocsf_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    """The ddos_response playbook member is gated the same way."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_ddos",
        {
            "stable_id": "kpi.synthetic_unbound_ddos@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.ddos_response@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].metric_stable_id == "kpi.synthetic_unbound_ddos@v1"


def test_fanout_pir_metric_is_not_incident_response(
    synthetic_metrics_dir: Path,
) -> None:
    """Fan-out metrics that span incident-response plus non-cluster
    playbooks (e.g. post_incident_review) must be kept out by the
    exclusivity gate — those belong to the PIR cluster, not this one."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_pir_fanout",
        {
            "stable_id": "kpi.synthetic_pir_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.incident_management@v1"},
                {"playbook_id": "playbook.post_incident_review@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_fanout_executive_metrics_is_not_incident_response(
    synthetic_metrics_dir: Path,
) -> None:
    """Fan-out metrics that span incident-response plus the
    executive_metrics catch-all must be kept out by the exclusivity
    gate."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_exec_fanout",
        {
            "stable_id": "kpi.synthetic_exec_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.incident_management@v1"},
                {"playbook_id": "playbook.executive_metrics@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_playbook_refs_is_not_incident_response(
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
# Negative regression for every incident-response metric in the
# cluster: stripping its OCSF telemetry_refs MUST trip the assertion.
# Per-metric coverage so a regression on any single binding surfaces.
# ---------------------------------------------------------------------------


INCIDENT_RESPONSE_METRICS = (
    "backup_integrity_pass_rate",
    "breach_notification_clock_margin",
    "mttd_exfil",
    "mttd_ransomware",
    "mttr_containment",
    "notification_sla_compliance",
    "regulator_notification_overrun",
)


@pytest.mark.parametrize("metric_name", INCIDENT_RESPONSE_METRICS)
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
        "incident-response cluster is supposed to leave every metric "
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
        "the incident-response-cluster assertion "
        f"(findings={[f.metric_stable_id for f in findings]})"
    )
    assert findings[0].metric_stable_id == doc.get("stable_id")


# ---------------------------------------------------------------------------
# Helpers / CLI
# ---------------------------------------------------------------------------


def test_has_ocsf_binding_helper() -> None:
    assert has_ocsf_binding(["telemetry.ocsf.incident_finding@v1"])
    assert has_ocsf_binding(
        ["telemetry.internal.something@v1", "telemetry.ocsf.detection_finding@v1"]
    )
    assert not has_ocsf_binding([])
    assert not has_ocsf_binding(["telemetry.internal.something@v1"])


def test_is_incident_response_metric_helper() -> None:
    assert is_incident_response_metric(["playbook.incident_management@v1"])
    assert is_incident_response_metric(["playbook.ransomware_containment@v1"])
    assert is_incident_response_metric(["playbook.ddos_response@v1"])
    assert is_incident_response_metric(["playbook.data_exfil@v1"])
    assert is_incident_response_metric(
        [
            "playbook.incident_management@v1",
            "playbook.ransomware_containment@v1",
            "playbook.data_exfil@v1",
        ]
    )
    assert not is_incident_response_metric([])
    assert not is_incident_response_metric(
        [
            "playbook.incident_management@v1",
            "playbook.post_incident_review@v1",
        ]
    )
    assert not is_incident_response_metric(["playbook.identity_compromise@v1"])


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_incident_response_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "incident-response-ocsf-bindings: PASS" in proc.stdout


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
                {"playbook_id": "playbook.incident_management@v1"}
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
                {"playbook_id": "playbook.incident_management@v1"}
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
    assert payload["incident_response_cluster"] == sorted(
        INCIDENT_RESPONSE_PLAYBOOK_IDS
    )
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.synthetic_unbound@v1"
    )
