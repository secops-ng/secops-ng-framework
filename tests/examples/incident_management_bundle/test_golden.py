"""F-WF-09 EXTEND — byte-parity golden for the incident_management bundle.

Pins the on-disk bytes of the auditor-handover bundle assembled for the
``playbook.incident_management@v1`` workflow against the committed
worked-example artifacts under
``examples/{n8n,temporal,langgraph}/incident_management/evidence/bundle/``.

The cross-target round-trip in
``tests/content_model/test_bundle_evidence_collector.py`` already pins
cross-target equivalence of the shared collector under one execution.
This test is the EXTEND complement for the incident_management bundle:
each target's bundle directory is exercised against the committed
bytes so a refactor of the shared collector, an adapter, or the
inlined incidents emitter that silently changes serialisation gets
caught at the byte level — one assertion per target so the failure
message names which target drifted, mirroring the per-stream goldens
under ``tests/examples/{access,incidents,vulnerabilities,...}_evidence/``.

Coverage axes (adapted to the bundle surface):

1. **Manifest byte-parity across targets.** The committed
   ``bundle.manifest.json`` under each compile target must be
   byte-identical. The shared collector renders the manifest from the
   same evidence surface for all three targets, so divergence here
   means an adapter is mutating the serialisation.
2. **Schema-conformant manifest.** Each target's committed manifest
   validates against ``schemas/evidence/bundle.schema.json``.
3. **bundle_id determinism.** ``bundle_id`` on each committed manifest
   matches ``SHA-256(<generated_at>|<bundle_window_start>|<bundle_window_end>)``
   per the F-WF-09 contract.
4. **Inlined incidents artifact matches the EXTEND-tests golden.**
   The file under ``content/evidence/incidents/`` in each bundle is
   byte-identical to the per-target incidents golden under
   ``tests/fixtures/incidents_evidence/`` — the bundle's inlined
   artifact is the same surface a reviewer cross-checks without
   leaving the bundle directory.
5. **Manifest manifest_paths resolve on disk.** Every ``artifact_paths``
   entry on every ``present`` stream resolves to a file under the
   bundle root.

If the shared collector, an adapter, or the inlined incidents emitter
changes the on-disk serialisation intentionally, regenerate the
bundles via the three ``regenerate.py`` scripts under
``examples/{n8n,temporal,langgraph}/incident_management/evidence/bundle/``
and commit the new bytes alongside the change.
"""
from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[3]
SCHEMAS = REPO / "schemas"
BUNDLE_SCHEMA = SCHEMAS / "evidence" / "bundle.schema.json"

EXAMPLES = REPO / "examples"
N8N_BUNDLE = EXAMPLES / "n8n" / "incident_management" / "evidence" / "bundle"
TEMPORAL_BUNDLE = (
    EXAMPLES / "temporal" / "incident_management" / "evidence" / "bundle"
)
LANGGRAPH_BUNDLE = (
    EXAMPLES / "langgraph" / "incident_management" / "evidence" / "bundle"
)
BUNDLES = (N8N_BUNDLE, TEMPORAL_BUNDLE, LANGGRAPH_BUNDLE)
TARGET_IDS = ("n8n", "temporal", "langgraph")

N8N_MANIFEST = N8N_BUNDLE / "bundle.manifest.json"
TEMPORAL_MANIFEST = TEMPORAL_BUNDLE / "bundle.manifest.json"
LANGGRAPH_MANIFEST = LANGGRAPH_BUNDLE / "bundle.manifest.json"
MANIFESTS = (N8N_MANIFEST, TEMPORAL_MANIFEST, LANGGRAPH_MANIFEST)

INCIDENTS_FIXTURES = REPO / "tests" / "fixtures" / "incidents_evidence"
N8N_INCIDENTS_GOLDEN = INCIDENTS_FIXTURES / "n8n.json"
TEMPORAL_INCIDENTS_GOLDEN = INCIDENTS_FIXTURES / "temporal.json"
LANGGRAPH_INCIDENTS_GOLDEN = INCIDENTS_FIXTURES / "langgraph.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_load_json(BUNDLE_SCHEMA))


# --------------------------------------------------------------------------- #
# Fixture-on-disk guardrails                                                  #
# --------------------------------------------------------------------------- #


def test_bundle_manifests_are_committed() -> None:
    for path in MANIFESTS:
        assert path.exists(), f"missing committed manifest: {path}"
        assert path.stat().st_size > 0, f"empty committed manifest: {path}"


# --------------------------------------------------------------------------- #
# Coverage axis 1: manifest byte-parity across targets                        #
# --------------------------------------------------------------------------- #


