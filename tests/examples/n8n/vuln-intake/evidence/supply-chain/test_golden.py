"""F-CP-03 EXTEND-tests-goldens (n8n) — byte-parity replay golden.

Pins the committed supply-chain worked example for the n8n target under
``examples/n8n/vuln-intake/evidence/supply-chain/`` against a fresh
re-emission driven through the n8n adapter at
:func:`compilers.n8n.evidence.emit_supply_chain_artifact_n8n`.

The committed snapshot — ``dependencies-snapshot.json`` — is the
human-friendly rename of the deterministic ``<artifact_id>.json`` file
the shared emitter writes. This test re-runs the adapter against the
same JSON-native payload
``examples/n8n/vuln-intake/evidence/supply-chain/regenerate.py`` ships,
schema-validates the result against
``schemas/evidence/supply-chain.schema.json`` (with promoted sibling
vocabularies resolved), and asserts byte-equality with the committed
snapshot.

Coverage axes (mirroring the F-CP-04 / F-CP-05 EXTEND-tests-goldens
contract on the supply-chain stream's specific invariants):

1. **Schema-conformant emit.** The re-emitted artifact validates against
   the supply-chain schema before the byte comparison runs, so a shape
   regression in the n8n adapter surfaces with a precise diagnostic.
2. **Byte-parity with the committed example.** The re-emitted
   artifact's on-disk bytes match the committed
   ``dependencies-snapshot.json`` exactly. If the shared emitter or
   n8n adapter intentionally changes serialisation, the example must
   be regenerated via
   ``PYTHONPATH=. python examples/n8n/vuln-intake/evidence/supply-chain/regenerate.py``
   and the new bytes committed alongside the change.
3. **Sovereignty atom + NIS2 Article 22 anchor.** Every
   ``dependencies[*]`` carries a sovereignty-classification block drawn
   from the promoted vocabularies, and ``regulation_refs`` carries the
   ``nis2:art-22`` Cooperation-Group wire that the G-02 milestone
   reads.
4. **artifact_id determinism.** ``artifact_id`` on the committed
   record matches ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)``
   per the schema contract, and the fresh adapter emission re-derives
   the same id (the shared helper writes the file as
   ``<artifact_id>.json``).

Sibling note: ``PAYLOAD`` below is kept byte-identical to ``PAYLOAD``
in ``examples/n8n/vuln-intake/evidence/supply-chain/regenerate.py``.
The filename in that path contains a hyphen, so the regenerate module
cannot be imported by ``import`` — the payload is duplicated here on
purpose and the byte-parity assertion catches drift on either side.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from compilers.n8n.evidence import emit_supply_chain_artifact_n8n

REPO = Path(__file__).resolve().parents[6]
SCHEMAS = REPO / "schemas"
SUPPLY_CHAIN_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "supply-chain.schema.json"
DEPENDENCY_KIND_SCHEMA = SCHEMAS / "supply_chain_dependency_kind.json"
RESIDENCY_SCHEMA = SCHEMAS / "sovereignty_residency.json"
OWNERSHIP_SCHEMA = SCHEMAS / "sovereignty_ownership.json"
BAND_SCHEMA = SCHEMAS / "sovereignty_band.json"
ATTESTATION_STATE_SCHEMA = SCHEMAS / "attestation_state.json"

EXAMPLE_DIR = REPO / "examples" / "n8n" / "vuln-intake" / "evidence" / "supply-chain"
GOLDEN = EXAMPLE_DIR / "dependencies-snapshot.json"


# Mirrors PAYLOAD in examples/n8n/vuln-intake/evidence/supply-chain/regenerate.py.
# Kept byte-identical on purpose; the byte-parity test below catches drift
# on either side. Sorted keys in the on-disk record come from the shared
# emitter, not from this payload — the input is intentionally in the same
# field order an n8n Code / executeCommand node would marshal.
PAYLOAD: dict = {
    "workflow_id": "vulnerability_triage",
    "execution_id": "n8n:vuln-intake-example-0001",
    "regulation_refs": ["nis2:art-21-2-d", "nis2:art-22"],
    "control_refs": [
        "control.supplier_inventory@v1",
        "control.provider_attestation@v1",
    ],
    "dependencies": [
        {
            "provider_id": "provider.cve_feed_eu@v1",
            "kind": "data_feed",
            "call_count": 4,
            "version": "2026-06-07",
            "sovereignty_classification": {
                "residency": "eu",
                "ownership": "eu_owned",
                "sovereignty_band": "sovereign",
                "sub_processor_chain": [],
                "band_rationale": (
                    "EU-owned vulnerability data feed operating wholly "
                    "inside an EU Member State; no declared "
                    "sub-processors."
                ),
                "kb_ref": "supplier-kb://provider-eu-sovereign-cve/2026-Q2",
            },
            "attestation": {
                "state": "effective",
                "last_reattested_at": "2026-04-01T00:00:00Z",
                "next_due_at": "2027-04-01T00:00:00Z",
                "attestation_ref": "atte-2026Q2-0001",
            },
            "risk_notes": (
                "Primary vulnerability-data source for triage "
                "enrichment in the vuln-intake worked example."
            ),
        },
        {
            "provider_id": "provider.llm_inference_non_eu@v1",
            "kind": "ai_provider",
            "call_count": 1,
            "sovereignty_classification": {
                "residency": "non_eu",
                "ownership": "non_eu_owned",
                "sovereignty_band": "non_eu",
                "band_rationale": (
                    "Non-EU LLM used for the optional risk-summary "
                    "generation branch; ownership chain not in scope "
                    "for the sovereign band."
                ),
                "kb_ref": "supplier-kb://provider-non-eu-llm/2026-Q2",
            },
            "attestation": {
                "state": "overdue",
                "last_reattested_at": "2025-01-01T00:00:00Z",
                "next_due_at": "2026-01-01T00:00:00Z",
            },
            "risk_notes": (
                "Surfaced as overdue per supplier-KB cadence; the "
                "vuln-intake playbook can degrade gracefully to "
                "non-AI risk summarisation."
            ),
        },
    ],
    "owner_role": "supplier-governance@example.org",
    "owner_assigned_at": "2026-01-15",
    "captured_at": "2026-06-07T06:00:00Z",
    "source_url": "https://example.org/runs/vuln-intake-example-0001",
    "aggregates": {
        "total_providers": 2,
        "sovereign_count": 1,
        "eu_hosted_count": 1,
        "non_eu_count": 1,
        "ai_provider_count": 1,
    },
}


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    """Draft 2020-12 validator with the promoted-vocabulary siblings pinned.

    The supply-chain schema references the promoted vocabularies by
    absolute ``https://secops-ng.org/schemas/...`` URIs;
    ``jsonschema.RefResolver`` mis-resolves an in-document
    ``#/$defs/...`` pointer after following an external ``$ref`` (the
    schema hits that path on every ``dependencies[]`` entry). The
    ``referencing`` registry is the supported successor and resolves
    correctly. See ``tests/examples/supply_chain_evidence/test_golden.py``
    for the same setup.
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
    """Schema cross-check before byte-comparison.

    The acceptance criterion is explicit: replay must validate against
    ``schemas/evidence/supply-chain.schema.json`` before the byte-parity
    assertion runs, so a shape regression in the n8n adapter surfaces
    with a JSON Schema diagnostic instead of a bytes-differ message.
    """
    result = emit_supply_chain_artifact_n8n(PAYLOAD, tmp_path)
    written = Path(result["artifact_path"])
    _validator().validate(_load_json(written))


