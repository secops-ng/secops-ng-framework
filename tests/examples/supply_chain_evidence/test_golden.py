"""F-CP-03 EXTEND-tests-goldens — per-target byte-parity goldens.

These tests pin the on-disk bytes of the supply-chain dependencies
snapshot evidence artifact emitted by each compile target (n8n,
Temporal, LangGraph) against a checked-in fixture under
``tests/fixtures/supply_chain_evidence/<target>.json``.

The CORE-FANOUT round-trip in
``tests/content_model/test_supply_chain_evidence_emitter.py`` already
pins cross-target equivalence (all three targets agree byte-for-byte
under one execution). These tests are the EXTEND complement: each
target's adapter is exercised against an immutable golden so a refactor
of the shared emitter that silently changes serialisation gets caught at
the byte level — one fixture per target so the failure message names
which target drifted, mirroring the F-CP-01 risk-analysis, F-CP-02
incidents, and F-CP-04 vulnerabilities goldens.

Coverage axes (per the F-CP-03 EXTEND-tests-goldens contract):

1. **Schema-conformant emit.** Each target's on-disk artifact validates
   against ``schemas/evidence/supply-chain.schema.json`` (with the
   promoted ``supply_chain_dependency_kind``, ``sovereignty_residency``,
   ``sovereignty_ownership``, ``sovereignty_band``, and
   ``attestation_state`` schemas resolved).
2. **Sovereignty atom presence + vocabulary normalisation.** Every
   ``dependencies[*].sovereignty_classification`` block carries
   ``residency`` / ``ownership`` / ``sovereignty_band`` drawn from the
   promoted vocabularies; the adapters do not coerce or rewrite the
   values the operator's Sovereign Provider KB carried in. This is the
   F-CP-03 sovereign-stack constraint already enforced in the shared
   emitter; pinning it on disk per target guards against a future
   adapter that silently re-spells one of the band values.
3. **NIS2 Article 22 Cooperation-Group anchor.** Every golden carries
   ``nis2:art-22`` on ``regulation_refs`` — the G-02 regulatory mapping
   beat for this stream. Adapters must not drop it.
4. **artifact_id determinism.** ``artifact_id`` on the on-disk record
   matches ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` per
   the schema contract and is byte-identical across targets.

If the shared emitter changes the on-disk serialisation intentionally,
regenerate the goldens by re-running the cross-target round-trip in
``test_supply_chain_evidence_emitter.py``, copying any one of the three
(they MUST be byte-identical) into each fixture, and committing the
updated bytes alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
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
    render_supply_chain_artifact,
)

REPO = Path(__file__).resolve().parents[3]
SCHEMAS = REPO / "schemas"
SUPPLY_CHAIN_EVIDENCE_SCHEMA = SCHEMAS / "evidence" / "supply-chain.schema.json"
DEPENDENCY_KIND_SCHEMA = SCHEMAS / "supply_chain_dependency_kind.json"
RESIDENCY_SCHEMA = SCHEMAS / "sovereignty_residency.json"
OWNERSHIP_SCHEMA = SCHEMAS / "sovereignty_ownership.json"
BAND_SCHEMA = SCHEMAS / "sovereignty_band.json"
ATTESTATION_STATE_SCHEMA = SCHEMAS / "attestation_state.json"

FIXTURES = REPO / "tests" / "fixtures" / "supply_chain_evidence"
N8N_GOLDEN = FIXTURES / "n8n.json"
TEMPORAL_GOLDEN = FIXTURES / "temporal.json"
LANGGRAPH_GOLDEN = FIXTURES / "langgraph.json"


# --------------------------------------------------------------------------- #
# Shared fixture context                                                       #
# --------------------------------------------------------------------------- #


def _classification_sovereign() -> SovereigntyClassification:
    return SovereigntyClassification(
        residency="eu",
        ownership="eu_owned",
        sovereignty_band="sovereign",
        sub_processor_chain=(),
        band_rationale=(
            "EU-owned provider operating wholly inside an EU Member State; "
            "no declared sub-processors."
        ),
        kb_ref="supplier-kb://provider-eu-sovereign-ai/2026-Q2",
    )


def _classification_non_eu() -> SovereigntyClassification:
    return SovereigntyClassification(
        residency="non_eu",
        ownership="non_eu_owned",
        sovereignty_band="non_eu",
        sub_processor_chain=None,
        band_rationale=(
            "Non-EU residency; ownership chain not in scope for the "
            "sovereign band."
        ),
        kb_ref="supplier-kb://provider-non-eu-llm/2026-Q2",
    )


def _attestation_effective() -> Attestation:
    return Attestation(
        state="effective",
        last_reattested_at=datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        next_due_at=datetime(2027, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        attestation_ref="atte-2026Q2-0001",
    )


def _attestation_overdue() -> Attestation:
    return Attestation(
        state="overdue",
        last_reattested_at=datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        next_due_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )


def _ctx() -> SupplyChainContext:
    """The canonical supply-chain context the three goldens pin against.

    Covers the union of the schema's surface for a single execution:
    two dependencies that together exercise both extremes of the
    promoted ``sovereignty_band`` vocabulary (one ``sovereign``, one
    ``non_eu``), both states of the promoted ``attestation_state``
    vocabulary that an operator commonly carries (``effective`` and
    ``overdue``), two distinct ``supply_chain_dependency_kind`` values
    (``data_feed`` and ``ai_provider``), and a full ``aggregates``
    block. Anchored on the F-WF-01 vulnerability-triage workflow and
    NIS2 Article 21(2)(d) plus the Article 22 Cooperation-Group wire
    that the G-02 milestone reads.

    Kept in lockstep with ``_ctx`` in
    ``tests/content_model/test_supply_chain_evidence_emitter.py`` so a
    drift on either side surfaces as a byte-parity mismatch instead of
    a silent vocabulary fork.
    """
    return SupplyChainContext(
        workflow_id="vulnerability_triage",
        execution_id="temporal:wf-run-supply-abc123",
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
                sovereignty_classification=_classification_sovereign(),
                attestation=_attestation_effective(),
                risk_notes=(
                    "EU-hosted, EU-owned vulnerability data feed; "
                    "primary source for triage enrichment."
                ),
            ),
            Dependency(
                provider_id="provider.llm_inference_non_eu@v1",
                kind="ai_provider",
                call_count=1,
                version=None,
                sovereignty_classification=_classification_non_eu(),
                attestation=_attestation_overdue(),
                risk_notes=(
                    "Non-EU LLM used for risk-summary generation; "
                    "attestation overdue per supplier KB cadence."
                ),
            ),
        ),
        owner_role="supplier-governance@example.org",
        owner_assigned_at="2026-01-15",
        captured_at=datetime(2026, 6, 7, 6, 0, 0, tzinfo=timezone.utc),
        source_url="https://example.org/runs/supply-abc123",
        aggregates=Aggregates(
            total_providers=2,
            sovereign_count=1,
            eu_hosted_count=1,
            non_eu_count=1,
            ai_provider_count=1,
        ),
        commit_sha="deadbeef0123456789",
    )


def _n8n_payload(ctx: SupplyChainContext) -> dict:
    """Re-shape a context as the JSON-native payload an n8n node sends.

    n8n cannot transport Python objects across the node-process
    boundary, so datetimes arrive as ISO-8601 ``...Z`` strings and
    nested dataclasses arrive as JSON objects / arrays. Kept in
    lockstep with the ``_payload_from_ctx`` helper in
    ``tests/content_model/test_supply_chain_evidence_emitter.py``.
    """
    def _cls(cls: SovereigntyClassification) -> dict:
        out: dict = {
            "residency": cls.residency,
            "ownership": cls.ownership,
            "sovereignty_band": cls.sovereignty_band,
        }
        if cls.sub_processor_chain is not None:
            out["sub_processor_chain"] = list(cls.sub_processor_chain)
        if cls.band_rationale is not None:
            out["band_rationale"] = cls.band_rationale
        if cls.kb_ref is not None:
            out["kb_ref"] = cls.kb_ref
        return out

    def _att(att: Attestation) -> dict:
        out: dict = {
            "state": att.state,
            "last_reattested_at": att.last_reattested_at.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "next_due_at": att.next_due_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if att.attestation_ref is not None:
            out["attestation_ref"] = att.attestation_ref
        return out

    def _dep(dep: Dependency) -> dict:
        out: dict = {
            "provider_id": dep.provider_id,
            "kind": dep.kind,
            "call_count": dep.call_count,
            "sovereignty_classification": _cls(dep.sovereignty_classification),
            "attestation": _att(dep.attestation),
        }
        if dep.version is not None:
            out["version"] = dep.version
        if dep.risk_notes is not None:
            out["risk_notes"] = dep.risk_notes
        return out

    payload: dict = {
        "workflow_id": ctx.workflow_id,
        "execution_id": ctx.execution_id,
        "regulation_refs": list(ctx.regulation_refs),
        "control_refs": list(ctx.control_refs),
        "dependencies": [_dep(d) for d in ctx.dependencies],
        "owner_role": ctx.owner_role,
        "owner_assigned_at": ctx.owner_assigned_at,
        "captured_at": ctx.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": ctx.source_url,
    }
    if ctx.commit_sha:
        payload["commit_sha"] = ctx.commit_sha
    if ctx.retention:
        payload["retention"] = ctx.retention
    if ctx.aggregates is not None:
        agg = ctx.aggregates
        agg_payload: dict = {}
        for key in (
            "total_providers",
            "sovereign_count",
            "eu_hosted_count",
            "non_eu_count",
            "ai_provider_count",
        ):
            val = getattr(agg, key)
            if val is not None:
                agg_payload[key] = val
        payload["aggregates"] = agg_payload
    return payload


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    """Draft 2020-12 validator with the promoted-vocabulary siblings pinned.

    See ``tests/content_model/test_supply_chain_evidence_emitter.py``
    for the rationale: ``jsonschema.RefResolver`` mis-resolves an
    in-document ``#/$defs/...`` pointer after following an external
    ``$ref`` (the supply-chain schema hits that path on every
    ``dependencies[]`` entry). The ``referencing`` registry is the
    supported successor and resolves correctly.
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


