"""F-CP-06 EXTEND-tests-goldens (n8n) — byte-parity replay golden.

Pins the committed effectiveness worked example for the n8n target
under ``examples/n8n/vuln_intake/evidence/effectiveness/`` against a
fresh re-emission driven through the n8n adapter at
:func:`compilers.n8n.evidence.emit_effectiveness_artifact_n8n`.

The committed snapshot — ``control-effectiveness-snapshot.json`` — is
the human-friendly rename of the deterministic ``<artifact_id>.json``
file the adapter writes. This test re-runs the adapter against the
same JSON-native payload
``examples/n8n/vuln_intake/evidence/effectiveness/regenerate.py``
ships, schema-validates the result against
``schemas/evidence/effectiveness.schema.json``, and asserts
byte-equality with the committed snapshot.

Coverage axes:

1. **Schema-conformant emit.** The re-emitted artifact validates
   against the effectiveness schema before the byte comparison runs,
   so a shape regression in the n8n adapter surfaces with a precise
   diagnostic.
2. **Byte-parity with the committed example.** The re-emitted
   artifact's on-disk bytes match the committed
   ``control-effectiveness-snapshot.json`` exactly. If the shared
   emitter or n8n adapter intentionally changes serialisation, the
   example must be regenerated via
   ``PYTHONPATH=. python examples/n8n/vuln_intake/evidence/effectiveness/regenerate.py``
   and the new bytes committed alongside the change.
3. **Indicator-anchor + NIS2 Article 21(2)(f) shape.** The record
   carries the F-CP-06 anchors — ``metric_ref``, ``subject_version``,
   the pre-computed indicator value, and the NIS2 regulatory anchor.

Sibling note: ``PAYLOAD`` below is kept byte-identical to ``PAYLOAD``
in ``examples/n8n/vuln_intake/evidence/effectiveness/regenerate.py``.
The filename in that path contains a hyphen, so the regenerate module
cannot be imported by ``import`` — the payload is duplicated here on
purpose and the byte-parity assertion catches drift on either side.
"""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from compilers.n8n.evidence import emit_effectiveness_artifact_n8n

REPO = Path(__file__).resolve().parents[6]
SCHEMA = REPO / "schemas" / "evidence" / "effectiveness.schema.json"
EXAMPLE_DIR = (
    REPO / "examples" / "n8n" / "vuln_intake" / "evidence" / "effectiveness"
)
GOLDEN = EXAMPLE_DIR / "control-effectiveness-snapshot.json"


