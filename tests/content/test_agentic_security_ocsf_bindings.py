"""Tests for the agentic-security-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension for the
agentic-security KPI/KRI triad shipped in F-MET-AGENTICSEC SKELETON
(PR #747): every metric whose ``stable_id`` is in the agentic-security
allow-list must declare at least one ``telemetry.ocsf.*`` ref.

Coverage mirrors ``test_availability_ocsf_bindings.py`` (this cluster
also classifies by ``stable_id`` allow-list, not ``playbook_refs``):

* the shipped tree passes (every agentic-security metric on main is
  bound to at least one OCSF source-data shape);
* the classifier identifies the three triad anchors from the SKELETON
  PR (structural anchor against silent no-op degradation);
* per-metric structural checks: each carries the required core fields
  (definition/summary, unit, formula, playbook_refs, foundation_property)
  and the non-empty thresholds + viz reference the triad card calls out;
* playbook_refs resolve to the shipped agentic_threat_response
  playbook directory;
* a synthetic agentic-security-cluster metric missing its OCSF ref is
  caught;
* metrics whose ``stable_id`` is outside the allow-list (including
  the sibling ``kpi.mttd_agentic_threat@v1`` /
  ``kpi.mttc_agentic_threat@v1`` that share the same playbook_ref) are
  correctly excluded;
* stripping the OCSF ref from any shipped triad metric trips the
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

from tools.lint_agentic_security_ocsf_bindings import (
    AGENTIC_SECURITY_STABLE_IDS,
    has_ocsf_binding,
    is_agentic_security_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTIC_PLAYBOOK_DIR = (
    REPO_ROOT / "content" / "playbooks" / "agentic_threat_response"
)


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_agentic_security_metrics() -> None:
    """Every agentic-security triad metric on main must carry OCSF."""
    findings = scan()
    assert findings == [], (
        "shipped agentic-security cluster has metrics without an OCSF "
        "source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_covers_agentic_security_anchors() -> None:
    """Sanity check: the scan classifies the three F-MET-AGENTICSEC
    SKELETON triad anchors as cluster-class.

    Without this anchor the assertion could silently degrade to a
    no-op (zero findings because zero metrics classify) and pass for
    the wrong reason.
    """
    classified: set[str] = set()
    for path in sorted((REPO_ROOT / "content" / "metrics").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        sid = doc.get("stable_id")
        if is_agentic_security_metric(sid):
            classified.add(sid)
    expected = {
        "kpi.agentic_threat_detection_rate@v1",
        "kri.agentic_model_decision_latency_seconds@v1",
        "kri.agentic_false_positive_rate@v1",
    }
    missing = expected - classified
    assert not missing, (
        "Agentic-security-cluster classifier no longer identifies the "
        f"anchor metrics — missing={sorted(missing)} "
        f"(classified={sorted(classified)})."
    )


# ---------------------------------------------------------------------------
# Per-metric structural checks: required catalog fields, non-empty
# thresholds + viz reference (SKELETON acceptance calls the triad's
# threshold/viz surface out explicitly), playbook_refs resolving to
# the shipped agentic_threat_response playbook directory.
# ---------------------------------------------------------------------------


AGENTIC_SECURITY_METRIC_FILES = (
    "agentic_threat_detection_rate",
    "agentic_model_decision_latency_seconds",
    "agentic_false_positive_rate",
)


@pytest.mark.parametrize("metric_name", AGENTIC_SECURITY_METRIC_FILES)
def test_triad_metric_has_required_catalog_fields(metric_name: str) -> None:
    """Every triad entry declares the catalog-schema core fields.

    The schema-level lint lives in ``test_metrics_schema.py``; this
    check is the cluster-scoped structural guard so a regression on
    any single triad member surfaces on this cluster's CI lane too.
    """
    src = REPO_ROOT / "content" / "metrics" / f"{metric_name}.yaml"
    doc = yaml.safe_load(src.read_text(encoding="utf-8"))
    # definition text — the canonical field name in this catalog is
    # ``summary`` (the seed exemplar mttd.yaml uses it); tolerate an
    # older ``definition`` alias too so a future rename doesn't
    # silently break this guard.
    assert doc.get("summary") or doc.get("definition"), (
        f"{metric_name}.yaml missing summary/definition prose"
    )
    assert isinstance(doc.get("unit"), str) and doc["unit"], (
        f"{metric_name}.yaml missing unit"
    )
    measurement = doc.get("measurement") or {}
    assert isinstance(measurement.get("formula"), str) and measurement[
        "formula"
    ].strip(), f"{metric_name}.yaml missing measurement.formula"
    assert doc.get("playbook_refs"), (
        f"{metric_name}.yaml missing playbook_refs"
    )
    telemetry_refs = doc.get("telemetry_refs") or []
    assert any(
        isinstance(r, str) and r.startswith("telemetry.ocsf.")
        for r in telemetry_refs
    ), f"{metric_name}.yaml missing telemetry.ocsf.* ref"
    foundation_property = doc.get("foundation_property")
    assert (
        isinstance(foundation_property, list) and foundation_property
    ), f"{metric_name}.yaml missing foundation_property"


@pytest.mark.parametrize("metric_name", AGENTIC_SECURITY_METRIC_FILES)
def test_triad_metric_has_non_empty_thresholds(metric_name: str) -> None:
    """The card calls thresholds out explicitly — every triad member
    ships at least one threshold band."""
    src = REPO_ROOT / "content" / "metrics" / f"{metric_name}.yaml"
    doc = yaml.safe_load(src.read_text(encoding="utf-8"))
    thresholds = doc.get("thresholds") or []
    assert thresholds, f"{metric_name}.yaml has no thresholds declared"


@pytest.mark.parametrize("metric_name", AGENTIC_SECURITY_METRIC_FILES)
def test_triad_metric_has_committed_viz_reference(metric_name: str) -> None:
    """The card calls the viz reference out explicitly — every triad
    member ships a committed ``<metric>.viz.md`` next to its YAML,
    and the metric's measurement.formula points at it."""
    viz_path = (
        REPO_ROOT / "content" / "metrics" / f"{metric_name}.viz.md"
    )
    assert viz_path.exists(), (
        f"{metric_name}.viz.md missing next to the YAML entry"
    )
    src = REPO_ROOT / "content" / "metrics" / f"{metric_name}.yaml"
    doc = yaml.safe_load(src.read_text(encoding="utf-8"))
    formula = ((doc.get("measurement") or {}).get("formula") or "")
    assert f"{metric_name}.viz.md" in formula, (
        f"{metric_name}.yaml measurement.formula does not reference "
        f"the committed viz rendering {metric_name}.viz.md"
    )