def _enum(path: Path) -> set[str]:
    return set(_load_json(path)["enum"])


# --------------------------------------------------------------------------- #
# Fixture-on-disk guardrails                                                  #
# --------------------------------------------------------------------------- #


def test_golden_fixtures_are_committed() -> None:
    for path in (N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN):
        assert path.exists(), f"missing golden fixture: {path}"
        assert path.stat().st_size > 0, f"empty golden fixture: {path}"


def test_golden_fixtures_are_byte_identical_across_targets() -> None:
    """The shared emitter's contract is record-shape parity across
    targets. The three checked-in fixtures must therefore be
    byte-identical; if they diverge, a per-target test below will
    succeed for one target and fail for the others, and the failure
    will be hard to diagnose. Pin the parity at fixture-load time too.
    """
    assert (
        N8N_GOLDEN.read_bytes()
        == TEMPORAL_GOLDEN.read_bytes()
        == LANGGRAPH_GOLDEN.read_bytes()
    )


# --------------------------------------------------------------------------- #
# Per-target byte-parity goldens                                              #
# --------------------------------------------------------------------------- #


def _drift_hint(target: str) -> str:
    return (
        f"{target} supply-chain evidence artifact drifted from the "
        f"committed golden. If the change is intentional, regenerate "
        f"the goldens by re-running the cross-target round-trip in "
        f"tests/content_model/test_supply_chain_evidence_emitter.py "
        f"and committing the new bytes alongside the emitter change."
    )


