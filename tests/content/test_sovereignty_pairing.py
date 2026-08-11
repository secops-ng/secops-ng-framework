"""The sovereignty coverage/residual-risk pairing invariant (G-04, F-SV-06).

Replaces ``test_sovereignty_lm_endpoint_pairing.py``. The retired lint matched
``kpi.lm_endpoint_*_coverage@vN`` against
``kri.lm_endpoint_*_unknown_*_exposure@vN`` **by name**, for one indicator
family. These tests pin the generalised rule: the pairing is *declared* in
``residual_risk_refs`` and applies to every sovereignty-cluster coverage KPI.

Two properties matter most here and each has a test:

* the LM-endpoint family, which shipped green under the retired lint, is HARD
  rather than folded into the SOFT population — widening a rule must not
  quietly relax the case it already covered;
* the SOFT ceiling gates when exceeded, so the undeclared population can only
  shrink.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.lint_sovereignty_pairing import (
    is_coverage_kpi,
    main,
    partition,
    scan,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _metric(**over) -> dict:
    doc = {
        "stable_id": "kpi.example_coverage@v1",
        "content_version": "0.1.0",
        "maturity": "experimental",
        "kind": "kpi",
        "title": "t",
        "unit": "ratio",
        "direction": "higher_is_better",
        "measurement": {"source": "workflow", "aggregation": "ratio"},
        "foundation_property": ["sovereignty"],
    }
    doc.update(over)
    return doc


def _write(d: Path, *docs: dict) -> Path:
    for doc in docs:
        stem = doc["stable_id"].split(".", 1)[1].split("@")[0]
        (d / f"{stem}.yaml").write_text(yaml.safe_dump(doc), encoding="utf-8")
    return d


# --- shipped tree -----------------------------------------------------------


def test_shipped_tree_has_no_hard_findings() -> None:
    hard, _ = partition(scan())
    assert hard == [], [f.as_text() for f in hard]


def test_shipped_tree_has_no_soft_findings() -> None:
    """F-SV-06 stage 2 promoted the last SOFT code; the partition is empty."""
    _, soft = partition(scan())
    assert soft == [], (
        "SOFT findings reappeared after the F-SV-06 stage-2 promotion — "
        f"{[f.kpi_stable_id for f in soft]}. Every code is HARD now; a new "
        "SOFT code is a decision that belongs in the module docstring."
    )


def test_shipped_tree_actually_contains_declared_pairings() -> None:
    """Guard against the lint passing because it found nothing to check."""
    import glob
    declared = [
        yaml.safe_load(open(p, encoding="utf-8"))
        for p in glob.glob(str(REPO_ROOT / "content" / "metrics" / "*.yaml"))
    ]
    with_refs = [d for d in declared
                 if isinstance(d, dict) and d.get("residual_risk_refs")]
    assert with_refs, "no metric declares residual_risk_refs at all"
    assert any(is_coverage_kpi(d) for d in with_refs)


def test_lm_endpoint_pairing_is_declared_not_inferred() -> None:
    """The retired lint's case now rests on an explicit declaration."""
    p = REPO_ROOT / "content" / "metrics" / "lm_endpoint_eu_residency_coverage.yaml"
    refs = yaml.safe_load(p.read_text(encoding="utf-8"))["residual_risk_refs"]
    assert "kri.lm_endpoint_unknown_residency_exposure@v1" in refs


def test_retired_linter_is_gone() -> None:
    """One source of truth: the bespoke module must not survive alongside."""
    assert not (REPO_ROOT / "tools" / "lint_sovereignty_lm_endpoint_pairing.py").exists()
    assert not (REPO_ROOT / "tests" / "content"
                / "test_sovereignty_lm_endpoint_pairing.py").exists()


# --- HARD codes -------------------------------------------------------------


def test_declared_pairing_that_holds_is_clean(tmp_path: Path) -> None:
    _write(tmp_path,
           _metric(residual_risk_refs=["kri.example_exposure@v1"]),
           _metric(stable_id="kri.example_exposure@v1", kind="kri",
                   unit="count", direction="lower_is_better"))
    assert scan(tmp_path) == []


def test_unresolved_ref_is_hard(tmp_path: Path) -> None:
    _write(tmp_path, _metric(residual_risk_refs=["kri.absent@v1"]))
    f = scan(tmp_path)
    assert [x.code for x in f] == ["unresolved_residual_risk_ref"]
    assert f[0].severity == "HARD"


