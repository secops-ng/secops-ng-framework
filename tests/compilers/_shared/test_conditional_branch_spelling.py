"""Conditional-step branch spelling: ``on_true`` / ``on_false`` vs the legacy
``on_success`` / ``on_failure``.

CACAO 2.0 (4.8, 4.9) names an if-condition's or while-condition's branches
``on_true`` and ``on_false``. It also defines ``on_success`` / ``on_failure``
on *every* step, where they mean the step's own execution outcome — so the
legacy spelling on a conditional step was not a synonym, it was a different
field that happened to be read as the branch. The canonical corpus now uses
the CACAO names. The parser accepts both spellings on conditional steps for
one release and lands them on the same AST fields, which is what keeps every
emitter's output unchanged; these tests pin that, and the two ways a document
can be ambiguous.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from compilers._shared.cacao_parser import CacaoSemanticError, StepType, parse
from compilers.langgraph.emit import emit as langgraph_emit
from compilers.langgraph.state import render_module
from compilers.n8n.emit import emit as n8n_emit
from compilers.temporal.emit import emit as temporal_emit

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "vuln_intake.cacao.json"


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)


def _conditional_ids(data: dict) -> list[str]:
    return [
        sid
        for sid, step in data["workflow"].items()
        if step.get("type") in ("if-condition", "while-condition")
    ]


def _to_legacy(data: dict) -> dict:
    """Rewrite every conditional step back to the legacy spelling."""
    legacy = deepcopy(data)
    for sid in _conditional_ids(legacy):
        step = legacy["workflow"][sid]
        if "on_true" in step:
            step["on_success"] = step.pop("on_true")
        if "on_false" in step:
            step["on_failure"] = step.pop("on_false")
    return legacy


def _canonical_with_conditionals() -> list[Path]:
    roots = sorted((REPO_ROOT / "content" / "playbooks").glob("*/playbook.cacao.json"))
    roots += sorted((REPO_ROOT / "content" / "playbooks").glob("*/playbook.cacao.yaml"))
    roots += sorted((REPO_ROOT / "content" / "playbooks").glob("*.cacao.yaml"))
    return [p for p in roots if "_template" not in p.parts and _conditional_ids(_load(p))]


CANONICAL = _canonical_with_conditionals()


@pytest.fixture()
def data() -> dict:
    return _load(FIXTURE)


@pytest.fixture()
def gate_id(data: dict) -> str:
    (sid,) = _conditional_ids(data)
    return sid


def test_on_true_and_on_false_land_on_the_branch_fields(data: dict, gate_id: str) -> None:
    raw = data["workflow"][gate_id]
    step = parse(data).workflow[gate_id]
    assert step.type is StepType.IF_CONDITION
    assert step.on_success == raw["on_true"]
    assert step.on_failure == raw["on_false"]


def test_legacy_spelling_still_parses_to_the_same_fields(data: dict, gate_id: str) -> None:
    current = parse(data).workflow[gate_id]
    legacy = parse(_to_legacy(data)).workflow[gate_id]
    assert (legacy.on_success, legacy.on_failure) == (current.on_success, current.on_failure)


def test_branch_names_do_not_leak_into_extra() -> None:
    """``condition`` stays in ``extra`` (the n8n emitter reads it there); the
    branch names are modelled, so they must not also ride along in ``extra``.
    Checked across the canonical corpus, where every conditional step now
    carries a condition."""
    for path in CANONICAL:
        playbook = parse(_load(path))
        for sid in _conditional_ids(_load(path)):
            step = playbook.workflow[sid]
            assert "condition" in step.extra, f"{path.name}:{sid}"
            for key in ("on_true", "on_false", "on_success", "on_failure"):
                assert key not in step.extra, f"{path.name}:{sid} leaks {key}"


@pytest.mark.parametrize(("new", "legacy"), [("on_true", "on_success"), ("on_false", "on_failure")])
def test_both_spellings_on_one_step_is_ambiguous(
    data: dict, gate_id: str, new: str, legacy: str
) -> None:
    step = data["workflow"][gate_id]
    step[legacy] = step[new]
    with pytest.raises(CacaoSemanticError, match=f"both {new} and {legacy}"):
        parse(data)


def test_on_true_on_a_non_conditional_step_is_rejected(data: dict) -> None:
    action_id = next(sid for sid, s in data["workflow"].items() if s["type"] == "action")
    data["workflow"][action_id]["on_true"] = data["workflow_start"]
    with pytest.raises(CacaoSemanticError, match="only defined for if-condition"):
        parse(data)


def test_dangling_branch_is_reported_under_the_name_the_author_used(
    data: dict, gate_id: str
) -> None:
    data["workflow"][gate_id]["on_true"] = "action--00000000-0000-4000-8000-00000000dead"
    with pytest.raises(CacaoSemanticError, match="on_true ->"):
        parse(data)




def test_canonical_corpus_uses_only_the_cacao_names() -> None:
    assert CANONICAL, "expected canonical playbooks with conditional steps"
    offenders = []
    for p in CANONICAL:
        data = _load(p)
        for sid in _conditional_ids(data):
            step = data["workflow"][sid]
            if {"on_success", "on_failure"} & set(step) or "condition" not in step:
                offenders.append(f"{p.relative_to(REPO_ROOT)}:{sid}")
    assert not offenders, f"conditional steps missing condition or using legacy names: {offenders}"


@pytest.mark.parametrize("path", CANONICAL, ids=lambda p: str(p.relative_to(REPO_ROOT / "content" / "playbooks")))
def test_every_emitter_compiles_both_spellings_identically(path: Path) -> None:
    """The one-release compatibility promise, checked end to end: rewriting a
    canonical playbook's conditional steps back to the legacy spelling changes
    nothing any of the three emitters produces."""
    current = parse(_load(path))
    legacy = parse(_to_legacy(_load(path)))
    assert n8n_emit(legacy) == n8n_emit(current)
    assert temporal_emit(legacy) == temporal_emit(current)
    assert langgraph_emit(legacy).to_dict() == langgraph_emit(current).to_dict()
    assert render_module(legacy) == render_module(current)
