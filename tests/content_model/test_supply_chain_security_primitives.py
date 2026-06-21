"""F-WF-SCS CORE-PRIM primitives: shape + happy-path + negative tests.

Pins the contract of:

* ``content.playbooks.supply_chain_security.primitives.assess.assess_supplier_signal``
  — canonicalisation of the operator-supplied raw supply-chain signal
  envelope into the closed assessment block.
* ``content.playbooks.supply_chain_security.primitives.artifact.build_supply_chain_evidence_artifact``
  — round-trip through the F-CP-03 shared emitter, including the
  supply-chain-security-side join (the assessed supplier handle MUST
  appear in the declared dependency surface).

Per-target compile-target fan-out and byte-parity goldens against
``examples/{n8n,temporal,langgraph}/supply_chain_security/`` are out
of scope (CORE-FANOUT sibling).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from content.playbooks.supply_chain_security.primitives import (
    InvalidSupplierSignalError,
    InvalidSupplyChainEvidenceArtifactError,
    assess_supplier_signal,
    build_supply_chain_evidence_artifact,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
SUPPLY_CHAIN_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "supply-chain.schema.json"
DEPENDENCY_KIND_SCHEMA = SCHEMAS / "supply_chain_dependency_kind.json"
RESIDENCY_SCHEMA = SCHEMAS / "sovereignty_residency.json"
OWNERSHIP_SCHEMA = SCHEMAS / "sovereignty_ownership.json"
BAND_SCHEMA = SCHEMAS / "sovereignty_band.json"
ATTESTATION_STATE_SCHEMA = SCHEMAS / "attestation_state.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    schema = _load_json(SUPPLY_CHAIN_EVIDENCE_SCHEMA)
    extras = {
        "https://secops-ng.org/schemas/supply_chain_dependency_kind.json": (
            _load_json(DEPENDENCY_KIND_SCHEMA)
        ),
        "https://secops-ng.org/schemas/sovereignty_residency.json": _load_json(
            RESIDENCY_SCHEMA
        ),
        "https://secops-ng.org/schemas/sovereignty_ownership.json": _load_json(
            OWNERSHIP_SCHEMA
        ),
        "https://secops-ng.org/schemas/sovereignty_band.json": _load_json(
            BAND_SCHEMA
        ),
        "https://secops-ng.org/schemas/attestation_state.json": _load_json(
            ATTESTATION_STATE_SCHEMA
        ),
    }
    registry = Registry().with_resources(
        (uri, Resource(contents=doc, specification=DRAFT202012))
        for uri, doc in extras.items()
    )
    return Draft202012Validator(schema, registry=registry)


# ---------------------------------------------------------------------------
# assess_supplier_signal
# ---------------------------------------------------------------------------


def _minimal_assessment_kwargs() -> dict:
    return dict(
        signal_class="sbom_diff",
        verdict="watch",
        affected_supplier_handle="provider.upstream_dep_eu@v1",
        received_at="2026-06-21T12:00:00Z",
        affected_component_set=[
            "pkg:pypi/foo@1.2.3",
            "pkg:pypi/foo@1.2.3",  # dedup
            "pkg:npm/bar@2.0.0",
        ],
        signal_id="sig-2026-06-21-001",
        scoring_notes="One direct dependency drifted to a non-attested upstream.",
    )


def test_assess_supplier_signal_canonical_shape() -> None:
    out = assess_supplier_signal(**_minimal_assessment_kwargs())
    assert out["verdict"] == "watch"
    assert out["affected_supplier_handle"] == "provider.upstream_dep_eu@v1"
    # dedup + sorted
    assert out["affected_component_set"] == [
        "pkg:npm/bar@2.0.0",
        "pkg:pypi/foo@1.2.3",
    ]
    assert out["received_at"] == "2026-06-21T12:00:00Z"
    assert out["signal_class"] == "sbom_diff"
    assert out["signal_id"] == "sig-2026-06-21-001"
    assert "scoring_notes" in out


def test_assess_supplier_signal_replay_byte_identical() -> None:
    a = assess_supplier_signal(**_minimal_assessment_kwargs())
    b = assess_supplier_signal(**_minimal_assessment_kwargs())
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_assess_supplier_signal_no_impact_with_empty_components() -> None:
    out = assess_supplier_signal(
        signal_class="upstream_advisory",
        verdict="no_impact",
        affected_supplier_handle="provider.cve_feed_eu@v1",
        received_at="2026-06-21T12:00:00Z",
        affected_component_set=None,
    )
    assert out["verdict"] == "no_impact"
    assert out["affected_component_set"] == []
    assert "signal_id" not in out


@pytest.mark.parametrize(
    "field, override",
    [
        ("signal_class", "free_text_class"),
        ("verdict", "unknown"),
        ("affected_supplier_handle", "Doe John <john@example.com>"),
        ("received_at", "2026/06/21 12:00:00"),
        ("affected_component_set", ["not a purl"]),
    ],
)
def test_assess_supplier_signal_rejects_bad_inputs(
    field: str, override
) -> None:
    kwargs = _minimal_assessment_kwargs()
    kwargs[field] = override
    with pytest.raises(InvalidSupplierSignalError):
        assess_supplier_signal(**kwargs)


# ---------------------------------------------------------------------------
# build_supply_chain_evidence_artifact
# ---------------------------------------------------------------------------


def _dep(provider: str = "provider.upstream_dep_eu@v1") -> dict:
    return {
        "provider_id": provider,
        "kind": "software_dependency",
        "call_count": 1,
        "version": "1.2.3",
        "sovereignty_classification": {
            "residency": "eu",
            "ownership": "eu_owned",
            "sovereignty_band": "sovereign",
            "sub_processor_chain": [],
            "band_rationale": (
                "EU-owned provider operating wholly inside an EU Member "
                "State; no declared sub-processors."
            ),
        },
        "attestation": {
            "state": "effective",
            "last_reattested_at": "2026-06-01T00:00:00Z",
            "next_due_at": "2027-06-01T00:00:00Z",
        },
    }


def _build_kwargs(**overrides) -> dict:
    kwargs = dict(
        workflow_id="supply_chain_security",
        execution_id="run-2026-06-21-001",
        regulation_refs=["nis2:art-21-2-d"],
        control_refs=["control.supplier_inventory@v1"],
        assessment=assess_supplier_signal(**_minimal_assessment_kwargs()),
        dependencies=[_dep()],
        owner_role="supplier_inventory_owner",
        owner_assigned_at="2026-01-15",
        captured_at="2026-06-21T12:00:05Z",
        source_url="https://runs.example.org/scs/2026-06-21-001",
    )
    kwargs.update(overrides)
    return kwargs


def test_build_artifact_renders_and_schema_validates() -> None:
    record = build_supply_chain_evidence_artifact(**_build_kwargs())
    errs = sorted(_validator().iter_errors(record), key=lambda e: list(e.path))
    assert errs == [], [e.message for e in errs]
    assert record["schema_version"] == "1.0.0"
    assert record["stream"] == "supply-chain"
    assert record["workflow_id"] == "supply_chain_security"
    assert record["regulation_refs"] == ["nis2:art-21-2-d"]
    assert len(record["dependencies"]) == 1
    assert record["dependencies"][0]["provider_id"] == (
        "provider.upstream_dep_eu@v1"
    )


def test_build_artifact_artifact_id_is_deterministic() -> None:
    a = build_supply_chain_evidence_artifact(**_build_kwargs())
    b = build_supply_chain_evidence_artifact(**_build_kwargs())
    assert a["artifact_id"] == b["artifact_id"]
    c = build_supply_chain_evidence_artifact(
        **_build_kwargs(captured_at="2026-06-21T12:00:06Z")
    )
    assert c["artifact_id"] != a["artifact_id"]


def test_build_artifact_rejects_orphan_supplier_handle() -> None:
    # Signal points at a supplier that is not declared as a dependency.
    bad = _build_kwargs(
        dependencies=[_dep(provider="provider.other_dep_eu@v1")],
    )
    with pytest.raises(InvalidSupplyChainEvidenceArtifactError) as exc:
        build_supply_chain_evidence_artifact(**bad)
    assert "not among the declared dependencies" in str(exc.value)


def test_build_artifact_rejects_bad_captured_at() -> None:
    with pytest.raises(InvalidSupplyChainEvidenceArtifactError):
        build_supply_chain_evidence_artifact(
            **_build_kwargs(captured_at="2026-06-21 12:00:05")
        )


def test_build_artifact_rejects_empty_regulation_refs() -> None:
    with pytest.raises(InvalidSupplyChainEvidenceArtifactError):
        build_supply_chain_evidence_artifact(**_build_kwargs(regulation_refs=[]))


def test_build_artifact_forwards_aggregates_when_present() -> None:
    record = build_supply_chain_evidence_artifact(
        **_build_kwargs(
            aggregates={
                "total_providers": 1,
                "sovereign_count": 1,
                "eu_hosted_count": 0,
                "non_eu_count": 0,
                "ai_provider_count": 0,
            },
        )
    )
    assert record["aggregates"]["total_providers"] == 1
    assert record["aggregates"]["sovereign_count"] == 1