def test_n8n_and_langgraph_manifests_are_byte_identical() -> None:
    """The shared collector renders the same manifest bytes for any
    targets that exercise the same evidence surface. The n8n and
    LangGraph bundles for incident_management still inline only the
    incidents artifact (the access write-path is wired on Temporal
    first as the F-CP-07 SKELETON; the named CORE-FANOUT sibling fans
    that wiring out to n8n and LangGraph), so the two unfanned-out
    targets must remain byte-identical to each other. Full three-target
    byte-parity for the access-populated bundle is the named
    EXTEND-tests-goldens sibling.
    """
    assert N8N_MANIFEST.read_bytes() == LANGGRAPH_MANIFEST.read_bytes()


# --------------------------------------------------------------------------- #
# Coverage axis 2: schema-conformant emit                                     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("manifest", MANIFESTS, ids=TARGET_IDS)
def test_manifest_validates_against_schema(manifest: Path) -> None:
    _validator().validate(_load_json(manifest))


# --------------------------------------------------------------------------- #
# Coverage axis 3: bundle_id determinism                                      #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("manifest", MANIFESTS, ids=TARGET_IDS)
def test_bundle_id_matches_window_derivation(manifest: Path) -> None:
    """``bundle_id`` on each committed manifest equals
    ``SHA-256(<generated_at>|<bundle_window_start>|<bundle_window_end>)``
    (UTF-8, no separators around the pipes) per the F-WF-09
    determinism contract pinned at
    ``compilers/_shared/evidence/bundle.py``.
    """
    record = _load_json(manifest)
    raw = (
        f"{record['generated_at']}|"
        f"{record['bundle_window_start']}|"
        f"{record['bundle_window_end']}"
    ).encode("utf-8")
    assert record["bundle_id"] == sha256(raw).hexdigest()


# --------------------------------------------------------------------------- #
# Coverage axis 4: inlined incidents artifact matches EXTEND-tests golden     #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "bundle,golden",
    [
        (N8N_BUNDLE, N8N_INCIDENTS_GOLDEN),
        (TEMPORAL_BUNDLE, TEMPORAL_INCIDENTS_GOLDEN),
        (LANGGRAPH_BUNDLE, LANGGRAPH_INCIDENTS_GOLDEN),
    ],
    ids=TARGET_IDS,
)
def test_inlined_incidents_matches_extend_golden(
    bundle: Path, golden: Path
) -> None:
    """The inlined incidents artifact under
    ``content/evidence/incidents/<artifact_id>.json`` is rebuilt from
    the same typed ``IncidentsContext`` the per-target byte-parity
    golden pins. The bundle's inlined file must therefore be
    byte-identical to the committed EXTEND-tests fixture — a reviewer
    can cross-check the bundle's incidents artifact against the
    canonical fixture without leaving the bundle directory.
    """
    incidents_dir = bundle / "content" / "evidence" / "incidents"
    files = sorted(incidents_dir.glob("*.json"))
    assert len(files) == 1, (
        f"expected exactly one incidents artifact under {incidents_dir}, "
        f"found {[p.name for p in files]}"
    )
    assert files[0].read_bytes() == golden.read_bytes(), (
        f"inlined incidents artifact at {files[0]} drifted from the "
        f"EXTEND-tests golden {golden}. Regenerate via the bundle's "
        f"regenerate.py and commit the new bytes."
    )


# --------------------------------------------------------------------------- #
# Coverage axis 5: manifest artifact_paths resolve on disk                    #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("bundle", BUNDLES, ids=TARGET_IDS)
def test_manifest_artifact_paths_resolve(bundle: Path) -> None:
    """Every ``artifact_paths`` entry on every ``present`` stream
    resolves to a file under the bundle root. The bundle is the
    auditor handover unit; a reviewer walks the manifest's
    bundle-relative paths and must land on real files.

    Temporal exercises both ``incidents`` and ``access`` once the
    F-CP-07 SKELETON Temporal write-path is wired; n8n and LangGraph
    still exercise only ``incidents`` pending the named CORE-FANOUT
    sibling.
    """
    record = _load_json(bundle / "bundle.manifest.json")
    streams_present = [s for s in record["streams"] if s["present"]]
    assert streams_present, (
        f"expected at least one present stream in {bundle}, got none"
    )
    target = bundle.parts[-4]
    expected_present = (
        {"incidents", "access"} if target == "temporal" else {"incidents"}
    )
    assert {s["stream"] for s in streams_present} == expected_present, (
        f"{target} incident_management bundle expected {expected_present}; "
        f"got {[s['stream'] for s in streams_present]} in {bundle}"
    )
    for stream in streams_present:
        assert stream["artifact_paths"], (
            f"stream {stream['stream']} marked present with empty "
            f"artifact_paths in {bundle}"
        )
        for rel in stream["artifact_paths"]:
            on_disk = bundle / rel
            assert on_disk.is_file(), (
                f"manifest in {bundle} references {rel!s} but it is "
                f"not present in the bundle"
            )