@pytest.mark.parametrize("metric_name", AGENTIC_SECURITY_METRIC_FILES)
def test_triad_playbook_refs_resolve_to_agentic_threat_response(
    metric_name: str,
) -> None:
    """Every triad entry's ``playbook_refs`` names the shipped
    ``agentic_threat_response`` playbook, and the referenced playbook
    directory exists under ``content/playbooks/`` with its CACAO
    payload committed."""
    src = REPO_ROOT / "content" / "metrics" / f"{metric_name}.yaml"
    doc = yaml.safe_load(src.read_text(encoding="utf-8"))
    playbook_refs = doc.get("playbook_refs") or []
    assert playbook_refs, (
        f"{metric_name}.yaml missing playbook_refs"
    )
    ids = {
        ref.get("playbook_id")
        for ref in playbook_refs
        if isinstance(ref, dict)
    }
    assert "playbook.agentic_threat_response@v1" in ids, (
        f"{metric_name}.yaml playbook_refs must include "
        f"playbook.agentic_threat_response@v1 (got {sorted(i for i in ids if i)})"
    )
    assert AGENTIC_PLAYBOOK_DIR.is_dir(), (
        f"content/playbooks/agentic_threat_response/ missing on tree"
    )
    assert (AGENTIC_PLAYBOOK_DIR / "playbook.cacao.json").exists(), (
        "agentic_threat_response playbook directory has no "
        "playbook.cacao.json — playbook_refs would point at an "
        "unshipped chain"
    )


# ---------------------------------------------------------------------------
# Synthetic positive: agentic-security-cluster metric missing OCSF binding
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


def test_agentic_security_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "agentic_threat_detection_rate",
        {
            "stable_id": "kpi.agentic_threat_detection_rate@v1",
            "kind": "kpi",
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id
        == "kpi.agentic_threat_detection_rate@v1"
    )


def test_agentic_security_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "agentic_threat_detection_rate",
        {
            "stable_id": "kpi.agentic_threat_detection_rate@v1",
            "kind": "kpi",
            "telemetry_refs": ["telemetry.ocsf.detection_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_out_of_allowlist_stable_id_is_not_agentic_security(
    synthetic_metrics_dir: Path,
) -> None:
    """Metrics whose ``stable_id`` is outside the triad allow-list
    must be excluded — even the sibling MTTD/MTTC agentic metrics
    that share the same ``agentic_threat_response`` playbook_ref."""
    _write_metric(
        synthetic_metrics_dir,
        "mttd_agentic_threat",
        {
            "stable_id": "kpi.mttd_agentic_threat@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.agentic_threat_response@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_stable_id_is_not_agentic_security(
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
# Negative regression for every triad metric:
# stripping its OCSF telemetry_refs MUST trip the assertion.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("metric_name", AGENTIC_SECURITY_METRIC_FILES)
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
        "agentic-security cluster is supposed to leave every metric "
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
        "the agentic-security-cluster assertion "
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


def test_is_agentic_security_metric_helper() -> None:
    assert is_agentic_security_metric("kpi.agentic_threat_detection_rate@v1")
    assert is_agentic_security_metric(
        "kri.agentic_model_decision_latency_seconds@v1"
    )
    assert is_agentic_security_metric("kri.agentic_false_positive_rate@v1")
    assert not is_agentic_security_metric(None)
    assert not is_agentic_security_metric("")
    # sibling metric sharing the playbook_ref is deliberately excluded
    assert not is_agentic_security_metric("kpi.mttd_agentic_threat@v1")
    assert not is_agentic_security_metric("kpi.mttc_agentic_threat@v1")


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_agentic_security_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "agentic-security-ocsf-bindings: PASS" in proc.stdout


def test_cli_fails_with_synthetic_unbound(tmp_path: Path) -> None:
    d = tmp_path / "metrics"
    d.mkdir()
    _write_metric(
        d,
        "agentic_threat_detection_rate",
        {
            "stable_id": "kpi.agentic_threat_detection_rate@v1",
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
        "agentic_threat_detection_rate",
        {
            "stable_id": "kpi.agentic_threat_detection_rate@v1",
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
    assert payload["agentic_security_cluster"] == sorted(
        AGENTIC_SECURITY_STABLE_IDS
    )
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.agentic_threat_detection_rate@v1"
    )
