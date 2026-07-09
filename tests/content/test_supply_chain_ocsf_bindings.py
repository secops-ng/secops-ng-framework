"""Tests for the supply-chain-security-cluster OCSF source-data-shape binding assertion.

Defends the G-04 catalogue-maturity OCSF dimension for the
supply-chain-security metric family: every metric whose
``playbook_refs`` resolve exclusively to the supply-chain-security
cluster must declare at least one ``telemetry.ocsf.*`` ref.

SKELETON note: the supply-chain-security cluster on main currently
has **zero** exclusive-membership metrics — every metric that
references ``playbook.supply_chain_security@v1`` today is a fan-out
across pipeline / executive-catch-all playbooks, so the exclusivity
gate correctly keeps them out. The shipped-tree assertion therefore
passes trivially and the classifier is expected to return an empty
set on main. Coverage relies on synthetic fixtures to arm the lint:

* the shipped tree passes (zero classified metrics, zero findings);
* the classifier correctly returns empty on main (baseline anchor,
  updated by F-MET-OCSF-SUPPLYCHAIN CORE once real bindings land);
* a synthetic supply-chain-cluster metric missing its OCSF ref is
  caught;
* fan-out metrics that span supply-chain + pipeline / executive
  catch-all playbooks (the exact shape of the current orphans) are
  correctly excluded from the cluster gate;
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

from tools.lint_supply_chain_ocsf_bindings import (
    SUPPLY_CHAIN_PLAYBOOK_IDS,
    has_ocsf_binding,
    is_supply_chain_metric,
    main,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Real-tree pass case
# ---------------------------------------------------------------------------


def test_shipped_tree_has_no_unbound_supply_chain_metrics() -> None:
    """Every supply-chain-cluster metric on main must carry OCSF.

    On SKELETON there are zero exclusive-membership metrics, so this
    passes trivially with an empty findings list. CORE lands real
    bindings + wires the lane into nightly orphan-CI.
    """
    findings = scan()
    assert findings == [], (
        "shipped supply-chain-security cluster has metrics without an "
        "OCSF source-data-shape binding: "
        + ", ".join(f.metric_stable_id for f in findings)
    )


def test_real_tree_supply_chain_classification_baseline() -> None:
    """Baseline anchor for the supply-chain-cluster classifier.

    F-WF-SCS EXTEND-metrics landed two exclusive-membership metrics
    that reference only ``playbook.supply_chain_security@v1``:

    * ``kri.supplier_attestation_staleness@v1``
    * ``kpi.supply_chain_coverage@v1``

    Both carry a ``telemetry.ocsf.api_activity@v1`` binding so the
    real-tree pass case above still returns zero findings. Any
    future exclusive-membership metric added to the cluster must be
    added here explicitly and confirmed to carry a ``telemetry.ocsf.*``
    ref — treating the silent transition as a bug prevents no-op
    degradation.
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
        if is_supply_chain_metric(pb):
            sid = doc.get("stable_id")
            if isinstance(sid, str):
                classified.add(sid)
    expected = {
        "kri.supplier_attestation_staleness@v1",
        "kpi.supply_chain_coverage@v1",
        "kri.supplier_attestation_overdue_ratio@v1",
        "kpi.supply_chain_audit_coverage@v1",
    }
    assert classified == expected, (
        "supply-chain-security-cluster classifier drift: "
        f"classified={sorted(classified)} expected={sorted(expected)}. "
        "Update this baseline to the expected set and confirm every "
        "listed metric carries a telemetry.ocsf.* binding."
    )


# ---------------------------------------------------------------------------
# Synthetic positive: supply-chain-cluster metric missing OCSF binding
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


def test_supply_chain_metric_without_ocsf_ref_is_flagged(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_unbound_supply_chain",
        {
            "stable_id": "kpi.synthetic_unbound_supply_chain@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.supply_chain_security@v1"}
            ],
            "telemetry_refs": [],
        },
    )
    findings = scan(synthetic_metrics_dir)
    assert len(findings) == 1
    assert (
        findings[0].metric_stable_id
        == "kpi.synthetic_unbound_supply_chain@v1"
    )


def test_supply_chain_metric_with_ocsf_ref_passes(
    synthetic_metrics_dir: Path,
) -> None:
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_bound_supply_chain",
        {
            "stable_id": "kpi.synthetic_bound_supply_chain@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.supply_chain_security@v1"}
            ],
            "telemetry_refs": [
                "telemetry.ocsf.vulnerability_finding@v1"
            ],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_fanout_executive_metric_is_not_supply_chain(
    synthetic_metrics_dir: Path,
) -> None:
    """Fan-out metrics that span supply-chain + the executive_metrics
    catch-all must be kept out by the exclusivity gate — this is the
    exact shape of the current orphan metrics on main, which correctly
    do not classify."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_exec_fanout",
        {
            "stable_id": "kpi.synthetic_exec_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.supply_chain_security@v1"},
                {"playbook_id": "playbook.executive_metrics@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_fanout_asset_management_metric_is_not_supply_chain(
    synthetic_metrics_dir: Path,
) -> None:
    """Fan-out metrics that span supply-chain + asset_management
    (compiler byte-parity pipeline metric shape) must be kept out by
    the exclusivity gate."""
    _write_metric(
        synthetic_metrics_dir,
        "synthetic_asset_fanout",
        {
            "stable_id": "kpi.synthetic_asset_fanout@v1",
            "kind": "kpi",
            "playbook_refs": [
                {"playbook_id": "playbook.supply_chain_security@v1"},
                {"playbook_id": "playbook.asset_management@v1"},
            ],
            "telemetry_refs": [],
        },
    )
    assert scan(synthetic_metrics_dir) == []


def test_metric_without_playbook_refs_is_not_supply_chain(
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
# Helpers / CLI
# ---------------------------------------------------------------------------


def test_has_ocsf_binding_helper() -> None:
    assert has_ocsf_binding(["telemetry.ocsf.vulnerability_finding@v1"])
    assert has_ocsf_binding(
        [
            "telemetry.internal.something@v1",
            "telemetry.ocsf.software_inventory@v1",
        ]
    )
    assert not has_ocsf_binding([])
    assert not has_ocsf_binding(["telemetry.internal.something@v1"])


def test_is_supply_chain_metric_helper() -> None:
    assert is_supply_chain_metric(["playbook.supply_chain_security@v1"])
    assert not is_supply_chain_metric([])
    assert not is_supply_chain_metric(
        [
            "playbook.supply_chain_security@v1",
            "playbook.executive_metrics@v1",
        ]
    )
    assert not is_supply_chain_metric(["playbook.asset_management@v1"])


def test_cli_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_supply_chain_ocsf_bindings"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "supply-chain-ocsf-bindings: PASS" in proc.stdout


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
                {"playbook_id": "playbook.supply_chain_security@v1"}
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
                {"playbook_id": "playbook.supply_chain_security@v1"}
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
    assert payload["supply_chain_cluster"] == sorted(
        SUPPLY_CHAIN_PLAYBOOK_IDS
    )
    assert (
        payload["findings"][0]["metric_stable_id"]
        == "kpi.synthetic_unbound@v1"
    )
