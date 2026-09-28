"""SecOps-NG data in the legacy ``x_secops_ng`` object vs the CACAO 2.0
extension slots (#1027, part 1).

The corpus is moving its SecOps-NG data from the private ``x_secops_ng`` key
to ``playbook_extensions`` / ``step_extensions``, keyed by one extension
definition, because CACAO tooling keeps extension data and discards unknown
keys. For one release both placements are read. These tests prove the move
is safe before any content moves: for every canonical playbook, the migrated
form parses to the same model, compiles to the same bytes in all three
emitters, and — the point of the exercise — passes the official OASIS
schema under both dialects, including the one that enforces
``unevaluatedProperties``, where the legacy form fails.
"""
from __future__ import annotations

import copy
import dataclasses
import json
import uuid
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from compilers._shared.cacao_parser import (
    SECOPS_NG_EXTENSION_ID,
    CacaoSchemaError,
    CacaoSemanticError,
    ExtensionPlacementError,
    migrate_to_extensions,
    parse,
    secops_extension,
)
from compilers._shared.cacao_parser.extensions import EXTENSION_SCHEMA_URL, SECOPS_NG_EXTENSION_DEFINITION
from compilers.langgraph.emit import emit as langgraph_emit
from compilers.langgraph.state import render_module
from compilers.n8n.emit import emit as n8n_emit
from compilers.temporal.emit import emit as temporal_emit
from tools.cacao_conformance import build_validator, discover_playbooks

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTS = [Path(p) for p in discover_playbooks()]
IDS = [str(p.relative_to(REPO_ROOT / "content" / "playbooks")) for p in DOCUMENTS]


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)


def test_the_extension_id_is_reproducible_and_a_valid_identifier() -> None:
    derived = "extension-definition--" + str(
        uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/secops-ng/secops-ng-framework/extensions/x-secops-ng"))
    assert derived == SECOPS_NG_EXTENSION_ID
    assert SECOPS_NG_EXTENSION_DEFINITION["schema"] == EXTENSION_SCHEMA_URL
    assert EXTENSION_SCHEMA_URL.endswith("content-model/x-secops-ng.extension.schema.json")


@pytest.mark.parametrize("path", DOCUMENTS, ids=IDS)
def test_the_migrated_form_is_equivalent_and_officially_conformant(path: Path) -> None:
    legacy = _load(path)
    migrated = migrate_to_extensions(legacy)
    assert "x_secops_ng" not in migrated
    assert all("x_secops_ng" not in s for s in migrated["workflow"].values())

    a, b = parse(copy.deepcopy(legacy)), parse(copy.deepcopy(migrated))
    differing = [f.name for f in dataclasses.fields(a) if getattr(a, f.name) != getattr(b, f.name)]
    assert differing == ["extension_definitions"], differing

    assert n8n_emit(b) == n8n_emit(a)
    assert temporal_emit(b) == temporal_emit(a)
    assert langgraph_emit(b).to_dict() == langgraph_emit(a).to_dict()
    assert render_module(b) == render_module(a)

    for dialect in ("declared", "2020-12"):
        errors = [e.message for e in build_validator(dialect).iter_errors(migrated)]
        assert not errors, f"{dialect}: {errors[:3]}"


def test_the_legacy_form_is_what_the_strict_dialect_rejects() -> None:
    """The baseline this moves away from: the root x_secops_ng alone."""
    legacy = _load(DOCUMENTS[0])
    messages = [e.message for e in build_validator("2020-12").iter_errors(legacy)]
    assert messages and all("x_secops_ng" in m for m in messages)


def _extension_validator() -> Draft202012Validator:
    ext = json.loads((REPO_ROOT / "content-model/x-secops-ng.extension.schema.json").read_text(encoding="utf-8"))
    model = json.loads((REPO_ROOT / "content-model/playbook.schema.json").read_text(encoding="utf-8"))
    base = EXTENSION_SCHEMA_URL.rsplit("/", 1)[0]
    registry = Registry().with_resources([
        (ext["$id"], Resource.from_contents(ext)),
        (f"{base}/playbook.schema.json", Resource.from_contents(model)),
        (model["$id"], Resource.from_contents(model)),
    ])
    return Draft202012Validator(ext, registry=registry)


@pytest.mark.parametrize("path", DOCUMENTS, ids=IDS)
def test_every_payload_matches_the_published_extension_schema(path: Path) -> None:
    migrated = migrate_to_extensions(_load(path))
    validator = _extension_validator()
    payloads = [migrated["playbook_extensions"][SECOPS_NG_EXTENSION_ID]] + [
        s["step_extensions"][SECOPS_NG_EXTENSION_ID]
        for s in migrated["workflow"].values() if SECOPS_NG_EXTENSION_ID in s.get("step_extensions", {})]
    for payload in payloads:
        assert not list(validator.iter_errors(payload)), payload


def _phishing() -> dict:
    return _load(REPO_ROOT / "content/playbooks/phishing_triage/playbook.cacao.json")


def test_migration_is_idempotent_and_keeps_other_tools_extensions() -> None:
    doc = _phishing()
    first_step = next(iter(doc["workflow"]))
    roaster = "extension-definition--00000000-0000-4000-8000-000000000001"
    doc["workflow"][first_step]["step_extensions"] = {roaster: {"x": 1, "y": 2}}
    migrated = migrate_to_extensions(doc)
    assert migrate_to_extensions(migrated) == migrated
    assert migrated["workflow"][first_step]["step_extensions"][roaster] == {"x": 1, "y": 2}
    step = parse(copy.deepcopy({**migrated, "extension_definitions": {
        **migrated["extension_definitions"], roaster: {**SECOPS_NG_EXTENSION_DEFINITION, "name": "roaster"}}})).workflow[first_step]
    assert step.extra["step_extensions"] == {roaster: {"x": 1, "y": 2}}   # foreign extension kept for emitters
    assert SECOPS_NG_EXTENSION_ID not in step.extra["step_extensions"]     # ours is modelled, not duplicated


def test_both_placements_on_one_object_are_rejected() -> None:
    doc = migrate_to_extensions(_phishing())
    with pytest.raises(ExtensionPlacementError):
        secops_extension({**doc, "x_secops_ng": doc["playbook_extensions"][SECOPS_NG_EXTENSION_ID]})
    both_root = {**doc, "x_secops_ng": doc["playbook_extensions"][SECOPS_NG_EXTENSION_ID]}
    with pytest.raises((CacaoSchemaError, CacaoSemanticError)):
        parse(both_root)
    both_step = copy.deepcopy(doc)
    sid = next(s for s, st in both_step["workflow"].items() if SECOPS_NG_EXTENSION_ID in st.get("step_extensions", {}))
    both_step["workflow"][sid]["x_secops_ng"] = both_step["workflow"][sid]["step_extensions"][SECOPS_NG_EXTENSION_ID]
    with pytest.raises((CacaoSchemaError, CacaoSemanticError)):
        parse(both_step)


def test_a_payload_keyed_by_an_undeclared_extension_is_rejected() -> None:
    doc = migrate_to_extensions(_phishing())
    del doc["extension_definitions"][SECOPS_NG_EXTENSION_ID]
    with pytest.raises(CacaoSemanticError, match="does not declare it"):
        parse(doc)


def test_a_playbook_with_no_secops_ng_data_is_rejected() -> None:
    doc = _phishing()
    del doc["x_secops_ng"]
    with pytest.raises((CacaoSchemaError, CacaoSemanticError)):
        parse(doc)
