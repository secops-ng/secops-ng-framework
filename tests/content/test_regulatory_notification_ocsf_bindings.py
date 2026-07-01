"""Tests for the regulatory-notification-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension: every metric
whose ``playbook_refs`` resolve exclusively to steps in the
regulatory-notification cluster must declare at least one
``telemetry.ocsf.*`` ref.

Coverage:

* the shipped tree passes (post-F-MET-OCSF-REGNOTIFY-SKELETON main has
  every CRA on-time metric bound to ``telemetry.ocsf.incident_finding@v1``);
* a synthetic regulatory-notification-class metric missing its OCSF
  ref is caught;
* fan-out metrics (regulator-notification step + non-cluster steps)
  are correctly excluded from the cluster gate;
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

from tools.lint_regulatory_notification_ocsf_bindings import (
    REGULATORY_NOTIFICATION_STEPS,
    has_ocsf_binding,
    is_regulatory_notification_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# The single anchor step wired by this SKELETON.
_REGNOTIFY_STEP = (
    "playbook.vuln_intake@v1",
    "action--01a17a01-0000-4000-8000-000000000006",
)


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_regnotify_metrics() -> None:
    """Every regulatory-notification-cluster metric on main must carry an OCSF ref."""
    findings = scan()
    assert findings == [], (
        "shipped regulatory-notification cluster has metrics without an "
        "OCSF source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_cra_notification_72h_anchor() -> None:
    """Sanity anchor: the scan actually classifies
    ``kpi.cra_notification_72h_on_time@v1`` as regulatory-notification-class.

    Without this anchor the assertion could silently degrade to a
    no-op (zero findings because zero metrics classify) and pass for
    the wrong reason.
    """
    anchor_sid = "kpi.cra_notification_72h_on_time@v1"
    src = REPO_ROOT / "content" / "metrics" / "cra_notification_72h_on_time.yaml"
    doc = yaml.safe_load(src.read_text(encoding="utf-8"))
    tuples = tuple(
        (r["playbook_id"], r["step_id"])
        for r in (doc.get("playbook_refs") or [])
        if isinstance(r, dict)
        and isinstance(r.get("playbook_id"), str)
        and isinstance(r.get("step_id"), str)
    )
    assert doc.get("stable_id") == anchor_sid
    assert is_regulatory_notification_metric(tuples), (
        "regulatory-notification classifier no longer identifies the "
        "CRA 72h on-time anchor — adjust REGULATORY_NOTIFICATION_STEPS "
        "or the test."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: regnotify-class metric missing OCSF binding
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


def test_regnotify_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_regnotify",
        {
            "stable_id": "kpi.synthetic_unbound_regnotify@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": _REGNOTIFY_STEP[0], "step_id": _REGNOTIFY_STEP[1]},
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].metric_stable_id == "kpi.synthetic_unbound_regnotify@v1"


def test_regnotify_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_bound_regnotify",
        {
            "stable_id": "kpi.synthetic_bound_regnotify@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": _REGNOTIFY_STEP[0], "step_id": _REGNOTIFY_STEP[1]},
            ],
            "telemetry_refs": ["telemetry.ocsf.incident_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_fanout_step_metric_is_not_regnotify(
    synthetic_metrics_dir: Path,
) -> None:
    """Metrics that touch the regulator-notification step alongside
    other steps of the same playbook (e.g. vuln disclosure intake)
    must be excluded from the cluster by the step-scoped gate."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_fanout_intake_plus_notify",
        {
            "stable_id": "kpi.synthetic_fanout_intake_plus_notify@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": _REGNOTIFY_STEP[0], "step_id": _REGNOTIFY_STEP[1]},
                {
                    "playbook_id": "playbook.vuln_intake@v1",
                    "step_id": "action--01a17a01-0000-4000-8000-000000000002",
                },
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_non_notification_step_metric_is_not_regnotify(
    synthetic_metrics_dir: Path,
) -> None:
    """A metric bound to a vuln_intake step other than the regulator-
    notification step (e.g. CVD intake) must not classify — its
    source-data shape is covered by a different cluster lint."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_cvd_intake_only",
        {
            "stable_id": "kpi.synthetic_cvd_intake_only@v1",
            "kind": "kpi",
            "playbook_refs": [
                {
                    "playbook_id": "playbook.vuln_intake@v1",
                    "step_id": "action--01a17a01-0000-4000-8000-000000000002",
                },
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_playbook_refs_is_not_regnotify(
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
# Negative regression for each shipped CRA on-time metric: removing
# its OCSF telemetry_ref MUST trip the assertion. This is the
# structural guard the SKELETON is armed against.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "metric_filename",
    [
        "cra_early_warning_on_time.yaml",
        "cra_notification_72h_on_time.yaml",
        "cra_severe_incident_on_time.yaml",
        "cra_final_report_on_time.yaml",
    ],
)
def test_stripping_ocsf_ref_trips_assertion(
    metric_filename: str, tmp_path: Path
) -> None:
    src = REPO_ROOT / "content" / "metrics" / metric_filename
    doc = yaml.safe_load(src.read_text(encoding="utf-8"))
    doc["telemetry_refs"] = [
        r
        for r in (doc.get("telemetry_refs") or [])
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
        "regulatory-notification-cluster assertion"
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


def test_is_regulatory_notification_metric_helper() -> None:
    assert is_regulatory_notification_metric([_REGNOTIFY_STEP])
    assert not is_regulatory_notification_metric([])
    # Fan-out: cluster step + non-cluster step on the same playbook.
    assert not is_regulatory_notification_metric(
        [
            _REGNOTIFY_STEP,
            (
                "playbook.vuln_intake@v1",
                "action--01a17a01-0000-4000-8000-000000000002",
            ),
        ]
    )
    # Non-cluster step alone.
    assert not is_regulatory_notification_metric(
        [
            (
                "playbook.vuln_intake@v1",
                "action--01a17a01-0000-4000-8000-000000000002",
            )
        ]
    )


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.lint_regulatory_notification_ocsf_bindings",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "regulatory-notification-ocsf-bindings: PASS" in proc.stdout


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
                {"playbook_id": _REGNOTIFY_STEP[0], "step_id": _REGNOTIFY_STEP[1]},
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
                {"playbook_id": _REGNOTIFY_STEP[0], "step_id": _REGNOTIFY_STEP[1]},
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
    assert payload["regulatory_notification_cluster"] == [
        {"playbook_id": pid, "step_id": sid}
        for pid, sid in sorted(REGULATORY_NOTIFICATION_STEPS)
    ]
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.synthetic_unbound@v1"
    )
