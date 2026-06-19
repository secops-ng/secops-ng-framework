"""End-to-end content-model worked example: vuln_intake.

Validates every artifact in `content-model/examples/vuln_intake/` against
its layer schema and asserts the cross-reference graph is closed:

- playbook ↔ detection / control / telemetry / metric (both directions)
- detection ↔ control, detection ↔ telemetry, control ↔ telemetry
- metric.measurement.inputs[*].{detection,control,telemetry,playbook}_ref
  every reference resolves to a sibling artifact in this example
- OCSF sample payload's class_uid matches the telemetry binding's class_uid

The point of this test is the worked example itself — if the schemas drift
in a way that breaks five-layer composition, this test catches it before
the linter does.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTENT_MODEL = ROOT / "content-model"
EX = CONTENT_MODEL / "examples" / "vuln_intake"

SCHEMAS = {
    "playbook":  CONTENT_MODEL / "playbook.schema.json",
    "detection": CONTENT_MODEL / "detection.schema.json",
    "control":   CONTENT_MODEL / "control.schema.json",
    "telemetry": CONTENT_MODEL / "telemetry.schema.json",
    "metric":    CONTENT_MODEL / "metrics.schema.json",
}

ARTIFACTS = {
    "playbook":  EX / "playbook.json",
    "detection": EX / "detection.json",
    "control":   EX / "control.json",
    "telemetry": EX / "telemetry.json",
}

METRICS_DIR = EX / "metrics"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validators() -> dict[str, Draft202012Validator]:
    out: dict[str, Draft202012Validator] = {}
    for name, path in SCHEMAS.items():
        schema = _load(path)
        Draft202012Validator.check_schema(schema)
        out[name] = Draft202012Validator(schema)
    return out


@pytest.fixture(scope="module")
def artifacts() -> dict[str, dict]:
    return {name: _load(path) for name, path in ARTIFACTS.items()}


@pytest.fixture(scope="module")
def metrics() -> list[dict]:
    return [_load(p) for p in sorted(METRICS_DIR.glob("*.json"))]


# ---------------------------------------------------------------------------
# Per-layer schema validation
# ---------------------------------------------------------------------------

def test_metrics_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(_load(SCHEMAS["metric"]))


@pytest.mark.parametrize("layer", sorted(ARTIFACTS))
def test_layer_artifact_validates(
    layer: str,
    artifacts: dict[str, dict],
    validators: dict[str, Draft202012Validator],
) -> None:
    errs = sorted(validators[layer].iter_errors(artifacts[layer]), key=lambda e: list(e.path))
    assert errs == [], [e.message for e in errs]


def test_each_metric_validates(
    metrics: list[dict],
    validators: dict[str, Draft202012Validator],
) -> None:
    assert metrics, "expected at least one metric in the worked example"
    v = validators["metric"]
    for m in metrics:
        errs = sorted(v.iter_errors(m), key=lambda e: list(e.path))
        assert errs == [], (m["stable_id"], [e.message for e in errs])


# ---------------------------------------------------------------------------
# Cross-reference graph closure
# ---------------------------------------------------------------------------

PLAYBOOK_ID = "playbook.vuln_intake@v1"


def _x(playbook: dict) -> dict:
    return playbook["x_secops_ng"]


def test_playbook_refs_are_mirrored_in_mid_layers(artifacts: dict[str, dict]) -> None:
    det, ctl, tlm = artifacts["detection"], artifacts["control"], artifacts["telemetry"]
    x = _x(artifacts["playbook"])

    assert det["stable_id"] in x["detection_refs"]
    assert ctl["stable_id"] in x["control_refs"]
    assert tlm["stable_id"] in x["telemetry_refs"]

    for art in (det, ctl, tlm):
        pb_ids = {r["playbook_id"] for r in art.get("playbook_refs", [])}
        assert PLAYBOOK_ID in pb_ids, f"{art['stable_id']} does not point at the playbook"


def test_mid_layer_graph_is_closed_and_bidirectional(artifacts: dict[str, dict]) -> None:
    det, ctl, tlm = artifacts["detection"], artifacts["control"], artifacts["telemetry"]

    # detection <-> control
    assert ctl["stable_id"] in det.get("control_refs", [])
    assert det["stable_id"] in ctl.get("detected_by", [])

    # detection <-> telemetry
    assert tlm["stable_id"] in det.get("telemetry_refs", [])
    assert det["stable_id"] in tlm.get("detection_refs", [])

    # control <-> telemetry
    assert tlm["stable_id"] in ctl.get("telemetry_refs", [])
    assert ctl["stable_id"] in tlm.get("control_refs", [])


def test_playbook_metric_refs_match_metrics_dir(
    artifacts: dict[str, dict], metrics: list[dict]
) -> None:
    declared = set(_x(artifacts["playbook"])["metric_refs"])
    present  = {m["stable_id"] for m in metrics}
    assert declared == present, (
        f"playbook.metric_refs and metrics/ disagree: "
        f"declared={declared} present={present}"
    )


def test_every_metric_points_back_at_the_playbook(metrics: list[dict]) -> None:
    for m in metrics:
        pb_ids = {r["playbook_id"] for r in m.get("playbook_refs", [])}
        assert PLAYBOOK_ID in pb_ids, f"metric {m['stable_id']} does not pin the playbook"


def test_metric_inputs_resolve_to_sibling_artifacts(
    artifacts: dict[str, dict], metrics: list[dict]
) -> None:
    siblings = {
        artifacts["detection"]["stable_id"],
        artifacts["control"]["stable_id"],
        artifacts["telemetry"]["stable_id"],
        PLAYBOOK_ID,
    }
    ref_fields = ("detection_ref", "control_ref", "telemetry_ref", "playbook_ref")
    for m in metrics:
        for inp in m["measurement"].get("inputs", []):
            for field in ref_fields:
                ref = inp.get(field)
                if ref is None:
                    continue
                assert ref in siblings, (
                    f"metric {m['stable_id']} input {inp.get('name')!r} "
                    f"{field}={ref} does not resolve to a sibling artifact"
                )


# ---------------------------------------------------------------------------
# Telemetry sample alignment
# ---------------------------------------------------------------------------

def test_telemetry_sample_matches_binding(artifacts: dict[str, dict]) -> None:
    tlm = artifacts["telemetry"]
    sample_path = ROOT / tlm["sample"]["path"]
    assert sample_path.exists(), f"missing sample payload: {sample_path}"
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    assert payload["class_uid"] == tlm["ocsf"]["class_uid"]


# ---------------------------------------------------------------------------
# Namespace / kind consistency on the metric layer
# ---------------------------------------------------------------------------

def test_metric_namespace_agrees_with_kind(metrics: list[dict]) -> None:
    for m in metrics:
        prefix = m["stable_id"].split(".", 1)[0]
        assert prefix == m["kind"], (
            f"metric {m['stable_id']} stable_id prefix '{prefix}' "
            f"does not match kind '{m['kind']}'"
        )
