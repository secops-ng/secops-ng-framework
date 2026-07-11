"""Byte-parity golden for the n8n network_security workflow (G-03).

The committed ``examples/n8n/network_security/workflow.n8n.json`` is the n8n
compiler's output for the canonical CACAO playbook at
``content/playbooks/network_security/playbook.cacao.yaml``. This module pins the
workflow JSON against the emitter and the co-located YAML mirror
against the canonical YAML source so an emitter refactor or a hand
edit gets caught at the byte level.

Regenerate on intentional change via::

    ./examples/n8n/network_security/regenerate.sh
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from compilers._shared.cacao_parser import parse_file
from compilers.n8n.emit import emit as emit_n8n

REPO = Path(__file__).resolve().parents[3]
CANON_YAML = REPO / "content" / "playbooks" / "network_security" / "playbook.cacao.yaml"
EXAMPLE = REPO / "examples" / "n8n" / "network_security"
WORKFLOW_GOLDEN = EXAMPLE / "workflow.n8n.json"
MIRROR = EXAMPLE / "playbook.cacao.yaml"


def _serialise_n8n(payload: dict) -> str:
    return json.dumps(payload, indent=2) + "\n"


def test_example_artifacts_are_committed() -> None:
    for path in (WORKFLOW_GOLDEN, MIRROR):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_mirrored_playbook_matches_canonical() -> None:
    assert MIRROR.read_bytes() == CANON_YAML.read_bytes(), (
        "examples/n8n/network_security/playbook.cacao.yaml drifted from the "
        "canonical content/playbooks/network_security/playbook.cacao.yaml. "
        "Regenerate via `./examples/n8n/network_security/regenerate.sh`."
    )


def test_n8n_workflow_matches_golden() -> None:
    playbook = parse_file(CANON_YAML)
    rendered = _serialise_n8n(emit_n8n(playbook))
    expected = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "network_security n8n workflow drifted. Regenerate via "
        "`./examples/n8n/network_security/regenerate.sh` and commit the new "
        "bytes alongside the emitter change."
    )


def test_n8n_workflow_emit_is_deterministic() -> None:
    playbook = parse_file(CANON_YAML)
    assert _serialise_n8n(emit_n8n(playbook)) == _serialise_n8n(emit_n8n(playbook))


def test_node_ids_mirror_cacao_step_ids() -> None:
    playbook_raw = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    cacao_step_ids = set(playbook_raw["workflow"].keys())
    workflow = json.loads(WORKFLOW_GOLDEN.read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in workflow["nodes"]}
    missing = cacao_step_ids - node_ids
    assert not missing, f"CACAO step ids without matching n8n node id: {sorted(missing)}"
    extra = node_ids - cacao_step_ids
    assert not extra, f"n8n node ids without matching CACAO step id: {sorted(extra)}"
    assert len(workflow["nodes"]) == len(cacao_step_ids), "duplicate node ids"