def test_temporal_artifact_matches_golden(tmp_path: Path) -> None:
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_supply_chain_artifact_activity

    written = Path(
        asyncio.run(emit_supply_chain_artifact_activity(_ctx(), str(tmp_path)))
    )
    assert written.read_bytes() == TEMPORAL_GOLDEN.read_bytes(), _drift_hint(
        "Temporal"
    )


def test_n8n_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.n8n.evidence import emit_supply_chain_artifact_n8n

    result = emit_supply_chain_artifact_n8n(_n8n_payload(_ctx()), tmp_path)
    written = Path(result["artifact_path"])
    assert written.read_bytes() == N8N_GOLDEN.read_bytes(), _drift_hint("n8n")


def test_langgraph_artifact_matches_golden(tmp_path: Path) -> None:
    from compilers.langgraph.evidence import emit_supply_chain_artifact_node

    update = emit_supply_chain_artifact_node(
        {
            "supply_chain_context": _ctx(),
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["supply_chain_artifact_path"])
    assert written.read_bytes() == LANGGRAPH_GOLDEN.read_bytes(), _drift_hint(
        "LangGraph"
    )


# --------------------------------------------------------------------------- #
# Coverage axis 1: schema-conformant emit                                     #
# --------------------------------------------------------------------------- #


def test_temporal_golden_validates_against_schema() -> None:
    _validator().validate(_load_json(TEMPORAL_GOLDEN))


def test_n8n_golden_validates_against_schema() -> None:
    _validator().validate(_load_json(N8N_GOLDEN))


def test_langgraph_golden_validates_against_schema() -> None:
    _validator().validate(_load_json(LANGGRAPH_GOLDEN))


# --------------------------------------------------------------------------- #
# Coverage axis 2: sovereignty atom presence + vocabulary normalisation        #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_sovereignty_classification_atom_on_every_dependency(
    fixture: Path,
) -> None:
    """F-CP-03 sovereign-stack constraint pinned at the byte level.

    The shared emitter already enforces that every declared dependency
    carries a ``sovereignty_classification`` sub-object; this test
    pins the same invariant on each per-target golden so a future
    adapter cannot strip the atom without the EXTEND-tests lane
    failing first.
    """
    record = _load_json(fixture)
    assert record["dependencies"], "fixture must exercise dependencies"
    for entry in record["dependencies"]:
        assert "sovereignty_classification" in entry, (
            "sovereignty_classification atom missing from a dependency entry"
        )
        cls = entry["sovereignty_classification"]
        for key in ("residency", "ownership", "sovereignty_band"):
            assert key in cls, (
                f"sovereignty_classification missing required key {key!r}"
            )


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_sovereignty_band_drawn_from_shared_vocabulary(
    fixture: Path,
) -> None:
    """``sovereignty_classification.sovereignty_band`` on each
    dependency must be one of the values pinned by
    ``schemas/sovereignty_band.json``. If a target's adapter silently
    re-coerced the value (e.g. uppercased it, expanded a synonym, or
    re-rolled the rollup), this test fails before the per-target
    byte-parity test does, giving a precise diagnosis.
    """
    record = _load_json(fixture)
    allowed = _enum(BAND_SCHEMA)
    expected = [
        d.sovereignty_classification.sovereignty_band for d in _ctx().dependencies
    ]
    seen = [
        entry["sovereignty_classification"]["sovereignty_band"]
        for entry in record["dependencies"]
    ]
    assert seen, "fixture must exercise dependencies"
    for name in seen:
        assert name in allowed, f"unknown sovereignty_band: {name}"
    assert seen == expected


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_residency_drawn_from_shared_vocabulary(fixture: Path) -> None:
    """``sovereignty_classification.residency`` reuses the promoted
    ``sovereignty_residency`` vocabulary; pin the invariant so a
    future adapter cannot fork the enum.
    """
    record = _load_json(fixture)
    allowed = _enum(RESIDENCY_SCHEMA)
    expected = [
        d.sovereignty_classification.residency for d in _ctx().dependencies
    ]
    seen = [
        entry["sovereignty_classification"]["residency"]
        for entry in record["dependencies"]
    ]
    for name in seen:
        assert name in allowed, f"unknown residency: {name}"
    assert seen == expected


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_ownership_drawn_from_shared_vocabulary(fixture: Path) -> None:
    """``sovereignty_classification.ownership`` reuses the promoted
    ``sovereignty_ownership`` vocabulary; pin the invariant.
    """
    record = _load_json(fixture)
    allowed = _enum(OWNERSHIP_SCHEMA)
    expected = [
        d.sovereignty_classification.ownership for d in _ctx().dependencies
    ]
    seen = [
        entry["sovereignty_classification"]["ownership"]
        for entry in record["dependencies"]
    ]
    for name in seen:
        assert name in allowed, f"unknown ownership: {name}"
    assert seen == expected


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_dependency_kind_drawn_from_shared_vocabulary(
    fixture: Path,
) -> None:
    """``dependencies[*].kind`` reuses the promoted
    ``supply_chain_dependency_kind`` vocabulary; pin so a future
    adapter cannot re-spell ``ai_provider`` as ``ai-provider``.
    """
    record = _load_json(fixture)
    allowed = _enum(DEPENDENCY_KIND_SCHEMA)
    expected = [d.kind for d in _ctx().dependencies]
    seen = [entry["kind"] for entry in record["dependencies"]]
    for name in seen:
        assert name in allowed, f"unknown dependency kind: {name}"
    assert seen == expected


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_attestation_state_drawn_from_shared_vocabulary(
    fixture: Path,
) -> None:
    """``dependencies[*].attestation.state`` reuses the promoted
    ``attestation_state`` vocabulary; pin the invariant.
    """
    record = _load_json(fixture)
    allowed = _enum(ATTESTATION_STATE_SCHEMA)
    expected = [d.attestation.state for d in _ctx().dependencies]
    seen = [
        entry["attestation"]["state"] for entry in record["dependencies"]
    ]
    for name in seen:
        assert name in allowed, f"unknown attestation_state: {name}"
    assert seen == expected