def test_ref_to_a_kpi_is_hard(tmp_path: Path) -> None:
    _write(tmp_path,
           _metric(residual_risk_refs=["kpi.other_coverage@v1"]),
           _metric(stable_id="kpi.other_coverage@v1"))
    assert "residual_risk_ref_not_kri" in {x.code for x in scan(tmp_path)}


def test_version_family_mismatch_is_hard(tmp_path: Path) -> None:
    _write(tmp_path,
           _metric(residual_risk_refs=["kri.example_exposure@v2"]),
           _metric(stable_id="kri.example_exposure@v2", kind="kri",
                   unit="count", direction="lower_is_better"))
    assert "residual_risk_ref_version_mismatch" in {x.code for x in scan(tmp_path)}


def test_counterpart_without_sovereignty_is_hard(tmp_path: Path) -> None:
    _write(tmp_path,
           _metric(residual_risk_refs=["kri.example_exposure@v1"]),
           _metric(stable_id="kri.example_exposure@v1", kind="kri",
                   unit="count", direction="lower_is_better",
                   foundation_property=["auditability"]))
    assert "residual_risk_ref_property_gap" in {x.code for x in scan(tmp_path)}


def test_counterpart_need_not_mirror_every_property(tmp_path: Path) -> None:
    """A KPI serving two properties may pair with a single-property KRI.

    ``kpi.lm_endpoint_eu_residency_coverage@v1`` serves sovereignty *and*
    determinism while its counterparts honestly serve only sovereignty. The
    stricter rule would have pushed contributors to add untrue property claims.
    """
    _write(tmp_path,
           _metric(foundation_property=["sovereignty", "determinism"],
                   residual_risk_refs=["kri.example_exposure@v1"]),
           _metric(stable_id="kri.example_exposure@v1", kind="kri",
                   unit="count", direction="lower_is_better",
                   foundation_property=["sovereignty"]))
    assert scan(tmp_path) == []


def test_lm_endpoint_without_declaration_is_hard_not_soft(tmp_path: Path) -> None:
    """Widening the rule must not relax the family it already covered."""
    _write(tmp_path, _metric(stable_id="kpi.lm_endpoint_eu_residency_coverage@v1"))
    f = scan(tmp_path)
    assert [x.code for x in f] == ["lm_endpoint_pairing_regressed"]
    assert f[0].severity == "HARD"
    assert main(["--format", "json", "--metrics-dir", str(tmp_path)]) == 1


# --- promoted code ----------------------------------------------------------


def test_coverage_kpi_without_declaration_is_hard(tmp_path: Path) -> None:
    """Promoted by F-SV-06 stage 2: an undeclared coverage KPI gates alone."""
    _write(tmp_path, _metric(stable_id="kpi.cloud_posture_coverage@v1"))
    f = scan(tmp_path)
    assert [x.code for x in f] == ["coverage_kpi_without_residual_risk"]
    assert f[0].severity == "HARD"
    assert main(["--format", "text", "--metrics-dir", str(tmp_path)]) == 1


# --- scope ------------------------------------------------------------------


def test_non_sovereignty_coverage_kpi_is_ignored(tmp_path: Path) -> None:
    _write(tmp_path, _metric(foundation_property=["auditability"]))
    assert scan(tmp_path) == []


def test_non_coverage_sovereignty_kpi_is_ignored(tmp_path: Path) -> None:
    _write(tmp_path, _metric(stable_id="kpi.sovereign_cloud_provider_diversity@v1"))
    assert scan(tmp_path) == []


def test_kri_is_never_required_to_pair(tmp_path: Path) -> None:
    _write(tmp_path, _metric(stable_id="kri.some_exposure@v1", kind="kri",
                             unit="count", direction="lower_is_better"))
    assert scan(tmp_path) == []


# --- CLI --------------------------------------------------------------------


def test_cli_json_payload_shape(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(tmp_path, _metric(residual_risk_refs=["kri.absent@v1"]))
    rc = main(["--format", "json", "--metrics-dir", str(tmp_path)])
    doc = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert doc["tool"] == "sovereignty-pairing"
    assert doc["hard"] == 1 and doc["soft"] == 0
    assert doc["findings"][0]["code"] == "unresolved_residual_risk_ref"


def test_cli_subprocess_on_real_tree() -> None:
    """The invocation the CI lane runs."""
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_sovereignty_pairing", "--format", "text"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "0 HARD" in proc.stdout
