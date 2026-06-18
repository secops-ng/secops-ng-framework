"""F-WF-09 EXTEND — byte-parity golden for the incident-management bundle.

Pins the on-disk bytes of the auditor-handover bundle assembled for the
``playbook.incident_management@v1`` workflow against the committed
worked-example artifacts under
``examples/{n8n,temporal,langgraph}/incident-management/evidence/bundle/``.

The cross-target round-trip in
``tests/content_model/test_bundle_evidence_collector.py`` already pins
cross-target equivalence of the shared collector under one execution.
This test is the EXTEND complement for the incident-management bundle:
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
``examples/{n8n,temporal,langgraph}/incident-management/evidence/bundle/``
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
N8N_BUNDLE = EXAMPLES / "n8n" / "incident-management" / "evidence" / "bundle"
TEMPORAL_BUNDLE = (
    EXAMPLES / "temporal" / "incident-management" / "evidence" / "bundle"
)
LANGGRAPH_BUNDLE = (
    EXAMPLES / "langgraph" / "incident-management" / "evidence" / "bundle"
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


def test_manifests_are_byte_identical_across_targets() -> None:
    """The shared collector renders the same manifest bytes for all
    three reference compile targets. The committed manifests must
    therefore be byte-identical; if they diverge, an adapter is
    mutating the serialisation on its way to disk.
    """
    assert (
        N8N_MANIFEST.read_bytes()
        == TEMPORAL_MANIFEST.read_bytes()
        == LANGGRAPH_MANIFEST.read_bytes()
    )


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
    """
    record = _load_json(bundle / "bundle.manifest.json")
    streams_present = [s for s in record["streams"] if s["present"]]
    assert streams_present, (
        f"expected at least one present stream in {bundle}, got none"
    )
    assert {s["stream"] for s in streams_present} == {"incidents"}, (
        f"incident-management bundle should exercise only incidents; "
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
    with ``present: false`` for the streams the incident-management
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
    assert not_present == expected - {"incidents"}