# --------------------------------------------------------------------------- #
# Coverage axis 2: byte-parity replay against the committed example           #
# --------------------------------------------------------------------------- #


def _drift_hint() -> str:
    return (
        "n8n supply-chain example drifted from a fresh adapter "
        "replay. If the change is intentional, regenerate the example "
        "via `PYTHONPATH=. python examples/n8n/vuln-intake/evidence/"
        "supply-chain/regenerate.py` and commit the new bytes alongside "
        "the emitter / adapter change."
    )


def test_n8n_replay_matches_committed_example(tmp_path: Path) -> None:
    """Replay the n8n adapter, then assert byte-equality with the example.

    The shared emitter writes ``<artifact_id>.json`` under ``tmp_path``;
    ``examples/.../regenerate.py`` copies that to the
    ``dependencies-snapshot.json`` snapshot for human-friendly diffing.
    We compare the adapter's freshly-written bytes against the
    committed snapshot bytes; the rename is a pure copy in
    ``regenerate.py`` (``shutil.copyfile``) so the on-disk bytes are
    identical at the two paths.
    """
    result = emit_supply_chain_artifact_n8n(PAYLOAD, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == GOLDEN.read_bytes(), _drift_hint()


# --------------------------------------------------------------------------- #
# Coverage axis 3: sovereignty atom + NIS2 Article 22 anchor                  #
# --------------------------------------------------------------------------- #


def test_committed_example_carries_sovereignty_classification_atom() -> None:
    """Every dependency carries a ``sovereignty_classification`` block.

    The F-CP-03 sovereign-stack constraint pinned at the byte level:
    each declared dependency must carry residency, ownership, and
    sovereignty_band drawn from the promoted vocabularies. Adapters
    must not strip or coerce the atom.
    """
    record = _load_json(GOLDEN)
    assert record["dependencies"], "expected a non-empty dependency surface"
    band_schema_enum = set(_load_json(BAND_SCHEMA)["enum"])
    residency_schema_enum = set(_load_json(RESIDENCY_SCHEMA)["enum"])
    ownership_schema_enum = set(_load_json(OWNERSHIP_SCHEMA)["enum"])
    for entry in record["dependencies"]:
        cls = entry["sovereignty_classification"]
        assert cls["residency"] in residency_schema_enum
        assert cls["ownership"] in ownership_schema_enum
        assert cls["sovereignty_band"] in band_schema_enum


def test_committed_example_carries_nis2_art_22() -> None:
    """G-02 regulatory-mapping anchor for the supply-chain stream.

    NIS2 Article 22 is the Cooperation-Group wire that consumes the
    supplier-coverage rollup. The committed example must carry it on
    ``regulation_refs`` per the F-CP-03 contract; the n8n adapter
    must not drop it on the way to disk.
    """
    record = _load_json(GOLDEN)
    assert "nis2:art-22" in record["regulation_refs"]


# --------------------------------------------------------------------------- #
# Coverage axis 4: artifact_id determinism                                    #
# --------------------------------------------------------------------------- #


def test_artifact_id_is_deterministic_sha256(tmp_path: Path) -> None:
    """``artifact_id`` on the committed record matches
    SHA-256(``<workflow_id>|<execution_id>|<captured_at>``).

    Schema contract — and the property that lets re-emissions of the
    same execution at the same captured-at instant land on
    byte-identical content. Replay-side: the fresh adapter emission
    re-derives the same id, which the shared emitter encodes into the
    written artifact filename and exposes on the next-node output.
    """
    record = _load_json(GOLDEN)
    expected = hashlib.sha256(
        f"{record['workflow_id']}|{record['execution_id']}|"
        f"{record['captured_at']}".encode("utf-8")
    ).hexdigest()
    assert record["artifact_id"] == expected

    result = emit_supply_chain_artifact_n8n(PAYLOAD, tmp_path)
    written = Path(result["artifact_path"])
    assert written.stem == expected
    assert result["artifact_id"] == expected
