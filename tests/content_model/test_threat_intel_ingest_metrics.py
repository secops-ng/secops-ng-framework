"""Threat-intel-ingest KPI metric files — schema validation + linkage.

Validates every JSON in
``content-model/examples/threat_intel_ingest/metrics/`` against the
metrics schema and asserts the per-playbook linkage invariants the
EXTEND card commits to:

- metric stable_ids are unique within the playbook's metrics dir;
- each metric pins ``playbook.threat_intel_ingest@v1`` in its
  ``playbook_refs``;
- step_ids referenced from metrics resolve to real workflow steps
  in ``content/playbooks/threat_intel_ingest/playbook.cacao.json``;
- the playbook's top-level ``x_secops_ng.metric_refs`` is exactly the
  set of metric stable_ids present in the metrics dir (closed graph).

Pure stdlib + jsonschema. No network.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTENT_MODEL = ROOT / "content-model"
METRICS_SCHEMA = CONTENT_MODEL / "metrics.schema.json"
METRICS_DIR = CONTENT_MODEL / "examples" / "threat_intel_ingest" / "metrics"
PLAYBOOK_PATH = (
    ROOT / "content" / "playbooks" / "threat_intel_ingest" / "playbook.cacao.json"
)
PLAYBOOK_STABLE_ID = "playbook.threat_intel_ingest@v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _metric_files() -> list[Path]:
    return sorted(METRICS_DIR.glob("*.json"))


@pytest.fixture(scope="module")
def validator() -> Draft202012Validator:
    schema = _load(METRICS_SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def metrics() -> list[dict]:
    return [_load(p) for p in _metric_files()]


@pytest.fixture(scope="module")
def playbook() -> dict:
    return _load(PLAYBOOK_PATH)


def test_metrics_dir_is_populated() -> None:
    files = _metric_files()
    assert files, (
        "expected at least one metric JSON under "
        "content-model/examples/threat_intel_ingest/metrics/"
    )


@pytest.mark.parametrize(
    "path", _metric_files(), ids=lambda p: p.name
)
def test_metric_file_validates(
    path: Path, validator: Draft202012Validator
) -> None:
    doc = _load(path)
    errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    assert errs == [], [
        f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}"
        for e in errs
    ]


def test_metric_stable_ids_are_unique(metrics: list[dict]) -> None:
    ids = [m["stable_id"] for m in metrics]
    assert len(ids) == len(set(ids)), f"duplicate metric stable_ids: {ids}"


def test_metric_namespace_agrees_with_kind(metrics: list[dict]) -> None:
    for m in metrics:
        prefix = m["stable_id"].split(".", 1)[0]
        assert prefix == m["kind"], (
            f"metric {m['stable_id']} stable_id prefix '{prefix}' "
            f"does not match kind '{m['kind']}'"
        )


def test_each_metric_pins_the_playbook(metrics: list[dict]) -> None:
    for m in metrics:
        pb_ids = {r["playbook_id"] for r in m.get("playbook_refs", [])}
        assert PLAYBOOK_STABLE_ID in pb_ids, (
            f"metric {m['stable_id']} does not pin "
            f"{PLAYBOOK_STABLE_ID} in playbook_refs"
        )


def test_metric_step_refs_resolve_to_workflow_steps(
    metrics: list[dict], playbook: dict
) -> None:
    workflow_step_ids = set(playbook["workflow"].keys())
    for m in metrics:
        for ref in m.get("playbook_refs", []):
            if ref["playbook_id"] != PLAYBOOK_STABLE_ID:
                continue
            step_id = ref.get("step_id")
            if step_id is None:
                continue
            assert step_id in workflow_step_ids, (
                f"metric {m['stable_id']} playbook_refs.step_id={step_id!r} "
                f"does not resolve to a workflow step in {PLAYBOOK_PATH.name}"
            )
        for inp in m["measurement"].get("inputs", []):
            step_id = inp.get("playbook_step")
            pb_ref = inp.get("playbook_ref")
            if step_id is None or pb_ref != PLAYBOOK_STABLE_ID:
                continue
            assert step_id in workflow_step_ids, (
                f"metric {m['stable_id']} measurement input "
                f"{inp.get('name')!r} playbook_step={step_id!r} does not "
                f"resolve to a workflow step in {PLAYBOOK_PATH.name}"
            )


def test_playbook_metric_refs_match_metrics_dir(
    metrics: list[dict], playbook: dict
) -> None:
    declared = set(playbook["x_secops_ng"]["metric_refs"])
    present = {m["stable_id"] for m in metrics}
    assert declared == present, (
        f"playbook.x_secops_ng.metric_refs and metrics/ disagree: "
        f"declared={declared} present={present}"
    )
