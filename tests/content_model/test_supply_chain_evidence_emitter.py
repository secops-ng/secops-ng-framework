"""F-CP-03 — supply-chain evidence-artifact round-trip (shared emitter).

Pins (CORE-FANOUT-SHARED scope only — the per-target adapters land in
their own sibling cards under F-CP-03 CORE-FANOUT-{N8N,TMP,LG}; per-target
byte-parity goldens land in the EXTEND-tests sibling):

1. The shared emitter writes a record that validates against
   ``schemas/evidence/supply-chain.schema.json`` (with the promoted
   ``supply_chain_dependency_kind``, ``sovereignty_residency``,
   ``sovereignty_ownership``, ``sovereignty_band``, and
   ``attestation_state`` schemas resolved).
2. The ``artifact_id`` is deterministic on
   ``(workflow_id, execution_id, captured_at)`` — same inputs reproduce
   the same id; different inputs do not.
3. The record persists to disk under ``<output_dir>/<artifact_id>.json``
   and re-reads byte-identical to the rendered record.
4. The deterministic :func:`compute_sovereignty_band` helper rolls
   (residency, ownership, sub-processor bands) up to the promoted
   ``sovereignty_band`` enum per the rules in
   ``schemas/sovereignty_band.json``.
"""
from __future__ import annotations

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
    compute_sovereignty_band,
    derive_supply_chain_artifact_id,
    emit_supply_chain_artifact,
    render_supply_chain_artifact,
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
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _validator() -> Draft202012Validator:
    schema = _load_json(SUPPLY_CHAIN_EVIDENCE_SCHEMA)
    # NOTE: ``jsonschema.RefResolver`` mis-resolves an in-document
    # ``#/$defs/...`` pointer once one of the schema's external
    # ``$ref`` siblings has been followed (the resolver's scope stack
    # keeps the last-pushed URI without popping it back to the host
    # schema). The supply-chain evidence schema hits that exact path —
    # ``dependencies[].$ref → #/$defs/dependency_record`` after each
    # promoted-vocabulary sibling is loaded. The ``referencing``
    # registry is the supported successor and resolves correctly; the
    # supporting schemas are pinned by URI here just like RefResolver's
    # ``store=``.
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


