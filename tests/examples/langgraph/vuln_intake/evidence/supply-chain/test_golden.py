"""F-CP-03 EXTEND-tests-goldens (LangGraph) — byte-parity replay golden.

Pins the committed supply-chain worked example for the LangGraph target
under ``examples/langgraph/vuln_intake/evidence/supply-chain/`` against
a fresh re-emission driven through the LangGraph node adapter at
:func:`compilers.langgraph.evidence.emit_supply_chain_artifact_node`.

The committed snapshot — ``dependencies-snapshot.json`` — is the
human-friendly rename of the deterministic ``<artifact_id>.json`` file
the shared emitter writes. This test re-runs the node adapter the way
an integrator's ``StateGraph`` would (state mapping in, partial state
update out), schema-validates the result against
``schemas/evidence/supply-chain.schema.json`` (with promoted sibling
vocabularies resolved), and asserts byte-equality with the committed
snapshot.

Coverage axes (mirroring the F-CP-04 / F-CP-05 EXTEND-tests-goldens
contract on the supply-chain stream's specific invariants):

1. **Schema-conformant emit.**
2. **Byte-parity with the committed example.** Regenerate via
   ``PYTHONPATH=. python examples/langgraph/vuln_intake/evidence/supply-chain/regenerate.py``.
3. **Sovereignty atom + NIS2 Article 22 anchor.**
4. **artifact_id determinism.**

Sibling note: ``CTX`` below is kept byte-identical to ``CTX`` in
``examples/langgraph/vuln_intake/evidence/supply-chain/regenerate.py``.
The filename in that path contains a hyphen, so the regenerate module
cannot be imported by ``import`` — the context is duplicated here on
purpose and the byte-parity assertion catches drift on either side.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from compilers._shared.evidence import (
    Aggregates,
    Attestation,
    Dependency,
    SovereigntyClassification,
    SupplyChainContext,
    derive_supply_chain_artifact_id,
)
from compilers.langgraph.evidence import emit_supply_chain_artifact_node

REPO = Path(__file__).resolve().parents[6]
SCHEMAS = REPO / "schemas"
SUPPLY_CHAIN_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "supply-chain.schema.json"
DEPENDENCY_KIND_SCHEMA = SCHEMAS / "supply_chain_dependency_kind.json"
RESIDENCY_SCHEMA = SCHEMAS / "sovereignty_residency.json"
OWNERSHIP_SCHEMA = SCHEMAS / "sovereignty_ownership.json"
BAND_SCHEMA = SCHEMAS / "sovereignty_band.json"
ATTESTATION_STATE_SCHEMA = SCHEMAS / "attestation_state.json"

EXAMPLE_DIR = REPO / "examples" / "langgraph" / "vuln_intake" / "evidence" / "supply-chain"
GOLDEN = EXAMPLE_DIR / "dependencies-snapshot.json"


# Mirrors CTX in examples/langgraph/vuln_intake/evidence/supply-chain/regenerate.py.
CTX = SupplyChainContext(
    workflow_id="vulnerability_triage",
    execution_id="langgraph:vuln_intake_example_0001",
    regulation_refs=("nis2:art-21-2-d", "nis2:art-22"),
    control_refs=(
        "control.supplier_inventory@v1",
        "control.provider_attestation@v1",
    ),
    dependencies=(
        Dependency(
            provider_id="provider.cve_feed_eu@v1",
            kind="data_feed",
            call_count=4,
            version="2026-06-07",
            sovereignty_classification=SovereigntyClassification(
                residency="eu",
                ownership="eu_owned",
                sovereignty_band="sovereign",
                sub_processor_chain=(),
                band_rationale=(
                    "EU-owned vulnerability data feed operating wholly "
                    "inside an EU Member State; no declared "
                    "sub-processors."
                ),
                kb_ref="supplier-kb://provider-eu-sovereign-cve/2026-Q2",
            ),
            attestation=Attestation(
                state="effective",
                last_reattested_at=datetime(
                    2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
                next_due_at=datetime(
                    2027, 4, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
                attestation_ref="atte-2026Q2-0001",
            ),
            risk_notes=(
                "Primary vulnerability-data source for triage "
                "enrichment in the vuln_intake worked example."
            ),
        ),
        Dependency(
            provider_id="provider.llm_inference_non_eu@v1",
            kind="ai_provider",
            call_count=1,
            sovereignty_classification=SovereigntyClassification(
                residency="non_eu",
                ownership="non_eu_owned",
                sovereignty_band="non_eu",
                band_rationale=(
                    "Non-EU LLM used for the optional risk-summary "
                    "generation branch; ownership chain not in scope "
                    "for the sovereign band."
                ),
                kb_ref="supplier-kb://provider-non-eu-llm/2026-Q2",
            ),
            attestation=Attestation(
                state="overdue",
                last_reattested_at=datetime(
                    2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
                next_due_at=datetime(
                    2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
                ),
            ),
            risk_notes=(
                "Surfaced as overdue per supplier-KB cadence; the "
                "vuln_intake playbook can degrade gracefully to "
                "non-AI risk summarisation."
            ),
        ),
    ),
    owner_role="supplier-governance@example.org",
    owner_assigned_at="2026-01-15",
    captured_at=datetime(2026, 6, 7, 6, 0, 0, tzinfo=timezone.utc),
    source_url="https://example.org/runs/vuln_intake_example_0001",
    aggregates=Aggregates(
        total_providers=2,
        sovereign_count=1,
        eu_hosted_count=1,
        non_eu_count=1,
        ai_provider_count=1,
    ),
)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    """Draft 2020-12 validator with the promoted-vocabulary siblings pinned.

    See the n8n sibling in this directory for the rationale.
    """
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


def _replay(output_dir: Path) -> tuple[Path, str]:
    """Drive the LangGraph node adapter exactly like a StateGraph would.

    The node takes a state mapping and returns a partial state update
    carrying the absolute artifact path and the deterministic
    artifact id.
    """
    update = emit_supply_chain_artifact_node(
        {
            "supply_chain_context": CTX,
            "evidence_output_dir": str(output_dir),
        }
    )
    return Path(update["supply_chain_artifact_path"]), update[
        "supply_chain_artifact_id"
    ]


# --------------------------------------------------------------------------- #
# Fixture-on-disk guardrails                                                  #
# --------------------------------------------------------------------------- #


def test_committed_example_exists() -> None:
    assert GOLDEN.exists(), f"missing committed example: {GOLDEN}"
    assert GOLDEN.stat().st_size > 0, f"empty committed example: {GOLDEN}"


# --------------------------------------------------------------------------- #
# Coverage axis 1: schema-conformant emit                                     #
# --------------------------------------------------------------------------- #


def test_committed_example_validates_against_schema() -> None:
    _validator().validate(_load_json(GOLDEN))


def test_replay_artifact_validates_against_schema(tmp_path: Path) -> None:
    """Schema cross-check before byte-comparison."""
    written, _ = _replay(tmp_path)
    _validator().validate(_load_json(written))


# --------------------------------------------------------------------------- #
# Coverage axis 2: byte-parity replay against the committed example           #
# --------------------------------------------------------------------------- #


def _drift_hint() -> str:
    return (
        "LangGraph supply-chain example drifted from a fresh adapter "
        "replay. If the change is intentional, regenerate the example "
        "via `PYTHONPATH=. python examples/langgraph/vuln_intake/"
        "evidence/supply-chain/regenerate.py` and commit the new bytes "
        "alongside the emitter / adapter change."
    )


def test_langgraph_replay_matches_committed_example(tmp_path: Path) -> None:
    """Replay the LangGraph node adapter, then assert byte-equality."""
    written, _ = _replay(tmp_path)
    assert written.read_bytes() == GOLDEN.read_bytes(), _drift_hint()


# --------------------------------------------------------------------------- #
# Coverage axis 3: sovereignty atom + NIS2 Article 22 anchor                  #
# --------------------------------------------------------------------------- #


def test_committed_example_carries_sovereignty_classification_atom() -> None:
    """Every dependency carries the sovereignty atom drawn from the
    promoted vocabularies."""
    record = _load_json(GOLDEN)
    assert record["dependencies"], "expected a non-empty dependency surface"
    band_enum = set(_load_json(BAND_SCHEMA)["enum"])
    residency_enum = set(_load_json(RESIDENCY_SCHEMA)["enum"])
    ownership_enum = set(_load_json(OWNERSHIP_SCHEMA)["enum"])
    for entry in record["dependencies"]:
        cls = entry["sovereignty_classification"]
        assert cls["residency"] in residency_enum
        assert cls["ownership"] in ownership_enum
        assert cls["sovereignty_band"] in band_enum


def test_committed_example_carries_nis2_art_22() -> None:
    """G-02 Cooperation-Group anchor must be present on the artifact."""
    record = _load_json(GOLDEN)
    assert "nis2:art-22" in record["regulation_refs"]


# --------------------------------------------------------------------------- #
# Coverage axis 4: artifact_id determinism                                    #
# --------------------------------------------------------------------------- #


def test_artifact_id_is_deterministic_sha256(tmp_path: Path) -> None:
    """``artifact_id`` matches
    SHA-256(``<workflow_id>|<execution_id>|<captured_at>``); the fresh
    node emission re-derives the same id and surfaces it on the
    partial state update under ``supply_chain_artifact_id``.
    """
    expected = derive_supply_chain_artifact_id(
        CTX.workflow_id, CTX.execution_id, CTX.captured_at
    )
    record = _load_json(GOLDEN)
    assert record["artifact_id"] == expected

    written, artifact_id = _replay(tmp_path)
    assert written.stem == expected
    assert artifact_id == expected
    assert _load_json(written)["artifact_id"] == expected
