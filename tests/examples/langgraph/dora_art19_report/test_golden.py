"""F-G03-PARITY — per-target byte-parity golden for examples/langgraph/dora_art19_report/.

Thin per-target sibling of the cross-target byte-parity guard at
``tests/examples/dora_art19_report/test_golden.py``. Re-runs the
LangGraph DORA Article 19 report node
(``compilers.langgraph.evidence.emit_dora_art19_report_node``) against
the canonical per-variant contexts and pins the on-disk bytes against
the committed goldens under
``tests/fixtures/dora_art19_report/langgraph.<variant>.json``.

This closes the LangGraph end of the cross-target parity ring (G-03)
for the ``dora_art19_report`` DORA Article 19 report variant, alongside
the n8n and Temporal siblings under
``tests/examples/{n8n,temporal}/dora_art19_report/``.

Regenerate via::

    PYTHONPATH=. python examples/langgraph/dora_art19_report/regenerate.py
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
FIXTURES = REPO / "tests" / "fixtures" / "dora_art19_report"
TEMPORAL_REGEN = (
    REPO / "examples" / "temporal" / "dora_art19_report" / "regenerate.py"
)

VARIANTS = ("initial_4h", "intermediate_72h", "final_1mo", "voluntary_cyber_threat")
TARGET = "langgraph"


def _load_contexts() -> dict:
    """Import the canonical per-variant contexts pinned by the goldens."""
    spec = importlib.util.spec_from_file_location(
        "_dora_art19_report_temporal_regen", TEMPORAL_REGEN
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CONTEXTS


def _fixture(variant: str) -> Path:
    return FIXTURES / f"{TARGET}.{variant}.json"


# --------------------------------------------------------------------------- #
# Fixture-on-disk guardrails                                                  #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("variant", VARIANTS)
def test_golden_fixture_committed(variant: str) -> None:
    path = _fixture(variant)
    assert path.exists(), f"missing golden fixture: {path}"
    assert path.stat().st_size > 0, f"empty golden fixture: {path}"


# --------------------------------------------------------------------------- #
# Byte-parity: LangGraph adapter output == committed golden                   #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("variant", VARIANTS)
def test_langgraph_artifact_matches_golden(tmp_path: Path, variant: str) -> None:
    from compilers.langgraph.evidence import emit_dora_art19_report_node

    ctx = _load_contexts()[variant]
    update = emit_dora_art19_report_node(
        {
            "dora_art19_report_context": ctx,
            "evidence_output_dir": str(tmp_path),
        }
    )
    written = Path(update["dora_art19_report_path"])
    golden = _fixture(variant)
    assert written.read_bytes() == golden.read_bytes(), (
        f"LangGraph DORA Art. 19 report-variant artifact for {variant!r} "
        f"drifted from the committed golden. If the change is intentional, "
        f"regenerate via `PYTHONPATH=. python "
        f"examples/langgraph/dora_art19_report/regenerate.py` and commit "
        f"the new bytes alongside the emitter change."
    )


# --------------------------------------------------------------------------- #
# report_variant / report_id determinism                                      #
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("variant", VARIANTS)
def test_report_variant_matches_filename(variant: str) -> None:
    record = json.loads(_fixture(variant).read_text(encoding="utf-8"))
    assert record["report_variant"] == variant


@pytest.mark.parametrize("variant", VARIANTS)
def test_report_id_matches_derivation(variant: str) -> None:
    from compilers._shared.evidence import derive_dora_art19_report_id

    ctx = _load_contexts()[variant]
    record = json.loads(_fixture(variant).read_text(encoding="utf-8"))
    expected = derive_dora_art19_report_id(
        ctx.incident_id, ctx.report_variant, ctx.submitted_at
    )
    assert record["report_id"] == expected
