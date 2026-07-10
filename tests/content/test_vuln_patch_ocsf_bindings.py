"""Tests for the vulnerability-handling-&-patch-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension for the
vulnerability-handling & patch (CRA-family) metric family: every
metric whose ``playbook_refs`` resolve exclusively to the vuln-&-patch
cluster must declare at least one ``telemetry.ocsf.*`` ref.

Coverage mirrors ``test_identity_access_ocsf_bindings.py``:

* the shipped tree passes (every vuln-&-patch metric on main is bound
  to at least one OCSF source-data shape);
* the classifier identifies the full six-metric cluster (structural
  anchor against silent no-op degradation);
* a synthetic vuln-&-patch-cluster metric missing its OCSF ref is
  caught;
* fan-out pipeline / regnotify metrics that span vuln + other
  playbooks are correctly excluded from the cluster gate;
* stripping the OCSF ref from any shipped vuln/patch metric trips the
  assertion (per-metric structural guard);
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

from tools.lint_vuln_patch_ocsf_bindings import (
    VULN_PATCH_PLAYBOOK_IDS,
    has_ocsf_binding,
    is_vuln_patch_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_vuln_patch_metrics() -> None:
    """Every vuln-&-patch-cluster metric on main must carry OCSF."""
    findings = scan()
    assert findings == [], (
        "shipped vulnerability-&-patch cluster has metrics without an "
        "OCSF source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_full_vuln_patch_cluster() -> None:
    """Sanity check: the scan classifies every shipped vuln-&-patch
    metric as cluster-class.

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
        if is_vuln_patch_metric(pb):
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                classified.add(sid)
    expected = {
        "kri.cvd_intake_aging@v1",
        "kpi.vuln_disclosure_sla@v1",
        "kri.releases_without_sbom@v1",
        "kpi.patch_disseminated_on_time@v1",
        "kpi.patch_rollout_success_rate@v1",
        "kri.patch_rollout_overdue_exposure@v1",
        # F-MET-G04-VULNMGMT SKELETON / CORE — vulnerability-management
        # KPI/KRI triad (NIS2 Art. 21(2)(e), DORA JC RTS Art. 10). All
        # three pin their host chain through
        # playbook.vulnerability_management@v1, so they classify into
        # this cluster and must stay OCSF-bound to the Vulnerability
        # Finding (2002) source-data shape.
        "kri.unpatched_critical_cve_age_days@v1",
        "kri.vuln_critical_open_age_p99@v1",
        "kpi.vuln_remediation_sla_compliance@v1",
    }
    missing = expected - classified
    assert not missing, (
        "vulnerability-&-patch-cluster classifier no longer identifies "
        f"the full metric set — missing={sorted(missing)} "
        f"(classified={sorted(classified)})."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: vuln-&-patch-cluster metric missing OCSF binding
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


def test_vuln_intake_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_vuln",
        {
            "stable_id": "kpi.synthetic_unbound_vuln@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.vuln_intake@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id
        == "kpi.synthetic_unbound_vuln@v1"
    )


def test_vuln_intake_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_bound_vuln",
        {
            "stable_id": "kpi.synthetic_bound_vuln@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.vuln_intake@v1"}
            ],
            "telemetry_refs": ["telemetry.ocsf.vulnerability_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_patch_management_metric_without_ocsf_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    """The other member of the cluster — the patch_management playbook
    — is gated the same way."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_patch",
        {
            "stable_id": "kri.synthetic_unbound_patch@v1",
            "kind": "kri",
            "playbook_refs": [
                {"playbook_id": "playbook.patch_management@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].metric_stable_id == "kri.synthetic_unbound_patch@v1"


def test_fanout_regnotify_metric_is_not_vuln_patch(
    synthetic_metrics_dir: Path,
) -> None:
    """Regnotify / pipeline metrics fan out across vuln + non-vuln
    playbooks; the exclusivity gate must keep them out. Explicitly
    guards against pulling in regulator_notification_overrun or
    breach_notification_clock_margin style metrics."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_regnotify_fanout",
        {
            "stable_id": "kpi.synthetic_regnotify_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.vuln_intake@v1"},
                {"playbook_id": "playbook.regulator_notification@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_playbook_refs_is_not_vuln_patch(
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
# Negative regression for every vuln-&-patch metric in the cluster:
# stripping its OCSF telemetry_refs MUST trip the assertion.
# Per-metric coverage so a regression on any single binding surfaces.
# ---------------------------------------------------------------------------


VULN_PATCH_METRICS = (
    "cvd_intake_aging",
    "vuln_disclosure_sla",
    "releases_without_sbom",
    "patch_disseminated_on_time",
    "patch_rollout_success_rate",
    "patch_rollout_overdue_exposure",
    # F-MET-G04-VULNMGMT SKELETON / CORE — vulnerability-management
    # KPI/KRI triad. Guard the OCSF binding on each catalogue entry
    # independently so a silent detach on any one file surfaces.
    "unpatched_critical_cve_age_days",
    "vuln_critical_open_age_p99",
    "vuln_remediation_sla_compliance",
)


@pytest.mark.parametrize("metric_name", VULN_PATCH_METRICS)
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
        "vulnerability-&-patch cluster is supposed to leave every "
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
        "the vulnerability-&-patch-cluster assertion "
        f"(findings={[f.metric_stable_id for f in findings]})"
    )
    assert findings[0].metric_stable_id == doc.get("stable_id")


# ---------------------------------------------------------------------------
# Helpers / CLI
# ---------------------------------------------------------------------------


def test_has_ocsf_binding_helper() -> None:
    assert has_ocsf_binding(["telemetry.ocsf.vulnerability_finding@v1"])
    assert has_ocsf_binding(
        ["telemetry.internal.something@v1", "telemetry.ocsf.patch_state@v1"]
    )
    assert not has_ocsf_binding([])
    assert not has_ocsf_binding(["telemetry.internal.something@v1"])


def test_is_vuln_patch_metric_helper() -> None:
    assert is_vuln_patch_metric(["playbook.vuln_intake@v1"])
    assert is_vuln_patch_metric(["playbook.patch_management@v1"])
    assert is_vuln_patch_metric(["playbook.vulnerability_management@v1"])
    assert is_vuln_patch_metric(
        [
            "playbook.vuln_intake@v1",
            "playbook.patch_management@v1",
            "playbook.vulnerability_management@v1",
        ]
    )
    assert not is_vuln_patch_metric([])
    assert not is_vuln_patch_metric(
        [
            "playbook.vuln_intake@v1",
            "playbook.regulator_notification@v1",
        ]
    )
    assert not is_vuln_patch_metric(["playbook.identity_compromise@v1"])


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_vuln_patch_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "vuln-patch-ocsf-bindings: PASS" in proc.stdout


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
                {"playbook_id": "playbook.vuln_intake@v1"}
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
                {"playbook_id": "playbook.vuln_intake@v1"}
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
    assert payload["vuln_patch_cluster"] == sorted(
        VULN_PATCH_PLAYBOOK_IDS
    )
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.synthetic_unbound@v1"
    )
