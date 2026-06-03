"""Drift guard for the ``examples/temporal/alert-triage/`` worked example.

The canonical alert-triage CACAO source is YAML at
``content/playbooks/alert-triage.cacao.yaml``. The worked example commits:

* ``playbook.cacao.json`` — byte-deterministic JSON mirror of the YAML
  source (the Temporal emitter consumes JSON via the CACAO parser);
* ``workflow.temporal.py`` — emitted Temporal stub.

This test re-runs the YAML→JSON mirror and the Temporal emitter, then
asserts the committed files match byte-for-byte. An activity-name ↔
CACAO action-id parity check enforces the one-to-one mirroring contract
the README documents.

Regenerate via::

    ./examples/temporal/alert-triage/regenerate.sh

Mirrors the langgraph alert-triage and per-target temporal drift guards
(phishing-triage, identity-compromise, cloud-misconfiguration).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from compilers.temporal.emit import emit_file

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_DIR = REPO_ROOT / "examples" / "temporal" / "alert-triage"
CANON_YAML = REPO_ROOT / "content" / "playbooks" / "alert-triage.cacao.yaml"
MIRRORED_CACAO = EXAMPLE_DIR / "playbook.cacao.json"
WORKED_EXAMPLE = EXAMPLE_DIR / "workflow.temporal.py"

_ACTIVITY_STEP_TYPES = {"action"}
_ACTIVITY_DEFN_RE = re.compile(
    r"@activity\.defn\nasync def (?P<name>[A-Za-z_][A-Za-z_0-9]*)\("
    r"[^)]*\)[^:]*:\n"
    r'    """[^"]*?\n\n'
    r"    CACAO step_id: (?P<step_id>[^\n]+)\n",
    re.DOTALL,
)


def _serialise_json_mirror(data) -> str:
    """Canonical YAML→JSON mirror serialisation used by ``regenerate.sh``."""
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------- #
# Sanity                                                                      #
# --------------------------------------------------------------------------- #


def test_committed_artefacts_exist() -> None:
    for path in (CANON_YAML, MIRRORED_CACAO, WORKED_EXAMPLE):
        assert path.exists(), f"missing worked-example artefact: {path}"
        assert path.stat().st_size > 0, f"empty worked-example artefact: {path}"


# --------------------------------------------------------------------------- #
# Drift guards                                                                #
# --------------------------------------------------------------------------- #


def test_json_mirror_matches_yaml_source() -> None:
    """``playbook.cacao.json`` must round-trip from the canonical YAML."""
    data = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    rendered = _serialise_json_mirror(data)
    expected = MIRRORED_CACAO.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/temporal/alert-triage/playbook.cacao.json drifted from the "
        "canonical YAML source. Regenerate via "
        "`./examples/temporal/alert-triage/regenerate.sh` and commit the new "
        "bytes."
    )


def test_worked_example_matches_emitter_output() -> None:
    rendered = emit_file(MIRRORED_CACAO)
    expected = WORKED_EXAMPLE.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/temporal/alert-triage/workflow.temporal.py drifted from the "
        "Temporal emitter output. Regenerate via "
        "`./examples/temporal/alert-triage/regenerate.sh` and commit the new "
        "bytes."
    )


# --------------------------------------------------------------------------- #
# Activity ↔ CACAO action-id parity                                           #
# --------------------------------------------------------------------------- #


def _action_step_ids_from_cacao() -> list[str]:
    playbook = json.loads(MIRRORED_CACAO.read_text(encoding="utf-8"))
    return [
        step_id
        for step_id, step in playbook["workflow"].items()
        if step.get("type") in _ACTIVITY_STEP_TYPES
    ]


def _activity_blocks_from_stub() -> list[tuple[str, str]]:
    """Return ``(activity_function_name, cacao_step_id)`` tuples in source order."""
    text = WORKED_EXAMPLE.read_text(encoding="utf-8")
    return [(m.group("name"), m.group("step_id")) for m in _ACTIVITY_DEFN_RE.finditer(text)]


def test_activity_names_mirror_cacao_action_ids() -> None:
    """Every CACAO action step gets exactly one ``@activity.defn`` whose
    docstring records the originating ``step_id``, and vice versa.
    """
    cacao_action_ids = set(_action_step_ids_from_cacao())
    stub_blocks = _activity_blocks_from_stub()
    stub_step_ids = {step_id for _, step_id in stub_blocks}

    missing = cacao_action_ids - stub_step_ids
    assert not missing, (
        f"CACAO action step ids without a matching Temporal activity: "
        f"{sorted(missing)}"
    )
    extra = stub_step_ids - cacao_action_ids
    assert not extra, (
        f"Temporal activities without a matching CACAO action step id: "
        f"{sorted(extra)}"
    )
    assert len(stub_blocks) == len(cacao_action_ids), (
        "duplicate @activity.defn for the same CACAO step id in the stub"
    )

    function_names = [name for name, _ in stub_blocks]
    assert len(function_names) == len(set(function_names)), (
        "duplicate activity function names in the stub"
    )


def test_emit_is_deterministic() -> None:
    assert emit_file(MIRRORED_CACAO) == emit_file(MIRRORED_CACAO)
