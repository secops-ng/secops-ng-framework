"""Golden test for the Temporal compiler.

Locks down the exact emitted Python source for the ``vuln_intake`` worked
example. Any change to the emitter that alters output for this fixture
must update the golden file in lockstep, surfacing regressions in code
review rather than letting silent drift land on main.

Regenerate the golden via::

    python -m compilers.temporal tests/compilers/_shared/fixtures/vuln_intake.cacao.json \\
        > tests/compilers/temporal/golden/vuln_intake.expected.py

A reviewer should inspect the diff before accepting an update.
"""
from __future__ import annotations

from pathlib import Path

from compilers.temporal.emit import emit_file

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "vuln_intake.cacao.json"
)
GOLDEN = Path(__file__).resolve().parent / "golden" / "vuln_intake.expected.py"

DATA_EXFIL_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "data_exfil.cacao.json"
)
DATA_EXFIL_GOLDEN = (
    Path(__file__).resolve().parent / "golden" / "data_exfil.expected.py"
)

THREAT_INTEL_INGEST_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "threat_intel_ingest.cacao.json"
)
THREAT_INTEL_INGEST_GOLDEN = (
    Path(__file__).resolve().parent
    / "golden"
    / "threat_intel_ingest.expected.py"
)


def test_vuln_intake_matches_golden() -> None:
    actual = emit_file(FIXTURE)
    expected = GOLDEN.read_text(encoding="utf-8")
    assert actual == expected, (
        "Temporal emitter output drifted from the golden file. "
        "If this change is intentional, regenerate "
        f"{GOLDEN.relative_to(Path(__file__).resolve().parents[3])} "
        "and review the diff before committing."
    )


def test_golden_file_is_committed() -> None:
    # Guards against an empty / missing golden landing on main.
    assert GOLDEN.exists(), f"missing golden file: {GOLDEN}"
    assert GOLDEN.stat().st_size > 0, f"empty golden file: {GOLDEN}"


def test_data_exfil_matches_golden() -> None:
    actual = emit_file(DATA_EXFIL_FIXTURE)
    expected = DATA_EXFIL_GOLDEN.read_text(encoding="utf-8")
    assert actual == expected, (
        "Temporal emitter output drifted from the data_exfil golden file. "
        "If this change is intentional, regenerate "
        f"{DATA_EXFIL_GOLDEN.relative_to(Path(__file__).resolve().parents[3])} "
        "and review the diff before committing."
    )


def test_data_exfil_golden_file_is_committed() -> None:
    assert DATA_EXFIL_GOLDEN.exists(), f"missing golden file: {DATA_EXFIL_GOLDEN}"
    assert DATA_EXFIL_GOLDEN.stat().st_size > 0, (
        f"empty golden file: {DATA_EXFIL_GOLDEN}"
    )


def test_data_exfil_emit_is_deterministic() -> None:
    assert emit_file(DATA_EXFIL_FIXTURE) == emit_file(DATA_EXFIL_FIXTURE)


def test_worked_example_stub_matches_golden() -> None:
    """The committed `examples/temporal/data_exfil/workflow.temporal.py`
    is the emitter's output for the data_exfil fixture; any drift between
    the worked example and the golden indicates the example was edited
    by hand instead of regenerated.
    """
    stub = (
        Path(__file__).resolve().parents[3]
        / "examples"
        / "temporal"
        / "data_exfil"
        / "workflow.temporal.py"
    )
    assert stub.exists(), f"missing worked-example stub: {stub}"
    assert stub.read_text(encoding="utf-8") == DATA_EXFIL_GOLDEN.read_text(
        encoding="utf-8"
    )


def test_threat_intel_ingest_matches_golden() -> None:
    actual = emit_file(THREAT_INTEL_INGEST_FIXTURE)
    expected = THREAT_INTEL_INGEST_GOLDEN.read_text(encoding="utf-8")
    assert actual == expected, (
        "Temporal emitter output drifted from the threat_intel_ingest "
        "golden file. If this change is intentional, regenerate "
        f"{THREAT_INTEL_INGEST_GOLDEN.relative_to(Path(__file__).resolve().parents[3])} "
        "and review the diff before committing."
    )


def test_threat_intel_ingest_golden_file_is_committed() -> None:
    assert THREAT_INTEL_INGEST_GOLDEN.exists(), (
        f"missing golden file: {THREAT_INTEL_INGEST_GOLDEN}"
    )
    assert THREAT_INTEL_INGEST_GOLDEN.stat().st_size > 0, (
        f"empty golden file: {THREAT_INTEL_INGEST_GOLDEN}"
    )


def test_threat_intel_ingest_emit_is_deterministic() -> None:
    assert emit_file(THREAT_INTEL_INGEST_FIXTURE) == emit_file(
        THREAT_INTEL_INGEST_FIXTURE
    )


# The threat_intel_ingest worked-example drift guard lives in
# tests/examples/threat_intel_ingest/test_temporal_workflow.py — it
# pins examples/temporal/threat_intel_ingest/workflow.temporal.py
# against the emitter output for the *canonical* CACAO playbook
# (content/playbooks/threat_intel_ingest/playbook.cacao.json), which
# is what regenerate.sh actually consumes. The fixture under
# tests/compilers/_shared/fixtures/ is a separate compiler unit-test
# input and diverges from the canonical source; do not pin the worked
# example against it.
