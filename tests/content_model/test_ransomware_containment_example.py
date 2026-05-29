"""End-to-end content-model worked example: ransomware-containment.

Validates every artifact in `content-model/examples/ransomware-containment/`
against its layer schema and asserts the cross-reference graph that the
example *does* materialise is closed:

- playbook → detection / control / telemetry (the materialised refs
  appear in the playbook's `x_secops_ng` ref lists);
- each materialised mid-layer artifact points back at the playbook via
  `playbook_refs[].playbook_id`;
- every metric pins the playbook;
- each metric's `measurement.inputs[*].{detection,control,telemetry,
  playbook}_ref` either resolves to a materialised sibling OR is an
  upstream Sigma pointer (the playbook references upstream rules
  directly via `external_references` and we don't re-author them);
- the OCSF sample payload's `class_uid` matches the telemetry binding;
- metric stable_id namespace prefix agrees with its `kind`.

The ransomware-containment example deliberately materialises only one
mid-layer artifact per layer (the canonical containment binding) and
references additional controls / telemetry that live in sibling worked
examples — so the assertions accept any `detection.sigma.*`,
`control.*`, or `telemetry.*` ref that the playbook declares but the
example does not materialise.

Pattern mirrors `test_cloud_misconfiguration_example.py`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTENT_MODEL = ROOT / "content-model"
EX = CONTENT_MODEL / "examples" / "ransomware-containment"

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

PLAYBOOK_ID = "playbook.ransomware_containment@v1"


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


@pytest.mark.parametrize("layer", sorted(ARTIFACTS))
def test_layer_artifact_validates(
    layer: str,
    artifacts: dict[str, dict],
    validators: dict[str, Draft202012Validator],
) -> None:
    errs = sorted(
        validators[layer].iter_errors(artifacts[layer]), key=lambda e: list(e.path)
    )
    assert errs == [], [e.message for e in errs]


def test_each_metric_validates(
    metrics: list[dict],
    validators: dict[str, Draft202012Validator],
) -> None:
    assert len(metrics) == 5, f"expected 5 metrics (4 KPI + 1 KRI), got {len(metrics)}"
    v = validators["metric"]
    for m in metrics:
        errs = sorted(v.iter_errors(m), key=lambda e: list(e.path))
        assert errs == [], (m["stable_id"], [e.message for e in errs])


# ---------------------------------------------------------------------------
# Cross-reference graph closure (over what the example materialises)
# ---------------------------------------------------------------------------


def _x(playbook: dict) -> dict:
    return playbook["x_secops_ng"]


def test_materialised_layers_appear_in_playbook_refs(
    artifacts: dict[str, dict],
) -> None:
    det, ctl, tlm = artifacts["detection"], artifacts["control"], artifacts["telemetry"]
    x = _x(artifacts["playbook"])

    assert det["stable_id"] in x["detection_refs"], (
        f"playbook does not list detection {det['stable_id']!r} in x_secops_ng.detection_refs"
    )
    assert ctl["stable_id"] in x["control_refs"], (
        f"playbook does not list control {ctl['stable_id']!r} in x_secops_ng.control_refs"
    )
    assert tlm["stable_id"] in x["telemetry_refs"], (
        f"playbook does not list telemetry {tlm['stable_id']!r} in x_secops_ng.telemetry_refs"
    )


def test_each_materialised_mid_layer_points_back_at_playbook(
    artifacts: dict[str, dict],
) -> None:
    for layer in ("detection", "control", "telemetry"):
        art = artifacts[layer]
        pb_ids = {r["playbook_id"] for r in art.get("playbook_refs", [])}
        assert PLAYBOOK_ID in pb_ids, (
            f"{art['stable_id']} does not point at {PLAYBOOK_ID}"
        )


def test_playbook_metric_refs_match_metrics_dir(
    artifacts: dict[str, dict], metrics: list[dict]
) -> None:
    declared = set(_x(artifacts["playbook"])["metric_refs"])
    present = {m["stable_id"] for m in metrics}
    assert declared == present, (
        f"playbook.metric_refs and metrics/ disagree: "
        f"declared={declared} present={present}"
    )


def test_every_metric_points_back_at_the_playbook(metrics: list[dict]) -> None:
    for m in metrics:
        pb_ids = {r["playbook_id"] for r in m.get("playbook_refs", [])}
        assert PLAYBOOK_ID in pb_ids, (
            f"metric {m['stable_id']} does not pin the playbook"
        )


def test_metric_inputs_resolve_to_sibling_or_upstream(
    artifacts: dict[str, dict], metrics: list[dict]
) -> None:
    """Metric inputs must resolve to a materialised sibling, OR be an
    upstream Sigma pointer (this example does not re-author Sigma)."""
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
                if field == "detection_ref" and ref.startswith("detection.sigma."):
                    # upstream Sigma pointer, accepted without an in-tree sibling
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
    assert payload["class_uid"] == tlm["ocsf"]["class_uid"], (
        f"sample class_uid={payload['class_uid']} but telemetry binds "
        f"class_uid={tlm['ocsf']['class_uid']}"
    )


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
