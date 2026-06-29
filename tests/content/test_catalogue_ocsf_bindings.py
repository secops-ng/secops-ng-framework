"""Tests for the catalogue-wide OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension at the catalogue
floor: every metric whose ``measurement.source`` is an
operator-telemetry source (i.e. anything other than ``composite``)
must declare at least one ``telemetry.ocsf.*`` ref. Composite metrics
are exempt — they are computed from the project's own CI / governance
signal, not from operator OCSF telemetry.

Coverage mirrors the per-cluster sibling tests
(``test_posture_ocsf_bindings.py`` / ``test_detection_ocsf_bindings.py``):

* the shipped tree passes clean today (every operator-telemetry
  metric on main already carries OCSF);
* a synthetic operator-telemetry metric without OCSF is caught;
* a synthetic composite metric without OCSF is correctly exempted;
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

from tools.lint_catalogue_ocsf_bindings import (
    COMPOSITE_SOURCE,
    DEFAULT_TELEMETRY_DIR,
    REASON_DANGLING_REF,
    REASON_NO_BINDING,
    is_operator_telemetry_source,
    main,
    resolve_ocsf_ref,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_operator_metrics() -> None:
    """Every operator-telemetry metric on main must carry OCSF."""
    findings = scan()
    assert findings == [], (
        "shipped catalogue has operator-telemetry metric(s) without an "
        "OCSF source-data-shape binding: "
        + ", ".join(
            f"{f.metric_stable_id} (source={f.measurement_source})"
            for f in findings
        )
    )


def test_real_tree_classifies_operator_and_composite() -> None:
    """Sanity check: the shipped tree contains BOTH non-empty sets —
    operator-telemetry metrics that the guard covers, and composite
    metrics that the exemption covers. Without both, the assertion
    could silently degrade and pass for the wrong reason.
    """
    operator_metrics: set[str] = set()
    composite_metrics: set[str] = set()
    for path in sorted((REPO_ROOT / "content" / "metrics").glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        src = ((doc.get("measurement") or {}).get("source")) or ""
        sid = doc.get("stable_id")
        if not isinstance(sid, str):
            continue
        if src == COMPOSITE_SOURCE:
            composite_metrics.add(sid)
        elif src:
            operator_metrics.add(sid)
    assert operator_metrics, (
        "catalogue has no operator-telemetry metrics — the catalogue-"
        "wide OCSF guard would silently no-op."
    )
    assert composite_metrics, (
        "catalogue has no composite metrics — the exemption path is "
        "untested by the shipped tree."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: operator-telemetry metric missing OCSF binding
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


def test_operator_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_operator",
        {
            "stable_id": "kpi.synthetic_unbound_operator@v1",
            "kind": "kpi",
            "measurement": {"source": "siem_event_stream"},
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    f = findings[0]
    assert f.metric_stable_id == "kpi.synthetic_unbound_operator@v1"
    assert f.measurement_source == "siem_event_stream"


def test_operator_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_bound_operator",
        {
            "stable_id": "kpi.synthetic_bound_operator@v1",
            "kind": "kpi",
            "measurement": {"source": "siem_event_stream"},
            "telemetry_refs": ["telemetry.ocsf.detection_finding@v1"],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_composite_metric_without_ocsf_ref_is_exempt(
    synthetic_metrics_dir: Path,
) -> None:
    """Composite metrics are computed from internal CI signal — they
    must NOT be required to carry an OCSF source-data shape."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_composite_governance",
        {
            "stable_id": "kpi.synthetic_composite_governance@v1",
            "kind": "kpi",
            "measurement": {"source": COMPOSITE_SOURCE},
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_operator_metric_with_only_non_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    """A non-OCSF telemetry_ref is not enough — the catalogue floor
    requires an OCSF source-data shape specifically."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_only_internal_ref",
        {
            "stable_id": "kpi.synthetic_only_internal_ref@v1",
            "kind": "kpi",
            "measurement": {"source": "siem_event_stream"},
            "telemetry_refs": ["telemetry.internal.something@v1"],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert findings[0].metric_stable_id == "kpi.synthetic_only_internal_ref@v1"


# ---------------------------------------------------------------------------
# CORE: OCSF ref resolution against content/telemetry/
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_telemetry_dir(tmp_path: Path) -> Path:
    d = tmp_path / "telemetry"
    d.mkdir()
    return d


def _write_ocsf_class(directory: Path, ref: str) -> Path:
    """Write a minimal OCSF class artifact under ``directory`` named
    ``<ref>.json`` — matches the shipped content/telemetry/ convention.
    """
    path = directory / f"{ref}.json"
    path.write_text(json.dumps({"stable_id": ref}), encoding="utf-8")
    return path


def test_operator_metric_with_resolving_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
    synthetic_telemetry_dir: Path,
) -> None:
    """CORE: a metric whose OCSF telemetry_ref resolves to a real
    artifact under content/telemetry/ passes the catalogue guard.
    """
    ref = "telemetry.ocsf.synthetic_resolves@v1"
    _write_ocsf_class(synthetic_telemetry_dir, ref)
    _write_metric(
        synthetic_metrics_dir,
        "metric_resolving",
        {
            "stable_id": "kpi.metric_resolving@v1",
            "kind": "kpi",
            "measurement": {"source": "siem_event_stream"},
            "telemetry_refs": [ref],
        },
    )
    assert scan(synthetic_metrics_dir, synthetic_telemetry_dir) == []


def test_operator_metric_with_dangling_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
    synthetic_telemetry_dir: Path,
) -> None:
    """CORE: a present-but-dangling OCSF telemetry_ref — declared on
    the metric but with no matching artifact under
    content/telemetry/ — fails. This is the gap the SKELETON missed:
    presence alone is not enough.
    """
    ref = "telemetry.ocsf.no_such_class@v1"
    # Intentionally do NOT write a backing artifact for ``ref``.
    _write_metric(
        synthetic_metrics_dir,
        "metric_dangling",
        {
            "stable_id": "kpi.metric_dangling@v1",
            "kind": "kpi",
            "measurement": {"source": "siem_event_stream"},
            "telemetry_refs": [ref],
        },
    )
    findings = scan(synthetic_metrics_dir, synthetic_telemetry_dir)
    assert len(findings) == 1
    f = findings[0]
    assert f.metric_stable_id == "kpi.metric_dangling@v1"
    assert f.reason == REASON_DANGLING_REF
    assert f.unresolved_refs == (ref,)


def test_operator_metric_with_partial_resolution_is_flagged(
    synthetic_metrics_dir: Path,
    synthetic_telemetry_dir: Path,
) -> None:
    """A metric declaring multiple OCSF refs fails if ANY of them is
    dangling — the catalogue floor is per-ref, not per-metric."""
    good_ref = "telemetry.ocsf.synthetic_good@v1"
    bad_ref = "telemetry.ocsf.synthetic_missing@v1"
    _write_ocsf_class(synthetic_telemetry_dir, good_ref)
    _write_metric(
        synthetic_metrics_dir,
        "metric_partial",
        {
            "stable_id": "kpi.metric_partial@v1",
            "kind": "kpi",
            "measurement": {"source": "siem_event_stream"},
            "telemetry_refs": [good_ref, bad_ref],
        },
    )
    findings = scan(synthetic_metrics_dir, synthetic_telemetry_dir)
    assert len(findings) == 1
    assert findings[0].reason == REASON_DANGLING_REF
    assert findings[0].unresolved_refs == (bad_ref,)


def test_resolve_ocsf_ref_helper(tmp_path: Path) -> None:
    d = tmp_path / "telemetry"
    d.mkdir()
    _write_ocsf_class(d, "telemetry.ocsf.exists@v1")
    assert resolve_ocsf_ref("telemetry.ocsf.exists@v1", d)
    assert not resolve_ocsf_ref("telemetry.ocsf.missing@v1", d)
    # Non-OCSF refs are not OCSF — helper returns False so callers
    # can rely on it without pre-filtering by prefix.
    assert not resolve_ocsf_ref("telemetry.internal.something@v1", d)


def test_shipped_tree_ocsf_refs_all_resolve() -> None:
    """The shipped tree must already satisfy the CORE bar: every
    bound metric's OCSF ref resolves under content/telemetry/."""
    findings = scan()
    assert findings == [], (
        "shipped catalogue has unresolved OCSF refs: "
        + ", ".join(
            f"{f.metric_stable_id} ({f.reason}: {list(f.unresolved_refs)})"
            for f in findings
        )
    )


# ---------------------------------------------------------------------------
# Helper unit coverage
# ---------------------------------------------------------------------------


def test_is_operator_telemetry_source_helper() -> None:
    assert is_operator_telemetry_source("siem_event_stream")
    assert is_operator_telemetry_source("posture_evidence_pull")
    assert not is_operator_telemetry_source(COMPOSITE_SOURCE)
    assert not is_operator_telemetry_source("")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_catalogue_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "catalogue-ocsf-bindings: PASS" in proc.stdout


def test_cli_fails_with_synthetic_unbound(tmp_path: Path) -> None:
    d = tmp_path / "metrics"
    d.mkdir()
    _write_metric(
        d,
        "synthetic_unbound",
        {
            "stable_id": "kpi.synthetic_unbound@v1",
            "kind": "kpi",
            "measurement": {"source": "siem_event_stream"},
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
            "measurement": {"source": "siem_event_stream"},
            "telemetry_refs": [],
        },
    )
    rc = main(["--format", "json", "--metrics-dir", str(d)])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 1
    assert payload["status"] == "fail"
    assert payload["finding_count"] == 1
    assert payload["exempt_source"] == COMPOSITE_SOURCE
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.synthetic_unbound@v1"
    )
    assert (
        payload["findings"][0]["measurement_source"] == "siem_event_stream"
    )
