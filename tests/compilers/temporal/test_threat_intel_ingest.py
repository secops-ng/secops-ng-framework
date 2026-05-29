"""Golden test for the Temporal compiler — threat-intel-ingest.

Pins the emitted Temporal workflow stub for the threat-intel-ingest
fixture; mirrors ``test_on_call_rotation.py`` so any drift in the
emitter surfaces in review.

Regenerate via::

    python -m compilers.temporal \\
        tests/compilers/_shared/fixtures/threat_intel_ingest.cacao.json \\
        > tests/compilers/temporal/golden/threat_intel_ingest.expected.py
"""
from __future__ import annotations

from pathlib import Path

from compilers.temporal.emit import emit_file

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "_shared"
    / "fixtures"
    / "threat_intel_ingest.cacao.json"
)
GOLDEN = (
    Path(__file__).resolve().parent
    / "golden"
    / "threat_intel_ingest.expected.py"
)


def test_threat_intel_ingest_matches_golden() -> None:
    actual = emit_file(FIXTURE)
    expected = GOLDEN.read_text(encoding="utf-8")
    assert actual == expected, (
        "Temporal emitter output drifted from the golden file. "
        "If this change is intentional, regenerate "
        f"{GOLDEN.relative_to(Path(__file__).resolve().parents[3])} "
        "and review the diff before committing."
    )


def test_golden_file_is_committed() -> None:
    assert GOLDEN.exists(), f"missing golden file: {GOLDEN}"
    assert GOLDEN.stat().st_size > 0, f"empty golden file: {GOLDEN}"


def test_emit_is_deterministic() -> None:
    assert emit_file(FIXTURE) == emit_file(FIXTURE)
