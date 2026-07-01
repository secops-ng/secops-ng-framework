"""Tests for the post-incident-review-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension: every metric
whose ``playbook_refs`` resolve exclusively to the
post-incident-review (PIR) cluster must declare at least one
``telemetry.ocsf.*`` ref.

Coverage:

* the shipped tree passes (post-F-MET-OCSF-PIR-SKELETON main has
  every PIR-cluster metric bound to ``telemetry.ocsf.incident_finding@v1``);
* a synthetic PIR-class metric missing its OCSF ref is caught;
* fan-out metrics (PIR + non-PIR playbooks) are correctly excluded
  from the cluster gate;
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

from tools.lint_post_incident_review_ocsf_bindings import (
    POST_INCIDENT_REVIEW_PLAYBOOK_IDS,
    has_ocsf_binding,
    is_post_incident_review_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_pir_metrics() -> None:
    """Every PIR-cluster metric on main must carry an OCSF ref."""
    findings = scan()
    assert findings == [], (
        "shipped post-incident-review cluster has metrics without an OCSF "
        "source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_known_pir_metrics() -> None:
    """Sanity check: the scan actually classifies the four PIR-cluster
    metrics on main as PIR-class.

    Without this anchor the assertion could silently degrade to a
    no-op (zero findings because zero metrics classify) and pass for
    the wrong reason.
    """
    known_pir = {
        "kpi.corrective_action_close_rate@v1",
        "kri.corrective_action_overdue@v1",
        "kpi.review_completion_sla@v1",
        "kpi.timeline_completeness@v1",
    }
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
        if is_post_incident_review_metric(pb):
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                classified.add(sid)
    missing = known_pir - classified
    assert not missing, (
        "PIR-cluster classifier no longer identifies these metrics: "
        f"{sorted(missing)} — adjust POST_INCIDENT_REVIEW_PLAYBOOK_IDS or the test."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: PIR-class metric missing OCSF binding
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


def test_pir_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_pir",
        {
            "stable_id": "kpi.synthetic_unbound_pir@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.post_incident_review@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].metric_stable_id == "kpi.synthetic_unbound_pir@v1"


def test_pir_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_bound_pir",
        {
            "stable_id": "kpi.synthetic_bound_pir@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.post_incident_review@v1"}
            ],
            "telemetry_refs": ["telemetry.ocsf.incident_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_fanout_pipeline_metric_is_not_pir(
    synthetic_metrics_dir: Path,
) -> None:
    """Pipeline/sovereignty metrics fan out across PIR + non-PIR
    playbooks; the exclusivity gate must keep them out of the cluster."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_pipeline_fanout",
        {
            "stable_id": "kpi.synthetic_pipeline_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.post_incident_review@v1"},
                {"playbook_id": "playbook.executive_metrics@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_playbook_refs_is_not_pir(
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
# Negative regression for each shipped PIR metric: removing its OCSF
# telemetry_ref MUST trip the assertion. This is the structural guard
# the card asks for.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "metric_filename",
    [
        "corrective_action_close_rate.yaml",
        "corrective_action_overdue.yaml",
        "review_completion_sla.yaml",
        "timeline_completeness.yaml",
    ],
)
def test_stripping_ocsf_ref_trips_assertion(
    metric_filename: str, tmp_path: Path
) -> None:
    src = REPO_ROOT / "content" / "metrics" / metric_filename
    doc = yaml.safe_load(src.read_text(encoding="utf-8"))
    doc["telemetry_refs"] = [
        r for r in (doc.get("telemetry_refs") or [])
        if not r.startswith("telemetry.ocsf.")
    ]
    dst_dir = tmp_path / "metrics"
    dst_dir.mkdir()
    (dst_dir / metric_filename).write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
    )
    findings = scan(dst_dir)
    assert len(findings) == 1, (
        f"stripping OCSF ref from {metric_filename} did not trip the "
        "post-incident-review-cluster assertion"
    )


# ---------------------------------------------------------------------------
# Helpers / CLI
# ---------------------------------------------------------------------------


def test_has_ocsf_binding_helper() -> None:
    assert has_ocsf_binding(["telemetry.ocsf.incident_finding@v1"])
    assert has_ocsf_binding(
        ["telemetry.internal.something@v1", "telemetry.ocsf.foo@v1"]
    )
    assert not has_ocsf_binding([])
    assert not has_ocsf_binding(["telemetry.internal.something@v1"])


def test_is_post_incident_review_metric_helper() -> None:
    assert is_post_incident_review_metric(
        ["playbook.post_incident_review@v1"]
    )
    assert not is_post_incident_review_metric([])
    assert not is_post_incident_review_metric(
        [
            "playbook.post_incident_review@v1",
            "playbook.executive_metrics@v1",
        ]
    )


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_post_incident_review_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "post-incident-review-ocsf-bindings: PASS" in proc.stdout


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
                {"playbook_id": "playbook.post_incident_review@v1"}
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
                {"playbook_id": "playbook.post_incident_review@v1"}
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
    assert payload["post_incident_review_cluster"] == sorted(
        POST_INCIDENT_REVIEW_PLAYBOOK_IDS
    )
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.synthetic_unbound@v1"
    )
