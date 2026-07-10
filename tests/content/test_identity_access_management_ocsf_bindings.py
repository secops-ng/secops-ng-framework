"""Tests for the identity/access-management-cluster OCSF binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension for the identity/
access-management KPI/KRI pair shipped in F-MET-G04-IDENTITYACCESS
SKELETON (NIS2 Art. 21(2)(i)/(j), GDPR Art. 32(1)(a), ISO/IEC 27001
Annex A.5.18/A.8.2): every metric whose ``stable_id`` is in the
identity/access-management allow-list must declare at least one
``telemetry.ocsf.*`` ref.

Coverage mirrors ``test_availability_ocsf_bindings.py`` (this cluster
also classifies by ``stable_id`` allow-list, not ``playbook_refs``):

* the shipped tree passes (every identity/access-management metric on
  main is bound to at least one OCSF source-data shape);
* the classifier identifies the two anchor metrics from the SKELETON
  PR (structural anchor against silent no-op degradation);
* a synthetic identity/access-management-cluster metric missing its
  OCSF ref is caught;
* metrics whose ``stable_id`` is outside the allow-list are correctly
  excluded;
* stripping the OCSF ref from any shipped identity/access-management
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

from tools.lint_identity_access_management_ocsf_bindings import (
    IDENTITY_ACCESS_MANAGEMENT_STABLE_IDS,
    has_ocsf_binding,
    is_identity_access_management_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_identity_access_management_metrics() -> None:
    """Every identity/access-management-cluster metric on main must carry OCSF."""
    findings = scan()
    assert findings == [], (
        "shipped identity/access-management cluster has metrics "
        "without an OCSF source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_identity_access_management_anchors() -> None:
    """Sanity check: the scan classifies the two NIS2 Art. 21(2)(i)/(j)
    identity/access-management KPI/KRI anchors as cluster-class.

    Without this anchor the assertion could silently degrade to a
    no-op (zero findings because zero metrics classify) and pass for
    the wrong reason. Anchors on the two metrics shipped in
    F-MET-G04-IDENTITYACCESS SKELETON.
    """
    classified: set[str] = set()
    for path in sorted((REPO_ROOT / "content" / "metrics").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        sid = doc.get("stable_id")
        if is_identity_access_management_metric(sid):
            classified.add(sid)
    expected = {
        "kpi.identity_mfa_enforcement_rate@v1",
        "kri.access_review_completion_rate@v1",
    }
    missing = expected - classified
    assert not missing, (
        "Identity/access-management-cluster classifier no longer "
        f"identifies the anchor metrics — missing={sorted(missing)} "
        f"(classified={sorted(classified)})."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: cluster metric missing OCSF binding
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


def test_identity_access_management_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "identity_mfa_enforcement_rate",
        {
            "stable_id": "kpi.identity_mfa_enforcement_rate@v1",
            "kind": "kpi",
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id
        == "kpi.identity_mfa_enforcement_rate@v1"
    )


def test_identity_access_management_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "identity_mfa_enforcement_rate",
        {
            "stable_id": "kpi.identity_mfa_enforcement_rate@v1",
            "kind": "kpi",
            "telemetry_refs": ["telemetry.ocsf.authentication@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_out_of_allowlist_stable_id_is_not_identity_access_management(
    synthetic_metrics_dir: Path,
) -> None:
    """Metrics whose ``stable_id`` is not in the identity/access-
    management allow-list must be kept out — even if their file name
    is suggestive or they share a playbook_ref with the identity_
    compromise / onboarding_offboarding detection cluster."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_out_of_allowlist",
        {
            "stable_id": "kpi.some_other_iam_thing@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.identity_compromise@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_stable_id_is_not_identity_access_management(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_no_stable_id",
        {
            "kind": "kpi",
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


# ---------------------------------------------------------------------------
# Negative regression for every metric in the cluster:
# stripping its OCSF telemetry_refs MUST trip the assertion.
# Per-metric coverage so a regression on any single binding surfaces.
# ---------------------------------------------------------------------------


IDENTITY_ACCESS_MANAGEMENT_METRICS = (
    "identity_mfa_enforcement_rate",
    "access_review_completion_rate",
)


@pytest.mark.parametrize("metric_name", IDENTITY_ACCESS_MANAGEMENT_METRICS)
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
        "identity/access-management cluster is supposed to leave every "
        "metric bound; fix the metric file before this test can guard it."
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
        "the identity/access-management-cluster assertion "
        f"(findings={[f.metric_stable_id for f in findings]})"
    )
    assert findings[0].metric_stable_id == doc.get("stable_id")


# ---------------------------------------------------------------------------
# Helpers / CLI
# ---------------------------------------------------------------------------


def test_has_ocsf_binding_helper() -> None:
    assert has_ocsf_binding(["telemetry.ocsf.authentication@v1"])
    assert has_ocsf_binding(
        ["telemetry.internal.something@v1", "telemetry.ocsf.account_change@v1"]
    )
    assert not has_ocsf_binding([])
    assert not has_ocsf_binding(["telemetry.internal.something@v1"])


def test_is_identity_access_management_metric_helper() -> None:
    assert is_identity_access_management_metric(
        "kpi.identity_mfa_enforcement_rate@v1"
    )
    assert is_identity_access_management_metric(
        "kri.access_review_completion_rate@v1"
    )
    assert not is_identity_access_management_metric(None)
    assert not is_identity_access_management_metric("")
    assert not is_identity_access_management_metric(
        "kpi.some_other_iam_thing@v1"
    )
    assert not is_identity_access_management_metric(
        "kri.cra_early_warning_latency_hours@v1"
    )


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.lint_identity_access_management_ocsf_bindings",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "identity-access-management-ocsf-bindings: PASS" in proc.stdout


def test_cli_fails_with_synthetic_unbound(tmp_path: Path) -> None:
    d = tmp_path / "metrics"
    d.mkdir()
    _write_metric(
        d,
        "identity_mfa_enforcement_rate",
        {
            "stable_id": "kpi.identity_mfa_enforcement_rate@v1",
            "kind": "kpi",
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
        "identity_mfa_enforcement_rate",
        {
            "stable_id": "kpi.identity_mfa_enforcement_rate@v1",
            "kind": "kpi",
            "telemetry_refs": [],
        },
    )
    rc = main(["--format", "json", "--metrics-dir", str(d)])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 1
    assert payload["status"] == "fail"
    assert payload["finding_count"] == 1
    assert payload["identity_access_management_cluster"] == sorted(
        IDENTITY_ACCESS_MANAGEMENT_STABLE_IDS
    )
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.identity_mfa_enforcement_rate@v1"
    )