def test_fixture_exercises_sovereign_and_non_eu_band_extremes() -> None:
    """Acceptance pin from the task body: the fixture MUST exercise
    the extremes of the promoted ``sovereignty_band`` vocabulary so a
    parity beat that loses one band silently fails loudly. The
    canonical context carries one ``sovereign`` and one ``non_eu``
    dependency.
    """
    record = _load_json(TEMPORAL_GOLDEN)
    seen = {
        entry["sovereignty_classification"]["sovereignty_band"]
        for entry in record["dependencies"]
    }
    assert {"sovereign", "non_eu"}.issubset(seen)


# --------------------------------------------------------------------------- #
# Coverage axis 3: NIS2 Article 22 Cooperation-Group anchor                   #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_regulation_refs_carry_nis2_art_22(fixture: Path) -> None:
    """G-02 regulatory-mapping anchor for the supply-chain stream.

    NIS2 Article 22 is the Cooperation-Group wire that consumes the
    supplier-coverage rollup. The golden must carry it on
    ``regulation_refs`` per the F-CP-03 contract; adapters must not
    drop it on the way to disk.
    """
    record = _load_json(fixture)
    assert "nis2:art-22" in record["regulation_refs"]
    assert record["regulation_refs"] == list(_ctx().regulation_refs)


