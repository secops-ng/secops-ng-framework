"""F-SV-03 CORE — per-target byte-parity goldens for the DORA Art. 19 report variant.

Pins the on-disk bytes of the DORA Article 19 report-variant artifact
emitted by each compile target (n8n, Temporal, LangGraph) against
checked-in fixtures under
``tests/fixtures/dora_art19_report/<target>.<variant>.json``.

The F-SV-03 CORE invariant is one shared helper / three thin adapters /
byte-identical output across the three reference targets. These tests
are the byte-level pin of that invariant:

1. **Cross-target byte parity.** The three adapters write byte-identical
   records per variant; pinned at fixture-load time so a future drift
   surfaces with one failure message instead of three.
2. **Per-target adapter parity.** Each target's adapter is exercised
   against its own immutable golden so a refactor of the shared
   emitter that silently changes serialisation gets caught at the byte
   level — the failure message names which target drifted.
3. **Article 19 chain coverage.** The variant axis covers all four
   entries on the DORA Art. 19 chain: ``initial_4h`` / ``intermediate_72h``
   / ``final_1mo`` / ``voluntary_cyber_threat``.
4. **report_id determinism.** ``report_id`` on the on-disk record
   matches ``SHA-256(<incident_id>|<report_variant>|<submitted_at>)``
   per the schema contract.

If the shared emitter changes the on-disk serialisation intentionally,
regenerate the goldens by re-running the per-target ``regenerate.py``
scripts under ``examples/{n8n,temporal,langgraph}/dora_art19_report/``,
copying the new bytes into ``tests/fixtures/dora_art19_report/``, and
committing the updated bytes alongside the emitter change.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pytest

from compilers._shared.evidence import (
    DoraArt19ReportContext,
    derive_dora_art19_report_id,
)

REPO = Path(__file__).resolve().parents[3]
FIXTURES = REPO / "tests" / "fixtures" / "dora_art19_report"
SCHEMA = REPO / "schemas" / "evidence" / "dora-art19-technical-incident-report.schema.json"
MILESTONE_SCHEMA = REPO / "schemas" / "dora_art19_report_milestone.json"

VARIANTS = ("initial_4h", "intermediate_72h", "final_1mo", "voluntary_cyber_threat")
TARGETS = ("n8n", "temporal", "langgraph")


# --------------------------------------------------------------------------- #
# Shared context loader                                                       #
# --------------------------------------------------------------------------- #


def _load_contexts() -> dict[str, DoraArt19ReportContext]:
    """Import the canonical per-variant contexts the goldens pin against.

    The Temporal worked-example's ``regenerate.py`` is the single
    source of truth for the example inputs — the n8n and LangGraph
    siblings re-import the same dict so a future edit to the contexts
    propagates to all three targets in lockstep.
    """
    path = REPO / "examples" / "temporal" / "dora_art19_report" / "regenerate.py"
    spec = importlib.util.spec_from_file_location(
        "_dora_art19_report_temporal_regen", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CONTEXTS


def _ctx_to_n8n_payload(ctx: DoraArt19ReportContext) -> dict:
    """Reshape a typed context as the JSON-native payload an n8n node sends."""
    from dataclasses import asdict

    payload = asdict(ctx)

    def _iso(dt: datetime) -> str:
        return dt.astimezone(dt.tzinfo).replace(microsecond=0).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    payload["submitted_at"] = _iso(ctx.submitted_at)
    payload["timeline_refs"]["clock_started_at"] = _iso(
        ctx.timeline_refs.clock_started_at
    )
    return payload


def _fixture(target: str, variant: str) -> Path:
    return FIXTURES / f"{target}.{variant}.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# Fixture-on-disk guardrails                                                  #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("target", TARGETS)
def test_golden_fixtures_are_committed(target: str, variant: str) -> None:
    path = _fixture(target, variant)
    assert path.exists(), f"missing golden fixture: {path}"
    assert path.stat().st_size > 0, f"empty golden fixture: {path}"


@pytest.mark.parametrize("variant", VARIANTS)
def test_golden_fixtures_are_byte_identical_across_targets(variant: str) -> None:
    """Cross-target byte parity: the three adapters all delegate to one
    shared emitter, so the three goldens for a variant MUST be
    byte-identical. Pinning the parity at fixture-load time means a
    per-target test below succeeds for one target and fails for the
    others — but the failure here surfaces the divergence with one
    diagnostic message instead of three.
    """
    n8n = _fixture("n8n", variant).read_bytes()
    temporal = _fixture("temporal", variant).read_bytes()
    langgraph = _fixture("langgraph", variant).read_bytes()
    assert n8n == temporal == langgraph, (
        f"cross-target byte parity drift on variant {variant!r}"
    )


# --------------------------------------------------------------------------- #
# Per-target byte-parity goldens                                              #
# --------------------------------------------------------------------------- #


def _drift_hint(target: str, variant: str) -> str:
    return (
        f"{target} DORA Art. 19 report-variant artifact for {variant!r} "
        f"drifted from the committed golden. If the change is "
        f"intentional, regenerate the goldens by re-running the "
        f"per-target regenerate.py scripts under "
        f"examples/{{n8n,temporal,langgraph}}/dora_art19_report/ and "
        f"committing the new bytes alongside the emitter change."
    )


@pytest.mark.parametrize("variant", VARIANTS)
def test_temporal_artifact_matches_golden(tmp_path: Path, variant: str) -> None:
    pytest.importorskip("temporalio")
    from compilers.temporal.evidence import emit_dora_art19_report_activity

    ctx = _load_contexts()[variant]
    written = Path(
        asyncio.run(emit_dora_art19_report_activity(ctx, str(tmp_path)))
    )
    golden = _fixture("temporal", variant)
    assert written.read_bytes() == golden.read_bytes(), _drift_hint(
        "Temporal", variant
    )


@pytest.mark.parametrize("variant", VARIANTS)
def test_n8n_artifact_matches_golden(tmp_path: Path, variant: str) -> None:
    from compilers.n8n.evidence import emit_dora_art19_report_n8n

    ctx = _load_contexts()[variant]
    payload = _ctx_to_n8n_payload(ctx)
    result = emit_dora_art19_report_n8n(payload, tmp_path)
    written = Path(result["report_path"])
    golden = _fixture("n8n", variant)
    assert written.read_bytes() == golden.read_bytes(), _drift_hint(
        "n8n", variant
    )


@pytest.mark.parametrize("variant", VARIANTS)
def test_langgraph_artifact_matches_golden(
    tmp_path: Path, variant: str
) -> None:
    from compilers.langgraph.evidence import emit_dora_art19_report_node

    ctx = _load_contexts()[variant]
    update = emit_dora_art19_report_node(
        {
            "dora_art19_report_context": ctx,
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["dora_art19_report_path"])
    golden = _fixture("langgraph", variant)
    assert written.read_bytes() == golden.read_bytes(), _drift_hint(
        "LangGraph", variant
    )


# --------------------------------------------------------------------------- #
# Coverage axis: schema-conformant emit                                       #
# --------------------------------------------------------------------------- #


def _validator():
    from jsonschema import Draft202012Validator, RefResolver

    schema = _load_json(SCHEMA)
    store = {
        "https://secops-ng.org/schemas/dora_art19_report_milestone.json": (
            _load_json(MILESTONE_SCHEMA)
        ),
    }
    resolver = RefResolver(base_uri=schema["$id"], referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("target", TARGETS)
def test_golden_validates_against_schema(target: str, variant: str) -> None:
    _validator().validate(_load_json(_fixture(target, variant)))


# --------------------------------------------------------------------------- #
# Coverage axis: DORA Art. 19 chain vocabulary                                #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("target", TARGETS)
def test_report_variant_matches_filename(target: str, variant: str) -> None:
    """The committed golden's ``report_variant`` is the variant the
    filename declares — guards an accidental cross-copy of fixtures.
    """
    record = _load_json(_fixture(target, variant))
    assert record["report_variant"] == variant


def test_fixtures_cover_all_four_dora_milestones() -> None:
    """Acceptance pin: the goldens cover the full DORA Art. 19 chain
    plus the Art. 19(2) voluntary-threat lane. If a future edit drops
    one, fail loudly so the parity beat doesn't silently lose
    schema-surface coverage.
    """
    seen = {
        _load_json(_fixture("temporal", v))["report_variant"] for v in VARIANTS
    }
    assert seen == set(VARIANTS)


# --------------------------------------------------------------------------- #
# Coverage axis: report_id determinism                                        #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("target", TARGETS)
def test_report_id_matches_derivation(target: str, variant: str) -> None:
    """``report_id`` on the on-disk record equals
    ``SHA-256(<incident_id>|<report_variant>|<submitted_at>)`` per the
    schema contract. A target that silently re-derives the id from a
    different key fails fast.
    """
    ctx = _load_contexts()[variant]
    record = _load_json(_fixture(target, variant))
    expected = derive_dora_art19_report_id(
        ctx.incident_id, ctx.report_variant, ctx.submitted_at
    )
    assert record["report_id"] == expected


# --------------------------------------------------------------------------- #
# Cross-milestone chain pin                                                   #
# --------------------------------------------------------------------------- #


def test_chain_variants_pin_previous_milestone_event_id() -> None:
    """``intermediate_72h`` pins the ``early_warning`` event id;
    ``final_1mo`` pins the ``notification`` event id. ``initial_4h``
    and ``voluntary_cyber_threat`` carry no prior milestone.
    """
    intermediate = _load_json(_fixture("temporal", "intermediate_72h"))
    final = _load_json(_fixture("temporal", "final_1mo"))
    initial = _load_json(_fixture("temporal", "initial_4h"))
    voluntary = _load_json(_fixture("temporal", "voluntary_cyber_threat"))

    assert "previous_milestone_event_id" in intermediate["timeline_refs"]
    assert "previous_milestone_event_id" in final["timeline_refs"]
    assert "previous_milestone_event_id" not in initial["timeline_refs"]
    assert "previous_milestone_event_id" not in voluntary["timeline_refs"]

    # Pin the values against the canonical timeline-events log on the
    # Temporal regen contexts so a re-ordering of the chain is caught.
    contexts = _load_contexts()
    chain_events = {
        e["stage"]: e["event_id"]
        for e in contexts["intermediate_72h"].timeline_events
    }
    assert (
        intermediate["timeline_refs"]["previous_milestone_event_id"]
        == chain_events["early_warning"]
    )
    assert (
        final["timeline_refs"]["previous_milestone_event_id"]
        == chain_events["notification"]
    )