def _ctx(**overrides) -> SupplyChainContext:
    base = dict(
        # F-CP-03 SCHEMA anchors the stream on the F-WF-01 vulnerability
        # triage workflow; the CORE-FANOUT worked path emits one
        # supply-chain artifact per execution of that workflow.
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
    base.update(overrides)
    return SupplyChainContext(**base)


# --------------------------------------------------------------------------- #
# Schema / determinism pins                                                   #
# --------------------------------------------------------------------------- #


def test_rendered_record_validates_against_schema() -> None:
    record = render_supply_chain_artifact(_ctx())
    _validator().validate(record)


def test_artifact_id_is_deterministic_on_anchors() -> None:
    ctx_a = _ctx()
    # Same inputs → same id.
    assert (
        render_supply_chain_artifact(ctx_a)["artifact_id"]
        == render_supply_chain_artifact(ctx_a)["artifact_id"]
    )
    expected = derive_supply_chain_artifact_id(
        ctx_a.workflow_id, ctx_a.execution_id, ctx_a.captured_at
    )
    assert render_supply_chain_artifact(ctx_a)["artifact_id"] == expected
    # Different execution_id → different id; same workflow_id carries through.
    ctx_b = _ctx(execution_id="temporal:wf-run-supply-zzz999")
    rendered_b = render_supply_chain_artifact(ctx_b)
    assert (
        rendered_b["artifact_id"]
        != render_supply_chain_artifact(ctx_a)["artifact_id"]
    )
    assert rendered_b["workflow_id"] == render_supply_chain_artifact(ctx_a)[
        "workflow_id"
    ]
    # Different captured_at instant → different id even at the same execution.
    ctx_c = _ctx(
        captured_at=datetime(2026, 6, 7, 7, 0, 0, tzinfo=timezone.utc)
    )
    assert (
        render_supply_chain_artifact(ctx_c)["artifact_id"]
        != render_supply_chain_artifact(ctx_a)["artifact_id"]
    )


def test_emit_persists_round_trip(tmp_path: Path) -> None:
    ctx = _ctx()
    written = emit_supply_chain_artifact(ctx, tmp_path)
    assert written.exists()
    assert (
        written.name
        == f"{render_supply_chain_artifact(ctx)['artifact_id']}.json"
    )
    on_disk = json.loads(written.read_text("utf-8"))
    assert on_disk == render_supply_chain_artifact(ctx)
    _validator().validate(on_disk)


def test_emit_omits_aggregates_when_caller_supplies_none(tmp_path: Path) -> None:
    """Schema marks ``aggregates`` optional. The helper must not emit
    an empty key when the caller leaves it unset.
    """
    ctx = _ctx(aggregates=None)
    written = emit_supply_chain_artifact(ctx, tmp_path)
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert "aggregates" not in on_disk


def test_emit_rejects_zero_dependencies(tmp_path: Path) -> None:
    """An execution with no external dependencies should not be in
    scope for the supply-chain stream at all; the helper enforces this
    above the schema floor.
    """
    with pytest.raises(ValueError):
        emit_supply_chain_artifact(_ctx(dependencies=()), tmp_path)


def test_emit_rejects_bad_workflow_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_supply_chain_artifact(_ctx(workflow_id="Bad ID"), tmp_path)


def test_emit_rejects_bad_provider_id(tmp_path: Path) -> None:
    bad_dep = Dependency(
        provider_id="not-a-provider-id",
        kind="hosted_api",
        call_count=1,
        sovereignty_classification=_classification_sovereign(),
        attestation=_attestation_effective(),
    )
    with pytest.raises(ValueError):
        emit_supply_chain_artifact(_ctx(dependencies=(bad_dep,)), tmp_path)


def test_emit_rejects_naive_captured_at(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        emit_supply_chain_artifact(
            _ctx(captured_at=datetime(2026, 6, 7, 5, 0, 0)),
            tmp_path,
        )


def test_emit_rejects_personal_name_owner_assigned_at_shape(
    tmp_path: Path,
) -> None:
    """``owner_assigned_at`` must be an ISO-8601 date — guards against
    a free-text owner-as-name slipping into the date field.
    """
    with pytest.raises(ValueError):
        emit_supply_chain_artifact(
            _ctx(owner_assigned_at="not-a-date"), tmp_path
        )


# --------------------------------------------------------------------------- #
# Sovereignty-band rollup                                                     #
# --------------------------------------------------------------------------- #


def test_band_rollup_sovereign_when_eu_eu_owned_all_sovereign() -> None:
    assert (
        compute_sovereignty_band("eu", "eu_owned", ()) == "sovereign"
    )
    assert (
        compute_sovereignty_band("eea", "eu_majority_owned", ("sovereign",))
        == "sovereign"
    )


def test_band_rollup_eu_hosted_non_sovereign_when_ownership_fails() -> None:
    assert (
        compute_sovereignty_band("eu", "non_eu_owned", ())
        == "eu_hosted_non_sovereign"
    )


def test_band_rollup_eu_hosted_non_sovereign_when_sub_processor_fails() -> None:
    assert (
        compute_sovereignty_band(
            "eu", "eu_owned", ("eu_hosted_non_sovereign",)
        )
        == "eu_hosted_non_sovereign"
    )


def test_band_rollup_eu_adequate() -> None:
    assert (
        compute_sovereignty_band(
            "eu_adequate_third_country", "non_eu_owned", ()
        )
        == "eu_adequate"
    )


def test_band_rollup_non_eu() -> None:
    assert (
        compute_sovereignty_band("non_eu", "non_eu_owned", ()) == "non_eu"
    )


def test_band_rollup_unknown_when_inputs_unknown() -> None:
    assert compute_sovereignty_band("unknown", "eu_owned", ()) == "unknown"
    assert compute_sovereignty_band("eu", "unknown", ()) == "unknown"
    assert (
        compute_sovereignty_band("eu", "eu_owned", ("unknown",)) == "unknown"
    )
    # None means the operator's KB has not captured the chain yet.
    assert compute_sovereignty_band("eu", "eu_owned", None) == "unknown"


# --------------------------------------------------------------------------- #
# n8n adapter round-trip (CORE-FANOUT-N8N)                                    #
# --------------------------------------------------------------------------- #


def _payload_from_ctx(ctx: SupplyChainContext) -> dict:
    """Re-shape a context as the JSON-native payload an n8n node sends.

    n8n cannot transport Python objects across the node-process
    boundary, so datetimes serialise to ISO-8601 ``...Z`` strings and
    nested dataclasses serialise to JSON objects / arrays. Kept in
    lockstep with the per-target adapter contract.
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


def test_n8n_adapter_wraps_shared_helper(tmp_path: Path) -> None:
    """CORE-FANOUT-N8N pins the n8n adapter against the shared helper.

    The adapter accepts the JSON-native payload an n8n
    ``executeCommand`` / ``Code`` node would marshal, rebuilds the
    typed context, and delegates to ``emit_supply_chain_artifact``.
    The on-disk record must be byte-identical to what the shared
    renderer produces, and the dict the adapter returns must name the
    right ``artifact_id`` / ``artifact_path``.
    """
    from compilers.n8n.evidence import emit_supply_chain_artifact_n8n

    ctx = _ctx()
    result = emit_supply_chain_artifact_n8n(_payload_from_ctx(ctx), tmp_path)
    written = Path(result["artifact_path"])
    assert written.exists()
    on_disk = json.loads(written.read_text("utf-8"))
    _validator().validate(on_disk)
    assert on_disk == render_supply_chain_artifact(ctx)
    assert result["artifact_id"] == on_disk["artifact_id"]
    assert written.name == f"{on_disk['artifact_id']}.json"


def test_n8n_adapter_preserves_sovereignty_classification(
    tmp_path: Path,
) -> None:
    """Provider sovereignty classification is forwarded verbatim.

    The n8n adapter must not reclassify, coerce, or default any of the
    classification axes (``residency``, ``ownership``,
    ``sovereignty_band``, ``sub_processor_chain``, ``band_rationale``,
    ``kb_ref``) — the operator's Sovereign Provider KB upstream of the
    node is the source of truth. Pins the contract per the F-CP-03
    CORE-FANOUT-N8N acceptance criteria.
    """
    from compilers.n8n.evidence import emit_supply_chain_artifact_n8n

    ctx = _ctx()
    result = emit_supply_chain_artifact_n8n(_payload_from_ctx(ctx), tmp_path)
    on_disk = json.loads(Path(result["artifact_path"]).read_text("utf-8"))
    # Sovereignty classification populated on every declared dependency.
    assert on_disk["dependencies"], "fixture must exercise dependencies"
    for emitted, source in zip(on_disk["dependencies"], ctx.dependencies):
        cls = emitted["sovereignty_classification"]
        src = source.sovereignty_classification
        assert cls["residency"] == src.residency
        assert cls["ownership"] == src.ownership
        assert cls["sovereignty_band"] == src.sovereignty_band
        if src.kb_ref is not None:
            assert cls["kb_ref"] == src.kb_ref