# --------------------------------------------------------------------------- #
# Closed seven-stream surface                                                 #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("manifest", MANIFESTS, ids=TARGET_IDS)
def test_manifest_carries_closed_seven_stream_surface(manifest: Path) -> None:
    """The manifest carries an entry for every shipped evidence stream,
    with ``present: false`` for the streams the incident_management
    workflow does not exercise. The seven-stream surface is closed so
    a reviewer sees an explicit empty slot rather than a quietly
    omitted stream.
    """
    record = _load_json(manifest)
    stream_names = {s["stream"] for s in record["streams"]}
    expected = {
        "risk-analysis",
        "incidents",
        "vulns",
        "supply-chain",
        "crypto",
        "access",
        "effectiveness",
    }
    assert stream_names == expected, (
        f"manifest in {manifest} streams: expected {expected}, "
        f"got {stream_names}"
    )
    not_present = {s["stream"] for s in record["streams"] if not s["present"]}
    target = manifest.parts[-5]
    expected_present_for_target = (
        {"incidents", "access"} if target == "temporal" else {"incidents"}
    )
    assert not_present == expected - expected_present_for_target


# --------------------------------------------------------------------------- #
# F-CP-07 SKELETON: Temporal access write-path happy path                     #
# --------------------------------------------------------------------------- #


TEMPORAL_ACCESS_GOLDEN = (
    REPO / "tests" / "fixtures" / "access_evidence" / "temporal.json"
)
ACCESS_SCHEMA = SCHEMAS / "evidence" / "access.schema.json"


def test_temporal_bundle_emits_one_access_record_per_run() -> None:
    """F-CP-07 SKELETON Temporal write-path — happy path.

    One execution of the incident_management Temporal worked example
    drives the Temporal access activity exactly once and lands one
    well-formed access record under
    ``content/evidence/access/<artifact_id>.json`` inside the bundle
    directory. The record validates against
    ``schemas/evidence/access.schema.json``, carries one
    ``caller_identity`` block, and a closed ``verb.resource``
    capability list. The bundle manifest's ``access`` slot resolves to
    that file rather than the previously-reserved empty slot.

    Mirrors the SKELETON test shape used by the other streams' first-
    target wiring: assert one artifact per run, schema-conformant,
    surfaced through the auditor-bundle manifest.

    Per-target byte-parity (n8n + LangGraph fan-out) for the populated
    access slot is the named EXTEND-tests-goldens sibling.
    """
    access_dir = (
        TEMPORAL_BUNDLE / "content" / "evidence" / "access"
    )
    files = sorted(access_dir.glob("*.json"))
    assert len(files) == 1, (
        f"expected exactly one access record under {access_dir}, "
        f"found {[p.name for p in files]}"
    )

    record = _load_json(files[0])
    Draft202012Validator(_load_json(ACCESS_SCHEMA)).validate(record)

    # One caller-identity block: ``principal_type`` + ``principal_id``
    # required, optional ``identity_provider``. The schema enforces
    # closed enums on the principal type; the assertion here pins the
    # presence and shape so an emitter that silently drops the block
    # is caught at the worked-example surface.
    identity = record["caller_identity"]
    assert isinstance(identity, dict)
    assert identity["principal_type"]
    assert identity["principal_id"]

    # One closed capability list of ``verb.resource`` tokens. The
    # schema-level regex pins token shape; pinning length > 0 and
    # tuple-ish shape here surfaces an empty-capabilities regression
    # at the worked-example surface rather than at the schema boundary.
    capabilities = record["capabilities"]
    assert isinstance(capabilities, list) and capabilities

    # The bundle manifest's access slot resolves to the emitted file.
    manifest = _load_json(TEMPORAL_BUNDLE / "bundle.manifest.json")
    access_entries = [s for s in manifest["streams"] if s["stream"] == "access"]
    assert len(access_entries) == 1
    access_slot = access_entries[0]
    assert access_slot["present"] is True
    assert access_slot["artifact_count"] == 1
    assert len(access_slot["artifact_paths"]) == 1
    on_disk = TEMPORAL_BUNDLE / access_slot["artifact_paths"][0]
    assert on_disk.is_file()
    assert on_disk == files[0]

    # The inlined access artifact is rebuilt from the same typed
    # ``AccessContext`` the EXTEND-tests Temporal golden pins, so the
    # bundle's inlined file is byte-identical to the committed fixture.
    # A reviewer can cross-check the bundle's access artifact against
    # the canonical fixture without leaving the bundle directory.
    assert files[0].read_bytes() == TEMPORAL_ACCESS_GOLDEN.read_bytes(), (
        f"inlined Temporal access artifact at {files[0]} drifted from "
        f"the EXTEND-tests golden {TEMPORAL_ACCESS_GOLDEN}. Regenerate "
        f"via the bundle's regenerate.py and commit the new bytes."
    )
