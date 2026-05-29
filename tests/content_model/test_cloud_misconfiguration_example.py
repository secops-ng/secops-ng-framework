"""End-to-end content-model worked example: cloud-misconfiguration.

Mirrors `test_vuln_intake_example.py` and validates every artifact in
`content-model/examples/cloud-misconfiguration/` against its layer
schema. The cloud-misconfiguration example has a slightly different
shape than vuln-intake — three controls + two telemetry classes, and
no in-tree detection layer (the detection refs are upstream SigmaHQ
rules pinned via the playbook's `external_references`) — so the
cross-reference assertions are adapted accordingly.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTENT_MODEL = ROOT / "content-model"
EX = CONTENT_MODEL / "examples" / "cloud-misconfiguration"
PLAYBOOK_PATH = ROOT / "content" / "playbooks" / "cloud-misconfiguration" / "playbook.cacao.json"

SCHEMAS = {
    "playbook":  CONTENT_MODEL / "playbook.schema.json",
    "control":   CONTENT_MODEL / "control.schema.json",
    "telemetry": CONTENT_MODEL / "telemetry.schema.json",
    "metric":    CONTENT_MODEL / "metrics.schema.json",
}

PLAYBOOK_ID = "playbook.cloud_misconfiguration@v1"


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
def playbook() -> dict:
    return _load(PLAYBOOK_PATH)


@pytest.fixture(scope="module")
def controls() -> list[dict]:
    return [_load(p) for p in sorted(EX.glob("control*.json"))]


@pytest.fixture(scope="module")
def telemetries() -> list[dict]:
    return [_load(p) for p in sorted(EX.glob("telemetry*.json"))]


@pytest.fixture(scope="module")
def metrics() -> list[dict]:
    return [_load(p) for p in sorted((EX / "metrics").glob("*.json"))]


# ---------------------------------------------------------------------------
# Per-layer schema validation
# ---------------------------------------------------------------------------

def test_playbook_validates(playbook: dict, validators: dict[str, Draft202012Validator]) -> None:
    errs = sorted(validators["playbook"].iter_errors(playbook), key=lambda e: list(e.path))
    assert errs == [], [e.message for e in errs]


def test_each_control_validates(controls: list[dict], validators: dict[str, Draft202012Validator]) -> None:
    assert len(controls) == 3, f"expected 3 controls, got {len(controls)}"
    v = validators["control"]
    for c in controls:
        errs = sorted(v.iter_errors(c), key=lambda e: list(e.path))
        assert errs == [], (c["stable_id"], [e.message for e in errs])


def test_each_telemetry_validates(telemetries: list[dict], validators: dict[str, Draft202012Validator]) -> None:
    assert len(telemetries) == 2, f"expected 2 telemetry artifacts, got {len(telemetries)}"
    v = validators["telemetry"]
    for t in telemetries:
        errs = sorted(v.iter_errors(t), key=lambda e: list(e.path))
        assert errs == [], (t["stable_id"], [e.message for e in errs])


def test_each_metric_validates(metrics: list[dict], validators: dict[str, Draft202012Validator]) -> None:
    assert len(metrics) == 4, f"expected 4 metrics (3 KPI + 1 KRI), got {len(metrics)}"
    v = validators["metric"]
    for m in metrics:
        errs = sorted(v.iter_errors(m), key=lambda e: list(e.path))
        assert errs == [], (m["stable_id"], [e.message for e in errs])


# ---------------------------------------------------------------------------
# Cross-reference graph closure
# ---------------------------------------------------------------------------

def _x(playbook: dict) -> dict:
    return playbook["x_secops_ng"]


def test_playbook_refs_are_mirrored_in_mid_layers(
    playbook: dict, controls: list[dict], telemetries: list[dict]
) -> None:
    x = _x(playbook)
    declared_controls = set(x["control_refs"])
    declared_telemetries = set(x["telemetry_refs"])
    present_controls = {c["stable_id"] for c in controls}
    present_telemetries = {t["stable_id"] for t in telemetries}

    assert declared_controls == present_controls, (
        f"playbook.control_refs disagrees with controls dir: "
        f"declared={declared_controls} present={present_controls}"
    )
    assert declared_telemetries == present_telemetries, (
        f"playbook.telemetry_refs disagrees with telemetry dir: "
        f"declared={declared_telemetries} present={present_telemetries}"
    )

    for art in (*controls, *telemetries):
        pb_ids = {r["playbook_id"] for r in art.get("playbook_refs", [])}
        assert PLAYBOOK_ID in pb_ids, f"{art['stable_id']} does not point at the playbook"


def test_playbook_metric_refs_match_metrics_dir(
    playbook: dict, metrics: list[dict]
) -> None:
    declared = set(_x(playbook)["metric_refs"])
    present = {m["stable_id"] for m in metrics}
    assert declared == present, (
        f"playbook.metric_refs and metrics/ disagree: "
        f"declared={declared} present={present}"
    )


def test_every_metric_points_back_at_the_playbook(metrics: list[dict]) -> None:
    for m in metrics:
        pb_ids = {r["playbook_id"] for r in m.get("playbook_refs", [])}
        assert PLAYBOOK_ID in pb_ids, f"metric {m['stable_id']} does not pin the playbook"


def test_metric_inputs_resolve_to_sibling_artifacts(
    controls: list[dict], telemetries: list[dict], metrics: list[dict]
) -> None:
    siblings = {c["stable_id"] for c in controls} \
        | {t["stable_id"] for t in telemetries} \
        | {PLAYBOOK_ID}
    # Detection refs in this example are upstream Sigma pointers carried
    # by the playbook's external_references — accept any
    # `detection.sigma.*` id without requiring an in-tree sibling.
    for m in metrics:
        for inp in m["measurement"].get("inputs", []):
            for field in ("control_ref", "telemetry_ref", "playbook_ref"):
                ref = inp.get(field)
                if ref is None:
                    continue
                assert ref in siblings, (
                    f"metric {m['stable_id']} input {inp.get('name')!r} "
                    f"{field}={ref} does not resolve to a sibling artifact"
                )


def test_metric_namespace_agrees_with_kind(metrics: list[dict]) -> None:
    for m in metrics:
        prefix = m["stable_id"].split(".", 1)[0]
        assert prefix == m["kind"], (
            f"metric {m['stable_id']} stable_id prefix '{prefix}' "
            f"does not match kind '{m['kind']}'"
        )


def test_control_to_telemetry_links_are_present(
    controls: list[dict], telemetries: list[dict]
) -> None:
    """Every control must point at >=1 telemetry binding in this example."""
    telemetry_ids = {t["stable_id"] for t in telemetries}
    for c in controls:
        refs = set(c.get("telemetry_refs", []))
        assert refs, f"control {c['stable_id']} has no telemetry_refs"
        assert refs <= telemetry_ids, (
            f"control {c['stable_id']} telemetry_refs={refs} "
            f"contains entries outside the example's telemetry layer"
        )
