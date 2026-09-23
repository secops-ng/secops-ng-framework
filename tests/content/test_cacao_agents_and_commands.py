"""Agents and commands on action steps (#1010 item 5, part 1).

The official OASIS CACAO 2.0 schema requires every action step to carry an
``agent`` (a reference into the playbook's ``agent_definitions``) and a
non-empty ``commands`` list. This suite pins the representation the
catalogue uses for the first of those, and for the commands of bound steps:

* every canonical document — and the ``_template`` — declares exactly one
  agent, the ``group`` "Security operations team", under one fixed id;
* every action step names that agent;
* every bound step (one with ``x_secops_ng.core_body``) carries exactly one
  command, of the open-vocabulary type ``secops-ng-primitive``, whose
  ``command`` is the core_body primitive's dotted path;
* no unbound step claims a ``secops-ng-primitive`` command.

The command duplicates the primitive path on purpose — it is what CACAO
tooling reads — and the compilers keep compiling ``core_body``. The equality
check is what stops the two copies drifting apart.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tools.cacao_conformance import discover_playbooks

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / "content" / "playbooks" / "_template" / "playbook.cacao.yaml"

AGENT_ID = "group--9479ad47-df96-5a3c-831a-f668158e5b9e"
AGENT = {"type": "group", "name": "Security operations team"}
PRIMITIVE_COMMAND = "secops-ng-primitive"


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)


DOCUMENTS = [Path(p) for p in discover_playbooks()]
IDS = [str(p.relative_to(REPO_ROOT / "content" / "playbooks")) for p in DOCUMENTS]


def _actions(data: dict) -> dict[str, dict]:
    return {sid: s for sid, s in data["workflow"].items() if s.get("type") == "action"}


def _core_body(step: dict) -> dict | None:
    return (step.get("x_secops_ng") or {}).get("core_body")


def test_the_agent_id_is_a_valid_cacao_identifier() -> None:
    """uuid5 of a fixed URL — deterministic, and version 5 / RFC 4122
    variant, as the official identifier pattern requires."""
    import re
    import uuid

    derived = "group--" + str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            "https://github.com/secops-ng/secops-ng-framework/agents/security-operations-team",
        )
    )
    assert derived == AGENT_ID
    assert re.match(
        r"^[a-z][a-z0-9-]+[a-z0-9]--[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}"
        r"-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$",
        AGENT_ID,
    )


@pytest.mark.parametrize("path", DOCUMENTS + [TEMPLATE], ids=IDS + ["_template"])
def test_one_agent_declared_and_every_action_names_it(path: Path) -> None:
    data = _load(path)
    assert data.get("agent_definitions") == {AGENT_ID: AGENT}
    missing = [sid for sid, s in _actions(data).items() if s.get("agent") != AGENT_ID]
    assert not missing, f"action steps without the catalogue agent: {missing}"


@pytest.mark.parametrize("path", DOCUMENTS, ids=IDS)
def test_bound_steps_carry_exactly_their_primitive_as_a_command(path: Path) -> None:
    problems = []
    for sid, step in _actions(_load(path)).items():
        body = _core_body(step)
        commands = step.get("commands")
        if body:
            expected = [{"type": PRIMITIVE_COMMAND, "command": body["primitive"]}]
            if commands != expected:
                problems.append(f"{sid}: commands {commands!r} != {expected!r}")
        elif commands and any(c.get("type") == PRIMITIVE_COMMAND for c in commands):
            problems.append(f"{sid}: unbound step claims a {PRIMITIVE_COMMAND} command")
    assert not problems, "\n".join(problems)
