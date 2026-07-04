"""F-WF-DPIA CORE \u2014 byte-parity golden for the n8n data_protection_impact_assessment workflow.

The committed
``examples/n8n/data_protection_impact_assessment/workflow.n8n.json`` is
the n8n compiler's output for the canonical CACAO playbook at
``content/playbooks/data_protection_impact_assessment/playbook.cacao.yaml``.

This module pins the workflow JSON against the emitter so a refactor
of the n8n compiler that silently changes serialisation (or a drift
between the canonical playbook and the mirrored example copy) gets
caught at the byte level.

Regenerate on intentional change via::

    ./examples/n8n/data_protection_impact_assessment/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit as emit_n8n

REPO = Path(__file__).resolve().parents[3]
CANON_YAML = (
    REPO
    / "content"
    / "playbooks"
    / "data_protection_impact_assessment"
    / "playbook.cacao.yaml"
)
EXAMPLE = REPO / "examples" / "n8n" / "data_protection_impact_assessment"
WORKFLOW_GOLDEN = EXAMPLE / "workflow.n8n.json"
MIRROR = EXAMPLE / "playbook.cacao.json"


def _serialise_n8n(payload: dict) -> str:
    """Match ``python -m tools.compile --target n8n`` (indent=2)."""
    return json.dumps(payload, indent=2) + "\n"


def _canonical_mirror_bytes() -> bytes:
    data = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def test_example_artifacts_are_committed() -> None:
    for path in (WORKFLOW_GOLDEN, MIRROR):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_mirrored_playbook_matches_canonical() -> None:
    assert MIRROR.read_bytes() == _canonical_mirror_bytes(), (
        "examples/n8n/data_protection_impact_assessment/playbook.cacao.json "
        "drifted from the canonical "
        "content/playbooks/data_protection_impact_assessment/playbook.cacao.yaml. "
        "Regenerate via "
        "`./examples/n8n/data_protection_impact_assessment/regenerate.sh`."
    )


def test_n8n_workflow_matches_golden() -> None:
    playbook = parse_file(MIRROR)
    rendered = _serialise_n8n(emit_n8n(playbook))
    expected = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "data_protection_impact_assessment n8n workflow drifted. Regenerate via "
        "`./examples/n8n/data_protection_impact_assessment/regenerate.sh` and "
        "commit the new bytes alongside the emitter change."
    )


def test_n8n_workflow_emit_is_deterministic() -> None:
    playbook = parse_file(MIRROR)
    assert _serialise_n8n(emit_n8n(playbook)) == _serialise_n8n(emit_n8n(playbook))


def test_node_ids_mirror_cacao_step_ids() -> None:
    playbook_raw = json.loads(MIRROR.read_text(encoding="utf-8"))
    cacao_step_ids = set(playbook_raw["workflow"].keys())
    workflow = json.loads(WORKFLOW_GOLDEN.read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in workflow["nodes"]}
    missing = cacao_step_ids - node_ids
    assert not missing, f"CACAO step ids without matching n8n node id: {sorted(missing)}"
    extra = node_ids - cacao_step_ids
    assert not extra, f"n8n node ids without matching CACAO step id: {sorted(extra)}"
    assert len(workflow["nodes"]) == len(cacao_step_ids), "duplicate node ids"
