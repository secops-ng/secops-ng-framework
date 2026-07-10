"""F-WF-NETWORK-SECURITY EXTEND — Temporal worked example for network_security.

Pins the Temporal end of the three-target contract for the
``network_security`` playbook (NIS2 Art. 21(2)(e)). The committed
``examples/temporal/network_security/workflow.temporal.py`` is the
Temporal compiler's output for the canonical CACAO playbook at
``content/playbooks/network_security/playbook.cacao.yaml``.

Activity-name <-> CACAO action-id parity is verified — every CACAO
action step gets exactly one ``@activity.defn`` whose docstring records
the originating ``step_id``.

Regenerate via::

    ./examples/temporal/network_security/regenerate.sh
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from compilers.temporal.emit import emit_file

REPO = Path(__file__).resolve().parents[4]
CANON_YAML = (
    REPO
    / "content"
    / "playbooks"
    / "network_security"
    / "playbook.cacao.yaml"
)
EXAMPLE = REPO / "examples" / "temporal" / "network_security"
WORKFLOW_GOLDEN = EXAMPLE / "workflow.temporal.py"
MIRRORED_CACAO = EXAMPLE / "playbook.cacao.yaml"

_ACTIVITY_STEP_TYPES = {"action"}
_ACTIVITY_DEFN_RE = re.compile(
    r"@activity\.defn\nasync def (?P<name>[A-Za-z_][A-Za-z_0-9]*)\("
    r"[^)]*\)[^:]*:\n"
    r'    """[^"]*?\n\n'
    r"    CACAO step_id: (?P<step_id>[^\n]+)\n",
    re.DOTALL,
)


# --------------------------------------------------------------------------- #
# Workflow source                                                             #
# --------------------------------------------------------------------------- #


def test_example_artifacts_are_committed() -> None:
    for path in (WORKFLOW_GOLDEN, MIRRORED_CACAO):
        assert path.exists(), f"missing example artifact: {path}"
        assert path.stat().st_size > 0, f"empty example artifact: {path}"


def test_worked_example_matches_emitter_output() -> None:
    rendered = emit_file(CANON_YAML)
    expected = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    assert rendered == expected, (
        "examples/temporal/network_security/workflow.temporal.py drifted "
        "from the Temporal emitter output. Regenerate via "
        "`./examples/temporal/network_security/regenerate.sh` and commit "
        "the new bytes."
    )


def test_mirrored_cacao_matches_canonical_source() -> None:
    assert MIRRORED_CACAO.read_bytes() == CANON_YAML.read_bytes(), (
        "examples/temporal/network_security/playbook.cacao.yaml drifted "
        "from the canonical "
        "content/playbooks/network_security/playbook.cacao.yaml. "
        "Regenerate via `./examples/temporal/network_security/regenerate.sh`."
    )


def test_emit_is_deterministic() -> None:
    assert emit_file(CANON_YAML) == emit_file(CANON_YAML)


# --------------------------------------------------------------------------- #
# Activity-name <-> CACAO action-id parity                                    #
# --------------------------------------------------------------------------- #


def _action_step_ids_from_cacao() -> list[str]:
    playbook = yaml.safe_load(CANON_YAML.read_text(encoding="utf-8"))
    return [
        step_id
        for step_id, step in playbook["workflow"].items()
        if step.get("type") in _ACTIVITY_STEP_TYPES
    ]


def _activity_blocks_from_stub() -> list[tuple[str, str]]:
    text = WORKFLOW_GOLDEN.read_text(encoding="utf-8")
    return [(m.group("name"), m.group("step_id")) for m in _ACTIVITY_DEFN_RE.finditer(text)]


def test_activity_names_mirror_cacao_action_ids() -> None:
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
