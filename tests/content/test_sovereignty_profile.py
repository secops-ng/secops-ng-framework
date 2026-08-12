"""F-SV-05 — declared sovereignty conformance profile.

Pins, mapped to the ROADMAP acceptance criteria:

1. The shipped baseline validates against its schema and classifies
   every sovereignty-tagged catalogue metric, both directions — the
   linter's force-a-classification contract, asserted here and via the
   CLI the CI lane runs.
2. Evaluation is deterministic and pure: evaluating the committed
   F-SV-04 temporal worked example twice yields byte-identical
   verdicts; the verdict is per-indicator with a pass/fail roll-up and
   carries no score-shaped key.
3. The committed example evaluates to its true verdict: the reference
   posture holds warn-band readings on warn-tolerating indicators and
   the profile does not paper over hard floors.
4. Tightening a band needs nothing; loosening below the baseline
   without a recorded override is refused naming the indicator; a
   correctly recorded override is honoured and surfaced in the verdict
   as ``via_override``.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from compilers._shared.evidence.sovereignty_profile import (
    ProfileError,
    effective_bands,
    evaluate_record,
    validate_profile_against_baseline,
)
from tools.lint_sovereignty_profile import scan

REPO_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = REPO_ROOT / "content" / "profiles" / "sovereignty_conformance.yaml"
RECORD_PATH = (
    REPO_ROOT / "examples" / "temporal" / "infra_posture_management"
    / "evidence" / "sovereignty" / "sovereignty-posture-attestation.json"
)


def _profile() -> dict:
    return yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))


def _record() -> dict:
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. shipped baseline: valid, complete, evaluable
# ---------------------------------------------------------------------------


def test_shipped_profile_is_clean() -> None:
    findings = scan()
    assert findings == [], [f.as_text() for f in findings]


def test_cli_lint_passes_on_shipped_tree() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.lint_sovereignty_profile"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_missing_indicator_is_a_named_finding(tmp_path: Path) -> None:
    profile = _profile()
    dropped = "kri.non_eu_vendor_sdk_exposure@v1"
    del profile["indicators"][dropped]
    mutated = tmp_path / "profile.yaml"
    mutated.write_text(yaml.safe_dump(profile))
    findings = scan(profile_path=mutated)
    assert [f.code for f in findings] == ["unclassified_sovereignty_metric"]
    assert dropped in findings[0].detail


def test_unknown_indicator_is_a_named_finding(tmp_path: Path) -> None:
    profile = _profile()
    profile["indicators"]["kpi.invented_coverage@v1"] = {
        "max_band": "warn",
        "rationale": "does not exist",
    }
    mutated = tmp_path / "profile.yaml"
    mutated.write_text(yaml.safe_dump(profile))
    findings = scan(profile_path=mutated)
    assert [f.code for f in findings] == ["unknown_profile_indicator"]
    assert "kpi.invented_coverage@v1" in findings[0].detail


# ---------------------------------------------------------------------------
# 2 + 3. deterministic evaluation of the committed example
# ---------------------------------------------------------------------------


def test_evaluation_is_deterministic_and_scoreless() -> None:
    first = evaluate_record(_record(), _profile())
    second = evaluate_record(_record(), _profile())
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    flat = json.dumps(first).lower()
    for w in ("score", "ratio", "percent"):
        assert f'"{w}' not in flat, f"verdict grew a {w}-shaped key"


def test_committed_example_verdict_is_true_not_flattering() -> None:
    verdict = evaluate_record(_record(), _profile())
    by = verdict["indicators"]
    # warn observations on warn-tolerating indicators pass…
    assert by["kri.lm_endpoint_unknown_residency_exposure@v1"]["outcome"] == "pass"
    assert by["kri.cloud_container_unclassifiable_scope_count@v1"]["outcome"] == "pass"
    # …the warn reading on the on_target LM-endpoint coverage floor fails…
    assert by["kpi.lm_endpoint_eu_residency_coverage@v1"]["outcome"] == "fail"
    # …and the high reading on the warn-tolerating critical-dependency KRI fails.
    assert by["kri.non_eu_critical_dependency_count@v1"]["outcome"] == "fail"
    # So the reference posture, honestly, does not (yet) hold.
    assert verdict["pass"] is False


def test_all_pass_record_holds(tmp_path: Path) -> None:
    record = _record()
    for obs in record["observations"].values():
        obs["threshold_band"] = "on_target"
    verdict = evaluate_record(record, _profile())
    assert verdict["pass"] is True
    assert all(v["outcome"] == "pass" for v in verdict["indicators"].values())


def test_unprofiled_observation_fails_roll_up() -> None:
    record = _record()
    record["observations"]["kpi.invented_coverage@v1"] = {
        "observed_value": 1.0,
        "threshold_band": "on_target",
        "observed_at": "2026-08-01T06:00:00Z",
    }
    verdict = evaluate_record(record, _profile())
    assert verdict["indicators"]["kpi.invented_coverage@v1"]["outcome"] == "unprofiled"
    assert verdict["pass"] is False


# ---------------------------------------------------------------------------
# 4. tighten freely; loosen only on the record
# ---------------------------------------------------------------------------


def _operator_profile(**changes) -> dict:
    profile = copy.deepcopy(_profile())
    profile["stable_id"] = "profile.operator_derived@v1"
    profile["baseline_ref"] = "profile.sovereignty_conformance@v1"
    for sid, band in changes.items():
        profile["indicators"][sid]["max_band"] = band
    return profile


def test_tightening_needs_no_override() -> None:
    tightened = _operator_profile(
        **{"kri.lm_endpoint_unknown_residency_exposure@v1": "on_target"}
    )
    validate_profile_against_baseline(tightened, _profile())  # no raise


def test_unrecorded_loosening_is_refused_naming_the_indicator() -> None:
    loosened = _operator_profile(
        **{"kpi.lm_endpoint_eu_residency_coverage@v1": "warn"}
    )
    with pytest.raises(ProfileError, match="lm_endpoint_eu_residency_coverage"):
        validate_profile_against_baseline(loosened, _profile())


def test_recorded_override_is_honoured_and_visible() -> None:
    sid = "kpi.lm_endpoint_eu_residency_coverage@v1"
    loosened = _operator_profile(**{sid: "warn"})
    loosened["overrides"] = [{
        "indicator": sid,
        "baseline_band": "on_target",
        "declared_band": "warn",
        "rationale": "Two UNKNOWN self-hosted gateways under active residency review; accepted until the review closes.",
        "recorded_by": "sovereignty-review-board",
        "recorded_at": "2026-08-12T00:00:00Z",
    }]
    validate_profile_against_baseline(loosened, _profile())  # recorded — fine
    verdict = evaluate_record(_record(), loosened)
    entry = verdict["indicators"][sid]
    assert entry["outcome"] == "pass"
    assert entry["via_override"] is True


def test_override_that_does_not_relax_is_a_mistake() -> None:
    profile = _operator_profile()
    profile["overrides"] = [{
        "indicator": "kpi.lm_endpoint_eu_residency_coverage@v1",
        "baseline_band": "on_target",
        "declared_band": "on_target",
        "rationale": "no-op",
        "recorded_by": "sovereignty-review-board",
        "recorded_at": "2026-08-12T00:00:00Z",
    }]
    with pytest.raises(ProfileError, match="does not relax"):
        effective_bands(profile)


# ---------------------------------------------------------------------------
# CLI — the invocation an operator (and CI) runs
# ---------------------------------------------------------------------------


def test_cli_evaluator_verdict_and_exit_code() -> None:
    proc = subprocess.run(
        [
            sys.executable, "-m", "tools.evaluate_sovereignty_conformance",
            str(RECORD_PATH), "--format", "json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    verdict = json.loads(proc.stdout)
    assert verdict["pass"] is False
    assert len(verdict["indicators"]) == 26


def test_cli_evaluator_is_byte_deterministic() -> None:
    def run() -> str:
        return subprocess.run(
            [
                sys.executable, "-m", "tools.evaluate_sovereignty_conformance",
                str(RECORD_PATH), "--format", "json",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        ).stdout
    assert run() == run()