# --------------------------------------------------------------------------- #
# Coverage axis 4: artifact_id determinism                                    #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "fixture",
    [N8N_GOLDEN, TEMPORAL_GOLDEN, LANGGRAPH_GOLDEN],
    ids=["n8n", "temporal", "langgraph"],
)
def test_artifact_id_matches_derivation(fixture: Path) -> None:
    """``artifact_id`` on the on-disk record must equal
    ``SHA-256(<workflow_id>|<execution_id>|<captured_at>)`` per the
    schema contract. Replays of the same execution at the same
    captured-at instant must re-derive the same id, so downstream
    deduplication is trivial. Pin the value alongside the per-target
    bytes so a target that silently re-derives the id from a different
    key fails fast.
    """
    ctx = _ctx()
    record = _load_json(fixture)
    expected = derive_supply_chain_artifact_id(
        ctx.workflow_id, ctx.execution_id, ctx.captured_at
    )
    assert record["artifact_id"] == expected


def test_artifact_id_byte_identical_across_targets() -> None:
    """The artifact_id is contained verbatim in each golden's bytes;
    cross-target parity at the byte level is already pinned in
    ``test_golden_fixtures_are_byte_identical_across_targets``, but
    naming the id in this test gives a precise diagnosis if a target
    drifts on the derivation rather than on the surrounding shape.
    """
    ctx = _ctx()
    needle = (
        f'"artifact_id": "'
        f"{derive_supply_chain_artifact_id(ctx.workflow_id, ctx.execution_id, ctx.captured_at)}"
        f'"'
    ).encode("utf-8")
    assert needle in N8N_GOLDEN.read_bytes()
    assert needle in TEMPORAL_GOLDEN.read_bytes()
    assert needle in LANGGRAPH_GOLDEN.read_bytes()


# --------------------------------------------------------------------------- #
# Pure-renderer sanity                                                        #
# --------------------------------------------------------------------------- #


def test_render_matches_golden_serialisation() -> None:
    """Independent of any compile target, the pure ``render`` helper
    composed with the canonical serialisation the emitter uses must
    reproduce the golden bytes. Guards the case where a future
    refactor moves serialisation logic out of the emitter into the
    adapters — the byte-parity pin should still hold against the
    pure render path.
    """
    rendered = render_supply_chain_artifact(_ctx())
    serialised = (
        json.dumps(rendered, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert serialised == TEMPORAL_GOLDEN.read_bytes()