# Mirrors PAYLOAD in
# examples/n8n/vuln_intake/evidence/effectiveness/regenerate.py.
# Kept byte-identical on purpose; the byte-parity test below catches
# drift on either side. Sorted keys in the on-disk record come from
# the shared emitter, not from this payload — the input is in the same
# field order an n8n Code / executeCommand node would marshal.
PAYLOAD: dict = {
    "workflow_id": "vulnerability_triage",
    "execution_id": "n8n:vuln_intake_effectiveness_example_0001",
    "compile_target": "n8n",
    "regulation_refs": ["nis2:art-21-2-f"],
    "control_refs": [
        "control.control_effectiveness_test@v1",
        "control.risk_management_policy@v1",
    ],
    "metric_ref": "kri.control_effectiveness@v1",
    "subject_version": {
        "kind": "policy_version",
        "value": "1.2.0",
    },
    "measurement": {
        "value": 0.08,
        "unit": "ratio",
        "direction": "lower_is_better",
        "source_shape": {
            "kind": "ocsf",
            "ocsf": {
                "class_uid": 2004,
                "class_name": "Detection Finding",
                "ocsf_version": "1.1.0",
            },
        },
        "evaluation_window": "P1D",
        "threshold_crossed": "warn",
    },
    "owner_role": "metrics-wg",
    "owner_assigned_at": "2026-01-15",
    "captured_at": "2026-06-18T05:00:00Z",
    "source_url": (
        "https://example.org/runs/effectiveness-vuln-intake-example-0001"
    ),
    "retention": "P2Y",
}


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    """Schema validator for the effectiveness record.

    The effectiveness schema is self-contained — all enum / pattern
    constraints live inline, so unlike the supply-chain stream this
    validator does not need an external ``referencing`` registry.
    """
    return Draft202012Validator(_load_json(SCHEMA))


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
    ``schemas/evidence/effectiveness.schema.json`` before the
    byte-parity assertion runs, so a shape regression in the n8n
    adapter surfaces with a JSON Schema diagnostic instead of a
    bytes-differ message.
    """
    result = emit_effectiveness_artifact_n8n(PAYLOAD, tmp_path)
    written = Path(result["artifact_path"])
    _validator().validate(_load_json(written))


# --------------------------------------------------------------------------- #
# Coverage axis 2: byte-parity replay against the committed example           #
# --------------------------------------------------------------------------- #


def _drift_hint() -> str:
    return (
        "n8n effectiveness example drifted from a fresh adapter replay. "
        "If the change is intentional, regenerate the example via "
        "`PYTHONPATH=. python examples/n8n/vuln_intake/evidence/"
        "effectiveness/regenerate.py` and commit the new bytes alongside "
        "the emitter / adapter change."
    )


def test_n8n_replay_matches_committed_example(tmp_path: Path) -> None:
    """Replay the n8n adapter, then assert byte-equality with the example.

    The shared emitter writes ``<artifact_id>.json`` under ``tmp_path``;
    ``examples/.../regenerate.py`` copies that to the
    ``control-effectiveness-snapshot.json`` snapshot for human-friendly
    diffing. We compare the adapter's freshly-written bytes against
    the committed snapshot bytes; the rename is a pure copy in
    ``regenerate.py`` (``shutil.copyfile``) so the on-disk bytes are
    identical at the two paths.
    """
    result = emit_effectiveness_artifact_n8n(PAYLOAD, tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == GOLDEN.read_bytes(), _drift_hint()


# --------------------------------------------------------------------------- #
# Coverage axis 3: indicator-anchor + NIS2 Article 21(2)(f) shape             #
# --------------------------------------------------------------------------- #


def test_committed_example_carries_indicator_anchors() -> None:
    """The F-CP-06 indicator anchors are present on the artifact.

    ``metric_ref`` matches the catalogue stable-id shape, the
    ``subject_version`` block carries both ``kind`` and ``value``,
    and the ``measurement`` block carries the pre-computed value plus
    the source-shape pointer. The NIS2 Article 21(2)(f) regulatory
    anchor is present on ``regulation_refs``.
    """
    record = _load_json(GOLDEN)
    assert record["metric_ref"] == "kri.control_effectiveness@v1"
    assert record["subject_version"]["kind"] == "policy_version"
    assert record["subject_version"]["value"] == "1.2.0"
    assert record["measurement"]["unit"] == "ratio"
    assert record["measurement"]["direction"] == "lower_is_better"
    assert record["measurement"]["source_shape"]["kind"] == "ocsf"
    assert "nis2:art-21-2-f" in record["regulation_refs"]


def test_artifact_id_is_deterministic_sha256(tmp_path: Path) -> None:
    """``artifact_id`` on the committed record matches
    SHA-256(``<workflow_id>|<execution_id>|<compile_target>|<metric_ref>|<subject_version.value>``).

    Schema contract — and the property that lets re-emissions of the
    same evaluation land on byte-identical content. Replay-side: the
    fresh adapter emission re-derives the same id.
    """
    import hashlib

    record = _load_json(GOLDEN)
    expected = hashlib.sha256(
        (
            f"{record['workflow_id']}|{record['execution_id']}|"
            f"{record['compile_target']}|{record['metric_ref']}|"
            f"{record['subject_version']['value']}"
        ).encode("utf-8")
    ).hexdigest()
    assert record["artifact_id"] == expected

    result = emit_effectiveness_artifact_n8n(PAYLOAD, tmp_path)
    assert result["artifact_id"] == expected
